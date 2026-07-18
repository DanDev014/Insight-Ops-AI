"""
schemas.py
----------
Response contracts. The recommendation fields (title, amount_at_risk, urgency,
alert_text) match exactly what the COO orchestrator's normalizer reads, so this
engine plugs into the brief with no adapter.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Summary(BaseModel):
    total_projects: int
    active_projects: int
    on_track: int
    at_risk_count: int
    avg_margin_pct: float
    avg_progress_pct: float
    margin_at_risk: float = Field(..., description="$ margin at stake across at-risk projects")


class Recommendation(BaseModel):
    title: str
    project_id: int
    amount_at_risk: float
    margin_pct: float | None
    projected_overrun_pct: float
    days_to_deadline: int | None
    urgency: str = Field(..., description="High | Medium")
    alert_text: str


class Intelligence(BaseModel):
    generated_at: str
    summary: Summary
    recommendations: list[Recommendation]
