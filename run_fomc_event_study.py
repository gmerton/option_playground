#!/usr/bin/env python3
"""
Tito archetype D on scheduled macro: buy ahead of the event, sell into the run-up. 55 FOMC decisions,
2019-10 -> 2026-09 (data/fomc_dates.json).

Pre-registered:
  index      SPY and QQQ: mean return over T-5..T0, the decision day itself, T0..T+5, and the
             "archetype D" trade = buy at the T-k close, sell at the T0 close (k = 1,2,3,5).
  names      same archetype-D trade on high-beta panel names (ADR >= 4, liquid) -- his TSLA/PLTR shape.
  control    the SAME holding length starting on a random non-event session in the same month, same names.
  stats      t clustered by event; both halves (2019-22 / 2023-26) must agree.
Costs 5 bps per side. Unscheduled 2020 meetings reported separately -- they are not tradeable ex ante.

Usage: PYTHONPATH=src .venv/bin/python3 run_fomc_event_study.py > data/studies/fomc_event_study_2026-09-18.log
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd, yfinance as yf
from lib.regime.trailing import Panel, liquidity_mask
warnings.filterwarnings("ignore"); pd.set_option("display.width", 210)
COST, RNG = 0.0005, np.random.default_rng(20260918)

ev = json.load(open("data/fomc_dates.json"))
FOMC = pd.to_datetime(ev["scheduled"]); UNS = pd.to_datetime(ev["unscheduled"])

ix = yf.download(["SPY", "QQQ"], start="2019-09-01", end="2026-09-19", auto_adjust=True, progress=False)["Close"]
ix.index = pd.to_datetime(ix.index).tz_localize(None)
print("=== INDEX: mean % return around the 55 scheduled FOMC decisions ===")
rows = {}
for sym in ("SPY", "QQQ"):
    s = ix[sym].dropna(); idx = s.index
    r = {}
    for lab, a, b in (("T-5 -> T0", -5, 0), ("T-3 -> T0", -3, 0), ("T-1 -> T0", -1, 0),
                      ("decision day", -1, 0), ("T0 -> T+1", 0, 1), ("T0 -> T+5", 0, 5), ("T-5 -> T+5", -5, 5)):
        vals = []
        for d in FOMC:
            p = idx.searchsorted(d)
            if p + b >= len(idx) or p + a < 0 or idx[p] != d:
                continue
            vals.append(100 * (s.iloc[p + b] / s.iloc[p + a] - 1))
        r[lab] = dict(n=len(vals), mean=np.mean(vals), win=100 * np.mean(np.array(vals) > 0),
                      t=np.mean(vals) / np.std(vals, ddof=1) * np.sqrt(len(vals)))
    rows[sym] = pd.DataFrame(r).T
    print(f"\n{sym}:"); print(rows[sym].round(3).to_string())

# archetype D on high-beta names: buy T-k close, sell T0 close, vs the same holding length on random sessions
raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
p = Panel.from_long(raw); C = p.close
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
adr = (C * 0).add((p.high / p.low - 1).shift(1).rolling(20).mean() * 100, fill_value=0)
hot = elig & (adr >= 4)
idx = C.index
print("\n=== ARCHETYPE D on high-beta names (ADR>=4): buy T-k close -> sell decision-day close ===")
out = {}
for k in (1, 2, 3, 5):
    ev_r, ctl_r, ev_dates = [], [], []
    for d in FOMC:
        p0 = idx.searchsorted(d)
        if p0 >= len(idx) or idx[p0] != d or p0 - k < 0:
            continue
        cols = np.flatnonzero(hot.values[p0 - k])
        if not len(cols):
            continue
        ret = (C.values[p0, cols] * (1 - COST)) / (C.values[p0 - k, cols] * (1 + COST)) - 1
        ev_r.append(100 * np.nanmean(ret)); ev_dates.append(d)
        month = np.flatnonzero((idx.year == d.year) & (idx.month == d.month))
        cand = [x for x in month if abs(x - p0) > k and x - k >= 0 and x < len(idx)]
        for x in RNG.choice(cand, size=min(5, len(cand)), replace=False) if cand else []:
            x = int(x)
            cr = (C.values[x, cols] * (1 - COST)) / (C.values[x - k, cols] * (1 + COST)) - 1
            ctl_r.append(100 * np.nanmean(cr))
    e, c = np.array(ev_r), np.array(ctl_r)
    h = pd.Series(e, index=pd.to_datetime(ev_dates))
    out[f"buy T-{k}"] = dict(events=len(e), mean=e.mean(), win=100 * (e > 0).mean(),
                             t=e.mean() / e.std(ddof=1) * np.sqrt(len(e)), control=c.mean(), edge=e.mean() - c.mean(),
                             h1=h[h.index < "2023-01-01"].mean(), h2=h[h.index >= "2023-01-01"].mean())
print(pd.DataFrame(out).T.round(3).to_string())

print("\n=== the two UNSCHEDULED 2020 meetings (not tradeable ex ante, shown for context) ===")
for sym in ("SPY", "QQQ"):
    s = ix[sym].dropna(); i2 = s.index
    for d in UNS:
        q = i2.searchsorted(d)
        if q + 5 < len(i2):
            print(f"  {sym} {d.date()}: day {100*(s.iloc[q]/s.iloc[q-1]-1):+.2f}%  T0->T+5 {100*(s.iloc[q+5]/s.iloc[q]-1):+.2f}%")
