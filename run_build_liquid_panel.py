#!/usr/bin/env python3
"""
Build/refresh data/cache/liquid_panel_2019.parquet: yfinance adjusted daily OHLCV (2019-01 -> today)
for the liquid universe (names with 50d ADDV >= $30M and price >= $5 as of --asof on the Minervini
cache) plus SPY/QQQ/IWM/RSP. This is the long-history panel every validation script reads
(run_regime_validation.py, run_adhikary_validation.py, run_trade_lens.py fallback).

Survivorship: the universe is whoever is liquid on --asof. Re-run monthly; ~2 min.
Usage: PYTHONPATH=src python run_build_liquid_panel.py [--asof 2026-07-31] [--addv 30e6]
"""
import argparse, time, sys
import pandas as pd, yfinance as yf
from lib.minervini.scan import load_cache

ap = argparse.ArgumentParser(); ap.add_argument("--asof", default=None); ap.add_argument("--addv", type=float, default=30e6); ap.add_argument("--start", default="2019-01-01")
ap.add_argument("--out", default="data/cache/liquid_panel_2019.parquet"); a = ap.parse_args()
close, high, low, dolvol = load_cache("data/cache/minervini_matrix.parquet")
asof = pd.Timestamp(a.asof) if a.asof else close.index[-1]
addv = dolvol.loc[:asof].tail(50).mean(); px = close.loc[:asof].iloc[-1]
tickers = sorted(set(addv[(addv >= a.addv) & (px >= 5)].index) | {"SPY", "QQQ", "IWM", "RSP"})
print(f"universe as of {asof.date()}: {len(tickers)} names", flush=True)
frames = []; t0 = time.time()
for k in range(0, len(tickers), 100):
    ch = tickers[k:k + 100]; ymap = {t: t.replace(".", "-") for t in ch}
    for attempt in range(3):
        try:
            df = yf.download(list(ymap.values()), start=a.start, auto_adjust=True, threads=True, progress=False, group_by="ticker"); break
        except Exception as e:
            print("retry", k, e, flush=True); time.sleep(10)
    for t, y in ymap.items():
        if y not in df.columns.get_level_values(0): continue
        d = df[y].dropna(subset=["Close"]).rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].copy()
        if d.empty: continue
        d["ticker"] = t; d.index.name = "date"; frames.append(d.reset_index())
    print(f"{k + len(ch)}/{len(tickers)} {time.time() - t0:.0f}s", flush=True); time.sleep(1)
out = pd.concat(frames, ignore_index=True); out["dolvol"] = out.close * out.volume
out.to_parquet(a.out); print("wrote", a.out, out.ticker.nunique(), "names", out.date.min().date(), "->", out.date.max().date())
