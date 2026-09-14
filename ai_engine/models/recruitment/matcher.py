"""
Two-stage candidate matching with score caching:
  1. Embedding retrieval (pgvector cosine similarity) narrows the full
     applicant pool down to a shortlist.
  2. LLM reranking (local Ollama llama3.1) scores the shortlist against
     the job's actual requirements.

Scores are persisted onto job_applications.ai_match_score so a page
refresh reads the saved value instead of recomputing everything (which
would mean re-running an LLM call on every load). Pass
force_refresh=True to recompute regardless of cache.
"""

import json
import pandas as pd
from sqlalchemy import text
from database import engine
from embeddings import embed_text
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

SHORTLIST_MULTIPLIER = 3


def _embedding_shortlist(job_text: str, shortlist_size: int) -> pd.DataFrame:
    query_vec = embed_text(job_text)
    query_literal = "[" + ",".join(map(str, query_vec)) + "]"

    query = text("""
        SELECT
            a.applicant_id, a.first_name, a.last_name, a.education_level,
            a.years_of_experience, ac.extracted_skills_json,
            1 - (ac.cv_embedding <=> :qvec) AS similarity
        FROM applicant_cvs ac
        JOIN applicants a ON a.applicant_id = ac.applicant_id
        WHERE ac.cv_embedding IS NOT NULL
        ORDER BY ac.cv_embedding <=> :qvec
        LIMIT :k
    """)

    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"qvec": query_literal, "k": shortlist_size})


def _rerank_with_llm(job_title: str, required_experience: float, shortlist: pd.DataFrame) -> dict:
    candidates_payload = [
        {
            "applicant_id": int(row.applicant_id),
            "years_of_experience": float(row.years_of_experience) if pd.notna(row.years_of_experience) else None,
            "education_level": row.education_level,
            "skills": json.loads(row.extracted_skills_json) if row.extracted_skills_json else [],
        }
        for row in shortlist.itertuples()
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


def _persist_scores(job_id: int, candidates: list):
    """Writes ai_match_score onto job_applications for any candidate who
    has actually applied to this job."""
    with engine.begin() as conn:
        for c in candidates:
            conn.execute(text("""
                UPDATE job_applications
                SET ai_match_score = :score
                WHERE applicant_id = :aid AND job_id = :jid
            """), {"score": round(c["match_score"]), "aid": c["applicant_id"], "jid": job_id})


def _load_cached_scores(job_id: int, top_k: int):
    """Returns cached candidates if every applicant for this job already
    has a saved ai_match_score, else None (meaning: compute fresh)."""
    query = text("""
        SELECT
            a.applicant_id, a.first_name, a.last_name, a.education_level,
            a.years_of_experience, ac.extracted_skills_json, ja.ai_match_score
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
            "embedding_score": None,
            "ai_reasoning": None,
        }
        for r in df.itertuples()
    ]


def match_candidates_to_job(job_id: int, top_k: int = 10, force_refresh: bool = False):
    with engine.connect() as conn:
        job = conn.execute(
            text("SELECT job_id, title, required_experience_years FROM job_postings WHERE job_id = :jid"),
            {"jid": job_id}
        ).fetchone()

    if job is None:
        return None

    if not force_refresh:
        cached = _load_cached_scores(job_id, top_k)
        if cached is not None:
            return {"job_id": job.job_id, "job_title": job.title, "candidates": cached}

    job_text = f"{job.title}. Requires {job.required_experience_years or 0} years of experience."
    shortlist_size = top_k * SHORTLIST_MULTIPLIER
    shortlist = _embedding_shortlist(job_text, shortlist_size)

    if shortlist.empty:
        return {"job_id": job.job_id, "job_title": job.title, "candidates": []}

    llm_scores = _rerank_with_llm(job.title, job.required_experience_years, shortlist)

    candidates = []
    for r in shortlist.itertuples():
        applicant_id = int(r.applicant_id)
        embedding_score = round(float(r.similarity) * 100, 1)

        llm_result = llm_scores.get(applicant_id)
        if llm_result:
            final_score = round(0.4 * embedding_score + 0.6 * llm_result["score"], 1)
            reasoning = llm_result["reasoning"]
        else:
            final_score = embedding_score
            reasoning = None

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
    top_candidates = candidates[:top_k]

    _persist_scores(job_id, top_candidates)

    return {"job_id": job.job_id, "job_title": job.title, "candidates": top_candidates}