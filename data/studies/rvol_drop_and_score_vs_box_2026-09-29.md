# Two questions about the precision tier: (1) drop the RVOL gate? (2) a fitted score vs the box (2026-09-29)

## Pre-registration (written BEFORE either run; do not edit this section after the results)

**Why.** Gabe: "my main concern is keeping a variable that doesn't add any statistical value", then "run both".
Leave-one-out ablation (9/24) found 0 of 9 tier gates earn their place individually, but the tier as a conjunction is the
book's one equity selection pass. (1) asks whether RVOL does joint work; (2) asks whether a continuous, walk-forward
score beats the hard-threshold box at all.

**Common.** `liquid_panel_2009`; eligibility 50-day ADDV ≥ $50M, price ≥ $5, not suspect. House trade: buy the close;
stop = min(day low, close × 0.98) judged on the close; exit on a close under the stop or the 20 EMA; 60-session cap;
5 bp/side; R capped ±20. **Control (both tests):** for each signal, 3 random same-date eligible names in the signal's
ADR tercile that are not signalling that day, bought at the same close with the same stop % and exit; excess = signal R
− control mean (seed 20260929). t = month-clustered (monthly mean excess, t on months).

### T1 — does RVOL do joint work?
A = the precision tier exactly as `run_precision_tier_control.build()` (RVOL ≥ 1.1 included). B = the same with the RVOL
gate removed. X = B \ A (breakouts rejected only by RVOL). Window: signals 2010-01 → 2026-06.
**Rule (declared now): DROP RVOL iff X's mean excess ≥ 0.5 × A's mean excess AND X's excess is ≥ 0 in both halves
(2010–2017 / 2018–2026). Otherwise KEEP.** Reported: A, B, X excess and t; counts.

### T2 — fitted score vs the box
**Pool** = every eligible first close ≥ the prior-15-session high (prior close below it) — the breakout EVENT only, with
none of the tier's filters. **Features** (continuous versions of the gates): ADR, 52-week range %, RVOL, close position in
the day's range, EMA-stack age (0 if not stacked), gap, day's change, distance from the 52-week high, log 50-day ADDV.
**Model:** ridge regression (α = 1 on standardised features) of R (clipped ±5 for fitting only) on the features.
**Walk-forward:** for each year Y = 2012 … 2026, fit on pool signals entered ≥ 90 calendar days before Jan 1 of Y
(every exit known), predict year Y. **SCORE arm:** each year, select signals whose predicted value ≥ the training-sample
quantile that makes the selected share equal the BOX's share of the pool in the training years (no look-ahead in the count).
**BOX arm:** the precision tier (A) on the same pool, same years.
**PRIMARY:** monthly mean excess (SCORE) − monthly mean excess (BOX), over months where both trade; **t ≥ 3**, both halves
(2012–2018 / 2019–2026) > 0 → the score beats the box. Also reported: each arm's own excess vs control and t; the fitted
coefficients per year (stability); rank correlation of predicted vs realised R out of sample.
**Charge:** two tests, one primary each; the house |t| ≥ 3 governs T2; T1 is a decision rule, not a significance claim.
**Prior:** T1 — neutral-to-drop (X ≈ tier in the ablation). T2 — low (within-date ranking 72 cells NULL; features do not
sort outcomes); a flexible model would fit noise, which is why the model is linear and ridge-shrunk.
Local, ~1.5–2 h.

---

## Results (run 2026-09-29, after effa552; `run_rvol_drop_and_score.py`, `.log`)

226,668 breakout events 2010–26 (the pool). "excess" = trade-weighted mean excess R; t and halves = month-weighted
(the pre-registered clustering) — the two disagree in sign, which is the book's known shape (the tier's return lives in
a few busy months; the multiple-testing correction already recorded the tier as month-weighted −0.04).

### T1 — RVOL: rule says KEEP, but the test cannot tell A from X
| set | n | mean R | excess (trade-wtd) | month t | halves (month-wtd) |
|---|---|---|---|---|---|
| A tier (RVOL ≥ 1.1) | 2,303 | +0.309 | +0.365 | −2.21 | −0.50 / −0.03 |
| B tier without RVOL | 4,644 | +0.334 | +0.324 | −2.04 | −0.46 / −0.01 |
| **X = rejected only by RVOL** | 2,341 | **+0.358** | **+0.283** | −1.44 | −0.45 / −0.04 |

Rule: X excess +0.283 ≥ 0.5 × A (+0.183) ✔, but X's halves are negative ✘ → **KEEP RVOL** as pre-registered.
⚠ The halves condition fails for the tier itself (A −0.50 / −0.03), so it cannot separate X from A. On every statistic X
≈ A (mean R +0.36 vs +0.31; month t −1.44 vs −2.21). **Honest read: RVOL does no measurable joint work; removing it
doubles the signal count at the same quality.** The KEEP is a rule artefact, disclosed rather than overridden.

### T2 — fitted score vs the box: FAIL
| arm (OOS 2012–26) | n | mean R | excess (trade-wtd) | month t |
|---|---|---|---|---|
| SCORE (walk-forward ridge) | 1,545 | +0.091 | +0.095 | +0.16 |
| BOX (precision tier) | 2,222 | +0.347 | +0.384 | −1.73 |

**PRIMARY SCORE − BOX monthly excess +0.186R, t 1.21** (143 months), halves +0.61 / −0.09 → **FAIL**. The score does
predict R across the whole pool (OOS rank correlation +0.13), but what it learns is mostly the R denominator: its largest
coefficients are ADR (−) and the day's change (+), i.e. breakouts whose day-low stop is tight relative to the move — an
R-scaling effect (the house rule: judge stop-width effects in percent, not R). It selects entirely different trades
(0 overlap with the tier) and earns less per trade. A continuous model is not better than the box.

**What it means for the book now.** (1) RVOL is Gabe's call on a principle, not on evidence: the data can't distinguish
the tier with or without it, and dropping it roughly doubles the list. (2) Keep the box; a fitted score adds nothing.
(3) Reminder the test surfaced: month-weighted, the tier's excess over random same-date names is negative 2010–26; its
positive trade-weighted mean comes from busy breakout months.
