#!/usr/bin/env python3
"""
Long Straddle — Early Exit Rule Analysis

Since we only have entry + expiry settlement (no intraday), this script simulates
exit rules by capping/flooring the realised ROC:

  profit_cap: min(roc, cap)        — take profit when up X%
  loss_floor: max(roc, -floor)     — stop out when down X%

This is an optimistic model for profit caps (assumes exit at exactly the target)
and a pessimistic model for stops (assumes you exit at exactly the floor, ignoring
trades that would recover). Results should be read as directional, not precise.

The analysis runs on proper OOS data using the walk-forward fold structure
from run_straddle_ticker_walkforward.py.

Filtering
---------
Trades with straddle cost < MIN_COST are excluded — these are effectively
penny straddles where ROC becomes meaningless (e.g. $0.05 cost → 1000x gain
on any move).

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_straddle_exit_analysis.py
  ... --min-cost 0.50    # default $0.50 minimum straddle cost
  ... --csv              # save results to CSV
"""

from __future__ import annotations

import argparse
import os
from datetime import date

import numpy as np
import pandas as pd

from lib.mysql_lib import _get_engine
from lib.studies.iron_fly_features import load_fvr_cached
from run_long_straddle_study import (
    assemble_long_straddle,
    compute_roc_buyer,
    load_all_legs,
)

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_START  = date(2018, 1, 1)
FVR_GATE       = 1.20
TEST_YEARS     = [2021, 2022, 2023, 2024, 2025]
MIN_COST       = 0.50      # minimum straddle cost in $ (removes penny straddles)
MIN_N_FVR      = 7         # IS minimum trades for ticker qualification


# ── Exit rule simulation ───────────────────────────────────────────────────────

def apply_exit_rule(roc: pd.Series, cap: float | None, floor: float | None) -> pd.Series:
    """
    Simulate an exit rule by clipping realised ROC.

    cap  : take-profit target (% ROC). None = no cap.
    floor: stop-loss floor   (% ROC loss, positive number). None = no stop.
           e.g. floor=50 means exit when down 50% (roc = -50%).
    """
    r = roc.copy()
    if floor is not None:
        r = r.clip(lower=-floor)
    if cap is not None:
        r = r.clip(upper=cap)
    return r


def _stats(roc: pd.Series) -> dict:
    if len(roc) < 3:
        return dict(n=len(roc), win=np.nan, avg_roc=np.nan, sharpe=np.nan)
    avg = roc.mean()
    std = roc.std()
    win = (roc > 0).mean()
    return dict(n=len(roc), win=win, avg_roc=avg, sharpe=avg/std if std > 0 else 0.0)


# ── Walk-forward OOS ──────────────────────────────────────────────────────────

def _qualify(df: pd.DataFrame, min_n: int) -> list[str]:
    approved = []
    for ticker, grp in df.groupby("ticker"):
        if len(grp) < min_n:
            continue
        avg = grp["roc"].mean()
        std = grp["roc"].std()
        sh  = avg / std if std > 0 else 0.0
        if avg > 0 and sh > 0:
            approved.append(ticker)
    return approved


def run_exit_analysis(df: pd.DataFrame, exit_rules: list[tuple]) -> pd.DataFrame:
    """
    For each exit rule, run the walk-forward and collect OOS stats per fold.

    df must have: ticker, entry_date, roc, win, fvr_put_30_90, cost
    exit_rules: list of (label, cap, floor) tuples
    """
    df = df.copy()
    df["year"] = pd.to_datetime(df["entry_date"]).dt.year
    df_fvr = df.dropna(subset=["fvr_put_30_90"])
    df_fvr_gated = df_fvr[df_fvr["fvr_put_30_90"] >= FVR_GATE]

    records = []

    for test_year in TEST_YEARS:
        is_fvr  = df_fvr_gated[df_fvr_gated["year"] < test_year]
        oos_fvr = df_fvr_gated[df_fvr_gated["year"] == test_year]

        approved = _qualify(is_fvr, MIN_N_FVR)
        oos_approved = oos_fvr[oos_fvr["ticker"].isin(approved)].copy()

        for label, cap, floor in exit_rules:
            sim_roc = apply_exit_rule(oos_approved["roc"], cap=cap, floor=floor)
            s = _stats(sim_roc)
            records.append(dict(
                test_year=test_year, rule=label,
                cap=cap, floor=floor,
                n_tickers=oos_approved["ticker"].nunique(),
                **s,
            ))

    return pd.DataFrame(records)


# ── FVR bucket analysis ───────────────────────────────────────────────────────

def fvr_bucket_exit(df: pd.DataFrame, exit_rules: list[tuple]) -> pd.DataFrame:
    """
    For each FVR bucket and each exit rule, compute full-period stats
    on the approved list (not walk-forward — for directional sizing insight).
    """
    app = pd.read_csv("straddle_walkforward_ticker_persistence.csv")
    approved = set(app[app["n_folds"] >= 3]["ticker"].tolist())

    df_app = df[
        df["ticker"].isin(approved) &
        df["fvr_put_30_90"].notna() &
        (df["fvr_put_30_90"] >= FVR_GATE)
    ].copy()

    buckets = [
        ("1.20–1.30", 1.20, 1.30),
        ("1.30–1.40", 1.30, 1.40),
        ("≥1.40",     1.40, 9999.),
    ]

    records = []
    for blabel, blo, bhi in buckets:
        slice_ = df_app[
            (df_app["fvr_put_30_90"] >= blo) &
            (df_app["fvr_put_30_90"] <  bhi)
        ]
        for rlabel, cap, floor in exit_rules:
            sim_roc = apply_exit_rule(slice_["roc"], cap=cap, floor=floor)
            s = _stats(sim_roc)
            s["fvr_bucket"] = blabel
            s["rule"]       = rlabel
            records.append(s)

    return pd.DataFrame(records)


# ── Printing ──────────────────────────────────────────────────────────────────

def print_walkforward_summary(results: pd.DataFrame) -> None:
    """Aggregate OOS across 5 folds per exit rule."""
    print(f"\n{'='*78}")
    print(f"  EXIT RULE COMPARISON — OOS aggregate (Var B approved, FVR≥{FVR_GATE}, "
          f"min_cost applied)")
    print(f"  Avg across {len(TEST_YEARS)} test years  [{min(TEST_YEARS)}–{max(TEST_YEARS)}]")
    print(f"{'='*78}")
    print(f"  {'Rule':<30}  {'avg_N':>7}  {'Win%':>6}  {'Avg ROC%':>9}  "
          f"{'Avg Sharpe':>11}  {'vs baseline':>12}")
    print(f"  {'-'*76}")

    # compute per-rule aggregate
    baseline_sh = None
    for rule in results["rule"].unique():
        rows = results[results["rule"] == rule].dropna(subset=["avg_roc"])
        if rows.empty:
            continue
        avg_n  = rows["n"].mean()
        avg_w  = rows["win"].mean()
        avg_r  = rows["avg_roc"].mean()
        avg_sh = rows["sharpe"].mean()
        if baseline_sh is None:
            baseline_sh = avg_sh
            delta_str = "   (baseline)"
        else:
            d = avg_sh - baseline_sh
            delta_str = f"  {d:>+.4f} Sharpe"
        print(f"  {rule:<30}  {avg_n:>7.0f}  {avg_w*100:>6.1f}%  {avg_r:>+9.2f}%  "
              f"{avg_sh:>+11.4f}  {delta_str}")


def print_per_year(results: pd.DataFrame, rules_to_show: list[str]) -> None:
    """Per-year breakdown for a subset of rules."""
    print(f"\n{'='*78}")
    print(f"  PER-YEAR BREAKDOWN (selected rules)")
    print(f"{'='*78}")
    for year in TEST_YEARS:
        yr = results[results["test_year"] == year]
        print(f"\n  ── {year} ──")
        print(f"  {'Rule':<30}  {'N':>6}  {'Win%':>6}  {'Avg ROC%':>9}  {'Sharpe':>8}")
        for rule in rules_to_show:
            row = yr[yr["rule"] == rule]
            if row.empty:
                continue
            r = row.iloc[0]
            print(f"  {rule:<30}  {int(r['n']):>6}  {r['win']*100:>6.1f}%  "
                  f"{r['avg_roc']:>+9.2f}%  {r['sharpe']:>+8.4f}")


def print_fvr_buckets(bucket_df: pd.DataFrame, rules_to_show: list[str]) -> None:
    """FVR sizing interaction with exit rules."""
    print(f"\n{'='*78}")
    print(f"  FVR BUCKET × EXIT RULE  (full-period, ≥3/5-fold approved tickers)")
    print(f"{'='*78}")
    for bucket in ["1.20–1.30", "1.30–1.40", "≥1.40"]:
        bdf = bucket_df[bucket_df["fvr_bucket"] == bucket]
        print(f"\n  FVR {bucket}:")
        print(f"  {'Rule':<30}  {'N':>6}  {'Win%':>6}  {'Avg ROC%':>9}  {'Sharpe':>8}")
        for rule in rules_to_show:
            row = bdf[bdf["rule"] == rule]
            if row.empty:
                continue
            r = row.iloc[0]
            print(f"  {rule:<30}  {int(r['n']):>6}  {r['win']*100:>6.1f}%  "
                  f"{r['avg_roc']:>+9.2f}%  {r['sharpe']:>+8.4f}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Straddle early-exit simulation")
    parser.add_argument("--tickers",     nargs="+", default=None)
    parser.add_argument("--ticker-file", type=str,  default=None)
    parser.add_argument("--min-cost",    type=float, default=MIN_COST)
    parser.add_argument("--csv",         action="store_true")
    args = parser.parse_args()

    if args.ticker_file:
        with open(args.ticker_file) as f:
            tickers = [l.strip() for l in f if l.strip()]
    elif args.tickers:
        tickers = args.tickers
    else:
        os.environ.setdefault("MYSQL_PASSWORD", "cthekb23")
        tickers = pd.read_sql(
            "SELECT DISTINCT ticker FROM study_summary WHERE study_id=12 ORDER BY ticker",
            _get_engine(),
        )["ticker"].tolist()

    print(f"Straddle Exit Analysis")
    print(f"  tickers  : {len(tickers)}")
    print(f"  min_cost : ${args.min_cost:.2f}  (penny straddles excluded)")
    print(f"  FVR gate : ≥{FVR_GATE}")

    # ── Load data ─────────────────────────────────────────────────────────────
    print(f"\n--- Loading legs ---")
    legs = load_all_legs(tickers, DEFAULT_START, date.today())
    if legs.empty:
        print("No data.")
        return

    print(f"\n--- Assembling straddles ---")
    raw = assemble_long_straddle(legs)
    df  = compute_roc_buyer(raw)

    # Apply minimum cost filter
    before = len(df)
    df = df[df["cost"] >= args.min_cost].reset_index(drop=True)
    print(f"  {len(df):,} trades after ${args.min_cost:.2f} min-cost filter "
          f"(removed {before-len(df):,} penny straddles)")

    print(f"\n--- Loading FVR (cached) ---")
    fvr = load_fvr_cached(tickers, DEFAULT_START, date.today())
    if not fvr.empty:
        df = df.merge(fvr[["ticker","entry_date","fvr_put_30_90"]],
                      on=["ticker","entry_date"], how="left")

    # ── Show cleaned distribution ─────────────────────────────────────────────
    app_file = "straddle_walkforward_ticker_persistence.csv"
    try:
        app_df = pd.read_csv(app_file)
        approved = set(app_df[app_df["n_folds"] >= 3]["ticker"].tolist())
        df_clean = df[
            df["ticker"].isin(approved) &
            df["fvr_put_30_90"].notna() &
            (df["fvr_put_30_90"] >= FVR_GATE)
        ]
    except FileNotFoundError:
        print(f"  WARNING: {app_file} not found. Run run_straddle_ticker_walkforward.py first.")
        return

    r = df_clean["roc"]
    print(f"\n  Cleaned dataset: {len(df_clean):,} trades  ({df_clean['ticker'].nunique()} tickers)")
    print(f"  ROC distribution (approved list, FVR≥{FVR_GATE}, cost≥${args.min_cost:.2f}):")
    for p in [1, 10, 25, 50, 75, 90, 95, 99]:
        print(f"    p{p:3d}: {np.percentile(r, p):>+8.1f}%")
    print(f"  mean={r.mean():>+8.1f}%  median={r.median():>+8.1f}%  std={r.std():>+8.1f}%")
    print(f"  ROC > 50%: {(r>50).mean()*100:.1f}%  "
          f"ROC > 100%: {(r>100).mean()*100:.1f}%  "
          f"ROC > 200%: {(r>200).mean()*100:.1f}%")
    print(f"  ROC < -50%: {(r<-50).mean()*100:.1f}%  "
          f"ROC < -75%: {(r<-75).mean()*100:.1f}%")

    # ── Define exit rules ─────────────────────────────────────────────────────
    # (label, cap, floor)
    # cap   = profit target (% ROC). None = hold forever.
    # floor = stop-loss depth (% loss). None = no stop.
    exit_rules = [
        ("Hold to expiry (baseline)",  None,  None),
        ("Cap 50%",                     50,   None),
        ("Cap 75%",                     75,   None),
        ("Cap 100%",                   100,   None),
        ("Cap 150%",                   150,   None),
        ("Cap 200%",                   200,   None),
        ("Cap 300%",                   300,   None),
        ("Stop -50%",                  None,    50),
        ("Stop -75%",                  None,    75),
        ("Cap 100% + Stop -50%",       100,    50),
        ("Cap 150% + Stop -50%",       150,    50),
        ("Cap 200% + Stop -50%",       200,    50),
    ]

    key_rules = [
        "Hold to expiry (baseline)",
        "Cap 100%",
        "Cap 150%",
        "Cap 200%",
        "Stop -50%",
        "Cap 150% + Stop -50%",
    ]

    # ── Walk-forward OOS ──────────────────────────────────────────────────────
    print(f"\n--- Running walk-forward OOS ---")
    results = run_exit_analysis(df, exit_rules)
    print_walkforward_summary(results)
    print_per_year(results, key_rules)

    # ── FVR bucket × exit rule ─────────────────────────────────────────────────
    bucket_df = fvr_bucket_exit(df, exit_rules)
    print_fvr_buckets(bucket_df, key_rules)

    if args.csv:
        results.to_csv("straddle_exit_walkforward.csv", index=False)
        bucket_df.to_csv("straddle_exit_fvr_buckets.csv", index=False)
        print(f"\n  Results saved → straddle_exit_walkforward.csv, straddle_exit_fvr_buckets.csv")


if __name__ == "__main__":
    main()
