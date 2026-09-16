#!/usr/bin/env python3
"""
Pull the option slice needed for the momentum-skew vertical test (oquants strategy #3, 2026-09-16).

What the trade needs, and why the slice is small: the spread is HELD TO EXPIRY, so a vertical settles at
intrinsic from the underlying close and no daily path is required. We only need, per ticker-day:
  * the strikes that can form the legs (45-60 delta long, 10-25 delta short) and the skew signal (ATM, 25 delta),
    i.e. |delta| 0.08..0.62 on 7..21 DTE, with a real two-sided quote;
  * a spot on the SAME basis as the strikes -- v3 strikes are UNADJUSTED for splits, so spot is recovered from
    put-call parity inside this same slice, never from an adjusted price feed.

⚠ Erratum rules (calendar_path_study.md): a delta filter is safe HERE only because nothing is looked up after
entry -- settlement comes from the underlying, not from a chain row. Do not copy this filter into a path sim.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_skew_vertical_pull.py [--years 2019 2026]
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path
import pandas as pd
from lib.athena_lib import athena
from lib.constants import S3TABLES_CATALOG, DB, TABLE

OUT = Path("data/cache/skew_vertical"); OUT.mkdir(parents=True, exist_ok=True)
DTE_LO, DTE_HI = 7, 21
D_LO, D_HI = 0.08, 0.62
END = "2026-02-28"          # v3 loses bid/ask in March 2026


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--years", nargs=2, type=int, default=[2019, 2026])
    ap.add_argument("--universe", default=str(OUT / "universe.txt")); a = ap.parse_args()
    tickers = [l.strip().upper() for l in open(a.universe) if l.strip()]
    tsql = ",".join(f"'{t}'" for t in tickers)
    print(f"{len(tickers)} tickers, {a.years[0]}..{a.years[1]}, DTE {DTE_LO}-{DTE_HI}, |delta| {D_LO}-{D_HI}", flush=True)
    for yr in range(a.years[0], a.years[1] + 1):
        out = OUT / f"skew_{yr}.parquet"
        if out.exists():
            print(f"{yr}: exists, skip", flush=True); continue
        lo, hi = f"{yr}-01-01", min(f"{yr}-12-31", END)
        if lo > END:
            break
        t0 = time.time()
        d = athena(f"""
            SELECT ticker, trade_date, expiry, cp, strike, bid, ask, delta, bid_iv, ask_iv, open_interest, volume
            FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}"
            WHERE ticker IN ({tsql})
              AND trade_date BETWEEN DATE '{lo}' AND DATE '{hi}'
              AND date_diff('day', trade_date, expiry) BETWEEN {DTE_LO} AND {DTE_HI}
              AND abs(delta) BETWEEN {D_LO} AND {D_HI}
              AND bid > 0 AND ask > 0 AND bid_iv > 0 AND ask_iv > 0""")
        d.to_parquet(out, index=False)
        print(f"{yr}: {len(d):,} rows, {d.ticker.nunique()} tickers, {time.time()-t0:.0f}s", flush=True)
    print("DONE", flush=True); return 0


if __name__ == "__main__":
    sys.exit(main())
