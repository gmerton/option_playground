#!/usr/bin/env python3
"""
AVERAGE DOWN A BULL PUT: the stock falls, the original short put goes from 25 to 45 delta -> SELL ANOTHER 0.25/0.15 bull
put at the new levels (pre-registered 2026-09-25, before any run; Gabe's question).

WHY NEW. The ledger has no add-on / averaging-down test for short premium. The nearest evidence points both ways:
  for     the one certified strategy sells SPY puts after weakness (below the 50-day with VIX >= 20, t 6.07), and IV is
          richest after drops;
  against "IV stays inflated after a big move" FAILED vs VIX-matched days (post-shock study), the crash-leader veto says
          deep drawdowns in names keep going, and adding doubles exposure at the worst moment.

UNIVERSE, DATA, BASE, COSTS: identical to run_leg_in_call_spread.py (SPY QQQ IWM + 10 mega-caps, 2012 -> 2026-03, v3
  direct, cached in data/cache/leg_in/; Friday 0.25/0.15 bull put at the expiry closest to 20 DTE, 50% take at the real
  closing cost; house cost model; raw chain-parity spot for settlement).
TRIGGER   the first session after entry, while the base spread is still open and DTE >= 5, on which the base SHORT put's
          delta is <= -0.45 (quoted delta of that strike that day).
TREATED   on the trigger day: SELL a new bull put, short nearest -0.25 delta, long nearest -0.15, SAME expiry. 50% take at
          the real closing cost, else settle at intrinsic on the expiry-date spot.
CONTROL   the same new spread (same ticker, 0.25/0.15, same DTE at entry) sold in cycles where the trigger did NOT fire,
          on the session with that same DTE; matched per treated trade on (ticker, DTE) within +-730 days. Only the
          timing varies: after a drop that pushed the first spread to 45 delta.
CELLS     PRIMARY: pooled, after-cost return on risk of the TREATED add-on, 50% take (the decision: is the second
          spread worth selling?). Month-clustered t >= 3, both halves (2019-01) > 0, a majority of years > 0.
          CO-REQUIREMENT for adoption: treated minus matched control >= 0.
          Reported: {pooled, ETFs, names} x {treated abs, treated - control} x {take, hold} = 12 -> Sidak(12) |t| >= 2.87;
          the house 3 governs.
RISK (declared, reported whatever the verdict): in triggered cycles, the COMBINED position (base + add-on, each per unit
          of its own risk, summed) vs the base alone: mean, the 5th percentile, the share of cycles where both lose >= 50%
          of risk, and the worst 5 cycles. Averaging down can raise the mean while fattening the tail, and both must be
          seen.
PRIOR     mixed: plausible on ETFs (the certified mechanism), weak on single names.

Usage: PYTHONPATH=src:. python run_add_on_put_spread.py  (log -> data/studies/logs/add_on_put_spread.log);
       run on Fargate via services/study-runner/ (WORKERS env sets the pool size).
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
LOG = REPO / "data/studies/logs/add_on_put_spread.log"
VARIANTS = [(take, cost) for take in (True, False) for cost in (True, False)]


def tag(take, cost):
    return f"r_{'take' if take else 'hold'}_{'net' if cost else 'gross'}"


def work(tk: str):
    V3 = pd.concat([pd.read_parquet(L.CACHE / f"v3_{y}.parquet", filters=[("ticker", "==", tk)]) for y in range(L.Y0, L.Y1 + 1)])
    V3 = V3[V3.trade_date <= L.END]
    cs = pd.read_parquet(REPO / "data/cache/chain_spot/chain_spot_daily.parquet", columns=["ticker", "trade_date", "spot"],
                         filters=[("ticker", "==", tk)])
    cs["trade_date"] = pd.to_datetime(cs.trade_date)
    spot = cs.set_index("trade_date").spot.sort_index()
    ch = L.Chain(V3)
    exps = np.array(sorted(V3.expiry.unique()))
    cycles, treated = [], []
    for f in [x for x in ch.dates if pd.Timestamp(x).dayofweek == 4]:
        f = pd.Timestamp(f)
        dte = np.array([(pd.Timestamp(e) - f).days for e in exps])
        ok = np.flatnonzero((dte >= 14) & (dte <= 28))
        if not len(ok) or f not in spot.index:
            continue
        exp = pd.Timestamp(exps[ok[np.argmin(np.abs(dte[ok] - 20))]])
        ks = ch.pick(f, exp, "P", -0.25)
        base = {v: L.spread_trade(ch, spot, f, exp, "P", -0.25, -0.15, *v) for v in VARIANTS}
        if ks is None or base[(True, True)] is None:
            continue
        close_day = base[(True, True)][1]
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
        if trig is not None:
            row = dict(ticker=tk, base_entry=f, entry=trig, expiry=exp, dte=(exp - trig).days)
            for v in VARIANTS:
                r = L.spread_trade(ch, spot, trig, exp, "P", -0.25, -0.15, *v)
                row[tag(*v)] = r[0] if r else np.nan
                row["base_" + tag(*v)] = base[v][0] if base[v] else np.nan
            treated.append(row)
    need = {t["dte"] for t in treated}
    dset = set(pd.to_datetime(ch.dates))
    controls = []
    for f, exp, trig in cycles:
        if trig is not None:
            continue
        for k in need:
            day = exp - pd.Timedelta(days=k)
            if day <= f or day not in dset:
                continue
            row = dict(ticker=tk, entry=day, expiry=exp, dte=k)
            for v in VARIANTS:
                r = L.spread_trade(ch, spot, day, exp, "P", -0.25, -0.15, *v)
                row[tag(*v)] = r[0] if r else np.nan
            controls.append(row)
    return treated, controls, len(cycles)


def main():
    with Pool(int(os.environ.get("WORKERS", "4"))) as p:
        res = p.map(work, L.TICKERS)
    T = pd.DataFrame([r for t, _, _ in res for r in t]); C = pd.DataFrame([r for _, c, _ in res for r in c])
    ncyc = sum(n for _, _, n in res)
    out = ["# Average down a bull put: sell another 0.25/0.15 once the first short put hits 45 delta (pre-registration in the docstring)",
           f"base cycles {ncyc}, triggered {len(T)} ({len(T) / ncyc:.0%}), control trades {len(C)}; median DTE at trigger {T.dte.median():.0f}"]
    cols = [tag(*v) for v in VARIANTS]
    g = C.groupby(["ticker", "dte"])
    for col in cols:
        mc = []
        for r in T.itertuples():
            try:
                m = g.get_group((r.ticker, r.dte))
            except KeyError:
                mc.append(np.nan); continue
            m = m[(m.entry - r.entry).abs() <= pd.Timedelta(days=730)][col]
            mc.append(m.mean() if m.notna().sum() >= 3 else np.nan)
        T[f"ctl_{col}"] = mc
    T["month"] = T.entry.dt.to_period("M")
    T.to_csv(REPO / "data/studies/logs/add_on_put_spread_treated.csv", index=False)
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
                              primary=grp == "pooled" and ex == "take" and kind == "abs"))
    D = pd.DataFrame(R)
    out.append(f"unconditional control spread (take, net): {C.r_take_net.mean() * 100:+.2f}%/trade, n {C.r_take_net.notna().sum()}")
    out.append("\n" + D.round(2).to_string(index=False))
    # risk: combined vs base alone in triggered cycles
    comb = (T.base_r_take_net + T.r_take_net) * 100; base = T.base_r_take_net * 100
    both = ((T.base_r_take_net <= -0.5) & (T.r_take_net <= -0.5)).mean()
    out.append(f"\nRISK (triggered cycles, take, net, % of each spread's risk): base alone mean {base.mean():+.1f} p5 {base.quantile(0.05):+.1f} | "
               f"base + add-on mean {comb.mean():+.1f} p5 {comb.quantile(0.05):+.1f} | both lose >= 50%: {both:.0%}")
    w = T.assign(comb=comb).nsmallest(5, "comb")
    out.append("  worst 5 combined cycles: " + ", ".join(f"{r.ticker} {r.entry.date()} {r.comb:+.0f}" for r in w.itertuples()))
    p = D[D.primary].iloc[0]; d = D[(D.group == "pooled") & (D.exit == "take") & (D.measure == "diff")].iloc[0]
    out.append(f"\nVERDICT (PRIMARY pooled/take/abs): {p['mean']:+.2f}%/trade net (gross {p.gross:+.2f}) t {p.t:+.2f} halves "
               f"{p.h1:+.2f}/{p.h2:+.2f} yrs {p.yrs_pos} -> {'PASS' if p.PASS else 'fail'}; vs matched control {d['mean']:+.2f}pp "
               f"t {d.t:+.2f} -> " + ("ADOPT" if p.PASS and d["mean"] >= 0 else "do not adopt"))
    D.to_csv(REPO / "data/studies/add_on_put_spread_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
