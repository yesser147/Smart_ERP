"""
Recruiter tools built on the processed CVs and the LLM:
  - search_cvs:          semantic search across ALL processed CVs (pgvector)
  - job_description:     draft a job posting (description + required skills)
  - interview_questions: questions targeting the gaps between a CV and a job
"""

import json
import logging

import pandas as pd
from sqlalchemy import text

from database import engine
from embeddings import embed_text
from models.recruitment.llm_client import generate_json
from models.recruitment.matcher import _load_job, _safe_parse_skills

log = logging.getLogger(__name__)


# ---------------------------------------------------------------- CV search

def search_cvs(query: str, limit: int = 20) -> list[dict]:
    """Nearest CVs to a free-text query ("Java developer with banking
    experience"). Uses the HNSW index on applicant_cvs.cv_embedding."""
    vector = "[" + ",".join(map(str, embed_text(query))) + "]"
    sql = text("""
        SELECT a.applicant_id, a.first_name, a.last_name, a.email, a.education_level,
               COALESCE(ac.cv_years_of_experience, a.years_of_experience) AS years_of_experience,
               ac.extracted_skills_json, ac.experience_profile,
               1 - (ac.cv_embedding <=> CAST(:q AS vector)) AS similarity,
               (SELECT jp.title FROM job_applications ja JOIN job_postings jp ON jp.job_id = ja.job_id
                 WHERE ja.applicant_id = a.applicant_id ORDER BY ja.application_date DESC LIMIT 1) AS applied_for
        FROM applicant_cvs ac
        JOIN applicants a ON a.applicant_id = ac.applicant_id
        WHERE ac.cv_embedding IS NOT NULL
        ORDER BY ac.cv_embedding <=> CAST(:q AS vector)
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"q": vector, "limit": max(1, min(limit, 100))}).fetchall()

    results = []
    for r in rows:
        results.append({
            "applicant_id": int(r.applicant_id),
            "name": f"{r.first_name} {r.last_name}",
            "education_level": r.education_level,
            "years_of_experience": float(r.years_of_experience) if r.years_of_experience is not None else None,
            "skills": _safe_parse_skills(r.extracted_skills_json)[:12],
            "experience_profile": r.experience_profile,
            "applied_for": r.applied_for,
            # cosine similarity of short queries vs long CVs rarely exceeds ~0.6: rescale for display
            "relevance": round(max(0.0, min(1.0, (float(r.similarity) - 0.1) / 0.5)) * 100, 1),
        })
    return results


# ---------------------------------------------------------------- job description

def job_description(title: str, department: str | None = None,
                    required_experience_years: float | None = None) -> dict:
    """Draft description + required skills. The skills are cached in
    job_title_skills (source 'llm') unless a curated / rule-based row exists."""
    context = ", ".join(x for x in [
        f"department: {department}" if department else "",
        f"required experience: {required_experience_years} years" if required_experience_years else "",
    ] if x)
    prompt = f"""Write a professional job posting for the position "{title}"{f' ({context})' if context else ''}
at Nexus, a pharmaceutical / life-sciences company.

Return ONLY a valid JSON object:
{{
  "description": "About the role (2-3 sentences), then 'Responsibilities:' with 5 bullet lines starting with '- ', then 'Profile:' with 4 bullet lines starting with '- '",
  "skills": ["8 to 12 required skills, tools or qualifications"]
}}"""
    result = generate_json(prompt, temperature=0.4, timeout=90)
    description = str(result.get("description", "")).strip()
    skills = [str(s).strip() for s in result.get("skills", []) if str(s).strip()]

    if skills:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO job_title_skills (title_key, title, skills, source)
                VALUES (:k, :t, :s, 'llm')
                ON CONFLICT (title_key) DO NOTHING
            """), {"k": title.strip().lower(), "t": title.strip(), "s": ", ".join(skills)})
    return {"title": title, "description": description, "skills": skills}


# ---------------------------------------------------------------- interview questions

def interview_questions(applicant_id: int, job_id: int) -> dict | None:
    job = _load_job(job_id)
    if job is None:
        return None
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT a.first_name, ac.extracted_skills_json, ac.experience_profile,
                   COALESCE(ac.cv_years_of_experience, a.years_of_experience) AS years, a.education_level
            FROM applicants a LEFT JOIN applicant_cvs ac ON ac.applicant_id = a.applicant_id
            WHERE a.applicant_id = :aid
        """), {"aid": applicant_id}).fetchone()
    if row is None or row.extracted_skills_json is None:
        return None

    candidate = {
        "skills": _safe_parse_skills(row.extracted_skills_json),
        "past_roles": row.experience_profile,
        "years_of_experience": float(row.years) if row.years is not None else None,
        "education": row.education_level,
    }
    prompt = f"""You are preparing a job interview.
Job: {job.title}. Required skills: {job.required_skills or 'not specified'}.
Required experience: {job.required_experience_years or 0} years.
Candidate (from the CV): {json.dumps(candidate)}

Write 8 interview questions: first the ones that check the GAPS between the candidate and the job
(missing or weak skills, lack of experience in the field), then questions that check the claimed strengths.

Return ONLY a valid JSON object:
{{
  "gaps": ["short list of the main gaps"],
  "questions": [{{"question": "...", "purpose": "what it checks, one short sentence", "type": "gap|strength|behavioral"}}]
}}"""
    result = generate_json(prompt, temperature=0.3, timeout=90)
    questions = [q for q in result.get("questions", []) if isinstance(q, dict) and q.get("question")]
    return {"gaps": result.get("gaps", []), "questions": questions}
