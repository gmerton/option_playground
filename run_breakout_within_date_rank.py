#!/usr/bin/env python3
"""
Can we RANK today's breakout candidates against each other? (pre-registered 2026-09-22)

THE GAP THIS FILLS. `breakout_hold_predictors_2026-09-20.md` scored 9 book features as POOLED THRESHOLD
gates and found nothing (best: distance to the 21 EMA, +0.057R over baseline, t ~2, ~3.5% of the available
spread; gates do not stack; `sma_stacked` inverts). But a pooled threshold is not the decision a trader
makes. The decision is CROSS-SECTIONAL and made inside one day: "there are 14 candidates on the screen
this morning, which 2 do I take?" An absolute threshold conflates the day with the name -- on a hot tape
every candidate has high rvol, on a dead tape none does -- so a feature can be useless as a cutoff and
still rank correctly within a session. That test has never been run on the breakout book.

PRECEDENT IN THIS REPO: exactly this reframe already paid once. Credit/width failed as a gate but ranks
single-name bull puts cross-sectionally, +7.6pp within-date (OptionsPlay KB). Same shape, different book.

WHY IT MATTERS STRATEGICALLY. The book fires 43,970 breakouts over 7 years = ~6,280/yr = ~25/day. No
discretionary trader runs that. Taking the top 2 per day is ~516/yr -- an actual book. If ranking works at
all, it converts a population statistic into something a person could trade; if it fails, that is strong
evidence the breakout average is unimprovable by selection and the answer is fewer, larger, discretionary
bets (which is where the ledger already points).

DESIGN
  Universe: the 43,970 cached house breakouts, 2019-02-13 -> 2026-09-11, 1,809 sessions.
  For each date, rank that day's candidates by feature f and take the top N (N = 1, 2, 3, 5).
  Eligibility: a date is used only if it has M >= max(5, 2N) candidates, so the "selection" is real.

  CONTROL: the same day's mean R over ALL its candidates. This is exact, not simulated -- the expectation
  of drawing N at random from that day IS the day's mean, so the day mean is the unbiased null and it holds
  the DAY constant. A rule cannot win here by picking good days; only by picking better names within a day.

  Statistic: per-date delta = mean R(top N) - mean R(all candidates that day); t across dates (date is the
  clustering unit, since picks inside a day share the tape).

BAR (house): |t| >= 3, both halves positive, and it must survive the multiple-testing charge below.

MULTIPLE TESTING, declared BEFORE running: 9 features x 2 directions x 4 values of N = 72 cells. Sidak
over 72 at alpha 0.05 needs p <= 0.000713 (|t| ~ 3.39). So the house |t| >= 3 is NOT sufficient here and
the corrected threshold governs.

PRIMARY (one cell, declared now, everything else is exploratory): the COMPOSITE rank at N = 2 --
mean of the within-date percentile ranks of (dist_21ema_ADR ascending) and (rvol20 descending), the two
features with a prior in this book. Reported first, judged at |t| >= 3 without the 72-cell charge.

PRE-DECLARED DIRECTIONS (from prior results, not fitted here):
  dist_21ema_ADR      ascending  -- closer to the 21 EMA is better (August location rule; best gate found)
  ext_above_level_ADR ascending  -- less extended is better (the 2.6-ADR entry finding)
  rvol20              descending -- more volume is better (rotation study raised the gate 1.2 -> 1.8)
  pct_off_52w_high    ascending  -- nearer the 52-week high is better (O'Neil)
  adr_pct             descending -- more range is better (universe test used ADR >= 4)
  range_pos, gap_ADR, sma_stacked, dolvol_musd -- NO prior, both directions exploratory only.
  (range_pos is expected flat: close_strength_2026-09-22 showed close-in-range does not sort.)

DIAGNOSTIC (not a test): does the entry-extension penalty survive selection? Report the selected group's
mean ext_above_level_ADR against the day mean. If ranking works but the picks are MORE extended, the
ranking is fighting the known entry leak rather than compounding with it.

NOT using lib.studies.pattern_test: the harness owns bar-level fills, arms and same-name controls for a
NEW pattern. This re-scores an existing, already-harnessed pattern's cached output under a different
selection rule, so the harness would add nothing and its same-name control is the wrong null here.

Usage: PYTHONPATH=src .venv/bin/python3 -u run_breakout_within_date_rank.py \
         > data/studies/breakout_within_date_rank_2026-09-22.log 2>&1
"""
from __future__ import annotations

import warnings
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)

REPO = Path(__file__).resolve().parent
PANEL = REPO / "data/cache/breakout_hold_features.parquet"
OUT = REPO / "data/studies/breakout_within_date_rank_2026-09-22.csv"

FEATURES = {
    "dist_21ema_ADR":      "asc",
    "ext_above_level_ADR": "asc",
    "rvol20":              "desc",
    "pct_off_52w_high":    "asc",
    "adr_pct":             "desc",
    "range_pos":           None,
    "gap_ADR":             None,
    "sma_stacked":         None,
    "dolvol_musd":         None,
}
TOPNS = [1, 2, 3, 5]
N_CELLS = 9 * 2 * 4
SIDAK_T = float(stats.norm.ppf(1 - (1 - (1 - 0.05) ** (1 / N_CELLS)) / 2))


def load() -> pd.DataFrame:
    d = pd.read_parquet(PANEL)
    d["date"] = pd.to_datetime(d["date"])
    d["composite"] = np.nan
    # within-date percentile ranks for the two features with a prior
    a = d.groupby("date")["dist_21ema_ADR"].rank(pct=True, ascending=True)
    b = d.groupby("date")["rvol20"].rank(pct=True, ascending=True)
    d["composite"] = (a + (1.0 - b)) / 2.0     # low = near 21 EMA AND high rvol
    return d


def score(d: pd.DataFrame, col: str, ascending: bool, n: int) -> dict:
    """Per-date: mean R of the top n by `col`, minus that day's mean R over all candidates."""
    use = d.dropna(subset=[col])
    sizes = use.groupby("date")["R"].transform("size")
    use = use[sizes >= max(5, 2 * n)]
    if use["date"].nunique() < 100:
        return {}

    ranked = use.sort_values(["date", col], ascending=[True, ascending])
    picks = ranked.groupby("date").head(n)

    sel = picks.groupby("date")["R"].mean()
    day = use.groupby("date")["R"].mean()
    delta = (sel - day).dropna()
    if len(delta) < 100:
        return {}

    t = float(delta.mean() / delta.std(ddof=1) * np.sqrt(len(delta)))
    half = len(delta) // 2
    h1, h2 = delta.iloc[:half].mean(), delta.iloc[half:].mean()

    ext_sel = picks.groupby("date")["ext_above_level_ADR"].mean()
    ext_day = use.groupby("date")["ext_above_level_ADR"].mean()

    return {
        "feature": col, "dir": "asc" if ascending else "desc", "N": n,
        "dates": len(delta), "sel_meanR": sel.mean(), "day_meanR": day.mean(),
        "delta": delta.mean(), "t": t, "h1": h1, "h2": h2,
        "both_halves": np.sign(h1) == np.sign(h2) == 1,
        "passes": (t >= SIDAK_T) and (np.sign(h1) == np.sign(h2) == 1),
        "ext_vs_day": ext_sel.mean() - ext_day.mean(),
    }


def main() -> None:
    d = load()
    print(f"panel {len(d):,} breakouts, {d.date.nunique():,} sessions, "
          f"{d.date.min().date()} -> {d.date.max().date()}, pooled meanR {d.R.mean():+.4f}")
    print(f"multiple testing: {N_CELLS} cells, Sidak alpha 0.05 -> |t| >= {SIDAK_T:.2f} "
          f"(the house |t| >= 3 alone is NOT enough here)\n")

    print("=" * 110)
    print("PRIMARY (declared in advance): composite rank (near 21 EMA + high rvol), N = 2, bar |t| >= 3")
    print("=" * 110)
    p = score(d, "composite", True, 2)
    if p:
        print(f"  dates {p['dates']:,}   selected meanR {p['sel_meanR']:+.4f}   day meanR {p['day_meanR']:+.4f}")
        print(f"  delta {p['delta']:+.4f}R   t {p['t']:+.2f}   halves {p['h1']:+.4f} / {p['h2']:+.4f}"
              f"   -> {'PASS' if abs(p['t']) >= 3 and p['both_halves'] else 'FAIL'}")
        print(f"  extension diagnostic: picks sit {p['ext_vs_day']:+.3f} ADR vs the day's mean candidate")
    print()

    rows = [r for f, pri in FEATURES.items() for asc, n in product([True, False], TOPNS)
            if (r := score(d, f, asc, n))]
    res = pd.DataFrame(rows).sort_values("t", ascending=False)
    res.to_csv(OUT, index=False)

    print("=" * 110)
    print(f"EXPLORATORY: all {len(res)} cells, sorted by t (prior direction in brackets)")
    print("=" * 110)
    show = res.copy()
    show["prior"] = show.feature.map(lambda f: FEATURES.get(f) or "-")
    show["on_prior"] = np.where(show.prior == "-", "", np.where(show.prior == show.dir, "yes", "no"))
    print(show[["feature", "dir", "prior", "on_prior", "N", "dates", "sel_meanR", "day_meanR",
                "delta", "t", "h1", "h2", "both_halves", "passes", "ext_vs_day"]].round(4).to_string(index=False))

    n_pass = int(res.passes.sum())
    print(f"\ncells clearing the corrected bar (|t| >= {SIDAK_T:.2f} AND both halves positive): {n_pass} of {len(res)}")
    exp_noise = len(res) * 2 * (1 - stats.norm.cdf(SIDAK_T))
    print(f"expected under pure noise at this threshold: {exp_noise:.2f} cells")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
