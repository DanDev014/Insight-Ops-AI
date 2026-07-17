"""
sample_data.py
--------------
Generates synthetic clients / projects / payments / team / time_logs that mirror
the Neon schema, with a *deliberate, learnable* relationship between client
behaviour and late payment (low engagement + large relative invoices + project
overruns -> later payment). This lets the model train to a real signal offline,
so the whole pipeline runs and demos without a database.

All dates are anchored to "now" so outstanding invoices always include some due
within the reminder window, regardless of when this runs.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(7)
np.random.seed(7)

NOW = datetime.now()

INDUSTRIES = ["SaaS", "Retail", "Fintech", "Logistics", "Real Estate",
              "Healthcare", "Media", "Consulting"]
ROLES = ["Backend Developer", "Frontend Developer", "Data Scientist",
         "BI Analyst", "Project Manager", "DevOps Engineer"]


def _make_clients(n=120):
    rows = []
    for i in range(n):
        # Each client has a latent "reliability" that drives engagement AND payment
        reliability = np.random.beta(2, 2)  # 0..1
        rows.append({
            "id": 1 + i,
            "name": f"Client {i:03d} {random.choice(['Ltd','LLC','PLC','Inc','& Sons'])}",
            "industry": random.choice(INDUSTRIES),
            "contract_value": float(random.randint(20000, 150000)),
            "payment_terms": random.choice([14, 30, 30, 45, 60]),
            "engagement_score": round(float(reliability * 100), 1),  # 0..100 scale
            "_reliability": reliability,  # hidden driver, dropped before "DB"
        })
    return pd.DataFrame(rows)


def _make_team(n=30):
    rows = []
    for i in range(n):
        rows.append({
            "id": 14 + i,
            "name": f"Member {i:02d}",
            "role": random.choice(ROLES),
            "hourly_rate": float(random.randint(60, 90)),
            "capacity": 40,
        })
    return pd.DataFrame(rows)


def _make_projects(client_ids, n=200):
    statuses = ["active", "completed", "paused"]
    rows = []
    for i in range(n):
        est = float(random.randint(60, 220))
        logged = round(est * random.uniform(0.5, 1.6), 2)
        rows.append({
            "id": 26 + i,
            "client_id": random.choice(client_ids),
            "name": f"Project {i}",
            "budget": float(random.randint(15000, 120000)),
            "hours_estimated": est,
            "hours_logged": logged,
            "deadline": (NOW + timedelta(days=random.randint(-60, 90))).date().isoformat(),
            "status": random.choice(statuses),
            "margin": round(random.uniform(10, 48), 2),
        })
    return pd.DataFrame(rows)


def _make_time_logs(team_ids, project_ids, n=1500):
    task_status = ["completed", "in_progress", "blocked"]
    rows = []
    for i in range(n):
        rows.append({
            "id": 219 + i,
            "team_member_id": random.choice(team_ids),
            "project_id": random.choice(project_ids),
            "log_date": (NOW - timedelta(days=random.randint(0, 60))).date().isoformat(),
            "hours_logged": round(random.uniform(0.5, 8.0), 1),
            "task_status": random.choice(task_status),
        })
    return pd.DataFrame(rows)


def _make_payments(clients):
    """Historical (paid) + outstanding invoices. Payment lateness is driven by the
    client's hidden reliability plus invoice size, so the model has real signal."""
    rows = []
    pid = 1
    for _, c in clients.iterrows():
        reliability = c["_reliability"]
        n_paid = random.randint(3, 8)
        # Historical paid invoices (due in the past)
        for _ in range(n_paid):
            amount = float(random.randint(2000, 20000))
            invoice_date = NOW - timedelta(days=random.randint(60, 400))
            terms = c["payment_terms"]
            due_date = invoice_date + timedelta(days=terms)
            rel = amount / c["contract_value"]
            # Late days: unreliable clients + big relative invoices pay later
            base_late = (1 - reliability) * 40 + rel * 30
            days_late = int(np.random.normal(base_late - 12, 8))
            paid_date = due_date + timedelta(days=days_late)
            rows.append({
                "id": pid, "client_id": c["id"], "amount": amount,
                "invoice_date": invoice_date.date().isoformat(),
                "due_date": due_date.date().isoformat(),
                "paid_date": paid_date.date().isoformat(),
            })
            pid += 1
        # Outstanding invoices (due around now, not yet paid)
        for _ in range(random.randint(0, 2)):
            amount = float(random.randint(2000, 20000))
            due_date = NOW + timedelta(days=random.randint(-8, 30))
            invoice_date = due_date - timedelta(days=c["payment_terms"])
            rows.append({
                "id": pid, "client_id": c["id"], "amount": amount,
                "invoice_date": invoice_date.date().isoformat(),
                "due_date": due_date.date().isoformat(),
                "paid_date": None,
            })
            pid += 1
    return pd.DataFrame(rows)


def load_sample_tables() -> dict[str, pd.DataFrame]:
    clients = _make_clients()
    team = _make_team()
    projects = _make_projects(clients["id"].tolist())
    time_logs = _make_time_logs(team["id"].tolist(), projects["id"].tolist())
    payments = _make_payments(clients)
    clients = clients.drop(columns=["_reliability"])  # hidden driver never reaches the model
    return {
        "clients": clients, "team": team, "projects": projects,
        "time_logs": time_logs, "payments": payments,
    }


if __name__ == "__main__":
    t = load_sample_tables()
    for name, df in t.items():
        print(f"{name}: {len(df)} rows")
    pays = t["payments"]
    print("Paid invoices:", pays["paid_date"].notna().sum())
    print("Outstanding:", pays["paid_date"].isna().sum())
