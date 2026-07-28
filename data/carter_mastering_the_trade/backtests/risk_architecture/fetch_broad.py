#!/usr/bin/env python3
"""
Fetch ~20y of daily OHLC for the liquid subset of the Minervini cache universe.

WHY: the cache itself (`data/cache/minervini_matrix.parquet`) is a 295-bar ROLLING window
built for the nightly screen — 2025-05-19 to 2026-07-22. SMA200 alone consumes 200 of those
bars and the backtest needs a 250-day forward window, so the cache supplies the UNIVERSE LIST
but cannot supply the history. It also stores no `open` column at all.

Universe: cache names with median daily dollar volume >= $3M and last price >= $5 (~2,684).
The $3M floor sits comfortably below the scorecard's own $10M 5-day gate, so it does not bind
the tiers being tested — it just removes names that could never be traded.

⚠ SURVIVORSHIP, unchanged and now larger in absolute terms: this is the universe that EXISTS
today. Names delisted between 2006 and 2026 are absent. Fixing it needs a delisting-inclusive
source (Polygon has one; the key here is free-tier rate limited). The bias inflates all entry
tiers, and hits long-hold/high-momentum tiers hardest.

Writes chunked parquets to broad_history/ (float32, one file per 100 tickers) so neither this
script nor the consumer has to hold the whole panel in memory.
"""
from __future__ import annotations

import os
import sys
import warnings

import pandas as pd
import yfinance as yf

sys.path.insert(0, "src")
from lib.minervini.scan import load_cache  # noqa: E402

warnings.filterwarnings("ignore")

OUT_DIR = "data/carter_mastering_the_trade/backtests/risk_architecture/broad_history"
CACHE = "data/cache/minervini_matrix.parquet"
START, END = "2006-01-01", "2026-07-24"
CHUNK = 100
MIN_DOLVOL, MIN_PRICE = 3e6, 5.0


def universe() -> list[str]:
    close, _, _, dolvol = load_cache(CACHE)
    last = close.ffill().iloc[-1]
    med = dolvol.median()
    keep = (med >= MIN_DOLVOL) & (last >= MIN_PRICE)
    return sorted(keep[keep].index.tolist())


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    tickers = universe()
    print(f"universe: {len(tickers)} names (median dolvol >= ${MIN_DOLVOL/1e6:.0f}M, "
          f"price >= ${MIN_PRICE:.0f})", flush=True)

    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i:i + CHUNK]
        path = f"{OUT_DIR}/part_{i:05d}.parquet"
        if os.path.exists(path):
            print(f"  [{i:5}] cached, skipping", flush=True)
            continue
        df = yf.download(chunk, start=START, end=END, auto_adjust=True,
                         progress=False, threads=True, group_by="column")
        if df is None or df.empty:
            print(f"  [{i:5}] EMPTY", flush=True)
            continue
        frames = []
        for col in ("Open", "High", "Low", "Close", "Volume"):
            if col not in df.columns.get_level_values(0):
                continue
            s = df[col].stack(dropna=True).rename(col.lower())
            frames.append(s)
        if not frames:
            continue
        out = pd.concat(frames, axis=1).reset_index()
        out.columns = ["date", "ticker"] + list(out.columns[2:])
        out = out.dropna(subset=["open", "close"])
        for c in ("open", "high", "low", "close"):
            out[c] = out[c].astype("float32")
        out["volume"] = out["volume"].astype("float32")
        out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None)
        out.to_parquet(path, index=False)
        print(f"  [{i:5}] {len(chunk):3} tickers -> {len(out):>9,} rows  "
              f"({out.ticker.nunique()} with data)", flush=True)

    parts = sorted(f for f in os.listdir(OUT_DIR) if f.endswith(".parquet"))
    print(f"\ndone: {len(parts)} part files in {OUT_DIR}")


if __name__ == "__main__":
    main()
