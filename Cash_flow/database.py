"""
database.py
-----------
Loads the tables the Cash Flow Engine needs from Neon, with a sample-data
fallback so training and the API run without a live DB.

Env vars (in .env at the project root):
    SHEILADATABASE_URL   -- Sheila's Neon branch connection string
    USE_SAMPLE_DATA      -- "true" to force sample data
"""

from __future__ import annotations

import os

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("SHEILADATABASE_URL") or os.getenv("DATABASE_URL")
USE_SAMPLE_DATA = os.getenv("USE_SAMPLE_DATA", "false").lower() == "true"

REQUIRED_TABLES = ["clients", "projects", "team", "time_logs", "payments"]


def _load_from_db() -> dict[str, pd.DataFrame]:
    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL)
    tables = {}
    with engine.connect() as conn:
        for name in REQUIRED_TABLES:
            tables[name] = pd.read_sql(f"SELECT * FROM {name};", conn)
    return tables


def load_tables() -> dict[str, pd.DataFrame]:
    if USE_SAMPLE_DATA or not DATABASE_URL:
        from sample_data import load_sample_tables
        return load_sample_tables()
    return _load_from_db()


def healthcheck() -> dict:
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
