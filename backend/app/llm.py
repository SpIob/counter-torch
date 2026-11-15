"""Optional OpenAI-compatible client. Configured only by LLM_BASE_URL, LLM_API_KEY, LLM_MODEL.
LLM_MODE=offline (or no base URL) serves deterministic template answers."""
import os

import httpx


def mode() -> str:
    if os.environ.get("LLM_MODE", "").lower() == "offline":
        return "offline"
    return "live" if os.environ.get("LLM_BASE_URL") and os.environ.get("LLM_MODEL") else "offline"


def chat(system: str, user: str, timeout: float = 30.0):
    """Return the model text, or None on any failure (callers fall back to templates)."""
    if mode() != "live":
        return None
    try:
        r = httpx.post(os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
                       headers={"Authorization": f"Bearer {os.environ.get('LLM_API_KEY', '')}"},
                       json={"model": os.environ["LLM_MODEL"], "temperature": 0.1,
                             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                       timeout=timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
