#!/usr/bin/env python3
"""
UVXY 20-DTE ATM short straddle backtest.

Usage
-----
# First run — full sync from Athena (takes a few minutes), then run study:
  PYTHONPATH=src python run_uvxy_straddle.py

# Re-sync from scratch (e.g. after a schema change):
  PYTHONPATH=src python run_uvxy_straddle.py --refresh

# Different DTE target:
  PYTHONPATH=src python run_uvxy_straddle.py --dte 30

# Custom date range:
  PYTHONPATH=src python run_uvxy_straddle.py --start 2020-01-01 --end 2023-12-31

# Custom output file:
  PYTHONPATH=src python run_uvxy_straddle.py --output results/uvxy_20dte.csv

Requires: MYSQL_PASSWORD, AWS_PROFILE=clarinut-gmerton (or equivalent)
"""

import argparse
from datetime import date, datetime

from lib.studies.straddle_study import UVXY_SPLIT_DATES, run_study

# UVXY changed from 2× to 1.5× leverage on this date — only use post-change data
UVXY_LEVERAGE_CHANGE = date(2018, 1, 12)


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UVXY ATM short straddle backtest",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dte", type=int, default=20,
        help="Target DTE at entry",
    )
    parser.add_argument(
        "--dte-tol", type=int, default=5,
        help="±DTE tolerance (only accept expiries within [dte-tol, dte+tol])",
    )
    parser.add_argument(
        "--start", type=_parse_date, default=UVXY_LEVERAGE_CHANGE,
        help="Study start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end", type=_parse_date, default=date.today(),
        help="Study end date for entries (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--delta", type=float, default=0.50,
        help="Target call delta for ATM selection",
    )
    parser.add_argument(
        "--delta-err", type=float, default=0.10,
        help="Max |actual_delta - target_delta| allowed for the call leg",
    )
    parser.add_argument(
        "--output", type=str,
        default=f"uvxy_straddle_{date.today().isoformat()}.csv",
        help="CSV output path",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Force re-sync of options_cache from Athena (ignores existing data)",
    )
    parser.add_argument(
        "--no-csv", action="store_true",
        help="Skip CSV output (print summary only)",
    )
    args = parser.parse_args()

    output_csv = None if args.no_csv else args.output

    run_study(
        ticker="UVXY",
        start=args.start,
        end=args.end,
        dte_target=args.dte,
        dte_tol=args.dte_tol,
        call_delta=args.delta,
        entry_weekday=4,          # Fridays, consistent with other studies
        split_dates=UVXY_SPLIT_DATES,
        max_call_delta_err=args.delta_err,
        output_csv=output_csv,
        force_sync=args.refresh,
    )


if __name__ == "__main__":
    main()
