#!/usr/bin/env python3
"""
Pull for the "buy a QQQ LEAP call every time QQQ closes down >= 1%" test.

Stage 1 (entries): every trading day 2011 -> 2026-02, the QQQ call expiry nearest 450 DTE within 360-600,
  and in it the contracts nearest 0.50 / 0.70 / 0.80 delta (bid > 0). Taken on EVERY day, not just down
  days, so the study can compare the signal against buying on any day.
Stage 2 (paths): the full daily quote history (no bid filter) of every contract picked in stage 1, so an
  exit can be priced on any later date, including a zero bid.

Output: data/cache/qqq_dip_leap/entries.parquet, paths.parquet   (gitignored)

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_qqq_dip_leap_pull.py
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from lib.athena_lib import athena

OUT = Path("data/cache/qqq_dip_leap")


def entries_sql(y: int) -> str:
    return f"""
WITH c AS (
  SELECT trade_date, expiry, strike, bid, ask, delta, (bid_iv + ask_iv) / 2 AS iv, open_interest,
         date_diff('day', trade_date, expiry) AS dte
  FROM silver.options_daily_v3
  WHERE ticker = 'QQQ' AND cp = 'C' AND trade_date BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
    AND bid > 0 AND ask >= bid AND delta BETWEEN 0.35 AND 0.97
    AND date_diff('day', trade_date, expiry) BETWEEN 360 AND 600
),
e AS (
  SELECT trade_date, expiry, row_number() OVER (PARTITION BY trade_date ORDER BY abs(dte - 450), dte) AS rk
  FROM (SELECT DISTINCT trade_date, expiry, dte FROM c)
),
x AS (SELECT c.* FROM c JOIN e ON c.trade_date = e.trade_date AND c.expiry = e.expiry AND e.rk = 1),
y AS (
  SELECT x.*,
    row_number() OVER (PARTITION BY trade_date ORDER BY abs(delta - 0.50)) AS r50,
    row_number() OVER (PARTITION BY trade_date ORDER BY abs(delta - 0.70)) AS r70,
    row_number() OVER (PARTITION BY trade_date ORDER BY abs(delta - 0.80)) AS r80
  FROM x
)
SELECT trade_date, expiry, strike, bid, ask, delta, iv, open_interest, dte,
       r50 = 1 AS d50, r70 = 1 AS d70, r80 = 1 AS d80
FROM y WHERE r50 = 1 OR r70 = 1 OR r80 = 1
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ent_f = OUT / "entries.parquet"
    if ent_f.exists():
        ent = pd.read_parquet(ent_f)
    else:
        frames = []
        for y in range(2011, 2027):
            t0 = time.time()
            d = athena(entries_sql(y))
            print(f"entries {y}: {len(d):,} rows, {time.time()-t0:.0f}s", flush=True)
            frames.append(d)
        ent = pd.concat(frames, ignore_index=True)
        ent.to_parquet(ent_f, index=False)
    ent["expiry"] = pd.to_datetime(ent.expiry)
    contracts = ent[["expiry", "strike"]].drop_duplicates().sort_values(["expiry", "strike"])
    print(f"{len(ent):,} entry rows, {len(contracts):,} distinct contracts, {contracts.expiry.nunique()} expiries")

    paths = []
    exps = sorted(contracts.expiry.unique())
    for i in range(0, len(exps), 8):
        chunk = exps[i:i + 8]
        ors = " OR ".join(
            f"(expiry = DATE '{pd.Timestamp(e).date()}' AND strike IN "
            f"({','.join(repr(float(k)) for k in contracts[contracts.expiry == e].strike)}))"
            for e in chunk)
        t0 = time.time()
        d = athena(f"""SELECT trade_date, expiry, strike, bid, ask, delta
                       FROM silver.options_daily_v3
                       WHERE ticker = 'QQQ' AND cp = 'C' AND ({ors})""")
        print(f"paths expiries {i+1}-{i+len(chunk)} of {len(exps)}: {len(d):,} rows, {time.time()-t0:.0f}s", flush=True)
        paths.append(d)
    pd.concat(paths, ignore_index=True).to_parquet(OUT / "paths.parquet", index=False)
    print("done")


if __name__ == "__main__":
    main()
