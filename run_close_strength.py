#!/usr/bin/env python3
"""
Does a WEAK CLOSE degrade the close-entry edge?  (pre-registered 2026-09-22)

Opened by a live position: ZETA entered on the close 2026-09-22 at 30.13, in the bottom 26% of the
day's range (DINO the same day, 20%).  The entry study (2026-09-17) established that buying the daily
CLOSE beats every intraday entry (+5.95% vs ORB/RECLAIM, paired t -1.6..-3.4) but never conditioned on
WHERE IN THE DAY'S RANGE that close landed.  So the house rule is silent on exactly the case we are in.

SIGNAL      cir = (close - low) / (high - low) on the entry bar.  0 = closed on the low, 1 = on the high.
POOL        the house breakout: close > prior 20d high, ADR >= 3, liquid+eligible, 2019-10 -> 2026-09.
ENTRY       the signal bar's close (the house process).
BUCKETS     cir quintiles.  Reported cut of interest: cir <= 0.3 (where ZETA/DINO sat).

*** THE CONFOUND, stated before running ***
The house stop IS the day's low, so cir IS the stop distance:  stop% = (close-low)/close.
A weak close is MECHANICALLY a tight stop -> small R denominator -> |R| inflated in BOTH tails and a
higher stop-out rate.  R is therefore confounded BY CONSTRUCTION and cannot answer the question alone.
This is the trap named in entry_extension_finding ("the best CLASSIFIER is the worst GATE ... predicts
mechanically/near-tautologically").  So we run three things and let the confound-free one decide:

  (1) RAW forward % return by cir quintile          <- confound-free, full panel, decides the question
  (2) R with the house day-low stop                 <- what Gabe actually experiences (confounded)
  (3) R with a FIXED 1-ADR stop                     <- breaks the mechanical link; isolates information

PRE-REGISTERED BAR
  cir carries information only if (1) is monotone in cir AND the top-bottom spread clears |t| >= 3 on
  date-clustered means in BOTH halves.  If (1) is flat while (2) moves, the verdict is MECHANICAL: cir
  is a stop-distance knob, not a forecast, and it must not become an entry gate.
  Anything else -> NULL.

Usage:  PYTHONPATH=src python run_close_strength.py [--quick]
"""
from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)

from lib.studies.pattern_test import DailyPanel, daily_signals, load_panel, run_daily

START = "2019-10-01"
HORIZONS = (5, 10, 20, 60)
QCUT = 5


def house_breakout(P: DailyPanel) -> pd.DataFrame:
    """close > prior 20-session high, ADR >= 3%, eligible."""
    level = P.high.shift(1).rolling(20).max()
    brk = (P.close > level) & (P.adr >= 3) & P.elig
    brk = brk.copy()
    brk[brk.index < START] = False
    return brk.fillna(False)


def close_in_range(P: DailyPanel) -> pd.DataFrame:
    rng = (P.high - P.low).replace(0, np.nan)
    return (P.close - P.low) / rng


def part1_raw(P: DailyPanel, brk: pd.DataFrame) -> pd.DataFrame:
    """Confound-free: raw forward % returns by cir quintile. Vectorised over the whole panel."""
    C = P.close
    cir = close_in_range(P)
    ii, jj = np.where(brk.values)
    cv = C.values
    n = len(C)
    rec = dict(date=C.index[ii], sym=C.columns[jj], cir=cir.values[ii, jj],
               adr=P.adr.values[ii, jj],
               stop_pct=100 * (cv[ii, jj] - P.low.values[ii, jj]) / cv[ii, jj])
    for h in HORIZONS:
        k = np.minimum(ii + h, n - 1)
        rec[f"r{h}"] = 100 * (cv[k, jj] / cv[ii, jj] - 1)
    T = pd.DataFrame(rec).dropna(subset=["cir"])
    T["q"] = pd.qcut(T.cir, QCUT, labels=[f"Q{i+1}" for i in range(QCUT)])
    T["half"] = np.where(T.date < pd.Timestamp("2023-01-01"), "H1", "H2")

    print(f"\n{'='*104}\n(1) RAW forward % return by close-in-range quintile  —  "
          f"{len(T):,} breakouts, {T.sym.nunique()} names, {T.date.min().date()} -> {T.date.max().date()}"
          f"\n    CONFOUND-FREE: no stop, no R denominator. This is the decisive table.\n{'='*104}")
    g = T.groupby("q")
    tab = g.agg(n=("cir", "size"), cir_med=("cir", "median"), stop_pct=("stop_pct", "median"),
                adr=("adr", "median"), **{f"r{h}": (f"r{h}", "mean") for h in HORIZONS})
    print(tab.round(2).to_string())

    print("\n  top-bottom spread (Q5 - Q1), date-clustered t:")
    for h in HORIZONS:
        a = T[T.q == f"Q{QCUT}"].groupby("date")[f"r{h}"].mean()
        b = T[T.q == "Q1"].groupby("date")[f"r{h}"].mean()
        d = (a - b).dropna()
        t = d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 else np.nan
        h1 = d[d.index < pd.Timestamp("2023-01-01")].mean()
        h2 = d[d.index >= pd.Timestamp("2023-01-01")].mean()
        flag = "PASS" if abs(t) >= 3 and np.sign(h1) == np.sign(h2) else "no"
        print(f"    r{h:<3} Q5-Q1 {d.mean():+6.2f}pp   t {t:+6.2f}   H1 {h1:+6.2f} / H2 {h2:+6.2f}   [{flag}]")

    print("\n  the ZETA/DINO cut — cir <= 0.30 vs the rest:")
    w, s = T[T.cir <= 0.30], T[T.cir > 0.30]
    for h in HORIZONS:
        a = s.groupby("date")[f"r{h}"].mean(); b = w.groupby("date")[f"r{h}"].mean()
        d = (b - a).dropna()
        t = d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 else np.nan
        print(f"    r{h:<3} weak {w[f'r{h}'].mean():+6.2f}%  strong {s[f'r{h}'].mean():+6.2f}%   "
              f"diff {d.mean():+6.2f}pp  t {t:+6.2f}   (n weak {len(w):,})")

    print("\n  monotonicity check (Spearman rank corr of quintile index vs mean return):")
    for h in HORIZONS:
        m = tab[f"r{h}"].values
        rho = pd.Series(m).corr(pd.Series(range(len(m))), method="spearman")
        print(f"    r{h:<3} rho {rho:+.2f}   {'monotone' if abs(rho) >= 0.9 else 'NOT monotone'}")
    return T


def part2_R(P: DailyPanel, brk: pd.DataFrame, T: pd.DataFrame, quick: bool) -> None:
    """R under (2) the house day-low stop and (3) a fixed 1-ADR stop, for the extreme cir quintiles."""
    cir = close_in_range(P)
    lo_thr, hi_thr = T.cir.quantile(0.2), T.cir.quantile(0.8)
    fixed_stop = P.close * (1 - P.adr / 100.0)
    hold = 20 if quick else 60

    for lab, stop_frame, tag in (("house day-low stop", P.low, "(2) CONFOUNDED by construction"),
                                 ("fixed 1-ADR stop", fixed_stop, "(3) mechanical link broken")):
        print(f"\n\n{'='*104}\n{tag} — {lab}\n{'='*104}")
        for qlab, m in (("WEAK close (bottom cir quintile)", brk & (cir <= lo_thr)),
                        ("STRONG close (top cir quintile)", brk & (cir >= hi_thr))):
            sig = lambda _P, mm=m, sf=stop_frame: daily_signals(mm, stop=sf, side="long")
            name = f"close-strength 2026-09-22: {qlab.split(' (')[0]} | {lab}"
            print(f"\n--- {qlab}: {int(m.values.sum()):,} breakouts ---")
            run_daily(name, sig, hold=hold, panel=P, entry_at="close", control="post",
                      ledger=(lab == "house day-low stop"),
                      note="pre-registered close-in-range test; house breakout, close entry")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="hold 20 instead of 60")
    a = ap.parse_args()

    P = load_panel()
    brk = house_breakout(P)
    print(f"house breakout pool: {int(brk.values.sum()):,} signals")
    T = part1_raw(P, brk)
    part2_R(P, brk, T, a.quick)

    T.to_csv("data/studies/close_strength_2026-09-22.csv", index=False)
    print("\nwrote data/studies/close_strength_2026-09-22.csv")


if __name__ == "__main__":
    main()
