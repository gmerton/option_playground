#!/usr/bin/env python3
"""
Alert-funnel test (2026-09-17): does an intraday alert on a name that already passed layer 2 add anything over the
daily-close entry -- and does layer-2 membership sort alert outcomes at all?

Layer 2 (the pool with the measured edge): as of the PRIOR close, ADDV >= $50M, ADR20 4-7%, within 15% of the 52-week
high, 10>20>50 stacked (house slack). Alerts = the study's replayed long alerts (UR / ORB9 / LVL, 153 sessions
2026-02..09, cached scores with the alert price and stop), first alert per name-day.

Multi-day hold for BOTH entries (the validated management): stop judged on the daily close, exit on the first daily
close under the 20 EMA, 60-session cap.
  alert entry : buy at the alert price; stop = the alert's stop (session low); the entry day's close counts.
  close entry : buy at that day's close; stop = that day's low; checks start the next session.
R = (exit - entry) / (entry - stop); % = plain return. The alert's stop is tighter, so compare % as well as R.

Usage: PYTHONPATH=src .venv/bin/python3 run_alert_funnel_test.py
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
from lib.regime.trailing import Panel, liquidity_mask
from lib.commons.ma_stack import stack_run

warnings.filterwarnings("ignore")
raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet"); raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
raw = raw[raw.date >= "2024-06-01"]
p = Panel.from_long(raw); O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0)
e20 = C.ewm(span=20, adjust=False).mean(); adr = (H / L - 1).shift(1).rolling(20).mean() * 100
hi52 = H.shift(1).rolling(252, min_periods=120).max(); piv15 = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
run = stack_run(C, adr=adr)
state = elig & (adr >= 4) & (adr <= 7) & (C / hi52 - 1 > -0.15) & (run > 0)            # layer 2, evaluated at each close
pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
brk = (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15)   # the daily breakout event
idx = C.index; col = {t: i for i, t in enumerate(C.columns)}; Cv, Lv, E20 = C.values, L.values, e20.values


def hold(i, j, entry, stop, first_check):
    if not (np.isfinite(entry) and np.isfinite(stop)) or entry <= stop: return np.nan, np.nan, np.nan
    for k in range(first_check, min(i + 61, len(Cv))):
        c = Cv[k, j]
        if not np.isfinite(c): continue
        if c < stop or c < E20[k, j]: return (c - entry) / (entry - stop), c / entry - 1, k - i
    k = min(i + 60, len(Cv) - 1); return (Cv[k, j] - entry) / (entry - stop), Cv[k, j] / entry - 1, k - i


a = pd.read_csv("data/watchlist/logs/alert_study_scores.csv", parse_dates=["date"])
a = a[a["kind"].isin(["UR", "ORB9", "LVL"]) & a["px"].notna() & a["stop"].notna()].sort_values(["date", "sym", "t"]).drop_duplicates(["date", "sym"])
a = a[a["date"] <= idx[-1]]
rows = []
for r in a.itertuples():
    if r.sym not in col or r.date not in idx: continue
    i, j = idx.get_loc(r.date), col[r.sym]
    if i == 0: continue
    in_state = bool(state.values[i - 1, j]); is_brk = bool(brk.values[i, j]) if np.isfinite(Cv[i, j]) else False
    Ra, pa, ha = hold(i, j, r.px, r.stop, i)
    Rc, pc, hc = hold(i, j, Cv[i, j], Lv[i, j], i + 1)
    rows.append(dict(date=r.date, sym=r.sym, kind=r.kind, grade_shown=not r.out_of_play, in_state=in_state, brk=is_brk, px=r.px,
                     alert_risk=100 * (r.px / r.stop - 1), R_alert=Ra, pct_alert=100 * pa, R_close=Rc, pct_close=100 * pc, close_risk=100 * (Cv[i, j] / Lv[i, j] - 1),
                     intraday_R=r.R))
d = pd.DataFrame(rows).dropna(subset=["R_alert"])
print(f"{len(d):,} long alerts (first per name-day), {d['date'].nunique()} sessions {d['date'].min().date()}..{d['date'].max().date()} | in layer-2 state the prior close: {d['in_state'].sum():,} | of those on a daily-breakout day: {(d['in_state'] & d['brk']).sum():,}")


def line(x, lab):
    x = x.dropna(subset=["R_alert"]); m = x.groupby("date")["R_alert"].mean(); t = m.mean() / (m.std(ddof=1) / np.sqrt(len(m))) if len(m) > 2 else np.nan
    print(f"  {lab:<58} n={len(x):5d}  R {x['R_alert'].mean():+5.2f} (t_day {t:+4.1f})  win {100*(x['R_alert']>0).mean():3.0f}%  ret {x['pct_alert'].mean():+5.2f}%  median ret {x['pct_alert'].median():+5.2f}%  alert stop {x['alert_risk'].median():.1f}% away")


print("\n== Q1. does layer-2 membership sort alert outcomes on the multi-day hold? ==")
line(d, "all long alerts"); line(d[d["in_state"]], "in the layer-2 state"); line(d[~d["in_state"]], "NOT in the state")
line(d[d["in_state"] & d["grade_shown"]], "in state AND the monitor showed it (grade B/C)"); line(d[d["in_state"] & d["brk"]], "in state, on a daily-breakout day")
line(d[d["in_state"] & ~d["brk"]], "in state, NO daily breakout that day")
print("  by kind, in state:"); [line(g, f"    {k}") for k, g in d[d["in_state"]].groupby("kind")]

print("\n== Q2. same name-days, both in state with a daily breakout: alert entry vs the daily-close entry (paired) ==")
m = d[d["in_state"] & d["brk"]].dropna(subset=["R_close"])
pr = m["pct_alert"] - m["pct_close"]; byd = m.assign(diff=pr).groupby("date")["diff"].mean(); t = byd.mean() / (byd.std(ddof=1) / np.sqrt(len(byd)))
print(f"  n={len(m)}  alert entry: ret {m['pct_alert'].mean():+.2f}% (R {m['R_alert'].mean():+.2f}, stop {m['alert_risk'].median():.1f}% away)   close entry: ret {m['pct_close'].mean():+.2f}% (R {m['R_close'].mean():+.2f}, stop {m['close_risk'].median():.1f}% away)")
print(f"  paired difference (alert - close) {pr.mean():+.2f}% per trade, t_day {t:+.2f}; alert entry cheaper than the close on {100*(m['px'] < m['pct_close'].mul(0).add(1)).mean():.0f}% of days (placeholder)".replace(" (placeholder)", ""))
ent = 100 * (m["px"] / (m["px"] / (1 + m["pct_alert"] / 100) * (1 + m["pct_close"] / 100)) - 1)   # px vs close: (exit same) -> derive close from returns
print(f"  alert price vs that day's close: median {ent.median():+.2f}% (negative = the alert got in below the close)")
print("\n== Q3. the same alerts scored as day trades (the alert study's own R, hold to stop/close) vs the multi-day hold ==")
for lab, x in (("in state", d[d["in_state"]]), ("not in state", d[~d["in_state"]])):
    print(f"  {lab:<14} day-trade R {x['intraday_R'].mean():+.2f}   multi-day R {x['R_alert'].mean():+.2f}   multi-day ret {x['pct_alert'].mean():+.2f}%")
print("\n== by month, in-state alerts (multi-day) ==")
for mth, g in d[d["in_state"]].groupby(d["date"].dt.to_period("M")): print(f"  {mth}  n={len(g):4d}  R {g['R_alert'].mean():+.2f}  ret {g['pct_alert'].mean():+.2f}%  win {100*(g['R_alert']>0).mean():.0f}%")
d.to_csv("data/studies/alert_funnel_events.csv", index=False)

print("\n== CONTROL: every layer-2 name-day in the same 153 sessions, bought at the close (stop = day's low, same hold), alert day or not ==")
sess = sorted(d["date"].unique()); alert_days = set(zip(d.loc[d["in_state"], "date"], d.loc[d["in_state"], "sym"]))
ctl = []
for dt in sess:
    i = idx.get_loc(dt)
    for j in np.where(state.values[i - 1])[0]:
        Rc, pc, hc = hold(i, j, Cv[i, j], Lv[i, j], i + 1)
        if np.isfinite(pc): ctl.append(dict(date=dt, sym=C.columns[j], pct=100 * pc, alerted=(dt, C.columns[j]) in alert_days, brk=bool(brk.values[i, j]), up=bool(chg.values[i, j] > 0)))
ctl = pd.DataFrame(ctl)
def cl(x, lab):
    m = x.groupby("date")["pct"].mean(); t = m.mean() / (m.std(ddof=1) / np.sqrt(len(m)))
    print(f"  {lab:<50} n={len(x):6d}  ret {x['pct'].mean():+5.2f}%  (t_day {t:+4.1f})  median {x['pct'].median():+5.2f}%  win {100*(x['pct']>0).mean():.0f}%")
cl(ctl, "ALL layer-2 name-days, close entry"); cl(ctl[ctl["alerted"]], "  with a long alert that day"); cl(ctl[~ctl["alerted"]], "  with NO alert that day")
cl(ctl[ctl["brk"]], "  daily-breakout days"); cl(ctl[~ctl["brk"] & ctl["up"]], "  up day, no breakout"); cl(ctl[~ctl["up"]], "  down day")
print("  by month, all layer-2 name-days, close entry:"); [print(f"    {k}  n={len(g):5d}  ret {g['pct'].mean():+5.2f}%") for k, g in ctl.groupby(ctl["date"].dt.to_period("M"))]

print("\n== CONTROL 2: same as above but ONLY names the monitor was streaming (any alert kind, incl. shorts, within +-10 sessions) ==")
allk = pd.read_csv("data/watchlist/logs/alert_study_scores.csv", parse_dates=["date"])
watched = {}
for dt in sess:
    lo, hi = dt - pd.Timedelta(days=14), dt + pd.Timedelta(days=14)
    watched[dt] = set(allk.loc[(allk["date"] >= lo) & (allk["date"] <= hi), "sym"])
c2 = ctl[[s in watched[dt] for dt, s in zip(ctl["date"], ctl["sym"])]]
cl(c2, "layer-2 name-days on WATCHED names, close entry"); cl(c2[c2["alerted"]], "  with a long alert that day"); cl(c2[~c2["alerted"]], "  with NO long alert that day")
cl(c2[~c2["alerted"] & c2["up"]], "    no alert, up day"); cl(c2[~c2["alerted"] & ~c2["up"]], "    no alert, down day")
# does the alert's own entry beat the close on the same alerted name-days?
al = d[d["in_state"]].dropna(subset=["R_close"]); pr = al["pct_alert"] - al["pct_close"]; byd = al.assign(x=pr).groupby("date")["x"].mean()
print(f"  alerted name-days, alert-price entry vs same-day close entry: {al['pct_alert'].mean():+.2f}% vs {al['pct_close'].mean():+.2f}%  paired diff {pr.mean():+.2f}% (t_day {byd.mean()/(byd.std(ddof=1)/np.sqrt(len(byd))):+.2f}), n={len(al)}")
print("  by month, watched layer-2 names: alert day vs no-alert day (close entry):")
for k, g in c2.groupby(c2["date"].dt.to_period("M")):
    print(f"    {k}  alert n={int(g['alerted'].sum()):4d} ret {g.loc[g['alerted'],'pct'].mean():+6.2f}%   no-alert n={int((~g['alerted']).sum()):4d} ret {g.loc[~g['alerted'],'pct'].mean():+6.2f}%")

print("\n== CONTROL 3: the study's NO-HINDSIGHT control set only (universe_study_extra.txt: large caps picked blind, never streamed live) ==")
extra = {s.strip().upper() for s in open("data/watchlist/universe_study_extra.txt") if s.strip() and not s.startswith("#")}
c3 = ctl[ctl["sym"].isin(extra)]; a3 = d[d["in_state"] & d["sym"].isin(extra)]
cl(c3, "layer-2 name-days, control names, close entry"); cl(c3[c3["alerted"]], "  with a long alert that day"); cl(c3[~c3["alerted"]], "  with NO long alert that day")
if len(a3): print(f"  control-name alerts: alert-price entry {a3['pct_alert'].mean():+.2f}% vs same-day close {a3['pct_close'].mean():+.2f}%  n={len(a3)}")
cur = {s.strip().upper() for s in open("data/watchlist/universe_latest.txt") if s.strip() and not s.startswith("#")}
c4 = ctl[ctl["sym"].isin(cur)]; cl(c4, "layer-2 name-days, names on TODAY's curated universe (hindsight)")
