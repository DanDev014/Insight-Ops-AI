"""
engines.py
----------
Fans out to each configured analytics engine's /intelligence endpoint and
collects their JSON. Resilient by design: an engine that has no URL, times out,
or errors is simply marked unavailable — the brief is still built from whatever
responded. This is what lets the demo work when only some engines are deployed.
"""

from __future__ import annotations

import requests

from config import ENGINES, FETCH_TIMEOUT_SECONDS


def collect_intelligence() -> dict:
    """Return {engine_name: {"ok": bool, "data": {...} | None, "error": str | None}}."""
    results = {}
    for name, base_url, path in ENGINES:
        if not base_url:
            results[name] = {"ok": False, "data": None, "error": "no URL configured"}
            continue
        url = base_url.rstrip("/") + path
        try:
            resp = requests.get(url, timeout=FETCH_TIMEOUT_SECONDS,
                                headers={"accept": "application/json"})
            resp.raise_for_status()
            results[name] = {"ok": True, "data": resp.json(), "error": None}
        except Exception as exc:  # noqa: BLE001
            results[name] = {"ok": False, "data": None, "error": str(exc)}
    return results


def available_engines(collected: dict) -> list[str]:
    return [name for name, r in collected.items() if r["ok"]]


def missing_engines(collected: dict) -> list[str]:
    return [name for name, r in collected.items() if not r["ok"]]
