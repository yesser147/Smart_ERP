"""
Two-stage candidate matching, scoped to actual applicants of a job:
  1. Embedding retrieval (pgvector cosine similarity) - but ONLY among
     applicants who have a job_applications row for this job_id, not
     the whole applicant pool.
  2. LLM reranking (local Ollama llama3.1) scores that same restricted
     set against the job's actual requirements.

Scores are persisted onto job_applications.ai_match_score. A normal
call only computes scores for applicants who don't have one yet (a
newly-submitted application, or a CV just processed) -- already-scored
applicants are read straight from the cache, no LLM call. Pass
recompute_all=True to force every applicant of this job to be rescored
(e.g. after the job's requirements changed).
"""

import json
import pandas as pd
from sqlalchemy import text
from database import engine
from embeddings import embed_text
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"


def _safe_parse_skills(raw_value):
    """extracted_skills_json is a JSONB column -- psycopg2 auto-
    deserializes it to a list/dict on read, so json.loads() on it
    throws TypeError (not str/bytes). Tolerate both shapes."""
    if raw_value is None:
        return []
    if isinstance(raw_value, (list, dict)):
        return raw_value
    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return []


def _fetch_job_applicants(job_id: int) -> pd.DataFrame:
    """The candidate pool for this job is ONLY people who actually have
    a job_applications row for it -- not the whole applicant table.
    This is the fix for candidates showing up who never applied."""
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
    """Cosine similarity, restricted to the given applicant_ids only."""
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


def _rerank_with_llm(job_title: str, required_experience: float, rows: pd.DataFrame) -> dict:
    """Only called on the subset of applicants that actually need
    scoring -- never the whole table."""
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
Title: {job_title}
Required experience: {required_experience or 0} years

Candidates (JSON):
{json.dumps(candidates_payload, indent=2)}

For each candidate, score 0-100 how well they fit this specific job based on
their actual skills, education, and experience versus the requirements above.
Penalize candidates significantly below the required experience. Reward
directly relevant skills over generic ones.

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


def _persist_score(application_id, score: float):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE job_applications SET ai_match_score = :score
            WHERE application_id = :aid
        """), {"score": round(score), "aid": application_id})


def match_candidates_to_job(job_id: int, top_k: int = 10, recompute_all: bool = False):
    with engine.connect() as conn:
        job = conn.execute(
            text("SELECT job_id, title, required_experience_years FROM job_postings WHERE job_id = :jid"),
            {"jid": job_id}
        ).fetchone()

    if job is None:
        return None

    applicants_df = _fetch_job_applicants(job_id)
    if applicants_df.empty:
        return {"job_id": job.job_id, "job_title": job.title, "candidates": []}

    # Anyone with no CV embedding yet can't be scored at all -- skip them
    # (they'll appear once "Traiter CV" runs for them).
    scorable = applicants_df[applicants_df["cv_embedding"].notna()].copy()

    if recompute_all:
        to_score = scorable
        already_scored = pd.DataFrame(columns=scorable.columns)
    else:
        already_scored = scorable[scorable["ai_match_score"].notna()]
        to_score = scorable[scorable["ai_match_score"].isna()]

    candidates = []

    # Reuse cached scores as-is -- no LLM call for these.
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

    # Only the genuinely new/unscored applicants trigger embedding +
    # LLM work -- this is what stops re-running the LLM on every load.
    if not to_score.empty:
        job_text = f"{job.title}. Requires {job.required_experience_years or 0} years of experience."
        applicant_ids = to_score["applicant_id"].astype(int).tolist()

        embedding_scores = _embedding_scores(job_text, applicant_ids)
        llm_scores = _rerank_with_llm(job.title, job.required_experience_years, to_score)

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

            _persist_score(r.application_id, final_score)

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