#!/usr/bin/env python3
"""
Step 2 of the long-call project (2026-09-16): pull the expiry x strike grid.

Calls at |delta| 0.18-0.72 (the 0.20-0.70 grid plus tolerance) and the near-ATM puts needed to recover a
put-call-parity spot on the SAME unadjusted basis as the strikes -- never an adjusted price feed. DTE 0-50 so
expiry-day rows are present for settlement. 2018 -> 2026-02-28 (v3 loses bid/ask in March 2026).

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_call_grid_pull.py
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path
import pandas as pd
from lib.athena_lib import athena
from lib.constants import S3TABLES_CATALOG, DB, TABLE

OUT = Path("data/cache/call_grid"); OUT.mkdir(parents=True, exist_ok=True)
END = "2026-02-28"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--years", nargs=2, type=int, default=[2018, 2026])
    ap.add_argument("--universe", default="data/watchlist/straddle_pool_323.txt"); a = ap.parse_args()
    ts = [l.strip().upper() for l in open(a.universe) if l.strip()]
    tsql = ",".join(f"'{t}'" for t in ts)
    print(f"{len(ts)} tickers, {a.years[0]}..{a.years[1]}, DTE 0-50, calls .18-.72 + ATM puts for parity", flush=True)
    for yr in range(a.years[0], a.years[1] + 1):
        out = OUT / f"grid_{yr}.parquet"
        if out.exists():
            print(f"{yr}: exists, skip", flush=True); continue
        lo, hi = f"{yr}-01-01", min(f"{yr}-12-31", END)
        if lo > END: break
        t0 = time.time()
        d = athena(f"""
            SELECT ticker, trade_date, expiry, cp, strike, bid, ask, delta, bid_iv, ask_iv, open_interest, volume
            FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}"
            WHERE ticker IN ({tsql})
              AND trade_date BETWEEN DATE '{lo}' AND DATE '{hi}'
              AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 50
              AND bid > 0 AND ask > 0
              AND ((cp = 'C' AND delta BETWEEN 0.18 AND 0.72)
                OR (cp = 'P' AND delta BETWEEN -0.72 AND -0.28))""")
        d.to_parquet(out, index=False)
        print(f"{yr}: {len(d):,} rows, {d.ticker.nunique()} tickers, {time.time() - t0:.0f}s", flush=True)
    print("DONE", flush=True); return 0


if __name__ == "__main__":
    sys.exit(main())
