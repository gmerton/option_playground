#!/usr/bin/env python3
"""
Stage-one screen for the "more like CF + XLE" idea (2026-09-17): measure the strike-breach rate DIRECTLY on
stock history before pulling any option chains (same logic as the VRP panel: measure the thing, don't simulate P&L).

The three entries (CF 9/1, XLE 8/31, XLE 9/3) shared one profile: a leader extended ~2-3 ADR above its 21 EMA,
above the 50/200-day, within ~7% of the 52-week high, with the SHORT PUT STRIKE AT THE 21 EMA, ~17 DTE, held to expiry.

Event  = ticker-day where ext21 (close vs 21 EMA, in ADR20 units) >= --min-ext, close > 50sma > 200sma,
         close within --max-off-high of the 252d high. One event per ticker per --gap trading days.
Strike = that day's 21 EMA. Horizon = --hold trading days (12 ~= 17 calendar).
Breach = close[t+hold] < strike.
Model  = lognormal P(close_T < K) using the name's own trailing RV20 (zero drift). Breach minus model is the
         quantity of interest: negative = the market's vol-scaled odds overstate the breach risk for this profile.
Control = same names, ALL days, a strike the same distance below spot in ADR units (distance-matched), so the
         comparison isolates the trend/extension state and not the cushion.

Overlap + cross-section: events cluster by date, so every SE is from weekly means (one observation per ISO week),
never a plain t-test across events.

Usage: .venv/bin/python3 run_ema_strike_breach.py [--min-ext 1.5] [--hold 12]
"""
import argparse
import numpy as np, pandas as pd
from math import sqrt
from scipy.stats import norm

ap = argparse.ArgumentParser()
ap.add_argument("--panel", default="data/cache/liquid_panel_2019.parquet")
ap.add_argument("--min-ext", type=float, default=1.5); ap.add_argument("--max-ext", type=float, default=4.0)
ap.add_argument("--max-off-high", type=float, default=0.08); ap.add_argument("--hold", type=int, default=12)
ap.add_argument("--gap", type=int, default=12); ap.add_argument("--min-adr", type=float, default=1.0)
a = ap.parse_args()

p = pd.read_parquet(a.panel).sort_values(["ticker", "date"])
g = p.groupby("ticker", sort=False)
p["ema21"] = g["close"].transform(lambda s: s.ewm(span=21, adjust=False).mean())
p["sma50"] = g["close"].transform(lambda s: s.rolling(50).mean())
p["sma200"] = g["close"].transform(lambda s: s.rolling(200).mean())
p["hi252"] = g["high"].transform(lambda s: s.rolling(252).max())
p["adr"] = (p["high"] / p["low"] - 1) * 100
p["adr20"] = g["adr"].transform(lambda s: s.rolling(20).mean())
p["ret"] = g["close"].transform(lambda s: np.log(s).diff())
p["rv20"] = g["ret"].transform(lambda s: s.rolling(20).std()) * sqrt(252)
p["ext21"] = (p["close"] / p["ema21"] - 1) * 100 / p["adr20"]
p["fwd"] = g["close"].shift(-a.hold)
p["fwd_low"] = g["low"].transform(lambda s: s[::-1].rolling(a.hold).min()[::-1].shift(-1))
p = p.dropna(subset=["sma200", "hi252", "adr20", "rv20", "fwd", "ext21"])
p = p[(p["adr20"] >= a.min_adr) & (p["rv20"] > 0.05)]
T = a.hold / 252


def model_p(spot, k, rv):
    return norm.cdf((np.log(k / spot) + 0.5 * rv ** 2 * T) / (rv * np.sqrt(T)))


def thin(df):  # one event per ticker per --gap trading days
    keep = []; last = {}
    for i, (t, n) in enumerate(zip(df["ticker"].values, df["n"].values)):
        if t not in last or n - last[t] >= a.gap:
            keep.append(i); last[t] = n
    return df.iloc[keep]


def weekly(df, col):
    w = df.groupby(df["date"].dt.to_period("W"))[col].mean()
    return w.mean(), w.std(ddof=1) / sqrt(len(w)), len(w)


p["n"] = p.groupby("ticker").cumcount()
trend = (p["close"] > p["sma50"]) & (p["sma50"] > p["sma200"]) & (p["close"] >= p["hi252"] * (1 - a.max_off_high))
ev = p[trend & p["ext21"].between(a.min_ext, a.max_ext)].copy()
ev["k"] = ev["ema21"]
ev = thin(ev)

ctl = p.copy()                                   # distance-matched control: same ADR cushion, any state
ctl = ctl[~(trend & (ctl["ext21"] >= a.min_ext))]
ctl["k"] = ctl["close"] * (1 - ev["ext21"].median() * ctl["adr20"] / 100 / (1 + ev["ext21"].median() * ctl["adr20"] / 100))
ctl = thin(ctl)

for name, d in (("EVENT  (extended leader, strike = 21 EMA)", ev), ("CONTROL (any state, same ADR cushion)", ctl)):
    d = d.copy()
    d["breach"] = (d["fwd"] < d["k"]).astype(float)
    d["touch"] = (d["fwd_low"] < d["k"]).astype(float)
    d["model"] = model_p(d["close"], d["k"], d["rv20"])
    d["edge"] = d["model"] - d["breach"]          # + = breaches LESS often than its own vol implies
    d["depth"] = np.where(d["breach"] == 1, (d["fwd"] / d["k"] - 1) * 100, np.nan)
    m, se, nw = weekly(d, "edge")
    print(f"\n=== {name}   n={len(d):,}  weeks={nw}  cushion {((d['close']/d['k']-1)*100).median():.1f}% = {d['ext21'].median() if 'EVENT' in name else ev['ext21'].median():.1f} ADR")
    print(f"  breach at T+{a.hold}: {d['breach'].mean()*100:5.1f}%   model (own RV20): {d['model'].mean()*100:5.1f}%   touched intraperiod: {d['touch'].mean()*100:5.1f}%")
    print(f"  edge (model - breach): {m*100:+5.2f}pp  weekly-SE {se*100:.2f}  t {m/se:+.2f}   median depth when breached {np.nanmedian(d['depth']):.1f}%")
    if "EVENT" in name:
        print("  by year:   year     n  breach  model   edge")
        for y, s in d.groupby(d["date"].dt.year):
            print(f"             {y}  {len(s):5d}  {s['breach'].mean()*100:5.1f}%  {s['model'].mean()*100:5.1f}%  {(s['model'].mean()-s['breach'].mean())*100:+5.1f}pp")
        print("  by extension (ADR over 21 EMA):")
        for lo, hi in ((1.5, 2.0), (2.0, 2.5), (2.5, 3.0), (3.0, 4.0)):
            s = d[d["ext21"].between(lo, hi)]
            if len(s) > 50:
                print(f"             {lo}-{hi}  n={len(s):5d}  breach {s['breach'].mean()*100:5.1f}%  model {s['model'].mean()*100:5.1f}%  edge {(s['model'].mean()-s['breach'].mean())*100:+5.1f}pp")
        ev_out = d
ev_out[["date", "ticker", "close", "k", "ext21", "adr20", "rv20", "breach", "model"]].to_csv("data/studies/ema_strike_breach_events.csv", index=False)
