"""
api.py
------
The deployment layer. Wraps the workforce engine in a FastAPI web service so the
frontend dashboard and the LLM Executive Briefing agent can pull live workforce
intelligence over HTTP instead of running a notebook.

Run locally:
    uvicorn api:app --reload --port 8000

Then open:
    http://localhost:8000/docs         <- interactive API docs (try it here)
    http://localhost:8000/workforce/intelligence   <- full JSON payload

Endpoints:
    GET /health                       service + DB connectivity
    GET /workforce/summary            KPI cards (total emps, avg util, etc.)
    GET /workforce/employees          per-person table rows
    GET /workforce/recommendations    reallocation alerts (LLM agent input)
    GET /workforce/intelligence       everything in one payload
    POST /refresh                     clear the cache / re-pull from the DB
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from schemas import (
    Employee,
    Recommendation,
    Summary,
    WorkforceIntelligence,
)
from workforce_engine import build_workforce_intelligence

app = FastAPI(
    title="Workforce Intelligence Agent",
    description="Resource Optimization Engine (DS 2) — workload, capacity, and "
                "reallocation intelligence for the Executive Briefing agent.",
    version="1.0.0",
)

# Allow the frontend (running on a different origin) to call this API.
# Tighten allow_origins to your deployed frontend URL before going public.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Simple in-memory cache -------------------------------------------------
# Recomputing on every request would hammer the DB. We compute once and reuse
# until someone calls /refresh (e.g. the morning cron job).
_cache: dict | None = None


def get_intelligence() -> dict:
    global _cache
    if _cache is None:
        tables = database.load_tables()
        _cache = build_workforce_intelligence(
            tables["team"], tables["projects"], tables["time_logs"]
        )
    return _cache


# --- Endpoints --------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "database": database.healthcheck()}


@app.get("/workforce/summary", response_model=Summary)
def workforce_summary():
    return get_intelligence()["summary"]


@app.get("/workforce/employees", response_model=list[Employee])
def workforce_employees():
    return get_intelligence()["employees"]


@app.get("/workforce/recommendations", response_model=list[Recommendation])
def workforce_recommendations():
    return get_intelligence()["recommendations"]


@app.get("/workforce/intelligence", response_model=WorkforceIntelligence)
def workforce_intelligence():
    """Full payload — this is what the LLM Executive Briefing agent ingests."""
    return get_intelligence()


@app.post("/refresh")
def refresh():
    """Clear the cache so the next request re-pulls fresh data from the DB.
    Call this from your morning pipeline before generating the briefing."""
    global _cache
    _cache = None
    return {"status": "cache cleared"}


@app.get("/")
def root():
    return {
        "service": "Workforce Intelligence Agent",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/workforce/summary",
            "/workforce/employees",
            "/workforce/recommendations",
            "/workforce/intelligence",
        ],
    }
