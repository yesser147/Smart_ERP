"""Removes personal details from CV text before it is sent to an LLM
(Groq is a cloud service). Used by the candidate chat and the matcher."""

import re

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# phone-like sequences (digits with spaces, dots, dashes, parentheses, leading +);
# only redacted when they hold 9+ digits, so date ranges like "2015 - 2019" stay
_PHONE_RE = re.compile(r"\+?\(?\d[\d\s().-]{7,}\d")


def _redact_phone(match: re.Match) -> str:
    return "[phone]" if sum(c.isdigit() for c in match.group()) >= 9 else match.group()


def redact(resume_text: str, names: tuple[str, ...] = ()) -> str:
    """Strips e-mail addresses, phone numbers and the candidate's own name."""
    text_out = _PHONE_RE.sub(_redact_phone, _EMAIL_RE.sub("[email]", resume_text or ""))
    for name in names:
        if name and len(name) >= 2:
            text_out = re.sub(r"\b" + re.escape(name) + r"\b", "[name]", text_out, flags=re.IGNORECASE)
    return text_out
