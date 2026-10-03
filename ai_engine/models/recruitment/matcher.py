"""
Candidate matching for a job's real applicants: requirement-by-requirement.

1. The job is turned into a short list of REQUIREMENTS (must-haves and
   nice-to-haves), once, and cached on the job posting. The required years of
   experience are added as a must-have checked by code, not by the LLM.
2. Cheap signals (skill coverage, role relevance, CV-vs-job similarity) pick
   the candidates worth a full review (config.MATCH_LLM_MAX).
3. Each of them is REVIEWED by the LLM: every requirement is marked met,
   partial or missing, with the evidence quoted from the CV.
4. The score comes from that checklist:
       met = 1, partial = 0.5, missing = 0; a must-have counts double
       1 must-have missing -> score capped at 60, 2 or more -> capped at 40
   so every score can be explained line by line.

Only complete (reviewed) scores are cached, with their checklist.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import numpy as np
import pandas as pd
from sqlalchemy import text

import config
from database import engine
from embeddings import embed_text, get_model
from models.recruitment.llm_client import generate_json
from models.recruitment.privacy import redact

log = logging.getLogger(__name__)

EMB_LOW, EMB_HIGH = 15.0, 60.0             # raw cosine % -> 0-100
SKILL_SIM_LOW, SKILL_SIM_HIGH = 0.25, 0.65
ROLE_SIM_LOW, ROLE_SIM_HIGH = 0.15, 0.60

WEIGHT = {"must": 2.0, "nice": 1.0}
POINTS = {"met": 1.0, "partial": 0.5, "missing": 0.0}
CAP_ONE_MUST_MISSING, CAP_MUSTS_MISSING = 60.0, 40.0
CV_EXCERPT_CHARS = 3000


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


def _clean(value):
    """pandas uses NaN for missing values; JSON can't encode NaN."""
    if value is None:
        return None
    try:
        return None if pd.isna(value) else value
    except (TypeError, ValueError):
        return value


# ---------------------------------------------------------------- job profile

def _generate_skills_with_llm(job) -> str:
    """Cache-miss fallback: no curated row for this title yet."""
    ctx = ", ".join(x for x in (job.department_type, job.division_description) if x)
    prompt = f"""List the 8 to 12 most important skills, tools and qualifications
required for the job "{job.title}"{f' in the department: {ctx}' if ctx else ''}.
Return ONLY a valid JSON object: {{"skills": ["skill1", "skill2"]}}"""
    try:
        skills = generate_json(prompt).get("skills", [])
        return ", ".join(str(s) for s in skills if s)
    except Exception as e:
        log.warning("Skill generation failed for '%s': %s", job.title, e)
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
            SELECT jp.job_id, jp.title, jp.required_experience_years, jp.description, jp.ai_requirements,
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


def _split_skills(raw) -> list:
    return [s.strip() for s in str(raw or "").split(",") if s.strip()]


# ---------------------------------------------------------------- requirements

def _years_requirement(job) -> dict | None:
    years = _clean(job.required_experience_years)
    if not years:
        return None
    return {"requirement": f"{float(years):g}+ years of relevant experience", "type": "must",
            "category": "years", "years": float(years)}


def _requirements_from_skills(job) -> list[dict]:
    """Fallback when the LLM can't extract the requirements: the first required
    skills are must-haves, the rest nice-to-haves."""
    skills = _split_skills(job.required_skills)
    return [{"requirement": s, "type": "must" if i < 4 else "nice", "category": "skill"}
            for i, s in enumerate(skills[:10])]


def _extract_requirements(job) -> list[dict]:
    prompt = f"""You prepare the screening checklist for a job opening.

JOB TITLE: {job.title}
DEPARTMENT: {job.department_type or '-'} / {job.division_description or '-'}
REQUIRED SKILLS (reference list): {job.required_skills or '-'}
JOB DESCRIPTION:
{(job.description or '-')[:3000]}

List 5 to 8 requirements a recruiter would check in a CV for this job.
- "must": essential for the job (at most 4); "nice": a plus.
- Each requirement must be concrete and verifiable from a CV (a skill, a tool,
  a type of experience, a degree), written in at most 8 words.
- Do NOT include the number of years of experience (it is checked separately).
- category is one of: skill, experience, education, other.

Return ONLY a valid JSON object:
{{"requirements": [{{"requirement": "B2B sales experience", "type": "must", "category": "experience"}}]}}"""
    try:
        raw = generate_json(prompt, temperature=0.0).get("requirements", [])
        reqs = []
        for r in raw:
            label = str(r.get("requirement", "")).strip()
            if not label:
                continue
            reqs.append({
                "requirement": label[:80],
                "type": "must" if str(r.get("type", "")).lower() == "must" else "nice",
                "category": str(r.get("category", "other")).lower(),
            })
        # keep the "at most 4 must-haves" rule even if the model ignored it
        musts = [r for r in reqs if r["type"] == "must"]
        for r in musts[4:]:
            r["type"] = "nice"
        if len(reqs) >= 3:
            return reqs[:8]
    except Exception as e:
        log.warning("Requirement extraction failed for job %s: %s", job.job_id, e)
    return _requirements_from_skills(job)


def get_requirements(job, refresh: bool = False) -> list[dict]:
    """The job's checklist (years requirement first), cached in job_postings.ai_requirements."""
    cached = job.ai_requirements
    if isinstance(cached, str):
        cached = json.loads(cached)
    if cached and not refresh:
        return cached

    reqs = _extract_requirements(job)
    years = _years_requirement(job)
    if years:
        reqs = [years] + reqs
    with engine.begin() as conn:
        conn.execute(text("UPDATE job_postings SET ai_requirements = CAST(:r AS jsonb) WHERE job_id = :jid"),
                     {"r": json.dumps(reqs), "jid": job.job_id})
    job.ai_requirements = reqs
    return reqs


# ---------------------------------------------------------------- cheap signals (pre-screen)

def _fetch_job_applicants(job_id: int) -> pd.DataFrame:
    """Only people who actually applied to this job. Years come from the
    CV itself when available."""
    query = text("""
        SELECT
            ja.application_id, ja.ai_match_score, ja.ai_match_reasoning,
            ja.ai_embedding_score, ja.ai_match_details,
            a.applicant_id, a.first_name, a.last_name, a.education_level,
            COALESCE(ac.cv_years_of_experience, a.years_of_experience) AS years_of_experience,
            ac.extracted_skills_json, ac.experience_profile, ac.parsed_text, ac.cv_embedding
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


def _coverage_scores(required: list, skills_by_applicant: dict) -> dict:
    """{applicant_id: 0-100, or None if the job has no required skills}."""
    if not required:
        return {aid: None for aid in skills_by_applicant}

    model = get_model()
    req_vecs = model.encode(required, normalize_embeddings=True)

    # every distinct skill of every candidate encoded in ONE batch
    cleaned = {aid: [str(x) for x in skills if x] for aid, skills in skills_by_applicant.items()}
    unique_skills = sorted({x for skills in cleaned.values() for x in skills})
    vec_by_skill = {}
    if unique_skills:
        vecs = model.encode(unique_skills, normalize_embeddings=True, batch_size=128)
        vec_by_skill = dict(zip(unique_skills, vecs))

    out = {}
    for aid, skills in cleaned.items():
        if not skills:
            out[aid] = 0.0
            continue
        cand_vecs = np.stack([vec_by_skill[x] for x in skills])
        best = (req_vecs @ cand_vecs.T).max(axis=1)
        scaled = np.clip((best - SKILL_SIM_LOW) / (SKILL_SIM_HIGH - SKILL_SIM_LOW), 0, 1)
        out[aid] = round(float(scaled.mean()) * 100, 1)
    return out


def _role_relevance(job, profiles: dict) -> dict:
    """{applicant_id: 0-100, or None if the CV has no experience profile}."""
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


def _prescreen(coverage, role, emb: float) -> float:
    """Cheap estimate used to choose who gets the full review."""
    parts = [(w, v) for w, v in ((0.4, coverage), (0.3, role), (0.3, emb)) if v is not None]
    return round(sum(w * v for w, v in parts) / sum(w for w, _ in parts), 1)


# ---------------------------------------------------------------- the review (checklist)

def _check_years(req: dict, years) -> dict:
    """The years requirement is checked by code: the LLM is bad at arithmetic."""
    years = _clean(years)
    needed = req["years"]
    if years is None:
        status, evidence = "missing", "Years of experience not found in the CV"
    elif float(years) >= needed:
        status, evidence = "met", f"{float(years):g} years of experience"
    elif float(years) >= 0.6 * needed:
        status, evidence = "partial", f"{float(years):g} years of experience (asks {needed:g})"
    else:
        status, evidence = "missing", f"{float(years):g} years of experience (asks {needed:g})"
    return {**{k: req[k] for k in ("requirement", "type", "category")}, "status": status, "evidence": evidence}


def _review_candidate(job, requirements: list[dict], row) -> dict | None:
    """Asks the LLM to check every (non-years) requirement against one CV.
    Returns {"checks": [...], "summary": "..."} or None if the LLM failed."""
    llm_reqs = [r for r in requirements if r.get("category") != "years"]
    checks = []
    if llm_reqs:
        numbered = "\n".join(f'{i + 1}. [{r["type"]}] {r["requirement"]}' for i, r in enumerate(llm_reqs))
        cv = redact((_clean(row.parsed_text) or "")[:CV_EXCERPT_CHARS], (row.first_name, row.last_name))
        prompt = f"""You check a candidate's CV against the requirements of a job, one by one.

JOB: {job.title}

REQUIREMENTS:
{numbered}

CANDIDATE
Education: {_clean(row.education_level) or 'not stated'}
Past roles: {_clean(row.experience_profile) or 'not stated'}
Skills: {json.dumps(_safe_parse_skills(row.extracted_skills_json))}
CV excerpt:
{cv}

For EACH requirement decide:
- "met": the CV clearly shows it;
- "partial": related or transferable experience, or only mentioned without detail;
- "missing": nothing in the CV supports it.
Be strict: never assume something that is not written. For met and partial, give
the evidence: a short quote or paraphrase from the CV (at most 15 words).
Then write one sentence summarising the fit.

Return ONLY a valid JSON object:
{{"checks": [{{"id": 1, "status": "met", "evidence": "..."}}], "summary": "..."}}"""
        try:
            payload = generate_json(prompt, temperature=0.0)
        except Exception as e:
            log.warning("Review failed for applicant %s: %s", row.applicant_id, e)
            return None
        by_id = {}
        for c in payload.get("checks", []):
            try:
                by_id[int(c.get("id"))] = c
            except (TypeError, ValueError):
                continue
        for i, req in enumerate(llm_reqs):
            c = by_id.get(i + 1, {})
            status = str(c.get("status", "missing")).lower()
            if status not in POINTS:
                status = "missing"
            checks.append({**req, "status": status,
                           "evidence": str(c.get("evidence") or "")[:160] if status != "missing" else ""})
        summary = str(payload.get("summary") or "").strip()
    else:
        summary = ""

    years_req = next((r for r in requirements if r.get("category") == "years"), None)
    if years_req:
        checks.insert(0, _check_years(years_req, row.years_of_experience))
    return {"checks": checks, "summary": summary}


def score_checklist(checks: list[dict]) -> float:
    """met = 1, partial = 0.5, missing = 0, must-haves count double; missing
    must-haves cap the score (60 for one, 40 for two or more)."""
    if not checks:
        return 0.0
    total = sum(WEIGHT[c["type"]] for c in checks)
    got = sum(WEIGHT[c["type"]] * POINTS[c["status"]] for c in checks)
    score = 100.0 * got / total
    missing_musts = sum(1 for c in checks if c["type"] == "must" and c["status"] == "missing")
    if missing_musts == 1:
        score = min(score, CAP_ONE_MUST_MISSING)
    elif missing_musts >= 2:
        score = min(score, CAP_MUSTS_MISSING)
    return round(score, 1)


def _reasoning(checks: list[dict], summary: str) -> str:
    musts = [c for c in checks if c["type"] == "must"]
    nices = [c for c in checks if c["type"] == "nice"]
    met = lambda cs: sum(1 for c in cs if c["status"] == "met")
    parts = [f"Must-haves met: {met(musts)}/{len(musts)}"]
    if nices:
        parts.append(f"nice-to-haves: {met(nices)}/{len(nices)}")
    missing = [c["requirement"] for c in musts if c["status"] == "missing"]
    text_out = ", ".join(parts) + (f"; missing: {', '.join(missing)}" if missing else "") + "."
    return f"{text_out} {summary}".strip()


def _persist(application_id, score: float, reasoning: str, embedding_score: float, checks: list[dict]):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE job_applications
            SET ai_match_score = :score, ai_match_reasoning = :why, ai_embedding_score = :emb,
                ai_match_details = CAST(:details AS jsonb)
            WHERE application_id = :aid
        """), {"score": round(score), "why": reasoning, "emb": embedding_score,
               "details": json.dumps(checks), "aid": application_id})


# ------------------------------------------------------------------ main entry

def match_candidates_to_job(job_id: int, top_k: int = 10, recompute_all: bool = False):
    job = _load_job(job_id)
    if job is None:
        return None
    requirements = get_requirements(job, refresh=recompute_all)

    applicants_df = _fetch_job_applicants(job_id)
    processed = applicants_df[applicants_df["cv_embedding"].notna()].copy()
    unprocessed_ids = applicants_df.loc[applicants_df["cv_embedding"].isna(), "applicant_id"].astype(int).tolist()
    meta = {
        "job_id": job.job_id,
        "job_title": job.title,
        "required_skills": job.required_skills or "",
        "required_experience_years": float(job.required_experience_years)
        if job.required_experience_years is not None else None,
        "requirements": requirements,
        "n_applicants": int(len(applicants_df)),
        "n_processed": int(len(processed)),
        "unprocessed_applicant_ids": unprocessed_ids,
    }
    if processed.empty:
        return {**meta, "candidates": []}

    if recompute_all:
        to_score, already_scored = processed, processed.iloc[0:0]
    else:
        done = processed["ai_match_score"].notna() & processed["ai_match_details"].notna()
        already_scored, to_score = processed[done], processed[~done]

    def base(r):
        years = _clean(r.years_of_experience)
        return {
            "applicant_id": int(r.applicant_id),
            "name": f"{r.first_name} {r.last_name}",
            "education_level": _clean(r.education_level),
            "years_of_experience": float(years) if years is not None else None,
            # a JSON string: that's what the frontend's parseSkills expects
            "skills": json.dumps(_safe_parse_skills(r.extracted_skills_json)),
        }

    candidates = []
    for r in already_scored.itertuples():
        emb = _clean(r.ai_embedding_score)
        details = r.ai_match_details
        candidates.append({
            **base(r),
            "match_score": float(r.ai_match_score),
            "embedding_score": float(emb) if emb is not None else None,
            "ai_reasoning": _clean(r.ai_match_reasoning),
            "requirements": json.loads(details) if isinstance(details, str) else details,
            "reviewed": True,
        })

    if not to_score.empty:
        ids = to_score["applicant_id"].astype(int).tolist()
        raw_sims = _embedding_scores(_job_profile_text(job), ids)
        coverages = _coverage_scores(
            _split_skills(job.required_skills),
            {int(r.applicant_id): _safe_parse_skills(r.extracted_skills_json) for r in to_score.itertuples()},
        )
        roles = _role_relevance(job, {int(r.applicant_id): _clean(r.experience_profile)
                                      for r in to_score.itertuples()})
        emb = {aid: _calibrate_embedding(raw_sims.get(aid, 0.0)) for aid in ids}
        cheap = {aid: _prescreen(coverages.get(aid), roles.get(aid), emb[aid]) for aid in ids}

        # only the most promising candidates get the (slow) LLM review, in parallel
        shortlist = set(sorted(ids, key=lambda a: cheap[a], reverse=True)[:config.MATCH_LLM_MAX])
        rows = {int(r.applicant_id): r for r in to_score.itertuples()}
        with ThreadPoolExecutor(max_workers=max(1, config.MATCH_LLM_WORKERS)) as pool:
            reviews = dict(zip(shortlist, pool.map(lambda a: _review_candidate(job, requirements, rows[a]), shortlist)))

        for aid, r in rows.items():
            review = reviews.get(aid)
            if review:
                score = round(score_checklist(review["checks"]))   # stored as a whole number
                reasoning = _reasoning(review["checks"], review["summary"])
                _persist(r.application_id, score, reasoning, emb[aid], review["checks"])   # cached
                candidates.append({**base(r), "match_score": score, "embedding_score": emb[aid],
                                   "ai_reasoning": reasoning, "requirements": review["checks"], "reviewed": True})
            else:
                why = ("Not reviewed: low pre-screen score." if aid not in shortlist
                       else "The AI review failed; it will be retried on the next search.")
                candidates.append({**base(r), "match_score": cheap[aid], "embedding_score": emb[aid],
                                   "ai_reasoning": why, "requirements": [], "reviewed": False})

    # reviewed candidates first (their score is the checklist), then the pre-screen-only ones
    candidates.sort(key=lambda c: (c["reviewed"], c["match_score"]), reverse=True)
    return {**meta, "candidates": candidates[:top_k]}
