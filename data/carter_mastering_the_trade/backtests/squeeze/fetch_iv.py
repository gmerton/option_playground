#!/usr/bin/env python3
"""
Pull ~30d ATM implied vol for the Squeeze universe from Athena silver.options_daily_v3.

ATM 30d IV proxy = mean of (bid_iv+ask_iv)/2 over CALL contracts with
delta in [0.45, 0.55] and DTE in [25, 35], per (ticker, trade_date).

Pulled for EVERY date (not just signal dates) so the same frame supplies both the
signal and the baseline. Chunked by year to keep result sets manageable.

Writes iv30.parquet: ticker, trade_date, iv30, n_contracts
"""
from __future__ import annotations

import pandas as pd

from lib.athena_lib import athena
from lib.minervini.scan import load_cache

OUT = "data/carter_mastering_the_trade/backtests/squeeze/iv30.parquet"
SRC = "data/carter_mastering_the_trade/backtests/squeeze/longhistory.parquet"
YEARS = range(2010, 2027)


def main() -> None:
    tickers = sorted(pd.read_parquet(SRC)["ticker"].unique().tolist())
    tlist = ",".join(f"'{t}'" for t in tickers)
    print(f"{len(tickers)} tickers, {YEARS.start}-{YEARS.stop - 1}")

    frames = []
    for y in YEARS:
        q = f"""
        SELECT ticker, trade_date,
               avg((bid_iv+ask_iv)/2.0) AS iv30,
               count(*) AS n_contracts
        FROM silver.options_daily_v3
        WHERE ticker IN ({tlist})
          AND trade_date BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
          AND cp = 'C'
          AND bid_iv IS NOT NULL AND ask_iv IS NOT NULL
          AND bid_iv > 0 AND ask_iv > 0
          AND delta BETWEEN 0.45 AND 0.55
          AND date_diff('day', trade_date, expiry) BETWEEN 25 AND 35
        GROUP BY ticker, trade_date
        """
        df = athena(q)
        print(f"  {y}: {len(df):,} ticker-days", flush=True)
        frames.append(df)

    out = pd.concat(frames, ignore_index=True)
    out["trade_date"] = pd.to_datetime(out["trade_date"])
    out.to_parquet(OUT, index=False)
    print(f"\nwrote {OUT}: {len(out):,} rows, {out['ticker'].nunique()} tickers, "
          f"{out['trade_date'].min().date()} -> {out['trade_date'].max().date()}")


if __name__ == "__main__":
    main()
