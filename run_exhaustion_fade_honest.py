#!/usr/bin/env python3
"""
Tito archetype C (climactic-exhaustion fade), HONEST intraday version (2026-09-22, pre-registered here before
the first run).

Why: `scratch_fade_detector.py` + `scratch_fade_trigger.py` scored 17/17 on 2024, but the detector requires the
trade day to CLOSE in the bottom 20% of its range and below the open -- then the trigger shorts that same day.
That is selection on the outcome. Here every condition is knowable at the entry minute.

Universe/data: the Stage A 1-min cache (data/cache/intraday_1min, 183 names, 2026-02-02 ..), daily bars from the
liquid panel for the setup.
SETUP (known at the prior close): prior close >= +10% above its 10-day SMA.
ARMING (intraday, as it happens): the session trades above the prior 10-day high, and cumulative volume at that
minute >= 2.0 x (50-day avg daily volume x elapsed fraction of the 390-min session).
ENTRY: after arming, the first 1-min close below the running session VWAP, not before 09:45, not after 15:00.
STOP: a trade above the high-at-entry (the session high so far) -> exit at that high. After a stop, re-arm on the
next VWAP loss (up to 3 legs per day, same as the original). EXIT: final leg at the 16:00 close.
P&L: short, % of entry per leg, minus 5 bp per leg; day P&L = sum of legs (equal unit each).
CONTROLS: (post) same name-day, 5 random entry minutes 09:45-15:00 AFTER arming, same stop/re-entry/close rules;
(xname) 5 random other cached names at the same entry minute with their own session-high stop.
PRE-REGISTERED PASS: day mean > 0 with date-clustered t >= 2, beats BOTH controls (paired) with t >= 2, positive
in both halves (Feb-May vs Jun-Sep 2026). Anything smaller n than ~30 dates = UNDERPOWERED whatever the sign.

Usage: PYTHONPATH=src .venv/bin/python3 run_exhaustion_fade_honest.py
"""
from __future__ import annotations
import glob, os
from math import sqrt
import numpy as np, pandas as pd

COST = 0.0005; MAX_LEGS = 3; ARM_T = "09:45"; LAST_T = "15:00"
rng = np.random.default_rng(22)

raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
raw["date"] = pd.to_datetime(raw["date"])
C = raw.pivot(index="date", columns="ticker", values="close").sort_index()
H = raw.pivot(index="date", columns="ticker", values="high").sort_index()
Vd = raw.pivot(index="date", columns="ticker", values="volume").sort_index()
ext10 = (C / C.rolling(10).mean() - 1).shift(1)          # prior close vs its 10-SMA
hi10 = H.shift(1).rolling(10).max()                     # prior 10-day high
av50 = Vd.shift(1).rolling(50).mean()

files = sorted(glob.glob("data/cache/intraday_1min/*.parquet"))
by_day: dict[str, list[str]] = {}
for f in files:
    sym, day = os.path.basename(f)[:-8].rsplit("_", 1); by_day.setdefault(day, []).append(sym)


def load(sym, day):
    d = pd.read_parquet(f"data/cache/intraday_1min/{sym}_{day}.parquet")
    if not isinstance(d.index, pd.DatetimeIndex):
        if "time" in d.columns: d = d.set_index(pd.to_datetime(d["time"]))
        elif "timestamp" in d.columns: d = d.set_index(pd.to_datetime(d["timestamp"], unit="s", utc=True).tz_convert("America/New_York").tz_localize(None))
        else: return None
    d = d[(d.index.strftime("%H:%M") >= "09:30") & (d.index.strftime("%H:%M") <= "15:59")]
    if len(d) < 300: return None
    tp = (d.high + d.low + d.close) / 3
    d = d.assign(rvwap=(tp * d.volume).cumsum() / d.volume.cumsum().replace(0, np.nan), hm=d.index.strftime("%H:%M"),
                 cumv=d.volume.cumsum(), hhigh=d.high.cummax())
    return d.reset_index(drop=True)


def run_legs(d, first_i, entry_rule):
    """entry_rule(d, start) -> index of the next entry bar at/after start (or None). Returns day P&L % and legs."""
    legs, start, n = [], first_i, len(d)
    while len(legs) < MAX_LEGS:
        i = entry_rule(d, start)
        if i is None: break
        ent = d.close.iat[i]; hi = d.hhigh.iat[i]
        post = np.where(d.high.values[i + 1:] > hi)[0]
        if len(post):
            k = i + 1 + post[0]; legs.append((ent - hi) / ent - COST); start = k + 1
        else:
            legs.append((ent - d.close.iat[-1]) / ent - COST); break
    return (sum(legs) * 100 if legs else np.nan), len(legs)


def vwap_loss_rule(arm_i):
    def rule(d, start):
        for j in range(max(start, arm_i), len(d)):
            if d.hm.iat[j] < ARM_T: continue
            if d.hm.iat[j] > LAST_T: return None
            if d.close.iat[j] < d.rvwap.iat[j]: return j
        return None
    return rule


def fixed_rule(idx):
    used = {"done": False}
    def rule(d, start):
        if not used["done"]:
            used["done"] = True; return idx if idx >= start else None
        for j in range(start, len(d)):            # re-entries follow the signal's re-arm rule (next VWAP loss)
            if d.hm.iat[j] > LAST_T: return None
            if d.close.iat[j] < d.rvwap.iat[j]: return j
        return None
    return rule


rows, cand = [], 0
for day, syms in sorted(by_day.items()):
    dt = pd.Timestamp(day)
    if dt not in C.index: continue
    for sym in syms:
        if sym not in C.columns: continue
        e, h10, a50 = ext10.at[dt, sym], hi10.at[dt, sym], av50.at[dt, sym]
        if not (np.isfinite(e) and e >= 0.10 and np.isfinite(h10) and np.isfinite(a50) and a50 > 0): continue
        cand += 1
        d = load(sym, day)
        if d is None: continue
        frac = (np.arange(len(d)) + 1) / 390
        armed = np.where((d.high.values > h10) & (d.cumv.values >= 2.0 * a50 * frac))[0]
        if not len(armed): continue
        arm_i = int(armed[0])
        pnl, nl = run_legs(d, arm_i, vwap_loss_rule(arm_i))
        if not np.isfinite(pnl): continue
        first = vwap_loss_rule(arm_i)(d, arm_i)
        # post control: random minutes after arming
        okm = [j for j in range(arm_i, len(d)) if ARM_T <= d.hm.iat[j] <= LAST_T]
        post = [run_legs(d, arm_i, fixed_rule(int(j)))[0] for j in rng.choice(okm, size=min(5, len(okm)), replace=False)] if okm else []
        # xname control: other names, same entry minute, their own session-high stop
        others = [s for s in syms if s != sym]
        xs = []
        for s2 in rng.choice(others, size=min(5, len(others)), replace=False) if others else []:
            d2 = load(s2, day)
            if d2 is None or first >= len(d2): continue
            xs.append(run_legs(d2, 0, fixed_rule(int(first)))[0])
        rows.append(dict(date=dt, sym=sym, ext10=e, arm=d.hm.iat[arm_i], entry=d.hm.iat[first], legs=nl, pnl=pnl,
                         post=np.nanmean(post) if post else np.nan, xname=np.nanmean(xs) if xs else np.nan,
                         day_ret=(d.close.iat[-1] / d.open.iat[0] - 1) * 100))
R = pd.DataFrame(rows)
print(f"setup name-days (ext10 >= 10%): {cand} ; armed + traded: {len(R)} on {R.date.nunique() if len(R) else 0} dates")
if len(R):
    def ct(col):
        m = R.groupby("date")[col].mean().dropna(); return m.mean(), m.mean() / (m.std(ddof=1) / sqrt(len(m))) if len(m) > 2 else np.nan
    print(R.sort_values("date").to_string(index=False, float_format=lambda x: f"{x:+.2f}"))
    mu, t = ct("pnl"); R["e_post"] = R.pnl - R.post; R["e_x"] = R.pnl - R.xname
    mp, tp = ct("e_post"); mx, tx = ct("e_x")
    h1 = R[R.date < "2026-06-01"].pnl.mean(); h2 = R[R.date >= "2026-06-01"].pnl.mean()
    print(f"\nday P&L (short, net 5bp/leg): mean {R.pnl.mean():+.2f}%  median {R.pnl.median():+.2f}%  win {100*(R.pnl>0).mean():.0f}%  "
          f"date-clustered mean {mu:+.2f} t {t:+.2f}")
    print(f"vs post (random minute same name-day): control {R.post.mean():+.2f}%  edge {mp:+.2f} t {tp:+.2f}")
    print(f"vs xname (other names same minute):    control {R.xname.mean():+.2f}%  edge {mx:+.2f} t {tx:+.2f}")
    print(f"halves: Feb-May {h1:+.2f}%  Jun-Sep {h2:+.2f}%  | legs/day {R.legs.mean():.1f} | days that closed red: {100*(R.day_ret<0).mean():.0f}%")
    ok = t >= 2 and tp >= 2 and tx >= 2 and h1 > 0 and h2 > 0 and R.date.nunique() >= 30
    print("PRE-REGISTERED PASS:", "YES" if ok else ("UNDERPOWERED" if R.date.nunique() < 30 else "NO"))
    R.to_csv("data/studies/exhaustion_fade_honest_2026.csv", index=False)
