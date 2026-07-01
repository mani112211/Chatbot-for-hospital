"""
llm.py
------
Reply generation for MediBot, powered by the Google Gemini API.

Resolution order (first available wins):
  1. Google Gemini      -> if GEMINI_API_KEY (or GOOGLE_API_KEY) is set and the
                           `google-genai` package is installed.
  2. Offline demo mode  -> keyword matching over the local KNOWLEDGE_BASE (no key required).

The offline mode means the app ALWAYS runs and can be demoed even without an API key,
while the code is ready for Gemini the moment a key is provided. The API key is read
only from environment variables — never hard-coded — per the assignment's security note.
"""

from __future__ import annotations

import os

from knowledge import (
    SYSTEM_PROMPT,
    KNOWLEDGE_BASE,
    FALLBACK_REPLY,
    MEDICAL_ADVICE_KEYWORDS,
    MEDICAL_ADVICE_REPLY,
)

# Default Gemini model (override via the GEMINI_MODEL env var).
# Common choices: gemini-2.5-flash, gemini-2.5-flash-lite, gemini-flash-lite-latest.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# How many recent turns of history to send to the model (keeps token cost sane).
MAX_HISTORY_TURNS = 12


class LLMError(Exception):
    """Raised when Gemini fails to return a reply."""


def _gemini_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------
def _gemini_available() -> bool:
    if not _gemini_api_key():
        return False
    try:
        from google import genai  # noqa: F401
        return True
    except ImportError:
        return False


def active_provider() -> str:
    """Return the provider that will be used: 'gemini' or 'demo'."""
    return "gemini" if _gemini_available() else "demo"


def provider_label() -> str:
    """Human-friendly status string for the sidebar."""
    if active_provider() == "gemini":
        return f"🟢 Gemini ({GEMINI_MODEL})"
    return "🟡 Offline demo mode (no API key)"


# ---------------------------------------------------------------------------
# Offline demo responder (safety-first keyword matching over the knowledge base)
# ---------------------------------------------------------------------------
def _demo_reply(user_message: str) -> str:
    text = user_message.lower()

    # Safety first: if the user seems to be asking for medical advice / describing
    # symptoms, always return the safe "please see a doctor" response.
    if any(kw in text for kw in MEDICAL_ADVICE_KEYWORDS):
        return MEDICAL_ADVICE_REPLY

    best_entry = None
    best_score = 0
    for entry in KNOWLEDGE_BASE:
        score = sum(1 for kw in entry["keywords"] if kw in text)
        if score > best_score:
            best_score = score
            best_entry = entry
    if best_entry is not None and best_score > 0:
        return best_entry["answer"]
    return FALLBACK_REPLY


# ---------------------------------------------------------------------------
# Real Gemini call
# ---------------------------------------------------------------------------
def _gemini_reply(history: list[dict]) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_gemini_api_key())

    # Gemini uses roles "user" and "model" (not "assistant").
    contents = [
        {
            "role": "user" if m["role"] == "user" else "model",
            "parts": [{"text": m["content"]}],
        }
        for m in history
    ]

    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.4,
            max_output_tokens=700,
        ),
    )

    # `resp.text` can be None if the response was blocked or empty — handle gracefully.
    try:
        text = (resp.text or "").strip()
    except Exception:
        text = ""
    return text


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def generate_reply(history: list[dict]) -> str:
    """
    Generate the assistant's next reply.

    `history` is the full chat as a list of {"role": "user"|"assistant", "content": str}.
    The most recent message is the user's current question.

    Raises LLMError on Gemini/API failure so the UI can show a friendly message
    without crashing the app.
    """
    if not history:
        raise LLMError("No conversation history was provided.")

    trimmed = history[-MAX_HISTORY_TURNS:]

    if active_provider() == "demo":
        # Demo mode never touches the network, so it can't fail here.
        return _demo_reply(trimmed[-1]["content"])

    try:
        reply = _gemini_reply(trimmed)
    except Exception as exc:  # network error, auth error, rate limit, bad model, etc.
        err_msg = str(exc)
        demo_ans = _demo_reply(trimmed[-1]["content"])
        if "429" in err_msg or "quota" in err_msg.lower() or "resource_exhausted" in err_msg.lower():
            return f"⚠️ *(Gemini API Quota Exceeded. Showing offline fallback reply)*\n\n{demo_ans}"
        return f"⚠️ *(Gemini API Error: Showing offline fallback)*\n\n{demo_ans}"

    if not reply:
        demo_ans = _demo_reply(trimmed[-1]["content"])
        return f"⚠️ *(Empty response from Gemini. Showing offline fallback)*\n\n{demo_ans}"
    return reply
