# Can we rank today's breakout candidates against each other? (2026-09-22) — **NULL**

**Verdict: NULL** (primary), with one PARKED era-bound cell and one ⭐ MECHANISM/REFRAME yield.
Scripts: `run_breakout_within_date_rank.py`, pre-registered in its docstring before running.
Log: `breakout_within_date_rank_2026-09-22.log` · cells: `breakout_within_date_rank_2026-09-22.csv`

## The question

`breakout_hold_predictors_2026-09-20.md` scored 9 book features as **pooled threshold gates** and found
nothing (best: distance to the 21 EMA, +0.057R, t ~2, ~3.5% of the available spread; gates do not stack).
But a pooled threshold is not the decision a trader makes. The real decision is **cross-sectional and inside
one day**: "there are 14 candidates on the screen this morning — which 2 do I take?" An absolute cutoff
conflates the day with the name (on a hot tape everything has high rvol), so a feature can be useless as a
threshold and still rank correctly *within* a session.

Precedent: this exact reframe already paid once in this repo — credit/width fails as a gate but ranks
single-name bull puts cross-sectionally, +7.6pp within-date (OptionsPlay KB).

It also matters strategically. The book fires 43,970 breakouts in 7 years ≈ 25/day; nobody trades that.
**Top-2-per-day is ~516/yr — an actual book.** If ranking works, the population statistic becomes tradeable.

## Design

43,970 cached house breakouts, 2019-02-13 → 2026-09-11, 1,809 sessions. For each date, rank that day's
candidates by a feature and take the top N (1/2/3/5); a date counts only if it has M ≥ max(5, 2N) candidates.

**Control = that day's mean R over all its candidates.** This is exact rather than simulated: the expectation
of drawing N at random from the day *is* the day mean. It holds the DAY constant, so nothing can win here by
picking good days — only by picking better names within a day. Statistic: per-date delta, t across dates.

**Multiple testing declared in advance:** 9 features × 2 directions × 4 N = 72 cells → Šidák at α 0.05 needs
**|t| ≥ 3.38**, so the house |t| ≥ 3 is *not* sufficient. One primary cell was named before running.

## Result 1 — the primary fails flat

Composite rank (near the 21 EMA **and** high rvol — the two features with a prior), N = 2, 1,442 dates:

| | selected | day mean | delta | t | halves |
|---|---|---|---|---|---|
| composite, top 2 | +0.0477R | +0.0503R | **−0.0026R** | **−0.11** | +0.0069 / −0.0121 |

Not weak — *absent*. The two features this book most believes in do not rank candidates against each other.

## Result 2 — 71 of 72 cells fail

One cell clears the corrected bar against 0.05 expected under pure noise: **dollar volume, descending**.
The family is internally monotone, which is what a real effect looks like:

| N | delta | t | halves | passes Šidák |
|---|---|---|---|---|
| 1 | +0.1241 | 3.34 | +0.070 / +0.178 | no |
| **2** | **+0.0888** | **3.48** | +0.044 / +0.134 | **yes** |
| 3 | +0.0613 | 2.97 | +0.034 / +0.088 | no |
| 5 | +0.0475 | 2.77 | +0.032 / +0.063 | no |

### It is not an ADR/size artefact — but it IS an era

The obvious confound is "this just picks low-volatility mega caps." **That is ruled out.** Ranking by dollar
volume *within* each (date, ADR tercile) still works, and the picks are not less volatile:

| | delta | t |
|---|---|---|
| ADR tercile 0 (median 3.3%) | +0.0613 | 1.56 |
| ADR tercile 1 (median 4.1%) | +0.1053 | 2.46 |
| ADR tercile 2 (median 5.9%) | +0.1054 | 2.75 |

Within-date Spearman(dolvol, ADR) = 0.13; top-2 picks median ADR 4.24% vs day 4.07%.

**But by year it collapses:**

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| +0.077 (t 1.19) | +0.087 (1.15) | +0.030 (0.42) | **−0.007 (−0.13)** | +0.024 (0.35) | +0.071 (1.04) | +0.167 (2.33) | +0.239 (2.80) |

Six of eight years are weak or negative. **All of the edge is 2025–26** — the mega-cap concentration era — and
2026's own halves are +0.485 / −0.007, so even inside 2026 it is front-loaded. The pooled both-halves test
passed only because the sample's back half *is* that era: 2025–26 supply 17,518 of 43,970 breakouts (40%) in
the last 1.7 years. ⟹ **PARKED as a regime bet, not adopted as a selection rule.** Same shape as the
crash-leader finding (a regime bet wearing a selection costume) and the retrospective's trailing-30d rules.

## ⭐ Result 3 — extension is a TIMING variable, not a SELECTION variable

The sharpest yield. `ext_above_level_ADR` **ascending** — our own prior direction, "less extended is better,"
straight from the 2.6-ADR entry finding — is **negative at every N** within-date:

| N | 1 | 2 | 3 | 5 |
|---|---|---|---|---|
| delta | −0.0622 | −0.0343 | −0.0278 | −0.0143 |
| t | −2.06 | −1.64 | −1.54 | −0.95 |

Picking the *least extended* of today's candidates makes things **worse**. This does not contradict
`entry_vs_stop_2026-09-20.md` — it sharpens it. That study held the name fixed and moved the clock: for **one
name**, waiting for a retrace to a lower extension is better. This one holds the clock fixed and moves the
name: **across names on the same day, the less-extended candidate is the weaker one** (it is less extended
partly because it is moving less). Extension answers *when to buy this name*, never *which name to buy*.

Note the passing dolvol cell agrees: its picks sit **+0.36 ADR more extended** than the day's average
candidate and win anyway.

## What this means

1. The reframe does not rescue the breakout book. Selection from the book's own features — threshold *or*
   within-date rank — does not improve the +0.014R average. Combined with the bimodality result (the +1.27R
   cohort is unknowable at entry), **the breakout average is what it is.**
2. This is evidence *for* the strategic read of 2026-09-22: if mechanical selection cannot improve a 44k-event
   book, the path is fewer and larger discretionary bets with strict execution, not a better screen.
3. Stop using extension as a cross-sectional filter anywhere on the desk. It is a timing variable only.

## Open / next

* **Dollar volume, honestly tested.** Needs a benchmark it never got here: does top-2-by-dolvol beat
  *buy-and-hold the same names*, and beat a large-cap index, over 2025–26? Until then it may be long mega-cap
  beta in the era that rewarded it. Do not build a screener on it.
* Untested: ranking on features **not** in this panel (theme/industry strength, catalyst presence, days since
  the base started). The panel's 9 features are exhausted.
