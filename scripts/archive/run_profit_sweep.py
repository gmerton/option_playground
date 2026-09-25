#!/usr/bin/env python3
"""
Profit-Target Optimization Sweep for put_spread / call_spread strategies.

Tests annualized-ROC profit targets from 50% to 2000% (step 50).
For each target, closes a spread when:
    (pnl / margin) × (365 / hold_days) ≥ target

Walk-forward split:
  In-sample:      2018–2022  (< 2023-01-01)
  Out-of-sample:  2023–2026  (≥ 2023-01-01)

Objective: maximize avg annualized ROC per trade.

Usage:
  # GLD put spread (confirmed 0.30Δ/0.10-wing/all-VIX):
  MYSQL_PASSWORD=xxx PYTHONPATH=src python run_profit_sweep.py \\
      --ticker GLD --strategy put_spread \\
      --short-delta 0.30 --wing 0.10 --vix none

  # ASHR call spread (confirmed 0.20Δ/0.10-wing/all-VIX):
  MYSQL_PASSWORD=xxx PYTHONPATH=src python run_profit_sweep.py \\
      --ticker ASHR --strategy call_spread \\
      --short-delta 0.20 --wing 0.10 --vix none

  # UVXY call spread (confirmed 0.50Δ/0.10-wing/all-VIX):
  MYSQL_PASSWORD=xxx PYTHONPATH=src python run_profit_sweep.py \\
      --ticker UVXY --strategy call_spread \\
      --short-delta 0.50 --wing 0.10 --vix none

Requires: MYSQL_PASSWORD, AWS_PROFILE=clarinut-gmerton
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta

import pandas as pd

from lib.studies.put_spread_study import (
    build_put_spread_trades,
    find_put_spread_exits,
    compute_spread_metrics,
    fetch_vix_data,
)
from lib.studies.call_spread_study import (
    build_call_spread_trades,
    find_spread_exits,
    compute_spread_metrics as compute_call_metrics,
)
from lib.studies.ticker_config import TICKER_CONFIG
from lib.studies.straddle_study import sync_options_cache

IS_CUTOFF = date(2023, 1, 1)
ANN_STEP  = 50
ANN_MIN   = 50
ANN_MAX   = 2000


def ann_roc_stats(df: pd.DataFrame) -> dict:
    if df.empty:
        return dict(n=0, win_pct=0.0, avg_ann_roc=0.0, avg_roc=0.0,
                    avg_days=0.0, sum_pnl=0.0)
    ann = (df["net_pnl"] / df["max_loss"]) * (365.0 / df["days_held"].clip(lower=1))
    roc = df["net_pnl"] / df["max_loss"]
    return dict(
        n          = len(df),
        win_pct    = (df["net_pnl"] > 0).mean() * 100,
        avg_ann_roc= ann.mean() * 100,
        avg_roc    = roc.mean() * 100,
        avg_days   = df["days_held"].mean(),
        sum_pnl    = df["net_pnl"].sum(),
    )


def run_sweep_put(
    ticker: str,
    df_opts: pd.DataFrame,
    df_vix: pd.DataFrame,
    short_delta: float,
    wing: float,
    vix_thresh,
    split_dates,
    dte_target: int = 20,
    dte_tol: int = 5,
) -> list[dict]:
    """Build positions once, sweep ann_targets, return result rows."""
    # Build positions (shared across all ann_target values)
    positions = build_put_spread_trades(
        df_opts,
        short_delta_target=short_delta,
        wing_delta_width=wing,
        dte_target=dte_target,
        dte_tol=dte_tol,
        entry_weekday=4,
        split_dates=split_dates,
        max_delta_err=0.08,
    )
    if positions.empty:
        print("  No positions found.")
        return [], {}, {}

    vix_lookup = df_vix.set_index("trade_date")["vix_close"]
    positions["vix_on_entry"] = positions["entry_date"].map(vix_lookup)
    positions["short_delta_target"] = short_delta
    positions["wing_delta_width"]   = wing

    # Apply VIX filter
    if vix_thresh is not None:
        positions = positions[
            positions["vix_on_entry"].isna()
            | (positions["vix_on_entry"] < float(vix_thresh))
        ]
    positions["vix_threshold"] = float("nan") if vix_thresh is None else float(vix_thresh)

    if positions.empty:
        print("  No positions after VIX filter.")
        return [], {}, {}

    print(f"  {len(positions)} entries. Sweeping {ANN_MIN}%–{ANN_MAX}% ...")

    # Baseline: fixed 50% take
    base_pos = find_put_spread_exits(positions, df_opts, profit_take_pct=0.50)
    base_pos = compute_spread_metrics(base_pos)
    base_closed = base_pos[~base_pos["is_open"] & ~base_pos["split_flag"]]
    is_base  = ann_roc_stats(base_closed[base_closed["entry_date"] <  IS_CUTOFF])
    oos_base = ann_roc_stats(base_closed[base_closed["entry_date"] >= IS_CUTOFF])

    rows = []
    for target in range(ANN_MIN, ANN_MAX + 1, ANN_STEP):
        t_pos = find_put_spread_exits(positions, df_opts,
                                      ann_target=float(target) / 100.0)
        t_pos = compute_spread_metrics(t_pos)
        closed = t_pos[~t_pos["is_open"] & ~t_pos["split_flag"]]
        is_s  = ann_roc_stats(closed[closed["entry_date"] <  IS_CUTOFF])
        oos_s = ann_roc_stats(closed[closed["entry_date"] >= IS_CUTOFF])
        rows.append(dict(target=target,
                         **{f"is_{k}": v  for k, v in is_s.items()},
                         **{f"oos_{k}": v for k, v in oos_s.items()}))
    return rows, is_base, oos_base


def run_sweep_call(
    ticker: str,
    df_opts: pd.DataFrame,
    df_vix: pd.DataFrame,
    short_delta: float,
    wing: float,
    vix_thresh,
    split_dates,
    dte_target: int = 20,
    dte_tol: int = 5,
) -> list[dict]:
    positions = build_call_spread_trades(
        df_opts,
        short_delta_target=short_delta,
        wing_delta_width=wing,
        dte_target=dte_target,
        dte_tol=dte_tol,
        entry_weekday=4,
        split_dates=split_dates,
        max_delta_err=0.08,
    )
    if positions.empty:
        print("  No positions found.")
        return [], {}, {}

    vix_lookup = df_vix.set_index("trade_date")["vix_close"]
    positions["vix_on_entry"] = positions["entry_date"].map(vix_lookup)
    positions["short_delta_target"] = short_delta
    positions["wing_delta_width"]   = wing

    if vix_thresh is not None:
        positions = positions[
            positions["vix_on_entry"].isna()
            | (positions["vix_on_entry"] < float(vix_thresh))
        ]
    positions["vix_threshold"] = float("nan") if vix_thresh is None else float(vix_thresh)

    if positions.empty:
        print("  No positions after VIX filter.")
        return [], {}, {}

    print(f"  {len(positions)} entries. Sweeping {ANN_MIN}%–{ANN_MAX}% ...")

    # Baseline
    base_pos = find_spread_exits(positions, df_opts, profit_take_pct=0.50)
    base_pos = compute_call_metrics(base_pos)
    base_closed = base_pos[~base_pos["is_open"] & ~base_pos["split_flag"]]
    is_base  = ann_roc_stats(base_closed[base_closed["entry_date"] <  IS_CUTOFF])
    oos_base = ann_roc_stats(base_closed[base_closed["entry_date"] >= IS_CUTOFF])

    rows = []
    for target in range(ANN_MIN, ANN_MAX + 1, ANN_STEP):
        t_pos = find_spread_exits(positions, df_opts,
                                  ann_target=float(target) / 100.0)
        t_pos = compute_call_metrics(t_pos)
        closed = t_pos[~t_pos["is_open"] & ~t_pos["split_flag"]]
        is_s  = ann_roc_stats(closed[closed["entry_date"] <  IS_CUTOFF])
        oos_s = ann_roc_stats(closed[closed["entry_date"] >= IS_CUTOFF])
        rows.append(dict(target=target,
                         **{f"is_{k}": v  for k, v in is_s.items()},
                         **{f"oos_{k}": v for k, v in oos_s.items()}))
    return rows, is_base, oos_base


def print_results(ticker: str, strategy: str, short_delta: float, wing: float,
                  vix_thresh, rows: list[dict], is_base: dict, oos_base: dict) -> None:
    df = pd.DataFrame(rows)
    best_idx    = df["is_avg_ann_roc"].idxmax()
    best_target = df.loc[best_idx, "target"]
    vix_label = "All VIX" if vix_thresh is None else f"VIX<{int(vix_thresh)}"

    W = 115
    print(f"\n{'═'*W}")
    print(f"  {ticker} {strategy.upper()} PROFIT-TARGET SWEEP  ·  "
          f"short={short_delta:.2f}  wing={wing:.2f}  {vix_label}")
    print(f"  Walk-forward: IS 2018–2022 / OOS 2023–2026  |  "
          f"Objective: avg (pnl/margin) × (365/days)")
    print(f"{'═'*W}")
    print(f"\n  {'Target':>8}  "
          f"{'IS N':>5}  {'IS Win%':>8}  {'IS AnnROC':>10}  {'IS ROC':>8}  {'IS Days':>8}  {'IS PnL':>8}  "
          f"{'OOS N':>6}  {'OOS Win%':>8}  {'OOS AnnROC':>11}  {'OOS ROC':>8}  {'OOS Days':>9}  {'OOS PnL':>8}")
    print(f"  {'─'*W}")

    b, o = is_base, oos_base
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

    best_row = df.loc[best_idx]
    delta = best_row["oos_avg_ann_roc"] - oos_base["avg_ann_roc"]
    print(f"\n{'═'*W}")
    print(f"  SUMMARY")
    print(f"{'═'*W}")
    print(f"  Baseline (50% fixed):      IS avg ann ROC {is_base['avg_ann_roc']:>+6.1f}%  "
          f"OOS avg ann ROC {oos_base['avg_ann_roc']:>+6.1f}%  avg hold {oos_base['avg_days']:.1f}d")
    print(f"  Best IS target ({best_target:>4}%):   IS avg ann ROC {best_row['is_avg_ann_roc']:>+6.1f}%  "
          f"OOS avg ann ROC {best_row['oos_avg_ann_roc']:>+6.1f}%  avg hold {best_row['oos_avg_days']:.1f}d")
    print(f"  OOS improvement vs baseline: {delta:>+.1f} pp ann ROC")
    print(f"{'═'*W}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ann-ROC profit-target sweep for put/call spreads (IS/OOS walk-forward)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--ticker",        required=True,  help="Ticker symbol (e.g. GLD, ASHR)")
    parser.add_argument("--strategy",      default="put_spread",
                        choices=["put_spread", "call_spread"],
                        help="Strategy type")
    parser.add_argument("--short-delta",   type=float, required=True,
                        help="Short leg delta (e.g. 0.30)")
    parser.add_argument("--wing",          type=float, required=True,
                        help="Wing width in delta units (e.g. 0.10)")
    parser.add_argument("--vix",           default="none",
                        help="VIX threshold (e.g. 25) or 'none' for all VIX")
    parser.add_argument("--dte",           type=int, default=20)
    parser.add_argument("--dte-tol",       type=int, default=5)
    parser.add_argument("--start",         default=None, help="Override start date YYYY-MM-DD")
    args = parser.parse_args()

    ticker      = args.ticker.upper()
    strategy    = args.strategy
    short_delta = args.short_delta
    wing        = args.wing
    vix_thresh  = None if args.vix.lower() in ("none", "all", "") else float(args.vix)

    cfg   = TICKER_CONFIG.get(ticker, {})
    start = (
        date.fromisoformat(args.start) if args.start
        else cfg.get("start", date(2018, 1, 1))
    )
    end         = date.today()
    split_dates = cfg.get("split_dates", [])

    print(f"\n{ticker} {strategy.upper()}  short={short_delta:.2f}  wing={wing:.2f}  "
          f"vix={'All' if vix_thresh is None else f'<{vix_thresh:.0f}'}  "
          f"dte={args.dte}±{args.dte_tol}  start={start}")

    # ── Load data ─────────────────────────────────────────────────────────────
    print(f"\nSyncing {ticker} options cache ...")
    sync_options_cache(ticker, start, force=False)

    vix_start = start - timedelta(days=5)
    print(f"Fetching VIX ({vix_start} → {end}) ...")
    df_vix = fetch_vix_data(vix_start, end)
    if df_vix.empty:
        print("WARNING: no VIX data")

    from lib.mysql_lib import fetch_options_cache
    fetch_end = end + timedelta(days=args.dte + args.dte_tol + 5)
    print(f"Loading {ticker} options from MySQL ({start} → {fetch_end}) ...")
    df_opts = fetch_options_cache(ticker, start, fetch_end)
    print(f"  {len(df_opts):,} rows loaded\n")

    # ── Run sweep ─────────────────────────────────────────────────────────────
    if strategy == "put_spread":
        rows, is_base, oos_base = run_sweep_put(
            ticker, df_opts, df_vix,
            short_delta=short_delta, wing=wing, vix_thresh=vix_thresh,
            split_dates=split_dates, dte_target=args.dte, dte_tol=args.dte_tol,
        )
    else:
        rows, is_base, oos_base = run_sweep_call(
            ticker, df_opts, df_vix,
            short_delta=short_delta, wing=wing, vix_thresh=vix_thresh,
            split_dates=split_dates, dte_target=args.dte, dte_tol=args.dte_tol,
        )

    if not rows or not is_base:
        print("No results.")
        return

    print_results(ticker, strategy, short_delta, wing, vix_thresh,
                  rows, is_base, oos_base)


if __name__ == "__main__":
    main()
