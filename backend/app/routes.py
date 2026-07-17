from flask import Blueprint, jsonify

from .models import Project

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