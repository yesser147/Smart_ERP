"""
Two-stage candidate matching with score caching, scoped to a job's real
applicants only, using curated/LLM-generated required skills per job title.
"""

import json
import requests
import pandas as pd
from types import SimpleNamespace
from sqlalchemy import text
from database import engine
from embeddings import embed_text

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"
SHORTLIST_MULTIPLIER = 3


def _safe_parse_skills(raw_value):
    """extracted_skills_json is JSONB -- psycopg2 auto-deserializes it to
    a list/dict on read, so json.loads() on it throws TypeError. Tolerate
    both shapes."""
    if raw_value is None:
        return []
    if isinstance(raw_value, (list, dict)):
        return raw_value
    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return []


def _generate_skills_with_llm(job) -> str:
    """Cache-miss fallback: no curated row exists for this title yet, so
    ask the LLM once and cache the result in job_title_skills."""
    ctx = ", ".join(x for x in (job.department_type, job.division_description) if x)
    prompt = f"""List the 8 to 12 most important skills, tools and qualifications
required for the job "{job.title}"{f' in the department: {ctx}' if ctx else ''}.
Return ONLY a valid JSON object: {{"skills": ["skill1", "skill2"]}}"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                  "format": "json", "options": {"temperature": 0.1}},
            timeout=60,
        )
        response.raise_for_status()
        skills = json.loads(response.json()["response"]).get("skills", [])
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
    ctx = ", ".join(x for x in (job.department_type, job.division_description) if x)
    if ctx:
        parts.append(f"Department: {ctx}.")
    return " ".join(parts)


def _fetch_job_applicants(job_id: int) -> pd.DataFrame:
    """Only people who actually applied to this job -- not the whole
    applicant pool."""
    query = text("""
        SELECT
            ja.application_id, ja.ai_match_score,
            a.applicant_id, a.first_name, a.last_name,
            a.education_level, a.years_of_experience,
            ac.extracted_skills_json, ac.cv_embedding
        FROM job_applications ja
        JOIN applicants a ON a.applicant_id = ja.applicant_id
        LEFT JOIN applicant_cvs ac ON ac.applicant_id = a.applicant_id
        WHERE ja.job_id = :jid
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"jid": job_id})


def _embedding_scores(job_text: str, applicant_ids: list) -> dict:
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


def _rerank_with_llm(job, rows: pd.DataFrame) -> dict:
    candidates_payload = [
        {
            "applicant_id": int(row.applicant_id),
            "years_of_experience": float(row.years_of_experience) if pd.notna(row.years_of_experience) else None,
            "education_level": row.education_level,
            "skills": _safe_parse_skills(row.extracted_skills_json),
        }
        for row in rows.itertuples()
    ]

    prompt = f"""You are ranking job candidates for this position:
Title: {job.title}
Required skills: {job.required_skills or 'not specified'}
Required experience: {job.required_experience_years or 0} years

Candidates (JSON):
{json.dumps(candidates_payload, indent=2)}

For each candidate, score 0-100 how well they fit this specific job based on
their actual skills, education, and experience versus the requirements above.
Penalize candidates significantly below the required experience or missing
most required skills. Reward directly relevant skills over generic ones.

Return ONLY a valid JSON object with no other text, in this exact shape:
{{
  "rankings": [
    {{"applicant_id": 123, "score": 82, "reasoning": "one short sentence why"}}
  ]
}}"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                  "format": "json", "options": {"temperature": 0.1}},
            timeout=90,
        )
        response.raise_for_status()
        payload = json.loads(response.json()["response"])
        return {
            int(r["applicant_id"]): {"score": float(r["score"]), "reasoning": r.get("reasoning", "")}
            for r in payload.get("rankings", [])
            if "applicant_id" in r and "score" in r
        }
    except Exception as e:
        print(f"  ⚠️  LLM reranking failed, falling back to embedding-only scores: {e}")
        return {}


def _persist_score(application_id, score: float, reasoning: str = None, embedding_score: float = None):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE job_applications
            SET ai_match_score = :score, ai_match_reasoning = :reasoning, ai_embedding_score = :emb
            WHERE application_id = :aid
        """), {"score": round(score), "reasoning": reasoning, "emb": embedding_score, "aid": application_id})


def _load_cached_scores(job_id: int, top_k: int):
    query = text("""
        SELECT
            a.applicant_id, a.first_name, a.last_name, a.education_level,
            a.years_of_experience, ac.extracted_skills_json,
            ja.ai_match_score, ja.ai_match_reasoning, ja.ai_embedding_score
        FROM job_applications ja
        JOIN applicants a ON a.applicant_id = ja.applicant_id
        LEFT JOIN applicant_cvs ac ON ac.applicant_id = a.applicant_id
        WHERE ja.job_id = :jid
        ORDER BY ja.ai_match_score DESC NULLS LAST
        LIMIT :k
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"jid": job_id, "k": top_k})

    if df.empty or df["ai_match_score"].isna().any():
        return None

    return [
        {
            "applicant_id": int(r.applicant_id),
            "name": f"{r.first_name} {r.last_name}",
            "education_level": r.education_level,
            "years_of_experience": float(r.years_of_experience) if pd.notna(r.years_of_experience) else None,
            "skills": r.extracted_skills_json,
            "match_score": float(r.ai_match_score),
            "embedding_score": float(r.ai_embedding_score) if pd.notna(r.ai_embedding_score) else None,
            "ai_reasoning": r.ai_match_reasoning,
        }
        for r in df.itertuples()
    ]


def match_candidates_to_job(job_id: int, top_k: int = 10, recompute_all: bool = False):
    job = _load_job(job_id)
    if job is None:
        return None

    applicants_df = _fetch_job_applicants(job_id)
    if applicants_df.empty:
        return {"job_id": job.job_id, "job_title": job.title, "candidates": []}

    scorable = applicants_df[applicants_df["cv_embedding"].notna()].copy()

    if recompute_all:
        to_score = scorable
        already_scored = pd.DataFrame(columns=scorable.columns)
    else:
        already_scored = scorable[scorable["ai_match_score"].notna()]
        to_score = scorable[scorable["ai_match_score"].isna()]

    candidates = []

    for r in already_scored.itertuples():
        candidates.append({
            "applicant_id": int(r.applicant_id),
            "name": f"{r.first_name} {r.last_name}",
            "education_level": r.education_level,
            "years_of_experience": float(r.years_of_experience) if pd.notna(r.years_of_experience) else None,
            "skills": r.extracted_skills_json,
            "match_score": float(r.ai_match_score),
            "embedding_score": None,
            "ai_reasoning": None,
        })

    if not to_score.empty:
        job_text = _job_profile_text(job)
        applicant_ids = to_score["applicant_id"].astype(int).tolist()

        embedding_scores = _embedding_scores(job_text, applicant_ids)
        llm_scores = _rerank_with_llm(job, to_score)

        for r in to_score.itertuples():
            applicant_id = int(r.applicant_id)
            embedding_score = embedding_scores.get(applicant_id, 0.0)
            llm_result = llm_scores.get(applicant_id)

            if llm_result:
                final_score = round(0.4 * embedding_score + 0.6 * llm_result["score"], 1)
                reasoning = llm_result["reasoning"]
            else:
                final_score = embedding_score
                reasoning = None

            _persist_score(r.application_id, final_score, reasoning, embedding_score)

            candidates.append({
                "applicant_id": applicant_id,
                "name": f"{r.first_name} {r.last_name}",
                "education_level": r.education_level,
                "years_of_experience": float(r.years_of_experience) if pd.notna(r.years_of_experience) else None,
                "skills": r.extracted_skills_json,
                "match_score": final_score,
                "embedding_score": embedding_score,
                "ai_reasoning": reasoning,
            })

    candidates.sort(key=lambda c: c["match_score"], reverse=True)

    return {"job_id": job.job_id, "job_title": job.title, "candidates": candidates[:top_k]}

