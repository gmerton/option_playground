#!/usr/bin/env python3
"""
REPAIR A LOSING BULL PUT INTO AN IRON FLY: the stock falls, the short put reaches 45 delta -> SELL a call spread whose
short call is AT THE SHORT PUT'S STRIKE, same width, same expiry (pre-registered 2026-09-25, before any run; Gabe's
question).

WHY NEW. The two call-side tests so far sold 0.25/0.15-delta calls ABOVE the market after a RALLY
(run_leg_in_call_spread.py, INVERTED -7.26%/trade; the delta sweep, all 8 cells negative). This one sells a near-the-money
call (the put's strike is now above spot) after a DROP, and it turns the position into an iron butterfly centred on the
original strike. Different timing, different moneyness, and a different purpose: a hedge on the put, not a standalone
bet on the drift.

UNIVERSE, DATA, BASE, TRIGGER, COSTS: identical to run_add_on_put_spread.py. SPY QQQ IWM + 10 mega-caps, 2012 -> 2026-03,
  v3 direct (data/cache/leg_in/), Friday 0.25/0.15 bull put at the expiry closest to 20 DTE, trigger = the first session
  with the base short put's delta <= -0.45 while the base is open and DTE >= 5. House cost model; raw parity spot for
  settlement.
TREATED   on the trigger day: short call at the base's short-put strike Ks (must be quoted with bid > 0), long call at the
          quoted strike nearest Ks + (Ks - Kl) (the put spread's width). Two management arms: 50% take on the call spread
          alone, and HOLD to expiry (the fly held together).
CONTROL   in untriggered cycles, the call spread sold at the same DTE with its short call at the strike whose delta is
          nearest the treated short call's entry delta (0.05 bins), and the same width as a fraction of the short strike (0.005 bins).
          Matched on (ticker, DTE, delta bin) within +-730 days. Only the timing varies (after a drop).
CELLS     PRIMARY: pooled, after-cost return on risk of the TREATED call spread, HOLD (the fly is the stated structure).
          Month-clustered t >= 3, halves (2019-01) > 0, majority of years > 0. CO-REQUIREMENT: treated - control >= 0.
          Reported: {pooled, ETFs, names} x {abs, diff} x {take, hold} = 12 -> Sidak(12) |t| >= 2.87; house 3 governs.
HEDGE VIEW (declared, reported whatever the verdict; no bar): in triggered cycles, the base put spread held to expiry
          alone vs base + call spread, both in dollars per unit of the BASE's risk: mean, p5, p1, the share of cycles
          losing >= 75% of base risk, and the worst 5 cycles. Reported as the insurance's price: the mean given up per
          point of p5 improvement.
PRIOR     for the call spread's own EV: negative-to-flat (the call side has lost everywhere and stocks drift up; a drop
          followed by a rebound through the strike is the fly's loss case). The hedge view could still show a sensible
          tail trade.

Usage: PYTHONPATH=src:. python run_put_repair_fly.py  (log -> data/studies/logs/put_repair_fly.log); run on Fargate via
       services/study-runner/ (WORKERS env).
"""
from __future__ import annotations

import os
import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

import run_leg_in_call_spread as L

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/put_repair_fly.log"


def trade_k(ch, spot, t0, exp, cp, ks, kl, take, cost):
    """Sell the vertical (ks short, kl long) at t0. Returns (pnl per share, risk per share) or None."""
    qs, ql = ch.quote(t0, exp, cp, ks), ch.quote(t0, exp, cp, kl)
    if qs is None or ql is None or qs[0] <= 0:
        return None
    credit = L.fill(*qs, True, cost) - L.fill(*ql, False, cost)
    width = abs(ks - kl)
    if credit <= 0 or credit >= width:
        return None
    if take:
        for day in ch.dates[(ch.dates > t0) & (ch.dates < exp)]:
            a, b = ch.quote(day, exp, cp, ks), ch.quote(day, exp, cp, kl)
            if a is None or b is None:
                continue
            close = L.fill(*a, False, cost) - L.fill(*b, True, cost)
            if close <= 0.5 * credit:
                return credit - close, width - credit
    s = spot.loc[:exp]
    if s.empty or (exp - s.index[-1]).days > 4:
        return None
    S = float(s.iloc[-1])
    intr = (max(ks - S, 0) - max(kl - S, 0)) if cp == "P" else (max(S - ks, 0) - max(S - kl, 0))
    return credit - intr, width - credit


def nearest(q, k):
    return q.index[np.argmin(np.abs(q.index.values - k))]


def work(tk: str):
    V3 = pd.concat([pd.read_parquet(L.CACHE / f"v3_{y}.parquet", filters=[("ticker", "==", tk)]) for y in range(L.Y0, L.Y1 + 1)])
    V3 = V3[V3.trade_date <= L.END]
    cs = pd.read_parquet(REPO / "data/cache/chain_spot/chain_spot_daily.parquet", columns=["ticker", "trade_date", "spot"],
                         filters=[("ticker", "==", tk)])
    cs["trade_date"] = pd.to_datetime(cs.trade_date)
    spot = cs.set_index("trade_date").spot.sort_index()
    ch = L.Chain(V3)
    exps = np.array(sorted(V3.expiry.unique()))
    dset = set(pd.to_datetime(ch.dates))
    cycles, treated = [], []
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
        base_take = trade_k(ch, spot, f, exp, "P", ks, kl, True, True)
        base_hold = trade_k(ch, spot, f, exp, "P", ks, kl, False, True)
        if base_take is None or base_hold is None:
            continue
        # close day of the take arm (for the "still open" condition)
        close_day = exp
        cr = L.fill(*ch.quote(f, exp, "P", ks), True, True) - L.fill(*ch.quote(f, exp, "P", kl), False, True)
        for day in ch.dates[(ch.dates > f) & (ch.dates < exp)]:
            a, b = ch.quote(day, exp, "P", ks), ch.quote(day, exp, "P", kl)
            if a is not None and b is not None and L.fill(*a, False, True) - L.fill(*b, True, True) <= 0.5 * cr:
                close_day = pd.Timestamp(day); break
        trig = None
        for day in ch.dates[(ch.dates > f) & (ch.dates < exp)]:
            day = pd.Timestamp(day)
            if day >= close_day or (exp - day).days < 5:
                break
            q = ch.get(day, exp, "P")
            if q is None or ks not in q.index:
                continue
            dl = q.loc[ks, "delta"]
            if np.isfinite(dl) and dl <= -0.45:
                trig = day; break
        cycles.append((f, exp, trig))
        if trig is None:
            continue
        qc = ch.get(trig, exp, "C")
        if qc is None or ks not in qc.index or not np.isfinite(qc.loc[ks, "delta"]):
            continue
        kc_l = nearest(qc, ks + (ks - kl))
        if kc_l <= ks:
            continue
        row = dict(ticker=tk, entry=trig, expiry=exp, dte=(exp - trig).days, c_delta=float(qc.loc[ks, "delta"]),
                   wfrac=(kc_l - ks) / ks, base_risk=base_hold[1], base_pnl_hold=base_hold[0])
        for take in (True, False):
            for cost in (True, False):
                r = trade_k(ch, spot, trig, exp, "C", ks, kc_l, take, cost)
                t = f"{'take' if take else 'hold'}_{'net' if cost else 'gross'}"
                row[f"r_{t}"] = r[0] / r[1] if r else np.nan
                row[f"pnl_{t}"] = r[0] if r else np.nan
        treated.append(row)
    # matched controls: untriggered cycles, same DTE, short call at the nearest-delta strike (0.05 bins), same width fraction
    need = {(t["dte"], round(t["c_delta"] / 0.05) * 0.05, round(t["wfrac"] / 0.005) * 0.005) for t in treated}
    controls = []
    for f, exp, trig in cycles:
        if trig is not None:
            continue
        for k, db, wf in need:
            day = exp - pd.Timedelta(days=k)
            if day <= f or day not in dset:
                continue
            qc = ch.get(day, exp, "C")
            if qc is None:
                continue
            qd = qc[qc.delta.notna() & (qc.bid > 0)]
            if qd.empty:
                continue
            kc = qd.index[np.argmin(np.abs(qd.delta.values - db))]
            kl2 = nearest(qc, kc * (1 + wf))
            if kl2 <= kc:
                continue
            row = dict(ticker=tk, entry=day, expiry=exp, dte=k, dbin=db, wfrac=wf)
            for take in (True, False):
                r = trade_k(ch, spot, day, exp, "C", kc, kl2, take, True)
                row[f"r_{'take' if take else 'hold'}_net"] = r[0] / r[1] if r else np.nan
            controls.append(row)
    return treated, controls, len(cycles)


def main():
    with Pool(int(os.environ.get("WORKERS", "4"))) as p:
        res = p.map(work, L.TICKERS)
    T = pd.DataFrame([r for t, _, _ in res for r in t]); C = pd.DataFrame([r for _, c, _ in res for r in c])
    ncyc = sum(n for _, _, n in res)
    out = ["# Repair a losing bull put into an iron fly (pre-registration in the docstring)",
           f"base cycles {ncyc}, treated {len(T)}; median call delta at entry {T.c_delta.median():.2f}, median DTE {T.dte.median():.0f}; "
           f"control trades {len(C)}"]
    T["dbin"] = (T.c_delta / 0.05).round() * 0.05; T["wf"] = (T.wfrac / 0.005).round() * 0.005
    g = C.groupby(["ticker", "dte", "dbin", "wfrac"])
    for ex in ("take", "hold"):
        mc = []
        for r in T.itertuples():
            try:
                m = g.get_group((r.ticker, r.dte, r.dbin, r.wf))
            except KeyError:
                mc.append(np.nan); continue
            m = m[(m.entry - r.entry).abs() <= pd.Timedelta(days=730)][f"r_{ex}_net"]
            mc.append(m.mean() if m.notna().sum() >= 3 else np.nan)
        T[f"ctl_r_{ex}_net"] = mc
    T["month"] = T.entry.dt.to_period("M")
    T.to_csv(REPO / "data/studies/logs/put_repair_fly_treated.csv", index=False)
    R = []
    for grp, G in (("pooled", T), ("ETFs", T[T.ticker.isin(L.ETFS)]), ("names", T[T.ticker.isin(L.NAMES)])):
        for ex in ("take", "hold"):
            for kind in ("abs", "diff"):
                x = G[f"r_{ex}_net"] * 100
                if kind == "diff":
                    x = x - G[f"ctl_r_{ex}_net"] * 100
                x = x.dropna(); mo = G.loc[x.index, "month"]; h = mo < L.SPLIT
                yr = x.groupby(G.loc[x.index, "entry"].dt.year).mean()
                t = L.clustered_t(x, mo)
                ok = t >= 3 and x[h].mean() > 0 and x[~h].mean() > 0 and (yr > 0).sum() > len(yr) / 2
                R.append(dict(group=grp, exit=ex, measure=kind, n=len(x), mean=x.mean(),
                              gross=G[f"r_{ex}_gross"].mean() * 100 if kind == "abs" else np.nan, t=t, h1=x[h].mean(),
                              h2=x[~h].mean(), yrs_pos=f"{(yr > 0).sum()}/{len(yr)}",
                              win=(x > 0).mean() if kind == "abs" else np.nan, PASS=ok,
                              primary=grp == "pooled" and ex == "hold" and kind == "abs"))
    D = pd.DataFrame(R)
    out.append("\n" + D.round(2).to_string(index=False))
    base = T.base_pnl_hold / T.base_risk * 100
    comb = (T.base_pnl_hold + T.pnl_hold_net) / T.base_risk * 100
    out.append(f"\nHEDGE VIEW (held to expiry, % of BASE risk): base alone mean {base.mean():+.1f} p5 {base.quantile(.05):+.1f} "
               f"p1 {base.quantile(.01):+.1f} lose>=75% {(base <= -75).mean():.0%} | fly mean {comb.mean():+.1f} p5 "
               f"{comb.quantile(.05):+.1f} p1 {comb.quantile(.01):+.1f} lose>=75% {(comb <= -75).mean():.0%}")
    dp5 = comb.quantile(.05) - base.quantile(.05)
    out.append(f"  insurance price: mean change {comb.mean() - base.mean():+.1f} for a p5 change of {dp5:+.1f} points")
    w = T.assign(comb=comb).nsmallest(5, "comb")
    out.append("  worst 5 fly cycles: " + ", ".join(f"{r.ticker} {r.entry.date()} {r.comb:+.0f}" for r in w.itertuples()))
    p = D[D.primary].iloc[0]; d = D[(D.group == "pooled") & (D.exit == "hold") & (D.measure == "diff")].iloc[0]
    out.append(f"\nVERDICT (PRIMARY pooled/hold/abs): call spread {p['mean']:+.2f}%/trade net (gross {p.gross:+.2f}) t {p.t:+.2f} "
               f"halves {p.h1:+.2f}/{p.h2:+.2f} yrs {p.yrs_pos} -> {'PASS' if p.PASS else 'fail'}; vs matched control "
               f"{d['mean']:+.2f}pp t {d.t:+.2f} -> " + ("ADOPT" if p.PASS and d["mean"] >= 0 else "do not adopt"))
    D.to_csv(REPO / "data/studies/put_repair_fly_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
