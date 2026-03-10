#!/usr/bin/env python3
"""
Put calendar spread backtest — short ATM put (~20 DTE) + long put (~27 DTE) at same strike.

Strategy: long calendar (net debit). Sell near-term put, buy far-term put at the same
strike. Hold to short expiry, then close the long leg at market. Profitable when the
underlying stays near the strike at expiration of the near leg (short decays to zero,
long retains time value). Loses on large moves in either direction.

Per-ticker defaults (start date, split dates) are loaded from TICKER_CONFIG.
The short/long DTE targets, delta sweep, and VIX thresholds can all be overridden.

Usage
-----
  # UVXY — default: 20/27 DTE, deltas 0.40/0.45/0.50, 25% spread filter
  PYTHONPATH=src python run_calendar.py --ticker UVXY --spread 0.25

  # Custom DTE targets:
  PYTHONPATH=src python run_calendar.py --ticker UVXY --short-dte 15 --long-dte 22

  # Per-year detail for one combo:
  PYTHONPATH=src python run_calendar.py --ticker UVXY --spread 0.25 \\
      --detail-delta 0.50 --no-csv

  # Custom delta sweep:
  PYTHONPATH=src python run_calendar.py --ticker UVXY --deltas 0.40,0.45,0.50,0.55

Requires: MYSQL_PASSWORD, AWS_PROFILE=clarinut-gmerton, TRADIER_API_KEY
"""

import argparse
from datetime import date, datetime

from lib.studies.calendar_study import run_calendar_study
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


# Default calendar parameters (not stored in TICKER_CONFIG; calendar-specific)
_DEFAULT_DELTAS = [0.40, 0.45, 0.50]
_DEFAULT_VIX_THRESHOLDS = [None, 30, 25, 20]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Put calendar spread backtest (short near / long far, same strike)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ticker", required=True,
        choices=sorted(TICKER_CONFIG),
        help="Underlying ticker (must exist in TICKER_CONFIG)",
    )
    parser.add_argument(
        "--short-dte", type=int, default=20,
        help="Target DTE for the short (near) leg",
    )
    parser.add_argument(
        "--long-dte", type=int, default=27,
        help="Target DTE for the long (far) leg",
    )
    parser.add_argument(
        "--dte-tol", type=int, default=5,
        help="±DTE tolerance around the short-dte target",
    )
    parser.add_argument(
        "--gap-tol", type=int, default=5,
        help="±DTE tolerance for matching the long leg DTE",
    )
    parser.add_argument(
        "--min-gap", type=int, default=None,
        help="Min days between short and long expiry (next-expiry mode; overrides --long-dte/--gap-tol)",
    )
    parser.add_argument(
        "--max-gap", type=int, default=None,
        help="Max days between short and long expiry (used with --min-gap)",
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
        help=f"Comma-separated unsigned put delta targets; default {_DEFAULT_DELTAS}",
    )
    parser.add_argument(
        "--delta-err", type=float, default=0.08,
        help="Max |actual_delta - (-target)| for the short leg",
    )
    parser.add_argument(
        "--vix-thresholds", type=_parse_vix, default=None,
        help="Comma-separated VIX thresholds (use 'none' for no filter); "
             "default sweeps [None, 30, 25, 20]",
    )
    parser.add_argument(
        "--spread", type=float, default=None,
        help="Max bid-ask spread as fraction of mid on the short leg (e.g. 0.25 = 25%%); "
             "omit for no spread filter",
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
        "--min-iv-ratio", type=float, default=None,
        help="Minimum iv_ratio at entry (e.g. 1.0 = backwardation only)",
    )
    parser.add_argument(
        "--max-fwd-vol-factor", type=float, default=None,
        help="Maximum fwd_vol_factor at entry (sigma_fwd/short_iv; e.g. 1.0 = only enter "
             "when market expects vol to fall or stay flat in the forward window)",
    )
    parser.add_argument(
        "--fwd-vol-thresholds", type=_parse_floats, default=None,
        help="Comma-separated fwd_vol_factor thresholds to sweep (e.g. 1.30,1.20,1.10,1.00,0.90); "
             "default sweeps [none,1.30,1.20,1.10,1.00,0.90,0.80]",
    )
    parser.add_argument(
        "--profit-target", type=float, default=None,
        help="Profit-take ROC target (e.g. 0.50 = close when spread value ≥ 1.5× debit = +50%% ROC)",
    )
    parser.add_argument(
        "--iv-ratio-thresholds", type=_parse_floats, default=None,
        help="Comma-separated iv_ratio thresholds to sweep (e.g. 0.90,0.95,1.00,1.05,1.10,1.20); "
             "default sweeps [none,0.90,0.95,1.00,1.05,1.10,1.20]",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="CSV output path; defaults to <ticker_lower>_calendar_<today>.csv",
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

    cfg          = TICKER_CONFIG[args.ticker]
    ticker_lower = args.ticker.lower()

    start          = args.start          or cfg["start"]
    delta_targets  = args.deltas         or _DEFAULT_DELTAS
    vix_thresholds = args.vix_thresholds or _DEFAULT_VIX_THRESHOLDS
    output_csv     = (
        None if args.no_csv
        else (args.output or f"{ticker_lower}_calendar_{date.today().isoformat()}.csv")
    )

    run_calendar_study(
        ticker=args.ticker,
        start=start,
        end=args.end,
        delta_targets=delta_targets,
        vix_thresholds=vix_thresholds,
        short_dte_target=args.short_dte,
        long_dte_target=args.long_dte,
        dte_tol=args.dte_tol,
        gap_tol=args.gap_tol,
        min_gap=args.min_gap,
        max_gap=args.max_gap,
        entry_weekday=4,              # Fridays
        split_dates=cfg["split_dates"],
        max_delta_err=args.delta_err,
        max_spread_pct=args.spread,
        output_csv=output_csv,
        force_sync=args.refresh,
        detail_delta=args.detail_delta,
        detail_vix=args.detail_vix,
        iv_ratio_thresholds=args.iv_ratio_thresholds,
        fwd_vol_thresholds=args.fwd_vol_thresholds,
        profit_target_roc=args.profit_target,
        min_iv_ratio=args.min_iv_ratio,
        max_fwd_vol_factor=args.max_fwd_vol_factor,
    )


if __name__ == "__main__":
    main()
