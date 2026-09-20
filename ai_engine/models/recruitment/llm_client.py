import os
import requests
import json

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"


class LLMUnavailable(Exception):
    pass


# Env vars are read inside the functions so they work even if load_dotenv()
# runs after this module is imported.
def _groq(messages, json_mode, temperature):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMUnavailable("GROQ_API_KEY manquante")
    body = {
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),  # use the same model as your chatbot
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}   # prompt must mention JSON (yours do)
    r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {key}"}, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _ollama(messages, json_mode, temperature):
    body = {
        "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_ctx": 8192},
    }
    if json_mode:
        body["format"] = "json"
    r = requests.post(OLLAMA_CHAT_URL, json=body, timeout=180)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def chat(messages: list[dict], json_mode: bool = False, temperature: float = 0.3) -> str:
    provider = os.getenv("LLM_PROVIDER", "groq")
    # local-only mode never falls back to the cloud
    order = [_groq, _ollama] if provider == "groq" else [_ollama]
    errors = []
    for fn in order:
        try:
            return fn(messages, json_mode, temperature)
        except Exception as e:
            errors.append(f"{fn.__name__.lstrip('_')}: {e}")
    raise LLMUnavailable(" | ".join(errors))


def generate(prompt: str, json_mode: bool = False, temperature: float = 0.1) -> str:
    return chat([{"role": "user", "content": prompt}], json_mode, temperature)

def _groq_stream(messages, temperature):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMUnavailable("GROQ_API_KEY manquante")
    body = {
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {key}"},
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
        "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature, "num_ctx": 8192},
    }
    r = requests.post(OLLAMA_CHAT_URL, json=body, timeout=180, stream=True)
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
    provider = os.getenv("LLM_PROVIDER", "groq")
    order = [_groq_stream, _ollama_stream] if provider == "groq" else [_ollama_stream]
    errors = []
    for fn in order:
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