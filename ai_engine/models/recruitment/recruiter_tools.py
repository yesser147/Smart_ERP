"""
Recruiter tools built on the processed CVs and the LLM:
  - search_cvs:          semantic search across ALL processed CVs (pgvector)
  - job_description:     draft a job posting (description + required skills)
  - interview_questions: questions targeting the gaps between a CV and a job
"""

import json
import logging
import re

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
                    required_experience_years: float | None = None,
                    team: str | None = None, notes: str | None = None) -> dict:
    """The job posting is always written by the AI, so it is clean and uses the right skills.

    - a title already known (job_title_skills) keeps its skills: the text is written around
      them, so every opening of the same job is screened the same way;
    - a new title gets 8-12 skills from the AI, saved for the next openings;
    - HR's own notes (optional, even messy) are rewritten into the text, never pasted."""
    key = title.strip().lower()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT skills FROM job_title_skills WHERE title_key = :k"), {"k": key}).fetchone()
    known_skills = [s.strip() for s in str(row.skills).split(",") if s.strip()] if row else []

    context = ", ".join(x for x in [
        f"department: {department}" if department else "",
        f"team: {team}" if team else "",
        f"required experience: {required_experience_years:g} years" if required_experience_years else "",
    ] if x)
    if known_skills:
        skills_rule = (f"The required skills of this job are fixed: {', '.join(known_skills)}. "
                       "The 'Profile' bullets must cover them; return exactly this list as \"skills\".")
    else:
        skills_rule = "List 8 to 12 required skills, tools or qualifications as \"skills\" (short labels)."
    notes_rule = (f"\nNotes from HR, possibly messy or with typos (include their content, rewritten correctly; "
                  f"ignore anything unrelated to the job): {notes.strip()}\n") if notes and notes.strip() else ""
    prompt = f"""Write a professional job posting for the position "{title}"{f' ({context})' if context else ''}
at Nexus, a pharmaceutical / life-sciences company.
{notes_rule}
- Correct, professional English, no spelling or grammar mistakes, no placeholders like [Company].
- Use only the facts given above. Never say who the role reports to, and never invent benefits,
  salary, team size or location.
- If a required experience is given, state it in the Profile.
- {skills_rule}

Return ONLY a valid JSON object:
{{
  "description": "About the role (2-3 sentences), then 'Responsibilities:' with 5 bullet lines starting with '- ', then 'Profile:' with 4 to 6 bullet lines starting with '- '",
  "skills": ["..."]
}}"""
    result = generate_json(prompt, temperature=0.3, timeout=90)
    description = str(result.get("description", "")).strip()
    if not description:
        raise ValueError("The AI returned an empty description.")
    # always the same layout: a blank line before each section title
    description = re.sub(r"\s*\b(Responsibilities|Profile):\s*", r"\n\n\1:\n", description).strip()
    description = re.sub(r"^About the role:\s*", "", description)

    if known_skills:
        skills = known_skills
    else:
        skills = [str(s).strip() for s in result.get("skills", []) if str(s).strip()][:12]
        if skills:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO job_title_skills (title_key, title, skills, source)
                    VALUES (:k, :t, :s, 'llm')
                    ON CONFLICT (title_key) DO NOTHING
                """), {"k": key, "t": title.strip(), "s": ", ".join(skills)})
    return {"title": title, "description": description, "skills": skills, "known_title": bool(known_skills)}


# ---------------------------------------------------------------- interview questions

def interview_questions(applicant_id: int, job_id: int) -> dict | None:
    job = _load_job(job_id)
    if job is None:
        return None
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT a.first_name, ac.extracted_skills_json, ac.experience_profile,
                   COALESCE(ac.cv_years_of_experience, a.years_of_experience) AS years, a.education_level,
                   (SELECT ja.ai_match_details FROM job_applications ja
                     WHERE ja.applicant_id = a.applicant_id AND ja.job_id = :jid) AS checklist
            FROM applicants a LEFT JOIN applicant_cvs ac ON ac.applicant_id = a.applicant_id
            WHERE a.applicant_id = :aid
        """), {"aid": applicant_id, "jid": job_id}).fetchone()
    if row is None or row.extracted_skills_json is None:
        return None

    candidate = {
        "skills": _safe_parse_skills(row.extracted_skills_json),
        "past_roles": row.experience_profile,
        "years_of_experience": float(row.years) if row.years is not None else None,
        "education": row.education_level,
    }
    # the screening checklist, when the candidate has been ranked: the gaps are then
    # exactly the requirements found missing or partial
    checklist = row.checklist if isinstance(row.checklist, list) else (json.loads(row.checklist) if row.checklist else None)
    checklist_text = ""
    if checklist:
        lines = [f"- [{c['type']}] {c['requirement']}: {c['status']}" + (f" ({c['evidence']})" if c.get("evidence") else "")
                 for c in checklist]
        checklist_text = "Screening checklist (requirement: status):\n" + "\n".join(lines) + "\n"
    prompt = f"""You are preparing a job interview.
Job: {job.title}. Required skills: {job.required_skills or 'not specified'}.
Required experience: {job.required_experience_years or 0} years.
Candidate (from the CV): {json.dumps(candidate)}
{checklist_text}
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
