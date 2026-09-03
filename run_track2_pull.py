#!/usr/bin/env python3
"""
Track 2 data pull: ~10 DTE ATM straddles on the 140-ticker approved list,
joined to iv_put_10 / iv_put_30 / fvr_put_30_90 from silver.fwd_vol_daily.

Output: track2_straddle_data.csv  (does NOT overwrite long_straddle_fvr_data.csv,
which the oquants reconciliation write-up references).

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_track2_pull.py
"""
from __future__ import annotations
from datetime import date
import pandas as pd

from run_fvr_straddle_regression import (
    BATCH_SIZE, DEFAULT_START, DTE_TARGET, DTE_TOL,
    fetch_straddle_batch, load_fvr,
)

OUT = "track2_straddle_data.csv"
TICKER_FILE = "data/watchlist/long_straddle_approved.txt"


def main() -> None:
    tickers = [l.strip().upper() for l in open(TICKER_FILE) if l.strip()]
    start, end = DEFAULT_START, date.today()
    print(f"Track 2 pull — {len(tickers)} approved tickers, {start} -> {end}")
    print(f"  entry Friday ~{DTE_TARGET} DTE (+/-{DTE_TOL}), ATM straddle, hold to expiry")

    frames = []
    nb = (len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(tickers), BATCH_SIZE):
        b = tickers[i:i + BATCH_SIZE]
        print(f"[batch {i//BATCH_SIZE+1}/{nb}] {b[0]}...{b[-1]}", end="  ", flush=True)
        sdf = fetch_straddle_batch(b, start, end)
        if sdf.empty:
            print("-> 0")
            continue
        fdf = load_fvr(b, start, end)
        m = sdf.merge(fdf.rename(columns={"trade_date": "entry_date"}),
                      on=["ticker", "entry_date"], how="inner")
        m = m.dropna(subset=["payout", "fvr_put_30_90"])
        m = m[m["entry_premium"] > 0]
        # long-side return, floored at -100%
        m["ret_pct_long"] = (m["payout"] - m["entry_premium"]) / m["entry_premium"] * 100
        print(f"-> {len(sdf):,} straddles, {len(m):,} matched")
        if len(m):
            frames.append(m)

    if not frames:
        print("no data")
        return
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(OUT, index=False)
    print(f"\n{len(df):,} rows, {df.ticker.nunique()} tickers, "
          f"{df.entry_date.min()} -> {df.entry_date.max()}")
    print(f"  mean ret {df.ret_pct_long.mean():+.2f}%  median {df.ret_pct_long.median():+.2f}%  "
          f"win {(df.ret_pct_long>0).mean()*100:.1f}%")
    print(f"  iv_put_10 present on {df.iv_put_10.notna().mean()*100:.0f}% of rows")
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
