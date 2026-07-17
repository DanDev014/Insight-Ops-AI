"""
sample_data.py
--------------
Generates realistic sample DataFrames that mirror the exact schema of the
Neon PostgreSQL tables (team, projects, time_logs).

Purpose: let the whole workforce engine + API run and demo WITHOUT a live
database connection. In production you swap this out for database.load_tables().

The schema here matches what your notebook loaded:
  team       -> id, name, role, hourly_rate, capacity, skills (list[str])
  projects   -> id, client_id, name, budget, hours_estimated, hours_logged,
                deadline, status, margin
  time_logs  -> id, team_member_id, project_id, log_date, hours_logged, task_status
"""

from __future__ import annotations

import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

# Deterministic output so demos are reproducible
random.seed(42)
np.random.seed(42)

# "Today" for the sample world. In production this is just date.today().
TODAY = date(2026, 7, 15)

SKILL_POOL = {
    "Backend Developer": ["FastAPI", "Django", "PostgreSQL", "Redis"],
    "Frontend Developer": ["React", "TypeScript", "Tailwind CSS", "Next.js"],
    "Data Engineer": ["Spark", "Airflow", "PostgreSQL", "dbt"],
    "Data Scientist": ["Python", "scikit-learn", "Pandas", "PyTorch"],
    "BI Analyst": ["Tableau", "Power BI", "SQL", "Excel"],
    "Project Manager": ["Agile", "Scrum", "Jira", "Resource Planning"],
    "DevOps Engineer": ["Docker", "AWS", "MLflow", "PostgreSQL"],
}

FIRST_NAMES = [
    "Savannah", "Carol", "Jose", "Jessica", "Andrew", "April", "Lauren",
    "Larry", "Samantha", "Frederick", "Virginia", "Angela", "Scott", "Lisa",
    "Marcus", "Priya", "Kevin", "Nadia", "Tomas", "Grace", "Hassan", "Wanjiru",
    "Brian", "Amina", "Derek", "Fatima", "Leo", "Chen", "Ada", "Omar",
]
LAST_NAMES = [
    "Thompson", "Mccullough", "Allen", "Reynolds", "Vasquez", "Roberts",
    "Carson", "Haynes", "Harrison", "Phillips", "Williams", "Stein", "Mathews",
    "Okoro", "Njoroge", "Silva", "Khan", "Mensah", "Ali", "Otieno",
]


def _make_team(n: int = 30) -> pd.DataFrame:
    roles = list(SKILL_POOL.keys())
    rows = []
    for i in range(n):
        role = random.choice(roles)
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        rows.append(
            {
                "id": 14 + i,  # start at 14 like your real data
                "name": name,
                "role": role,
                "hourly_rate": float(random.randint(60, 90)),
                "capacity": 40,
                "skills": SKILL_POOL[role],
            }
        )
    return pd.DataFrame(rows)


def _make_projects(team_ids: list[int], n: int = 60) -> pd.DataFrame:
    statuses = ["active", "completed", "paused"]
    rows = []
    for i in range(n):
        est = float(random.randint(60, 220))
        # Some projects run over (variance), some under
        variance_factor = random.uniform(0.4, 1.6)
        logged = round(est * variance_factor, 2)
        rows.append(
            {
                "id": 26 + i,
                "client_id": random.randint(20, 160),
                "name": f"Project {random.choice(['Alpha','Beacon','Cascade','Delta','Echo','Forge','Grid','Halo'])} {i}",
                "budget": float(random.randint(15000, 120000)),
                "hours_estimated": est,
                "hours_logged": logged,
                "deadline": (TODAY + timedelta(days=random.randint(-40, 90))).isoformat(),
                "status": random.choice(statuses),
                "margin": round(random.uniform(15, 48), 2),
            }
        )
    return pd.DataFrame(rows)


def _make_time_logs(team_ids: list[int], project_ids: list[int]) -> pd.DataFrame:
    """Generate logs by first choosing a realistic TARGET weekly utilization for
    each employee, then emitting log entries in the last 7 days that sum to it.
    This produces a believable spread: some Available, some Optimal, a few
    Overloaded/Critical — and crucially some free people to reallocate work to."""
    task_statuses = ["completed", "in_progress", "blocked"]
    rows = []
    log_id = 219

    for member_id in team_ids:
        # Target utilization: most people 55-95%, a few overloaded, a few idle
        target_util = np.random.choice(
            [np.random.uniform(30, 55),    # available
             np.random.uniform(70, 92),    # optimal (most common)
             np.random.uniform(70, 92),
             np.random.uniform(98, 130)],  # overloaded
            p=[0.25, 0.30, 0.25, 0.20],
        )
        target_hours = 40 * target_util / 100

        # Spread target hours across 3-7 log entries in the last week
        n_entries = random.randint(3, 7)
        splits = np.random.dirichlet(np.ones(n_entries)) * target_hours
        for h in splits:
            rows.append({
                "id": log_id,
                "team_member_id": member_id,
                "project_id": random.choice(project_ids),
                "log_date": (TODAY - timedelta(days=random.randint(0, 6))).isoformat(),
                "hours_logged": round(float(h), 1),
                "task_status": random.choices(task_statuses, weights=[0.55, 0.30, 0.15])[0],
            })
            log_id += 1

        # Add some older historical logs (outside the recent window) for realism
        for _ in range(random.randint(5, 15)):
            rows.append({
                "id": log_id,
                "team_member_id": member_id,
                "project_id": random.choice(project_ids),
                "log_date": (TODAY - timedelta(days=random.randint(8, 60))).isoformat(),
                "hours_logged": round(random.uniform(0.5, 7.0), 1),
                "task_status": random.choices(task_statuses, weights=[0.6, 0.25, 0.15])[0],
            })
            log_id += 1

    return pd.DataFrame(rows)


def load_sample_tables() -> dict[str, pd.DataFrame]:
    """Return {'team':..., 'projects':..., 'time_logs':...} as DataFrames."""
    team = _make_team()
    projects = _make_projects(team["id"].tolist())
    time_logs = _make_time_logs(team["id"].tolist(), projects["id"].tolist())
    time_logs = time_logs.sample(frac=1, random_state=42).reset_index(drop=True)
    return {"team": team, "projects": projects, "time_logs": time_logs}


if __name__ == "__main__":
    tables = load_sample_tables()
    for name, df in tables.items():
        print(f"\n=== {name} ({len(df)} rows) ===")
        print(df.head(3).to_string())
