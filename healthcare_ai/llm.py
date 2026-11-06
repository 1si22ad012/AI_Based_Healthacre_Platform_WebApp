import json
import logging
import urllib.error
import urllib.request
from django.conf import settings

logger = logging.getLogger(__name__)

SAFETY_SYSTEM_PROMPT = (
    "You are a healthcare information assistant. You provide general health information only. "
    "You must never diagnose a disease, never prescribe medication or dosage, never recommend stopping prescribed medication, "
    "and never claim symptoms are harmless without sufficient information. "
    "Identify emergency warning signs and recommend immediate emergency services when appropriate. "
    "Always recommend consulting a qualified healthcare professional. "
    "Use only the provided context when available; do not fabricate sources or citations."
)


def llm_configured() -> bool:
    return bool(getattr(settings, "LLM_API_KEY", "")) and bool(getattr(settings, "LLM_BASE_URL", ""))


def call_llm(messages, timeout=None):
    """Call an OpenAI-compatible chat completions endpoint. Returns (text, error)."""
    if not llm_configured():
        return None, "LLM provider not configured."
    timeout = timeout or getattr(settings, "LLM_TIMEOUT", 30)
    url = getattr(settings, "LLM_BASE_URL", "").rstrip("/") + "/chat/completions"
    payload = {
        "model": getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 600,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + settings.LLM_API_KEY,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        choices = body.get("choices") or []
        if not choices:
            return None, "Empty LLM response."
        text = choices[0].get("message", {}).get("content", "").strip()
        return text or None, None
    except urllib.error.HTTPError as exc:
        logger.warning("LLM HTTP error: %s", exc.code)
        return None, f"LLM provider error ({exc.code})."
    except Exception as exc:
        logger.warning("LLM request failed: %s", exc)
        return None, "LLM provider unavailable."