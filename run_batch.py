#!/usr/bin/env python3
"""
Batch put sweep + put spread sweep for multiple tickers.

Efficiency vs. running each ticker sequentially:
  1. Athena syncs run in parallel (ThreadPoolExecutor) — biggest win:
       4 tickers × ~3 min/sync = ~12 min sequential → ~3 min parallel
  2. VIX data fetched once and shared across all tickers.
  3. Each ticker's sweep (fast, in-memory pandas) runs sequentially
     so output stays readable.

Usage
-----
  # Default: sync + put sweep + put spread sweep for all four tickers
  PYTHONPATH=src python run_batch.py --tickers XLE,XLV,XOP,USO --spread 0.25

  # Puts only, no CSV output:
  PYTHONPATH=src python run_batch.py --tickers XLE,XLV --spread 0.25 --no-spread --no-csv

  # Force re-sync from Athena:
  PYTHONPATH=src python run_batch.py --tickers XLE,XLV,XOP,USO --refresh

Requires: MYSQL_PASSWORD, AWS_PROFILE=clarinut-gmerton, TRADIER_API_KEY
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import date, timedelta
from typing import Optional

import pandas as pd

from lib.mysql_lib import fetch_options_cache
from lib.studies.put_study import (
    fetch_vix_data,
    run_delta_sweep,
    print_sweep_summary,
)
from lib.studies.put_spread_study import (
    run_spread_delta_sweep,
    print_spread_sweep_summary,
)
from lib.studies.ticker_config import TICKER_CONFIG


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch put + put-spread sweep across multiple tickers",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--tickers", required=True,
        help="Comma-separated tickers, e.g. XLE,XLV,XOP,USO. "
             "Each must exist in TICKER_CONFIG.",
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
        "--end", type=lambda s: date.fromisoformat(s), default=date.today(),
        help="Study end date for entries (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--spread", type=float, default=None,
        help="Max bid-ask spread as fraction of mid on short leg (e.g. 0.25)",
    )
    parser.add_argument(
        "--profit-take", type=float, default=0.50,
        help="Exit when net spread value <= (1 - profit_take) × net_credit",
    )
    parser.add_argument(
        "--sync-workers", type=int, default=4,
        help="Number of parallel Athena sync workers",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Force re-sync of options_cache from Athena for all tickers",
    )
    parser.add_argument(
        "--no-puts", action="store_true",
        help="Skip short put sweep",
    )
    parser.add_argument(
        "--no-spread", action="store_true",
        help="Skip put spread sweep",
    )
    parser.add_argument(
        "--no-csv", action="store_true",
        help="Skip CSV output",
    )
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    unknown = [t for t in tickers if t not in TICKER_CONFIG]
    if unknown:
        print(f"ERROR: unknown tickers (not in TICKER_CONFIG): {unknown}", file=sys.stderr)
        sys.exit(1)

    today_str = date.today().isoformat()
    BAR = "=" * 72

    # ── Step 1: Parallel Athena sync via subprocesses ────────────────────────
    # boto3/awswrangler is not thread-safe; spawn one subprocess per ticker so
    # each gets its own Python interpreter and AWS session.
    print(f"\n{BAR}")
    print(f"  BATCH SYNC — {', '.join(tickers)}  ({args.sync_workers} workers)")
    print(BAR)

    env = os.environ.copy()
    sync_script = (
        "import sys; from datetime import date; "
        "from lib.studies.straddle_study import sync_options_cache; "
        "ticker, start_str, force = sys.argv[1], sys.argv[2], sys.argv[3]=='1'; "
        "y,m,d = map(int, start_str.split('-')); "
        "n = sync_options_cache(ticker, date(y,m,d), force=force); "
        "print(f'[{ticker}] sync done ({n:,} rows upserted)')"
    )

    procs: dict[subprocess.Popen, str] = {}
    queue = list(tickers)
    active: list[tuple[subprocess.Popen, str]] = []

    while queue or active:
        # Fill up to max workers
        while queue and len(active) < args.sync_workers:
            ticker = queue.pop(0)
            cfg    = TICKER_CONFIG[ticker]
            start  = cfg["start"]
            force  = "1" if args.refresh else "0"
            proc   = subprocess.Popen(
                [sys.executable, "-c", sync_script, ticker, start.isoformat(), force],
                env={**env, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            active.append((proc, ticker))

        # Poll for completed processes
        still_running = []
        for proc, ticker in active:
            rc = proc.poll()
            if rc is None:
                still_running.append((proc, ticker))
            else:
                out = proc.stdout.read().strip()
                if rc == 0:
                    print(f"  {out}" if out else f"  [{ticker}] sync done")
                else:
                    print(f"  [{ticker}] ERROR (exit {rc}): {out}")
        active = still_running

        if active:
            import time; time.sleep(1)

    # ── Step 2: Fetch VIX once ───────────────────────────────────────────────
    earliest_start = min(TICKER_CONFIG[t]["start"] for t in tickers)
    vix_start = earliest_start - timedelta(days=5)
    print(f"\nFetching VIX data ({vix_start} → {args.end}) ...")
    df_vix = fetch_vix_data(vix_start, args.end)
    if df_vix.empty:
        print("WARNING: no VIX data — VIX filters will be skipped.")

    # ── Step 3: Per-ticker sweeps ────────────────────────────────────────────
    for ticker in tickers:
        cfg            = TICKER_CONFIG[ticker]
        start          = cfg["start"]
        split_dates    = cfg["split_dates"]
        put_deltas     = cfg["put_deltas"]
        short_deltas   = cfg["short_deltas"]
        wing_widths    = cfg["wing_widths"]
        vix_thresholds = cfg["vix_thresholds"]

        print(f"\n{BAR}")
        print(f"  {ticker}  —  loading options from MySQL ...")
        print(BAR)

        fetch_end = args.end + timedelta(days=args.dte + args.dte_tol + 5)
        df_opts = fetch_options_cache(ticker, start, fetch_end)
        if df_opts.empty:
            print(f"  [{ticker}] no options data in cache — skipping.")
            continue
        print(f"  {len(df_opts):,} rows loaded.")

        # ── Short put sweep ───────────────────────────────────────────────
        if not args.no_puts:
            print(f"\nRunning short put sweep for {ticker}: deltas={put_deltas}")
            put_sweep = run_delta_sweep(
                df_opts=df_opts,
                df_vix=df_vix,
                delta_targets=put_deltas,
                vix_thresholds=vix_thresholds,
                dte_target=args.dte,
                dte_tol=args.dte_tol,
                entry_weekday=4,
                split_dates=split_dates,
                max_delta_err=0.08,
                max_spread_pct=args.spread,
                profit_take_pct=args.profit_take,
            )
            if not put_sweep.empty:
                put_sweep = put_sweep[put_sweep["entry_date"] <= args.end]

            if put_sweep.empty:
                print(f"  [{ticker}] no put trades found.")
            else:
                print_sweep_summary(
                    put_sweep, put_deltas, vix_thresholds,
                    dte_target=args.dte,
                    profit_take_pct=args.profit_take,
                    ticker=ticker,
                )
                if not args.no_csv:
                    fname = f"{ticker.lower()}_puts_{today_str}.csv"
                    put_sweep.to_csv(fname, index=False)
                    print(f"  Saved {len(put_sweep)} rows → {fname}")

        # ── Put spread sweep ──────────────────────────────────────────────
        if not args.no_spread:
            print(f"\nRunning put spread sweep for {ticker}:"
                  f" short_deltas={short_deltas} wing_widths={wing_widths}")
            spread_sweep = run_spread_delta_sweep(
                df_opts=df_opts,
                df_vix=df_vix,
                short_delta_targets=short_deltas,
                wing_delta_widths=wing_widths,
                vix_thresholds=vix_thresholds,
                dte_target=args.dte,
                dte_tol=args.dte_tol,
                entry_weekday=4,
                split_dates=split_dates,
                max_delta_err=0.08,
                max_spread_pct=args.spread,
                profit_take_pct=args.profit_take,
            )
            if not spread_sweep.empty:
                spread_sweep = spread_sweep[spread_sweep["entry_date"] <= args.end]

            if spread_sweep.empty:
                print(f"  [{ticker}] no spread trades found.")
            else:
                print_spread_sweep_summary(
                    spread_sweep, short_deltas, wing_widths, vix_thresholds,
                    dte_target=args.dte,
                    profit_take_pct=args.profit_take,
                    ticker=ticker,
                )
                if not args.no_csv:
                    fname = f"{ticker.lower()}_put_spreads_{today_str}.csv"
                    spread_sweep.to_csv(fname, index=False)
                    print(f"  Saved {len(spread_sweep)} rows → {fname}")

    print(f"\n{BAR}")
    print(f"  Batch complete: {', '.join(tickers)}")
    print(BAR)


if __name__ == "__main__":
    main()
