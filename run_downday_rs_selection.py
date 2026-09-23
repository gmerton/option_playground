#!/usr/bin/env python3
"""
Down-day relative strength as a name-level SELECTION filter (pre-registered 2026-09-23; TEST_INDEX §125).

THE CLAIM (SMB Capital, "relative strength breakout", reviewed 2026-09-22, scored 3/5). On a genuinely
weak tape, names that REFUSE TO FALL are being accumulated -- institutions work orders over days and use
market weakness to fill. "Weakness in the market is what makes strength visible." The filter is: flat or
green while the index flushes, **more than once**, and near the 52-week high (explicitly not mid-range).
He is emphatic that this is not an entry -- "relative strength on its own is not an entry, it's an alert"
-- it RANKS the watchlist, and the trade is still the first close over resistance.

WHY IT IS WORTH RUNNING WHEN FIVE ANGLES SAY SELECTION CANNOT BE IMPROVED. Because unlike the five, this
one has a MECHANISM (accumulation visible only under stress) and a precedent at a different scale: the
rotation study's Part III found bottom-3-sector, volume-confirmed breakouts at **+5.6pp, t 2.61** -- the
same idea at sector level. It is also the one creator claim whose process independently matches the house
process (rank don't buy, close trigger, stop at the day's low, earnings veto).

⚠ THE PRE-REGISTERED SCEPTICAL PRIOR, declared before the run: **RVOL does the work and the RS filter is a
proxy for it.** Our most robust breakout result is monotone in RVOL (<1.0 = -0.68% @21d ... 1.8-2.5 =
+0.86% @63d, t 3.64; all breakouts pooled -0.51%, t -3.29). A name that holds up on a down day is very
likely a name with real demand, i.e. one that will break out on volume. **So the RS effect is only
interesting if it survives WITHIN an RVOL bucket.** That interaction is the primary, not an afterthought.
⚠ Also note the review's own finding: of the creator's three examples, the one he TRADED broke out on
RVOL 0.99 and the one he SKIPPED was the only one in the passing volume cohort -- his narrative ranking
was backwards relative to the gate that sorts in our data.

DESIGN
  down day   index (QQQ) close falls >= 1.5%
  RS event   on such a day, a name closes FLAT OR GREEN and sits within 15% of its 52-week high
  dose       count of RS events in the trailing LOOKBACK (20) sessions, **shifted 1** -- the dose must be
             fully known before the entry bar. (Today's lesson: the UR band sweep was retracted for
             exactly this kind of conditioning.)
  entry      the next BREAKOUT close: close > prior 20-session high, ADR >= 3, eligible
  arms       dose >= 1 / dose >= 2 (his "more than once") vs dose == 0, the SAME breakout pool otherwise
  controls   pattern_test `xname` (same date, other name) and `post` (same name, random later session)

PRIMARY: within-date mean forward return of dose>=2 breakouts minus dose==0 breakouts, date-clustered t.
Within-date because a down-day filter is mechanically correlated with the calendar -- comparing across
dates would measure the regime, not the name.
PASS: positive with |t| >= 3, both halves the same sign (split 2023-01-01), AND the effect still present
inside the RVOL >= 1.8 bucket. 2 doses x 2 horizons x 3 RVOL cells = 12 -> Sidak |t| >= 2.87; house 3.0.

PRIOR: ~70% that the raw RS effect is positive but vanishes inside RVOL buckets, i.e. MECHANISM yield --
"he is right that it marks demand, wrong that it adds anything to volume confirmation". ~15% it survives
(which would be the first selection filter to work here), ~15% it is flat throughout.

Usage: PYTHONPATH=src .venv/bin/python3 -u run_downday_rs_selection.py 2>&1 | tee data/studies/logs/downday_rs.log
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250)

from lib.commons.ma_stack import stack_run  # noqa: F401  (kept: panel parity with the other breakout studies)
from lib.regime.trailing import Panel, liquidity_mask
from lib.studies import pattern_test as pt

INDEX = "QQQ"
DOWN_PCT = -1.5
OFF52_MAX = -15.0       # within 15% of the 52-week high
LOOKBACK = 20
SPLIT = "2023-01-01"
HORIZONS = (21, 63)


def build():
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    idx = raw[raw.ticker == INDEX].set_index("date").close.sort_index()
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max()
    off52 = (C / hi52 - 1) * 100
    piv20 = H.shift(1).rolling(20).max()
    rvol = V / V.shift(1).rolling(50).mean()
    chg = C.pct_change(fill_method=None) * 100

    idx_chg = (idx.pct_change(fill_method=None) * 100).reindex(C.index)
    down = (idx_chg <= DOWN_PCT).fillna(False)
    down_wide = pd.DataFrame(np.repeat(down.to_numpy()[:, None], C.shape[1], axis=1),
                             index=C.index, columns=C.columns)

    rs_event = (down_wide & (chg >= 0) & (off52 > OFF52_MAX) & elig).fillna(False)
    dose = rs_event.rolling(LOOKBACK).sum().shift(1)          # ⚠ shift: known BEFORE the entry bar
    brk = ((C > piv20) & (adr >= 3) & elig).fillna(False)
    print(f"panel {C.shape}; {int(down.sum())} down days ({DOWN_PCT}% on {INDEX}); "
          f"{int(rs_event.to_numpy().sum()):,} RS events; {int(brk.to_numpy().sum()):,} breakouts")
    return dict(C=C, brk=brk, dose=dose, rvol=rvol, adr=adr, elig=elig)


def main() -> None:
    D = build()
    C, brk, dose, rvol = D["C"], D["brk"], D["dose"], D["rvol"]
    rows = []
    for h in HORIZONS:
        fwd = (C.shift(-h) / C - 1) * 100
        for rv_lab, rv_mask in (("ALL", pd.DataFrame(True, index=C.index, columns=C.columns)),
                                ("RVOL < 1.8", rvol < 1.8),
                                ("RVOL >= 1.8", rvol >= 1.8)):
            base = brk & rv_mask.fillna(False)
            for k in (1, 2):
                hit = base & (dose >= k)
                non = base & (dose == 0)
                a = fwd.where(hit).mean(axis=1)
                b = fwd.where(non).mean(axis=1)
                j = pd.concat([a.rename("hit"), b.rename("non")], axis=1).dropna()
                if len(j) < 30:
                    continue
                d = j.hit - j.non
                t = float(d.mean() / (d.std(ddof=1) / sqrt(len(d))))
                h1, h2 = d[d.index < SPLIT], d[d.index >= SPLIT]
                rows.append(dict(horizon=f"{h}d", rvol=rv_lab, dose=f">={k}",
                                 n_hit=int(hit.to_numpy().sum()), n_non=int(non.to_numpy().sum()),
                                 dates=len(j), hit_ret=j.hit.mean(), non_ret=j["non"].mean(),
                                 edge=d.mean(), t=t, h1=h1.mean(), h2=h2.mean(),
                                 agree=bool(np.sign(h1.mean()) == np.sign(h2.mean()))))
    R = pd.DataFrame(rows)
    R.to_csv("data/studies/downday_rs_selection_2026-09-23.csv", index=False)
    print(f"\n{'='*126}\nWITHIN-DATE: breakouts WITH prior down-day RS vs breakouts WITHOUT, same pool\n{'='*126}")
    print(R.round(3).to_string(index=False))

    prim = R[(R.dose == ">=2") & (R.rvol == "ALL")]
    conf = R[(R.dose == ">=2") & (R.rvol == "RVOL >= 1.8")]
    print(f"\n  PRIMARY (dose>=2, all RVOL): " +
          ", ".join(f"{r.horizon} edge {r.edge:+.2f}pp t {r.t:+.2f}" for r in prim.itertuples()))
    print(f"  SURVIVES INSIDE RVOL>=1.8?  " +
          ", ".join(f"{r.horizon} edge {r.edge:+.2f}pp t {r.t:+.2f}" for r in conf.itertuples()))
    ok = R[(R.dose == ">=2") & (R.edge > 0) & (R.t.abs() >= 3) & R.agree]
    print(f"\n  cells passing (edge>0, |t|>=3, halves agree): {len(ok)} of {len(R[R.dose=='>=2'])}")
    passed = bool(len(prim[(prim.edge > 0) & (prim.t.abs() >= 3) & prim.agree])
                  and len(conf[(conf.edge > 0) & (conf.t.abs() >= 3) & conf.agree]))
    print(f"  PRE-REGISTERED PASS: {'YES' if passed else 'NO'}")
    print("\nwrote data/studies/downday_rs_selection_2026-09-23.csv")


if __name__ == "__main__":
    main()
