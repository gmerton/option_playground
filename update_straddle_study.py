#!/usr/bin/env python3
"""
Incremental straddle study update.

Fetches only the new date range from Athena for tickers already in the MySQL
summary table, upserts the new detail rows, then recomputes all summary stats
from the full MySQL detail table.

Usage:
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python3 update_straddle_study.py
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python3 update_straddle_study.py --ts-start 2025-09-01 --ts-end 2026-03-16
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lib.mysql_lib import get_study_tickers
from lib.condor_tools import straddle_study


def main():
    parser = argparse.ArgumentParser(description="Incremental straddle study update")
    parser.add_argument("--ts-start", default="2025-09-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--ts-end",   default="2026-03-16", help="End date YYYY-MM-DD")
    args = parser.parse_args()

    print("Fetching tickers from MySQL summary table...")
    tickers = get_study_tickers()
    print(f"  {len(tickers)} tickers found\n")

    print(f"Running straddle study for {args.ts_start} → {args.ts_end}...")
    straddle_study(tickers, ts_start=args.ts_start, ts_end=args.ts_end)


if __name__ == "__main__":
    main()
