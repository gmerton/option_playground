#!/usr/bin/env python3
"""
Precision tier, gate by gate: which gates earn their place, which only cost trades? (pre-registered 2026-09-24,
before the first run; Gabe after the IONQ check: "have we looked at each of these gates individually?")

WHAT IS ALREADY ANSWERED (not re-tested): the tier as a whole is a REGIME finding (freeze-forward 2026-09-23: 2019-22
-0.01..-0.07R, positive only 2023+); ADR floor 4 vs 3-4 (adr_floor_test 2026-09-24: 3-4 loses under the house process,
no band beats its ADR peers); Trend Template criteria (ablation 2026-09-22, all UNDERPOWERED). NEW AXIS: a leave-one-out
over the tier's OWN gates under the house process -- no gate except ADR has been isolated, and 4 never have been.

DESIGN
  base       house breakout scan (run_precision_tier_control.build): eligible (ADDV >= $50M, px >= $5, not suspect),
             ADR >= 3, close crosses the prior 15-session high. Always on -- this defines "a breakout".
  gates      the 9 tier conditions, each dropped in turn:
               ADR47   ADR 4-7                 OFF52   within 15% of the 52wk high     RANGE52  52wk range >= 17%
               STACK5  EMA stack >= 5 sessions STACK40 stack run <= 40 sessions        RVOL     RVOL >= 1.1
               UPPER   close in the upper half GAP     gap < 5%                        DAY      day change < 8%
  sets       T   = passes all 9 (the tier).   M_k = fails gate k, passes the other 8 (what dropping k would admit).
  process    the house process (as adr_floor_test): close entry, day-low stop floored at 2%, judged on the close,
             exit on the first close under the 20 EMA, <= 60 sessions; % of price and R (cap 20).
  PRIMARY    per gate: 20-session forward return minus the same-date mean of ELIGIBLE names in the same ADR band
             (bands 3-4 / 4-5 / 5-7 / 7-10 / 10+), T minus M_k, Welch on date means (date-clustered).
  bar        a gate EARNS ITS PLACE if T - M_k > 0 with t >= 3 (Sidak over 9 gates at 5% = 2.77; 3 governs), both
             halves (split 2023-01) positive, and the house-process % difference has the same sign.
             A gate is a PRUNE CANDIDATE if T - M_k < 0 in BOTH halves on the primary AND M_k's house-process % is not
             below T's (diff t > -1) -- precision over recall: pruning needs the admitted trades to be no worse, not
             merely an insignificant gate. Everything else: UNPROVEN (keep, it costs nothing we can measure).
  also       per-year for every gate; n of M_k (a gate that almost never binds cannot matter); regime split
             (2019-22 vs 2023+) because the tier is a regime finding.
  caveat     survivor panel (names liquid as of 2026) flatters levels; compare sets. Judge in %, not R.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_precision_gate_ablation.py > data/studies/logs/precision_gate_ablation.log
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask
from lib.studies import pattern_test as pt
from run_adr_floor_test import house

START, SPLIT, H = "2019-10-01", "2023-01-01", 20
BANDS = [(3, 4), (4, 5), (5, 7), (7, 10), (10, 999)]
GATES = ["ADR47", "OFF52", "RANGE52", "STACK5", "STACK40", "RVOL", "UPPER", "GAP", "DAY"]


def welch(a: pd.Series, b: pd.Series) -> tuple[float, float]:
    a, b = a.dropna(), b.dropna()
    if len(a) < 3 or len(b) < 3:
        return np.nan, np.nan
    d = a.mean() - b.mean()
    return d, d / sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def main() -> None:
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
    C, Hh, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    adr = (Hh / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = Hh.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    piv15 = Hh.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (Hh - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    sd = stack_run(C, adr=adr); off52 = (C / hi52 - 1) * 100

    base = (elig & (adr >= 3) & (C >= piv15) & (C.shift(1) < piv15)).fillna(False)
    g = {
        "ADR47": (adr >= 4) & (adr <= 7), "OFF52": off52 > -15, "RANGE52": range52 >= 17,
        "STACK5": sd >= 5, "STACK40": sd <= 40, "RVOL": rvol >= 1.1, "UPPER": pos >= 0.5,
        "GAP": gap < 0.05, "DAY": chg < 0.08,
    }
    g = {k: v.fillna(False) for k, v in g.items()}
    allg = base.copy()
    for v in g.values():
        allg &= v
    P = pt.DailyPanel(open=O, high=Hh, low=L, close=C, adr=adr, elig=elig, ema20=C.ewm(span=20, adjust=False).mean())

    F = ((C.shift(-H) / C - 1) * 100).values
    A, E = adr.values, elig.values
    bench = np.full(F.shape, np.nan)
    for lo, hi in BANDS:
        mk = E & (A >= lo) & (A < hi) & np.isfinite(F)
        s = np.where(mk, F, 0).sum(axis=1); n = mk.sum(axis=1)
        b = np.where(n >= 10, s / np.maximum(n, 1), np.nan)
        inb = (A >= lo) & (A < hi)
        bench = np.where(inb, b[:, None], bench)

    def score(mask) -> pd.DataFrame:
        T = house(P, mask)
        if T.empty:
            return T
        T["excess"] = [F[i, j] - bench[i, j] for i, j in zip(T.i, T.j)]
        T["date"] = pd.to_datetime(T.date)
        return T

    T = score(allg)
    print(f"# Precision tier, gate by gate (pre-registration in the docstring)\n")
    print(f"TIER (all 9 gates): n {len(T):,}, {T.date.nunique()} dates, excess20 {T.excess.mean():+.2f}pp, "
          f"house {T.pct.mean():+.2f}%/trade (median {T.pct.median():+.2f}), R {T.R.mean():+.3f}, "
          f"win {100 * (T.pct > 0).mean():.0f}%\n")
    Tx, Tp = T.groupby("date").excess.mean(), T.groupby("date").pct.mean()

    rows, peryear = [], {}
    for k in GATES:
        m = base.copy()
        for kk, v in g.items():
            m &= (~v) if kk == k else v
        M = score(m)
        if len(M) < 30:
            rows.append(dict(gate=k, n_M=len(M))); continue
        Mx, Mp = M.groupby("date").excess.mean(), M.groupby("date").pct.mean()
        d, t = welch(Tx, Mx)
        dp, tp = welch(Tp, Mp)
        h1 = welch(Tx[Tx.index < SPLIT], Mx[Mx.index < SPLIT])[0]
        h2 = welch(Tx[Tx.index >= SPLIT], Mx[Mx.index >= SPLIT])[0]
        earns = d > 0 and t >= 3 and h1 > 0 and h2 > 0 and dp > 0
        prune = h1 < 0 and h2 < 0 and tp < 1           # tp = t of (T - M) in %, i.e. M not below T by > 1 sd
        rows.append(dict(gate=k, n_M=len(M), M_excess=M.excess.mean(), T_minus_M=d, t=t, h1=h1, h2=h2,
                         M_house=M.pct.mean(), house_T_minus_M=dp, t_house=tp, M_win=100 * (M.pct > 0).mean(),
                         verdict="EARNS" if earns else ("PRUNE?" if prune else "unproven")))
        yT = T.groupby(T.date.dt.year).excess.mean(); yM = M.groupby(M.date.dt.year).excess.mean()
        peryear[k] = (yT - yM)
    R = pd.DataFrame(rows)
    print("T - M_k: tier minus what dropping gate k would admit. PRIMARY = 20d ADR-matched excess (pp), Welch on date "
          "means; bar t >= 3 both halves (Sidak 2.77).")
    print(R.round(3).to_string(index=False))
    print("\nper year, T - M_k on the primary (pp):")
    print(pd.DataFrame(peryear).T.round(2).to_string())
    R.to_csv(pt.REPO / "data/studies/precision_gate_ablation_2026-09-24.csv", index=False)


if __name__ == "__main__":
    main()
