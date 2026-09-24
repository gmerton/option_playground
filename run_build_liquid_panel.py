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
out = pd.concat(frames, ignore_index=True)
out["date"] = pd.to_datetime(out.date).dt.tz_localize(None) if getattr(pd.to_datetime(out.date).dt, "tz", None) else pd.to_datetime(out.date)


def drop_open_session(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance returns today's IN-PROGRESS bar during market hours; a panel close must be a real close."""
    from zoneinfo import ZoneInfo
    from datetime import datetime
    now = datetime.now(ZoneInfo("America/New_York"))
    today = pd.Timestamp(now.date())
    if (df.date == today).any() and now.hour * 60 + now.minute < 16 * 60 + 30:
        print(f"dropped today's in-progress bar ({today.date()}, run at {now:%H:%M} ET)")
        return df[df.date != today]
    return df


def fill_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance's batch download can silently omit a whole session for most names (2026-09-22: 181 of 1,726 present,
    and a re-download did not fix it). Every rolling feature downstream (ADR20, the MA stack) goes NaN for 20
    sessions, so the scans quietly lose ~85% of the universe. Detect short sessions and fill the missing names from
    Polygon's grouped-daily file, scaled onto the panel's adjusted basis by each name's close ratio on the nearest
    complete session (Polygon adjusts for splits only; yfinance also for dividends)."""
    import os, requests
    n = df.groupby("date").ticker.nunique()
    med = n.rolling(21, center=True, min_periods=5).median()
    short = n[n < 0.9 * med].index
    short = short[short >= n.index.max() - pd.Timedelta(days=400)]            # older holes are history, not today's job
    if not len(short):
        print("gap check: no short sessions"); return df
    key = os.environ.get("POLYGON_API_KEY")
    if not key:
        print(f"WARN gap check: {len(short)} short session(s) {[str(d.date()) for d in short]} and no POLYGON_API_KEY -- NOT filled")
        return df

    def grouped(d: pd.Timestamp) -> pd.DataFrame:
        j = requests.get(f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{d.date()}",
                         params={"adjusted": "true", "apiKey": key}, timeout=60).json()
        g = pd.DataFrame(j.get("results") or [])
        if g.empty:
            return g
        g = g.rename(columns={"T": "ticker", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
        g["ticker"] = g.ticker.str.replace("-", ".", regex=False)
        return g[["ticker", "open", "high", "low", "close", "volume"]]

    sessions = n.index.sort_values(); names = set(df.ticker)
    adds, unfilled = [], []
    for d in short:
        have = set(df.loc[df.date == d, "ticker"]); need = names - have
        g = grouped(d)
        k = sessions.get_loc(d)
        ref = next((s for s in list(sessions[k + 1:k + 4]) + list(sessions[max(0, k - 3):k][::-1]) if s not in short), None)
        if g.empty or ref is None:
            unfilled.append(str(d.date())); continue
        gr = grouped(ref).set_index("ticker").close
        pc = df[df.date == ref].set_index("ticker").close
        f = (pc / gr).dropna()
        x = g[g.ticker.isin(need) & g.ticker.isin(f.index)].copy()
        for c in ("open", "high", "low", "close"):
            x[c] = x[c] * x.ticker.map(f)
        x["date"] = d
        adds.append(x)
        print(f"gap check: {d.date()} had {len(have)} of {len(names)} names; filled {len(x)} from Polygon "
              f"(basis ref {ref.date()}, max basis adj {100 * (f - 1).abs().max():.2f}%); still missing {len(need) - len(x)}")
    if unfilled:
        print(f"WARN gap check: could not fill {unfilled}")
    return pd.concat([df] + adds, ignore_index=True).sort_values(["ticker", "date"]).reset_index(drop=True)


out = fill_gaps(drop_open_session(out))
out["dolvol"] = out.close * out.volume
out.to_parquet(a.out); print("wrote", a.out, out.ticker.nunique(), "names", out.date.min().date(), "->", out.date.max().date())
