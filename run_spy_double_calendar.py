"""
SPY Double Calendar Spread Backtest

Structure:
  Entry Friday → short legs expire on the Friday ~10-15 DTE
                 long legs expire one week after the short legs

  Sell OTM put  (short expiry, delta_target below spot)
  Buy  OTM put  (long  expiry, same strike)
  Sell OTM call (short expiry, delta_target above spot)
  Buy  OTM call (long  expiry, same strike)

Usage:
  PYTHONPATH=src python run_spy_double_calendar.py
  PYTHONPATH=src python run_spy_double_calendar.py --delta 0.25 --profit-target 0.50
  PYTHONPATH=src python run_spy_double_calendar.py --detail-delta 0.25 --detail-pt 0.25
"""

import argparse
from datetime import date
from collections import defaultdict

import numpy as np
import pandas as pd

from lib.studies.double_calendar_study import (
    build_double_calendar_trades,
    find_double_calendar_exits,
    compute_double_calendar_metrics,
)

TICKER    = "SPY"
CACHE_DIR = "data/cache"

# Sweep parameters
DELTA_TARGETS   = [0.15, 0.20, 0.25, 0.30]
PROFIT_TARGETS  = [None, 0.25, 0.50, 0.75]

SHORT_DTE_TARGET = 12   # target DTE for short legs
SHORT_DTE_TOL    = 3    # ±3 → 9–15 DTE
GAP_DAYS         = 7    # long expiry = short expiry + ~7 days
GAP_TOL          = 2    # ±2 days tolerance


def load_options() -> pd.DataFrame:
    path = f"{CACHE_DIR}/{TICKER}_options.parquet"
    print(f"Loading {TICKER} options from {path} ...")
    df = pd.read_parquet(path)
    print(f"  {len(df):,} rows  ({df['trade_date'].min()} → {df['trade_date'].max()})")
    return df


def print_sweep(results: list[dict]) -> None:
    if not results:
        print("No results.")
        return

    df = pd.DataFrame(results)
    df = df.sort_values(["delta", "profit_target"], na_position="first")

    pt_label = lambda pt: "hold" if (pt is None or (isinstance(pt, float) and np.isnan(pt))) else f"{int(pt*100)}%"
    print(f"\n{'Δ':>6} {'ProfitTake':>10} {'N':>5} {'Win%':>6} {'AvgROC%':>8} "
          f"{'AnnROC%':>8} {'SumPnL':>8} {'AvgHold':>8}")
    print("-" * 65)
    for _, r in df.iterrows():
        print(
            f"{r['delta']:>6.2f} {pt_label(r['profit_target']):>10} "
            f"{int(r['n']):>5} {r['win_pct']:>6.1f}% {r['avg_roc']:>7.2f}% "
            f"{r['avg_ann_roc']:>7.0f}% {r['sum_pnl']:>8.2f} {r['avg_hold']:>7.1f}d"
        )


def print_year_detail(metrics: pd.DataFrame, delta: float, pt: float | None) -> None:
    pt_label = "hold-to-expiry" if pt is None else f"{int(pt*100)}% profit take"
    print(f"\n=== Year-by-Year: {TICKER} Double Calendar  Δ={delta:.2f}  {pt_label} ===")
    print(f"{'Year':>6} {'N':>4} {'Win%':>6} {'AvgROC%':>8} {'SumPnL':>8} {'EarlyExit%':>11}")
    print("-" * 52)
    metrics["year"] = pd.to_datetime(metrics["entry_date"]).dt.year
    for yr, g in metrics.groupby("year"):
        wr    = g["is_win"].mean()
        roc   = g["roc"].mean()
        sp    = g["net_pnl"].sum()
        early = (g["exit_type"] == "profit_take").mean() if "exit_type" in g.columns else 0.0
        print(f"{yr:>6} {len(g):>4} {wr*100:>6.1f}% {roc*100:>7.2f}% {sp:>8.3f} {early*100:>10.1f}%")
    wr    = metrics["is_win"].mean()
    roc   = metrics["roc"].mean()
    sp    = metrics["net_pnl"].sum()
    early = (metrics["exit_type"] == "profit_take").mean() if "exit_type" in metrics.columns else 0.0
    print("-" * 52)
    print(f"{'TOTAL':>6} {len(metrics):>4} {wr*100:>6.1f}% {roc*100:>7.2f}% {sp:>8.3f} {early*100:>10.1f}%")

    # Sample a few trades
    print(f"\nSample trades (first 5):")
    cols = ["entry_date", "short_expiry", "long_expiry",
            "sp_strike", "sc_strike", "net_debit", "net_pnl", "roc", "exit_type", "days_held"]
    cols = [c for c in cols if c in metrics.columns]
    print(metrics[cols].head(5).to_string(index=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--delta",        type=float, default=None, help="Single delta target (default: sweep all)")
    parser.add_argument("--profit-target",type=float, default=None, help="Single profit target pct (default: sweep all)")
    parser.add_argument("--detail-delta", type=float, default=None, help="Delta for per-year detail output")
    parser.add_argument("--detail-pt",    type=float, default=None, help="Profit target pct for per-year detail (omit for hold)")
    parser.add_argument("--no-sweep",     action="store_true",       help="Skip sweep table, only show detail")
    args = parser.parse_args()

    df_opts = load_options()

    delta_targets  = [args.delta]          if args.delta          is not None else DELTA_TARGETS
    profit_targets = [args.profit_target]  if args.profit_target  is not None else PROFIT_TARGETS

    print(f"\nShort DTE target: {SHORT_DTE_TARGET} ± {SHORT_DTE_TOL}  ({SHORT_DTE_TARGET-SHORT_DTE_TOL}–{SHORT_DTE_TARGET+SHORT_DTE_TOL} DTE)")
    print(f"Gap to long expiry: {GAP_DAYS} ± {GAP_TOL} days")
    print(f"Deltas: {delta_targets}  |  Profit targets: {profit_targets}")

    results = []
    detail_metrics = {}   # (delta, pt) → metrics df

    for delta in delta_targets:
        print(f"\nBuilding trades for Δ={delta:.2f} ...")
        trades = build_double_calendar_trades(
            df_opts, delta,
            short_dte_target=SHORT_DTE_TARGET, short_dte_tol=SHORT_DTE_TOL,
            gap_days=GAP_DAYS, gap_tol=GAP_TOL,
            max_delta_err=0.08, max_spread_pct=0.25,
        )
        if trades.empty:
            print(f"  No valid trades found for Δ={delta:.2f}")
            continue
        print(f"  {len(trades)} entries found")

        for pt in profit_targets:
            pt_label = "hold" if pt is None else f"{int(pt*100)}%PT"
            exits   = find_double_calendar_exits(trades, df_opts, profit_target_roc=pt)
            metrics = compute_double_calendar_metrics(exits)
            metrics = metrics[~metrics["is_open"]]
            if metrics.empty:
                continue

            n        = len(metrics)
            wr       = metrics["is_win"].mean()
            avg_roc  = metrics["roc"].mean()
            ann_roc  = metrics["annualized_roc"].mean()
            sum_pnl  = metrics["net_pnl"].sum()
            avg_hold = metrics["days_held"].mean()

            results.append({
                "delta": delta, "profit_target": pt,
                "n": n, "win_pct": round(wr*100, 1),
                "avg_roc": round(avg_roc*100, 2),
                "avg_ann_roc": round(ann_roc*100, 0),
                "sum_pnl": round(sum_pnl, 3),
                "avg_hold": round(avg_hold, 1),
            })
            detail_metrics[(delta, pt)] = metrics
            print(f"    Δ={delta:.2f} {pt_label:>8}: n={n:3d}  win={wr*100:.1f}%  roc={avg_roc*100:.2f}%")

    print(f"\n{'='*65}")
    print(f"SPY Double Calendar — Sweep Results")
    print(f"Short expiry: {SHORT_DTE_TARGET}±{SHORT_DTE_TOL} DTE  |  Long expiry: +{GAP_DAYS} days  |  Entry: Friday")
    print_sweep(results)

    # Per-year detail for requested combo (or best by avg_roc)
    if args.detail_delta is not None:
        detail_key = (args.detail_delta, args.detail_pt)
        if detail_key in detail_metrics:
            print_year_detail(detail_metrics[detail_key], args.detail_delta, args.detail_pt)
        else:
            print(f"\nNo detail data for Δ={args.detail_delta}, pt={args.detail_pt}")
    elif results:
        # Auto-show best by avg_roc
        best = max(results, key=lambda r: r["avg_roc"])
        key  = (best["delta"], best["profit_target"])
        if key in detail_metrics:
            print_year_detail(detail_metrics[key], best["delta"], best["profit_target"])


if __name__ == "__main__":
    main()
