#!/usr/bin/env python3
"""
Dry-run strangle study on 2 tickers to verify strangle_study_det population.

Usage:
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python3 dry_run_strangle.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lib.condor_tools import strangle_study
from lib.mysql_lib import _get_conn

TICKERS = ["CORT", "WES"]

print(f"=== Dry run: {TICKERS} ===\n")
strangle_study(
    TICKERS,
    ts_start="2020-12-15",
    ts_end="2026-03-16",
    study_description="dry-run 2-ticker strangle",
)

# Verify: show strangle_study_det rows for the new study
conn = _get_conn()
cur = conn.cursor()
cur.execute("SELECT MAX(id) FROM studies")
study_id = cur.fetchone()[0]
print(f"\n=== strangle_study_det sample (study_id={study_id}) ===")
cur.execute("""
    SELECT sd.ticker, sd.entry_date, sd.expiry, sd.pricing,
           ssd.call_delta, ssd.put_delta
    FROM study_detail sd
    JOIN strangle_study_det ssd ON ssd.study_detail_id = sd.id
    WHERE sd.study_id = %s
    ORDER BY sd.ticker, sd.entry_date, sd.pricing
    LIMIT 20
""", (study_id,))
rows = cur.fetchall()
print(f"{'Ticker':<8} {'Entry':>12} {'Expiry':>12} {'Pricing':>7} {'CallΔ':>8} {'PutΔ':>8}")
print("-" * 60)
for r in rows:
    print(f"{r[0]:<8} {str(r[1]):>12} {str(r[2]):>12} {r[3]:>7} {float(r[4]):>8.4f} {float(r[5]):>8.4f}")
cur.execute("""
    SELECT COUNT(*) FROM strangle_study_det ssd
    JOIN study_detail sd ON sd.id = ssd.study_detail_id
    WHERE sd.study_id = %s
""", (study_id,))
print(f"\nTotal strangle_study_det rows: {cur.fetchone()[0]}")
conn.close()
