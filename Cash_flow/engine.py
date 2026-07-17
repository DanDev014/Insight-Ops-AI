"""
engine.py
---------
Inference layer. Loads the trained bundle and scores the CURRENTLY-OUTSTANDING
invoices (paid_date is null) — the ones the agent can still act on. For each it
produces: probability of being >15 days late, expected days late, the dollar
amount at risk, and whether a reminder is due (invoice within the lead window
AND high-risk).

This is what makes DS 1 actionable rather than descriptive: the output directly
supports "send a polite reminder 5 days before the due date."
"""

from __future__ import annotations

from datetime import datetime

import joblib
import pandas as pd

from config import ARTIFACT_PATH, REMINDER_LEAD_DAYS
from features import build_scoring_frame


def load_artifacts(path: str = ARTIFACT_PATH) -> dict:
    return joblib.load(path)


def _money(x: float) -> str:
    return f"${x:,.0f}"


def score_outstanding(tables: dict, artifacts: dict, today: datetime | None = None) -> pd.DataFrame:
    today = pd.Timestamp(today or datetime.now()).normalize()
    frame = build_scoring_frame(tables, artifacts["industry_cols"])
    if frame.empty:
        return frame

    X = frame[artifacts["feature_cols"]]
    frame = frame.copy()
    frame["prob_late"] = artifacts["clf"].predict_proba(X)[:, 1]
    frame["predicted_days_late"] = artifacts["reg"].predict(X).round().astype(int)
    frame["is_high_risk"] = (frame["prob_late"] >= artifacts["threshold"]).astype(int)
    frame["days_until_due"] = (frame["due_date"] - today).dt.days
    frame["needs_reminder"] = (
        (frame["is_high_risk"] == 1)
        & (frame["days_until_due"] >= 0)
        & (frame["days_until_due"] <= REMINDER_LEAD_DAYS)
    )
    return frame


def build_intelligence(tables: dict, artifacts: dict, today: datetime | None = None) -> dict:
    scored = score_outstanding(tables, artifacts, today=today)

    if scored.empty:
        return {
            "generated_at": pd.Timestamp(today or datetime.now()).date().isoformat(),
            "model": artifacts.get("metrics", {}),
            "summary": {"total_clients": 0, "outstanding_invoices": 0,
                        "revenue_at_risk": 0.0, "high_risk_clients": 0,
                        "high_risk_invoices": 0, "avg_days_late_predicted": 0.0},
            "invoices": [], "reminders": [], "recommendations": [],
        }

    high = scored[scored["is_high_risk"] == 1]

    summary = {
        "total_clients": int(scored["client_id"].nunique()),
        "outstanding_invoices": int(len(scored)),
        "revenue_at_risk": round(float(high["amount"].sum()), 2),
        "high_risk_clients": int(high["client_id"].nunique()),
        "high_risk_invoices": int(len(high)),
        "avg_days_late_predicted": round(
            float(high["predicted_days_late"].mean()) if len(high) else 0.0, 1),
    }

    def invoice_row(r):
        return {
            "invoice_id": int(r["id"]),
            "client_id": int(r["client_id"]),
            "client_name": r.get("client_name"),
            "amount": round(float(r["amount"]), 2),
            "due_date": r["due_date"].date().isoformat(),
            "days_until_due": int(r["days_until_due"]),
            "prob_late": round(float(r["prob_late"]), 3),
            "predicted_days_late": int(r["predicted_days_late"]),
            "risk_status": "HIGH RISK" if r["is_high_risk"] else "LOW RISK",
            "needs_reminder": bool(r["needs_reminder"]),
        }

    invoices = [invoice_row(r) for _, r in
                scored.sort_values("prob_late", ascending=False).iterrows()]

    # Recommendations: one COO-style action per high-risk invoice, phrased like
    # the spec's "Client X has an 85% probability of delaying their $10,000
    # payment by 18 days."
    recs = []
    for _, r in high.sort_values("amount", ascending=False).iterrows():
        alert = (
            f"{r.get('client_name', 'Client')} has a "
            f"{r['prob_late'] * 100:.0f}% probability of paying their "
            f"{_money(r['amount'])} invoice ~{int(r['predicted_days_late'])} days late "
            f"(due {r['due_date'].date().isoformat()})."
        )
        if r["needs_reminder"]:
            alert += " Due within the reminder window — send a polite payment reminder now."
        recs.append({
            "client_name": r.get("client_name"),
            "invoice_id": int(r["id"]),
            "amount": round(float(r["amount"]), 2),
            "prob_late": round(float(r["prob_late"]), 3),
            "predicted_days_late": int(r["predicted_days_late"]),
            "due_date": r["due_date"].date().isoformat(),
            "needs_reminder": bool(r["needs_reminder"]),
            "alert_text": alert,
        })

    reminders = [x for x in recs if x["needs_reminder"]]

    return {
        "generated_at": pd.Timestamp(today or datetime.now()).date().isoformat(),
        "model": artifacts.get("metrics", {}),
        "summary": summary,
        "invoices": invoices,
        "reminders": reminders,
        "recommendations": recs,
    }
