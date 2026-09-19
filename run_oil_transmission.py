#!/usr/bin/env python3
"""
Oil transmission map: given a move in crude, what has historically happened to energy equities?

NOT a forecast of oil. The input is the thesis ("crude rises"); this answers the parts a thesis does not:
which vehicle, how much, with what lag, and -- the question that kills most thesis trades -- is it
already priced?

Method: daily, 2015 -> today (yfinance). Crude = CL=F front-month (USO as a tradeable proxy).
  1. beta/lag    regress each vehicle's daily return on crude's, and on crude lagged 1-3 sessions
  2. episodes    crude moves >= +10% over 20 sessions -> what each vehicle did over the SAME window,
                 and over the NEXT 20 sessions (the "am I late" question)
  3. dispersion  per-episode spread across vehicles, so the map shows what varies and what does not
  4. priced-in   within an episode, vehicle return vs crude return so far -- the ratio that says late

Usage: PYTHONPATH=src .venv/bin/python3 run_oil_transmission.py > data/studies/oil_transmission_2026-09-18.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd, yfinance as yf
warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

VEH = {"CL=F": "crude front", "USO": "USO (oil ETF)", "XLE": "XLE energy", "XOP": "XOP E&P",
       "OIH": "OIH services", "VDE": "VDE energy broad", "CRAK": "CRAK refiners", "XES": "XES equip",
       "AMLP": "AMLP midstream", "SPY": "SPY"}
px = yf.download(list(VEH), start="2015-01-01", end="2026-09-19", auto_adjust=True, progress=False)["Close"]
px.index = pd.to_datetime(px.index).tz_localize(None)
px = px.dropna(how="all").ffill(limit=2)
ret = px.pct_change()
oil = ret["CL=F"]

print("=== 1. daily beta to crude (2015-2026), and to crude lagged ===")
rows = {}
for s, lab in VEH.items():
    if s == "CL=F" or s not in ret:
        continue
    d = pd.concat([ret[s], oil, oil.shift(1), oil.shift(2)], axis=1).dropna()
    d.columns = ["y", "x0", "x1", "x2"]
    b0 = np.polyfit(d.x0, d.y, 1)[0]
    b1 = np.polyfit(d.x1, d.y, 1)[0]
    b2 = np.polyfit(d.x2, d.y, 1)[0]
    rows[lab] = dict(beta_same_day=b0, beta_lag1=b1, beta_lag2=b2, corr=d.y.corr(d.x0), n=len(d))
print(pd.DataFrame(rows).T.round(3).to_string())

print("\n=== 2. episodes: crude +10% or more over 20 sessions (non-overlapping) ===")
c20 = px["CL=F"] / px["CL=F"].shift(20) - 1
eps, last = [], None
for d, v in c20.dropna().items():
    if v >= 0.10 and (last is None or (d - last).days > 30):
        eps.append(d); last = d
print(f"{len(eps)} episodes: {', '.join(x.strftime('%Y-%m') for x in eps)}")
tab = {}
for s, lab in VEH.items():
    if s not in px:
        continue
    dur, nxt = [], []
    for d in eps:
        i = px.index.searchsorted(d)
        if i - 20 < 0 or i + 20 >= len(px):
            continue
        dur.append(100 * (px[s].iloc[i] / px[s].iloc[i - 20] - 1))
        nxt.append(100 * (px[s].iloc[i + 20] / px[s].iloc[i] - 1))
    tab[lab] = dict(during_mean=np.nanmean(dur), during_med=np.nanmedian(dur),
                    next20_mean=np.nanmean(nxt), next20_med=np.nanmedian(nxt),
                    next20_win=100 * np.nanmean(np.array(nxt) > 0), n=len(dur))
T = pd.DataFrame(tab).T
print(T.round(2).to_string())

print("\n=== 3. capture ratio: vehicle move / crude move during the episode (median) ===")
cap = {}
for s, lab in VEH.items():
    if s in ("CL=F",) or s not in px:
        continue
    r = []
    for d in eps:
        i = px.index.searchsorted(d)
        if i - 20 < 0:
            continue
        o = 100 * (px["CL=F"].iloc[i] / px["CL=F"].iloc[i - 20] - 1)
        v = 100 * (px[s].iloc[i] / px[s].iloc[i - 20] - 1)
        if o > 0:
            r.append(v / o)
    cap[lab] = dict(median_capture=np.nanmedian(r), p25=np.nanpercentile(r, 25), p75=np.nanpercentile(r, 75))
print(pd.DataFrame(cap).T.round(2).to_string())

print("\n=== 4. 'am I late?' next-20-session return, split by how much the vehicle already moved ===")
for s in ("XLE", "XOP"):
    rows = []
    for d in eps:
        i = px.index.searchsorted(d)
        if i - 20 < 0 or i + 20 >= len(px):
            continue
        already = 100 * (px[s].iloc[i] / px[s].iloc[i - 20] - 1)
        fwd = 100 * (px[s].iloc[i + 20] / px[s].iloc[i] - 1)
        rows.append((already, fwd))
    r = pd.DataFrame(rows, columns=["already", "fwd"])
    b = pd.cut(r.already, [-100, 0, 5, 10, 100])
    print(f"  {s}:")
    print("   " + r.groupby(b, observed=True).fwd.agg(["size", "mean", "median"]).round(2).to_string().replace("\n", "\n   "))

print("\n=== 5. today ===")
last = px.index[-1]
c20_now = 100 * (px["CL=F"].iloc[-1] / px["CL=F"].iloc[-21] - 1)
print(f"  as of {last.date()}: crude 20-session move {c20_now:+.1f}%")
for s, lab in VEH.items():
    if s in px:
        print(f"    {lab:20} 20d {100*(px[s].iloc[-1]/px[s].iloc[-21]-1):+6.1f}%   "
              f"5d {100*(px[s].iloc[-1]/px[s].iloc[-6]-1):+6.1f}%")
