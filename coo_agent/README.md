# Virtual COO — Executive Brief

The orchestration layer. Every morning it pulls the three analytics engines,
ranks their findings by financial threat + urgency, and produces the **Top-3
Executive Brief** with ready-to-send draft actions — the thing the dashboard's
Executive Brief screen shows.

```
[workforce] ─┐
[cashflow]  ─┼─→ engines.py (fetch) → brief.py (rank + draft) → api.py → dashboard
[projects]  ─┘        each engine's /intelligence JSON
```

## Two design choices that matter

**Resilient to missing engines.** Only engines with a URL set are called; any
that's absent or down is skipped and noted. The brief is built from whatever
responded — so it works today on workforce + cashflow, and project-health slots
in the moment it's deployed (just set `PROJECTS_URL`, no code change).

**Runs with no LLM key.** `LLM_PROVIDER=mock` (the default) uses a transparent
rule-based ranker that scores by financial impact + urgency. Point it at a real
model (OpenAI, Gemini, Claude, Groq) whenever you're ready — same output shape.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env      # then set the engine URLs that are live
uvicorn api:app --reload --port 8002   # note: port 8002
```

Open **http://localhost:8002/brief** to see the morning brief, or `/docs`.

## Configure

`.env`:
```
WORKFORCE_URL="https://insight-ops-ai.onrender.com"
CASHFLOW_URL="https://<sheila-service>.onrender.com"    # when live
PROJECTS_URL=""                                         # when live

LLM_PROVIDER="mock"        # mock | openai | anthropic
LLM_API_KEY=""
LLM_MODEL=""
LLM_BASE_URL=""            # for Gemini/Groq/etc. OpenAI-compatible endpoints
```

## Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/health` | service status + which engines are reachable |
| GET | `/brief` | the Executive Brief: health score, headline, Top-3 actions |
| POST | `/refresh` | clear cache and re-pull from the engines |

## Brief shape (what the frontend renders)

```json
{
  "agency_health_score": 87,
  "headline": "3 high-urgency items today; $23,672 in weighted risk.",
  "top_actions": [
    {"rank": 1, "title": "...", "category": "Cash flow", "source": "cashflow",
     "urgency": "High", "why": "...", "draft_message": "..."}
  ],
  "engines": {"available": ["workforce", "cashflow"], "unavailable": ["projects"]},
  "generated_by": "rule-based (no LLM configured)"
}
```

Each `top_actions[].draft_message` is what sits behind the dashboard's "Send"
button — the owner approves with one click.

## Switching on a real LLM later

Set `LLM_PROVIDER` + `LLM_API_KEY` (+ `LLM_MODEL`, and `LLM_BASE_URL` for
OpenAI-compatible providers). The LLM then does the ranking and writes the
drafts; if the call ever fails, it automatically falls back to the rule-based
brief so the demo never breaks.
