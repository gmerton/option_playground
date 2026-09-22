#!/usr/bin/env python3
"""
Build `data/cache/gex/<TICKER>_short_expiry_quotes.parquet` — the near-expiry quote cache the
1-day GEX studies read (run_gex_spy_straddle / _ironfly / _condor, run_weekend_premium).

⚠ This builder did not exist in the repo: the SPY cache was produced by an uncommitted ad-hoc pull
(the same data-integrity gap TEST_INDEX §10 #1 flags for the ETF bull-put roster). Committed here so
every ticker's cache is reproducible. Schema matches the existing SPY file exactly:

    trade_date, expiry, strike, cp, bid, ask, delta        DTE 1-4, one row per contract-day

Usage:
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_gex_quotes_pull.py --ticker QQQ
    ... --ticker SPY --start 2010 --end 2026        # reproduce the existing cache

⚠ v3 coverage: greeks/IV top out ~2026-05 and bid/ask go NULL from mid-July 2026
([[reference_options_daily_v3]]), so --end beyond 2026-02 returns progressively less.
"""
from __future__ import annotations

import argparse
import pathlib

import pandas as pd

from lib.athena_lib import athena

OUT = pathlib.Path("data/cache/gex")
SQL = """
SELECT trade_date, expiry, strike, cp,
       CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask, CAST(delta AS DOUBLE) AS delta
FROM silver.options_daily_v3
WHERE ticker = '{tk}'
  AND trade_date BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
  AND date_diff('day', trade_date, expiry) BETWEEN 1 AND 4
  AND bid IS NOT NULL AND ask IS NOT NULL
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="QQQ")
    ap.add_argument("--start", type=int, default=2010)
    ap.add_argument("--end", type=int, default=2026)
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    frames = []
    for y in range(a.start, a.end + 1):
        df = athena(SQL.format(tk=a.ticker, y=y))
        print(f"  [{a.ticker} {y}] {len(df):,} rows")
        if len(df):
            frames.append(df)
    if not frames:
        raise SystemExit(f"no rows for {a.ticker}")

    q = pd.concat(frames, ignore_index=True)
    q["trade_date"] = pd.to_datetime(q.trade_date)
    q["expiry"] = pd.to_datetime(q.expiry)
    q["cp"] = q.cp.astype(str).str.upper().str[0]
    path = OUT / f"{a.ticker}_short_expiry_quotes.parquet"
    q.to_parquet(path, index=False)
    print(f"\n{len(q):,} rows -> {path}")
    print(f"  {q.trade_date.min().date()} -> {q.trade_date.max().date()}")
    print("  DTE mix:", (q.expiry - q.trade_date).dt.days.value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
