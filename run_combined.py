#!/usr/bin/env python3
"""
Generic combined strategy analysis: bear call spread + short put.

Loads from previously saved CSV files produced by run_puts.py and
run_call_spreads.py (fast — no MySQL/Athena needed).

By default the script finds the most recently dated CSV in the repo root
matching the expected naming pattern (<ticker_lower>_puts_*.csv and
<ticker_lower>_call_spreads_*.csv).

Usage
-----
# Use the most recent CSVs for a ticker:
  PYTHONPATH=src python run_combined.py --ticker UVXY
  PYTHONPATH=src python run_combined.py --ticker TLT

# Specify CSV files explicitly:
  PYTHONPATH=src python run_combined.py --ticker TLT \\
      --put-csv tlt_puts_2026-03-03.csv \\
      --spread-csv tlt_call_spreads_2026-03-03.csv

# Override the (delta, wing, VIX) parameters used to slice the CSVs:
  PYTHONPATH=src python run_combined.py --ticker TLT \\
      --put-delta 0.20 --put-vix 25 --short-delta 0.25 --wing 0.10
"""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from lib.studies.combined_study import combine_strategies, print_combined_summary
from lib.studies.ticker_config import TICKER_CONFIG

_ROOT = Path(__file__).parent


def _latest_csv(pattern: str) -> str:
    """Return path of the most recently dated CSV matching <pattern>_*.csv."""
    matches = sorted(_ROOT.glob(f"{pattern}_*.csv"), reverse=True)
    if matches:
        return str(matches[0])
    return str(_ROOT / f"{pattern}_{date.today().isoformat()}.csv")


def load_and_filter(
    put_csv: str,
    spread_csv: str,
    put_delta: float,
    put_vix_max: float,
    short_delta: float,
    wing_width: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load CSVs and filter to the requested (delta, wing, VIX) combination."""
    puts    = pd.read_csv(put_csv)
    spreads = pd.read_csv(spread_csv)

    puts_f = puts[
        (puts["delta_target"]   == put_delta)
        & (puts["vix_threshold"] == put_vix_max)
    ].copy()

    # All-VIX spreads: no VIX filter applied at entry (call spread always enters).
    spreads_f = spreads[
        (spreads["short_delta_target"] == short_delta)
        & (spreads["wing_delta_width"] == wing_width)
        & spreads["vix_threshold"].isna()
    ].copy()

    print(f"Put trades    : {len(puts_f):>4}  (delta={put_delta}, VIX<{put_vix_max:.0f})")
    print(f"Spread trades : {len(spreads_f):>4}  (short={short_delta}, wing={wing_width}, All VIX)")

    if puts_f.empty:
        raise SystemExit(
            f"No put trades found for delta={put_delta}, vix_threshold={put_vix_max}.\n"
            f"Available: delta={sorted(puts['delta_target'].unique())}, "
            f"vix={sorted(puts['vix_threshold'].dropna().unique())}"
        )
    if spreads_f.empty:
        raise SystemExit(
            f"No spread trades found for short={short_delta}, wing={wing_width}.\n"
            f"Available short_deltas={sorted(spreads['short_delta_target'].unique())}, "
            f"wings={sorted(spreads['wing_delta_width'].unique())}"
        )

    return puts_f, spreads_f


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generic combined strategy: call spread + short put",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ticker", required=True,
        choices=sorted(TICKER_CONFIG),
        help="Underlying ticker (must exist in TICKER_CONFIG)",
    )
    parser.add_argument(
        "--put-csv", default=None,
        help="Put study CSV; defaults to the most recent <ticker_lower>_puts_*.csv",
    )
    parser.add_argument(
        "--spread-csv", default=None,
        help="Call spread CSV; defaults to the most recent <ticker_lower>_call_spreads_*.csv",
    )
    parser.add_argument(
        "--put-delta", type=float, default=None,
        help="Put delta to slice from the put CSV; defaults to ticker's middle put_delta",
    )
    parser.add_argument(
        "--put-vix", type=float, default=None,
        help="Put VIX entry threshold (VIX must be < this value); defaults to 20",
    )
    parser.add_argument(
        "--short-delta", type=float, default=None,
        help="Call spread short delta to slice from the spread CSV; "
             "defaults to ticker's middle short_delta",
    )
    parser.add_argument(
        "--wing", type=float, default=None,
        help="Call spread wing width to slice from the spread CSV; "
             "defaults to ticker's middle wing_width",
    )
    args = parser.parse_args()

    cfg = TICKER_CONFIG[args.ticker]
    ticker_lower = args.ticker.lower()

    put_csv    = args.put_csv    or _latest_csv(f"{ticker_lower}_puts")
    spread_csv = args.spread_csv or _latest_csv(f"{ticker_lower}_call_spreads")

    # Default to the middle of the configured sweep ranges as a sensible starting point.
    put_deltas   = cfg["put_deltas"]
    short_deltas = cfg["short_deltas"]
    wing_widths  = cfg["wing_widths"]

    put_delta   = args.put_delta   or put_deltas[len(put_deltas) // 2]
    put_vix_max = args.put_vix     or 20.0
    short_delta = args.short_delta or short_deltas[len(short_deltas) // 2]
    wing_width  = args.wing        or wing_widths[len(wing_widths) // 2]

    puts_f, spreads_f = load_and_filter(
        put_csv, spread_csv,
        put_delta=put_delta,
        put_vix_max=put_vix_max,
        short_delta=short_delta,
        wing_width=wing_width,
    )

    combined = combine_strategies(puts_f, spreads_f)
    print_combined_summary(
        combined,
        put_delta=put_delta,
        short_delta=short_delta,
        wing_width=wing_width,
        put_vix_max=put_vix_max,
        ticker=args.ticker,
    )


if __name__ == "__main__":
    main()
