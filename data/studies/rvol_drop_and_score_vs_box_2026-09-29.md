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
