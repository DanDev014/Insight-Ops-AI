"""
config.py
---------
Configuration for the COO orchestration layer. Everything is driven by
environment variables so nothing is hard-coded and engines can be added/removed
without touching code.

Engine URLs (set the ones that are live; leave the rest unset and they're skipped):
    WORKFORCE_URL   e.g. https://insight-ops-ai.onrender.com
    CASHFLOW_URL    e.g. https://cashflow-xxxx.onrender.com
    PROJECTS_URL    e.g. https://projects-xxxx.onrender.com

LLM (optional — defaults to "mock" so it runs with no key):
    LLM_PROVIDER    mock | openai | anthropic       (default: mock)
    LLM_API_KEY     your key (not needed for mock)
    LLM_MODEL       model name (provider-specific)
    LLM_BASE_URL    override for OpenAI-compatible providers (Gemini, Groq, ...)
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Each engine: (name, base_url, intelligence_path). Only those with a URL run.
ENGINES = [
    ("workforce", os.getenv("WORKFORCE_URL"), "/workforce/intelligence"),
    ("cashflow", os.getenv("CASHFLOW_URL"), "/cashflow/intelligence"),
    ("projects", os.getenv("PROJECTS_URL"), "/projects/intelligence"),
]

FETCH_TIMEOUT_SECONDS = 60  # generous, because free-tier engines cold-start

# --- LLM ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")

# How many actions the morning brief surfaces
TOP_N_ACTIONS = 3
