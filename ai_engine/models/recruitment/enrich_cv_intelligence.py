"""
Batch CV intelligence: runs structure_and_embed() (the same shared core
cv_processing.py's button uses) over every applicant whose parsed_text
is ready but hasn't been processed yet (cv_embedding IS NULL).
"""

from sqlalchemy import text
from database import engine
from models.recruitment.cv_intelligence_core import structure_and_embed, write_results


def run():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT ac.applicant_id, ac.parsed_text
            FROM applicant_cvs ac
            WHERE ac.parsed_text IS NOT NULL
              AND ac.cv_embedding IS NULL
        """)).fetchall()

    if not rows:
        print("Nothing to process -- either no parsed_text yet, or every row is already done. "
              "Run the reset SQL first if you want to reprocess everything.")
        return

    print(f"Running LLM extraction + embedding for {len(rows)} remaining applicants...")

    processed, skipped = 0, 0

    for i, row in enumerate(rows):
        applicant_id, resume_text = row.applicant_id, row.parsed_text

        try:
            result = structure_and_embed(resume_text)
            with engine.begin() as conn:
                write_results(conn, applicant_id, result)
            processed += 1

        except Exception as e:
            # One bad row no longer kills the whole run -- log it and move
            # on. cv_embedding stays NULL, so it retries next run.
            skipped += 1
            print(f"  ⚠️  Skipped applicant {applicant_id} due to error: {e}")
            continue

        if (i + 1) % 10 == 0 or (i + 1) == len(rows):
            print(f"  Processed {i+1}/{len(rows)} ({processed} succeeded, {skipped} skipped)")

    print(f"Done. {processed} succeeded, {skipped} skipped (will retry automatically next run).")


if __name__ == "__main__":
    run()