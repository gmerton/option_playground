#!/usr/bin/env python3
"""Pull the full SPY option chain (puts AND calls, DTE 0-70) from silver.options_daily_v3, 2010-01 -> 2026-03-31,
for the leg-return surface (run_spy_leg_surface.py, 2026-09-28). One Athena query per year, written per year to
data/cache/spy_chain_v3/<year>.parquet (float32) so the 8 GB laptop never holds more than one year.
Scope (2026-09-28): ~12.2M rows total; bid/ask coverage ends ~Mar 2026 so the window stops there.
SPY has never split, so the raw v3 strikes are directly comparable to the SPY close.
Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_spy_chain_v3_pull.py [--force]
"""
import sys
from pathlib import Path

import pandas as pd

from lib.athena_lib import athena

OUT = Path("data/cache/spy_chain_v3")
SQL = """
SELECT trade_date, expiry, CAST(strike AS DOUBLE) AS strike, upper(substr(cp, 1, 1)) AS cp,
       CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask,
       CAST(bid_iv AS DOUBLE) AS bid_iv, CAST(ask_iv AS DOUBLE) AS ask_iv, CAST(delta AS DOUBLE) AS delta,
       open_interest AS oi, volume
FROM silver.options_daily_v3
WHERE ticker = 'SPY'
  AND trade_date BETWEEN DATE '{a}' AND DATE '{b}'
  AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 70
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    force = "--force" in sys.argv
    total = 0
    for y in range(2010, 2027):
        f = OUT / f"{y}.parquet"
        if f.exists() and not force:
            n = len(pd.read_parquet(f, columns=["strike"]))
            print(f"  {y}: cached {n:,}"); total += n; continue
        a, b = f"{y}-01-01", (f"{y}-12-31" if y < 2026 else "2026-03-31")
        df = athena(SQL.format(a=a, b=b))
        df["trade_date"] = pd.to_datetime(df.trade_date); df["expiry"] = pd.to_datetime(df.expiry)
        for c in ("strike", "bid", "ask", "bid_iv", "ask_iv", "delta"):
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32")
        for c in ("oi", "volume"):
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32")
        dup = int(df.duplicated(["trade_date", "expiry", "strike", "cp"]).sum())
        df.to_parquet(f, index=False)
        total += len(df)
        print(f"  {y}: {len(df):,} rows, dup keys {dup}", flush=True)
    print(f"total {total:,} rows -> {OUT}/")


if __name__ == "__main__":
    main()
