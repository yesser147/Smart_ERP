"""
Two-stage candidate matching:
  1. Embedding retrieval (pgvector cosine similarity) narrows the full
     applicant pool down to a manageable shortlist -- fast, scales to
     thousands of applicants.
  2. LLM reranking (local Ollama llama3.1) reads each shortlisted
     candidate's real extracted skills/experience/education against the
     job's actual requirements and produces a reasoned score + one-line
     justification -- something cosine similarity alone can't do (it
     can't tell you a candidate is a great semantic match but missing a
     hard requirement like years of experience).

Stage 2 only runs on the shortlist, not the whole applicant pool, so a
handful of local LLM calls per search stays fast enough for interactive
use.
"""

import json
import time
import pandas as pd
import requests
from sqlalchemy import text
from database import engine
from embeddings import embed_text

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

SHORTLIST_MULTIPLIER = 3  # retrieve top_k * this many candidates for the LLM to rerank


def _embedding_shortlist(job_text: str, shortlist_size: int) -> pd.DataFrame:
    """Stage 1: fast semantic retrieval via pgvector cosine similarity."""
    query_vec = embed_text(job_text)
    query_literal = "[" + ",".join(map(str, query_vec)) + "]"

    query = text("""
        SELECT
            a.applicant_id,
            a.first_name,
            a.last_name,
            a.education_level,
            a.years_of_experience,
            ac.extracted_skills_json,
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
    """Stage 2: asks llama3.1 to score and justify each shortlisted
    candidate against the job's actual requirements. Returns
    {applicant_id: {"score": 0-100, "reasoning": "..."}}; falls back to
    an empty dict (pure embedding score used instead) on any failure, so
    a local LLM hiccup never breaks the whole match request."""
    candidates_payload = [
        {
            "applicant_id": int(row.applicant_id),
            "years_of_experience": float(row.years_of_experience) if pd.notna(row.years_of_experience) else None,
            "education_level": row.education_level,
            "skills": _parse_skills(row.extracted_skills_json),
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
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1},
            },
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
def _parse_skills(value):
    """JSONB columns come back already-parsed (list/dict) via
    psycopg2/SQLAlchemy -- json.loads() on that raises 'the JSON object
    must be str, bytes or bytearray, not list'. Only parse if it's
    genuinely still a string."""
    if not value:
        return []
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return []

def match_candidates_to_job(job_id: int, top_k: int = 10):
    with engine.connect() as conn:
        job = conn.execute(
            text("SELECT job_id, title, required_experience_years FROM job_postings WHERE job_id = :jid"),
            {"jid": job_id}
        ).fetchone()

    if job is None:
        return None

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
            # Blend: LLM reasoning carries more weight since it actually
            # checks hard requirements (experience threshold, specific
            # skills) that raw cosine similarity can miss entirely.
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

    return {
        "job_id": job.job_id,
        "job_title": job.title,
        "candidates": candidates[:top_k],
    }