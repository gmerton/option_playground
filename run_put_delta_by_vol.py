#!/usr/bin/env python3
"""
SHORT-PUT DELTA x VOLATILITY: "16 delta when vol is low, 20-25 delta when vol is high" (pre-registered 2026-09-25,
before any run; Sosnoff, More Tom clip u-86ZHe-d5s; Gabe asked for the test).

WHY NEW. The ledger has vol LEVEL as a predictor of put-spread ROC (vix_pct t +6.54) and the certified SPY cell at
0.25/0.15 with VIX >= 20, but never the INTERACTION: whether the best short delta depends on the vol regime. That
interaction is the claim.

UNIVERSE, DATA, COSTS: as run_leg_in_call_spread.py -- SPY QQQ IWM + 10 mega-caps, 2012 -> 2026-03, v3 direct (cached in
  data/cache/leg_in/, puts pulled down to -0.60 delta), house cost model, raw chain-parity spot for settlement.
TRADES    every Friday, per ticker: a bull put at the expiry closest to 20 DTE (14-28), short put nearest
          -{0.16, 0.20, 0.25, 0.30} delta, long put nearest (short - 0.10), i.e. -{0.06, 0.10, 0.15, 0.20}. The four
          spreads share a ticker-date, so every comparison is PAIRED. 50% take at the real closing cost (PRIMARY), else
          intrinsic at expiry; hold-to-expiry reported. Return = P&L / max risk.
VOL REGIME the VIX close on the entry day as its percentile over the trailing 252 sessions (no look-ahead;
          data/cache/vix_daily_long.parquet): LOW < 33rd, MID 33-67th, HIGH > 67th.
PRIMARY   the interaction I = [R(0.16) - R(0.25) | LOW] - [R(0.16) - R(0.25) | HIGH], pooled, after costs, 50% take.
          Paired per ticker-date, then averaged by month (month-clustered); I is estimated as the difference of the
          two month-clustered means, SE from the two independent month sets. The claim predicts I > 0. Bar: t >= 3
          (one primary test), both halves (2019-01) the same sign, a majority of years the same sign (per year I, where
          both regimes occur).
          The two simple effects are reported: the claim needs R(0.16) - R(0.25) > 0 in LOW and < 0 in HIGH.
REPORTED  the full grid (4 deltas x 3 regimes: mean net, gross, win rate, n) for pooled / ETFs / names; the same for hold.
          Descriptive, not bar-bearing: the best delta per regime (a best-of-4 pick; no claim is made from it).
NOT TESTED "further out in time when vol is low": the cached pull stops at 35 DTE. Stated here so a null on delta isn't
          read as a null on tenor.
PRIOR     low-moderate. Vol level matters; a delta x vol interaction is plausible (the skew steepens in low vol, making
          far-OTM puts relatively richer), but it's a second-order effect and the pooled data is noisy.

Usage: PYTHONPATH=src:. python run_put_delta_by_vol.py (log -> data/studies/logs/put_delta_by_vol.log); run on Fargate
       via services/study-runner/ (WORKERS env).
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
LOG = REPO / "data/studies/logs/put_delta_by_vol.log"
DELTAS = [0.16, 0.20, 0.25, 0.30]


def work(tk: str):
    V3 = pd.concat([pd.read_parquet(L.CACHE / f"v3_{y}.parquet", filters=[("ticker", "==", tk)]) for y in range(L.Y0, L.Y1 + 1)])
    V3 = V3[V3.trade_date <= L.END]
    cs = pd.read_parquet(REPO / "data/cache/chain_spot/chain_spot_daily.parquet", columns=["ticker", "trade_date", "spot"],
                         filters=[("ticker", "==", tk)])
    cs["trade_date"] = pd.to_datetime(cs.trade_date)
    spot = cs.set_index("trade_date").spot.sort_index()
    ch = L.Chain(V3)
    exps = np.array(sorted(V3.expiry.unique()))
    rows = []
    for f in [x for x in ch.dates if pd.Timestamp(x).dayofweek == 4]:
        f = pd.Timestamp(f)
        dte = np.array([(pd.Timestamp(e) - f).days for e in exps])
        ok = np.flatnonzero((dte >= 14) & (dte <= 28))
        if not len(ok) or f not in spot.index:
            continue
        exp = pd.Timestamp(exps[ok[np.argmin(np.abs(dte[ok] - 20))]])
        row = dict(ticker=tk, entry=f, expiry=exp)
        for d in DELTAS:
            for take in (True, False):
                for cost in (True, False):
                    r = L.spread_trade(ch, spot, f, exp, "P", -d, -(d - 0.10), take, cost)
                    row[f"r{int(d * 100)}_{'take' if take else 'hold'}_{'net' if cost else 'gross'}"] = r[0] if r else np.nan
        rows.append(row)
    return rows


def main():
    with Pool(int(os.environ.get("WORKERS", "4"))) as p:
        T = pd.DataFrame([r for rows in p.map(work, L.TICKERS) for r in rows])
    v = pd.read_parquet(REPO / "data/cache/vix_daily_long.parquet")
    v["trade_date"] = pd.to_datetime(v.trade_date)
    v = v.set_index("trade_date").vix_close.sort_index()
    vp = v.rolling(252, min_periods=200).apply(lambda x: (x[:-1] < x[-1]).mean() * 100, raw=True)
    T["vix_pct"] = vp.reindex(T.entry).values
    T["regime"] = pd.cut(T.vix_pct, [-1, 33, 67, 101], labels=["LOW", "MID", "HIGH"])
    T["month"] = T.entry.dt.to_period("M")
    T.to_parquet(REPO / "data/studies/logs/put_delta_by_vol_trades.parquet")
    out = ["# Short-put delta x volatility regime (pre-registration in the docstring)",
           f"ticker-Fridays {len(T)}; regimes: " + ", ".join(f"{k} {n}" for k, n in T.regime.value_counts().sort_index().items())]
    # grid
    for grp, G in (("pooled", T), ("ETFs", T[T.ticker.isin(L.ETFS)]), ("names", T[T.ticker.isin(L.NAMES)])):
        for ex in ("take", "hold"):
            lines = []
            for reg in ("LOW", "MID", "HIGH"):
                g = G[G.regime == reg]
                cells = " | ".join(f"{int(d*100)}d {g[f'r{int(d*100)}_{ex}_net'].mean()*100:+6.2f} (gross {g[f'r{int(d*100)}_{ex}_gross'].mean()*100:+.2f}, "
                                   f"win {(g[f'r{int(d*100)}_{ex}_net'] > 0).mean():.0%})" for d in DELTAS)
                lines.append(f"  {reg:4s} n {len(g):5d}: {cells}")
            out.append(f"\n## {grp} / {ex} -- net %/trade on risk by short delta")
            out += lines
    # primary interaction
    def simple(G, reg, ex="take"):
        g = G[G.regime == reg]
        d = (g[f"r16_{ex}_net"] - g[f"r25_{ex}_net"]) * 100
        m = d.groupby(g.month).mean().dropna()
        return m
    res = []
    for grp, G in (("pooled", T), ("ETFs", T[T.ticker.isin(L.ETFS)]), ("names", T[T.ticker.isin(L.NAMES)])):
        for ex in ("take", "hold"):
            lo, hi = simple(G, "LOW", ex), simple(G, "HIGH", ex)
            I = lo.mean() - hi.mean(); se = np.sqrt(lo.var(ddof=1) / len(lo) + hi.var(ddof=1) / len(hi))
            t = I / se
            h1 = lo[lo.index < L.SPLIT].mean() - hi[hi.index < L.SPLIT].mean()
            h2 = lo[lo.index >= L.SPLIT].mean() - hi[hi.index >= L.SPLIT].mean()
            ly, hy = lo.groupby(lo.index.year).mean(), hi.groupby(hi.index.year).mean()
            yi = (ly - hy).dropna(); same = int((np.sign(yi) == np.sign(I)).sum())
            tl = lo.mean() / (lo.std(ddof=1) / np.sqrt(len(lo))); th = hi.mean() / (hi.std(ddof=1) / np.sqrt(len(hi)))
            ok = t >= 3 and h1 > 0 and h2 > 0 and same > len(yi) / 2
            res.append(dict(group=grp, exit=ex, I=I, t=t, h1=h1, h2=h2, yrs=f"{same}/{len(yi)}", low_16m25=lo.mean(), t_low=tl,
                            high_16m25=hi.mean(), t_high=th, PASS=ok, primary=grp == "pooled" and ex == "take"))
    D = pd.DataFrame(res)
    out.append("\n## INTERACTION I = [R16 - R25 | LOW] - [R16 - R25 | HIGH] (pp per trade, month-clustered)")
    out.append(D.round(2).to_string(index=False))
    p = D[D.primary].iloc[0]
    claim = p.low_16m25 > 0 and p.high_16m25 < 0
    out.append(f"\nVERDICT (PRIMARY pooled/take): I {p.I:+.2f}pp t {p.t:+.2f} halves {p.h1:+.2f}/{p.h2:+.2f} yrs {p.yrs} -> "
               f"{'PASS' if p.PASS else 'fail'}; simple effects: LOW 16-25 {p.low_16m25:+.2f} (t {p.t_low:+.2f}), HIGH 16-25 "
               f"{p.high_16m25:+.2f} (t {p.t_high:+.2f}) -> the claimed sign pattern {'HOLDS' if claim else 'does NOT hold'}")
    D.to_csv(REPO / "data/studies/put_delta_by_vol_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
