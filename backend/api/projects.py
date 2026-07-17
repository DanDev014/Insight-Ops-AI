import os
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load env variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
app.config["TITLE"] = "Insight Ops AI - Projects API"

# Allow your React frontend to access this API securely
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)


def get_db_connection():
    if not DATABASE_URL:
        raise Exception("Database URL not configured")
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        raise Exception(f"Database connection error: {str(e)}")


@app.route("/api/projects", methods=["GET"])
def get_projects():
    try:
        conn = get_db_connection()
    except Exception as e:
        return