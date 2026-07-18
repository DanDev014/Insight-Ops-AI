"""
config.py
---------
Single source of truth for the Cash Flow Engine's business rules and feature
definitions. Keeping these here (not scattered through the code) means thresholds
can be tuned in one place and the training and inference paths can never disagree
about which columns the model expects.
"""

from __future__ import annotations

import os

# --- Business rules (from the DS 1 spec) ------------------------------------
# "the likelihood that a payment will be more than 15 days late"
LATE_THRESHOLD_DAYS = 15

# "Five days before the invoice's due date, automatically send a reminder"
REMINDER_LEAD_DAYS = 5

# Probability at/above which an invoice is treated as high-risk. Chosen at train
# time by an F1 sweep, but clamped to this range so it can never collapse to a
# degenerate boundary value (the bug that flagged every client one class).
DEFAULT_PROB_THRESHOLD = 0.5
THRESHOLD_MIN = 0.30
THRESHOLD_MAX = 0.70

# --- Feature definitions ----------------------------------------------------
# Numeric features used by both classifier and regressor.
BASE_FEATURE_COLS = [
    "amount",                 # invoice size
    "relative_amount",        # amount / client's contract value
    "payment_terms",          # contract terms
    "days_allowed",           # due_date - invoice_date
    "invoice_month",          # seasonality
    "client_engagement",      # engagement score
    "contract_value",
    "client_hist_delay",      # client's past mean delay (leakage-safe, leave-one-out)
    "client_hist_late_rate",  # client's past >15-late rate (leakage-safe)
    "num_projects",           # operational stress signals ...
    "avg_margin",
    "avg_hours_variance",
]

# Top-N industries kept as their own one-hot column; the rest collapse to "Other".
TOP_N_INDUSTRIES = 6

# Where trained artifacts live
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
ARTIFACT_PATH = os.path.join(MODELS_DIR, "cashflow_model.joblib")
