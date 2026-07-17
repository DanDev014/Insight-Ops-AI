"""
Non-destructive patch: regenerates `paid_date` on existing `payments` rows so that
payment delay actually correlates with each client's `historical_payment_delay`.

WHY THIS EXISTS
----------------
The original seed script assigned clients a risk tier (historical_payment_delay,
engagement_score, contract_value all tied to tier) but then generated each invoice's
actual `paid_date` from a delay drawn uniformly at random, completely independent of
that tier. Net effect: the label your model is trying to predict (derived from actual
paid_date) has no real relationship to any client feature, including the client's own
historical_payment_delay. No amount of feature engineering or model tuning can recover
a signal that was never encoded into the data.

WHAT THIS SCRIPT DOES
----------------------
- Reads each client's existing `historical_payment_delay` (untouched, used only as an
  anchor).
- For every payment row that ALREADY has a paid_date (i.e. was not one of the ~20%
  seeded as still-outstanding), recomputes paid_date = due_date + a noisy delay drawn
  around that client's anchor -- correlated, not identical, so the model has to learn
  a real but imperfect relationship rather than trivially copying one column.
- Leaves untouched: row counts, ids, every other column, every other table, and any
  invoice that was seeded with paid_date = NULL (still outstanding).

This is UPDATE-only. No TRUNCATE, no DELETE, no schema changes. Safe to run against a
shared database, but see the coordination note in step 1 of the instructions below.
"""

import os
import random
import psycopg2
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Set a seed so the run is reproducible if you need to explain/redo it later.
random.seed(42)

# How much noise to add around each client's historical_payment_delay anchor.
# A tight noise band keeps the correlation strong but not perfect/leaky.
NOISE_STD_DAYS = 5
# Occasionally an invoice pays early or late regardless of the client's usual pattern
# (real businesses have outlier invoices too) -- keeps the data from looking too clean.
OUTLIER_PROBABILITY = 0.08
OUTLIER_RANGE_DAYS = (-15, 45)


def sample_delay(anchor_delay: int) -> int:
    """Draw a settlement delay correlated with, but not identical to, the client's anchor."""
    if random.random() < OUTLIER_PROBABILITY:
        return random.randint(*OUTLIER_RANGE_DAYS)
    noisy = round(random.gauss(mu=anchor_delay, sigma=NOISE_STD_DAYS))
    # Don't let noise push a reliable client's invoice absurdly early/late.
    return max(-10, min(noisy, 90))


def run(dry_run: bool = True):
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in your environment variables.")
        return

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Pull each client's anchor delay.
        cur.execute("SELECT id, historical_payment_delay FROM clients;")
        client_anchors = dict(cur.fetchall())
        print(f"Loaded anchor delay for {len(client_anchors)} clients.")

        # Pull only invoices that were actually marked paid (leave NULL paid_date rows alone).
        cur.execute("""
            SELECT id, client_id, due_date
            FROM payments
            WHERE paid_date IS NOT NULL;
        """)
        paid_rows = cur.fetchall()
        print(f"Found {len(paid_rows)} paid invoices eligible for patching.")

        updates = []
        for payment_id, client_id, due_date in paid_rows:
            anchor = client_anchors.get(client_id, 10)  # fallback if a client is somehow missing
            delay_days = sample_delay(anchor)
            new_paid_date = due_date + timedelta(days=delay_days)
            updates.append((new_paid_date, payment_id))

        print(f"\nPreview of first 10 updates:")
        print(f"{'payment_id':<12}{'new_paid_date':<15}")
        for new_paid_date, payment_id in updates[:10]:
            print(f"{payment_id:<12}{str(new_paid_date):<15}")

        if dry_run:
            print("\nDRY RUN ONLY -- no changes written. Re-run with dry_run=False to apply.")
            return

        cur.executemany(
            "UPDATE payments SET paid_date = %s WHERE id = %s;",
            updates,
        )
        conn.commit()
        print(f"\nSUCCESS: Updated paid_date on {len(updates)} payment rows. "
              f"Row count and every other column/table are unchanged.")

    except Exception as e:
        print(f"\nERROR during patch: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    import sys
    # Default to a dry run unless explicitly told to apply.
    apply_changes = "--apply" in sys.argv
    run(dry_run=not apply_changes)
