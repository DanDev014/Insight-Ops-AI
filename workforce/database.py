"""
database.py
-----------
Owns the connection to your Neon PostgreSQL branch and loads the three tables
the engine needs. This is the ONLY file that knows about the database — the
engine stays pure and unaware of where data comes from.

Environment variable required (put it in a .env file, see .env.example):
    DATABASE_URL="postgresql://user:pass@host/neondb?sslmode=require"

If USE_SAMPLE_DATA=true (or DATABASE_URL is missing), we fall back to the
generated sample data so the API always boots — handy for demos and for
teammates who haven't set up the DB yet.
"""

from __future__ import annotations

import os

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
USE_SAMPLE_DATA = os.getenv("USE_SAMPLE_DATA", "false").lower() == "true"

# Tables the workforce engine needs
REQUIRED_TABLES = ["team", "projects", "time_logs"]


def _load_from_db() -> dict[str, pd.DataFrame]:
    from sqlalchemy import create_engine  # imported here so sample-only runs don't need it

    engine = create_engine(DATABASE_URL)
    tables: dict[str, pd.DataFrame] = {}
    with engine.connect() as conn:
        for name in REQUIRED_TABLES:
            tables[name] = pd.read_sql(f"SELECT * FROM {name};", conn)
    return tables


def load_tables() -> dict[str, pd.DataFrame]:
    """Return {'team':df, 'projects':df, 'time_logs':df}.

    Uses the live Neon DB when configured; otherwise falls back to sample data.
    """
    if USE_SAMPLE_DATA or not DATABASE_URL:
        from sample_data import load_sample_tables
        return load_sample_tables()
    return _load_from_db()


def healthcheck() -> dict:
    """Lightweight connectivity check for the /health endpoint."""
    if USE_SAMPLE_DATA or not DATABASE_URL:
        return {"source": "sample_data", "connected": True}
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return {"source": "neon_postgres", "connected": True}
    except Exception as exc:  # noqa: BLE001
        return {"source": "neon_postgres", "connected": False, "error": str(exc)}
