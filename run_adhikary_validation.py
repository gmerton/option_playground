#!/usr/bin/env python3
"""
Validate the Adhikary-archetype detectors (run_adhikary_scan.py) on 2019-2026 history so the
recipe's thresholds are not fit to the 20 curated winners.

Panel: data/cache/liquid_panel_2019.parquet (yfinance adjusted, names liquid on 2026-07-31).
Eligibility is point-in-time (trailing-50 ADDV >= $50M, price >= $5) -- trims but does not remove
survivorship. Read RELATIVE comparisons (gate on vs off, archetype vs baseline), not absolute levels.

For each event: 5/10/21-session forward return, excess vs the same-date every-stock baseline,
and a simulated Tito hold: stop = close below the entry bar's low, exit = first daily close below
the 20 EMA (grind trail), capped at 60 sessions; R = return / (entry - entry-day low).

Usage: PYTHONPATH=src python run_adhikary_validation.py [--panel path]
"""
from __future__ import annotations
import argparse, warnings
import numpy as np, pandas as pd
from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)

def tstat(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--panel", default="data/cache/liquid_panel_2019.parquet"); a = ap.parse_args()
    raw = pd.read_parquet(a.panel); raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw); O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    s10, s20, s50 = C.rolling(10).mean(), C.rolling(20).mean(), C.rolling(50).mean(); e20 = C.ewm(span=20, adjust=False).mean()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52, lo52 = H.shift(1).rolling(252, min_periods=120).max(), L.shift(1).rolling(252, min_periods=120).min(); range52 = (hi52 - lo52) / C * 100
    piv15, piv50 = H.shift(1).rolling(15).max(), H.shift(1).rolling(50).max()
    avgv = V.shift(1).rolling(50).mean(); rvol = V / avgv
    stacked = (s10 > s20) & (s20 > s50)
    stack_days = stacked.astype(int).copy(); arr = stack_days.values
    for i in range(1, len(arr)): arr[i] = np.where(arr[i] > 0, arr[i - 1] + 1, 0)
    stack_days = pd.DataFrame(arr, index=C.index, columns=C.columns)
    pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    r10 = H.rolling(10).max() - L.rolling(10).min(); r20p = H.shift(10).rolling(20).max() - L.shift(10).rolling(20).min(); contr = r10 / r20p
    dry = V.shift(1).rolling(5).mean() / avgv; ext20 = (C / s20 - 1) * 100 / adr
    gate = (adr >= 3) & (range52 >= 17) & elig
    ev = {}
    ev["A_breakout15"] = gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15)
    ev["A_noADRgate"] = elig & (range52 >= 17) & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15) & (adr < 3)
    ev["A_rvol>=1.5"] = ev["A_breakout15"] & (rvol >= 1.5)
    ev["A_rvol1.1-1.5"] = ev["A_breakout15"] & (rvol < 1.5)
    ev["A_pivot50"] = gate & (C >= piv50) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv50)
    ev["A_notstacked"] = gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days < 5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15)
    vp = C / piv15 - 1; setup = stacked & (vp >= -0.05) & (vp <= 0) & (contr <= 0.6) & (dry <= 0.8) & gate
    setup_recent = setup.shift(1).rolling(10).max().fillna(0).astype(bool)
    ev["A_after_SETUP"] = ev["A_breakout15"] & setup_recent
    ev["A_no_SETUP"] = ev["A_breakout15"] & ~setup_recent
    ev["B_catalyst"] = gate & ((gap >= 0.05) | (chg >= 0.08)) & (rvol >= 2) & (C >= piv15) & (pos >= 0.75)
    ev["C_exhaustion(SHORT)"] = gate & (H >= H.shift(1).rolling(20).max()) & (C < O) & (pos <= 0.30) & (rvol >= 2.3) & (ext20 >= 2) & stacked
    ev["SETUP_day"] = setup
    # forward returns
    fr = {n: (C.shift(-n) / C - 1).clip(-0.6, 1.0).where(elig) for n in (5, 10, 21)}
    base = {n: fr[n].mean(axis=1) for n in fr}
    Cv, Lv, E20v = C.values, L.values, e20.values; idx = C.index; cols = C.columns
    def trail(i, j):
        entry = Cv[i, j]; stop = Lv[i, j]
        if not np.isfinite(entry) or not np.isfinite(stop) or entry <= stop: return np.nan, np.nan, np.nan, np.nan
        for k in range(i + 1, min(i + 61, len(Cv))):
            c = Cv[k, j]
            if not np.isfinite(c): continue
            if c < stop: return c / entry - 1, (c - entry) / (entry - stop), k - i, 1
            if c < E20v[k, j]: return c / entry - 1, (c - entry) / (entry - stop), k - i, 0
        k = min(i + 60, len(Cv) - 1); c = Cv[k, j]
        return c / entry - 1, (c - entry) / (entry - stop), k - i, 0
    print(f"panel {C.shape[1]} names {idx[0].date()}..{idx[-1].date()}; eligible/day median {int(elig.sum(axis=1).median())}")
    rows = []; res = {}
    for name, m in list(ev.items()):
        mm = m.fillna(False).astype(bool); mm = mm[mm.index >= "2019-10-01"]
        ii, jj = np.where(mm.values); ii = ii + (len(C) - len(mm))
        if len(ii) == 0: rows.append(dict(setup=name, n=0)); continue
        d = idx[ii]; r = {n: fr[n].values[ii, jj] for n in fr}; xs = {n: r[n] - base[n].values[ii] for n in fr}
        tr = np.array([trail(i, j) for i, j in zip(ii, jj)])
        de = pd.Series(xs[10], index=d).groupby(level=0).mean()
        rows.append(dict(setup=name, n=len(ii), names=len(set(jj)), r5=100*np.nanmean(r[5]), r10=100*np.nanmean(r[10]), r10_med=100*np.nanmedian(r[10]), win10=100*np.nanmean(r[10] > 0),
                         xs10=100*np.nanmean(xs[10]), t_xs10=tstat(de), r21=100*np.nanmean(r[21]), xs21=100*np.nanmean(xs[21]),
                         trail_ret=100*np.nanmean(tr[:, 0]), trail_med=100*np.nanmedian(tr[:, 0]), R_mean=np.nanmean(tr[:, 1]), R_med=np.nanmedian(tr[:, 1]), R_win=100*np.nanmean(tr[:, 1] > 0), stopped=100*np.nanmean(tr[:, 3]), hold_med=np.nanmedian(tr[:, 2])))
        res[name] = (d, jj, r, xs, tr)
    out = pd.DataFrame(rows).set_index("setup")
    print("\n=== ARCHETYPE EVENT STUDY (events 2019-10 .. 2026-09; long returns, so C should be NEGATIVE) ===")
    print(out.round(2).to_string())
    print("\n=== BY YEAR: A_breakout15 (10s excess, trail R) vs A_pivot50 ===")
    for name in ("A_breakout15", "A_pivot50", "B_catalyst", "SETUP_day"):
        d, jj, r, xs, tr = res[name]; df = pd.DataFrame({"y": d.year, "xs10": xs[10], "R": tr[:, 1], "r21": r[21]})
        g = df.groupby("y").agg(n=("xs10", "size"), xs10=("xs10", "mean"), r21=("r21", "mean"), R=("R", "mean"), Rwin=("R", lambda x: (x > 0).mean()))
        g[["xs10", "r21"]] *= 100; g["Rwin"] *= 100
        print(f"  {name}:"); print("   " + g.round(2).to_string().replace("\n", "\n   "))
    d, jj, r, xs, tr = res["A_breakout15"]
    df = pd.DataFrame({"adr": adr.values[np.searchsorted(idx, d), jj], "rvol": rvol.values[np.searchsorted(idx, d), jj], "stackd": stack_days.values[np.searchsorted(idx, d), jj], "off52": (C / hi52 - 1).values[np.searchsorted(idx, d), jj] * 100, "xs10": xs[10], "R": tr[:, 1], "r21": r[21]})
    print("\n=== A_breakout15 by feature bucket (xs10 pp, mean R, R win%) ===")
    for col, bins in (("adr", [3, 4, 5, 7, 10, 100]), ("rvol", [1.1, 1.3, 1.5, 2, 3, 100]), ("stackd", [5, 10, 20, 40, 1000]), ("off52", [-100, -30, -15, -5, 0.01])):
        g = df.groupby(pd.cut(df[col], bins), observed=True).agg(n=("xs10", "size"), xs10=("xs10", "mean"), r21=("r21", "mean"), R=("R", "mean"), Rwin=("R", lambda x: (x > 0).mean()))
        g[["xs10", "r21"]] *= 100; g["Rwin"] *= 100; print(f"  {col}:"); print("   " + g.round(2).to_string().replace("\n", "\n   "))
    # combined precision filter: A after SETUP, ADR 4-7, within 15% of the 52wk high, stack 5-40d
    m = (df.adr.between(4, 7)) & (df.off52 > -15) & (df.stackd <= 40)
    setup_flag = pd.Series(res["A_after_SETUP"][0]).isin([]) if False else None
    d_all = res["A_breakout15"][0]; jj_all = res["A_breakout15"][1]
    sr = setup_recent.values[np.searchsorted(idx, d_all), jj_all]
    df["after_setup"] = sr; df["y"] = d_all.year
    print("\n=== COMBINED FILTERS on A_breakout15 (xs10 pp, r21 %, mean R, R win %) ===")
    for lab, mask in (("all A", np.ones(len(df), bool)), ("after SETUP", df.after_setup.values), ("ADR 4-7 & off52>-15 & stack<=40", m.values), ("after SETUP & ADR 4-7 & off52>-15 & stack<=40", (m & df.after_setup).values), ("after SETUP & off52>-15", (df.after_setup & (df.off52 > -15)).values)):
        g = df[mask]; by = g.groupby("y").R.mean()
        print(f"  {lab:48s} n={len(g):5d} xs10 {100*g.xs10.mean():+.2f} r21 {100*g.r21.mean():+.2f} R {g.R.mean():+.2f} med {g.R.median():+.2f} win {100*(g.R>0).mean():.0f}% | R by year: " + " ".join(f"{y}:{v:+.2f}" for y, v in by.items()))
    # ---- regime conditioning (feedback 2026-09-08: studies must weight current conditions) ----
    spy = raw[raw.ticker == "SPY"].set_index("date").close.sort_index() if (raw.ticker == "SPY").any() else None
    if spy is None:
        spy = pd.read_parquet(a.panel); spy = spy[spy.ticker == "SPY"].set_index("date").close.sort_index(); spy.index = pd.to_datetime(spy.index)
    s50s, s200s = spy.rolling(50).mean(), spy.rolling(200).mean()
    adv = (C.pct_change(fill_method=None) > 0).where(elig).mean(axis=1); adv10 = adv.rolling(10).mean()
    trend = pd.Series(np.where((spy > s50s) & (s50s > s200s), "up", np.where(spy < s200s, "bear", "chop")), index=spy.index).reindex(idx).ffill()
    breadth = pd.Series(np.where(adv10 >= 0.5, "B+", "B-"), index=idx)
    state = (trend + "/" + breadth)
    today = state.iloc[-1]
    print(f"\n=== REGIME CONDITIONING: state = SPY trend (up: >50>200 | chop | bear: <200) / 10d advancer avg (B+ >=50%) — TODAY = {today} ({idx[-1].date()}) ===")
    for name in ("A_breakout15", "B_catalyst", "SETUP_day"):
        dd, jj2, r2, xs2, tr2 = res[name]; st = state.reindex(dd).values
        g = pd.DataFrame({"state": st, "xs10": xs2[10], "r21": r2[21], "R": tr2[:, 1]}).groupby("state").agg(n=("R", "size"), xs10=("xs10", "mean"), r21=("r21", "mean"), R=("R", "mean"), Rwin=("R", lambda x: (x > 0).mean()))
        g[["xs10", "r21"]] *= 100; g["Rwin"] *= 100; g["TODAY"] = np.where(g.index == today, "<==", "")
        print(f"  {name}:"); print("   " + g.round(2).to_string().replace("\n", "\n   "))
    st = state.reindex(d_all).values; dfp = df[m.values].copy(); dfp["state"] = st[m.values]
    g = dfp.groupby("state").agg(n=("R", "size"), xs10=("xs10", "mean"), R=("R", "mean"), Rwin=("R", lambda x: (x > 0).mean())); g[["xs10"]] *= 100; g["Rwin"] *= 100; g["TODAY"] = np.where(g.index == today, "<==", "")
    print("  PRECISION tier:"); print("   " + g.round(2).to_string().replace("\n", "\n   "))
    # SETUP -> does it break within 10 sessions, and does that break outperform?
    s = ev["SETUP_day"].fillna(False).astype(bool); brk = (C >= piv15) & (C.shift(1) < piv15)
    brk_next10 = brk.shift(-1).rolling(10).max().shift(-9).fillna(0).astype(bool) if False else pd.DataFrame(np.zeros(C.shape, bool), index=idx, columns=cols)
    bv = brk.fillna(False).values
    for k in range(1, 11): brk_next10.values[:-k] |= bv[k:]
    sm = s[s.index >= "2019-10-01"]; bn = brk_next10[brk_next10.index >= "2019-10-01"]
    print(f"\nSETUP days: {int(sm.values.sum())}; P(pivot break within 10 sessions) = {100*bn.values[sm.values].mean():.1f}% vs unconditional stacked-gated day {100*bn.values[(stacked & gate)[stacked.index >= '2019-10-01'].fillna(False).values].mean():.1f}%")

if __name__ == "__main__":
    main()

# ---- appended 2026-09-08: combined "precision" filter check (run as part of main via env COMBO=1) ----
def combo():
    import os
    if os.environ.get("COMBO") != "1": return
combo()
