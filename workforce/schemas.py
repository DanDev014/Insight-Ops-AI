"""
schemas.py
----------
Pydantic models that define the SHAPE of every API response. This is your
contract with the rest of the team: the frontend and the LLM agent code against
these types, so nobody has to guess what fields exist. FastAPI also uses them to
auto-generate interactive docs at /docs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Summary(BaseModel):
    total_employees: int
    avg_utilization_pct: float
    over_capacity_count: int = Field(..., description="Members currently over 100% utilization")
    available_capacity_hours: float = Field(..., description="Total free hours across the team")
    high_burnout_risk_count: int
    total_weekly_labour_cost: float


class Employee(BaseModel):
    name: str
    role: str
    weekly_hours: float
    capacity: int
    utilization_pct: float
    remaining_capacity: float
    predicted_utilization: float
    forecast_status: str = Field(..., description="Healthy | Warning | Critical")
    completed_tasks: float
    blocked_tasks: float
    productivity_score: float
    blocked_rate: float
    labour_cost: float
    num_skills: int
    status: str = Field(..., description="Available | Optimal | Overloaded")
    burnout_risk: str = Field(..., description="Low | Medium | High")


class Recommendation(BaseModel):
    overloaded_employee: str
    overloaded_role: str
    predicted_utilization: float
    driver_project: str | None
    suggested_employee: str
    suggested_role: str
    available_capacity_hours: float
    shared_skills: list[str]
    alert_text: str
    confidence: str = Field(..., description="High | Medium")


class WorkforceIntelligence(BaseModel):
    """The full payload the Executive Briefing (LLM) agent ingests."""
    generated_for_week_ending: str
    summary: Summary
    employees: list[Employee]
    recommendations: list[Recommendation]
