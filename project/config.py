"""
config.py
---------
Single source of truth for the Project Health Engine (DS 3 — Margin Expansion).
Thresholds live here so they're tunable in one place and the logic never drifts.
"""

from __future__ import annotations

import os

# --- Risk thresholds --------------------------------------------------------
THIN_MARGIN_PCT = 15.0        # margin below this % = at risk
DEADLINE_WINDOW_DAYS = 14     # deadline within this many days = watch it
PROGRESS_FLOOR = 0.80         # ...and progress under this = behind schedule
TREND_OVERRUN_PCT = 20.0      # projected to blow estimate by >this % = trending over
RECENT_WINDOW_DAYS = 7        # burn-rate is measured over the last week

# How many at-risk projects the recommendations endpoint returns
TOP_N_RECOMMENDATIONS = 5

# --- Data source ------------------------------------------------------------
# Uses its own connection string if provided, else the shared DATABASE_URL.
DATABASE_URL = os.getenv("PROJECTS_DATABASE_URL") or os.getenv("DATABASE_URL")
USE_SAMPLE_DATA = os.getenv("USE_SAMPLE_DATA", "false").lower() == "true"
