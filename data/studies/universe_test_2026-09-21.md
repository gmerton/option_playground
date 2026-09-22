# Universe test: Ariel momentum scan vs our Trend Template + 2 hybrids (2026-09-21)

**Verdict: no arm clears the bar. HYB-B = PARKED (best selection, survives ADR matching, beats both parents in both
halves, t 2.6). HYB-A = NULL (its lead was mostly ADR). Our current Trend Template is the WEAKEST of the five on
selection. No universe makes the breakout entry work. YIELD: MECHANISM (speed explains part of "momentum").**

Pre-registered spec: `data/ariel_hernandez/analysis/2026-09-21_universe_list_review.md` (written before the run).
Script `run_universe_test.py`; log `universe_test_2026-09-21.log`; tables `universe_test_q1*.csv`, `universe_test_q2*.csv`.
Liquid panel (1,742 names, ADDV ≥ $50M), membership as of the PRIOR close, window 2020-01 → 2026-09, split 2023-01-01.

## Arms (as pre-registered)

| arm | definition | names/day median (p10–p90) | monthly turnover | median ADR |
|---|---|---|---|---|
| TT | Trend Template, RS ≥ 70, $200M | 66 (28–108) | 40% | 2.8% |
| AH | ≥70% off 52w low, > 50 SMA, ≥2M sh, > $7, $100M | 72 (19–148) | 40% | 3.7% |
| INT | TT ∩ AH | 35 (9–62) | 39% | 3.5% |
| HYB-A | AH + > rising 200 SMA + ADR ≥ 4% | 20 (5–65) | 51% | 5.6% |
| HYB-B | TT at $100M + ADR ≥ 4% | 18 (5–66) | 53% | 5.2% |

## Q1. Does the universe select? (member forward return minus the eligible panel, same dates, %)

20-session horizon, non-overlapping dates (~80 = the effective n). "ADR-matched" subtracts the mean of panel names in
the same ADR decile on the same date, so a basket can't win just by being fast. This check was NOT pre-registered;
it's a mechanism diagnostic, reported because the hybrids select on ADR.

| arm | raw excess | t | halves | **ADR-matched excess** | t | halves |
|---|---|---|---|---|---|---|
| TT | +0.48 | 1.00 | +0.72 / +0.29 | **+0.56** | 1.30 | +0.58 / +0.54 |
| AH | +1.07 | 2.08 | +0.98 / +1.15 | **+0.87** | 2.14 | +1.04 / +0.73 |
| INT | +1.60 | 2.47 | +1.81 / +1.46 | **+1.44** | 2.47 | +1.63 / +1.31 |
| HYB-A | +1.94 | 1.91 | +1.27 / +2.49 | **+1.19** | 1.73 | +1.00 / +1.35 |
| HYB-B | +2.17 | 2.33 | +1.66 / +2.57 | **+1.79** | **2.60** | +1.77 / +1.80 |

5-session horizon ranks the same (INT/HYB-A/HYB-B top, TT last, all t < 2.4). Every arm is positive in both halves;
none reaches t 3.

## Q2. House breakout inside each universe (close entry, day-low stop, hold 60; R)

| universe | n | ema20 trail meanR | t | edge vs same-name later day | edge vs random in-universe name | halves |
|---|---|---|---|---|---|---|
| all breakouts | 8,152 | −0.117 | −0.65 | −0.105 | −0.016 | −0.28 / −0.02 |
| TT | 1,517 | −0.066 | 0.10 | −0.023 | +0.055 | −0.03 / −0.09 |
| AH | 2,499 | +0.008 | 1.17 | −0.061 | +0.151 | −0.19 / +0.13 |
| INT | 1,192 | +0.078 | 1.76 | +0.079 | +0.154 | +0.12 / +0.05 |
| HYB-A | 1,229 | +0.170 | 2.63 | +0.040 | +0.287 | −0.02 / +0.27 |
| HYB-B | 1,221 | +0.004 | 1.92 | +0.004 | +0.185 | +0.00 / +0.01 |

No arm passes the harness bar (beats its control, both halves positive, |t| ≥ 3). A better universe lifts the
breakout from −0.12R to about 0, but the breakout DAY still isn't a better entry than a random later day in the same
name (edge vs post ≈ 0 everywhere). This restates "we select well, we enter badly": the universe is where the return
is, not the trigger.

## Pre-registered hybrid rule

"A hybrid must beat BOTH parents in BOTH halves on Q1 (20d) or Q2 (ema20)."
- **HYB-A:** passes on raw Q1 and on Q2 meanR, but on the ADR-matched Q1 its first half (+1.00) is below AH (+1.04),
  and its Q2 first half is negative. The lead is mostly speed → **NULL.**
- **HYB-B:** passes on raw Q1 AND on ADR-matched Q1 (+1.77 / +1.80 vs parents' best +1.04 / +0.73); fails Q2.
  t 2.6 on ~77 dates → **PARKED** (below the t 3 bar).

## What it means

1. **Our Trend Template is the weakest universe** of the five on selection (+0.56% ADR-matched, t 1.3). The binding
   costs are its $200M floor and its slow large-cap tail; HYB-B keeps the template's structure and fixes both.
2. **Candidate change (PARKED, not adopted):** preferred list = Trend Template at a $100M floor with ADR ≥ 4%.
   ⚠ It's small: median 18 names on the liquid panel (5 in a weak tape), 46 on the full Polygon universe on 9/18,
   and it turns over half its names a month.
3. **Ariel's scan beats ours** (+0.87 vs +0.56 ADR-matched) but not significantly, and his groups-first step wasn't
   tested here (our rotation study inverts it).
4. **No universe fixes the entry.** Keep the desk's fixed small sizing and 21 EMA location rule.

⚠ Survivorship: the panel is today's liquid names, so compare arms with each other, not as absolute returns. RS
percentile is ranked inside the liquid panel, not the ~5k Polygon universe production uses (stricter). 5 ledger rows
added (one per arm, post control).
