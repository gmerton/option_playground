#!/usr/bin/env python3
"""
Iron Butterfly — filtered universe analysis.

Applies two filters to find where iron butterflies actually work:
  1. FVR filter : only enter when fvr_put_30_90 < threshold (backwardation / mild contango)
  2. Ticker filter: only trade names where historical per-ticker ROC is positive (n ≥ MIN_N)

For each (wing_delta × fvr_threshold) combination, reports:
  - Overall stats vs unfiltered baseline
  - Per-ticker leaderboard (sorted by Sharpe)
  - Recommended universe: tickers with avg_roc > 0, win > 50%, n ≥ MIN_N

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_iron_butterfly_filtered.py

  # Specific wing delta and FVR threshold:
  ... run_iron_butterfly_filtered.py --wing-delta 0.05 --fvr-max 0.90

  # Save per-ticker breakdown to CSV:
  ... run_iron_butterfly_filtered.py --csv

Requires: AWS_PROFILE=clarinut-gmerton, MYSQL_PASSWORD=cthekb23
"""

from __future__ import annotations

import argparse
import os
from datetime import date

import numpy as np
import pandas as pd
import awswrangler as wr

from lib.mysql_lib import _get_engine
from lib.studies.iron_butterfly_study import (
    assemble_iron_fly,
    compute_roc,
    load_legs_from_cache,
)

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_WING_DELTAS  = [0.05, 0.10, 0.15, 0.20]
DEFAULT_FVR_THRESHOLDS = [0.80, 0.90, 1.00]   # also test 1.00 = "any non-contango"
DEFAULT_START        = date(2018, 1, 1)
OOS_START            = date(2023, 1, 1)
MIN_N                = 15     # min trades per ticker to include in per-ticker ranking
LEG_BATCH_SIZE       = 50
FVR_BATCH_SIZE       = 100


# ── Data loaders (same as main study) ────────────────────────────────────────

def load_all_legs(tickers, start, end):
    frames = []
    n_batches = (len(tickers) + LEG_BATCH_SIZE - 1) // LEG_BATCH_SIZE
    for i in range(0, len(tickers), LEG_BATCH_SIZE):
        batch = tickers[i : i + LEG_BATCH_SIZE]
        print(f"  [legs {i//LEG_BATCH_SIZE+1}/{n_batches}] {batch[0]}…{batch[-1]}", flush=True)
        df = load_legs_from_cache(batch, start, end)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    print(f"  → {len(out):,} legs  ({out['ticker'].nunique():,} tickers)")
    return out


def load_all_fvr(tickers, start, end):
    frames = []
    for i in range(0, len(tickers), FVR_BATCH_SIZE):
        batch = tickers[i : i + FVR_BATCH_SIZE]
        tickers_sql = ", ".join(f"'{t}'" for t in batch)
        df = wr.athena.read_sql_query(
            sql=f"""
            SELECT ticker, trade_date, fvr_put_30_90
            FROM silver.fwd_vol_daily
            WHERE ticker IN ({tickers_sql})
              AND trade_date >= DATE '{start.isoformat()}'
              AND trade_date <= DATE '{end.isoformat()}'
              AND fvr_put_30_90 > 0
            """,
            database="silver",
            workgroup="dev-v3",
            s3_output="s3://athena-919061006621/",
        )
        if not df.empty:
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True).rename(columns={"trade_date": "entry_date"})
    print(f"  → {len(out):,} FVR rows  ({out['ticker'].nunique():,} tickers)")
    return out


# ── Per-ticker analysis ───────────────────────────────────────────────────────

def per_ticker_stats(df: pd.DataFrame, min_n: int = MIN_N) -> pd.DataFrame:
    """Compute per-ticker ROC stats. Returns sorted DataFrame."""
    rows = []
    for ticker, grp in df.groupby("ticker"):
        if len(grp) < min_n:
            continue
        avg = grp["roc"].mean()
        med = grp["roc"].median()
        win = grp["win"].mean()
        std = grp["roc"].std()
        sh  = avg / std if std > 0 else 0
        # OOS split
        oos = grp[grp["entry_date"] >= OOS_START]
        rows.append({
            "ticker":     ticker,
            "n":          len(grp),
            "n_oos":      len(oos),
            "avg_roc":    avg,
            "median_roc": med,
            "win_rate":   win,
            "sharpe":     sh,
            "oos_avg_roc":  oos["roc"].mean() if len(oos) >= 5 else np.nan,
            "oos_win_rate": oos["win"].mean() if len(oos) >= 5 else np.nan,
        })
    return pd.DataFrame(rows).sort_values("sharpe", ascending=False).reset_index(drop=True)


def print_stats(df: pd.DataFrame, label: str) -> None:
    if df.empty:
        print(f"  [{label}] No data")
        return
    sharpe = df["roc"].mean() / df["roc"].std() if df["roc"].std() > 0 else 0
    print(f"  [{label}]  N={len(df):,}  tickers={df['ticker'].nunique():,}  "
          f"avg_roc={df['roc'].mean():+.2f}%  median={df['roc'].median():+.2f}%  "
          f"win={df['win'].mean()*100:.1f}%  sharpe={sharpe:.4f}")


def analyze_filtered(
    df_base: pd.DataFrame,
    wing_delta: float,
    fvr_max: float,
    save_csv: bool = False,
) -> pd.DataFrame:
    """
    Apply FVR filter, print stats, per-ticker leaderboard, recommended universe.
    Returns per-ticker stats DataFrame.
    """
    label = f"{int(wing_delta*100)}Δ / FVR<{fvr_max}"

    # Subset to trades that have FVR data
    has_fvr = df_base.dropna(subset=["fvr_put_30_90"])
    filtered = has_fvr[has_fvr["fvr_put_30_90"] < fvr_max]

    print(f"\n{'='*70}")
    print(f"  {label}  →  {len(filtered):,} trades  ({filtered['ticker'].nunique():,} tickers)")
    print(f"{'='*70}")

    # Overall stats: unfiltered vs fvr-filtered
    print(f"\n  Baseline (all, has FVR):")
    print_stats(has_fvr, "all")
    print(f"\n  FVR < {fvr_max}:")
    print_stats(filtered, f"FVR<{fvr_max}")

    # Walk-forward
    is_df  = filtered[filtered["entry_date"] < OOS_START]
    oos_df = filtered[filtered["entry_date"] >= OOS_START]
    print(f"\n  Walk-forward:")
    print_stats(is_df,  "IS  2018–2022")
    print_stats(oos_df, "OOS 2023+    ")

    # Per-ticker breakdown
    tk = per_ticker_stats(filtered, min_n=MIN_N)
    if tk.empty:
        return tk

    # Recommended universe: positive avg_roc, win > 50%, Sharpe > 0
    good = tk[(tk["avg_roc"] > 0) & (tk["win_rate"] > 0.50) & (tk["sharpe"] > 0)]
    print(f"\n  Per-ticker leaderboard (n ≥ {MIN_N}, sorted by Sharpe):")
    print(f"  {'Ticker':<8}  {'N':>5}  {'Avg ROC%':>9}  {'Median%':>8}  "
          f"{'Win%':>7}  {'Sharpe':>8}  {'OOS ROC%':>9}  {'OOS Win%':>9}")
    print(f"  {'-'*75}")
    for _, row in tk.head(40).iterrows():
        oos_roc = f"{row['oos_avg_roc']:>+9.2f}" if not np.isnan(row["oos_avg_roc"]) else "       N/A"
        oos_win = f"{row['oos_win_rate']*100:>8.1f}%" if not np.isnan(row["oos_win_rate"]) else "      N/A"
        marker = " ✓" if row["ticker"] in good["ticker"].values else ""
        print(f"  {row['ticker']:<8}  {int(row['n']):>5}  "
              f"{row['avg_roc']:>+9.2f}  {row['median_roc']:>+8.2f}  "
              f"{row['win_rate']*100:>6.1f}%  {row['sharpe']:>8.4f}  "
              f"{oos_roc}  {oos_win}{marker}")

    print(f"\n  Recommended universe ({len(good)} tickers, avg_roc>0 + win>50% + Sharpe>0):")
    print(f"  {', '.join(good['ticker'].tolist())}")

    if save_csv:
        path = f"iron_fly_tickers_{int(wing_delta*100)}d_fvr{int(fvr_max*100)}.csv"
        tk.to_csv(path, index=False)
        print(f"\n  Per-ticker stats saved → {path}")

    return tk


# ── Comparison table across filter combos ────────────────────────────────────

def print_filter_comparison(results: list[dict]) -> None:
    print(f"\n{'='*80}")
    print(f"  FILTER COMBINATION COMPARISON")
    print(f"{'='*80}")
    print(f"  {'Config':<22}  {'N':>7}  {'Tickers':>7}  {'Avg ROC%':>9}  "
          f"{'Median%':>8}  {'Win%':>6}  {'Sharpe':>8}")
    print(f"  {'-'*76}")
    for r in results:
        print(f"  {r['label']:<22}  {r['n']:>7,}  {r['tickers']:>7,}  "
              f"{r['avg_roc']:>+9.2f}  {r['median_roc']:>+8.2f}  "
              f"{r['win_rate']*100:>5.1f}%  {r['sharpe']:>8.4f}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Iron butterfly filtered universe analysis"
    )
    parser.add_argument("--wing-deltas", nargs="+", type=float, default=DEFAULT_WING_DELTAS)
    parser.add_argument("--fvr-thresholds", nargs="+", type=float, default=DEFAULT_FVR_THRESHOLDS)
    parser.add_argument("--tickers",     nargs="+", default=None)
    parser.add_argument("--ticker-file", type=str,  default=None)
    parser.add_argument("--start",       type=str,  default=None)
    parser.add_argument("--end",         type=str,  default=None)
    parser.add_argument("--csv", action="store_true")
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

    start = date.fromisoformat(args.start) if args.start else DEFAULT_START
    end   = date.fromisoformat(args.end)   if args.end   else date.today()

    print(f"Iron Butterfly — filtered universe analysis")
    print(f"  tickers        : {len(tickers)}")
    print(f"  date range     : {start} → {end}")
    print(f"  wing deltas    : {args.wing_deltas}")
    print(f"  FVR thresholds : {args.fvr_thresholds}")

    print(f"\n--- Loading option legs ---")
    legs = load_all_legs(tickers, start, end)
    if legs.empty:
        print("No leg data. Exiting.")
        return

    print(f"\n--- Loading FVR data ---")
    fvr = load_all_fvr(tickers, start, end)

    comparison_results = []

    for wing_delta in args.wing_deltas:
        label_d = f"{int(wing_delta*100)}Δ"
        print(f"\n{'#'*70}")
        print(f"  Wing delta: {label_d}")
        print(f"{'#'*70}")

        raw = assemble_iron_fly(legs, wing_delta)
        if raw.empty:
            continue
        df = compute_roc(raw)
        if df.empty:
            continue

        if not fvr.empty:
            df = df.merge(fvr, on=["ticker", "entry_date"], how="left")

        # Unfiltered baseline for this wing
        sharpe_base = df["roc"].mean() / df["roc"].std() if df["roc"].std() > 0 else 0
        comparison_results.append({
            "label":      f"{label_d} / unfiltered",
            "n":          len(df),
            "tickers":    df["ticker"].nunique(),
            "avg_roc":    df["roc"].mean(),
            "median_roc": df["roc"].median(),
            "win_rate":   df["win"].mean(),
            "sharpe":     sharpe_base,
        })

        for fvr_max in args.fvr_thresholds:
            tk = analyze_filtered(df, wing_delta, fvr_max, save_csv=args.csv)

            filt = df.dropna(subset=["fvr_put_30_90"])
            filt = filt[filt["fvr_put_30_90"] < fvr_max]
            if not filt.empty:
                sh = filt["roc"].mean() / filt["roc"].std() if filt["roc"].std() > 0 else 0
                comparison_results.append({
                    "label":      f"{label_d} / FVR<{fvr_max}",
                    "n":          len(filt),
                    "tickers":    filt["ticker"].nunique(),
                    "avg_roc":    filt["roc"].mean(),
                    "median_roc": filt["roc"].median(),
                    "win_rate":   filt["win"].mean(),
                    "sharpe":     sh,
                })

    print_filter_comparison(comparison_results)


if __name__ == "__main__":
    main()
