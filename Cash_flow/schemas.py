"""
schemas.py
----------
Response contracts for the Cash Flow Engine API. The `summary` field names match
the KPI-card contract agreed with the frontend (revenue_at_risk,
high_risk_clients, avg_days_late_predicted).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Summary(BaseModel):
    total_clients: int
    outstanding_invoices: int
    revenue_at_risk: float = Field(..., description="$ total of high-risk outstanding invoices")
    high_risk_clients: int
    high_risk_invoices: int
    avg_days_late_predicted: float


class Invoice(BaseModel):
    invoice_id: int
    client_id: int
    client_name: str | None
    amount: float
    due_date: str
    days_until_due: int
    prob_late: float
    predicted_days_late: int
    risk_status: str = Field(..., description="HIGH RISK | LOW RISK")
    needs_reminder: bool


class Recommendation(BaseModel):
    client_name: str | None
    invoice_id: int
    amount: float
    prob_late: float
    predicted_days_late: int
    due_date: str
    needs_reminder: bool
    alert_text: str


class Intelligence(BaseModel):
    generated_at: str
    model: dict
    summary: Summary
    invoices: list[Invoice]
    reminders: list[Recommendation]
    recommendations: list[Recommendation]
