"""
Embedding-based semantic candidate matching. Given a job posting, ranks
applicants by cosine similarity between their profile embedding and the
job's embedding -- both computed with the same model, so they live in
the same vector space. Distinct AI technique from the XGBoost
regressor/classifier used in budget/retention -- this is retrieval, not
prediction.
"""

import pandas as pd
from sqlalchemy import text
from database import engine
from embeddings import embed_text  # same embeddings.py used by the ETL


def match_candidates_to_job(job_id: int, top_k: int = 10):
    with engine.connect() as conn:
        job = conn.execute(
            text("SELECT job_id, title, required_experience_years FROM job_postings WHERE job_id = :jid"),
            {"jid": job_id}
        ).fetchone()

    if job is None:
        return None

    # Build a query profile from the job posting in the same shape of
    # text as the applicant profiles the ETL embeds, so both sides live
    # in the same semantic space.
    job_text = f"{job.title}. Requires {job.required_experience_years or 0} years of experience."
    query_vec = embed_text(job_text)
    query_literal = "[" + ",".join(map(str, query_vec)) + "]"

    # <=> is pgvector's cosine distance operator (0 = identical, 2 = opposite).
    # Convert to a 0-100 similarity score for the frontend.
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
        ORDER BY ac.cv_embedding <=> :qvec
        LIMIT :k
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"qvec": query_literal, "k": top_k})

    return {
        "job_id": job.job_id,
        "job_title": job.title,
        "candidates": [
            {
                "applicant_id": int(r.applicant_id),
                "name": f"{r.first_name} {r.last_name}",
                "education_level": r.education_level,
                "years_of_experience": float(r.years_of_experience) if pd.notna(r.years_of_experience) else None,
                "skills": r.extracted_skills_json,
                "match_score": round(float(r.similarity) * 100, 1),
            }
            for r in df.itertuples()
        ]
    }