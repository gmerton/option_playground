#!/usr/bin/env python3
"""
LEG INTO A CONDOR -- delta sweep: "at what deltas does selling the call spread work?" (pre-registered 2026-09-25,
before any run; Gabe, after run_leg_in_call_spread.py came back INVERTED at 0.25/0.15: -7.26%/trade net, t -4.31).

WHAT CHANGES. Only the call spread's deltas. Everything else is identical to run_leg_in_call_spread.py: the same universe
(SPY QQQ IWM + 10 mega-caps), 2012 -> 2026-03, the same Friday 20-DTE 0.25/0.15 bull put base, the same trigger
(spot > entry and the put spread >= 25% profitable at mid, DTE >= 5), same expiry, the same house cost model, a 50% take
else settle at intrinsic, the same matched control (the same call spread at the same DTE in untriggered cycles, same
ticker, +-730 days). Cached v3 pulls are reused (data/cache/leg_in/).

GRID (short / long call delta), 8 cells, fixed now:
  0.30/0.20  0.30/0.15  0.25/0.15 (the original)  0.25/0.10  0.20/0.10  0.20/0.05  0.15/0.05  0.10/0.03
MEASURE   per cell: the treated call spread's after-cost return on risk (pooled, month-clustered t), gross alongside;
          the difference vs the matched control; halves (2019-01); years.
BAR       this is a SEARCH, so the charge is on the best cell: Sidak(8) |t| >= 2.73, and the house |t| >= 3 GOVERNS;
          both halves positive; majority of years positive. ⚠ A lone passing cell whose grid NEIGHBOURS are negative is
          read as a best-of-k artefact (the WL-2 neighbourhood rule), not a result.
          The 0.25/0.15 cell re-runs the original and must reproduce -7.26 (method check).
PRIOR     very low. The original lost money gross (-4.57%), not just after costs; further-OTM calls collect less credit, so
          the fixed costs weigh more, and index call skew is cheapest in the wings.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_leg_in_delta_sweep.py   (log -> data/studies/logs/leg_in_delta_sweep.log)
"""
from __future__ import annotations

import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

import run_leg_in_call_spread as L

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/leg_in_delta_sweep.log"
GRID = [(0.30, 0.20), (0.30, 0.15), (0.25, 0.15), (0.25, 0.10), (0.20, 0.10), (0.20, 0.05), (0.15, 0.05), (0.10, 0.03)]


def work(tk: str):
    V3 = pd.concat([pd.read_parquet(L.CACHE / f"v3_{y}.parquet", filters=[("ticker", "==", tk)]) for y in range(L.Y0, L.Y1 + 1)])
    V3 = V3[V3.trade_date <= L.END]
    import run_dip_survivorship as DS
    cs = DS.pull(); cs = cs[cs.ticker == tk].copy(); cs["trade_date"] = pd.to_datetime(cs.trade_date)
    spot = cs.set_index("trade_date").spot.sort_index()
    ch = L.Chain(V3)
    exps = np.array(sorted(V3.expiry.unique()))
    cycles = []
    for f in [x for x in ch.dates if pd.Timestamp(x).dayofweek == 4]:
        f = pd.Timestamp(f)
        dte = np.array([(pd.Timestamp(e) - f).days for e in exps])
        ok = np.flatnonzero((dte >= 14) & (dte <= 28))
        if not len(ok) or f not in spot.index:
            continue
        exp = pd.Timestamp(exps[ok[np.argmin(np.abs(dte[ok] - 20))]])
        ks, kl = ch.pick(f, exp, "P", -0.25), ch.pick(f, exp, "P", -0.15)
        if ks is None or kl is None or not kl < ks:
            continue
        qs, ql = ch.quote(f, exp, "P", ks), ch.quote(f, exp, "P", kl)
        cm = (qs[0] + qs[1]) / 2 - (ql[0] + ql[1]) / 2
        base = L.spread_trade(ch, spot, f, exp, "P", -0.25, -0.15, True, True)
        if base is None or cm <= 0:
            continue
        s0, trig = float(spot.loc[f]), None
        for day in ch.dates[(ch.dates > f) & (ch.dates < exp)]:
            day = pd.Timestamp(day)
            if day >= base[1] or (exp - day).days < 5:
                break
            if day not in spot.index or spot.loc[day] <= s0:
                continue
            p = L.put_mid_profit(ch, day, exp, ks, kl, cm)
            if p is not None and p >= 0.25:
                trig = day; break
        cycles.append((f, exp, trig))
    dset = set(pd.to_datetime(ch.dates))
    need = {(e - t).days for f, e, t in cycles if t is not None}
    rows = []
    for ds, dl in GRID:
        for f, exp, trig in cycles:
            if trig is not None:
                r = L.spread_trade(ch, spot, trig, exp, "C", ds, dl, True, True)
                g = L.spread_trade(ch, spot, trig, exp, "C", ds, dl, True, False)
                rows.append(dict(ticker=tk, cell=f"{ds:.2f}/{dl:.2f}", kind="T", entry=trig, dte=(exp - trig).days,
                                 net=r[0] if r else np.nan, gross=g[0] if g else np.nan))
            else:
                for k in need:
                    day = exp - pd.Timedelta(days=k)
                    if day <= f or day not in dset:
                        continue
                    r = L.spread_trade(ch, spot, day, exp, "C", ds, dl, True, True)
                    rows.append(dict(ticker=tk, cell=f"{ds:.2f}/{dl:.2f}", kind="C", entry=day, dte=k,
                                     net=r[0] if r else np.nan, gross=np.nan))
    return rows


def main():
    with Pool(8) as p:
        R = pd.DataFrame([r for rows in p.map(work, L.TICKERS) for r in rows])
    R.to_parquet(REPO / "data/studies/logs/leg_in_delta_sweep_trades.parquet")
    out = ["# Leg-in call spread: delta sweep (pre-registration in the docstring)"]
    res = []
    for cell, G in R.groupby("cell", sort=False):
        T, C = G[G.kind == "T"].copy(), G[G.kind == "C"]
        cmap = C.groupby(["ticker", "dte"])
        ctl = []
        for r in T.itertuples():
            try:
                m = cmap.get_group((r.ticker, r.dte))
            except KeyError:
                ctl.append(np.nan); continue
            m = m[(m.entry - r.entry).abs() <= pd.Timedelta(days=730)].net
            ctl.append(m.mean() if m.notna().sum() >= 3 else np.nan)
        T["ctl"] = ctl
        x = (T.net * 100).dropna(); mo = T.loc[x.index, "entry"].dt.to_period("M"); h = mo < L.SPLIT
        yr = x.groupby(T.loc[x.index, "entry"].dt.year).mean()
        t = L.clustered_t(x, mo)
        d = ((T.net - T.ctl) * 100).dropna(); td = L.clustered_t(d, T.loc[d.index, "entry"].dt.to_period("M"))
        ok = t >= 3 and x[h].mean() > 0 and x[~h].mean() > 0 and (yr > 0).sum() > len(yr) / 2
        res.append(dict(cell=cell, n=len(x), net=x.mean(), gross=T.gross.mean() * 100, t=t, h1=x[h].mean(), h2=x[~h].mean(),
                        yrs_pos=f"{(yr > 0).sum()}/{len(yr)}", win=(x > 0).mean(), vs_ctl=d.mean(), t_vs_ctl=td,
                        ctl_net=C.net.mean() * 100, PASS=ok))
    D = pd.DataFrame(res)
    out.append(D.round(2).to_string(index=False))
    best = D.loc[D.t.idxmax()]
    out.append(f"\nMETHOD CHECK 0.25/0.15: {D[D.cell == '0.25/0.15'].net.iloc[0]:+.2f} (original -7.26)")
    out.append(f"VERDICT: best cell {best.cell} {best.net:+.2f}%/trade net t {best.t:+.2f} -> "
               + ("PASS" if D.PASS.any() else "no cell passes (Sidak(8) 2.73, house 3)"))
    D.to_csv(REPO / "data/studies/leg_in_delta_sweep_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
