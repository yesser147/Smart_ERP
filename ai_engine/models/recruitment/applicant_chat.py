"""
Multi-turn chat about a specific applicant's fit for a specific job.

The conversation is stored in the ai_chat_messages table, keyed by
(applicant_id, job_id), so it survives an AI engine restart. The grounding
context (CV + job requirements) is rebuilt on every turn from the database,
so it always reflects the latest processed CV; reprocessing a CV clears its
chats (see cv_intelligence_core.write_results).

LLM calls go through llm_client (Groq first, Ollama as fallback).
"""

import json
import re
from sqlalchemy import text
from database import engine
from models.recruitment.matcher import _load_job, _safe_parse_skills
from models.recruitment.llm_client import stream_chat

# system context + the last 12 messages are sent to the LLM
HISTORY_LIMIT = 12

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# phone-like sequences (digits with spaces, dots, dashes, parentheses, leading +);
# only redacted when they hold 9+ digits, so date ranges like "2015 - 2019" stay
_PHONE_RE = re.compile(r"\+?\(?\d[\d\s().-]{7,}\d")


def _redact_phone(match: re.Match) -> str:
    return "[phone]" if sum(c.isdigit() for c in match.group()) >= 9 else match.group()


class ChatError(Exception):
    pass


def _redact(resume_text: str, names: tuple[str, ...] = ()) -> str:
    """The resume may leave the machine (Groq), so strip contact details and
    the candidate's own name."""
    text_out = _PHONE_RE.sub(_redact_phone, _EMAIL_RE.sub("[email]", resume_text))
    for name in names:
        if name and len(name) >= 2:
            text_out = re.sub(r"\b" + re.escape(name) + r"\b", "[name]", text_out, flags=re.IGNORECASE)
    return text_out


def _build_context_block(applicant_id: int, job_id: int) -> str | None:
    """The grounding text sent as the system message: everything the LLM
    needs to know about this candidate and this job."""
    job = _load_job(job_id)
    if job is None:
        return None

    with engine.connect() as conn:
        applicant = conn.execute(text("""
            SELECT a.applicant_id, a.first_name, a.last_name, a.education_level,
                   COALESCE(ac.cv_years_of_experience, a.years_of_experience) AS years_of_experience,
                   ac.extracted_skills_json, ac.experience_profile, ac.parsed_text
            FROM applicants a
            LEFT JOIN applicant_cvs ac ON ac.applicant_id = a.applicant_id
            WHERE a.applicant_id = :aid
        """), {"aid": applicant_id}).fetchone()

    if applicant is None or not applicant.extracted_skills_json:
        return None

    skills = _safe_parse_skills(applicant.extracted_skills_json)

    return f"""You are an HR assistant helping evaluate whether a specific candidate
fits a specific job. Answer every question honestly and specifically, grounded
only in the information below -- never invent details not present here. If
something can't be determined from the CV, say so plainly rather than guessing.

JOB
Title: {job.title}
Required skills: {job.required_skills or 'not specified'}
Required experience: {job.required_experience_years or 0} years

CANDIDATE
Education: {applicant.education_level or 'not specified'}
Years of experience: {applicant.years_of_experience if applicant.years_of_experience is not None else 'not specified'}
Past roles: {applicant.experience_profile or 'not specified'}
Extracted skills: {json.dumps(skills)}
Resume text:
{_redact((applicant.parsed_text or '')[:3000], (applicant.first_name, applicant.last_name))}

From now on, answer the user's questions about this candidate's fit for this
job directly and concisely, in plain text (not JSON) -- this is a conversation,
not a structured report. Reply in the same language the user writes in."""


def get_chat_history(applicant_id: int, job_id: int, limit: int | None = None) -> list[dict]:
    """Visible conversation, oldest first."""
    query = """
        SELECT role, content FROM (
            SELECT id, role, content FROM ai_chat_messages
            WHERE applicant_id = :aid AND job_id = :jid
            ORDER BY id DESC
            {limit}
        ) last ORDER BY id
    """.format(limit="LIMIT :lim" if limit else "")
    params = {"aid": applicant_id, "jid": job_id}
    if limit:
        params["lim"] = limit
    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()
    return [{"role": r.role, "content": r.content} for r in rows]


def _save_turn(applicant_id: int, job_id: int, user_message: str, reply: str) -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO ai_chat_messages (applicant_id, job_id, role, content)
            VALUES (:aid, :jid, 'user', :u), (:aid, :jid, 'assistant', :a)
        """), {"aid": applicant_id, "jid": job_id, "u": user_message, "a": reply})


def reset_chat(applicant_id: int, job_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ai_chat_messages WHERE applicant_id = :aid AND job_id = :jid"),
                     {"aid": applicant_id, "jid": job_id})


def stream_chat_message(applicant_id: int, job_id: int, user_message: str):
    """Returns a generator of text chunks. Raises ChatError / LLMUnavailable
    BEFORE streaming starts, so the endpoint can still return a proper HTTP error.
    The turn is saved only once the stream finishes."""
    context = _build_context_block(applicant_id, job_id)
    if context is None:
        raise ChatError("Candidate or job not found, or the CV has not been processed yet.")

    messages = ([{"role": "system", "content": context}]
                + get_chat_history(applicant_id, job_id, limit=HISTORY_LIMIT)
                + [{"role": "user", "content": user_message}])

    stream = stream_chat(messages, temperature=0.3)
    first = next(stream, None)          # connects here; raises LLMUnavailable if no provider works

    def generate():
        parts = []
        if first is not None:
            parts.append(first)
            yield first
        for chunk in stream:
            parts.append(chunk)
            yield chunk
        _save_turn(applicant_id, job_id, user_message, "".join(parts))

    return generate()
