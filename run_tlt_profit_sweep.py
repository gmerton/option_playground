#!/usr/bin/env python3
"""
TLT Profit-Target Optimization Sweep (Walk-Forward)

Tests annualized-ROC profit targets from 50% to 2000% (step 50).
For each target, closes a spread when:
    (pnl / margin) × (365 / hold_days) ≥ target

Walk-forward split:
  In-sample:      2018–2022
  Out-of-sample:  2023–2026

Objective: maximize avg annualized ROC = mean((pnl/margin) × (365/days)) per trade.

Loads TLT options from parquet cache (built by run_tlt_regime_switch.py).

Usage:
  PYTHONPATH=src python run_tlt_profit_sweep.py [--ticker TLT]
"""
from __future__ import annotations

import argparse
from datetime import date

import numpy as np
import pandas as pd

# Import all infrastructure from the production script
from run_tlt_regime_switch import (
    TICKER_REGIME_STRATEGIES,
    load_data,
    build_trades,
)

IS_CUTOFF  = date(2023, 1, 1)   # in-sample: < 2023,  out-of-sample: >= 2023
ANN_STEP   = 50                  # sweep granularity (%)
ANN_MIN    = 50
ANN_MAX    = 2000


def ann_roc_stats(df: pd.DataFrame) -> dict:
    """Compute avg annualized ROC and supporting metrics."""
    if df.empty:
        return dict(n=0, win_pct=0.0, avg_ann_roc=0.0, avg_roc=0.0,
                    avg_days=0.0, sum_pnl=0.0)
    ann = (df["pnl"] / df["margin"]) * (365.0 / df["days"].clip(lower=1))
    roc = df["pnl"] / df["margin"]
    return dict(
        n          = len(df),
        win_pct    = (df["pnl"] > 0).mean() * 100,
        avg_ann_roc= ann.mean() * 100,
        avg_roc    = roc.mean() * 100,
        avg_days   = df["days"].mean(),
        sum_pnl    = df["pnl"].sum(),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="TLT")
    args   = parser.parse_args()
    ticker = args.ticker.upper()

    regime_strategies = TICKER_REGIME_STRATEGIES.get(ticker, TICKER_REGIME_STRATEGIES["TLT"])

    print(f"Loading {ticker} data...")
    data = load_data(ticker)
    daily_map_c, daily_map_p, opts_by_date, stock_map, regime_map, entry_dates, nrows = data
    print(f"  {nrows:,} rows loaded\n")

    # ── Baseline: fixed 50% take ──────────────────────────────────────────────
    sw_base, _, _ = build_trades(regime_strategies, daily_map_c, daily_map_p,
                                  opts_by_date, stock_map, regime_map, entry_dates,
                                  ann_target=None)
    is_base  = ann_roc_stats(sw_base[sw_base["edate"] <  IS_CUTOFF])
    oos_base = ann_roc_stats(sw_base[sw_base["edate"] >= IS_CUTOFF])

    # ── Sweep ─────────────────────────────────────────────────────────────────
    targets = list(range(ANN_MIN, ANN_MAX + 1, ANN_STEP))
    results = []

    print(f"Sweeping {len(targets)} ann_target values ({ANN_MIN}%–{ANN_MAX}%)...")
    for target in targets:
        sw, _, _ = build_trades(regime_strategies, daily_map_c, daily_map_p,
                                 opts_by_date, stock_map, regime_map, entry_dates,
                                 ann_target=float(target) / 100.0)
        is_s  = ann_roc_stats(sw[sw["edate"] <  IS_CUTOFF])
        oos_s = ann_roc_stats(sw[sw["edate"] >= IS_CUTOFF])
        results.append(dict(target=target, **{f"is_{k}": v  for k, v in is_s.items()},
                                             **{f"oos_{k}": v for k, v in oos_s.items()}))

    df = pd.DataFrame(results)

    # ── Best in-sample target ─────────────────────────────────────────────────
    best_idx    = df["is_avg_ann_roc"].idxmax()
    best_target = df.loc[best_idx, "target"]

    # ── Print results ─────────────────────────────────────────────────────────
    W = 110
    print(f"\n{'═'*W}")
    print(f"  {ticker} PROFIT-TARGET SWEEP  ·  Walk-forward (IS: 2018–2022 / OOS: 2023–2026)")
    print(f"  Objective: avg annualized ROC = mean((pnl/margin) × (365/days))")
    print(f"{'═'*W}")
    print(f"\n  {'Target':>8}  "
          f"{'IS N':>5}  {'IS Win%':>8}  {'IS AnnROC':>10}  {'IS ROC':>8}  {'IS Days':>8}  {'IS PnL':>8}  "
          f"{'OOS N':>6}  {'OOS Win%':>8}  {'OOS AnnROC':>11}  {'OOS ROC':>8}  {'OOS Days':>9}  {'OOS PnL':>8}")
    print(f"  {'─'*W}")

    # Baseline row
    b = is_base
    o = oos_base
    print(f"  {'50% fixed':>8}  "
          f"{b['n']:>5}  {b['win_pct']:>7.1f}%  {b['avg_ann_roc']:>+9.1f}%  "
          f"{b['avg_roc']:>+7.1f}%  {b['avg_days']:>7.1f}d  ${b['sum_pnl']:>+6.2f}  "
          f"{o['n']:>6}  {o['win_pct']:>7.1f}%  {o['avg_ann_roc']:>+10.1f}%  "
          f"{o['avg_roc']:>+7.1f}%  {o['avg_days']:>8.1f}d  ${o['sum_pnl']:>+6.2f}  ← baseline")
    print(f"  {'─'*W}")

    for _, row in df.iterrows():
        marker = " ◀ BEST IS" if row["target"] == best_target else ""
        print(f"  {row['target']:>7}%  "
              f"{row['is_n']:>5.0f}  {row['is_win_pct']:>7.1f}%  {row['is_avg_ann_roc']:>+9.1f}%  "
              f"{row['is_avg_roc']:>+7.1f}%  {row['is_avg_days']:>7.1f}d  ${row['is_sum_pnl']:>+6.2f}  "
              f"{row['oos_n']:>6.0f}  {row['oos_win_pct']:>7.1f}%  {row['oos_avg_ann_roc']:>+10.1f}%  "
              f"{row['oos_avg_roc']:>+7.1f}%  {row['oos_avg_days']:>8.1f}d  ${row['oos_sum_pnl']:>+6.2f}"
              f"{marker}")

    # ── Summary ───────────────────────────────────────────────────────────────
    best_row = df.loc[best_idx]
    print(f"\n{'═'*W}")
    print(f"  SUMMARY")
    print(f"{'═'*W}")
    print(f"  Baseline (50% fixed):      IS avg ann ROC {is_base['avg_ann_roc']:>+6.1f}%  "
          f"OOS avg ann ROC {oos_base['avg_ann_roc']:>+6.1f}%  avg hold {oos_base['avg_days']:.1f}d")
    print(f"  Best IS target ({best_target:>4}%):   IS avg ann ROC {best_row['is_avg_ann_roc']:>+6.1f}%  "
          f"OOS avg ann ROC {best_row['oos_avg_ann_roc']:>+6.1f}%  avg hold {best_row['oos_avg_days']:.1f}d")
    delta = best_row["oos_avg_ann_roc"] - oos_base["avg_ann_roc"]
    print(f"  OOS improvement vs baseline: {delta:>+.1f} pp ann ROC")
    print(f"{'═'*W}\n")


if __name__ == "__main__":
    main()
