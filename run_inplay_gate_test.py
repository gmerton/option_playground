#!/usr/bin/env python3
"""
In-play gate: RELATIVE range expansion vs the ABSOLUTE ADR gate on the house breakout
(pre-registered 2026-09-24, before the first run; TEST_INDEX §10 queue item, spec data/lance_breitstein/principles/in-play-stocks.md)

CLAIM (Breitstein): in-play stocks "move multiple average trading ranges relative to their normal behavior". The desk
gates on an ABSOLUTE ADR (>= 3), which selects a CLASS of permanently volatile names; a RELATIVE gate
(today's range / own ADR20 >= k) selects a MOMENT -- a quiet name waking up. Never tested. Today's range is known
at the close, so it fits the house close entry.

DESIGN (reuses run_adr_floor_test so the two studies are directly comparable)
  events    the house breakout (run_adr_floor_test.build: 15d pivot on the close, RVOL >= 1.1, upper half, stacked
            >= 5d, no >= 5% gap / >= 8% day) with the ADR gate lowered to 2 (liquidity floor only).
  arms      ABS        ADR20 >= 3                                  (the current desk gate -- the baseline)
            REL k      range_today / ADR20 >= k, k in {1.5, 2, 3}  (relative only, ADR >= 2)
            ABS+REL k  both                                         k in {1.5, 2, 3}
            PRIMARY = REL 2 (the spec's middle value). 6 test cells; Sidak 6 -> 2.64; the house |t| >= 3 governs.
  metrics   (1) PRIMARY: 20d excess vs same-date eligible names in the SAME ADR BAND (bands 2-3/3-4/4-7/7+) --
                the relative gate changes which vol classes get in, so a raw comparison would just measure vol.
            (2) house process in % (close entry, day-low stop floored at 2%, 20-EMA exit, <= 60d).
  bar       an arm is an UPGRADE only if its ADR-matched excess clears t >= 3 with both halves (2023-01) positive
            and >= 5/8 years positive, AND its house-process % beats ABS (difference t > 0). If ABS itself shows no
            ADR-matched excess (as run_adr_floor_test found), the relative gate must add selection, not vol.
  caveat    survivor panel; "clean levels" -- the discretionary half of his definition -- is not captured, so the
            mechanical version is expected to UNDER-state his claim (spec §4).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_inplay_gate_test.py > data/studies/logs/inplay_gate_test.log
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

import run_adr_floor_test as af
from lib.studies import pattern_test as pt

KS = [1.5, 2.0, 3.0]


def main() -> None:
    P, brk, _tier = af.build()
    C = P.close
    rng_ratio = ((P.high / P.low - 1) * 100) / P.adr                       # today's range in own-ADR units (ADR = prior 20d)
    F = ((C.shift(-af.H) / C - 1) * 100).values
    A, E = P.adr.values, P.elig.values
    bench = {}
    for lo, hi in af.BANDS:
        mk = E & (A >= lo) & (A < hi) & np.isfinite(F)
        s = np.where(mk, F, 0).sum(axis=1); n = mk.sum(axis=1)
        bench[f"{lo}-{hi if hi < 99 else '+'}"] = np.where(n >= 10, s / np.maximum(n, 1), np.nan)
    band_of = lambda a: next((f"{lo}-{hi if hi < 99 else '+'}" for lo, hi in af.BANDS if lo <= a < hi), None)

    T = af.house(P, brk)                                                  # all breakouts at ADR >= 2, house process
    T["band"] = T.adr.map(band_of)
    T["rr"] = [rng_ratio.values[i, j] for i, j in zip(T.i, T.j)]
    T["fwd"] = [F[i, j] for i, j in zip(T.i, T.j)]
    T["excess"] = [F[i, j] - bench[b][i] if b else np.nan for i, j, b in zip(T.i, T.j, T.band)]
    T["year"] = pd.to_datetime(T.date).dt.year
    arms = {"ABS (adr>=3) baseline": T.adr >= 3}
    for k in KS:
        arms[f"REL {k}" + (" *PRIMARY*" if k == 2.0 else "")] = T.rr >= k
    for k in KS:
        arms[f"ABS+REL {k}"] = (T.adr >= 3) & (T.rr >= k)
    base_pct = T[arms["ABS (adr>=3) baseline"]].groupby("date").pct.mean()
    rows = []
    for name, m in arms.items():
        g = T[m]
        ex = g.groupby("date").excess.mean(); yrs = g.groupby("year").excess.mean()
        h1, h2 = g[g.date < af.SPLIT].excess.mean(), g[g.date >= af.SPLIT].excess.mean()
        pc = g.groupby("date").pct.mean()
        se = sqrt(pc.var(ddof=1) / len(pc) + base_pct.var(ddof=1) / len(base_pct))
        dt = (pc.mean() - base_pct.mean()) / se if "baseline" not in name else np.nan
        passed = bool("baseline" not in name and g.excess.mean() > 0 and af.tstat(ex) >= 3 and h1 > 0 and h2 > 0
                      and (yrs > 0).sum() >= 5 and dt > 0)
        rows.append(dict(arm=name, n=len(g), per_yr=round(len(g) / 7), med_adr=g.adr.median(),
                         share_adr_lt3=100 * (g.adr < 3).mean(), fwd20=g.fwd.mean(), excess20=g.excess.mean(),
                         t=af.tstat(ex), h1=h1, h2=h2, yrs_pos=f"{(yrs > 0).sum()}/{len(yrs)}",
                         house_pct=g.pct.mean(), house_med=g.pct.median(), vs_abs_t=dt, win=100 * (g.pct > 0).mean(),
                         upgrade=passed))
    R = pd.DataFrame(rows)
    print(f"house breakout, ADR >= 2 liquidity floor, {af.START} ->; {len(T):,} events. PRIMARY = 20d ADR-matched "
          f"excess; house process in %\n")
    print(R.round(3).to_string(index=False))
    print("\nby year, 20d ADR-matched excess (pp):")
    for name in ("ABS (adr>=3) baseline", "REL 2.0 *PRIMARY*", "ABS+REL 2.0"):
        g = T[arms[name]]
        print(f"  {name:22s} " + "  ".join(f"{y} {v:+.2f}" for y, v in g.groupby("year").excess.mean().items()))
    print("\nquiet names waking up (ADR 2-3, the class ABS excludes), by range ratio:")
    q = T[(T.adr < 3)]
    for lo, hi in ((0, 1.5), (1.5, 2), (2, 3), (3, 99)):
        g = q[(q.rr >= lo) & (q.rr < hi)]
        if len(g) >= 30:
            print(f"  rr {lo}-{hi if hi < 99 else '+'}: n {len(g):5d}  excess {g.excess.mean():+.2f}pp "
                  f"(t {af.tstat(g.groupby('date').excess.mean()):+.2f})  house {g.pct.mean():+.2f}%")
    print(f"\nupgrades: {int(R.upgrade.sum())} of {len(R) - 1}")
    R.to_csv(pt.REPO / "data/studies/inplay_gate_test_2026-09-24.csv", index=False)


if __name__ == "__main__":
    main()
