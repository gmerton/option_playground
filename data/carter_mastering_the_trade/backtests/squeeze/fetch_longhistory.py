#!/usr/bin/env python3
"""
Fetch ~20y of daily bars for a liquid universe, for the Squeeze regime-decay test.

Universe = the 300 most liquid names in the Minervini cache TODAY. That is survivorship-
and selection-biased (they are liquid now, and many were not in 2006). The bias is largely
neutralized by the design: every result is reported as signal-minus-BASELINE where the
baseline is the same universe over the same dates, so a universe-wide upward bias cancels.
It would still distort absolute returns, so absolute numbers are not the deliverable.

Writes longhistory.parquet (long format: date, ticker, open/high/low/close/volume).
"""
from __future__ import annotations

import warnings

import pandas as pd
import yfinance as yf

from lib.minervini.scan import load_cache

warnings.filterwarnings("ignore")
OUT = "data/carter_mastering_the_trade/backtests/squeeze/longhistory.parquet"
N = 300
START, END = "2006-01-01", "2026-07-25"


def main() -> None:
    close, high, low, dolvol = load_cache("data/cache/minervini_matrix.parquet")
    addv = dolvol.rolling(50, min_periods=50).mean().iloc[-1].dropna()
    universe = sorted(addv.sort_values(ascending=False).head(N).index.tolist())
    print(f"universe: {len(universe)} names, e.g. {universe[:10]}")

    frames = []
    for i in range(0, len(universe), 60):
        chunk = universe[i:i + 60]
        print(f"  downloading {i}-{i+len(chunk)} ...", flush=True)
        df = yf.download(chunk, start=START, end=END, auto_adjust=True,
                         progress=False, threads=True, group_by="column")
        if df is None or df.empty:
            continue
        for field in ("Open", "High", "Low", "Close", "Volume"):
            if field not in df.columns.get_level_values(0):
                continue
            sub = df[field].stack().rename(field.lower()).reset_index()
            sub.columns = ["date", "ticker", field.lower()]
            frames.append(sub.set_index(["date", "ticker"]))
    wide = pd.concat(frames, axis=0).groupby(level=[0, 1]).first()
    out = wide.reset_index()
    out.to_parquet(OUT, index=False)
    print(f"\nwrote {OUT}: {len(out):,} rows, "
          f"{out['ticker'].nunique()} tickers, {out['date'].min()} -> {out['date'].max()}")


if __name__ == "__main__":
    main()
