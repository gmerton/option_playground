#!/usr/bin/env python3
"""
Generic bull put spread backtest — short delta × wing width × VIX regime sweep.

Per-ticker defaults (start date, delta sweep, wing widths, VIX thresholds, split
dates) are loaded from TICKER_CONFIG in src/lib/studies/ticker_config.py.
All defaults can be overridden on the command line.

Usage
-----
# Default run for a given ticker:
  PYTHONPATH=src python run_put_spreads.py --ticker GLD
  PYTHONPATH=src python run_put_spreads.py --ticker TLT

# With a 25% spread filter on the short leg:
  PYTHONPATH=src python run_put_spreads.py --ticker GLD --spread 0.25

# Per-year detail for a specific (short_delta, wing, VIX) combo:
  PYTHONPATH=src python run_put_spreads.py --ticker GLD --spread 0.25 \\
      --detail-short-delta 0.25 --detail-wing 0.10 --no-csv

# Custom parameters:
  PYTHONPATH=src python run_put_spreads.py --ticker GLD \\
      --short-deltas 0.20,0.25,0.30 --wing-widths 0.05,0.10 --dte 20

Requires: MYSQL_PASSWORD, AWS_PROFILE=clarinut-gmerton, TRADIER_API_KEY
"""

import argparse
from datetime import date, datetime

from lib.studies.put_spread_study import run_put_spread_study
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
        description="Generic bull put spread backtest — short delta × wing width × VIX filter",
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
        "--short-deltas", type=_parse_floats, default=None,
        help="Comma-separated unsigned short put delta targets, e.g. 0.20,0.25,0.30; "
             "defaults to ticker's configured sweep",
    )
    parser.add_argument(
        "--wing-widths", type=_parse_floats, default=None,
        help="Comma-separated wing delta widths, e.g. 0.05,0.10,0.15; "
             "defaults to ticker's configured sweep",
    )
    parser.add_argument(
        "--delta-err", type=float, default=0.08,
        help="Max |actual_delta - target_delta| for each leg",
    )
    parser.add_argument(
        "--vix-thresholds", type=_parse_vix, default=None,
        help="Comma-separated VIX thresholds (use 'none' for no filter); "
             "defaults to ticker's configured sweep",
    )
    parser.add_argument(
        "--profit-take", type=float, default=0.50,
        help="Exit when net spread value <= (1 - profit_take) × net_credit",
    )
    parser.add_argument(
        "--spread", type=float, default=None,
        help="Max bid-ask spread as fraction of mid for the short leg (e.g. 0.25 = 25%%); "
             "omit to apply no spread filter",
    )
    parser.add_argument(
        "--detail-short-delta", type=float, default=None,
        help="Print per-year breakdown for this short delta",
    )
    parser.add_argument(
        "--detail-wing", type=float, default=None,
        help="Wing width for the per-year detail",
    )
    parser.add_argument(
        "--detail-vix", type=float, default=None,
        help="VIX threshold for the per-year detail (omit = no filter)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="CSV output path; defaults to <ticker_lower>_put_spreads_<today>.csv",
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

    start          = args.start          or cfg["start"]
    short_deltas   = args.short_deltas   or cfg["short_deltas"]
    wing_widths    = args.wing_widths    or cfg["wing_widths"]
    vix_thresholds = args.vix_thresholds or cfg["vix_thresholds"]
    output_csv     = (
        None if args.no_csv
        else (args.output or f"{ticker_lower}_put_spreads_{date.today().isoformat()}.csv")
    )

    run_put_spread_study(
        ticker=args.ticker,
        start=start,
        end=args.end,
        short_delta_targets=short_deltas,
        wing_delta_widths=wing_widths,
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
        detail_short_delta=args.detail_short_delta,
        detail_wing_width=args.detail_wing,
        detail_vix=args.detail_vix,
    )


if __name__ == "__main__":
    main()
