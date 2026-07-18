"""
brief.py
--------
The orchestrator. Turns the engines' raw intelligence into the morning Executive
Brief:

  1. Normalize   -- pull candidate actions from every engine into one shape.
  2. Prioritize  -- score each by financial threat + urgency.
  3. Synthesize  -- either ask the LLM to rank + draft (if configured) or use the
                    built-in rule-based ranker (mock). Same output shape either way.

The output is the payload the dashboard's Executive Brief screen renders.
"""

from __future__ import annotations

from config import TOP_N_ACTIONS
from engines import available_engines, missing_engines
from llm import LLMUnavailable, call_llm, parse_json

URGENCY_WEIGHT = {"High": 3, "Medium": 2, "Low": 1}


# --------------------------------------------------------------------------
# 1. Normalize: each engine's recommendations -> a common candidate shape
# --------------------------------------------------------------------------
def _normalize(collected: dict) -> list[dict]:
    candidates = []

    # Workforce: overload/reallocation recommendations
    wf = collected.get("workforce", {})
    if wf.get("ok"):
        for r in wf["data"].get("recommendations", []):
            util = r.get("predicted_utilization", 0)
            candidates.append({
                "source": "workforce",
                "category": "Team capacity",
                "title": f"{r.get('overloaded_employee', 'A team member')} projected to {util:.0f}% capacity",
                "financial_impact": 0.0,  # workforce risk isn't dollar-denominated
                "urgency": "High" if util >= 110 else "Medium",
                "detail": r.get("alert_text", ""),
                "draft": r.get("alert_text", ""),
            })

    # Cashflow: reminders + escalations (dollar-denominated risk)
    cf = collected.get("cashflow", {})
    if cf.get("ok"):
        for r in cf["data"].get("recommendations", []):
            amount = r.get("amount", 0)
            prob = r.get("prob_late", 0)
            escalate = r.get("needs_escalation", False)
            candidates.append({
                "source": "cashflow",
                "category": "Collections" if escalate else "Cash flow",
                "title": f"{r.get('client_name', 'A client')} — ${amount:,.0f} at risk",
                "financial_impact": float(amount) * float(prob),
                "urgency": "High" if (escalate or r.get("needs_reminder")) else "Medium",
                "detail": r.get("alert_text", ""),
                "draft": r.get("alert_text", ""),
            })

    # Projects: generic — pick up alert_text + any amount-at-risk field if present
    pj = collected.get("projects", {})
    if pj.get("ok"):
        for r in pj["data"].get("recommendations", []):
            amount = r.get("amount_at_risk", r.get("budget_at_risk", 0)) or 0
            candidates.append({
                "source": "projects",
                "category": "Project health",
                "title": r.get("title", r.get("project_name", "Project at risk")),
                "financial_impact": float(amount),
                "urgency": r.get("urgency", "Medium"),
                "detail": r.get("alert_text", ""),
                "draft": r.get("alert_text", ""),
            })

    return candidates


# --------------------------------------------------------------------------
# 2. Prioritize: threat score for ranking
# --------------------------------------------------------------------------
def _threat_score(c: dict) -> float:
    # Financial impact dominates; urgency breaks ties / lifts non-dollar items.
    return c["financial_impact"] + URGENCY_WEIGHT.get(c["urgency"], 1) * 1000


# --------------------------------------------------------------------------
# 3a. Rule-based synthesis (mock — no LLM key needed)
# --------------------------------------------------------------------------
def _pick_with_variety(ranked: list[dict], n: int) -> list[dict]:
    """Surface the top item from each engine first (so every available engine is
    represented in the brief), then fill any remaining slots by threat score.
    Keeps the demo showing all three engines instead of an all-cashflow list."""
    picked, seen_sources = [], set()
    # Pass 1: highest-scoring item per source (ranked is already score-sorted)
    for c in ranked:
        if c["source"] not in seen_sources:
            picked.append(c)
            seen_sources.add(c["source"])
        if len(picked) >= n:
            return picked
    # Pass 2: fill remaining slots with the next-highest, regardless of source
    for c in ranked:
        if c not in picked:
            picked.append(c)
        if len(picked) >= n:
            break
    return picked


def _rule_based_brief(candidates: list[dict], collected: dict) -> dict:
    ranked = sorted(candidates, key=_threat_score, reverse=True)
    top = _pick_with_variety(ranked, TOP_N_ACTIONS)

    # A simple, transparent agency-health score: start at 100, subtract for risk.
    total_at_risk = sum(c["financial_impact"] for c in candidates)
    high_urgency = sum(1 for c in candidates if c["urgency"] == "High")
    score = max(0, 100 - high_urgency * 4 - int(total_at_risk / 20000))

    actions = []
    for i, c in enumerate(top, 1):
        actions.append({
            "rank": i,
            "title": c["title"],
            "category": c["category"],
            "source": c["source"],
            "urgency": c["urgency"],
            "why": c["detail"],
            "draft_message": c["draft"],
        })

    return {
        "agency_health_score": score,
        "headline": f"{high_urgency} high-urgency items today; "
                    f"${total_at_risk:,.0f} in weighted risk across engines.",
        "top_actions": actions,
        "generated_by": "rule-based (no LLM configured)",
    }


# --------------------------------------------------------------------------
# 3b. LLM synthesis
# --------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are the virtual Chief Operating Officer for a creative agency. Each "
    "morning you receive prioritized findings from three analytics engines "
    "(team capacity, cash flow, project health). Your job: (1) synthesize them "
    "into one picture of the day, (2) rank by financial threat and urgency, and "
    "(3) for the top items, write a short, ready-to-send draft the owner can "
    "approve with one click. Be concise and action-oriented."
)


def _llm_brief(candidates: list[dict], collected: dict) -> dict:
    import json
    user = (
        "Here are today's candidate findings (already scored). Return STRICT JSON "
        "only, no prose, with this shape:\n"
        '{"agency_health_score": <0-100 int>, "headline": "<one sentence>", '
        '"top_actions": [{"rank": <int>, "title": "<short>", "category": "<short>", '
        '"source": "<engine>", "urgency": "High|Medium|Low", "why": "<one sentence>", '
        '"draft_message": "<ready-to-send message>"}]}\n'
        f"Pick the top {TOP_N_ACTIONS} actions.\n\n"
        f"FINDINGS:\n{json.dumps(candidates, indent=2)}"
    )
    raw = call_llm(SYSTEM_PROMPT, user)
    brief = parse_json(raw)
    brief["generated_by"] = "llm"
    return brief


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------
def build_brief(collected: dict) -> dict:
    candidates = _normalize(collected)

    if not candidates:
        brief = {"agency_health_score": 100,
                 "headline": "No actionable findings from available engines.",
                 "top_actions": [], "generated_by": "none"}
    else:
        try:
            brief = _llm_brief(candidates, collected)
        except (LLMUnavailable, Exception):  # noqa: BLE001
            # Any LLM failure (no key, bad response, timeout) -> rule-based fallback
            brief = _rule_based_brief(candidates, collected)

    # Always attach engine availability so the UI can show what's missing.
    brief["engines"] = {
        "available": available_engines(collected),
        "unavailable": missing_engines(collected),
    }
    brief["total_candidates"] = len(candidates)
    return brief
