"""
api.py
------
The deployment layer for the Cash Flow Engine. Loads the trained model bundle
once at startup and serves invoice-level payment-risk intelligence.

Run locally:
    python train.py          # first, to produce models/cashflow_model.joblib
    uvicorn api:app --reload --port 8001

Docs: http://localhost:8001/docs

Endpoints:
    GET /health                    service + DB connectivity + model status
    GET /cashflow/summary          KPI cards (revenue at risk, high-risk clients)
    GET /cashflow/invoices         every outstanding invoice, scored
    GET /cashflow/reminders        invoices needing a reminder now (the action list)
    GET /cashflow/intelligence     full payload (the LLM agent ingests this)
    POST /refresh                  re-pull from DB and re-score
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import database
import engine
from config import ARTIFACT_PATH
from schemas import Intelligence, Invoice, Recommendation, Summary

app = FastAPI(
    title="Cash Flow Engine",
    description="DS 1 — Client Payment Risk. Predicts which outstanding invoices "
                "will be paid >15 days late and drafts reminder actions.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_cache: dict | None = None
_artifacts: dict | None = None


def get_artifacts() -> dict:
    global _artifacts
    if _artifacts is None:
        if not os.path.exists(ARTIFACT_PATH):
            raise HTTPException(
                status_code=503,
                detail="Model not trained yet. Run `python train.py` first.",
            )
        _artifacts = engine.load_artifacts()
    return _artifacts


def get_intelligence() -> dict:
    global _cache
    if _cache is None:
        tables = database.load_tables()
        _cache = engine.build_intelligence(tables, get_artifacts())
    return _cache


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database": database.healthcheck(),
        "model_trained": os.path.exists(ARTIFACT_PATH),
    }


@app.get("/cashflow/summary", response_model=Summary)
def summary():
    return get_intelligence()["summary"]


@app.get("/cashflow/invoices", response_model=list[Invoice])
def invoices():
    return get_intelligence()["invoices"]


@app.get("/cashflow/reminders", response_model=list[Recommendation])
def reminders():
    return get_intelligence()["reminders"]


@app.get("/cashflow/intelligence", response_model=Intelligence)
def intelligence():
    return get_intelligence()


@app.post("/refresh")
def refresh():
    global _cache
    _cache = None
    return {"status": "cache cleared"}


@app.get("/")
def root():
    return {"service": "Cash Flow Engine", "docs": "/docs",
            "endpoints": ["/health", "/cashflow/summary", "/cashflow/invoices",
                          "/cashflow/reminders", "/cashflow/intelligence"]}
