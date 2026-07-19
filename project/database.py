"""
database.py
-----------
Loads the tables the Project Health Engine needs (projects, time_logs) from
Neon, with a sample-data fallback so it runs without a live DB.

Env (root .env):
    PROJECTS_DATABASE_URL   this engine's Neon connection string
                            (falls back to DATABASE_URL if not set)
    USE_SAMPLE_DATA         "true" to force sample data
"""

from __future__ import annotations

import pandas as pd

from config import DATABASE_URL, USE_SAMPLE_DATA

REQUIRED_TABLES = ["projects", "time_logs"]


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
