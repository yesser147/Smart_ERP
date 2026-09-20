"""
Candidate matching for a job's real applicants.

Final score = weighted blend (a missing signal is dropped and the rest
renormalized):
    40% LLM judgment         (skills + past roles + years, small batches)
    25% skill coverage       (each REQUIRED skill matched semantically)
    25% role relevance       (job title vs the candidate's past job titles)
    10% CV-vs-job similarity (calibrated embedding)
plus a gate: covering almost none of the required skills caps the score.
Only complete (LLM-judged) scores are cached.
"""

import json
import numpy as np
import pandas as pd
from types import SimpleNamespace
from sqlalchemy import text
from database import engine
from embeddings import embed_text, get_model
from models.recruitment.llm_client import generate

LLM_BATCH_SIZE = 5
EMB_LOW, EMB_HIGH = 15.0, 60.0             # raw cosine % -> 0-100 (tune on real values)
SKILL_SIM_LOW, SKILL_SIM_HIGH = 0.25, 0.65
ROLE_SIM_LOW, ROLE_SIM_HIGH = 0.15, 0.60
W_LLM, W_COVERAGE, W_ROLE, W_EMB = 0.40, 0.25, 0.25, 0.10
GATE_COVERAGE, GATE_CAP = 20.0, 35.0


def _safe_parse_skills(raw_value):
    """extracted_skills_json is JSONB -- psycopg2 auto-deserializes it to
    a list/dict on read. Tolerate both shapes."""
    if raw_value is None:
        return []
    if isinstance(raw_value, (list, dict)):
        return raw_value
    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return []


# ---------------------------------------------------------------- job profile

def _generate_skills_with_llm(job) -> str:
    """Cache-miss fallback: no curated row for this title yet."""
    ctx = ", ".join(x for x in (job.department_type, job.division_description) if x)
    prompt = f"""List the 8 to 12 most important skills, tools and qualifications
required for the job "{job.title}"{f' in the department: {ctx}' if ctx else ''}.
Return ONLY a valid JSON object: {{"skills": ["skill1", "skill2"]}}"""
    try:
        skills = json.loads(generate(prompt, json_mode=True)).get("skills", [])
        return ", ".join(str(s) for s in skills if s)
    except Exception as e:
        print(f"  ⚠️  Skill generation failed for '{job.title}': {e}")
        return ""


def get_required_skills(job) -> str:
    """Curated row if present, else generate once with the LLM and cache it."""
    key = job.title.strip().lower()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT skills FROM job_title_skills WHERE title_key = :k"),
                           {"k": key}).fetchone()
    if row:
        return row.skills

    skills = _generate_skills_with_llm(job)
    if skills:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO job_title_skills (title_key, title, skills, source)
                VALUES (:k, :t, :s, 'llm')
                ON CONFLICT (title_key) DO NOTHING
            """), {"k": key, "t": job.title.strip(), "s": skills})
    return skills


def _load_job(job_id: int):
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT jp.job_id, jp.title, jp.required_experience_years,
                   d.department_type, d.division_description
            FROM job_postings jp
            LEFT JOIN departments d ON d.department_id = jp.department_id
            WHERE jp.job_id = :jid
        """), {"jid": job_id}).fetchone()
    if row is None:
        return None
    job = SimpleNamespace(**row._mapping)
    job.required_skills = get_required_skills(job)
    return job


def _job_profile_text(job) -> str:
    parts = [f"Job title: {job.title}."]
    if job.required_skills:
        parts.append(f"Required skills: {job.required_skills}.")
    parts.append(f"Requires {job.required_experience_years or 0} years of experience.")
    return " ".join(parts)


def _job_meta(job) -> dict:
    """Job details sent back with every match result (shown on the job page)."""
    return {
        "job_id": job.job_id,
        "job_title": job.title,
        "required_skills": job.required_skills or "",
        "required_experience_years": (
            float(job.required_experience_years)
            if job.required_experience_years is not None else None
        ),
    }


# -------------------------------------------------------------------- signals

def _fetch_job_applicants(job_id: int) -> pd.DataFrame:
    """Only people who actually applied to this job. Years come from the
    CV itself when available (the applicants table values are not tied
    to the resume text)."""
    query = text("""
        SELECT
            ja.application_id, ja.ai_match_score,
            ja.ai_match_reasoning, ja.ai_embedding_score,
            a.applicant_id, a.first_name, a.last_name,
            a.education_level,
            COALESCE(ac.cv_years_of_experience, a.years_of_experience) AS years_of_experience,
            ac.extracted_skills_json, ac.experience_profile, ac.cv_embedding
        FROM job_applications ja
        JOIN applicants a ON a.applicant_id = ja.applicant_id
        LEFT JOIN applicant_cvs ac ON ac.applicant_id = a.applicant_id
        WHERE ja.job_id = :jid
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"jid": job_id})


def _embedding_scores(job_text: str, applicant_ids: list) -> dict:
    """Raw cosine similarity (%), restricted to the given applicants."""
    if not applicant_ids:
        return {}
    query_vec = embed_text(job_text)
    query_literal = "[" + ",".join(map(str, query_vec)) + "]"
    query = text("""
        SELECT applicant_id, 1 - (cv_embedding <=> :qvec) AS similarity
        FROM applicant_cvs
        WHERE applicant_id = ANY(:aids) AND cv_embedding IS NOT NULL
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"qvec": query_literal, "aids": applicant_ids})
    return {int(r.applicant_id): round(float(r.similarity) * 100, 1) for r in df.itertuples()}


def _calibrate_embedding(sim_pct: float) -> float:
    return round(max(0.0, min(100.0, (sim_pct - EMB_LOW) / (EMB_HIGH - EMB_LOW) * 100)), 1)


def _split_skills(raw) -> list:
    return [s.strip() for s in str(raw or "").split(",") if s.strip()]


def _coverage_scores(required: list, skills_by_applicant: dict) -> dict:
    """{applicant_id: 0-100, or None if the job has no required skills}."""
    if not required:
        return {aid: None for aid in skills_by_applicant}

    model = get_model()
    req_vecs = model.encode(required, normalize_embeddings=True)
    out = {}
    for aid, skills in skills_by_applicant.items():
        skills = [str(s) for s in skills if s]
        if not skills:
            out[aid] = 0.0
            continue
        cand_vecs = model.encode(skills, normalize_embeddings=True)
        best = (req_vecs @ cand_vecs.T).max(axis=1)
        scaled = np.clip((best - SKILL_SIM_LOW) / (SKILL_SIM_HIGH - SKILL_SIM_LOW), 0, 1)
        out[aid] = round(float(scaled.mean()) * 100, 1)
    return out


def _role_relevance(job, profiles: dict) -> dict:
    """{applicant_id: 0-100, or None if the CV has no experience profile}:
    semantic fit between the job title and the candidate's past job titles."""
    out = {aid: None for aid in profiles}
    ids = [aid for aid, p in profiles.items() if p]
    if not ids:
        return out

    model = get_model()
    job_vec = model.encode(f"Job title: {job.title}.", normalize_embeddings=True)
    vecs = model.encode([profiles[a] for a in ids], normalize_embeddings=True)
    sims = vecs @ job_vec
    for aid, s in zip(ids, sims):
        scaled = np.clip((float(s) - ROLE_SIM_LOW) / (ROLE_SIM_HIGH - ROLE_SIM_LOW), 0, 1)
        out[aid] = round(float(scaled) * 100, 1)
    return out


def _rerank_batch(job, rows: pd.DataFrame) -> dict:
    payload_in = [
        {
            "applicant_id": int(r.applicant_id),
            "years_of_experience": float(r.years_of_experience) if pd.notna(r.years_of_experience) else None,
            "education_level": r.education_level,
            "past_roles": r.experience_profile if pd.notna(r.experience_profile) else None,
            "skills": _safe_parse_skills(r.extracted_skills_json),
        }
        for r in rows.itertuples()
    ]

    prompt = f"""You are ranking job candidates for this position:
{_job_profile_text(job)}

Candidates (JSON):
{json.dumps(payload_in, indent=2)}

Score each candidate 0-100 for how well they can actually do THIS job.
Consider (1) whether their skills match the required skills and (2) whether
their past roles are in a relevant field. A career in an unrelated field (for
example an accountant applying for a nursing job) must score below 25, even
with more years of experience than required or a higher degree.

Return ONLY a valid JSON object with no other text, in this exact shape:
{{
  "rankings": [
    {{"applicant_id": 123, "score": 82, "reasoning": "one short sentence why"}}
  ]
}}"""

    try:
        payload = json.loads(generate(prompt, json_mode=True))
        return {
            int(r["applicant_id"]): {"score": max(0.0, min(100.0, float(r["score"]))),
                                     "reasoning": r.get("reasoning", "")}
            for r in payload.get("rankings", [])
            if "applicant_id" in r and "score" in r
        }
    except Exception as e:
        print(f"  ⚠️  LLM batch failed: {e}")
        return {}


def _rerank_with_llm(job, rows: pd.DataFrame) -> dict:
    results = {}
    for start in range(0, len(rows), LLM_BATCH_SIZE):
        results.update(_rerank_batch(job, rows.iloc[start:start + LLM_BATCH_SIZE]))
    return results


def _weighted(parts) -> float:
    parts = [(w, v) for w, v in parts if v is not None]
    return sum(w * v for w, v in parts) / sum(w for w, _ in parts)


def _blend(llm_score: float, coverage, role, emb: float) -> float:
    final = _weighted([(W_LLM, llm_score), (W_COVERAGE, coverage), (W_ROLE, role), (W_EMB, emb)])
    if coverage is not None and coverage < GATE_COVERAGE:
        final = min(final, GATE_CAP)
    return round(final, 1)


def _provisional(coverage, role, emb: float) -> float:
    """Used when the LLM failed: shown but never cached."""
    return round(_weighted([(0.4, coverage), (0.3, role), (0.3, emb)]), 1)


def _persist_score(application_id, score: float, reasoning: str, embedding_score: float):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE job_applications
            SET ai_match_score = :score, ai_match_reasoning = :why, ai_embedding_score = :emb
            WHERE application_id = :aid
        """), {"score": round(score), "why": reasoning, "emb": embedding_score, "aid": application_id})


# ------------------------------------------------------------------ main entry

def match_candidates_to_job(job_id: int, top_k: int = 10, recompute_all: bool = False):
    job = _load_job(job_id)
    if job is None:
        return None

    applicants_df = _fetch_job_applicants(job_id)
    if applicants_df.empty:
        return {**_job_meta(job), "candidates": []}

    scorable = applicants_df[applicants_df["cv_embedding"].notna()].copy()

    if recompute_all:
        to_score = scorable
        already_scored = pd.DataFrame(columns=scorable.columns)
    else:
        already_scored = scorable[scorable["ai_match_score"].notna()]
        to_score = scorable[scorable["ai_match_score"].isna()]

    def base(r):
        # skills go out as a JSON string: that's what the frontend's parseSkills expects
        return {
            "applicant_id": int(r.applicant_id),
            "name": f"{r.first_name} {r.last_name}",
            "education_level": r.education_level,
            "years_of_experience": float(r.years_of_experience) if pd.notna(r.years_of_experience) else None,
            "skills": json.dumps(_safe_parse_skills(r.extracted_skills_json)),
        }

    candidates = []

    # Cached: score, similarity and reasoning all come from the DB.
    for r in already_scored.itertuples():
        candidates.append({
            **base(r),
            "match_score": float(r.ai_match_score),
            "embedding_score": float(r.ai_embedding_score) if pd.notna(r.ai_embedding_score) else None,
            "ai_reasoning": r.ai_match_reasoning if pd.notna(r.ai_match_reasoning) else None,
        })

    if not to_score.empty:
        applicant_ids = to_score["applicant_id"].astype(int).tolist()

        raw_sims = _embedding_scores(_job_profile_text(job), applicant_ids)
        coverages = _coverage_scores(
            _split_skills(job.required_skills),
            {int(r.applicant_id): _safe_parse_skills(r.extracted_skills_json)
             for r in to_score.itertuples()},
        )
        role_scores = _role_relevance(
            job,
            {int(r.applicant_id): (r.experience_profile if pd.notna(r.experience_profile) else None)
             for r in to_score.itertuples()},
        )
        llm_scores = _rerank_with_llm(job, to_score)

        for r in to_score.itertuples():
            aid = int(r.applicant_id)
            emb = _calibrate_embedding(raw_sims.get(aid, 0.0))
            coverage = coverages.get(aid)
            role = role_scores.get(aid)
            llm_result = llm_scores.get(aid)

            if llm_result:
                final = _blend(llm_result["score"], coverage, role, emb)
                reasoning = llm_result["reasoning"]
                _persist_score(r.application_id, final, reasoning, emb)   # only complete scores are cached
            else:
                final, reasoning = _provisional(coverage, role, emb), None   # retried on next search

            candidates.append({**base(r), "match_score": final,
                               "embedding_score": emb, "ai_reasoning": reasoning})

    candidates.sort(key=lambda c: c["match_score"], reverse=True)
    return {**_job_meta(job), "candidates": candidates[:top_k]}