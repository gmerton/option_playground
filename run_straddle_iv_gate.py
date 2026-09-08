#!/usr/bin/env python3
"""
Long-straddle playbook gate 3 (IV percentile <= 30), rebuilt live from option PRINTS.

silver.fwd_vol_daily stopped on 2026-02-20 and options_daily_v3 carries no bid/ask/greeks after
mid-July 2026, so iv_put_10 cannot be read from the tables. This pulls 6-14 DTE puts with volume>0
from v3, inverts Black-Scholes against the yfinance close, takes the median per day (>=2 prints),
and ranks the latest level against the ticker's own trailing 252 days.

Usage (pairs with run_straddle_fvr_scan.py --universe data/watchlist/straddle_pool_323.txt):
  AWS_PROFILE=... PYTHONPATH=src python run_straddle_iv_gate.py --tickers GAP,KGC,QBTS [--out csv]
  AWS_PROFILE=... PYTHONPATH=src python run_straddle_iv_gate.py --from-scan data/watchlist/straddle_scan_latest.txt
"""
import argparse, re, warnings
import numpy as np, pandas as pd, yfinance as yf
from math import log, sqrt, exp
from scipy.stats import norm
from scipy.optimize import brentq
from lib.athena_lib import athena
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser(); ap.add_argument("--tickers", default=None); ap.add_argument("--from-scan", default=None); ap.add_argument("--min-fvr", type=float, default=1.20); ap.add_argument("--out", default=None); a = ap.parse_args()
if a.from_scan:
    txt = open(a.from_scan).read(); tk = [m[0] for m in re.findall(r"^(\S+)\s+\S+\s+[\d.]+\s+[\d.]+%\s+[\d.]+%\s+([\d.]+)\s+(FULL|half)", txt, re.M) if float(m[1]) >= a.min_fvr]
else:
    tk = a.tickers.split(",")
raw = yf.download(tk, start="2025-06-01", auto_adjust=False, threads=True, progress=False, group_by="ticker")
spot = {t: (raw[t]["Close"].dropna() if t in raw.columns.get_level_values(0) else None) for t in tk}
inl = ",".join(f"'{t}'" for t in tk)
q = athena(f"""SELECT ticker, trade_date, expiry, strike, last, volume FROM silver.options_daily_v3
WHERE ticker IN ({inl}) AND cp='P' AND trade_date >= date_add('day', -400, current_date) AND date_diff('day', trade_date, expiry) BETWEEN 6 AND 14 AND last>0 AND last<9999 AND volume>0""")
q["trade_date"] = pd.to_datetime(q.trade_date); q["expiry"] = pd.to_datetime(q.expiry); r = 0.04
def bs_put(S, K, T, s):
    d1 = (log(S / K) + (r + s * s / 2) * T) / (s * sqrt(T)); d2 = d1 - s * sqrt(T); return K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
def iv(p, S, K, T):
    try: return brentq(lambda s: bs_put(S, K, T, s) - p, 0.03, 5, xtol=1e-4)
    except Exception: return np.nan
rows = []
for t, g in q.groupby("ticker"):
    sp = spot.get(t)
    if sp is None: rows.append(dict(ticker=t, note="no spot")); continue
    g = g.join(sp.rename("S"), on="trade_date").dropna(subset=["S"]); g = g[(g.strike / g.S).between(0.95, 1.05)]; g["T"] = (g.expiry - g.trade_date).dt.days / 365
    g["iv"] = [iv(p, S, K, T) for p, S, K, T in zip(g["last"], g.S, g.strike, g["T"])]
    daily = g.dropna(subset=["iv"]).groupby("trade_date").agg(iv=("iv", "median"), n=("iv", "size")); daily = daily[daily.n >= 2]
    if len(daily) < 60: rows.append(dict(ticker=t, n_days=len(daily), note="insufficient history")); continue
    last = daily.iloc[-1]; hist = daily.iv.iloc[:-1].tail(252)
    rows.append(dict(ticker=t, last_date=daily.index[-1].date(), n_days=len(hist), iv_7_14d=round(100 * last.iv, 1), pctile=round(100 * (hist < last.iv).mean()), p30_level=round(100 * hist.quantile(.3), 1), passes_gate3=bool((hist < last.iv).mean() <= 0.30)))
out = pd.DataFrame(rows); print(out.to_string(index=False))
if a.out: out.to_csv(a.out, index=False)
