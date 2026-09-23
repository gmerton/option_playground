#!/usr/bin/env python3
"""
Stage 1 for the poor-man's-covered-call test: pull mega-cap call chains out to ~100 DTE.

⚠ `options_cache` (MySQL) cannot serve this — it caps at **DTE 65** and the PMCC's long leg is ~90 DTE.
v3 it is. Calls only; DTE 0-100 so the settlement day is included; delta 0.02-0.98 so a contract's whole
path survives (a deep-ITM long and a dying short both need to stay in the pull).

Universe = the mega-caps Galarnyk actually recommends, which is close to our own measured tradeable set
(`vrp_shortdte_names`: "liquidity is the gate, tradeable set = SPY + NVDA/AMZN/AAPL/V").

⚠ v3 is the RAW table: dedupe on (ticker, expiry, strike, trade_date) after loading, and never take spot
from a price panel — v3 strikes are unadjusted while every panel we keep is split-adjusted (median 3.1%
mismatch, a whole split factor for a name that split in-sample). `bid_iv`/`ask_iv` are pulled so that
`lib.studies.chain_spot.spot_from_chain()` can recover the RAW spot from the chain itself, which is what
every settlement here uses.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 -u pull_pmcc_chains.py
"""
from __future__ import annotations

import pathlib
import time

import pandas as pd

from lib.athena_lib import athena
from lib import constants as K

OUT = pathlib.Path("/private/tmp/claude-501/-Users-gmerton-v2-options-playground/"
                   "0dc56bae-9a64-43e3-9215-162f5d8a0c59/scratchpad/pmcc")
TICKERS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META",
           "TSLA", "V", "MA", "COST", "HD", "WMT", "AVGO", "JPM", "UNH", "JNJ"]
YEARS = range(2019, 2027)
NEEDED = {"trade_date", "ticker", "strike", "expiry", "bid", "ask", "last", "delta", "bid_iv", "ask_iv"}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tk = "','".join(TICKERS)
    for y in YEARS:
        f = OUT / f"calls_{y}.parquet"
        if f.exists():
            # ⚠ Check the SCHEMA, not just existence. A first pass of this script omitted bid_iv/ask_iv;
            # the plain exists() guard then silently kept those files when the query was fixed, which
            # would have handed spot_from_chain() NaN IV for 2019-2020 and settled those trades on
            # garbage spot. Re-pull any year whose columns do not match what we now ask for.
            have = set(pd.read_parquet(f, columns=None).columns) if f.stat().st_size else set()
            if NEEDED <= have:
                print(f"  {y}: have {f.name} ({f.stat().st_size/1e6:.0f} MB) — skip", flush=True)
                continue
            print(f"  {y}: {f.name} missing {sorted(NEEDED - have)} — re-pulling", flush=True)
        q = f"""
        SELECT trade_date, ticker, strike, expiry, bid, ask, last, delta, bid_iv, ask_iv
        FROM "{K.S3TABLES_CATALOG}"."{K.DB}"."{K.TABLE}"
        WHERE year(trade_date) = {y}
          AND cp = 'C'
          AND ticker IN ('{tk}')
          AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 100
          AND delta BETWEEN 0.02 AND 0.98
        """
        t0 = time.time()
        try:
            d = athena(q)
        except Exception as e:
            print(f"  {y}: ERROR {type(e).__name__}: {str(e)[:180]}", flush=True)
            continue
        d.to_parquet(f, index=False)
        print(f"  {y}: {len(d):>10,} rows, {d.ticker.nunique():>2} names, {time.time()-t0:>5.0f}s "
              f"-> {f.name} ({f.stat().st_size/1e6:.0f} MB)", flush=True)
    got = sorted(OUT.glob("calls_*.parquet"))
    print(f"\ndone: {len(got)} files, {sum(p.stat().st_size for p in got)/1e9:.2f} GB")


if __name__ == "__main__":
    main()
