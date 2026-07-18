from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

from .models import Project, User

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

    # Find user by email
    user = User.query.filter_by(email=email).first()

    # Validate credentials
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    # Successful login
    return jsonify({
        "message": "Login successful",
        "user": user.to_dict()
    }), 200