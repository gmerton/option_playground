#!/usr/bin/env python3
"""
Does every criterion of the Ariel momentum scan earn its place inside the production INT universe? (pre-registered
2026-09-28, before the run; queued 2026-09-22 as the mirror of the Trend Template ablation; Gabe: "Let's do 1 and 2").

WHY. Production switched to INT = Trend Template AND Ariel scan on 2026-09-22. The TT half was ablated that day (c1/c2
redundant, everything else underpowered, full TT only +0.575pp); the Ariel half was only ever tested WHOLE. Two
concrete suspicions from the queue row: a3 (>= 2M shares/day) is price-distorted liquidity filtering, redundant with
the $200M ADDV floor (it drops liquid high-priced names); and a1 (>= 70% above the 252-day low) is the BINDING
constraint inside INT -- 36 of the 48 names the switch dropped -- and Ariel himself overrides it nightly (every
mega-cap he watches fails it). So INT may encode his published rule, not his practice.

METHOD  identical to run_trend_template_ablation.py (imported): leave-one-out, membership as of the prior close,
        non-overlapping dates, PRIMARY statistic = the paired, date-held-fixed change in ADR-matched 20-day excess when
        one criterion is dropped (delta > 0 => the criterion SUBTRACTS). Also 5-day.
CRITERIA (his, as coded in lib.minervini.scan / run_universe_test.py)
        a1 close >= 1.70 x 252-day low · a2 close > 50 SMA · a3 50-day avg volume >= 2M shares · a4 close > $7 ·
        a5 50-day ADDV >= $100M
UNIVERSES  PRIMARY: inside INT (TT conjuncts c1..c10 AND a1..a5) -- the production universe. SECONDARY: inside AH alone.
        a2 and a5 are subsumed by TT inside INT (c6 close > 50 SMA; c10 ADDV >= $200M), so their INT deltas should be
        ~0 by construction: a built-in sanity check.
BAR     5 criteria x 2 horizons x 2 universes = 20 cells -> Sidak |t| >= 3.09 (same as the TT ablation) AND both halves
        (split 2023-01-01) the same sign. Otherwise INERT/UNRESOLVED -- and "inert but expensive in universe size" is
        itself actionable. Universe size (names/day) reported for every arm.
DESCRIPTIVE  the latest date: which mega-caps (AAPL MSFT NVDA AMZN GOOGL META AVGO TSLA NOW) are in TT but excluded
        by a1 alone.
⚠ Survivor-biased panel (today's liquid names): arms compare fairly with each other; absolute levels are optimistic.
Local.

Run: PYTHONPATH=src .venv/bin/python3 run_ariel_ablation.py   (log -> data/studies/logs/ariel_ablation.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import run_trend_template_ablation as TA
from lib.studies import pattern_test as pt

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/ariel_ablation.log"
MEGA = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "NOW"]


def ah_conj(P, raw):
    C, L = P.close, P.low
    piv = lambda v: raw.pivot(index="date", columns="ticker", values=v).sort_index().reindex(index=C.index, columns=C.columns)
    dolvol, vol = piv("dolvol"), piv("volume")
    lo252 = L.rolling(252, min_periods=200).min()
    return {"a1 >=70% off low": C >= 1.70 * lo252,
            "a2 close>50sma": C > C.rolling(50, min_periods=50).mean(),
            "a3 >=2M sh/day": vol.rolling(50, min_periods=50).mean() >= 2e6,
            "a4 price>$7": C > 7,
            "a5 ADDV>=$100M": dolvol.rolling(50, min_periods=50).mean() >= 100e6}


def main():
    import run_precision_tier_control as pc
    P, _b, _p = pc.build()
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    tt, adr = TA.build(P, raw)
    ah = ah_conj(P, raw)
    C, base = P.close, P.elig.shift(1).fillna(False).astype(bool)
    tt_ = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan
    out = ["# Ariel scan ablation inside INT and AH (pre-registration in the docstring)",
           f"multiple testing: 20 cells, Sidak |t| >= {TA.SIDAK_T:.2f}"]
    rows = []
    for uni, conj in (("INT (production)", {**tt, **ah}), ("AH alone", ah)):
        full = TA.mask_from(conj, P, None)
        for h in (20, 5):
            fr = C.shift(-h) / C - 1
            dates = C.index[C.index >= TA.START][::h]
            dates = dates[dates <= C.index[-1 - h]]
            f_raw, f_b, f_n = TA.per_date_returns(P, full, fr, dates, adr, base)
            ok = f_n >= 5
            for k in [None] + list(ah):
                m = full if k is None else TA.mask_from(conj, P, k)
                a_raw, a_b, a_n = TA.per_date_returns(P, m, fr, dates, adr, base)
                good = ok & (a_n >= 5)
                d = ((a_raw - a_b) - (f_raw - f_b))[good].dropna()
                h1, h2 = d[d.index < TA.SPLIT], d[d.index >= TA.SPLIT]
                rows.append(dict(universe=uni, horizon=f"{h}d", dropped=("— full —" if k is None else k),
                                 names=int(m.sum(axis=1)[m.index >= TA.START].median()),
                                 excess=((a_raw - a_b)[good]).mean() * 100, d_adj=d.mean() * 100, t=tt_(d),
                                 h1=h1.mean() * 100, h2=h2.mean() * 100,
                                 agree=bool(np.sign(h1.mean()) == np.sign(h2.mean()))))
    R = pd.DataFrame(rows)
    R["verdict"] = np.where((R.t.abs() >= TA.SIDAK_T) & R.agree, np.where(R.d_adj > 0, "SUBTRACTS", "ADDS"), "inert/unresolved")
    R.loc[R.dropped == "— full —", "verdict"] = ""
    for uni in R.universe.unique():
        for h in ("20d", "5d"):
            s = R[(R.universe == uni) & (R.horizon == h)]
            out.append(f"\n== {uni}, {h} (delta > 0 => the criterion SUBTRACTS) ==")
            out.append(s[["dropped", "names", "excess", "d_adj", "t", "h1", "h2", "agree", "verdict"]].round(3).to_string(index=False))
    # descriptive: mega-caps in TT but out of INT only because of a1, on the latest date
    last = C.index[-1]
    ttm = TA.mask_from(tt, P, None).loc[last]
    a1 = ah["a1 >=70% off low"].shift(1).loc[last]
    rest = TA.mask_from({k: v for k, v in ah.items() if k != "a1 >=70% off low"}, P, None).loc[last]
    lo = P.low.rolling(252, min_periods=200).min().shift(1).loc[last]
    info = [f"{t} ({C[t].iloc[-2] / lo[t]:.2f}x low)" for t in MEGA if t in C and bool(ttm.get(t)) and bool(rest.get(t)) and not bool(a1.get(t))]
    out.append(f"\nDESCRIPTIVE {last.date()}: mega-caps in TT and passing a2-a5 but excluded by a1 alone: {', '.join(info) or 'none'}")
    R.to_csv(REPO / "data/studies/ariel_ablation_2026-09-28.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
