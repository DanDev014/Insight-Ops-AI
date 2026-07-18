"""
api.py
------
Serves the morning Executive Brief. Pulls the three engines, ranks + drafts,
returns the brief the dashboard renders.

Run:
    uvicorn api:app --reload --port 8002

Endpoints:
    GET /            service info
    GET /health      service status + which engines are reachable
    GET /brief       the morning Executive Brief (Top-3 actions + health score)
    POST /refresh    clear cache and re-pull from the engines
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from brief import build_brief
from config import ENGINES, LLM_PROVIDER
from engines import collect_intelligence

app = FastAPI(
    title="Virtual COO — Executive Brief",
    description="Orchestrates the workforce, cashflow, and project engines into a "
                "ranked morning brief with ready-to-send draft actions.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_cache: dict | None = None


def get_brief() -> dict:
    global _cache
    if _cache is None:
        _cache = build_brief(collect_intelligence())
    return _cache


@app.get("/health")
def health():
    collected = collect_intelligence()
    return {
        "status": "ok",
        "llm_provider": LLM_PROVIDER,
        "engines": {name: r["ok"] for name, r in collected.items()},
    }


@app.get("/brief")
def brief():
    return get_brief()


@app.post("/refresh")
def refresh():
    global _cache
    _cache = None
    return {"status": "cache cleared"}


@app.get("/")
def root():
    return {
        "service": "Virtual COO — Executive Brief",
        "docs": "/docs",
        "configured_engines": [name for name, url, _ in ENGINES if url],
        "llm_provider": LLM_PROVIDER,
    }
