#!/usr/bin/env python3
"""
Build (or refresh) the fwd_vol_daily Glue table from options_daily_v3.

Computes ATM put implied volatility at ~30 DTE and ~90 DTE for a list of
tickers, then derives the 30→90 forward volatility ratio (fvr_put_30_90).

Output schema (Glue table: silver.fwd_vol_daily)
------------------------------------------------
  trade_date    date    -- observation date
  ticker        string  -- equity ticker        ┐ partition cols
  year          int     -- derived from date    ┘
  iv_put_30     double  -- annualized IV of ATM put ~30 DTE
  iv_put_90     double  -- annualized IV of ATM put ~90 DTE
  fvr_put_30_90 double  -- σ_fwd(30→90) / iv_put_30

Naming convention
-----------------
  iv_{method}_{dte}           → iv_put_30, iv_put_90
  fvr_{method}_{near}_{far}   → fvr_put_30_90
  Future methods: iv_straddle_30, iv_vix_30, etc.

Usage
-----
  # Full backfill, S&P 100 stocks (2018–today):
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_fwd_vol.py --mode full

  # Incremental (only dates after last record in table):
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_fwd_vol.py

  # Specific tickers:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_fwd_vol.py --tickers SPY QQQ TLT

  # Specific date range:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_fwd_vol.py \\
      --mode full --start 2024-01-01 --end 2024-12-31 --tickers SPY

Requires: AWS_PROFILE=clarinut-gmerton
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Optional

import pandas as pd
import awswrangler as wr

from lib.studies.fwd_vol_study import (
    FWD_VOL_DB,
    FWD_VOL_TABLE,
    compute_all_fvr,
    fetch_atm_puts_all,
    write_fwd_vol,
)

# ── Default ticker universe — S&P 100 individual stocks (no ETFs/indices) ─────
# Composition as of 2026. Add/remove as index changes.

SP100_TICKERS: list[str] = [
    # Mega-cap tech
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AVGO", "ORCL", "CRM",
    # Large tech
    "ADBE", "AMD",  "CSCO", "IBM",  "INTU", "INTC", "QCOM", "AMAT", "ADI",  "NOW",
    # Financials
    "JPM",  "BAC",  "WFC",  "GS",   "MS",   "V",    "MA",   "AXP",  "BX",   "SCHW",
    "SPGI", "CME",  "MCO",  "CB",   "PGR",  "MMC",  "ADP",
    # Healthcare
    "LLY",  "UNH",  "JNJ",  "ABBV", "MRK",  "TMO",  "ABT",  "AMGN", "BMY",  "GILD",
    "MDT",  "SYK",  "ISRG", "REGN", "VRTX", "BDX",  "CI",   "ELV",  "HCA",  "ZTS",
    # Consumer discretionary
    "COST", "HD",   "WMT",  "DIS",  "SBUX", "LOW",  "TGT",  "NKE",  "BKNG", "MCD",
    # Consumer staples
    "KO",   "PEP",  "PM",   "MO",   "CL",   "PG",
    # Industrials
    "CAT",  "GE",   "RTX",  "UPS",  "DE",   "GD",   "ETN",  "HON",  "MMM",  "TT",
    "APH",  "BA",
    # Energy
    "XOM",  "CVX",  "EOG",
    # Utilities / Telecom
    "NEE",  "SO",   "DUK",  "VZ",   "T",
    # Real estate
    "PLD",
    # Other large-cap
    "ACN",  "BSX",  "MU",   "KLAC", "PANW", "NFLX", "TXN",  "F",
]

DEFAULT_START = date(2018, 1, 1)
BATCH_SIZE    = 10  # tickers per Athena query (stocks are more uniform than ETFs)


# ── Incremental helper ───────────────────────────────────────────────────────

def _get_table_max_date() -> Optional[date]:
    """Return the latest trade_date in silver.fwd_vol_daily, or None."""
    try:
        df = wr.athena.read_sql_query(
            sql=f'SELECT MAX(trade_date) AS max_td FROM "{FWD_VOL_DB}"."{FWD_VOL_TABLE}"',
            database=FWD_VOL_DB,
            workgroup="dev-v3",
            s3_output="s3://athena-919061006621/",
        )
        val = df.iloc[0, 0] if not df.empty else None
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return pd.to_datetime(val).date()
    except Exception:
        return None


# ── Main run loop ─────────────────────────────────────────────────────────────

def run(
    tickers: list[str],
    start: date,
    end: date,
    batch_size: int = BATCH_SIZE,
    write_mode: str = "append",
) -> int:
    """Process tickers in batches; return total rows written."""
    total_rows = 0

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(tickers) + batch_size - 1) // batch_size
        print(f"\n[batch {batch_num}/{total_batches}] {batch}  ({start} → {end})")

        raw = fetch_atm_puts_all(batch, start, end)
        if raw.empty:
            print("  → no data returned (tickers may lack 90-DTE options in this window)")
            continue
        n_with_10 = raw["dte_10"].notna().sum()
        print(f"  → {len(raw):,} raw (ticker, date) pairs  "
              f"({n_with_10:,} with 10-DTE leg, {len(raw)-n_with_10:,} monthly-only)")

        out = compute_all_fvr(raw)
        if out.empty:
            print("  → no valid IV solutions computed")
            continue
        skipped = len(raw) - len(out)
        print(f"  → {len(out):,} rows computed  ({skipped} skipped — IV solve failed)")

        write_fwd_vol(out, mode=write_mode)
        total_rows += len(out)

    return total_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build/refresh silver.fwd_vol_daily (30→90d forward vol ratios)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tickers", nargs="+", default=None,
        help="Tickers to process (default: SP100_TICKERS)",
    )
    parser.add_argument(
        "--ticker-file", type=str, default=None,
        help="Path to a file with one ticker per line (overrides --tickers and default list)",
    )
    parser.add_argument(
        "--start", type=str, default=None,
        help="Start date YYYY-MM-DD (default: 2018-01-01 for full; table max+1d for incremental)",
    )
    parser.add_argument(
        "--end", type=str, default=None,
        help="End date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--mode", choices=["full", "incremental"], default="incremental",
        help=(
            "full = backfill from --start (overwrites matching partitions); "
            "incremental = only dates after table max_date (default)"
        ),
    )
    parser.add_argument(
        "--batch-size", type=int, default=BATCH_SIZE,
        help=f"Tickers per Athena query (default: {BATCH_SIZE})",
    )
    args = parser.parse_args()

    if args.ticker_file:
        with open(args.ticker_file) as f:
            tickers = [line.strip() for line in f if line.strip()]
    else:
        tickers = args.tickers or SP100_TICKERS
    end     = date.fromisoformat(args.end) if args.end else date.today()

    if args.mode == "incremental" and args.start is None:
        max_date = _get_table_max_date()
        if max_date is not None:
            start = max_date + timedelta(days=1)
            print(f"[incremental] resuming from {start}  (table max_date = {max_date})")
        else:
            start = DEFAULT_START
            print(f"[incremental] table empty/missing — full backfill from {start}")
    else:
        start = date.fromisoformat(args.start) if args.start else DEFAULT_START

    if start > end:
        print(f"Nothing to do: start {start} > end {end}")
        return

    write_mode = "overwrite_partitions" if args.mode == "full" else "append"

    print(f"\nForward vol build")
    print(f"  tickers   : {tickers}")
    print(f"  date range: {start} → {end}")
    print(f"  mode      : {args.mode}  (write_mode={write_mode})")
    print(f"  batch size: {args.batch_size}")

    total = run(tickers, start, end, batch_size=args.batch_size, write_mode=write_mode)
    print(f"\nDone. Total rows written: {total:,}")


if __name__ == "__main__":
    main()
