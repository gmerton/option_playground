#!/usr/bin/env python3
"""
Fetch daily bars for the index-ETF opening-gap study (Carter, Mastering the Trade, ch. 7).

Instruments: SPY / QQQ / IWM / DIA — the tradeable proxies for the futures Carter fades
(ES / NQ / TF / YM). Cash indexes are avoided on purpose: the ^GSPC "open" is a stale
composite of staggered constituent opens, which would corrupt the single most important
number in this study.

auto_adjust=False is REQUIRED. Dividend back-adjustment rescales history and shrinks the
measured ex-dividend gap; but the ex-div gap-down really happened in the tape and really
was tradeable. Raw (split-adjusted, div-unadjusted) OHLC is the correct series for gaps.

Also pulls ^VIX for regime slicing.

Writes gapdata.parquet (long: date, ticker, open/high/low/close/volume) and vix.parquet.
"""
from __future__ import annotations

import warnings

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

HERE = "data/carter_mastering_the_trade/backtests/opening_gap"
OUT = f"{HERE}/gapdata.parquet"
VIX_OUT = f"{HERE}/vix.parquet"

TICKERS = ["SPY", "QQQ", "IWM", "DIA"]
START, END = "1993-01-01", "2026-07-26"


def _flatten(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1)
    df = df.rename(columns=str.lower).reset_index()
    df = df.rename(columns={"Date": "date", "index": "date"})
    df["ticker"] = ticker
    keep = ["date", "ticker", "open", "high", "low", "close", "volume"]
    return df[[c for c in keep if c in df.columns]]


def main() -> None:
    frames = []
    for t in TICKERS:
        print(f"  downloading {t} ...", flush=True)
        df = yf.download(t, start=START, end=END, auto_adjust=False,
                         progress=False, threads=False)
        if df is None or df.empty:
            print(f"    !! no data for {t}")
            continue
        frames.append(_flatten(df, t))

    out = pd.concat(frames, ignore_index=True).dropna(subset=["open", "close"])
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None)
    out = out.sort_values(["ticker", "date"]).reset_index(drop=True)
    out.to_parquet(OUT, index=False)
    print(f"\nwrote {OUT}: {len(out):,} rows")
    for t, g in out.groupby("ticker"):
        print(f"  {t}: {len(g):,} bars  {g.date.min().date()} -> {g.date.max().date()}")

    print("\n  downloading ^VIX ...", flush=True)
    vix = yf.download("^VIX", start=START, end=END, auto_adjust=False,
                      progress=False, threads=False)
    vix = _flatten(vix, "VIX")[["date", "close"]].rename(columns={"close": "vix"})
    vix["date"] = pd.to_datetime(vix["date"]).dt.tz_localize(None)
    vix.to_parquet(VIX_OUT, index=False)
    print(f"wrote {VIX_OUT}: {len(vix):,} rows  "
          f"{vix.date.min().date()} -> {vix.date.max().date()}")


if __name__ == "__main__":
    main()
