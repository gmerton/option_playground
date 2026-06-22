#!/usr/bin/env python3
"""
Daily breakout scan over the curated preferred-ticker universe.

Reads data/preferred_tickers.txt, runs the Luk/Qullamaggie EOD screen
(Stage 2 + EMA stack + ADR + dollar-volume + tight-base pivot + breakout
volume confirmation), prints the report, and writes three artifacts under
data/watchlist/:

  eod_<YYYY-MM-DD>.txt   -- the human-readable report (archived per day)
  eod_latest.json        -- full structured results + derived buckets
  monitor_latest.json    -- the coiling/primed names in breakout_monitor.py's
                            CONFIG schema; this is the bridge to the intraday
                            trigger monitor (ibkr_bot/breakout_monitor.py
                            --watchlist data/watchlist/monitor_latest.json)

Usage:
  PYTHONPATH=src python run_preferred_breakouts.py
  PYTHONPATH=src python run_preferred_breakouts.py --mode premarket

Requires: TRADIER_API_KEY (premarket mode also needs yfinance).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from lib.interface.breakout_artifacts import buckets as derive_buckets
from lib.interface.breakout_artifacts import monitor_config
from lib.interface.premarket_watchlist import (
    enrich_premarket,
    format_eod_output,
    format_premarket_output,
    run_eod_scan,
)
from lib.tradier.tradier_client_wrapper import TradierClient

REPO_ROOT = Path(__file__).resolve().parent
TICKERS_FILE = REPO_ROOT / "data" / "preferred_tickers.txt"
OUT_DIR = REPO_ROOT / "data" / "watchlist"


def _load_tickers() -> List[str]:
    if not TICKERS_FILE.exists():
        print(f"Error: {TICKERS_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    return [ln.strip().upper() for ln in TICKERS_FILE.read_text().splitlines() if ln.strip()]


def _write_artifacts(results: List[Dict[str, Any]], report: str, as_of: date) -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    monitor = monitor_config(results)
    bk = derive_buckets(results)

    (OUT_DIR / f"eod_{as_of}.txt").write_text(report)
    (OUT_DIR / "monitor_latest.json").write_text(json.dumps(monitor, indent=2))
    (OUT_DIR / "eod_latest.json").write_text(json.dumps({
        "as_of": str(as_of),
        "n_candidates": len(results),
        "confirmed_breakouts": [r["ticker"] for r in bk["confirmed"]],
        "monitor_list": list(monitor.keys()),
        "results": results,
    }, indent=2))
    return {"monitor": monitor, "buckets": bk}


async def _run(api_key: str, tickers: List[str], premarket: bool) -> None:
    print(f"Scanning {len(tickers)} preferred tickers...", flush=True)
    async with TradierClient(api_key=api_key) as client:
        results = await run_eod_scan(client, tickers)

    as_of = date.today()
    report = format_eod_output(results, as_of)
    print(report)

    if premarket:
        enriched = enrich_premarket(results)
        report = report + "\n" + format_premarket_output(enriched, as_of)
        print(format_premarket_output(enriched, as_of))

    info = _write_artifacts(results, report, as_of)
    mon = info["monitor"]
    confirmed = info["buckets"]["confirmed"]

    print(f"\n--- Artifacts written to {OUT_DIR} ---")
    print(f"  Confirmed breakouts ({len(confirmed)}): "
          f"{', '.join(r['ticker'] for r in confirmed) or '(none)'}")
    print(f"  Intraday monitor list ({len(mon)}): "
          f"{', '.join(mon.keys()) or '(none)'}")
    print(f"\nTo arm the intraday trigger monitor (market hours, IB gateway up):")
    print(f"  .venv/bin/python3 ibkr_bot/breakout_monitor.py "
          f"--watchlist {OUT_DIR / 'monitor_latest.json'}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Preferred-ticker breakout scan")
    ap.add_argument("--mode", choices=["eod", "premarket"], default="eod",
                    help="eod: scan only; premarket: + yfinance gap overlay")
    args = ap.parse_args()

    api_key = os.environ.get("TRADIER_API_KEY")
    if not api_key:
        print("Error: TRADIER_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(_run(api_key, _load_tickers(), args.mode == "premarket"))


if __name__ == "__main__":
    main()
