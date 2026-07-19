"""
engine.py
---------
The Project Health / Margin Expansion Engine (DS 3). Pure functions: DataFrames
in, JSON-serializable dict out. No DB, no I/O — testable and reusable.

Two layers of risk detection:

  RULES (current state)     -- thin margin, already over estimated hours, or
                               deadline close with too little progress.
  FORECAST (predictive)     -- projects each active project's CURRENT burn rate
                               (hours logged in the last week) forward to its
                               deadline. If that projects it to blow the hour
                               estimate by >20%, it's flagged as "trending over"
                               BEFORE it actually happens. This is the DS 3
                               predictive angle, done deterministically (no ML).

Output feeds:
  summary          -> the "Projects at Risk" KPI card
  recommendations  -> the COO brief (title, amount_at_risk, urgency, alert_text)
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from config import (DEADLINE_WINDOW_DAYS, PROGRESS_FLOOR, RECENT_WINDOW_DAYS,
                    THIN_MARGIN_PCT, TOP_N_RECOMMENDATIONS, TREND_OVERRUN_PCT)


def _money(x: float) -> str:
    return f"${x:,.0f}"


def _recent_burn_by_project(time_logs: pd.DataFrame, today: pd.Timestamp) -> dict:
    """Hours logged per project in the last RECENT_WINDOW_DAYS (the burn rate)."""
    if time_logs is None or time_logs.empty:
        return {}
    tl = time_logs.copy()
    tl["log_date"] = pd.to_datetime(tl["log_date"], errors="coerce")
    cutoff = today - pd.Timedelta(days=RECENT_WINDOW_DAYS)
    recent = tl[tl["log_date"] >= cutoff]
    return recent.groupby("project_id")["hours_logged"].sum().to_dict()


def analyze_projects(projects: pd.DataFrame, time_logs: pd.DataFrame,
                     today: datetime | None = None) -> pd.DataFrame:
    today = pd.Timestamp(today or datetime.now()).normalize()
    df = projects.copy()
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")

    for col in ["budget", "hours_estimated", "hours_logged", "margin"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    burn = _recent_burn_by_project(time_logs, today)
    df["recent_weekly_hours"] = df["id"].map(burn).fillna(0.0)

    # progress by hours (capped at 100%)
    df["progress"] = (df["hours_logged"] / df["hours_estimated"]).clip(upper=1.0)
    df["effort_variance_pct"] = (
        (df["hours_logged"] - df["hours_estimated"]) / df["hours_estimated"] * 100
    )
    df["days_to_deadline"] = (df["deadline"] - today).dt.days

    # --- Forward projection: burn current weekly rate to the deadline ---
    weeks_left = (df["days_to_deadline"] / 7).clip(lower=0)
    df["projected_final_hours"] = df["hours_logged"] + df["recent_weekly_hours"] * weeks_left
    df["projected_overrun_pct"] = (
        (df["projected_final_hours"] - df["hours_estimated"]) / df["hours_estimated"] * 100
    )

    # margin dollars = what's actually financially at stake (not the whole budget)
    df["amount_at_risk"] = (df["budget"] * df["margin"] / 100).round(2)

    df["is_active"] = df["status"] == "active"

    # --- Risk flags ---
    df["thin_margin"] = df["margin"] < THIN_MARGIN_PCT
    df["over_hours"] = df["hours_logged"] > df["hours_estimated"]
    df["trending_over"] = df["projected_overrun_pct"] > TREND_OVERRUN_PCT
    df["deadline_risk"] = (
        (df["days_to_deadline"].between(0, DEADLINE_WINDOW_DAYS))
        & (df["progress"] < PROGRESS_FLOOR)
    )
    df["at_risk"] = df["is_active"] & (
        df["thin_margin"] | df["over_hours"] | df["trending_over"] | df["deadline_risk"]
    )
    return df


def _risk_reason(row) -> tuple[str, str]:
    """Return (urgency, alert_text) for an at-risk project. Concrete/current
    problems are High; predictive/future ones are Medium."""
    name = row["name"]
    if row["over_hours"]:
        return "High", (
            f"Project '{name}' has blown its hour budget "
            f"({row['hours_logged']:.0f}/{row['hours_estimated']:.0f}h logged), "
            f"eroding its {_money(row['amount_at_risk'])} margin. Review scope creep."
        )
    if row["thin_margin"]:
        return "High", (
            f"Project '{name}' is running a thin {row['margin']:.0f}% margin "
            f"({_money(row['amount_at_risk'])} at stake). Review pricing or scope."
        )
    if row["trending_over"]:
        return "Medium", (
            f"Project '{name}' is on pace to exceed its hour estimate by "
            f"{row['projected_overrun_pct']:.0f}% by deadline at the current burn rate. "
            f"Rebalance resources now to protect the {_money(row['amount_at_risk'])} margin."
        )
    # deadline risk
    return "Medium", (
        f"Project '{name}' has {int(row['days_to_deadline'])} days to deadline "
        f"but only {row['progress'] * 100:.0f}% of hours logged. Check the delivery plan."
    )


def build_summary(analyzed: pd.DataFrame) -> dict:
    active = analyzed[analyzed["is_active"]]
    at_risk = analyzed[analyzed["at_risk"]]
    margins = analyzed["margin"].dropna()
    progress = analyzed["progress"].dropna()
    return {
        "total_projects": int(len(analyzed)),
        "active_projects": int(len(active)),
        "on_track": int(len(active) - len(at_risk)),
        "at_risk_count": int(len(at_risk)),
        "avg_margin_pct": round(float(margins.mean()), 1) if len(margins) else 0.0,
        "avg_progress_pct": round(float(progress.mean()) * 100, 1) if len(progress) else 0.0,
        "margin_at_risk": round(float(at_risk["amount_at_risk"].sum()), 2),
    }


def build_recommendations(analyzed: pd.DataFrame) -> list[dict]:
    at_risk = analyzed[analyzed["at_risk"]].copy()
    recs = []
    for _, row in at_risk.iterrows():
        urgency, alert = _risk_reason(row)
        recs.append({
            "title": row["name"],
            "project_id": int(row["id"]),
            "amount_at_risk": float(row["amount_at_risk"]),
            "margin_pct": float(row["margin"]) if pd.notna(row["margin"]) else None,
            "projected_overrun_pct": round(float(row["projected_overrun_pct"]), 1),
            "days_to_deadline": int(row["days_to_deadline"]) if pd.notna(row["days_to_deadline"]) else None,
            "urgency": urgency,
            "alert_text": alert,
        })
    # High urgency first, then biggest margin at risk
    recs.sort(key=lambda r: (r["urgency"] != "High", -r["amount_at_risk"]))
    return recs[:TOP_N_RECOMMENDATIONS]


def build_project_intelligence(projects: pd.DataFrame, time_logs: pd.DataFrame,
                               today: datetime | None = None) -> dict:
    """Single entry point. Returns summary + recommendations for the COO brief."""
    analyzed = analyze_projects(projects, time_logs, today=today)
    return {
        "generated_at": pd.Timestamp(today or datetime.now()).date().isoformat(),
        "summary": build_summary(analyzed),
        "recommendations": build_recommendations(analyzed),
    }
