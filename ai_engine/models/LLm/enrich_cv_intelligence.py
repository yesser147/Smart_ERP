import json
import time
import requests
from sqlalchemy import text

from database import engine
from embeddings import embed_text

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

# employees/applicants.education_level is VARCHAR(100) in schema.sql --
# llama3.1 sometimes ignores the enum instruction and dumps a whole
# certificate list instead (that's what crashed the run at applicant
# 1085). Normalize to one of these labels; anything unrecognized is
# rejected rather than truncated, since a truncated certificate list is
# still garbage, just shorter garbage.
ALLOWED_EDUCATION_LEVELS = ["High School", "Associate's", "Bachelor's", "Master's", "PhD", "Other"]
EDUCATION_KEYWORDS = {
    "high school": "High School",
    "associate": "Associate's",
    "bachelor": "Bachelor's",
    "master": "Master's",
    "phd": "PhD",
    "doctorate": "PhD",
}


def normalize_education_level(raw_value):
    """Returns a safe value to write, or None to skip the update entirely
    if the LLM's output can't be trusted (too long, unrecognized)."""
    if not raw_value:
        return None
    value = str(raw_value).strip()

    # A real label is short. Anything this long is a certificate dump,
    # a sentence, or similar noise -- reject outright rather than
    # truncate, since a truncated version is still not a real label.
    if len(value) > 40:
        return None

    lower = value.lower()
    for keyword, label in EDUCATION_KEYWORDS.items():
        if keyword in lower:
            return label

    return "Other" if len(value) <= 40 else None


def extract_with_llm(resume_text: str) -> dict:
    """Extracts structured information from resume text using a local
    Ollama model -- no API key, no rate limit, no token quota."""
    prompt = f"""Extract structured information from this resume.

Resume:
{resume_text[:6000]}

Return ONLY a valid JSON object matching this schema, with no other text before or after it:
{{
  "skills": ["skill1", "skill2"],
  "years_of_experience": 5,
  "education_level": "Bachelor's",
  "summary": "Professional summary here"
}}"""

    for attempt in range(5):
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
                timeout=120,
            )
            response.raise_for_status()
            raw_text = response.json()["response"]
            return json.loads(raw_text)

        except requests.exceptions.ConnectionError:
            print(f" 🔌 Can't reach Ollama at {OLLAMA_URL} -- is `ollama serve` running? Retrying in 5 seconds...")
            time.sleep(5)
        except json.JSONDecodeError as e:
            print(f" ⚠️  Model returned invalid JSON on attempt {attempt + 1}: {e}. Retrying...")
            time.sleep(2)
        except Exception as e:
            print(f" 🔌 Error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

    print(" ❌ Failed after 5 retries. Returning empty data.")
    return {"skills": [], "years_of_experience": None, "education_level": None, "summary": ""}


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
            extracted = extract_with_llm(resume_text)

            skills = extracted.get("skills", [])
            if not isinstance(skills, list):
                skills = []

            embedding_text = f"{resume_text[:2000]} Skills: {', '.join(str(s) for s in skills)}."
            vector_literal = "[" + ",".join(map(str, embed_text(embedding_text))) + "]"

            safe_education = normalize_education_level(extracted.get("education_level"))

            years_exp = extracted.get("years_of_experience")
            if not isinstance(years_exp, (int, float)):
                years_exp = None

            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE applicant_cvs SET
                        extracted_skills_json = :skills_json,
                        cv_embedding = :embedding
                    WHERE applicant_id = :applicant_id
                """), {
                    "skills_json": json.dumps(skills),
                    "embedding": vector_literal,
                    "applicant_id": applicant_id,
                })

                if years_exp is not None:
                    conn.execute(text("""
                        UPDATE applicants SET years_of_experience = :yoe
                        WHERE applicant_id = :aid AND years_of_experience IS NULL
                    """), {"yoe": years_exp, "aid": applicant_id})

                if safe_education:
                    conn.execute(text("""
                        UPDATE applicants SET education_level = :edu
                        WHERE applicant_id = :aid AND education_level IS NULL
                    """), {"edu": safe_education, "aid": applicant_id})

            processed += 1

        except Exception as e:
            # One bad row (malformed LLM output, a DB constraint, whatever)
            # no longer kills the whole run -- log it and move on. Since
            # cv_embedding stays NULL for this applicant, it will be
            # retried automatically the next time this script runs.
            skipped += 1
            print(f"  ⚠️  Skipped applicant {applicant_id} due to error: {e}")
            continue

        if (i + 1) % 10 == 0 or (i + 1) == len(rows):
            print(f"  Processed {i+1}/{len(rows)} ({processed} succeeded, {skipped} skipped)")

    print(f"Done. {processed} succeeded, {skipped} skipped (will retry automatically next run).")


if __name__ == "__main__":
    run()