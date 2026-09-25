#!/usr/bin/env python3
"""
UVXY short call backtest — delta sweep with VIX regime filter.

Usage
-----
# Default run (delta 0.10–0.50, all VIX thresholds, 30 DTE, 50% profit take):
  PYTHONPATH=src python run_uvxy_calls.py

# With 25% spread filter (more realistic execution):
  PYTHONPATH=src python run_uvxy_calls.py --spread 0.25

# 20 DTE:
  PYTHONPATH=src python run_uvxy_calls.py --dte 20 --spread 0.25

# Per-year detail for a specific combo:
  PYTHONPATH=src python run_uvxy_calls.py --spread 0.25 --detail-delta 0.30 --detail-vix 25

# Re-sync options cache from Athena:
  PYTHONPATH=src python run_uvxy_calls.py --refresh

# Custom delta range or VIX thresholds:
  PYTHONPATH=src python run_uvxy_calls.py --deltas 0.20,0.30,0.40,0.50 --vix-thresholds none,30,25,20

Requires: MYSQL_PASSWORD, AWS_PROFILE=clarinut-gmerton, TRADIER_API_KEY
"""

import argparse
from datetime import date, datetime

from lib.studies.call_study import run_call_study
from lib.studies.straddle_study import UVXY_SPLIT_DATES

UVXY_LEVERAGE_CHANGE = date(2018, 1, 12)

DEFAULT_DELTAS        = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]
DEFAULT_VIX_THRESHOLDS = [None, 30, 25, 20]


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _parse_deltas(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(",")]


def _parse_vix(s: str) -> list:
    result = []
    for x in s.split(","):
        x = x.strip().lower()
        if x in ("none", "all", ""):
            result.append(None)
        else:
            result.append(float(x))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UVXY short call backtest — delta sweep with VIX filter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dte", type=int, default=30,
        help="Target DTE at entry",
    )
    parser.add_argument(
        "--dte-tol", type=int, default=5,
        help="±DTE tolerance",
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
        "--deltas", type=_parse_deltas, default=DEFAULT_DELTAS,
        help="Comma-separated unsigned call delta targets, e.g. 0.10,0.30,0.50",
    )
    parser.add_argument(
        "--delta-err", type=float, default=0.08,
        help="Max |actual_delta - target_delta| allowed",
    )
    parser.add_argument(
        "--vix-thresholds", type=_parse_vix, default=DEFAULT_VIX_THRESHOLDS,
        help="Comma-separated VIX thresholds (use 'none' for no filter), e.g. none,30,25,20",
    )
    parser.add_argument(
        "--profit-take", type=float, default=0.50,
        help="Exit when call mid ≤ (1 - profit_take) × entry_mid",
    )
    parser.add_argument(
        "--spread", type=float, default=None,
        help="Max spread as fraction of mid at entry (e.g. 0.25 = 25%%). "
             "Omit to apply no spread filter.",
    )
    parser.add_argument(
        "--detail-delta", type=float, default=None,
        help="Print per-year breakdown for this delta target",
    )
    parser.add_argument(
        "--detail-vix", type=float, default=None,
        help="VIX threshold for the per-year detail (omit = no filter)",
    )
    parser.add_argument(
        "--output", type=str,
        default=f"uvxy_calls_{date.today().isoformat()}.csv",
        help="CSV output path",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Force re-sync of options_cache from Athena",
    )
    parser.add_argument(
        "--no-csv", action="store_true",
        help="Skip CSV output (print summary only)",
    )
    args = parser.parse_args()

    output_csv = None if args.no_csv else args.output

    run_call_study(
        ticker="UVXY",
        start=args.start,
        end=args.end,
        delta_targets=args.deltas,
        vix_thresholds=args.vix_thresholds,
        dte_target=args.dte,
        dte_tol=args.dte_tol,
        entry_weekday=4,
        split_dates=UVXY_SPLIT_DATES,
        max_delta_err=args.delta_err,
        max_spread_pct=args.spread,
        profit_take_pct=args.profit_take,
        output_csv=output_csv,
        force_sync=args.refresh,
        detail_delta=args.detail_delta,
        detail_vix=args.detail_vix,
    )


if __name__ == "__main__":
    main()
