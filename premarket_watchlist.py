#!/usr/bin/env python3
"""
Pre-market watchlist CLI.

Usage:
    # EOD prep — run after market close (~7pm ET)
    PYTHONPATH=src python premarket_watchlist.py --mode eod

    # Pre-market enrichment — run 8-9am ET
    PYTHONPATH=src python premarket_watchlist.py --mode premarket

    # Extended universe
    PYTHONPATH=src python premarket_watchlist.py --mode eod --universe nyse
    PYTHONPATH=src python premarket_watchlist.py --mode eod --universe all

    # Custom ticker list
    PYTHONPATH=src python premarket_watchlist.py --mode eod --universe NVDA,MSFT,AAPL

Requires: TRADIER_API_KEY
Pre-market mode also requires: pip install yfinance
"""

import argparse
import asyncio
import os
import sys
from datetime import date

from lib.interface.premarket_watchlist import (
    DEFAULT_UNIVERSE,
    enrich_premarket,
    format_eod_output,
    format_premarket_output,
    run_eod_scan,
)
from lib.tradier.tradier_client_wrapper import TradierClient


def _get_universe(name: str) -> list[str]:
    if name == "default":
        return DEFAULT_UNIVERSE

    if name in ("nyse", "all"):
        from lib.commons.nyse_arca_list import nyse_list, nasdaq_list
        if name == "nyse":
            return list(nyse_list)
        return sorted(set(list(nyse_list) + list(nasdaq_list)))

    # Treat as comma-separated ticker list
    tickers = [t.strip().upper() for t in name.split(",") if t.strip()]
    if tickers:
        return tickers

    print(f"Unknown universe '{name}'. Using default.", file=sys.stderr)
    return DEFAULT_UNIVERSE


async def _run_eod(api_key: str, tickers: list[str]) -> list[dict]:
    print(f"Scanning {len(tickers)} tickers for EOD watchlist...", flush=True)
    async with TradierClient(api_key=api_key) as client:
        results = await run_eod_scan(client, tickers)
    print(format_eod_output(results, date.today()))
    return results


async def _run_premarket(api_key: str, tickers: list[str]) -> None:
    print(f"Scanning {len(tickers)} tickers...", flush=True)
    async with TradierClient(api_key=api_key) as client:
        eod_results = await run_eod_scan(client, tickers)

    print(f"EOD scan complete: {len(eod_results)} candidates", flush=True)
    print(format_eod_output(eod_results, date.today()))

    print("Fetching pre-market prices via yfinance...", flush=True)
    enriched = enrich_premarket(eod_results)
    print(format_premarket_output(enriched, date.today()))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pre-market watchlist scanner (Luk / Qullamaggie style)"
    )
    parser.add_argument(
        "--mode",
        choices=["eod", "premarket"],
        default="eod",
        help=(
            "eod: EOD scan only (run after close); "
            "premarket: EOD scan + pre-market gap enrichment (run 8-9am ET)"
        ),
    )
    parser.add_argument(
        "--universe",
        default="default",
        help="Ticker universe: default | nyse | all | TICKER1,TICKER2,...",
    )
    args = parser.parse_args()

    api_key = os.environ.get("TRADIER_API_KEY")
    if not api_key:
        print("Error: TRADIER_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    tickers = _get_universe(args.universe)
    print(f"Universe: {args.universe} ({len(tickers)} tickers)")

    if args.mode == "eod":
        asyncio.run(_run_eod(api_key, tickers))
    else:
        asyncio.run(_run_premarket(api_key, tickers))


if __name__ == "__main__":
    main()
