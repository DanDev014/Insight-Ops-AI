from datetime import date, datetime

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

from .models import Client, Project, User, db

api = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Shared analytics logic (projects agent)
# ---------------------------------------------------------------------------
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

        # margin dollars at stake (not full budget) — keeps ranking fair vs other engines
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


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@api.get("/health")
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Analytics endpoints (projects agent — feed the COO brief)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Auth + CRUD endpoints (from develop)
# ---------------------------------------------------------------------------
@api.get("/projects/<int:user_id>")
def get_projects(user_id):
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)
    search = request.args.get("search", default="", type=str).strip()
    status = request.args.get("status", default="", type=str).strip()

    per_page = min(max(per_page, 1), 100)

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    query = Project.query.filter_by(user_id=user_id)

    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))
    if status:
        query = query.filter(Project.status == status)

    pagination = query.order_by(Project.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "projects": [project.to_dict() for project in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages,
    }), 200


@api.post("/projects")
def create_project():
    data = request.get_json(silent=True) or {}
    required_fields = ["user_id", "client_id", "name"]

    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": "Client or user not found"}), 404

    client = Client.query.filter_by(id=data["client_id"], user_id=data["user_id"]).first()
    if not client:
        return jsonify({"error": "Client or user not found"}), 404

    deadline = None
    if data.get("deadline"):
        try:
            deadline = datetime.strptime(data["deadline"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Deadline must be in YYYY-MM-DD format"}), 400

    try:
        project = Project(
            user_id=data["user_id"],
            client_id=data["client_id"],
            name=data["name"],
            budget=data.get("budget"),
            hours_estimated=data.get("hours_estimated"),
            hours_logged=data.get("hours_logged", 0),
            deadline=deadline,
            status=data.get("status", "active"),
            margin=data.get("margin"),
        )
        db.session.add(project)
        db.session.commit()
        return jsonify({"message": "Project created", "project": project.to_dict()}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to create project"}), 500


@api.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

feat/ui
    # Validate credentials
    # Validate credentials
    if not user or not check_password_hash(
        user.password_hash,
        password
    ):
        return jsonify({
            "error": "Invalid email or password"
        }), 401
    return jsonify({
        "message": "Login successful",
        "user": user.to_dict()
    }), 200
