#!/usr/bin/env python3
"""
Re-run the top ~1,000 tickers from the February bulk put spread study using
standard parameters (0.30Δ short / 0.15Δ long), so results are comparable to
the current strategy suite (SOXX, XLV, XLF, GLD, etc.).

The February study used "50-15" parameters (near-ATM short, very wide wing),
which inflates ROC vs standard 0.20-0.30Δ strategies. This re-run produces
apples-to-apples data for identifying new per-ticker study candidates.

Filter for selecting tickers from the bulk CSV:
  - pricing == "mid"
  - n_entries >= 25  (meaningful sample in the original study)
  - roc > 0          (any positive return)
  - Sorted by win_rate × roc descending
  - Top N_TICKERS selected

New study parameters:
  - short_delta = 0.30  (standard short side)
  - long_delta  = 0.15  (standard wing)
  - dte         = 30    (hardcoded in put_spread_study)
  - entry_day   = Friday (hardcoded in put_spread_study)
  - date range  = 2020-12-15 → today

Usage:
    AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_standard_put_spread_bulk.py
    AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_standard_put_spread_bulk.py --top 500
    AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src python run_standard_put_spread_bulk.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lib.condor_tools import put_spread_study

# ── Configuration ──────────────────────────────────────────────────────────────

BULK_CSV      = "src/lib/output/put_spread_study_20260222154422.csv"
SHORT_DELTA   = 0.30
LONG_DELTA    = 0.15
STUDY_DESC    = "30-15 put spread"
TS_END        = date.today().isoformat()
TS_START      = "2020-12-15"

DEFAULT_N     = 1000
MIN_ENTRIES   = 25      # minimum n_entries in the original 50-15 study
MIN_ROC       = 0.0     # any positive return in original study

# ── Already-studied tickers (skip — already have full per-ticker playbooks) ───
ALREADY_STUDIED = {
    "UVXY", "UVIX", "TLT", "TMF", "GLD", "XLV", "XLF", "SOXX", "SQQQ",
    "YINN", "ASHR", "BJ", "USO", "XLE", "XOP", "IWM", "QQQ", "GDX",
    "EEM", "FXI", "XLU", "XLP", "INDA", "SPY", "IWV", "VOO", "SSO",
}


def load_candidates(n: int) -> list[str]:
    """Load top-N tickers from the February bulk study CSV."""
    with open(BULK_CSV) as f:
        rows = list(csv.DictReader(f))

    mid = [r for r in rows if r["pricing"] == "mid"]
    print(f"Loaded {len(mid)} mid-pricing rows from {BULK_CSV}")

    # Basic filters
    filtered = []
    for r in mid:
        n_entries = int(r["n_entries"])
        roc       = float(r["roc"])
        if n_entries >= MIN_ENTRIES and roc > MIN_ROC:
            r["score"] = float(r["win_rate"]) * roc
            filtered.append(r)
    print(f"After n>={MIN_ENTRIES} and ROC>{MIN_ROC}: {len(filtered)} tickers")

    # Exclude already-studied
    filtered = [r for r in filtered if r["ticker"] not in ALREADY_STUDIED]
    print(f"After excluding already-studied: {len(filtered)} tickers")

    # Sort by win_rate × ROC descending
    filtered.sort(key=lambda r: r["score"], reverse=True)

    top = filtered[:n]
    print(f"\nTop {len(top)} tickers selected (by win_rate × ROC):")
    for i, r in enumerate(top[:20], 1):
        print(f"  {i:4d}. {r['ticker']:<8} n={r['n_entries']:>4}  "
              f"win={float(r['win_rate']):.1%}  ROC={float(r['roc']):+.3f}  score={r['score']:.4f}")
    if len(top) > 20:
        print(f"  ...and {len(top) - 20} more")

    return [r["ticker"] for r in top]


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk re-run with standard 30-15 put spread params")
    parser.add_argument("--top",     type=int, default=DEFAULT_N,
                        help=f"Number of tickers to re-study (default: {DEFAULT_N})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print selected tickers but do not run Athena queries")
    args = parser.parse_args()

    tickers = load_candidates(args.top)

    print(f"\n{'='*70}")
    print(f"  STANDARD PUT SPREAD BULK RE-RUN")
    print(f"  Short delta: {SHORT_DELTA}Δ  |  Long delta: {LONG_DELTA}Δ")
    print(f"  DTE: 30  |  Entry: Fridays  |  Date range: {TS_START} → {TS_END}")
    print(f"  Tickers: {len(tickers)}  |  Study: '{STUDY_DESC}'")
    print(f"{'='*70}")

    if args.dry_run:
        print("\n[DRY RUN] Would study the following tickers:")
        for i, t in enumerate(tickers, 1):
            print(f"  {i:4d}. {t}")
        print(f"\n[DRY RUN] No Athena queries run.")
        return

    put_spread_study(
        tickers,
        ts_start=TS_START,
        ts_end=TS_END,
        short_delta=SHORT_DELTA,
        long_delta=LONG_DELTA,
        study_description=STUDY_DESC,
    )


if __name__ == "__main__":
    main()
