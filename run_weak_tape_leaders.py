#!/usr/bin/env python3
"""
Stocks that hold up in a weak tape (O'Neil): do names near their 52-week high while breadth is washed out beat the
field once breadth recovers? (pre-registered 2026-09-24, before the first run; TEST_INDEX §10 row queued 2026-09-20;
timely: the 2026-09-22 regime read has 32.6% of the liquid universe above its 50 SMA).

WHAT IS ALREADY ANSWERED (not re-tested): group/industry-level RS as a filter INVERTED (rotation study); down-day RS as
a name-level filter INVERTED, but its control varied 52wk proximity too (2026-09-23); inside the breakout tier,
52wk-high distance has no selection power (gate ablation 2026-09-24, t 0.14); crash-leader study: buying DEEP drawdowns
is a regime bet. NEW AXIS: relative strength conditioned on a breadth WASHOUT, held through the recovery -- a state
test, not a trigger (the FTD study's hint: post-FTD names beat the field while the breakout entry lost).

DESIGN
  panel      liquid_panel_2009 (2010 -> 2026-09), point-in-time eligible (trailing-50 ADDV >= $50M, px >= $5, not suspect).
  breadth    share of eligible names closing above their 50 SMA.
  episode    WASHOUT starts on the first close with breadth < 35% after breadth was >= 45% (hysteresis, so one episode
             per washout; the unit of inference). Entry = that day's close.
  STRONG     eligible names with close >= 0.90 x the prior 252-session high on the episode day.
  FIELD      all other eligible names that day (the control), ADR-MATCHED: excess is taken against the same-date mean
             of field names in the same ADR band (<2, 2-3, 3-4, 4-6, 6+), so "strong" cannot win by being low-vol.
  outcome    forward close-to-close return over 20 / 40 / 60 sessions; no stop (a state test, not a trade).
  PRIMARY    40-session ADR-matched excess of STRONG, averaged per episode (episode = one observation), t across
             episodes. Bar: t >= 3, both chronological halves (split 2018-01) positive, >= 70% of episodes positive.
             Expected power is LOW (~20-30 episodes); an UNDERPOWERED verdict is an acceptable outcome.
  SECONDARY  (exploratory) 20 / 60 sessions; every washout day (date-clustered, overlapping, descriptive only);
             WAIT arm: the same STRONG names bought at the first close breadth recovers >= 50%, 40 sessions on --
             does buying during the washout beat waiting for the recovery (state vs moment)?
             Excess RAW (vs the whole field, no ADR match) to show what the ADR match removes.
  caveat     survivor panel: names liquid as of 2026; strong names that later failed are under-represented, which
             FLATTERS strong vs field. Read a pass with that in mind.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_weak_tape_leaders.py   (log -> data/studies/logs/weak_tape_leaders.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from lib.regime.trailing import Panel, liquidity_mask

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/weak_tape_leaders.log"
OUT = REPO / "data/studies/weak_tape_leaders_2026-09-24.csv"
LO, HI_RESET, RECOVER, NEAR = 35.0, 45.0, 50.0, 0.90
BANDS = [(0, 2), (2, 3), (3, 4), (4, 6), (6, 999)]
SPLIT = pd.Timestamp("2018-01-01")


def tstat(x) -> float:
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * sqrt(len(x))) if len(x) > 2 else np.nan


def main() -> None:
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP", "DIA"])]
    p = Panel.from_long(raw)
    C, H, L = p.close, p.high, p.low
    elig = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()).fillna(False)
    sma50 = C.rolling(50).mean()
    above = (C > sma50) & elig & sma50.notna()
    denom = (elig & sma50.notna()).sum(axis=1)
    breadth = 100 * above.sum(axis=1) / denom
    # drop partial panel days (e.g. a last row with only a handful of names): < 50% of the trailing-20 median
    breadth = breadth[denom >= 0.5 * denom.rolling(20, min_periods=5).median().shift(1).fillna(denom)]
    breadth = breadth[breadth.index >= "2010-01-01"]
    hi252 = H.shift(1).rolling(252, min_periods=200).max()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    near = (C >= NEAR * hi252) & elig
    band = pd.DataFrame(np.select([(adr >= lo) & (adr < hi) for lo, hi in BANDS], range(len(BANDS)), -1),
                        index=adr.index, columns=adr.columns)

    # episodes (hysteresis)
    eps, armed = [], True
    for d, b in breadth.items():
        if armed and b < LO:
            eps.append(d); armed = False
        elif not armed and b >= HI_RESET:
            armed = True
    idx = C.index

    def excess_on(d, h, strong_mask_row=None):
        i = idx.get_loc(d)
        if i + h >= len(idx):
            return None
        fwd = C.iloc[i + h] / C.iloc[i] - 1
        e, s, bd = elig.loc[d], (near.loc[d] if strong_mask_row is None else strong_mask_row), band.loc[d]
        ok = e & fwd.notna()
        st, fl = ok & s, ok & ~s
        if st.sum() < 5:
            return None
        ex = []
        for k in range(len(BANDS)):
            a, b = fwd[st & (bd == k)], fwd[fl & (bd == k)]
            if len(a) and len(b) >= 10:
                ex.append((a - b.mean()).values)
        exm = np.concatenate(ex).mean() if ex else np.nan
        return dict(n_strong=int(st.sum()), n_field=int(fl.sum()), strong=100 * fwd[st].mean(),
                    field=100 * fwd[fl].mean(), raw_excess=100 * (fwd[st].mean() - fwd[fl].mean()), excess=100 * exm)

    rows = []
    for d in eps:
        rec = dict(episode=d.date(), breadth=round(breadth[d], 1))
        for h in (20, 40, 60):
            r = excess_on(d, h)
            if r:
                rec.update({f"{k}_{h}": v for k, v in r.items() if k in ("excess", "raw_excess", "strong", "field")})
                rec["n_strong"] = r["n_strong"]
        # WAIT arm: same names, bought at the first close breadth recovers >= 50%, held 40
        after = breadth[breadth.index > d]
        rec_d = after[after >= RECOVER].index.min() if (after >= RECOVER).any() else None
        if rec_d is not None:
            rec["recovery"] = rec_d.date()
            rec["days_to_recovery"] = int((idx.get_loc(rec_d) - idx.get_loc(d)))
            w = excess_on(rec_d, 40, strong_mask_row=near.loc[d])
            if w:
                rec["wait_excess_40"] = w["excess"]
        rows.append(rec)
    E = pd.DataFrame(rows)
    E.to_csv(OUT, index=False)

    out = []
    pr = out.append
    pr("# Stocks that hold up in a weak tape (pre-registration in the docstring)\n")
    pr(f"breadth = % of eligible names above the 50 SMA; episode = first close < {LO:.0f}% after >= {HI_RESET:.0f}%; "
       f"STRONG = within {100 * (1 - NEAR):.0f}% of the 252d high\n{len(E)} episodes 2010 -> {E.episode.max()}")
    cols = ["episode", "breadth", "n_strong", "strong_40", "field_40", "raw_excess_40", "excess_40",
            "days_to_recovery", "wait_excess_40"]
    pr(E[[c for c in cols if c in E]].round(2).to_string(index=False))

    pr("\n## PRIMARY: 40-session ADR-matched excess of STRONG, one observation per episode")
    x = E.excess_40.dropna()
    h1 = E[pd.to_datetime(E.episode) < SPLIT].excess_40.dropna()
    h2 = E[pd.to_datetime(E.episode) >= SPLIT].excess_40.dropna()
    t = tstat(x)
    pos = (x > 0).mean()
    pr(f"  mean {x.mean():+.2f}pp  median {x.median():+.2f}  t {t:+.2f}  n {len(x)} episodes  positive {100 * pos:.0f}%")
    pr(f"  halves: pre-2018 {h1.mean():+.2f} (n {len(h1)}, t {tstat(h1):+.2f}) / 2018+ {h2.mean():+.2f} (n {len(h2)}, t {tstat(h2):+.2f})")
    ok = t >= 3 and h1.mean() > 0 and h2.mean() > 0 and pos >= 0.70
    pr(f"  bar t >= 3, both halves > 0, >= 70% of episodes positive: {'PASS' if ok else 'FAIL'}")

    pr("\n## SECONDARY (exploratory)")
    for h in (20, 60):
        y = E[f"excess_{h}"].dropna()
        pr(f"  {h}-session ADR-matched excess: {y.mean():+.2f}pp t {tstat(y):+.2f} ({100 * (y > 0).mean():.0f}% +)")
    y = E.raw_excess_40.dropna()
    pr(f"  40-session RAW excess (no ADR match): {y.mean():+.2f}pp t {tstat(y):+.2f}  <- what the ADR match removes")
    if "wait_excess_40" in E:
        j = E[["excess_40", "wait_excess_40"]].dropna()
        d = j.excess_40 - j.wait_excess_40
        pr(f"  WAIT arm (same names bought at breadth >= {RECOVER:.0f}%, 40 sessions): {j.wait_excess_40.mean():+.2f}pp; "
           f"washout entry minus wait {d.mean():+.2f}pp t {tstat(d):+.2f} (n {len(j)})")

    # every washout day, date-clustered (descriptive; overlapping)
    wd = breadth[breadth < LO].index
    ex = [excess_on(d, 40) for d in wd]
    ex = pd.Series([r["excess"] for r in ex if r], dtype=float)
    pr(f"  every washout day ({len(wd)} days, overlapping, descriptive): 40d excess {ex.mean():+.2f}pp")

    pr(f"\n## TODAY: breadth {breadth.iloc[-1]:.1f}% on {breadth.index[-1].date()}; "
       f"in an episode since {E.episode.iloc[-1] if len(E) else '-'}; STRONG names that day: {int(near.loc[breadth.index[-1]].sum())}")
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
