from datetime import datetime

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

from .models import Client, Project, User, db

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify({
        "status": "ok"
    })


@api.get("/projects/<int:user_id>")
def get_projects(user_id):
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)
    search = request.args.get("search", default="", type=str).strip()
    status = request.args.get("status", default="", type=str).strip()

    # Prevent excessively large page sizes
    per_page = min(max(per_page, 1), 100)

    # Ensure user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    query = Project.query.filter_by(user_id=user_id)

    # Search by project name (case-insensitive)
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))

    # Exact status match
    if status:
        query = query.filter(Project.status == status)

    pagination = query.order_by(Project.id.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return jsonify({
        "projects": [project.to_dict() for project in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages,
    }), 200


api.post("/projects")
def create_project():
    data = request.get_json(silent=True) or {}

    required_fields = ["user_id", "client_id", "name"]

    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    # Validate user
    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({
            "error": "Client or user not found"
        }), 404

    # Validate client belongs to the user
    client = Client.query.filter_by(
        id=data["client_id"],
        user_id=data["user_id"]
    ).first()

    if not client:
        return jsonify({
            "error": "Client or user not found"
        }), 404

    # Parse deadline if provided
    deadline = None
    if data.get("deadline"):
        try:
            deadline = datetime.strptime(
                data["deadline"],
                "%Y-%m-%d"
            ).date()
        except ValueError:
            return jsonify({
                "error": "Deadline must be in YYYY-MM-DD format"
            }), 400

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

        return jsonify({
            "message": "Project created",
            "project": project.to_dict()
        }), 201

    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Failed to create project"
        }), 500

@api.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password")

    # Validate required fields
    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    # Find user
    user = User.query.filter_by(email=email).first()

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