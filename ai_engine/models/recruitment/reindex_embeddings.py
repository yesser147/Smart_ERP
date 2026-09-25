"""
Re-embeds every processed CV with the skills-first text format, WITHOUT
re-running the LLM (skills are already stored), then resets cached match
scores so they get recomputed with the new logic.
"""

import json
from sqlalchemy import text
from database import engine
from embeddings import get_model
from models.recruitment.cv_intelligence_core import build_cv_embedding_text

BATCH = 64


def _parse_skills(raw):
    if raw is None:
        return []
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []


def run():
    # (the matcher's columns are created by the backend migration V2__bug_fixes.sql)
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT ac.applicant_id, ac.parsed_text, ac.extracted_skills_json,
                   ac.experience_profile,
                   COALESCE(ac.cv_years_of_experience, a.years_of_experience) AS years_of_experience,
                   a.education_level
            FROM applicant_cvs ac
            JOIN applicants a ON a.applicant_id = ac.applicant_id
            WHERE ac.parsed_text IS NOT NULL
              AND ac.extracted_skills_json IS NOT NULL
        """)).fetchall()

    if not rows:
        print("Nothing to re-embed (no processed CVs found).")
        return

    print(f"Re-embedding {len(rows)} CVs...")
    model = get_model()

    for start in range(0, len(rows), BATCH):
        chunk = rows[start:start + BATCH]
        texts = [
            # same text format as cv_intelligence_core, past roles included
            build_cv_embedding_text(
                r.parsed_text,
                _parse_skills(r.extracted_skills_json),
                r.years_of_experience,
                r.education_level,
                r.experience_profile,
            )
            for r in chunk
        ]
        vectors = model.encode(texts, normalize_embeddings=True)
        params = [
            {"v": "[" + ",".join(map(str, vec.tolist())) + "]", "aid": r.applicant_id}
            for r, vec in zip(chunk, vectors)
        ]
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE applicant_cvs SET cv_embedding = :v WHERE applicant_id = :aid"),
                params,
            )
        print(f"  {min(start + BATCH, len(rows))}/{len(rows)}")

    # cached scores were computed with the old embeddings/logic
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE job_applications
            SET ai_match_score = NULL, ai_match_reasoning = NULL, ai_embedding_score = NULL
        """))

    print("Done. All match scores reset -- press Search on each job to recompute.")


if __name__ == "__main__":
    run()