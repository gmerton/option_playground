#!/usr/bin/env python3
"""
Delta-hedged ATM straddle study — CLI runner.

Usage:
    PYTHONPATH=src python run_delta_hedged_straddle.py
    PYTHONPATH=src python run_delta_hedged_straddle.py --ticker KWEB
    PYTHONPATH=src python run_delta_hedged_straddle.py --ticker KWEB --months 6
    PYTHONPATH=src python run_delta_hedged_straddle.py --ticker KWEB --refresh
    PYTHONPATH=src python run_delta_hedged_straddle.py --ticker KWEB --detail YYYY-MM-DD

Options:
    --ticker    Underlying ticker (default: KWEB)
    --months    Months of history to study (default: 3)
    --dte       Target DTE for each straddle entry (default: 30)
    --refresh   Force re-fetch of cached data from Athena / Tradier
    --detail    Print day-by-day P&L for the position entered on this date

Requires: TRADIER_API_KEY, AWS_PROFILE=clarinut-gmerton
"""

import argparse
import sys
from datetime import date

from lib.studies.delta_hedged_straddle import print_summary, run_study


def print_daily_detail(results: list[dict], entry_date_str: str) -> None:
    target = date.fromisoformat(entry_date_str)
    pos = next((r for r in results if r["entry_date"] == target), None)
    if pos is None:
        print(f"No position found for entry date {entry_date_str}")
        return

    print(f"\n--- Daily detail: {pos['entry_date']} → {pos['expiry']}  "
          f"strike ${pos['strike']:.2f}  status: {pos['status']} ---")
    print(f"  {'Date':<12} {'Stock':>8} {'Straddle':>10} {'NetΔ':>7} "
          f"{'HedgeSh':>9} {'StrdlPnL':>10} {'HedgePnL':>10} "
          f"{'DailyPnL':>10} {'CumPnL':>10}")
    print(f"  {'-'*98}")
    for d in pos["daily"]:
        print(f"  {str(d['date']):<12} {d['stock_close']:>8.3f} "
              f"{d['straddle_mid']:>10.4f} {d['net_delta']:>7.3f} "
              f"{d['hedge_shares']:>9.2f} {d['straddle_pnl']:>10.2f} "
              f"{d['hedge_pnl']:>10.2f} {d['daily_pnl']:>10.2f} "
              f"{d['cum_pnl']:>10.2f}")
    print(f"  {'-'*98}")
    print(f"  Total P&L: ${pos['total_pnl']:.2f}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delta-hedged ATM straddle backtest"
    )
    parser.add_argument("--ticker",  default="KWEB",  help="Underlying ticker")
    parser.add_argument("--months",  default=3, type=int, help="Months of history")
    parser.add_argument("--dte",     default=30, type=int, help="Target DTE")
    parser.add_argument("--refresh", action="store_true",  help="Force cache refresh")
    parser.add_argument("--detail",  default=None, metavar="YYYY-MM-DD",
                        help="Print day-by-day detail for this entry date")
    args = parser.parse_args()

    results = run_study(
        ticker=args.ticker,
        months_back=args.months,
        dte=args.dte,
        force_refresh=args.refresh,
    )

    print_summary(results, args.ticker)

    if args.detail:
        print_daily_detail(results, args.detail)


if __name__ == "__main__":
    main()
