"""
Shared CV intelligence core: the ONE place that talks to the LLM,
normalizes its output, computes the embedding, and writes results back
to applicant_cvs/applicants. Used by both:
  - enrich_cv_intelligence.py (batch, runs over all unprocessed rows)
  - cv_processing.py (single applicant, "Traiter CV" button)
  - reindex_embeddings.py (re-embeds stored CVs via build_cv_embedding_text)

Besides skills/years/education it now extracts an experience profile
(past job titles + industries) and the CV's own total years, so the
matcher can judge background and not just a skills list.
"""

import json
import logging
from sqlalchemy import text
from embeddings import embed_text
from models.recruitment.llm_client import generate_json

log = logging.getLogger(__name__)

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


def _clean_profile(raw) -> "str | None":
    if isinstance(raw, list):
        raw = "; ".join(str(x) for x in raw if x)
    if not raw:
        return None
    return str(raw).strip()[:400] or None


def structure_with_llm(resume_text: str) -> dict:
    """Extracts structured info from resume text with the configured LLM
    (see llm_client). Raises when the LLM is unreachable or keeps returning
    invalid JSON, so a CV is never marked as processed with empty data."""
    prompt = f"""Extract structured information from this resume.

Resume:
{resume_text[:6000]}

Return ONLY a valid JSON object matching this schema, with no other text before or after it:
{{
  "skills": ["skill1", "skill2"],
  "years_of_experience": 5,
  "education_level": "Bachelor's",
  "summary": "Professional summary here",
  "experience_profile": "Accountant (retail banking); Bookkeeper (construction)"
}}

Rules: years_of_experience is the total years of professional work computed from the
job dates in the resume, as a number. experience_profile lists the candidate's real
past job titles (at most 4, newest first), each with its industry in parentheses.
Never invent job titles that are not in the resume."""

    return generate_json(prompt, temperature=0.1, retries=2, timeout=120)


def build_cv_embedding_text(resume_text, skills, years=None, education=None,
                            experience_profile=None) -> str:
    """Most important first: all-MiniLM-L6-v2 only reads ~256 tokens, so
    anything at the end of a long text is silently cut."""
    parts = []
    if skills:
        parts.append("Skills: " + ", ".join(str(s) for s in skills) + ".")
    if experience_profile:
        parts.append(f"Past roles: {experience_profile}.")
    if education:
        parts.append(f"Education: {education}.")
    if years is not None:
        parts.append(f"{years} years of experience.")
    parts.append(resume_text[:1000])
    return " ".join(parts)


def structure_and_embed(resume_text: str) -> dict:
    """The single core step: resume text in, fully normalized structured
    result out (skills, years, education, profile, embedding, summary)."""
    extracted = structure_with_llm(resume_text)

    skills = extracted.get("skills", [])
    if not isinstance(skills, list):
        skills = []

    safe_education = normalize_education_level(extracted.get("education_level"))

    years_exp = extracted.get("years_of_experience")
    if (not isinstance(years_exp, (int, float)) or isinstance(years_exp, bool)
            or not 0 <= years_exp <= 50):
        years_exp = None

    profile = _clean_profile(extracted.get("experience_profile"))

    embedding_text = build_cv_embedding_text(resume_text, skills, years_exp, safe_education, profile)
    vector_literal = "[" + ",".join(map(str, embed_text(embedding_text))) + "]"

    return {
        "skills": skills,
        "skills_json": json.dumps(skills),
        "embedding": vector_literal,
        "years_of_experience": years_exp,
        "education_level": safe_education,
        "experience_profile": profile,
        "summary": str(extracted.get("summary") or ""),
    }


def write_results(conn, applicant_id: int, result: dict):
    """Shared DB write. applicant_cvs gets skills + embedding + profile +
    the CV's own years together; applicants is only backfilled where a
    field is genuinely missing."""
    conn.execute(text("""
        UPDATE applicant_cvs SET
            extracted_skills_json = :skills_json,
            cv_embedding = :embedding,
            experience_profile = :profile,
            cv_years_of_experience = :cv_years
        WHERE applicant_id = :applicant_id
    """), {
        "skills_json": result["skills_json"],
        "embedding": result["embedding"],
        "profile": result["experience_profile"],
        "cv_years": result["years_of_experience"],
        "applicant_id": applicant_id,
    })

    # Candidate chats were grounded in the previous version of this CV
    conn.execute(text("DELETE FROM ai_chat_messages WHERE applicant_id = :aid"),
                 {"aid": applicant_id})

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