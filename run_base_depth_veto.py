#!/usr/bin/env python3
"""
Base depth as a VETO on the house breakout (pre-registered 2026-09-30, committed BEFORE the first run).

Origin: Gabe on COHR (35% off its June high) -> "have we established a base is a positive signal?" -> no, five base
definitions NULL (VCP, Wedge Pop, RMV, EP base-break, beaten-down long base). The O'Neil claim that bases deeper than
~33% fail is UNTOUCHED in TEST_INDEX. What is new vs the ledger: the 52wk-high gate (precision ablation 9/24) and the
beaten-down test (9/24) condition on where price IS relative to the high; this conditions on how deep the prior
CORRECTION went -- a deep cup that has recovered to near the high is deep here and near-the-high there.

Universe: data/cache/liquid_panel_2009.parquet, house breakout = close > prior 20-day high, ADR20 >= 3%, eligible
  (ADDV >= $50M, px >= $5), 2010-01-01 -> panel end (last ~60 sessions truncated by the hold). Survivorship caveat:
  panel names are those liquid in the build, not a point-in-time index.
Depth (no look-ahead, bars <= t-1 only): peak = max high over t-252 .. t-1 (date p); trough = min low over p .. t-1;
  depth = 1 - trough / peak. Also recorded: dist = 1 - close_t / peak (how far below the peak the breakout fires).
Trade (identical to the RMV / VCP tests): enter at the breakout CLOSE (+0.10% slip), stop = breakout-day low judged on
  the close, exit on first close < EMA20, max 60 sessions, -0.10% slip. METRIC = % return per trade (R second).

PRIMARY (one cell, direction declared): DEEP (depth > 33%) minus NOT-DEEP (depth <= 33%), date-matched cross-name:
  per date with >= 1 of each, diff_d = mean(DEEP %) - mean(NOT-DEEP %); t on date means. HYPOTHESIS: diff < 0.
Bar: t <= -3, both halves (split 2018-01-01) negative, per-year shown (a back-half regime must not carry it).
Pre-declared confound checks, each must hold the sign for a VETO verdict:
  (a) ADR-tercile-matched within date (deep bases are mechanically high-vol names);
  (b) within dist-from-peak terciles (depth correlates with being far below the peak, which is the already-NULL
      52wk-high axis -- if the effect lives only in dist, it is that axis again, not depth);
  (c) O'Neil's own form: breakouts with dist <= 10% only (the cup has recovered to near the pivot).
Verdicts: t <= -3 + halves + (a)(b) hold -> ADOPT as a veto candidate (then a freeze-forward before production).
  |t| < 3 -> NULL: depth is not disqualifying. t >= +3 -> INVERTED (deep bases do BETTER).
Exploratory (Sidak k = 6, |t| ~ 2.9, no verdict of their own): 3 buckets <15 / 15-33 / >33 dose response;
  DEEP > 50%; depth in ADR units (top vs bottom tercile, scale-free per house convention); 126-day lookback;
  the COHR cell (depth > 33% AND dist >= 20%); held-the-level share DEEP vs NOT-DEEP.
Local, not cloud: cached panel, minutes of CPU.

Run: PYTHONPATH=src .venv/bin/python3 run_base_depth_veto.py   (log -> data/studies/logs/base_depth_veto.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.pattern_test import load_panel
import run_vcp_damped_sine as V
from run_rmv_gate import tstat

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/base_depth_veto.log"
START, SPLIT, LOOK = "2010-01-01", "2018-01-01", 252


def trades(P, look: int = LOOK) -> pd.DataFrame:
    lvl = P.high.shift(1).rolling(20).max()
    hb = ((P.close > lvl) & (P.adr >= 3) & P.elig).fillna(False)
    hb[hb.index < START] = False
    C, H, L, A = P.close.values, P.high.values, P.low.values, P.adr.values
    rows = []
    for i, j in zip(*np.where(hb.values)):
        if i < look:
            continue
        h = H[i - look:i, j]
        if np.isnan(h).mean() > 0.1:
            continue
        p = int(np.nanargmax(h))
        peak = h[p]
        trough = np.nanmin(L[i - look + p:i, j])
        r = V.pct_trade(P, j, i, L[i, j], lvl.values[i, j])
        if r is None:
            continue
        stop_pct = max((C[i, j] - L[i, j]) / C[i, j], 0.02) * 100
        d126 = np.nan
        if look >= 126:
            h2 = H[i - 126:i, j]
            p2 = int(np.nanargmax(h2))
            d126 = 1 - np.nanmin(L[i - 126 + p2:i, j]) / h2[p2]
        rows.append(dict(date=hb.index[i], sym=hb.columns[j], ret=r[0], held=r[1],
                         R=float(np.clip(r[0] / stop_pct, -20, 20)), adr=A[i, j],
                         depth=1 - trough / peak, dist=1 - C[i, j] / peak, d126=d126))
    T = pd.DataFrame(rows)
    T["depth_adr"] = 100 * T.depth / T.adr
    return T


def dm(T: pd.DataFrame, gate, col: str = "ret", by: list[str] | None = None) -> dict:
    keys = ["date"] + (by or [])
    g = T.assign(g=np.asarray(gate)).groupby(keys + ["g"])[col].mean().unstack("g")
    if True not in g or False not in g:
        return dict(n_dates=0)
    d = (g[True] - g[False]).dropna()
    dd = d.groupby(level=0).mean()
    return dict(n_dates=len(dd), a=g[True].loc[d.index].mean(), b=g[False].loc[d.index].mean(), diff=dd.mean(),
                t=tstat(dd), h1=dd[dd.index < SPLIT].mean(), h2=dd[dd.index >= SPLIT].mean(), _dd=dd)


def fmt(r: dict, a="DEEP", b="not") -> str:
    if not r.get("n_dates"):
        return "no paired dates"
    return (f"dates {r['n_dates']:4d} | {a} {r['a']:+.2f} vs {b} {r['b']:+.2f} | diff {r['diff']:+.2f} "
            f"t {r['t']:+.2f} | halves {r['h1']:+.2f}/{r['h2']:+.2f}")


def main():
    P = load_panel("data/cache/liquid_panel_2009.parquet")
    T = trades(P)
    deep = (T.depth > 0.33).values
    print(f"# Base depth veto -- {len(T):,} house breakouts, {T.sym.nunique()} names, "
          f"{T.date.min().date()} -> {T.date.max().date()}; all-breakout mean {T.ret.mean():+.2f}%")
    print("depth quantiles (10/25/50/75/90): " + " / ".join(f"{q:.0%}" for q in T.depth.quantile([.1, .25, .5, .75, .9])))
    print(f"DEEP (>33%) share {deep.mean():.1%} | median dist-from-peak DEEP {T.dist[deep].median():.0%} "
          f"vs not {T.dist[~deep].median():.0%} | median ADR DEEP {T.adr[deep].median():.1f} vs {T.adr[~deep].median():.1f}")

    print("\n## PRIMARY: DEEP (>33%) - NOT-DEEP, same date, other names, % per trade (hypothesis < 0)")
    P1 = dm(T, deep)
    print(fmt(P1))
    yr = P1["_dd"].groupby(P1["_dd"].index.year).agg(["size", "mean"]).round(2)
    print("per year:\n" + yr.T.to_string())
    RR = dm(T, deep, "R")
    print(f"R: DEEP {RR['a']:+.3f} vs not {RR['b']:+.3f} | diff {RR['diff']:+.3f} t {RR['t']:+.2f}")

    print("\n## pre-declared confound checks")
    T["adr_terc"] = T.groupby("date").adr.transform(
        lambda s: pd.qcut(s.rank(method="first"), 3, labels=False) if len(s) >= 3 else 0)
    print("(a) ADR-tercile-matched within date: " + fmt(dm(T, deep, by=["adr_terc"])))
    T["dist_terc"] = pd.qcut(T.dist, 3, labels=["near peak", "mid", "far below"])
    print("(b) within dist-from-peak terciles:")
    for k in ("near peak", "mid", "far below"):
        m = (T.dist_terc == k).values
        lo, hi = T.dist[m].min(), T.dist[m].max()
        print(f"    {k:9s} (dist {lo:.0%}-{hi:.0%}, DEEP share {deep[m].mean():.0%}) " + fmt(dm(T[m], deep[m])))
    m = (T.dist <= 0.10).values
    print(f"(c) O'Neil form, dist <= 10% (n {m.sum():,}, DEEP share {deep[m].mean():.1%}): " + fmt(dm(T[m], deep[m])))

    print("\n## exploratory (Sidak k = 6, |t| ~ 2.9; no verdict of their own)")
    b = pd.cut(T.depth, [-1, .15, .33, 9], labels=["<15%", "15-33%", ">33%"])
    print("  dose response (pooled means, not date-matched): " +
          " | ".join(f"{k} n {int((b == k).sum()):,} mean {T.ret[b == k].mean():+.2f}% med {T.ret[b == k].median():+.2f}"
                     for k in b.cat.categories))
    print("  15-33% vs <15%:           " + fmt(dm(T[(b != '>33%').values], (b[b != '>33%'] == '15-33%').values), "15-33", "<15"))
    print("  DEEP > 50%:               " + fmt(dm(T, (T.depth > 0.5).values), ">50%"))
    q = T.groupby("date").depth_adr.transform(lambda s: s.rank(pct=True))
    ex = (q >= 2 / 3) | (q <= 1 / 3)
    print("  depth in ADR, top vs bottom tercile (within date): " + fmt(dm(T[ex.values], (q[ex] >= 2 / 3).values), "top", "bottom"))
    print("  126-day lookback, >33%:   " + fmt(dm(T.dropna(subset=["d126"]), (T.d126.dropna() > 0.33).values)))
    cohr = ((T.depth > 0.33) & (T.dist >= 0.20)).values
    print(f"  COHR cell (depth>33% & dist>=20%, share {cohr.mean():.1%}): " + fmt(dm(T, cohr), "cell", "rest"))
    H = dm(T, deep, "held")
    print(f"  held-the-level share: DEEP {100 * H['a']:.1f}% vs not {100 * H['b']:.1f}% | diff {100 * H['diff']:+.1f}pp "
          f"t {H['t']:+.2f}")
    T.to_csv(REPO / "data/studies/logs/base_depth_veto_trades.csv", index=False)
    return P1


if __name__ == "__main__":
    real = sys.stdout
    LOG.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
