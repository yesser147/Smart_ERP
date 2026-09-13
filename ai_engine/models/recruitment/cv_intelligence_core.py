"""
Shared CV intelligence core: the ONE place that talks to the LLM,
normalizes its output, computes the embedding, and writes results back
to applicant_cvs/applicants. Used by both:
  - enrich_cv_intelligence.py (batch, runs over all unprocessed rows)
  - cv_processing.py (single applicant, triggered by the "Traiter CV"
    button -- text extraction from a freshly uploaded PDF happens there,
    then it calls into this module for the actual skills/embedding step)

Keeping this in one place means pressing the button and running the
batch script always produce identical results, and a fix here (like the
education_level truncation guard) applies everywhere at once.
"""

import json
import time
import requests
from sqlalchemy import text
from embeddings import embed_text

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

# employees/applicants.education_level is VARCHAR(100) in schema.sql --
# llama3.1 sometimes ignores the enum instruction and dumps a whole
# certificate list instead. Normalize to one of these labels; anything
# unrecognized is rejected rather than truncated, since a truncated
# certificate list is still garbage, just shorter garbage.
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
    if len(value) > 40:
        return None
    lower = value.lower()
    for keyword, label in EDUCATION_KEYWORDS.items():
        if keyword in lower:
            return label
    return "Other"


def structure_with_llm(resume_text: str, retries: int = 5) -> dict:
    """Extracts structured skills/experience/education from resume text
    using a local Ollama model. Retries on connection issues or
    malformed JSON; returns an empty structure after exhausting retries
    so callers never crash on a bad LLM response."""
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

    for attempt in range(retries):
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
            return json.loads(response.json()["response"])

        except requests.exceptions.ConnectionError:
            print(f" 🔌 Can't reach Ollama at {OLLAMA_URL} -- is `ollama serve` running? Retrying in 5 seconds...")
            time.sleep(5)
        except json.JSONDecodeError as e:
            print(f" ⚠️  Model returned invalid JSON on attempt {attempt + 1}: {e}. Retrying...")
            time.sleep(2)
        except Exception as e:
            print(f" 🔌 Error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

    print(" ❌ Failed after retries. Returning empty data.")
    return {"skills": [], "years_of_experience": None, "education_level": None, "summary": ""}


def structure_and_embed(resume_text: str) -> dict:
    """The single core step: resume text in, fully normalized structured
    result out (skills, years, education, embedding vector, summary).
    Guaranteed to always include the skills extraction -- there is no
    code path that produces an embedding without also running this."""
    extracted = structure_with_llm(resume_text)

    skills = extracted.get("skills", [])
    if not isinstance(skills, list):
        skills = []

    embedding_text = f"{resume_text[:2000]} Skills: {', '.join(str(s) for s in skills)}."
    vector_literal = "[" + ",".join(map(str, embed_text(embedding_text))) + "]"

    safe_education = normalize_education_level(extracted.get("education_level"))

    years_exp = extracted.get("years_of_experience")
    if not isinstance(years_exp, (int, float)):
        years_exp = None

    return {
        "skills": skills,
        "skills_json": json.dumps(skills),
        "embedding": vector_literal,
        "years_of_experience": years_exp,
        "education_level": safe_education,
        "summary": extracted.get("summary", ""),
    }


def write_results(conn, applicant_id: int, result: dict):
    """Shared DB write: applicant_cvs always gets skills+embedding
    together (never one without the other), and applicants only gets
    backfilled where a field is genuinely missing -- never overwrites
    real Kaggle/user-submitted data with an LLM guess."""
    conn.execute(text("""
        UPDATE applicant_cvs SET
            extracted_skills_json = :skills_json,
            cv_embedding = :embedding
        WHERE applicant_id = :applicant_id
    """), {
        "skills_json": result["skills_json"],
        "embedding": result["embedding"],
        "applicant_id": applicant_id,
    })

    if result["years_of_experience"] is not None:
        conn.execute(text("""
            UPDATE applicants SET years_of_experience = :yoe
            WHERE applicant_id = :aid AND years_of_experience IS NULL
        """), {"yoe": result["years_of_experience"], "aid": applicant_id})

    if result["education_level"]:
        conn.execute(text("""
            UPDATE applicants SET education_level = :edu
            WHERE applicant_id = :aid AND education_level IS NULL
        """), {"edu": result["education_level"], "aid": applicant_id})