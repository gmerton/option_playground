#!/usr/bin/env python3
"""
[WL-3b] Flanders 5-day breadth deferral (pre-registered 2026-09-23; spec copied from
data/usic_champions/videos/2025-12-22_ecmHzX-6x8g/notes.md "Not tested, could be" BEFORE running).

Claim (Christian Flanders, USIC, 00:18:20): when ~80%+ of stocks close above their 5-day MA, the tape is stretched --
wait before entering new breakouts.
Signal (strictly prior): b5(t) = share of the liquid-eligible panel whose close > its own 5-day SMA at the close of t.
Thresholds: b5 >= 0.80 (PRIMARY), >= 0.90.
Trades: precision-tier house breakouts (run_precision_tier_control.build), close entry, stop = breakout day's low judged
  on the close, 20-EMA close trail, max 60 sessions, 0.10% slippage a side. METRIC = % per trade (the two arms enter at
  different prices against the same stop level, so R would move with the denominator); R (cap 20) reported second.
Arms on b5 >= thr breakout days:
  A enter at the breakout close.
  B same name, defer to the first close within 10 sessions where b5 < 0.60 AND close <= breakout level + 1 ADR (level =
    prior 20d high), and the stop was not closed through first. Otherwise ABANDONED: counted at 0% and reported
    separately (runaways never come back -- the retrace-entry survivorship trap).
PRIMARY: paired A - B per trade (holds the name fixed, moves only the clock), t clustered by date, both halves the same
  sign, per-year shown.
Readings: (2) gate-as-filter: breakouts on b5 >= thr days vs b5 < thr days, ADR-decile-matched (different dates by
  construction, so this is a date-level comparison); (3) date-level: equal-weight panel return +1 / +5 sessions after
  b5 >= thr vs all days, in ADR units. Also: rank correlation of b5 with the activity gate's cnt5_pct.
Bar: |t| >= 3 on the primary; 2 thresholds x 2 readings -> Sidak k = 4 (|t| ~ 2.8 for non-primary cells).
Prior low-moderate: breadth > 20 EMA did nothing (t -1.23); the correlated activity count points the other way.

Run: PYTHONPATH=src .venv/bin/python3 run_breadth_deferral.py   (log -> data/studies/logs/breadth_deferral.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from lib.studies.pattern_test import SLIP
import run_precision_tier_control as pc

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/breadth_deferral.log"
START, SPLIT, CAP, WAIT = "2019-10-01", "2023-01-01", 60, 10


def run_trade(C, E, j, i, stop) -> float:
    """% return entering at close i; exit on first close < EMA20 or < stop, cap CAP."""
    entry = C[i, j] * (1 + SLIP)
    px = np.nan
    for k in range(i + 1, min(i + 1 + CAP, len(C))):
        c = C[k, j]
        if not np.isfinite(c):
            continue
        if c < stop or (np.isfinite(E[k, j]) and c < E[k, j]):
            px = c
            break
    if not np.isfinite(px):
        px = C[min(i + CAP, len(C) - 1), j]
    return 100 * (px * (1 - SLIP) / entry - 1)


def tstat(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def main():
    P, brk, prec = pc.build()
    C, L, E = P.close.values, P.low.values, P.ema20.values
    elig = P.elig.fillna(False)
    above5 = (P.close > P.close.rolling(5).mean()) & elig
    b5 = above5.sum(axis=1) / elig.sum(axis=1).replace(0, np.nan)
    b5v = b5.values
    lvl = P.high.shift(1).rolling(20).max().values
    adrpx = (P.adr / 100 * P.close).values
    idx = P.close.index
    print(f"# Breadth deferral [WL-3b] -- b5 median {b5[b5.index >= START].median():.2f}, share of days >= 0.80: "
          f"{(b5[b5.index >= START] >= 0.8).mean():.1%}, >= 0.90: {(b5[b5.index >= START] >= 0.9).mean():.1%}")
    m = prec.copy(); m[m.index < START] = False
    rows = []
    for i, j in zip(*np.where(m.values)):
        if i + 2 >= len(idx) or not np.isfinite(C[i, j]):
            continue
        stop = L[i, j]
        a = run_trade(C, E, j, i, stop)
        stop_pct = max((C[i, j] - stop) / C[i, j], 0.02) * 100
        b, bstat, bi = 0.0, "abandoned", None
        for k in range(i + 1, min(i + 1 + WAIT, len(idx))):
            c = C[k, j]
            if not np.isfinite(c):
                continue
            if c < stop:
                bstat = "stopped before entry"; break
            if b5v[k] < 0.60 and c <= lvl[i, j] + adrpx[i, j]:
                b, bstat, bi = run_trade(C, E, j, k, stop), "entered", k
                break
        rows.append(dict(date=idx[i], sym=P.close.columns[j], b5=b5v[i], adr=P.adr.values[i, j], A=a,
                         A_R=float(np.clip(a / stop_pct, -20, 20)), B=b, B_status=bstat,
                         B_R=float(np.clip(b / stop_pct, -20, 20)) if bi is not None else 0.0))
    T = pd.DataFrame(rows)
    print(f"precision-tier breakouts {len(T):,}; mean {T.A.mean():+.2f}%")
    out = {}
    for thr in (0.80, 0.90):
        S = T[T.b5 >= thr].copy()
        S["diff"] = S.A - S.B
        dd = S.groupby("date")["diff"].mean()
        tag = "PRIMARY" if thr == 0.80 else "secondary"
        print(f"\n## {tag}: b5 >= {thr:.2f} -- {len(S)} breakouts on {S.date.nunique()} dates")
        print(S.B_status.value_counts().to_string())
        ent = S[S.B_status == "entered"]
        print(f"A (enter now) {S.A.mean():+.2f}% | B (defer) {S.B.mean():+.2f}% incl. abandoned at 0 | "
              f"A - B {dd.mean():+.2f}pp t {tstat(dd):+.2f} | halves {dd[dd.index < SPLIT].mean():+.2f}/"
              f"{dd[dd.index >= SPLIT].mean():+.2f}")
        print(f"  entered-only: A {ent.A.mean():+.2f}% vs B {ent.B.mean():+.2f}% (n {len(ent)}); abandoned names' A "
              f"{S[S.B_status == 'abandoned'].A.mean():+.2f}% (n {(S.B_status == 'abandoned').sum()}); "
              f"stopped-before-entry names' A {S[S.B_status == 'stopped before entry'].A.mean():+.2f}%")
        dR = S.groupby("date").apply(lambda g: (g.A_R - g.B_R).mean())
        print(f"  R (cap 20): A {S.A_R.mean():+.3f} vs B {S.B_R.mean():+.3f} | A - B t {tstat(dR):+.2f}")
        yr = dd.groupby(dd.index.year).agg(["size", "mean"]).round(2)
        print("  per year (A - B, pp):\n" + yr.T.to_string())
        # (2) gate-as-filter, ADR-decile matched
        T["dec"] = pd.qcut(T.adr, 10, labels=False, duplicates="drop")
        hi, lo = T[T.b5 >= thr], T[T.b5 < thr]
        w = hi.dec.value_counts(normalize=True)
        lo_m = sum(w.get(d, 0) * lo[lo.dec == d].A.mean() for d in w.index)
        dhi = hi.groupby("date").A.mean()
        dlo = lo.groupby("date").A.mean()
        tw = stats.ttest_ind(dhi, dlo, equal_var=False).statistic
        print(f"  (2) filter: breakouts on b5 >= {thr:.2f} days {hi.A.mean():+.2f}% vs ADR-matched other days "
              f"{lo_m:+.2f}% | date-level Welch t {tw:+.2f}")
        # (3) date-level forward panel returns in ADR units
        fr1 = (P.close.shift(-1) / P.close - 1) * 100 / P.adr
        fr5 = (P.close.shift(-5) / P.close - 1) * 100 / P.adr
        e1 = fr1.where(elig).mean(axis=1); e5 = fr5.where(elig).mean(axis=1)
        win = b5.index >= START
        for lab, e in (("+1", e1), ("+5", e5)):
            x = e[win & (b5 >= thr).values].dropna(); y = e[win].dropna()
            print(f"  (3) panel {lab} sessions, ADR units: after b5 >= {thr:.2f} {x.mean():+.3f} (n {len(x)}) vs all days "
                  f"{y.mean():+.3f} | Welch t {stats.ttest_ind(x, y, equal_var=False).statistic:+.2f}")
        out[thr] = (dd, S)
    act = pd.read_csv(REPO / "data/studies/breakout_activity_gate_2026-09-22.csv", parse_dates=["date"])
    a = act.groupby("date").cnt5_pct.first()
    j = pd.concat([b5.rename("b5"), a.rename("cnt5_pct")], axis=1).dropna()
    print(f"\nrank corr b5 vs activity cnt5_pct: {stats.spearmanr(j.b5, j.cnt5_pct).statistic:+.3f} (n {len(j)} dates)")
    T.to_csv(REPO / "data/studies/logs/breadth_deferral_trades.csv", index=False)
    return out


if __name__ == "__main__":
    real = sys.stdout
    LOG.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
