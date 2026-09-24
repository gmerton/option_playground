#!/usr/bin/env python3
"""
Undervalued idea #1: an EPS BEAT in a BEATEN-DOWN name (pre-registered 2026-09-24, before the first run; Gabe: "there
are certainly many cases where it's better to buy undervalued stocks").

WHAT IS ALREADY ANSWERED: PEAD on the actual surprise NULL (pead 2026-09-20, all names, hold 10); EP out of a long base
NULL; crash-leader deep-drawdown buying = regime bet; beaten-down long-base breakout NULL (today). NEW AXIS: the surprise
CONDITIONED on the name being beaten down -- the market's low expectations meeting good news -- at a swing/position
horizon, against controls that isolate each half of the idea.

DESIGN
  events    data/cache/earnings_yf.parquet (surprise_pct, AMC/BMO) on liquid_panel_2009, eligible names, 2010 ->.
            Reaction session = the report session if BMO, the next session if AMC.
  beaten    the close BEFORE the reaction session <= 0.70 x its prior 252-session high.
  beat      surprise_pct >= +5%;  miss = surprise_pct <= -5%.
  entry     the CLOSE of the reaction session (after the market has reacted -- no gap capture).
  outcome   forward return over 20 / 60 sessions minus the same-date mean of eligible names in the same ADR band
            (<2, 2-3, 3-4, 4-6, 6+): ADR-matched excess. No stop (a state test).
  cells     BB beaten + beat (the idea) | BM beaten + miss (does the BEAT matter?) | NB not beaten + beat (does
            BEATEN matter?).
  PRIMARY   60-session ADR-matched excess of BB, t clustered by reaction date. Bar: t >= 3, both halves (2018-01) > 0,
            AND BB - BM > 0 and BB - NB > 0 (each difference t reported; the idea needs both halves of it).
  SECONDARY (exploratory) 20 sessions; BB split by the reaction (reaction-day return > 0 vs <= 0: "good news, bad
            reaction" is the classic undervaluation story); deeper cut (<= 0.50 x high); per year; market breadth
            at entry (< 40% of names above the 50 SMA vs >= 40).
  caveat    survivor panel (names liquid as of 2026): beaten-down names that later failed are under-represented,
            which FLATTERS BB. A pass needs that read against it.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_beaten_down_beats.py   (log -> data/studies/logs/beaten_down_beats.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/beaten_down_beats.log"
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]
SPLIT = pd.Timestamp("2018-01-01")


def tstat_by(x: pd.Series, g: pd.Series) -> float:
    m = pd.Series(x.values, index=g.values).groupby(level=0).mean()
    return float(m.mean() / m.std(ddof=1) * sqrt(len(m))) if len(m) > 2 else np.nan


def main() -> None:
    P = pt.load_panel("data/cache/liquid_panel_2009.parquet")
    n = P.close.notna().sum(axis=1)
    keep = n >= 0.5 * n.rolling(20, min_periods=5).median().shift(1).fillna(n)
    C, H, A, E = P.close.loc[keep], P.high.loc[keep], P.adr.loc[keep], P.elig.loc[keep].fillna(False)
    idx = C.index
    hi252 = H.shift(1).rolling(252, min_periods=200).max()
    sma50 = C.rolling(50).mean()
    breadth = 100 * ((C > sma50) & E).sum(axis=1) / (E & sma50.notna()).sum(axis=1)
    F = {h: ((C.shift(-h) / C - 1) * 100) for h in (20, 60)}
    bench = {}
    for h, Fh in F.items():
        b = np.full(Fh.shape, np.nan); Av, Ev, Fv = A.values, E.values, Fh.values
        for lo, hi in BANDS:
            mk = Ev & (Av >= lo) & (Av < hi) & np.isfinite(Fv)
            s = np.where(mk, Fv, 0).sum(axis=1); c = mk.sum(axis=1)
            m = np.where(c >= 10, s / np.maximum(c, 1), np.nan)
            b = np.where((Av >= lo) & (Av < hi), m[:, None], b)
        bench[h] = b

    ev = pd.read_parquet(REPO / "data/cache/earnings_yf.parquet")
    ev["session"] = pd.to_datetime(ev.session)
    ev = ev[ev.ticker.isin(C.columns) & ev.surprise_pct.notna() & (ev.session >= "2010-06-01")]
    col = {t: k for k, t in enumerate(C.columns)}
    Cv, Ev_, hv = C.values, E.values, hi252.values
    rows = []
    for r in ev.itertuples(index=False):
        i0 = idx.searchsorted(r.session)
        i = i0 if r.timing == "BMO" else i0 + 1
        if i < 1 or i + 60 >= len(idx):
            continue
        j = col[r.ticker]
        if not Ev_[i, j] or not np.isfinite(Cv[i, j]) or not np.isfinite(hv[i - 1, j]):
            continue
        dd = Cv[i - 1, j] / hv[i - 1, j]
        rx = Cv[i, j] / Cv[i - 1, j] - 1
        rows.append(dict(ticker=r.ticker, date=idx[i], surp=r.surprise_pct, dd=dd, rx=100 * rx,
                         breadth=breadth.iloc[i],
                         ex20=F[20].values[i, j] - bench[20][i, j], ex60=F[60].values[i, j] - bench[60][i, j]))
    R = pd.DataFrame(rows).dropna(subset=["ex60"])
    R["beaten"] = R.dd <= 0.70
    BB = R[R.beaten & (R.surp >= 5)]; BM = R[R.beaten & (R.surp <= -5)]; NB = R[~R.beaten & (R.surp >= 5)]

    out = []; pr = out.append
    pr("# Undervalued #1: EPS beat in a beaten-down name (pre-registration in the docstring)\n")
    pr(f"events with a scored reaction: {len(R):,} ({R.ticker.nunique()} names, {R.date.min().date()} -> {R.date.max().date()})")
    pr(f"cells: BB beaten+beat {len(BB):,} | BM beaten+miss {len(BM):,} | NB not beaten+beat {len(NB):,}\n")
    pr(f"{'cell':26s} {'n':>6s} {'ex20':>7s} {'ex60':>7s} {'t60':>6s} {'%+':>5s} {'rx day':>7s}")
    for lab, X in (("BB beaten + beat", BB), ("BM beaten + miss", BM), ("NB not beaten + beat", NB)):
        pr(f"{lab:26s} {len(X):>6,} {X.ex20.mean():>+7.2f} {X.ex60.mean():>+7.2f} {tstat_by(X.ex60, X.date):>6.2f} "
           f"{100 * (X.ex60 > 0).mean():>5.0f} {X.rx.mean():>+7.2f}")

    t = tstat_by(BB.ex60, BB.date)
    h1, h2 = BB[BB.date < SPLIT].ex60, BB[BB.date >= SPLIT].ex60

    def diff_t(X, Y):
        a = X.groupby(X.date).ex60.mean(); b = Y.groupby(Y.date).ex60.mean()
        d = a.mean() - b.mean()
        return d, d / sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    dm, tm = diff_t(BB, BM); dn, tn = diff_t(BB, NB)
    pr(f"\n## PRIMARY: BB 60d ADR-matched excess {BB.ex60.mean():+.2f}pp (median {BB.ex60.median():+.2f}), t {t:+.2f}; "
       f"halves {h1.mean():+.2f} (n {len(h1)}) / {h2.mean():+.2f} (n {len(h2)})")
    pr(f"  BB - BM (does the beat matter?)     {dm:+.2f}pp, t {tm:+.2f}")
    pr(f"  BB - NB (does beaten-down matter?)  {dn:+.2f}pp, t {tn:+.2f}")
    ok = t >= 3 and h1.mean() > 0 and h2.mean() > 0 and dm > 0 and dn > 0
    pr(f"  bar (t >= 3, both halves > 0, BB > BM and BB > NB): {'PASS' if ok else 'FAIL'}")

    pr("\n## SECONDARY (exploratory)")
    for lab, X in (("BB, reaction day UP", BB[BB.rx > 0]), ("BB, reaction day DOWN ('good news, bad reaction')", BB[BB.rx <= 0]),
                   ("BB deeper (<= 0.50 x high)", BB[BB.dd <= 0.50]),
                   ("BB, broken tape (breadth < 40)", BB[BB.breadth < 40]), ("BB, healthy tape (breadth >= 40)", BB[BB.breadth >= 40])):
        pr(f"  {lab:50s} n {len(X):>5,}  ex60 {X.ex60.mean():+.2f} (t {tstat_by(X.ex60, X.date):+.2f})  ex20 {X.ex20.mean():+.2f}")
    pr("  BB per year ex60: " + "  ".join(f"{y} {v:+.1f}" for y, v in BB.groupby(BB.date.dt.year).ex60.mean().items()))
    R.to_csv(REPO / "data/studies/beaten_down_beats_2026-09-24.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
