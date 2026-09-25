#!/usr/bin/env python3
"""
Stop-loss sensitivity test for the UVXY bear call spread.

Compares the baseline strategy (no stop) against stop-loss exits triggered at
N× the original credit received (stop_multiple = 2 and 3).

Stop-loss mechanics:
  stop_multiple=2 → exit when it costs 2× your credit to close (lost 1× credit)
  stop_multiple=3 → exit when it costs 3× your credit to close (lost 2× credit)

Usage:
  PYTHONPATH=src python run_uvxy_stop_loss_test.py
  PYTHONPATH=src python run_uvxy_stop_loss_test.py --refresh
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta

import numpy as np
import pandas as pd

from lib.mysql_lib import fetch_options_cache
from lib.studies.call_spread_study import (
    build_call_spread_trades,
    find_spread_exits,
    compute_spread_metrics,
)
from lib.studies.put_study import fetch_vix_data
from lib.studies.straddle_study import sync_options_cache, UVXY_SPLIT_DATES

UVXY_START = date(2018, 1, 12)

# ── Baseline strategy parameters (from combined study) ─────────────────────────
SHORT_DELTA    = 0.50
WING_WIDTH     = 0.10
PROFIT_TAKE    = 0.50
MAX_SPREAD_PCT = 0.25
DTE            = 20
DTE_TOL        = 5
VIX_MIN        = 20.0   # call spread only when VIX ≥ 20 (per optimizer)


def run_scenario(
    df_calls: pd.DataFrame,
    vix_lookup: pd.Series,
    stop_multiple: float | None,
) -> pd.DataFrame:
    """Build entries, apply stop-loss, compute metrics. Returns closed trades only."""
    positions = build_call_spread_trades(
        df_calls,
        short_delta_target=SHORT_DELTA,
        wing_delta_width=WING_WIDTH,
        dte_target=DTE,
        dte_tol=DTE_TOL,
        entry_weekday=4,
        split_dates=UVXY_SPLIT_DATES,
        max_delta_err=0.08,
        max_spread_pct=MAX_SPREAD_PCT,
    )
    positions["vix_on_entry"] = positions["entry_date"].map(vix_lookup)

    # All-VIX for this test (same as combined study for the spread side)
    positions = find_spread_exits(
        positions, df_calls,
        profit_take_pct=PROFIT_TAKE,
        stop_multiple=stop_multiple,
    )
    positions = compute_spread_metrics(positions)
    return positions[~positions["split_flag"] & ~positions["is_open"]].copy()


def print_comparison(scenarios: dict[str, pd.DataFrame]) -> None:
    """Print per-year and overall comparison across all stop scenarios."""
    bar = "=" * 88

    # Collect all years
    all_years = sorted(set(
        yr
        for df in scenarios.values()
        for yr in pd.to_datetime(df["entry_date"]).dt.year.unique()
    ))

    labels = list(scenarios.keys())

    # Header
    print(f"\n{bar}")
    print("  UVXY Bear Call Spread — Stop-Loss Sensitivity")
    print(f"  short_delta={SHORT_DELTA}  wing={WING_WIDTH}  profit_take={int(PROFIT_TAKE*100)}%"
          f"  max_spread={int(MAX_SPREAD_PCT*100)}%  DTE={DTE}")
    print(bar)

    col_w = 30
    hdr = f"  {'Year':>4}  {'N':>4}"
    sub = f"  {'':>4}  {'':>4}"
    for lbl in labels:
        hdr += f"  {lbl:^{col_w}}"
        sub += f"  {'ROC%':>6} {'Win%':>5} {'Stop%':>5} {'MaxROC%':>8} {'MinROC%':>8}"
    print(hdr)
    print(sub)
    print("  " + "-" * (10 + len(labels) * (col_w + 2)))

    for yr in all_years:
        baseline_df = scenarios[labels[0]]
        n = int((pd.to_datetime(baseline_df["entry_date"]).dt.year == yr).sum())
        row = f"  {yr:>4}  {n:>4}"
        for lbl in labels:
            df = scenarios[lbl]
            grp = df[pd.to_datetime(df["entry_date"]).dt.year == yr]
            if grp.empty:
                row += f"  {'—':^{col_w}}"
                continue
            roc     = grp["roc"].mean() * 100
            win_pct = grp["is_win"].mean() * 100
            stop_pct = (grp["exit_type"] == "stop").mean() * 100 if "stop" in grp["exit_type"].values else 0.0
            max_roc = grp["roc"].max() * 100
            min_roc = grp["roc"].min() * 100
            row += f"  {roc:>+5.2f}% {win_pct:>4.1f}% {stop_pct:>4.1f}% {max_roc:>+7.2f}% {min_roc:>+7.2f}%"
        print(row)

    print("  " + "-" * (10 + len(labels) * (col_w + 2)))

    # Totals
    for yr_label, mask_fn in [
        ("ALL", lambda df: df),
        ("2018-22", lambda df: df[pd.to_datetime(df["entry_date"]).dt.year <= 2022]),
        ("2023+",   lambda df: df[pd.to_datetime(df["entry_date"]).dt.year >= 2023]),
    ]:
        first_df = mask_fn(scenarios[labels[0]])
        n = len(first_df)
        row = f"  {yr_label:>4}  {n:>4}"
        for lbl in labels:
            grp = mask_fn(scenarios[lbl])
            if grp.empty:
                row += f"  {'—':^{col_w}}"
                continue
            roc     = grp["roc"].mean() * 100
            win_pct = grp["is_win"].mean() * 100
            stop_pct = (grp["exit_type"] == "stop").mean() * 100 if "stop" in grp["exit_type"].values else 0.0
            max_roc = grp["roc"].max() * 100
            min_roc = grp["roc"].min() * 100
            row += f"  {roc:>+5.2f}% {win_pct:>4.1f}% {stop_pct:>4.1f}% {max_roc:>+7.2f}% {min_roc:>+7.2f}%"
        print(row)

    print(f"\n  Columns: ROC%=avg roc  Win%=win rate  Stop%=pct of trades stopped out")
    print(f"           MaxROC%/MinROC%=best/worst single trade")
    print(bar)

    # Exit type breakdown
    print(f"\n  Exit type breakdown:")
    print(f"  {'Scenario':<20}  {'N':>5}  {'Early%':>7}  {'Stop%':>6}  {'Expiry%':>8}")
    print("  " + "-" * 50)
    for lbl, df in scenarios.items():
        n       = len(df)
        early   = (df["exit_type"] == "early").sum()
        stop    = (df["exit_type"] == "stop").sum()
        expiry  = (df["exit_type"] == "expiry").sum()
        print(f"  {lbl:<20}  {n:>5}  {early/n*100:>6.1f}%  {stop/n*100:>5.1f}%  {expiry/n*100:>7.1f}%")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UVXY stop-loss sensitivity test",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--refresh", action="store_true", help="Force Athena re-sync")
    args = parser.parse_args()

    end = date.today()

    print("Syncing UVXY options cache...")
    sync_options_cache("UVXY", UVXY_START, force=args.refresh)

    fetch_end = end + timedelta(days=DTE + 10)
    print(f"Loading options from MySQL ({UVXY_START} → {fetch_end}) ...")
    df_opts = fetch_options_cache("UVXY", UVXY_START, fetch_end)
    print(f"  {len(df_opts):,} rows loaded.")

    print("Fetching VIX data ...")
    df_vix = fetch_vix_data(UVXY_START - timedelta(days=5), end)
    vix_lookup = df_vix.set_index("trade_date")["vix_close"]

    df_calls = df_opts[df_opts["cp"] == "C"].copy()

    print("\nRunning scenarios...")
    scenarios = {}
    for label, stop_mult in [
        ("No stop (baseline)", None),
        ("Stop at 2× credit",  2.0),
        ("Stop at 3× credit",  3.0),
    ]:
        print(f"  {label} ...", end=" ", flush=True)
        df = run_scenario(df_calls, vix_lookup, stop_mult)
        scenarios[label] = df
        print(f"{len(df)} trades.")

    print_comparison(scenarios)


if __name__ == "__main__":
    main()
