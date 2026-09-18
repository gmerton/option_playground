#!/usr/bin/env python3
"""
ENTRY STUDY (2026-09-17, parked earlier tonight, run after the stop-distance finding). Question: can a tight intraday
stop be made to work the way Luk / Qullamaggie run it -- enter at the trigger near the intraday low, exit the moment
the level breaks, RE-ENTER on the next trigger -- rather than the way every test so far judged it (single shot,
stop checked on the daily close)?

Universe: layer-2 names (ADDV >= $50M, ADR 4-7, within 15% of the 52wk high, stacked w/ house slack, as of the prior
close) among the 183 names with 1-min bars in data/cache/intraday_1min (Feb 2 - Sep 11 2026 = the alert study's
universe: curated list = HINDSIGHT, plus universe_study_extra.txt = blind control set). Both reported.

Entries, all on the same name-days:
  CLOSE   buy the close; stop = the day's low; managed on daily closes from the next session (house baseline).
  ORB15   first 1-min close above the 15-min opening-range high, 09:46-12:00; stop = OR low.
  RECLAIM flush >= 0.25 ADR below max(open, prior close) then the first 1-min close back above VWAP, 09:40-12:00;
          stop = the session low at entry.
Execution variants for ORB15 / RECLAIM:
  close-judged   no intraday exit; the stop is checked on daily closes (entry day included) -- how the earlier tests did it.
  intraday       exit at the first 1-min close below the stop the same day; if still long at the close, from the next
                 session on manage on daily closes with the stop raised to the entry day's session low (house).
  intraday+re    same, plus re-entry on the next trigger the same day (ORB: 1-min close back above the OR high;
                 RECLAIM: another VWAP reclaim), max 2 re-entries; the name-day's result = the sum of its trades.
Costs: 0.05% slippage per side + 0.01% commission per side, charged on every entry and exit (re-entries pay again).
Multi-day exit for everything: first daily close under the stop or under the 20 EMA, 60-session cap.
Metrics per name-day: % return, R on the INITIAL stop, share stopped on the entry day, return per 1% initially risked.
SEs cluster by date. Usage: PYTHONPATH=src .venv/bin/python3 run_entry_study.py
"""
from __future__ import annotations
import os, warnings
from math import sqrt
import numpy as np, pandas as pd
from lib.regime.trailing import Panel, liquidity_mask
from lib.commons.ma_stack import stack_run

warnings.filterwarnings("ignore")
CACHE = "data/cache/intraday_1min"; SLIP = 0.0005 + 0.0001
syms = sorted({f.split("_")[0] for f in os.listdir(CACHE) if f.endswith(".parquet")})
extra = {s.strip().upper() for s in open("data/watchlist/universe_study_extra.txt") if s.strip() and not s.startswith("#")}
raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet"); raw = raw[raw.ticker.isin(syms)]; raw = raw[raw.date >= "2025-01-01"]
p = Panel.from_long(raw); O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0)
e20 = C.ewm(span=20, adjust=False).mean(); adr = (H / L - 1).shift(1).rolling(20).mean() * 100
hi52 = H.shift(1).rolling(252, min_periods=120).max(); run = stack_run(C, adr=adr)
state = (elig & (adr >= 4) & (adr <= 7) & (C / hi52 - 1 > -0.15) & (run > 0)).shift(1).fillna(False).astype(bool)
idx = C.index; Cv, Lv, E20 = C.values, L.values, e20.values; col = {t: i for i, t in enumerate(C.columns)}


def daily_hold(i, j, entry, stop, first_check):
    """Daily-close management from session first_check: exit on close < stop or close < 20 EMA, 60-session cap. Returns exit px."""
    for k in range(first_check, min(i + 61, len(Cv))):
        c = Cv[k, j]
        if np.isfinite(c) and (c < stop or c < E20[k, j]): return c
    return Cv[min(i + 60, len(Cv) - 1), j]


def trade(entry, exit_px, stop):
    e, x = entry * (1 + SLIP), exit_px * (1 - SLIP)
    return 100 * (x / e - 1), (x - e) / (entry - stop)


def simulate(bars, i, j, kind, execution, day_adr):
    """One name-day. Returns dict(pct, R, stopped_intraday, n_entries, risk_pct) or None if no trigger."""
    px, vw = bars["close"].values, bars["vwap"].values; hi, lo = bars["high"].values, bars["low"].values
    t = bars.index; mins = t.hour * 60 + t.minute - 570; n = len(px)
    day_low_close = Lv[i, j]; prev_close = Cv[i - 1, j]; day_open = bars["open"].values[0]
    if kind == "ORB":
        m15 = mins < 15
        if m15.sum() < 10: return None
        or_hi, or_lo = hi[m15].max(), lo[m15].min(); stop0 = or_lo
        def trigger(k): return mins[k] >= 15 and mins[k] <= 150 and px[k] > or_hi and px[k - 1] <= or_hi
    else:
        ref = max(day_open, prev_close); flush_lvl = ref * (1 - 0.0025 * day_adr)
        def trigger(k):
            if mins[k] < 10 or mins[k] > 150: return False
            flushed = lo[: k + 1].min() <= flush_lvl
            return flushed and px[k] > vw[k] and px[k - 1] <= vw[k - 1]
    trades, k, entries, stopped = [], 1, 0, 0; max_entries = 3 if execution == "intraday+re" else 1
    while k < n and entries < max_entries:
        if trigger(k):
            entry = px[k]; stop = or_lo if kind == "ORB" else lo[: k + 1].min(); entries += 1
            if entry <= stop: k += 1; continue
            if execution == "close-judged":
                if Cv[i, j] < stop: trades.append(trade(entry, Cv[i, j], stop)); break        # stopped on the entry-day close
                trades.append(trade(entry, daily_hold(i, j, entry, stop, i + 1), stop)); break
            # intraday execution: first 1-min close below the stop
            out = None
            for q in range(k + 1, n):
                if px[q] < stop: out = q; break
            if out is not None:
                trades.append(trade(entry, px[out], stop)); stopped += 1; k = out + 1; continue
            # survived the day: raise the stop to the session low, manage on daily closes
            trades.append(trade(entry, daily_hold(i, j, entry, min(lo.min(), day_low_close), i + 1), stop)); break
        k += 1
    if not trades: return None
    pct = sum(x[0] for x in trades); R = sum(x[1] for x in trades)
    first_entry_risk = None
    return dict(pct=pct, R=R, stopped=int(stopped > 0), n_entries=entries, risk_pct=100 * (trades[0][0] * 0 + 1) * 0 + 0)  # risk filled below


rows = []
files = {f: True for f in os.listdir(CACHE)}
for s in syms:
    if s not in col: continue
    j = col[s]
    for d in idx[idx >= "2026-02-02"]:
        i = idx.get_loc(d)
        if i == 0 or not state.values[i, j]: continue
        f = f"{s}_{d.date()}.parquet"
        if f not in files or not np.isfinite(Cv[i, j]): continue
        bars = pd.read_parquet(os.path.join(CACHE, f))
        if len(bars) < 300: continue
        day_adr = adr.values[i, j]
        base = trade(Cv[i, j], daily_hold(i, j, Cv[i, j], Lv[i, j], i + 1), Lv[i, j])
        rec = dict(date=d, sym=s, control=s in extra, close_pct=base[0], close_R=base[1], close_risk=100 * (Cv[i, j] / Lv[i, j] - 1))
        for kind in ("ORB", "RECLAIM"):
            for ex in ("close-judged", "intraday", "intraday+re"):
                r = simulate(bars, i, j, kind, ex, day_adr)
                if r: rec[f"{kind}_{ex}_pct"] = r["pct"]; rec[f"{kind}_{ex}_R"] = r["R"]; rec[f"{kind}_{ex}_stopped"] = r["stopped"]; rec[f"{kind}_{ex}_n"] = r["n_entries"]
        # initial risk of the ORB / RECLAIM entry (from the first trigger) for the return-per-1%-risked metric
        px, lo, hi = bars["close"].values, bars["low"].values, bars["high"].values; mins = bars.index.hour * 60 + bars.index.minute - 570
        m15 = mins < 15
        if m15.sum() >= 10:
            or_hi, or_lo = hi[m15].max(), lo[m15].min(); kk = [k for k in range(1, len(px)) if 15 <= mins[k] <= 150 and px[k] > or_hi and px[k - 1] <= or_hi]
            if kk: rec["ORB_risk"] = 100 * (px[kk[0]] / or_lo - 1)
        rows.append(rec)
D = pd.DataFrame(rows)
print(f"{len(D):,} layer-2 name-days with 1-min bars, {D['sym'].nunique()} names, {D['date'].nunique()} sessions {D['date'].min().date()}..{D['date'].max().date()} | control-set name-days {D['control'].sum():,}")


def line(x, pcol, lab, rcol=None, stcol=None, riskcol=None):
    y = x.dropna(subset=[pcol])
    if len(y) < 15: print(f"  {lab:<44} n={len(y):4d} (too few)"); return
    m = y.groupby("date")[pcol].mean(); t = m.mean() / (m.std(ddof=1) / sqrt(len(m)))
    s = f"  {lab:<44} n={len(y):4d}  ret {y[pcol].mean():+6.2f}% (t_day {t:+4.1f})  median {y[pcol].median():+6.2f}%  win {100*(y[pcol]>0).mean():3.0f}%"
    if rcol: s += f"  R {y[rcol].mean():+6.2f}"
    if stcol and stcol in y: s += f"  stopped same day {100*y[stcol].mean():3.0f}%"
    if riskcol and riskcol in y: s += f"  initial stop {y[riskcol].median():.1f}% away  ret/1% risked {y[pcol].mean()/y[riskcol].median():+.2f}"
    print(s)


for lab, X in (("ALL (curated = hindsight)", D), ("BLIND CONTROL SET only", D[D["control"]])):
    print(f"\n==================== {lab} ====================")
    line(X, "close_pct", "CLOSE entry, stop = day low, daily management", "close_R", None, "close_risk")
    for kind in ("ORB", "RECLAIM"):
        print(f"  -- {kind} --")
        for ex in ("close-judged", "intraday", "intraday+re"):
            line(X, f"{kind}_{ex}_pct", f"{kind} {ex}", f"{kind}_{ex}_R", f"{kind}_{ex}_stopped", "ORB_risk" if kind == "ORB" else None)
        sub = X.dropna(subset=[f"{kind}_intraday+re_pct"])
        if len(sub): print(f"     re-entry: name-days with >1 entry {100*(sub[f'{kind}_intraday+re_n']>1).mean():.0f}%, mean entries {sub[f'{kind}_intraday+re_n'].mean():.2f}")
    # paired: same name-days, ORB intraday+re vs CLOSE
    for kind in ("ORB", "RECLAIM"):
        pr = X.dropna(subset=[f"{kind}_intraday+re_pct"]); diff = pr[f"{kind}_intraday+re_pct"] - pr["close_pct"]; m = pr.assign(x=diff).groupby("date")["x"].mean()
        if len(m) > 5: print(f"  paired {kind} intraday+re minus CLOSE on the same name-days: {diff.mean():+.2f}pp (t_day {m.mean()/(m.std(ddof=1)/sqrt(len(m))):+.1f}, n={len(pr)})")
print("\n== by month, ALL: CLOSE vs ORB intraday+re vs RECLAIM intraday+re (% per name-day) ==")
for k, g in D.groupby(D["date"].dt.to_period("M")):
    print(f"  {k}  n={len(g):4d}  close {g['close_pct'].mean():+6.2f}  ORB+re {g['ORB_intraday+re_pct'].mean():+6.2f} (n{g['ORB_intraday+re_pct'].notna().sum()})  RECLAIM+re {g['RECLAIM_intraday+re_pct'].mean():+6.2f} (n{g['RECLAIM_intraday+re_pct'].notna().sum()})")
D.to_csv("data/studies/entry_study_events.csv", index=False)
