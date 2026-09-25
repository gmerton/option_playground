#!/usr/bin/env python3
"""
Does VOLUME mark a real low? The O'Neil/Minervini pullback signature on the confirmation ladder (pre-registered
2026-09-25, before any run; Gabe: "did we take volume into account in signaling the low?").

WHY NEW. Volume at a low has only been tested in the CAPITULATION sense -- Breitstein scorecard (vol >= 3x, FAIL both
sides) and the counter-trend flush with dollar volume >= 2x (FAIL). The uptrend signature is the opposite: a pullback
on DRYING volume (no sellers), then a turn day on EXPANDING volume (buyers return). The Adhikary SETUP dry-up raised
P(break) 45% -> 57% but was never scored as a return edge at a pullback low.

EVENTS  exactly the (look-ahead-fixed) ladder: run_low_confirmation_ladder.episodes(), >= 1-ADR pullbacks from a
        10-session high, P1 precision tier / P2 broad uptrend, 2010-2026, liquid_panel_2009. Entry at the K1 close (first
        close above the high of the candidate-low bar); K0 (the dip) reported as context.
VOLUME (all known at the entry close; avg50 = mean volume of the 50 sessions ending the day BEFORE the peak)
  V1 DRY     mean volume over the pullback days (peak+1 .. the low bar) <= 0.8 x avg50
  V2 TURN    volume on the K1 entry day >= 1.5 x avg50
  V3 BOTH    V1 and V2
MEASURE  within-rung DIFFERENCE: excess(+h) of tagged K1 entries minus excess of untagged K1 entries in the same
        population (month-clustered difference series) -- this cancels whatever the population-level control carries
        (the ladder's P2 dip result is PARKED as fragile/survivorship-exposed; a within-rung contrast is robust to that).
        Excess vs the ladder's same-date same-population ADR-tercile control. Also: hold20 (low not undercut in 20
        sessions) tagged vs untagged -- the "reliably exiting the low" question -- with a two-proportion z.
CELLS   3 filters x 2 populations x 2 horizons (20 PRIMARY, 60) = 12. PRIMARY = P2 x V3 x +20 (P1 is ~2.6k K1
        entries; V3 may leave < 200). Sidak(12) |t| >= 2.87; the house |t| >= 3 GOVERNS; both halves (2018-01) the
        same sign; majority of years.
READ    a volume signature is a SIGNAL only if its difference passes. A higher hold20 with no return difference means
        volume identifies lows that hold but the price already reflects it (the ladder's lesson again).
PRIOR   low: every confirmation on the ladder was bought 1-for-1 in price.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_volume_low_signature.py   (log -> data/studies/logs/volume_low_signature.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

import run_low_confirmation_ladder as L
from lib.studies.pattern_test import load_panel

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/volume_low_signature.log"
SPLIT, T_BAR = "2018-01-01", 3.0
FILTERS = {"V1 DRY": "dry", "V2 TURN": "turn", "V3 BOTH": "both"}


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def main():
    P = load_panel(L.PANEL)
    idx = P.close.index
    raw = pd.read_parquet(REPO / L.PANEL, columns=["date", "ticker", "volume"])
    raw["date"] = pd.to_datetime(raw.date)
    Vol = raw.pivot(index="date", columns="ticker", values="volume").reindex(index=idx, columns=P.close.columns).values
    F = L.features(P)
    E = L.episodes(F, idx)
    T = L.score(E, F, idx, P)                       # same row order as E
    T["i"], T["low_day"] = E.i.values, E.low_day.values
    avg50 = pd.DataFrame(Vol).shift(1).rolling(50, min_periods=40).mean().values
    rows = []
    for r in T.itertuples():
        a = avg50[r.peak, r.j]
        pull = Vol[r.peak + 1:r.low_day + 1, r.j]
        rows.append((np.nanmean(pull) / a if a > 0 and len(pull) else np.nan, Vol[r.i, r.j] / a if a > 0 else np.nan))
    T["pull_rv"], T["turn_rv"] = np.array(rows).T
    T["dry"] = T.pull_rv <= 0.8
    T["turn"] = T.turn_rv >= 1.5
    T["both"] = T.dry & T.turn
    out = ["# Volume signature at the pullback low (pre-registration in the docstring)"]
    R = []
    for pop in ("P2", "P1"):
        K = T[(T["pop"] == pop) & (T.rung == "K1") & T.pull_rv.notna()]
        out.append(f"\n## {pop} K1 entries: n {len(K):,}; median pullback vol {K.pull_rv.median():.2f}x, turn-day vol "
                   f"{K.turn_rv.median():.2f}x avg50; hold20 {K.hold20.mean():.0%}")
        for lab, col in FILTERS.items():
            a, b = K[K[col]], K[~K[col]]
            p1, p2 = a.hold20.mean(), b.hold20.mean()
            pp = (a.hold20.sum() + b.hold20.sum()) / (len(a) + len(b))
            z = (p1 - p2) / np.sqrt(pp * (1 - pp) * (1 / max(len(a), 1) + 1 / max(len(b), 1)))
            for h in (20, 60):
                ma = a.groupby(a.date.dt.to_period("M"))[f"x{h}"].mean()
                mb = b.groupby(b.date.dt.to_period("M"))[f"x{h}"].mean()
                dm = (ma - mb).dropna(); hh = dm.index < pd.Period(SPLIT, "M")
                yr = dm.groupby(dm.index.year).mean(); same = int((np.sign(yr) == np.sign(dm.mean())).sum())
                ok = abs(tstat(dm)) >= T_BAR and np.sign(dm[hh].mean()) == np.sign(dm[~hh].mean()) and same > len(yr) / 2
                prim = pop == "P2" and col == "both" and h == 20
                out.append(f"  {lab:8s} +{h}: tagged n {len(a):5d} ({len(a)/len(K):4.0%}) x {a[f'x{h}'].mean():+.2f} vs rest {b[f'x{h}'].mean():+.2f} "
                           f"| diff {dm.mean():+.2f}pp t {tstat(dm):+.2f} halves {dm[hh].mean():+.2f}/{dm[~hh].mean():+.2f} yrs {same}/{len(yr)} "
                           f"{'PASS' if ok else 'fail'}" + (f" | hold20 {p1:.0%} vs {p2:.0%} z {z:+.1f}" if h == 20 else "")
                           + ("  <- PRIMARY" if prim else ""))
                R.append(dict(pop=pop, filter=lab, h=h, n_tag=len(a), diff=dm.mean(), t=tstat(dm), h1=dm[hh].mean(),
                              h2=dm[~hh].mean(), yrs=f"{same}/{len(yr)}", PASS=ok, hold_tag=p1, hold_rest=p2, z_hold=z))
        # context: the dip itself (K0) with the dry-volume tag
        K0 = T[(T["pop"] == pop) & (T.rung == "K0") & T.pull_rv.notna()]
        a, b = K0[K0.dry], K0[~K0.dry]
        out.append(f"  [context] K0 dip on dry volume: n {len(a)} x20 {a.x20.mean():+.2f} vs rest {b.x20.mean():+.2f}; "
                   f"hold20 {a.hold20.mean():.0%} vs {b.hold20.mean():.0%}")
    D = pd.DataFrame(R)
    out.append("\nVERDICT: " + (", ".join(f"{r.pop} {r.filter} +{r.h} ({r.diff:+.2f}pp t {r.t:+.2f})" for r in D[D.PASS].itertuples())
                                or "no volume signature passes"))
    D.to_csv(REPO / "data/studies/volume_low_signature_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
