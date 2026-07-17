"""
features.py
-----------
Invoice-level feature engineering, shared by training and inference so the two
can never drift.

Two correctness decisions that fix real bugs from the original notebook:

1. LEAKAGE-SAFE CLIENT HISTORY. The original used a stored `historical_payment_delay`
   column that correlated 0.969 with the target (it was essentially the label in
   disguise). Here, a client's "past delay" features are computed leave-one-out
   from their OTHER paid invoices, so an invoice's own outcome never informs its
   own features. That's legitimate "past behaviour predicts future" signal.

2. ROBUST INDUSTRY ONE-HOT. The notebook's single-row `get_dummies(drop_first=True)`
   silently produced zero columns, mis-encoding every scored client. Here we
   one-hot against a FIXED, known column set and reindex — so training and
   inference always align, whether we're scoring 1 invoice or 1000.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import BASE_FEATURE_COLS, LATE_THRESHOLD_DAYS, TOP_N_INDUSTRIES


def _to_dt(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def client_operational_signals(projects: pd.DataFrame) -> pd.DataFrame:
    """Per-client operational stress aggregates (overrun/margin/variance)."""
    p = projects.copy()
    p["hours_variance"] = (
        (p["hours_logged"] - p["hours_estimated"])
        / p["hours_estimated"].replace(0, np.nan)
    )
    agg = p.groupby("client_id").agg(
        num_projects=("id", "count"),
        avg_margin=("margin", "mean"),
        avg_hours_variance=("hours_variance", "mean"),
    ).reset_index()
    return agg


def _leave_one_out_stats(paid: pd.DataFrame) -> pd.DataFrame:
    """For each paid invoice, compute the client's mean delay and >15-late rate
    over their OTHER paid invoices (leave-one-out). Falls back to the global mean
    for clients with only one paid invoice."""
    df = paid.copy()
    df["is_late"] = (df["days_late"] > LATE_THRESHOLD_DAYS).astype(int)

    grp = df.groupby("client_id")
    sum_delay = grp["days_late"].transform("sum")
    cnt = grp["days_late"].transform("count")
    sum_late = grp["is_late"].transform("sum")

    global_delay = df["days_late"].mean()
    global_late = df["is_late"].mean()

    # leave-one-out = (group total - this row) / (group count - 1)
    loo_delay = (sum_delay - df["days_late"]) / (cnt - 1)
    loo_late = (sum_late - df["is_late"]) / (cnt - 1)
    df["client_hist_delay"] = loo_delay.where(cnt > 1, global_delay)
    df["client_hist_late_rate"] = loo_late.where(cnt > 1, global_late)
    return df


def _client_full_history(paid: pd.DataFrame) -> pd.DataFrame:
    """Full (not leave-one-out) client history, used to score OUTSTANDING invoices
    which were never part of training."""
    df = paid.copy()
    df["is_late"] = (df["days_late"] > LATE_THRESHOLD_DAYS).astype(int)
    hist = df.groupby("client_id").agg(
        client_hist_delay=("days_late", "mean"),
        client_hist_late_rate=("is_late", "mean"),
    ).reset_index()
    return hist, df["days_late"].mean(), df["is_late"].mean()


def _add_industry_dummies(df, clients, industry_cols=None):
    """One-hot industry against a fixed column set. If industry_cols is given
    (inference), reindex to exactly those columns; else derive and return them
    (training)."""
    merged = df.merge(clients[["id", "industry"]], left_on="client_id",
                      right_on="id", how="left", suffixes=("", "_c"))
    if industry_cols is None:
        top = merged["industry"].value_counts().nlargest(TOP_N_INDUSTRIES).index
        grp = merged["industry"].where(merged["industry"].isin(top), other="Other")
        dummies = pd.get_dummies(grp, prefix="industry")  # NO drop_first
        industry_cols = list(dummies.columns)
        top_industries = list(top)
    else:
        # reconstruct the grouping used at train time from the known columns
        known = {c.replace("industry_", "") for c in industry_cols}
        grp = merged["industry"].where(merged["industry"].isin(known), other="Other")
        dummies = pd.get_dummies(grp, prefix="industry")
        dummies = dummies.reindex(columns=industry_cols, fill_value=0)
        top_industries = None
    out = pd.concat([df.reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)
    return out, industry_cols, top_industries


def build_training_frame(tables: dict) -> tuple[pd.DataFrame, list, list]:
    """Return (feature_frame_for_paid_invoices, feature_cols, industry_cols)."""
    payments = _to_dt(tables["payments"].copy(),
                      ["invoice_date", "due_date", "paid_date"])
    clients = tables["clients"].copy()
    projects = tables["projects"].copy()

    paid = payments[payments["paid_date"].notna()].copy()
    paid["days_late"] = (paid["paid_date"] - paid["due_date"]).dt.days
    paid["days_allowed"] = (paid["due_date"] - paid["invoice_date"]).dt.days
    paid["invoice_month"] = paid["invoice_date"].dt.month

    # merge client static fields
    paid = paid.merge(
        clients[["id", "contract_value", "payment_terms", "engagement_score"]],
        left_on="client_id", right_on="id", how="left", suffixes=("", "_cl"),
    )
    paid = paid.rename(columns={"engagement_score": "client_engagement"})
    paid["relative_amount"] = paid["amount"] / paid["contract_value"].replace(0, 1)

    # leakage-safe history
    paid = _leave_one_out_stats(paid)

    # operational signals
    ops = client_operational_signals(projects)
    paid = paid.merge(ops, on="client_id", how="left")
    for c in ["num_projects", "avg_margin", "avg_hours_variance"]:
        paid[c] = paid[c].fillna(0)

    # industry one-hot
    paid, industry_cols, _ = _add_industry_dummies(paid, clients)

    feature_cols = BASE_FEATURE_COLS + industry_cols
    paid["is_late"] = (paid["days_late"] > LATE_THRESHOLD_DAYS).astype(int)
    return paid, feature_cols, industry_cols


def build_scoring_frame(tables: dict, industry_cols: list) -> pd.DataFrame:
    """Feature frame for OUTSTANDING (unpaid) invoices, aligned to training cols."""
    payments = _to_dt(tables["payments"].copy(),
                      ["invoice_date", "due_date", "paid_date"])
    clients = tables["clients"].copy()
    projects = tables["projects"].copy()

    paid = payments[payments["paid_date"].notna()].copy()
    paid["days_late"] = (paid["paid_date"] - paid["due_date"]).dt.days
    hist, global_delay, global_late = _client_full_history(paid)

    out = payments[payments["paid_date"].isna()].copy()
    out["days_allowed"] = (out["due_date"] - out["invoice_date"]).dt.days
    out["invoice_month"] = out["invoice_date"].dt.month

    out = out.merge(
        clients[["id", "name", "contract_value", "payment_terms", "engagement_score"]],
        left_on="client_id", right_on="id", how="left", suffixes=("", "_cl"),
    )
    out = out.rename(columns={"engagement_score": "client_engagement",
                              "name": "client_name"})
    out["relative_amount"] = out["amount"] / out["contract_value"].replace(0, 1)

    out = out.merge(hist, on="client_id", how="left")
    out["client_hist_delay"] = out["client_hist_delay"].fillna(global_delay)
    out["client_hist_late_rate"] = out["client_hist_late_rate"].fillna(global_late)

    ops = client_operational_signals(projects)
    out = out.merge(ops, on="client_id", how="left")
    for c in ["num_projects", "avg_margin", "avg_hours_variance"]:
        out[c] = out[c].fillna(0)

    out, _, _ = _add_industry_dummies(out, clients, industry_cols=industry_cols)
    return out
