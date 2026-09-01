from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi4-mini:latest")
_AVAILABILITY_TIMEOUT = 2
_GENERATE_TIMEOUT = 30


class OllamaUnavailable(Exception):
    """Raised when Ollama can't be reached, times out, or returns unusable output.

    Callers are expected to catch this and fall back to the deterministic
    rule-based path -- an LLM being down should degrade the pipeline, not break it.
    """


def is_available(host: str = OLLAMA_HOST) -> bool:
    try:
        req = urllib.request.Request(f"{host}/api/tags")
        with urllib.request.urlopen(req, timeout=_AVAILABILITY_TIMEOUT) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def generate_json(
    prompt: str,
    *,
    model: str | None = None,
    host: str | None = None,
    timeout: int = _GENERATE_TIMEOUT,
) -> dict:
    """Call Ollama's generate endpoint with a JSON-format constraint and return the
    parsed object. Raises OllamaUnavailable on any connection, timeout, or parse
    failure so callers can fall back cleanly.
    """
    payload = {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1},
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{host or OLLAMA_HOST}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        raise OllamaUnavailable(f"Ollama request failed: {exc}") from exc

    text = raw.get("response", "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise OllamaUnavailable(f"Ollama returned non-JSON output: {text[:200]!r}") from exc

    if not isinstance(parsed, dict):
        raise OllamaUnavailable(f"Ollama returned a non-object JSON value: {parsed!r}")
    return parsed
