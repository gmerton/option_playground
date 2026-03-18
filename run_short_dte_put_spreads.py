#!/usr/bin/env python3
"""
Short-DTE bull put spread backtest — 0-5 DTE, Thursday entry, trend-filtered sweep.

Sweeps short delta × wing width × VIX regime × MA trend filter.
Designed for near-expiry (0-5 DTE) put spreads on liquid underlyings.

Usage
-----
# Default run (Thursday entry, 1 DTE target, 0.10–0.20Δ, MA sweep):
  PYTHONPATH=src python run_short_dte_put_spreads.py --ticker GLD

# Custom DTE and entry day:
  PYTHONPATH=src python run_short_dte_put_spreads.py --ticker TLT --dte 2 --entry-weekday 3

# Specific delta/wing combo with per-year detail:
  PYTHONPATH=src python run_short_dte_put_spreads.py --ticker GLD \\
      --detail-short-delta 0.10 --detail-wing 0.05 --no-csv

# No MA sweep (unfiltered only):
  PYTHONPATH=src python run_short_dte_put_spreads.py --ticker GLD --no-ma-sweep

Requires: MYSQL_PASSWORD, AWS_PROFILE=clarinut-gmerton, TRADIER_API_KEY
"""

import argparse
from datetime import date, datetime

from lib.studies.put_spread_study import run_put_spread_study
from lib.studies.ticker_config import TICKER_CONFIG

_WEEKDAY_NAMES = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday",
}


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _parse_floats(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(",")]


def _parse_vix(s: str) -> list:
    result = []
    for x in s.split(","):
        x = x.strip().lower()
        result.append(None if x in ("none", "all", "") else float(x))
    return result


def _parse_ma(s: str) -> list:
    result = []
    for x in s.split(","):
        x = x.strip().lower()
        result.append(None if x in ("none", "all", "") else int(x))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Short-DTE bull put spread backtest — Thursday entry, trend filter sweep",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ticker", required=True,
        choices=sorted(TICKER_CONFIG),
        help="Underlying ticker (must exist in TICKER_CONFIG)",
    )
    parser.add_argument(
        "--dte", type=int, default=1,
        help="Target DTE at entry (default 1 = Thursday entry → Friday expiry)",
    )
    parser.add_argument(
        "--dte-tol", type=int, default=4,
        help="±DTE tolerance (default 4 = accepts 0-5 DTE window)",
    )
    parser.add_argument(
        "--entry-weekday", type=int, default=3,
        choices=[0, 1, 2, 3, 4],
        metavar="N",
        help="Entry day of week: 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri (default 3=Thursday)",
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
        "--short-deltas", type=_parse_floats, default=[0.05, 0.10, 0.15, 0.20],
        help="Comma-separated unsigned short put delta targets",
    )
    parser.add_argument(
        "--wing-widths", type=_parse_floats, default=[0.05, 0.10],
        help="Comma-separated wing delta widths",
    )
    parser.add_argument(
        "--vix-thresholds", type=_parse_vix, default=[None, 25, 20],
        help="Comma-separated VIX thresholds (use 'none' for no filter)",
    )
    parser.add_argument(
        "--ma-thresholds", type=_parse_ma, default=[None, 20, 50, 200],
        help="Comma-separated MA lookback periods to sweep as trend filters "
             "(e.g. 'none,20,50,200'); 'none' = no filter baseline",
    )
    parser.add_argument(
        "--no-ma-sweep", action="store_true",
        help="Disable MA sweep — output unfiltered results only",
    )
    parser.add_argument(
        "--delta-err", type=float, default=0.06,
        help="Max |actual_delta - target_delta| for each leg (tighter than 20DTE default)",
    )
    parser.add_argument(
        "--spread", type=float, default=0.25,
        help="Max bid-ask spread as fraction of mid for the short leg",
    )
    parser.add_argument(
        "--profit-take", type=float, default=0.50,
        help="Exit when net spread value <= (1 - profit_take) × net_credit",
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
        help="CSV output path",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Force re-sync of options_cache from Athena",
    )
    parser.add_argument(
        "--no-csv", action="store_true",
        help="Skip CSV output",
    )
    args = parser.parse_args()

    cfg = TICKER_CONFIG[args.ticker]
    ticker_lower = args.ticker.lower()

    start         = args.start or cfg["start"]
    ma_thresholds = None if args.no_ma_sweep else args.ma_thresholds
    output_csv    = (
        None if args.no_csv
        else (args.output or f"{ticker_lower}_short_dte_puts_{date.today().isoformat()}.csv")
    )

    day_name = _WEEKDAY_NAMES.get(args.entry_weekday, str(args.entry_weekday))
    print(
        f"\nShort-DTE put spread study: {args.ticker}  "
        f"DTE={args.dte}±{args.dte_tol}  entry={day_name}  "
        f"deltas={args.short_deltas}  wings={args.wing_widths}"
    )
    if ma_thresholds:
        print(f"MA trend filter sweep: {ma_thresholds}")

    run_put_spread_study(
        ticker=args.ticker,
        start=start,
        end=args.end,
        short_delta_targets=args.short_deltas,
        wing_delta_widths=args.wing_widths,
        vix_thresholds=args.vix_thresholds,
        dte_target=args.dte,
        dte_tol=args.dte_tol,
        entry_weekday=args.entry_weekday,
        split_dates=cfg["split_dates"],
        max_delta_err=args.delta_err,
        max_spread_pct=args.spread,
        profit_take_pct=args.profit_take,
        output_csv=output_csv,
        force_sync=args.refresh,
        detail_short_delta=args.detail_short_delta,
        detail_wing_width=args.detail_wing,
        detail_vix=args.detail_vix,
        ma_thresholds=ma_thresholds,
    )


if __name__ == "__main__":
    main()
