#!/usr/bin/env python3
"""
Long Straddle — Ticker-Level Walk-Forward Validation

Instead of predicting individual trade outcomes (AUC ~0.50, useless), this script
validates whether an IS-qualified ticker list generalises to held-out years.

Walk-forward design
-------------------
For each test year N in {2021, 2022, 2023, 2024, 2025}:

  IS  = all trades with entry_date.year < N
  OOS = all trades with entry_date.year == N

  Qualification (IS):
    Variant A — IS all entries  : avg_roc>0, Sharpe>0, n≥MIN_N
    Variant B — IS FVR≥1.20     : same, but computed on FVR-filtered IS trades

  Testing (OOS):
    Each approved list is traded on OOS period with FVR≥1.20 entry gate.

Baselines
---------
  [universe / all]      : all 987 tickers, all entries
  [universe / FVR≥1.20] : all 987 tickers, FVR≥1.20 gate only

FVR sizing analysis
-------------------
Within approved tickers (variant B) in OOS, bucket FVR by magnitude:
  1.20–1.30, 1.30–1.40, ≥1.40 → does higher FVR → higher ROC?

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_straddle_ticker_walkforward.py
  ... --min-n 10            # relax IS min-trades (default 15)
  ... --csv                 # save fold-level and ticker-persistence CSVs
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

DEFAULT_START = date(2018, 1, 1)
TEST_YEARS    = [2021, 2022, 2023, 2024, 2025]
FVR_GATE      = 1.20
MIN_N         = 15        # minimum IS trades for qualification
MIN_N_FVR     = 10        # minimum IS FVR-filtered trades for variant B


# ── Helpers ───────────────────────────────────────────────────────────────────

def _stats(df: pd.DataFrame) -> dict:
    """Summarise a slice of trades."""
    if df.empty or len(df) < 3:
        return dict(n=len(df), win=np.nan, avg_roc=np.nan, sharpe=np.nan)
    avg = df["roc"].mean()
    std = df["roc"].std()
    return dict(
        n=len(df),
        win=df["win"].mean(),
        avg_roc=avg,
        sharpe=avg / std if std > 0 else 0.0,
    )


def _qualify(df: pd.DataFrame, min_n: int) -> list[str]:
    """Return list of tickers meeting IS qualification criteria."""
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


def _ticker_is_stats(df: pd.DataFrame, tickers: list[str], min_n: int) -> pd.DataFrame:
    """IS stats table for qualified tickers (for display)."""
    rows = []
    for ticker in tickers:
        grp = df[df["ticker"] == ticker]
        if len(grp) < min_n:
            continue
        avg = grp["roc"].mean()
        std = grp["roc"].std()
        sh  = avg / std if std > 0 else 0.0
        rows.append(dict(
            ticker=ticker, n=len(grp),
            avg_roc=avg, win=grp["win"].mean(), sharpe=sh,
        ))
    return pd.DataFrame(rows).sort_values("sharpe", ascending=False).reset_index(drop=True)


def _print_fold_row(label: str, stats: dict) -> None:
    if np.isnan(stats["avg_roc"]):
        print(f"    {label:<35}  N={stats['n']:>5}   (insufficient data)")
        return
    print(
        f"    {label:<35}  N={stats['n']:>5}  "
        f"win={stats['win']*100:>5.1f}%  "
        f"avg_roc={stats['avg_roc']:>+7.2f}%  "
        f"sharpe={stats['sharpe']:>+7.4f}"
    )


# ── Walk-forward ──────────────────────────────────────────────────────────────

def walk_forward(df: pd.DataFrame, min_n: int = MIN_N, min_n_fvr: int = MIN_N_FVR) -> dict:
    """
    Run walk-forward over TEST_YEARS. Returns dict of fold results.

    df must have columns: ticker, entry_date (date), roc, win, fvr_put_30_90 (may be NaN)
    """
    df = df.copy()
    df["year"] = pd.to_datetime(df["entry_date"]).dt.year
    df_fvr = df.dropna(subset=["fvr_put_30_90"])
    df_fvr_gated = df_fvr[df_fvr["fvr_put_30_90"] >= FVR_GATE]

    fold_records = []   # one row per (test_year, variant)
    ticker_appearances: dict[str, list[int]] = {}  # ticker → [years it was approved]

    for test_year in TEST_YEARS:
        is_df     = df[df["year"] < test_year]
        oos_all   = df[df["year"] == test_year]
        oos_fvr   = df_fvr_gated[df_fvr_gated["year"] == test_year]

        # ── Baselines ────────────────────────────────────────────────────────
        base_all = _stats(oos_all)
        base_fvr = _stats(oos_fvr)

        # ── Variant A: qualify on all IS entries ──────────────────────────────
        approved_a = _qualify(is_df, min_n)
        oos_a = oos_fvr[oos_fvr["ticker"].isin(approved_a)]
        stats_a = _stats(oos_a)

        # ── Variant B: qualify on IS FVR-filtered entries ─────────────────────
        is_fvr = df_fvr_gated[df_fvr_gated["year"] < test_year]
        approved_b = _qualify(is_fvr, min_n_fvr)
        oos_b = oos_fvr[oos_fvr["ticker"].isin(approved_b)]
        stats_b = _stats(oos_b)

        for t in approved_b:
            ticker_appearances.setdefault(t, []).append(test_year)

        # ── FVR sizing (within variant B approved list) ───────────────────────
        sizing_rows = []
        if not oos_b.empty:
            for lo, hi, label in [
                (FVR_GATE,  1.30,  "1.20–1.30"),
                (1.30,      1.40,  "1.30–1.40"),
                (1.40,      9999., "≥1.40"),
            ]:
                slice_ = oos_b[
                    (oos_b["fvr_put_30_90"] >= lo) &
                    (oos_b["fvr_put_30_90"] <  hi)
                ]
                s = _stats(slice_)
                s["fvr_bucket"] = label
                s["test_year"]  = test_year
                sizing_rows.append(s)

        # Print fold
        print(f"\n  ── Test year {test_year} "
              f"(IS: 2018–{test_year-1}, "
              f"OOS n_all={len(oos_all):,}, n_fvr={len(oos_fvr):,}) ──")
        print(f"    IS approved: A={len(approved_a)} tickers  B={len(approved_b)} tickers")
        _print_fold_row("Baseline: all tickers / all entries", base_all)
        _print_fold_row("Baseline: all tickers / FVR≥1.20",   base_fvr)
        _print_fold_row("Var A: IS-all qual + FVR≥1.20",      stats_a)
        _print_fold_row("Var B: IS-FVR qual + FVR≥1.20",      stats_b)

        if sizing_rows:
            print(f"    FVR sizing (Var B approved, OOS {test_year}):")
            for r in sizing_rows:
                if r["n"] > 0 and not np.isnan(r["avg_roc"]):
                    print(f"      {r['fvr_bucket']:<12}  N={r['n']:>4}  "
                          f"win={r['win']*100:>5.1f}%  avg_roc={r['avg_roc']:>+7.2f}%")

        # Store for aggregate
        for variant, stats, approved in [
            ("baseline_all",   base_all,  []),
            ("baseline_fvr",   base_fvr,  []),
            ("var_a",          stats_a,   approved_a),
            ("var_b",          stats_b,   approved_b),
        ]:
            fold_records.append(dict(
                test_year=test_year, variant=variant,
                n_approved=len(approved),
                **stats,
            ))

    return dict(
        fold_records=pd.DataFrame(fold_records),
        ticker_appearances=ticker_appearances,
    )


def print_aggregate(fold_df: pd.DataFrame) -> None:
    """Print aggregate OOS stats across all test years."""
    print(f"\n{'='*72}")
    print(f"  AGGREGATE OOS  (stacked across {len(TEST_YEARS)} test years)")
    print(f"{'='*72}")
    for variant in ["baseline_all", "baseline_fvr", "var_a", "var_b"]:
        rows = fold_df[fold_df["variant"] == variant].dropna(subset=["avg_roc"])
        if rows.empty:
            continue
        avg_n    = rows["n"].mean()
        all_n    = rows["n"].sum()
        avg_roc  = rows["avg_roc"].mean()         # simple average across folds
        avg_win  = rows["win"].mean()
        avg_sh   = rows["sharpe"].mean()
        label = {
            "baseline_all": "Baseline all/all",
            "baseline_fvr": "Baseline all/FVR≥1.20",
            "var_a":        "Var A (IS-all qual + FVR gate)",
            "var_b":        "Var B (IS-FVR qual + FVR gate)",
        }[variant]
        print(f"  {label:<35}  "
              f"avg_N={avg_n:>6.0f}  win={avg_win*100:>5.1f}%  "
              f"avg_roc={avg_roc:>+7.2f}%  avg_sharpe={avg_sh:>+7.4f}")


def print_ticker_persistence(appearances: dict[str, list[int]]) -> None:
    """Print tickers that appear in multiple folds (Var B approved list)."""
    print(f"\n{'='*72}")
    print(f"  TICKER PERSISTENCE — Var B approved list across {len(TEST_YEARS)} test years")
    print(f"{'='*72}")
    rows = sorted(
        [(t, yrs) for t, yrs in appearances.items()],
        key=lambda x: -len(x[1]),
    )
    max_years = len(TEST_YEARS)
    # Group by frequency
    for freq in range(max_years, 0, -1):
        cohort = [(t, yrs) for t, yrs in rows if len(yrs) == freq]
        if not cohort:
            continue
        label = f"All {freq} years" if freq == max_years else f"{freq} of {max_years} years"
        tickers_str = ", ".join(t for t, _ in cohort)
        print(f"\n  [{label}] — {len(cohort)} tickers")
        print(f"  {tickers_str}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Ticker-level walk-forward for long straddle")
    parser.add_argument("--tickers",     nargs="+", default=None)
    parser.add_argument("--ticker-file", type=str,  default=None)
    parser.add_argument("--start",       type=str,  default=None)
    parser.add_argument("--min-n",       type=int,  default=MIN_N)
    parser.add_argument("--csv",         action="store_true")
    args = parser.parse_args()

    min_n     = args.min_n
    min_n_fvr = max(5, args.min_n // 2)

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

    start = date.fromisoformat(args.start) if args.start else DEFAULT_START
    end   = date.today()

    print(f"Long Straddle — Ticker Walk-Forward")
    print(f"  tickers    : {len(tickers)}")
    print(f"  date range : {start} → {end}")
    print(f"  test years : {TEST_YEARS}")
    print(f"  FVR gate   : ≥{FVR_GATE}")
    print(f"  min-n IS   : {min_n} (all), {min_n_fvr} (FVR-filtered)")

    # ── Load legs ─────────────────────────────────────────────────────────────
    print(f"\n--- Step 1: Load option legs ---")
    legs = load_all_legs(tickers, start, end)
    if legs.empty:
        print("No data. Exiting.")
        return

    # ── Assemble straddles ────────────────────────────────────────────────────
    print(f"\n--- Step 2: Assemble straddles ---")
    raw = assemble_long_straddle(legs)
    df  = compute_roc_buyer(raw)
    print(f"  {len(df):,} trades  ({df['ticker'].nunique():,} tickers)")

    # ── Load FVR (cached) ─────────────────────────────────────────────────────
    print(f"\n--- Step 3: Load FVR (cached) ---")
    fvr = load_fvr_cached(tickers, start, end)
    if fvr.empty:
        print("  WARNING: no FVR data, walk-forward will run without FVR gate")
    else:
        print(f"  {len(fvr):,} FVR rows  ({fvr['ticker'].nunique():,} tickers)")
        df = df.merge(
            fvr[["ticker", "entry_date", "fvr_put_30_90"]],
            on=["ticker", "entry_date"], how="left",
        )

    # ── Walk-forward ──────────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print(f"  WALK-FORWARD RESULTS")
    print(f"{'='*72}")
    results = walk_forward(df, min_n=min_n, min_n_fvr=min_n_fvr)

    fold_df      = results["fold_records"]
    appearances  = results["ticker_appearances"]

    print_aggregate(fold_df)
    print_ticker_persistence(appearances)

    # ── Final approved list (qualified in ≥3 of 5 folds) ─────────────────────
    stable = [t for t, yrs in appearances.items() if len(yrs) >= 3]
    print(f"\n{'='*72}")
    print(f"  RECOMMENDED APPROVED LIST: appeared in ≥3/5 folds — {len(stable)} tickers")
    print(f"{'='*72}")
    if stable:
        # Show their full-period stats (FVR-gated, all years)
        df_fvr_all = df.dropna(subset=["fvr_put_30_90"])
        df_fvr_all = df_fvr_all[df_fvr_all["fvr_put_30_90"] >= FVR_GATE]
        df_stable  = df_fvr_all[df_fvr_all["ticker"].isin(stable)]
        print(f"\n  Full-period (FVR≥{FVR_GATE}) stats for stable tickers:")
        print(f"  {'Ticker':<8}  {'N':>5}  {'Avg ROC%':>9}  {'Win%':>7}  {'Sharpe':>8}  "
              f"{'Appearances':>12}")
        print(f"  {'-'*60}")
        rows = []
        for t in stable:
            grp = df_stable[df_stable["ticker"] == t]
            if grp.empty:
                continue
            avg = grp["roc"].mean()
            std = grp["roc"].std()
            sh  = avg / std if std > 0 else 0.0
            rows.append(dict(
                ticker=t, n=len(grp), avg_roc=avg,
                win=grp["win"].mean(), sharpe=sh,
                appearances=len(appearances[t]),
            ))
        rows.sort(key=lambda x: -x["sharpe"])
        for r in rows:
            app_years = ", ".join(str(y) for y in sorted(appearances[r["ticker"]]))
            print(f"  {r['ticker']:<8}  {r['n']:>5}  "
                  f"{r['avg_roc']:>+9.2f}  {r['win']*100:>6.1f}%  "
                  f"{r['sharpe']:>8.4f}  [{app_years}]")

    # ── CSV output ────────────────────────────────────────────────────────────
    if args.csv:
        fold_path = "straddle_walkforward_folds.csv"
        fold_df.to_csv(fold_path, index=False)
        print(f"\n  Fold records saved → {fold_path}")

        if appearances:
            app_df = pd.DataFrame([
                {"ticker": t, "n_folds": len(yrs), "years": ",".join(str(y) for y in sorted(yrs))}
                for t, yrs in appearances.items()
            ]).sort_values("n_folds", ascending=False)
            app_path = "straddle_walkforward_ticker_persistence.csv"
            app_df.to_csv(app_path, index=False)
            print(f"  Ticker persistence saved → {app_path}")


if __name__ == "__main__":
    main()
