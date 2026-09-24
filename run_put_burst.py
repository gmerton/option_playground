#!/usr/bin/env python3
"""
Options flow as a SHORT / VETO signal: do bursts of short-dated OTM PUT buying precede underperformance?
(pre-registered 2026-09-24, before the first run; Gabe's "other ideas" #3. The mirror of [A1] call bursts, which was
NULL; the literature version is Pan & Poteshman 2006: a high put share of option volume predicts lower returns.)

DESIGN (identical to run_call_burst.py except the side, so the two rows are comparable)
  data      silver.options_flow_daily, liquid names (cached data/cache/options_flow_liquid.parquet), 2010-02 -> 2026-04.
  PUT BURST on day t: put_vol_otm30 >= 3 x its own prior-20-session mean, >= 1,000 contracts, >= 2 x call_vol_otm30;
            eligible; first burst per name in any 10-session window.
  entry     next OPEN (+10 bps); exit the close at +h (-10 bps).
  control   same-date non-burst names in the same day-t return quintile x ADR tercile (up to 20), so a burst on a
            down day is compared with other down-day names -- the flow must add something beyond the price move.
  PRIMARY   +5 sessions, burst - control, t clustered by date. Bar |t| >= 3, both halves (2018-01) the same sign.
            Hypothesis: NEGATIVE (informed or hedging put demand precedes weakness) -> usable as a long-book veto.
  SECONDARY (exploratory) +1 / +10 / +20; PP-RATIO: put share of total option volume (put_vol / (put_vol + call_vol))
            in the top 5% of the name's own trailing 252-session distribution with >= 500 puts traded, same control;
            put bursts on names in an uptrend (close > 50 SMA) -- the case where a veto would matter to the long book.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_put_burst.py   (log -> data/studies/logs/put_burst.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.pattern_test import load_panel, SLIP
from run_call_burst import pull_flow, tstat, PANEL, START, END, SPLIT

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/put_burst.log"
RNG = np.random.default_rng(20260924)


def thin(mask: np.ndarray, gap: int = 10) -> np.ndarray:
    bv = mask.copy()
    for j in range(bv.shape[1]):
        last = -99
        for i in np.flatnonzero(bv[:, j]):
            if i - last < gap:
                bv[i, j] = False
            else:
                last = i
    return bv


def score(bv, P, label, out, horizons=(5, 1, 10, 20), extra=None):
    idx, cols = P.close.index, P.close.columns
    O, C = P.open.values, P.close.values
    n = len(idx)

    def fwd(i, j, h):
        if i + h >= n or not np.isfinite(O[i + 1, j]) or not np.isfinite(C[i + h, j]):
            return np.nan
        return 100 * (C[i + h, j] * (1 - SLIP) / (O[i + 1, j] * (1 + SLIP)) - 1)

    r1 = C / np.roll(C, 1, axis=0) - 1; r1[0] = np.nan
    elig = P.elig.fillna(False).values & np.isfinite(r1)
    adr = P.adr.values
    rows = []
    for i in np.flatnonzero(bv.any(axis=1)):
        e = elig[i]
        if e.sum() < 50:
            continue
        rq = pd.qcut(pd.Series(r1[i, e]), 5, labels=False, duplicates="drop").values
        aq = pd.qcut(pd.Series(adr[i, e]), 3, labels=False, duplicates="drop").values
        names = np.flatnonzero(e)
        cell = dict(zip(names, zip(rq, aq)))
        for j in np.flatnonzero(bv[i]):
            if j not in cell:
                continue
            ctl = [k for k in names if k != j and not bv[i, k] and cell[k] == cell[j]]
            if len(ctl) < 3:
                continue
            ctl = RNG.choice(ctl, size=min(20, len(ctl)), replace=False)
            rec = dict(date=idx[i], sym=cols[j], day_ret=100 * r1[i, j],
                       uptrend=bool(extra[i, j]) if extra is not None else None)
            for h in horizons:
                rec[f"b{h}"] = fwd(i, j, h)
                rec[f"c{h}"] = np.nanmean([fwd(i, int(k), h) for k in ctl])
            rows.append(rec)
    T = pd.DataFrame(rows)
    out.append(f"\n# {label}: {len(T):,} events, {T.sym.nunique()} names, {T.date.min().date()} -> {T.date.max().date()}; "
               f"median day-t return {T.day_ret.median():+.2f}%")
    res = {}
    for h in horizons:
        d = (T[f"b{h}"] - T[f"c{h}"]); dd = d.groupby(T.date).mean(); hh = dd.index < SPLIT
        res[h] = (dd.mean(), tstat(dd), dd[hh].mean(), dd[~hh].mean())
        out.append(f"  +{h:2d}: event {T[f'b{h}'].mean():+.3f}% vs matched control {T[f'c{h}'].mean():+.3f}% | diff "
                   f"{dd.mean():+.3f}pp t {tstat(dd):+.2f} | halves {dd[hh].mean():+.3f} / {dd[~hh].mean():+.3f}")
    if extra is not None:
        for lab, m in (("uptrend (close > 50 SMA)", T.uptrend == True), ("not uptrend", T.uptrend == False)):  # noqa: E712
            x = (T.b5 - T.c5)[m].groupby(T.date[m]).mean()
            out.append(f"  +5 {lab:26s} n {int(m.sum()):6,} diff {x.mean():+.3f}pp t {tstat(x):+.2f}")
    return T, res


def main():
    P = load_panel(PANEL)
    idx, cols = P.close.index, P.close.columns
    f = pull_flow(list(cols))
    pv = lambda c: f.pivot(index="trade_date", columns="ticker", values=c).reindex(index=idx, columns=cols)
    potm, cotm, put, call = pv("put_vol_otm30"), pv("call_vol_otm30"), pv("put_vol"), pv("call_vol")
    elig = P.elig.fillna(False)
    win = (idx >= START) & (idx <= END)
    up = (P.close > P.close.rolling(50).mean()).values
    out = ["# Options flow as a short / veto signal (pre-registration in the docstring)"]

    base = potm.shift(1).rolling(20, min_periods=15).mean()
    burst = ((potm >= 3 * base) & (potm >= 1000) & (potm >= 2 * cotm.fillna(0)) & elig).values & win[:, None]
    T, res = score(thin(burst), P, "PUT BURSTS (short-dated OTM put buying)", out, extra=up)
    m, t, h1, h2 = res[5]
    ok = abs(t) >= 3 and np.sign(h1) == np.sign(h2)
    out.append(f"  PRIMARY +5 bar (|t| >= 3, halves same sign): {'PASS' if ok else 'FAIL'}"
               + (f" -> {'NEGATIVE: a veto candidate' if m < 0 else 'POSITIVE'}" if ok else ""))
    T.to_csv(REPO / "data/studies/logs/put_burst_events.csv", index=False)

    share = put / (put + call).replace(0, np.nan)
    q95 = share.shift(1).rolling(252, min_periods=200).quantile(0.95)
    pp = ((share >= q95) & (put >= 500) & elig).values & win[:, None]
    score(thin(pp), P, "PP-RATIO (put share of volume in its own top 5%, >= 500 puts) -- secondary", out, extra=up)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
