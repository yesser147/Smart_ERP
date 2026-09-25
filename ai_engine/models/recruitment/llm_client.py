"""
The ONE place that calls an LLM. Every AI feature (chatbot, CV reading,
matching, candidate chat, retention strategy, budget memo) goes through it,
so the provider, model and timeouts are configured once in .env:

    LLM_PROVIDER=groq    Groq first, local Ollama as fallback
    LLM_PROVIDER=ollama  local only: no data leaves the machine
"""

import json
import logging

import requests

import config

log = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMUnavailable(Exception):
    pass


def _ollama_chat_url():
    return f"{config.OLLAMA_URL.rstrip('/')}/api/chat"


def _groq(messages, json_mode, temperature, max_tokens, timeout):
    if not config.GROQ_API_KEY:
        raise LLMUnavailable("GROQ_API_KEY is not set")
    body = {
        "model": config.GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        body["max_tokens"] = max_tokens
    if json_mode:
        body["response_format"] = {"type": "json_object"}   # prompts must mention JSON (they do)
    r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
                      json=body, timeout=timeout)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _ollama(messages, json_mode, temperature, max_tokens, timeout):
    options = {"temperature": temperature, "num_ctx": 8192}
    if max_tokens:
        options["num_predict"] = max_tokens
    body = {
        "model": config.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": options,
    }
    if json_mode:
        body["format"] = "json"
    r = requests.post(_ollama_chat_url(), json=body, timeout=max(timeout, 180))
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def _providers(groq_fn, ollama_fn):
    # local-only mode never falls back to the cloud
    return [groq_fn, ollama_fn] if config.LLM_PROVIDER == "groq" else [ollama_fn]


def chat(messages: list[dict], json_mode: bool = False, temperature: float = 0.3,
         max_tokens: int | None = None, timeout: float = 60) -> str:
    errors = []
    for fn in _providers(_groq, _ollama):
        try:
            return fn(messages, json_mode, temperature, max_tokens, timeout)
        except Exception as e:
            errors.append(f"{fn.__name__.lstrip('_')}: {e}")
    raise LLMUnavailable(" | ".join(errors))


def generate(prompt: str, json_mode: bool = False, temperature: float = 0.1,
             max_tokens: int | None = None, timeout: float = 60) -> str:
    return chat([{"role": "user", "content": prompt}], json_mode, temperature, max_tokens, timeout)


def generate_json(prompt: str, temperature: float = 0.1, retries: int = 2, **kwargs) -> dict:
    """generate() in JSON mode, parsed. Retries when the model returns
    invalid JSON; raises LLMUnavailable / ValueError when it keeps failing."""
    last_error = None
    for attempt in range(retries + 1):
        raw = generate(prompt, json_mode=True, temperature=temperature, **kwargs)
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return payload
            last_error = ValueError("the model returned JSON that is not an object")
        except json.JSONDecodeError as e:
            last_error = e
        log.warning("LLM returned invalid JSON (attempt %d/%d): %s", attempt + 1, retries + 1, last_error)
    raise ValueError(f"invalid JSON from the LLM: {last_error}")


def _groq_stream(messages, temperature):
    if not config.GROQ_API_KEY:
        raise LLMUnavailable("GROQ_API_KEY is not set")
    body = {
        "model": config.GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
                      json=body, timeout=60, stream=True)
    r.raise_for_status()
    r.encoding = "utf-8"
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        delta = json.loads(data)["choices"][0]["delta"].get("content")
        if delta:
            yield delta


def _ollama_stream(messages, temperature):
    body = {
        "model": config.OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature, "num_ctx": 8192},
    }
    r = requests.post(_ollama_chat_url(), json=body, timeout=180, stream=True)
    r.raise_for_status()
    r.encoding = "utf-8"
    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue
        obj = json.loads(line)
        piece = obj.get("message", {}).get("content")
        if piece:
            yield piece
        if obj.get("done"):
            break


def stream_chat(messages: list[dict], temperature: float = 0.3):
    """Yields text chunks. Provider fallback only happens before the first chunk,
    so connection errors surface before any output is sent."""
    errors = []
    for fn in _providers(_groq_stream, _ollama_stream):
        gen = fn(messages, temperature)
        try:
            first = next(gen)
        except StopIteration:
            return
        except Exception as e:
            errors.append(f"{fn.__name__.strip('_')}: {e}")
            continue
        yield first
        yield from gen
        return
    raise LLMUnavailable(" | ".join(errors))
