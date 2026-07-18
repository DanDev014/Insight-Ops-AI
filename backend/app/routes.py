from flask import Blueprint, jsonify
from .models import Project
from datetime import date

api = Blueprint("api", __name__)


# Shared logic (defined ONCE, used by every endpoint)

def is_at_risk(project):
    """A live project is at risk if margin is thin, hours are overrun,
    or the deadline is close with too little progress."""
    if project.status != "active":
        return False

    margin = float(project.margin) if project.margin is not None else None
    hours_estimated = float(project.hours_estimated) if project.hours_estimated else None
    hours_logged = float(project.hours_logged) if project.hours_logged else None

    if margin is not None and margin < 15:
        return True
    if hours_estimated and hours_logged and hours_logged > hours_estimated:
        return True
    if project.deadline and hours_estimated and hours_logged is not None:
        days_left = (project.deadline - date.today()).days
        progress = hours_logged / hours_estimated
        if days_left <= 14 and progress < 0.8:
            return True
    return False


def build_summary(projects):
    """Compute the project KPI summary."""
    active_projects = [p for p in projects if p.status == "active"]
    margins = [float(p.margin) for p in projects if p.margin is not None]

    progress_values = []
    for p in projects:
        if p.hours_estimated and p.hours_logged is not None:
            progress_values.append(min(float(p.hours_logged) / float(p.hours_estimated), 1.0) * 100)

    return {
        "total_projects": len(projects),
        "on_track": sum(1 for p in active_projects if not is_at_risk(p)),
        "at_risk_count": sum(1 for p in active_projects if is_at_risk(p)),
        "avg_margin_pct": round(sum(margins) / len(margins), 1) if margins else 0,
        "avg_progress_pct": round(sum(progress_values) / len(progress_values), 1) if progress_values else 0,
    }


def build_recommendations(projects, limit=5):
    """Build the top at-risk project recommendations, highest urgency first."""
    recommendations = []
    for p in projects:
        if not is_at_risk(p):
            continue

        margin = float(p.margin) if p.margin is not None else None
        hours_estimated = float(p.hours_estimated) if p.hours_estimated else None
        hours_logged = float(p.hours_logged) if p.hours_logged else None
        budget_val = float(p.budget) if p.budget is not None else 0

        # dollars of margin at stake (not full budget — keeps ranking fair vs other engines)
        amount_at_risk = round(budget_val * (margin or 0) / 100, 2)

        if margin is not None and margin < 15:
            alert_text = f"Project '{p.name}' has a thin margin of {margin}% — review pricing or scope."
            urgency = "High"
        elif hours_estimated and hours_logged and hours_logged > hours_estimated:
            alert_text = f"Project '{p.name}' has exceeded its estimated hours ({hours_logged}/{hours_estimated}) — review scope creep."
            urgency = "High"
        else:
            days_left = (p.deadline - date.today()).days if p.deadline else None
            if days_left is not None:
                alert_text = f"Project '{p.name}' has {days_left} days left with limited progress logged — check delivery plan."
            else:
                alert_text = f"Project '{p.name}' is flagged at risk — check delivery plan."
            urgency = "Medium"

        recommendations.append({
            "title": p.name,
            "amount_at_risk": amount_at_risk,
            "urgency": urgency,
            "alert_text": alert_text,
        })

    recommendations.sort(key=lambda r: r["urgency"] != "High")
    return recommendations[:limit]


# Endpoints (each just calls the helpers)

@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.get("/projects")
def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects])


@api.get("/projects/summary")
def projects_summary():
    return jsonify(build_summary(Project.query.all()))


@api.get("/projects/recommendations")
def projects_recommendations():
    return jsonify(build_recommendations(Project.query.all()))


@api.get("/projects/intelligence")
def projects_intelligence():
    projects = Project.query.all()
    return jsonify({
        "summary": build_summary(projects),
        "recommendations": build_recommendations(projects),
    })