# Cash Flow Engine

**DS 1 — Client Payment Risk** (Sheila's module, restructured as a deployable service)

Predicts which **outstanding** invoices will be paid more than 15 days late, how
many days late, and how much money is at risk — then drafts the reminder action.
Served as a REST API the Executive Briefing agent and frontend consume.

```
[Neon] -> database.py -> features.py -> train.py (offline) -> models/cashflow_model.joblib
                                                                       |
                                                       engine.py (loads bundle) -> api.py -> agent + frontend
```

## Why this shape

A notebook computes once and prints. This splits into a **training** path (run
occasionally, produces the model artifact) and an **inference** path (the API,
loads the artifact and scores live invoices). That's the standard way to deploy
an ML model — you don't retrain on every request.

| File | Role |
|------|------|
| `config.py` | Thresholds (15-day late, 5-day reminder) and feature lists — one source of truth. |
| `features.py` | Leakage-safe, invoice-level feature engineering shared by train + inference. |
| `train.py` | Trains classifier (prob late) + regressor (days late), saves one bundle. |
| `engine.py` | Loads the bundle, scores outstanding invoices, builds the payload. |
| `database.py` | Loads tables from Neon, with sample-data fallback. |
| `sample_data.py` | Synthetic data with a real late-payment signal, for offline runs. |
| `schemas.py` | Pydantic response contracts. |
| `api.py` | FastAPI service. |

## Run it (5 minutes)

```bash
pip install -r requirements.txt

# .env at the project root needs SHEILADATABASE_URL
# (or set USE_SAMPLE_DATA="true" to run without the DB)

python train.py                       # trains + saves models/cashflow_model.joblib
uvicorn api:app --reload --port 8001   # note: port 8001 (workforce uses 8000)
```

Open **http://localhost:8001/docs** to try the endpoints.

## Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/health` | service, DB, and model-trained status |
| GET | `/cashflow/summary` | KPI cards: revenue at risk, high-risk clients, avg days late |
| GET | `/cashflow/invoices` | every outstanding invoice, scored |
| GET | `/cashflow/reminders` | invoices needing a reminder now — the action list |
| GET | `/cashflow/intelligence` | full payload (the LLM agent ingests this) |
| POST | `/refresh` | re-pull from DB and re-score |

## Integration

* **LLM / Executive Briefing agent** → `/cashflow/intelligence`. Each
  `recommendations[].alert_text` is written as an action, e.g. *"Client X has an
  82% probability of paying their $19,174 invoice ~20 days late (due ...). Send a
  polite payment reminder now."*
* **Frontend** → `/cashflow/summary` for the Revenue-at-Risk KPI card and
  `/cashflow/invoices` / `/cashflow/reminders` for the Clients table.

## What was fixed vs the original notebook

* **Threshold collapse:** the Youden's-J step picked 0.873 — just above every
  positive prediction — flagging every client one class. Replaced with an F1
  sweep clamped to [0.30, 0.70]; it can no longer collapse.
* **Target leakage:** dropped the stored `historical_payment_delay` (0.969
  correlated with the label). Client history is now computed leave-one-out from
  the client's *other* paid invoices.
* **Industry encoding bug:** single-row `get_dummies(drop_first=True)` produced
  zero columns and silently mis-encoded every scored client. Now one-hot against
  a fixed column set with reindex, so 1 row or 1000 always align.
* **Actionability:** scores the currently-**outstanding** invoices (not a static
  client label), so the agent can actually send a reminder before a due date.

## Note on the model artifact

`models/cashflow_model.joblib` is **not** committed — train it fresh with
`python train.py` so it's built on live Neon data with your installed sklearn
version.
