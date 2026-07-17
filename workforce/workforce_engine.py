"""
workforce_engine.py
-------------------
The Resource Optimization Engine (DS 2: Workload & Team Performance).

This module contains PURE analytics functions. They take pandas DataFrames in
and return plain Python dicts/lists out. No database calls, no printing, no
global state. That is what makes them:
  - testable (feed sample data, assert on the output)
  - reusable (the API layer and the LLM agent both call the same functions)
  - portable (swap the data source without touching the logic)

Pipeline:
    build_workforce_intelligence(team, projects, time_logs)  <- single entry point
        -> team-level summary        (dashboard KPI cards)
        -> per-employee workload     (dashboard "Team" table)
        -> reallocation alerts       (AI Actions / LLM agent input)

Everything downstream (the FastAPI service, the LLM Executive Briefing agent)
consumes the dict returned by build_workforce_intelligence().
"""

from __future__ import annotations

import ast
from datetime import timedelta
from typing import Any

import pandas as pd

# ----------------------------------------------------------------------------
# Tunable business thresholds (keep them here so they're easy to defend/justify)
# ----------------------------------------------------------------------------
RECENT_WINDOW_DAYS = 7          # capacity is weekly, so we look at the last 7 days
OVERLOADED_THRESHOLD = 95.0     # >= this utilization % => Overloaded
OPTIMAL_THRESHOLD = 70.0        # >= this (and < overloaded) => Optimal, else Available
FORECAST_CRITICAL = 100.0       # predicted utilization >= this => Critical next week
FORECAST_WARNING = 90.0         # predicted utilization >= this => Warning


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _parse_skills(value: Any) -> list[str]:
    """Skills can arrive as a real list (psycopg2 array) or a stringified list
    ("['FastAPI', 'Django']") depending on the driver. Normalize to list[str]."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
            return parsed if isinstance(parsed, list) else []
        except (ValueError, SyntaxError):
            return [s.strip() for s in value.strip("{}").split(",") if s.strip()]
    return []


def classify_workload(utilization: float) -> str:
    if utilization >= OVERLOADED_THRESHOLD:
        return "Overloaded"
    if utilization >= OPTIMAL_THRESHOLD:
        return "Optimal"
    return "Available"


def forecast_status(utilization: float) -> str:
    if utilization >= FORECAST_CRITICAL:
        return "Critical"
    if utilization >= FORECAST_WARNING:
        return "Warning"
    return "Healthy"


def _burnout_risk(utilization: float, blocked_rate: float) -> str:
    """Composite burnout signal driving the dashboard's 'Burnout Risk' column.
    Combines how overloaded someone is with how much of their work is blocked
    (blocked work = frustration + rework, a real burnout driver)."""
    score = 0
    if utilization >= 100:
        score += 2
    elif utilization >= OVERLOADED_THRESHOLD:
        score += 1
    if blocked_rate >= 40:
        score += 2
    elif blocked_rate >= 20:
        score += 1
    return {0: "Low", 1: "Low", 2: "Medium", 3: "Medium"}.get(score, "High")


# ----------------------------------------------------------------------------
# Step 1: recent activity window
# ----------------------------------------------------------------------------
def get_recent_logs(time_logs: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp]:
    df = time_logs.copy()
    df["log_date"] = pd.to_datetime(df["log_date"])
    latest = df["log_date"].max()
    cutoff = latest - timedelta(days=RECENT_WINDOW_DAYS)
    return df[df["log_date"] >= cutoff].copy(), latest


# ----------------------------------------------------------------------------
# Step 2: per-employee workload (includes EVERYONE, even idle members)
# ----------------------------------------------------------------------------
def compute_employee_workload(
    team: pd.DataFrame, recent_logs: pd.DataFrame
) -> pd.DataFrame:
    agg = (
        recent_logs.groupby("team_member_id")
        .agg(
            weekly_hours=("hours_logged", "sum"),
            total_logs=("id", "count"),
            completed_tasks=("task_status", lambda x: (x == "completed").sum()),
            blocked_tasks=("task_status", lambda x: (x == "blocked").sum()),
            active_tasks=("task_status", lambda x: (x == "in_progress").sum()),
        )
        .reset_index()
    )

    # LEFT merge from team => idle employees are kept (fix for the notebook bug
    # where anyone with no recent logs silently vanished from the dashboard).
    wl = team.merge(agg, left_on="id", right_on="team_member_id", how="left")
    wl["team_member_id"] = wl["id"]

    # Idle employees have NaN aggregates -> fill with zeros
    for col in ["weekly_hours", "total_logs", "completed_tasks",
                "blocked_tasks", "active_tasks"]:
        wl[col] = wl[col].fillna(0)

    wl["skills"] = wl["skills"].apply(_parse_skills)

    # KPIs
    wl["utilization_pct"] = (wl["weekly_hours"] / wl["capacity"]) * 100
    wl["remaining_capacity"] = wl["capacity"] - wl["weekly_hours"]
    wl["labour_cost"] = wl["weekly_hours"] * wl["hourly_rate"]
    wl["productivity_score"] = (
        wl["completed_tasks"] / wl["total_logs"].replace(0, pd.NA)
    ).fillna(0) * 100
    wl["blocked_rate"] = (
        wl["blocked_tasks"] / wl["total_logs"].replace(0, pd.NA)
    ).fillna(0) * 100
    wl["num_skills"] = wl["skills"].apply(len)
    wl["status"] = wl["utilization_pct"].apply(classify_workload)
    wl["burnout_risk"] = wl.apply(
        lambda r: _burnout_risk(r["utilization_pct"], r["blocked_rate"]), axis=1
    )
    return wl


# ----------------------------------------------------------------------------
# Step 3: per-employee forecast (weighted by the projects they actually work on)
# ----------------------------------------------------------------------------
def add_forecast(
    workload: pd.DataFrame, projects: pd.DataFrame, recent_logs: pd.DataFrame
) -> pd.DataFrame:
    wl = workload.copy()

    # Per-project overrun % (only positive overruns matter for capacity risk)
    proj = projects.copy()
    proj["variance_pct"] = (
        (proj["hours_logged"] - proj["hours_estimated"]) / proj["hours_estimated"]
    ) * 100
    proj["overrun_pct"] = proj["variance_pct"].clip(lower=0)
    overrun_by_project = proj.set_index("id")["overrun_pct"].to_dict()
    global_overrun = proj["overrun_pct"].mean()

    # For each employee, weight the overrun by hours spent per project this week.
    hours_by_member_project = (
        recent_logs.groupby(["team_member_id", "project_id"])["hours_logged"]
        .sum()
        .reset_index()
    )

    def employee_overrun(member_id: int) -> float:
        rows = hours_by_member_project[
            hours_by_member_project["team_member_id"] == member_id
        ]
        if rows.empty:
            return global_overrun
        weights = rows["hours_logged"].to_numpy()
        overruns = rows["project_id"].map(
            lambda pid: overrun_by_project.get(pid, global_overrun)
        ).to_numpy()
        total = weights.sum()
        return float((weights * overruns).sum() / total) if total else global_overrun

    wl["expected_overrun_pct"] = wl["team_member_id"].apply(employee_overrun)
    wl["predicted_hours"] = wl["weekly_hours"] * (1 + wl["expected_overrun_pct"] / 100)
    wl["predicted_utilization"] = (wl["predicted_hours"] / wl["capacity"]) * 100
    wl["capacity_gap"] = wl["predicted_hours"] - wl["capacity"]
    wl["forecast_status"] = wl["predicted_utilization"].apply(forecast_status)
    return wl


# ----------------------------------------------------------------------------
# Step 4: reallocation recommendations (skill-matched, capacity-aware)
# ----------------------------------------------------------------------------
def build_recommendations(
    workload: pd.DataFrame, recent_logs: pd.DataFrame, projects: pd.DataFrame
) -> list[dict]:
    recs = []

    # Top project per member (what's driving their load) for the alert text
    member_project_hours = (
        recent_logs.groupby(["team_member_id", "project_id"])["hours_logged"]
        .sum()
        .reset_index()
        .merge(projects[["id", "name"]], left_on="project_id", right_on="id", how="left")
    )

    def top_project_name(member_id: int) -> str | None:
        rows = member_project_hours[
            member_project_hours["team_member_id"] == member_id
        ].sort_values("hours_logged", ascending=False)
        return rows.iloc[0]["name"] if not rows.empty else None

    critical = workload[workload["forecast_status"] == "Critical"]
    healthy = workload[workload["forecast_status"] == "Healthy"]

    for _, emp in critical.iterrows():
        emp_skills = set(emp["skills"])
        candidates = healthy[
            healthy["skills"].apply(lambda s: len(emp_skills & set(s)) > 0)
        ]
        if candidates.empty:
            continue
        best = candidates.sort_values("remaining_capacity", ascending=False).iloc[0]
        shared = sorted(emp_skills & set(best["skills"]))
        driver = top_project_name(emp["team_member_id"])

        alert = (
            f"{emp['name']} is projected to reach "
            f"{emp['predicted_utilization']:.0f}% capacity next week"
        )
        if driver:
            alert += f" due to '{driver}'"
        alert += (
            f". Recommend reallocating work to {best['name']} "
            f"(currently {best['remaining_capacity']:.0f}h free) "
            f"who shares: {', '.join(shared)}."
        )

        recs.append(
            {
                "overloaded_employee": emp["name"],
                "overloaded_role": emp["role"],
                "predicted_utilization": round(float(emp["predicted_utilization"]), 1),
                "driver_project": driver,
                "suggested_employee": best["name"],
                "suggested_role": best["role"],
                "available_capacity_hours": round(float(best["remaining_capacity"]), 1),
                "shared_skills": shared,
                "alert_text": alert,
                "confidence": "High" if len(shared) >= 3 else "Medium",
            }
        )
    return recs


# ----------------------------------------------------------------------------
# Team-level summary (dashboard KPI cards)
# ----------------------------------------------------------------------------
def build_summary(workload: pd.DataFrame) -> dict:
    return {
        "total_employees": int(len(workload)),
        "avg_utilization_pct": round(float(workload["utilization_pct"].mean()), 1),
        "over_capacity_count": int((workload["utilization_pct"] > 100).sum()),
        "available_capacity_hours": round(
            float(workload.loc[workload["remaining_capacity"] > 0, "remaining_capacity"].sum()), 1
        ),
        "high_burnout_risk_count": int((workload["burnout_risk"] == "High").sum()),
        "total_weekly_labour_cost": round(float(workload["labour_cost"].sum()), 2),
    }


# ----------------------------------------------------------------------------
# Public API of this module: one call does everything
# ----------------------------------------------------------------------------
def build_workforce_intelligence(
    team: pd.DataFrame, projects: pd.DataFrame, time_logs: pd.DataFrame
) -> dict:
    """Single entry point. Returns a JSON-serializable dict with three sections:
        summary        -> dashboard KPI cards
        employees      -> per-person rows for the 'Team' table
        recommendations-> reallocation alerts for the AI Actions / LLM agent
    """
    recent_logs, latest = get_recent_logs(time_logs)
    workload = compute_employee_workload(team, recent_logs)
    workload = add_forecast(workload, projects, recent_logs)
    recommendations = build_recommendations(workload, recent_logs, projects)

    employee_cols = [
        "name", "role", "weekly_hours", "capacity", "utilization_pct",
        "remaining_capacity", "predicted_utilization", "forecast_status",
        "completed_tasks", "blocked_tasks", "productivity_score", "blocked_rate",
        "labour_cost", "num_skills", "status", "burnout_risk",
    ]
    employees = (
        workload[employee_cols]
        .round(2)
        .sort_values("utilization_pct", ascending=False)
        .to_dict(orient="records")
    )

    return {
        "generated_for_week_ending": latest.date().isoformat(),
        "summary": build_summary(workload),
        "employees": employees,
        "recommendations": recommendations,
    }
