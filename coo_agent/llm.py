"""
llm.py
------
A single call_llm() function the rest of the code uses. Provider is chosen by
LLM_PROVIDER:

  * mock       -> no API call; caller falls back to rule-based ranking.
  * openai     -> OpenAI or any OpenAI-compatible endpoint (set LLM_BASE_URL for
                  Gemini/Groq/Together/etc.).
  * anthropic  -> Claude.

Isolating the provider here means swapping models is a one-line env change; the
orchestration logic never changes.
"""

from __future__ import annotations

import json

import requests

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_PROVIDER


class LLMUnavailable(Exception):
    """Raised when no real provider is configured, so the caller uses mock ranking."""


def call_llm(system: str, user: str) -> str:
    if LLM_PROVIDER == "mock" or not LLM_API_KEY:
        raise LLMUnavailable("LLM_PROVIDER=mock or no API key set")

    if LLM_PROVIDER == "anthropic":
        return _anthropic(system, user)
    return _openai_compatible(system, user)


def _openai_compatible(system: str, user: str) -> str:
    base = (LLM_BASE_URL or "https://api.openai.com/v1").rstrip("/")
    model = LLM_MODEL or "gpt-4o-mini"
    resp = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {LLM_API_KEY}",
                 "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0.3,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _anthropic(system: str, user: str) -> str:
    model = LLM_MODEL or "claude-sonnet-4-6"
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": LLM_API_KEY,
                 "anthropic-version": "2023-06-01",
                 "Content-Type": "application/json"},
        json={"model": model, "max_tokens": 1500, "system": system,
              "messages": [{"role": "user", "content": user}]},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def parse_json(text: str) -> dict:
    """LLMs sometimes wrap JSON in ```json fences; strip and parse safely."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned.strip())
