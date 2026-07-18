from flask import Blueprint, jsonify

from .models import Project
from datetime import date

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify({
        "status": "ok"
    })


@api.get("/projects")
def get_projects():
    projects = Project.query.all()

    return jsonify([project.to_dict() for project in projects])
def is_at_risk(project):
    """A live project is at risk if margin is thin, hours are overrun,
    or the deadline is close with too little progress."""
    if project.status != "active":
        return False

    margin = float(project.margin) if project.margin is not None else None
    hours_estimated = float(project.hours_estimated) if project.hours_estimated else None
    hours_logged = float(project.hours_logged) if project.hours_logged else None

    # Rule 1: thin margin
    if margin is not None and margin < 15:
        return True

    # Rule 2: already over the estimated hours
    if hours_estimated and hours_logged and hours_logged > hours_estimated:
        return True

    # Rule 3: deadline close, not enough progress
    if project.deadline:
        days_left = (project.deadline - date.today()).days
        if hours_estimated and hours_logged is not None:
            progress = hours_logged / hours_estimated
            if days_left <= 14 and progress < 0.8:
                return True

    return False


@api.get("/projects/summary")
def projects_summary():
    projects = Project.query.all()

    total_projects = len(projects)
    active_projects = [p for p in projects if p.status == "active"]
    on_track = sum(1 for p in active_projects if not is_at_risk(p))
    at_risk_count = sum(1 for p in active_projects if is_at_risk(p))

    margins = [float(p.margin) for p in projects if p.margin is not None]
    avg_margin_pct = round(sum(margins) / len(margins), 1) if margins else 0

    progress_values = []
    for p in projects:
        if p.hours_estimated and p.hours_logged is not None:
            progress_values.append(min(float(p.hours_logged) / float(p.hours_estimated), 1.0) * 100)
    avg_progress_pct = round(sum(progress_values) / len(progress_values), 1) if progress_values else 0

    return jsonify({
        "total_projects": total_projects,
        "on_track": on_track,
        "at_risk_count": at_risk_count,
        "avg_margin_pct": avg_margin_pct,
        "avg_progress_pct": avg_progress_pct,
    })


@api.get("/projects/recommendations")
def projects_recommendations():
    projects = Project.query.all()
    recommendations = []

    for p in projects:
        if not is_at_risk(p):
            continue

        margin = float(p.margin) if p.margin is not None else None
        hours_estimated = float(p.hours_estimated) if p.hours_estimated else None
        hours_logged = float(p.hours_logged) if p.hours_logged else None

        if margin is not None and margin < 15:
            alert_text = f"Project '{p.name}' has a thin margin of {margin}% — review pricing or scope."
            severity = "high"
        elif hours_estimated and hours_logged and hours_logged > hours_estimated:
            alert_text = f"Project '{p.name}' has exceeded its estimated hours ({hours_logged}/{hours_estimated}) — review scope creep."
            severity = "high"
        else:
            days_left = (p.deadline - date.today()).days if p.deadline else None
            alert_text = f"Project '{p.name}' has {days_left} days left with limited progress logged — check delivery plan."
            severity = "medium"

        recommendations.append({
            "project_id": p.id,
            "alert_text": alert_text,
            "severity": severity,
        })

    # Highest severity first, cap at top 5 for the demo
    recommendations.sort(key=lambda r: r["severity"] != "high")
    return jsonify(recommendations[:5])