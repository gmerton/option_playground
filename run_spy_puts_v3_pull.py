#!/usr/bin/env python3
"""Pull SPY PUTS from silver.options_daily_v3 for the tail-overlay test [WL-5f] (2026-09-23).

Why a new pull: data/cache/SPY_options.parquet (the MySQL options_cache subset) was empty, and a MySQL refetch needs
~13 GB RAM (this machine has 8). v3 is also the more complete source (options_cache drops zero-bid quotes).
Scope: puts only, trade_date 2018-01 -> 2026-04, DTE 0-35 (the 20-DTE bucket spreads + their exit paths and the
same-expiry 5-delta overlay) and 50-70 (the 60-DTE 3-delta overlay arm). One Athena query per year (~6 s each).
Schema matches what lib.studies.put_spread_study expects from the options cache.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_spy_puts_v3_pull.py
"""
import pandas as pd
from lib.athena_lib import athena

OUT = "data/cache/SPY_puts_v3_2018_2026.parquet"
SQL = """
SELECT trade_date, expiry, strike, cp,
       CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask, CAST(delta AS DOUBLE) AS delta
FROM silver.options_daily_v3
WHERE ticker = 'SPY'
  AND trade_date BETWEEN DATE '{a}' AND DATE '{b}'
  AND upper(substr(cp, 1, 1)) = 'P'
  AND (date_diff('day', trade_date, expiry) BETWEEN 0 AND 35 OR date_diff('day', trade_date, expiry) BETWEEN 50 AND 70)
"""
frames = []
for y in range(2018, 2027):
    a, b = f"{y}-01-01", (f"{y}-12-31" if y < 2026 else "2026-04-30")
    df = athena(SQL.format(a=a, b=b))
    print(f"  [SPY puts {y}] {len(df):,} rows", flush=True)
    frames.append(df)
q = pd.concat(frames, ignore_index=True)
q["trade_date"] = pd.to_datetime(q.trade_date); q["expiry"] = pd.to_datetime(q.expiry)
q["cp"] = "P"
q = q.sort_values(["trade_date", "expiry", "strike"]).reset_index(drop=True)
q.to_parquet(OUT, index=False)
print(f"{len(q):,} rows -> {OUT}; {q.trade_date.min().date()} -> {q.trade_date.max().date()}")
print("dups on (trade_date, expiry, strike):", int(q.duplicated(["trade_date", "expiry", "strike"]).sum()))
