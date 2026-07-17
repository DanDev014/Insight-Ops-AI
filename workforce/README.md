# Workforce Intelligence Agent

**DS 2 — Resource Optimization Engine** (Daniel's module)

Turns raw workload data into live workforce intelligence: who's overloaded, who's
free, and exactly which tasks to move to whom. Exposed as a REST API that the
frontend dashboard and the LLM Executive Briefing agent both consume.

```
[Neon Postgres] --> database.py --> workforce_engine.py --> api.py (FastAPI) --> frontend + LLM agent
     data              load            pure analytics         HTTP / JSON
```

## What each file does

| File | Role |
|------|------|
| `workforce_engine.py` | The brain. Pure functions: workload KPIs, forecast, skill-matched reallocation. No DB, no I/O — fully testable. |
| `database.py` | Loads `team`, `projects`, `time_logs` from Neon. Falls back to sample data if the DB isn't set up. |
| `sample_data.py` | Generates realistic fake data so everything runs with zero setup. |
| `schemas.py` | Pydantic models = the API contract the frontend/LLM code against. |
| `api.py` | FastAPI service. The thing you deploy. |
| `run_demo.py` | Run the engine once, save `workforce_output.json` for teammates. |

## Run it locally (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your environment
cp .env.example .env
# then edit .env with your Neon DATABASE_URL
# (or set USE_SAMPLE_DATA="true" to skip the DB entirely)

# 3a. Quick check — no server, just see the output
python run_demo.py

# 3b. Start the API
uvicorn api:app --reload --port 8000
```

Then open **http://localhost:8000/docs** — FastAPI gives you an interactive page
where you can click "Try it out" on every endpoint. This is your demo screen.

## Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/health` | Service + DB connectivity |
| GET | `/workforce/summary` | KPI cards: total employees, avg utilization, over-capacity count, free hours, burnout risk |
| GET | `/workforce/employees` | Per-person rows for the **Team** table |
| GET | `/workforce/recommendations` | Reallocation alerts — **this is what the LLM agent ingests** |
| GET | `/workforce/intelligence` | Everything in one payload |
| POST | `/refresh` | Clear cache / re-pull from DB (call from the morning cron job) |

## How your teammates plug in

- **Frontend:** fetch `/workforce/summary` for the KPI cards and
  `/workforce/employees` for the Team table.
- **LLM Executive Briefing agent:** ingest `/workforce/intelligence`. The
  `recommendations[].alert_text` fields are already written as natural-language
  actions (e.g. *"Reallocate work to X who shares React, TypeScript"*) — the LLM
  ranks and drafts from these.

## Deploy (for the demo)

Easiest is **Render** or **Railway** (free tier, no card):

1. Push this folder to a GitHub repo.
2. New Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
5. Add `DATABASE_URL` as an environment variable in the dashboard.

You get a public URL your frontend can call.

## Tunable thresholds

All business rules live at the top of `workforce_engine.py`
(`OVERLOADED_THRESHOLD`, `FORECAST_CRITICAL`, etc.) — adjust in one place, no
logic changes needed.
