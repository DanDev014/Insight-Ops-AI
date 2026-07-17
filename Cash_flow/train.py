"""
train.py
--------
Trains the Cash Flow Engine and saves a single artifact bundle the API loads.

Two models (the DS 1 spec asks for both):
  * Classifier -> probability an invoice is paid MORE THAN 15 days late.
  * Regressor  -> the expected number of days late (the "...by 18 days" figure).

Threshold selection is the fix for the notebook's collapse bug: instead of
Youden's J (which picked 0.873, just above every positive prediction, flagging
everyone one class), we sweep interior thresholds for best F1 and CLAMP the
result to [0.30, 0.70] so it can never land on a degenerate boundary.

Run:
    python train.py
"""

from __future__ import annotations

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    classification_report, confusion_matrix, f1_score,
    mean_absolute_error, roc_auc_score,
)
from sklearn.model_selection import train_test_split

import database
from config import (ARTIFACT_PATH, DEFAULT_PROB_THRESHOLD, THRESHOLD_MAX,
                    THRESHOLD_MIN, LATE_THRESHOLD_DAYS)
from features import build_training_frame


def choose_threshold(y_true, probs) -> float:
    """Sweep interior thresholds for best F1, clamped so it can't collapse."""
    candidates = np.linspace(THRESHOLD_MIN, THRESHOLD_MAX, 41)
    f1s = [f1_score(y_true, (probs >= t).astype(int), zero_division=0) for t in candidates]
    best = float(candidates[int(np.argmax(f1s))])
    return best if max(f1s) > 0 else DEFAULT_PROB_THRESHOLD


def main():
    tables = database.load_tables()
    frame, feature_cols, industry_cols = build_training_frame(tables)

    X = frame[feature_cols]
    y_clf = frame["is_late"]
    y_reg = frame["days_late"]

    print(f"Training on {len(X)} paid invoices | "
          f"{y_clf.mean() * 100:.1f}% are >{LATE_THRESHOLD_DAYS} days late")

    X_tr, X_te, ycl_tr, ycl_te, yrg_tr, yrg_te = train_test_split(
        X, y_clf, y_reg, test_size=0.25, random_state=42, stratify=y_clf
    )

    # --- Classifier ---------------------------------------------------------
    clf = RandomForestClassifier(
        n_estimators=300, max_depth=8, min_samples_leaf=3,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )
    clf.fit(X_tr, ycl_tr)
    probs_te = clf.predict_proba(X_te)[:, 1]

    threshold = choose_threshold(ycl_tr, clf.predict_proba(X_tr)[:, 1])
    preds_te = (probs_te >= threshold).astype(int)

    print("\n=== CLASSIFIER (is invoice >15 days late?) ===")
    print(f"Chosen threshold: {threshold:.3f}")
    print(f"ROC AUC: {roc_auc_score(ycl_te, probs_te):.3f}")
    print(f"F1:      {f1_score(ycl_te, preds_te):.3f}")
    print(f"Flagged high-risk: {int(preds_te.sum())} of {len(preds_te)}")
    print(classification_report(ycl_te, preds_te,
          target_names=["On-time", "Late >15d"], zero_division=0))
    print("Confusion matrix [rows=actual, cols=pred]:")
    print(confusion_matrix(ycl_te, preds_te))

    # --- Regressor ----------------------------------------------------------
    reg = RandomForestRegressor(
        n_estimators=300, max_depth=8, min_samples_leaf=3,
        random_state=42, n_jobs=-1,
    )
    reg.fit(X_tr, yrg_tr)
    reg_pred = reg.predict(X_te)
    print("\n=== REGRESSOR (how many days late?) ===")
    print(f"MAE: {mean_absolute_error(yrg_te, reg_pred):.1f} days")

    # --- Save bundle --------------------------------------------------------
    artifacts = {
        "clf": clf,
        "reg": reg,
        "feature_cols": feature_cols,
        "industry_cols": industry_cols,
        "threshold": threshold,
        "late_threshold_days": LATE_THRESHOLD_DAYS,
        "metrics": {
            "roc_auc": float(roc_auc_score(ycl_te, probs_te)),
            "f1": float(f1_score(ycl_te, preds_te)),
            "reg_mae": float(mean_absolute_error(yrg_te, reg_pred)),
        },
    }
    joblib.dump(artifacts, ARTIFACT_PATH)
    print(f"\nSaved model bundle -> {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
