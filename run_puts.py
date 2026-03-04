#!/usr/bin/env python3
"""
Generic short put backtest — delta sweep with VIX regime filter.

Per-ticker defaults (start date, delta sweep, VIX thresholds, split dates) are
loaded from TICKER_CONFIG in src/lib/studies/ticker_config.py.  All defaults
can be overridden on the command line.

Usage
-----
# Default run for a given ticker:
  PYTHONPATH=src python run_puts.py --ticker UVXY
  PYTHONPATH=src python run_puts.py --ticker TLT

# Re-sync options cache from Athena before running:
  PYTHONPATH=src python run_puts.py --ticker TLT --refresh

# Single delta with per-year detail:
  PYTHONPATH=src python run_puts.py --ticker TLT --deltas 0.20 --detail-delta 0.20

# Per-year detail for a specific (delta, VIX) combo:
  PYTHONPATH=src python run_puts.py --ticker TLT --detail-delta 0.20 --detail-vix 25

# Custom date range or DTE:
  PYTHONPATH=src python run_puts.py --ticker UVXY --start 2020-01-01 --dte 30

# Skip CSV output:
  PYTHONPATH=src python run_puts.py --ticker TLT --no-csv

Requires: MYSQL_PASSWORD, AWS_PROFILE=clarinut-gmerton
"""

import argparse
from datetime import date, datetime

from lib.studies.put_study import run_put_study
from lib.studies.ticker_config import TICKER_CONFIG


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _parse_floats(s: str) -> list[float]:
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
        description="Generic short put backtest — delta sweep with VIX filter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ticker", required=True,
        choices=sorted(TICKER_CONFIG),
        help="Underlying ticker (must exist in TICKER_CONFIG)",
    )
    parser.add_argument(
        "--dte", type=int, default=20,
        help="Target DTE at entry",
    )
    parser.add_argument(
        "--dte-tol", type=int, default=5,
        help="±DTE tolerance around the target",
    )
    parser.add_argument(
        "--start", type=_parse_date, default=None,
        help="Study start date (YYYY-MM-DD); defaults to ticker's configured start",
    )
    parser.add_argument(
        "--end", type=_parse_date, default=date.today(),
        help="Study end date for entries (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--deltas", type=_parse_floats, default=None,
        help="Comma-separated unsigned put delta targets, e.g. 0.10,0.20,0.30; "
             "defaults to ticker's configured sweep",
    )
    parser.add_argument(
        "--delta-err", type=float, default=0.08,
        help="Max |actual_delta - target_delta| allowed",
    )
    parser.add_argument(
        "--vix-thresholds", type=_parse_vix, default=None,
        help="Comma-separated VIX thresholds (use 'none' for no filter), e.g. none,30,25,20; "
             "defaults to ticker's configured sweep",
    )
    parser.add_argument(
        "--profit-take", type=float, default=0.50,
        help="Exit when put mid <= (1 - profit_take) × entry_mid",
    )
    parser.add_argument(
        "--spread", type=float, default=None,
        help="Max bid-ask spread as fraction of mid at entry (e.g. 0.25 = 25%%); "
             "omit to apply no spread filter",
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
        "--output", type=str, default=None,
        help="CSV output path; defaults to <ticker_lower>_puts_<today>.csv",
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

    cfg = TICKER_CONFIG[args.ticker]
    ticker_lower = args.ticker.lower()

    start           = args.start            or cfg["start"]
    delta_targets   = args.deltas           or cfg["put_deltas"]
    vix_thresholds  = args.vix_thresholds   or cfg["vix_thresholds"]
    output_csv      = (
        None if args.no_csv
        else (args.output or f"{ticker_lower}_puts_{date.today().isoformat()}.csv")
    )

    run_put_study(
        ticker=args.ticker,
        start=start,
        end=args.end,
        delta_targets=delta_targets,
        vix_thresholds=vix_thresholds,
        dte_target=args.dte,
        dte_tol=args.dte_tol,
        entry_weekday=4,                  # Fridays
        split_dates=cfg["split_dates"],
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
