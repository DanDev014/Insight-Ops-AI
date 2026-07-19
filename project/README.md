# Project Health Engine

**DS 3 — Margin Expansion.** Flags active projects that are eroding margin —
over budget, thin on margin, or trending over their hour estimate — and drafts
the action. Served as a REST API the dashboard and the COO brief consume.

```
[Neon] -> database.py -> engine.py (rules + burn-rate forecast) -> api.py -> dashboard + COO agent
```

## What "at risk" means

An **active** project is flagged if any of:
- **Thin margin** — margin below 15%
- **Over hours** — already logged more than estimated
- **Trending over** — its current weekly burn rate, projected to the deadline,
  would blow the hour estimate by >20% (the predictive angle — catches it
  *before* it's actually over)
- **Deadline risk** — within 14 days of deadline with under 80% of hours logged

No ML — it's transparent rules plus a deterministic forward projection of the
burn rate, the same style as the workforce forecast.

## Why `amount_at_risk` is margin, not budget

Each recommendation's `amount_at_risk` is the project's **margin in dollars**
(`budget × margin%`), i.e. the profit actually at stake — not the whole budget.
This keeps projects ranking fairly against cashflow invoices in the COO brief
instead of swamping them.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env      # set PROJECTS_DATABASE_URL (or USE_SAMPLE_DATA=true)
uvicorn api:app --reload --port 8003    # note: port 8003
```

Open **http://localhost:8003/docs** to try the endpoints.

## Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/health` | service + DB connectivity |
| GET | `/projects/summary` | KPI card: totals, at-risk count, margin at risk |
| GET | `/projects/recommendations` | top at-risk projects |
| GET | `/projects/intelligence` | summary + recommendations (**the COO agent reads this**) |
| POST | `/refresh` | clear cache and re-pull |

## Plugging into the COO brief

Deploy this, then set `PROJECTS_URL` on the COO service to this engine's base
URL. The orchestrator calls `/projects/intelligence` and reads the
`recommendations` list — fields (`title`, `amount_at_risk`, `urgency`,
`alert_text`) already match its normalizer, so it slots in with no changes.
