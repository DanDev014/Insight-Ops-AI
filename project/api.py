"""
api.py
------
Deployment layer for the Project Health Engine (DS 3). Serves project-risk
intelligence for the dashboard's "Projects at Risk" card and the COO brief.

Run:
    uvicorn api:app --reload --port 8003

Endpoints:
    GET /health                    service + DB connectivity
    GET /projects/summary          KPI card: totals, at-risk count, margin at risk
    GET /projects/recommendations  top at-risk projects (list)
    GET /projects/intelligence     summary + recommendations (the COO agent reads this)
    POST /refresh                  clear cache and re-pull from the DB
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from engine import build_project_intelligence
from schemas import Intelligence, Recommendation, Summary

app = FastAPI(
    title="Project Health Engine",
    description="DS 3 — Margin Expansion. Flags projects that are over budget, "
                "thin on margin, or trending over their hour estimate.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_cache: dict | None = None


def get_intelligence() -> dict:
    global _cache
    if _cache is None:
        tables = database.load_tables()
        _cache = build_project_intelligence(tables["projects"], tables.get("time_logs"))
    return _cache


@app.get("/health")
def health():
    return {"status": "ok", "database": database.healthcheck()}


@app.get("/projects/summary", response_model=Summary)
def projects_summary():
    return get_intelligence()["summary"]


@app.get("/projects/recommendations", response_model=list[Recommendation])
def projects_recommendations():
    return get_intelligence()["recommendations"]


@app.get("/projects/intelligence", response_model=Intelligence)
def projects_intelligence():
    return get_intelligence()


@app.post("/refresh")
def refresh():
    global _cache
    _cache = None
    return {"status": "cache cleared"}


@app.get("/")
def root():
    return {"service": "Project Health Engine", "docs": "/docs",
            "endpoints": ["/health", "/projects/summary",
                          "/projects/recommendations", "/projects/intelligence"]}
