"""
Multi-turn chat about a specific applicant's fit for a specific job.
Keeps conversation history server-side, keyed by (applicant_id, job_id),
so the LLM has the candidate's resume/skills and the job's requirements
as grounding on every turn without the frontend needing to resend them.

LLM calls go through llm_client (Groq first, Ollama as fallback).
"""

import json
import re
from sqlalchemy import text
from database import engine
from models.recruitment.matcher import _load_job, _safe_parse_skills
from models.recruitment.llm_client import chat, stream_chat, LLMUnavailable

# In-memory session store: {(applicant_id, job_id): [{"role": ..., "content": ...}, ...]}
# Resets on server restart -- fine for a demo/school project. If you ever
# need this to survive restarts, swap this dict for a DB table keyed the
# same way.
_SESSIONS: dict[tuple[int, int], list[dict]] = {}

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def _redact(resume_text: str) -> str:
    """The resume may leave the machine (Groq), so strip email addresses."""
    return _EMAIL_RE.sub("[email]", resume_text)


def _build_context_block(applicant_id: int, job_id: int) -> str | None:
    """The grounding text injected as the first message of a new session --
    everything the LLM needs to know about this specific candidate and
    this specific job, so the user's questions don't need to repeat it."""
    job = _load_job(job_id)
    if job is None:
        return None

    with engine.connect() as conn:
           applicant = conn.execute(text("""
            SELECT a.applicant_id, a.education_level,
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
Extracted skills: {json.dumps(skills)}
Resume text:
{_redact((applicant.parsed_text or '')[:3000])}

From now on, answer the user's questions about this candidate's fit for this
job directly and concisely, in plain text (not JSON) -- this is a conversation,
not a structured report. Reply in the same language the user writes in."""


def start_or_continue_chat(applicant_id: int, job_id: int, user_message: str) -> dict:
    """Sends one user message and returns the assistant's reply, creating
    the session (with grounding context) on first use."""
    session_key = (applicant_id, job_id)

    if session_key not in _SESSIONS:
        context = _build_context_block(applicant_id, job_id)
        if context is None:
            return {"status": "error", "message": "Candidat ou poste introuvable, ou CV non traité."}
        _SESSIONS[session_key] = [{"role": "system", "content": context}]

    history = _SESSIONS[session_key]
    history.append({"role": "user", "content": user_message})

    try:
        reply = chat(history, temperature=0.3)
    except LLMUnavailable as e:
        history.pop()  # don't keep a user message that never got a real reply
        return {"status": "error", "message": f"IA indisponible : {e}"}
    except Exception as e:
        history.pop()
        return {"status": "error", "message": f"Échec de la réponse IA: {e}"}

    history.append({"role": "assistant", "content": reply})

    # Keep sessions from growing unbounded across a long conversation --
    # system context + last 12 turns is plenty for this use case.
    if len(history) > 13:
        _SESSIONS[session_key] = [history[0]] + history[-12:]

    return {"status": "success", "reply": reply}


def get_chat_history(applicant_id: int, job_id: int) -> list[dict]:
    """Returns the visible conversation (system context excluded) so the
    frontend can render it after a page refresh within the same server
    session, or when reopening the chat panel."""
    history = _SESSIONS.get((applicant_id, job_id), [])
    return [m for m in history if m["role"] != "system"]


def reset_chat(applicant_id: int, job_id: int) -> None:
    _SESSIONS.pop((applicant_id, job_id), None)

class ChatError(Exception):
    pass


def stream_chat_message(applicant_id: int, job_id: int, user_message: str):
    """Returns a generator of text chunks. Raises ChatError / LLMUnavailable
    BEFORE streaming starts, so the endpoint can still return a proper HTTP error.
    The turn is saved to history only once the stream finishes."""
    session_key = (applicant_id, job_id)

    if session_key not in _SESSIONS:
        context = _build_context_block(applicant_id, job_id)
        if context is None:
            raise ChatError("Candidat ou poste introuvable, ou CV non traité.")
        _SESSIONS[session_key] = [{"role": "system", "content": context}]

    history = _SESSIONS[session_key]
    pending = history + [{"role": "user", "content": user_message}]

    stream = stream_chat(pending, temperature=0.3)
    first = next(stream, None)          # connects here; raises LLMUnavailable if no provider works

    def generate():
        parts = []
        if first is not None:
            parts.append(first)
            yield first
        for chunk in stream:
            parts.append(chunk)
            yield chunk
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": "".join(parts)})
        if len(history) > 13:
            _SESSIONS[session_key] = [history[0]] + history[-12:]

    return generate()