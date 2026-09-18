#!/usr/bin/env python3
"""
Daily OHLCV + split history for the BCI CSP test (pool + SPY), 2017 -> 2026-04, from yfinance.

yfinance Close with auto_adjust=False is split-adjusted but not dividend-adjusted. Option strikes are RAW
(as traded), so run_bci_csp_study.py converts back: raw = close x product of split ratios dated after the day.
Output: data/cache/bci_csp/prices.parquet (long: date, ticker, open/high/low/close/volume, raw_close)
"""
import pandas as pd, yfinance as yf

pool = [l.strip() for l in open("data/watchlist/straddle_pool_323.txt") if l.strip()] + ["SPY"]
px = yf.download(pool, start="2017-01-01", end="2026-04-15", auto_adjust=False, progress=False, threads=True, group_by="column")
px.index = pd.to_datetime(px.index).tz_localize(None)
long = px[["Open", "High", "Low", "Close", "Volume"]].stack(level=1, future_stack=True).reset_index()
long.columns = ["date", "ticker", "open", "high", "low", "close", "volume"]
long = long.dropna(subset=["close"])
fac = []
for t in long.ticker.unique():
    try:
        s = yf.Ticker(t).splits
    except Exception:
        s = pd.Series(dtype=float)
    s.index = pd.to_datetime(s.index).tz_localize(None) if len(s) else s.index
    d = long.loc[long.ticker == t, ["date"]].copy()
    d["factor"] = [float(s[s.index > x].prod()) if len(s) else 1.0 for x in d.date]
    fac.append(d.assign(ticker=t))
long = long.merge(pd.concat(fac), on=["ticker", "date"])
long["raw_close"] = long.close * long.factor
long.to_parquet("data/cache/bci_csp/prices.parquet", index=False)
print(long.shape, long.ticker.nunique(), "tickers; with splits:", int((long.groupby("ticker").factor.max() != 1).sum()))
