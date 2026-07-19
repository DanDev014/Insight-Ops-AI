"""
sample_data.py
--------------
Generates projects + time_logs that mirror the Neon schema, with a deliberate
spread of healthy / at-risk / trending-over projects so the engine has real
signal and the demo shows variety. Deadlines are anchored to "now" so some fall
inside the deadline window every run.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(11)
np.random.seed(11)

NOW = datetime.now()

STATUSES = ["active", "active", "active", "completed", "paused"]
ADJ = ["Robust", "Visionary", "Enhanced", "Intuitive", "Seamless", "Agile",
       "Scalable", "Dynamic", "Global", "Streamlined"]
NOUN = ["Rebrand", "Campaign", "Platform", "Launch", "Redesign", "Rollout",
        "Microsite", "Identity", "Toolkit", "Portal"]


def _make_projects(n=120):
    rows = []
    for i in range(n):
        est = float(random.randint(60, 220))
        # health profile: some healthy, some over, some thin-margin
        profile = random.choice(["healthy", "healthy", "over_hours", "thin_margin", "trending"])
        if profile == "over_hours":
            logged = round(est * random.uniform(1.05, 1.5), 2)
            margin = round(random.uniform(18, 40), 2)
        elif profile == "thin_margin":
            logged = round(est * random.uniform(0.4, 0.9), 2)
            margin = round(random.uniform(5, 14), 2)
        elif profile == "trending":
            logged = round(est * random.uniform(0.6, 0.95), 2)  # not over yet, but burning fast
            margin = round(random.uniform(18, 35), 2)
        else:  # healthy
            logged = round(est * random.uniform(0.3, 0.8), 2)
            margin = round(random.uniform(20, 45), 2)

        rows.append({
            "id": 26 + i,
            "client_id": random.randint(1, 120),
            "name": f"{random.choice(ADJ)} {random.choice(NOUN)} {i}",
            "budget": float(random.randint(15000, 130000)),
            "hours_estimated": est,
            "hours_logged": logged,
            "deadline": (NOW + timedelta(days=random.randint(-30, 90))).date().isoformat(),
            "status": random.choice(STATUSES),
            "margin": margin,
            "_profile": profile,
        })
    return pd.DataFrame(rows)


def _make_time_logs(projects):
    """Recent burn per project drives the forward projection. 'trending' and
    'over_hours' projects get heavier recent logging so they project over."""
    task_status = ["completed", "in_progress", "blocked"]
    rows = []
    log_id = 219
    for _, p in projects.iterrows():
        # heavier recent burn for at-risk profiles
        weekly = {"trending": (18, 30), "over_hours": (15, 28),
                  "thin_margin": (5, 15), "healthy": (2, 12)}[p["_profile"]]
        n_entries = random.randint(3, 6)
        total = random.uniform(*weekly)
        splits = np.random.dirichlet(np.ones(n_entries)) * total
        for h in splits:
            rows.append({
                "id": log_id,
                "team_member_id": random.randint(14, 43),
                "project_id": p["id"],
                "log_date": (NOW - timedelta(days=random.randint(0, 6))).date().isoformat(),
                "hours_logged": round(float(h), 1),
                "task_status": random.choice(task_status),
            })
            log_id += 1
    return pd.DataFrame(rows)


def load_sample_tables() -> dict[str, pd.DataFrame]:
    projects = _make_projects()
    time_logs = _make_time_logs(projects)
    projects = projects.drop(columns=["_profile"])
    return {"projects": projects, "time_logs": time_logs}


if __name__ == "__main__":
    t = load_sample_tables()
    for name, df in t.items():
        print(f"{name}: {len(df)} rows")
