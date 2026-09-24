# ADX ≤ 12 holdout and Qullamaggie's partial-then-trail exit [WL-4] — 2026-09-23

Both ran locally. The ADX holdout needed a 2009+ rebuild of the liquid panel: `run_build_liquid_panel.py --start
2009-01-01 --out data/cache/liquid_panel_2009.parquet`, 1,728 names, ~90 s. The existing 2019 panel is untouched.

## 1. ADX(14) ≤ 12 gate on the house breakout — HOLDOUT (`run_adx_gate_holdout.py`, log `logs/adx_gate_holdout.log`)

**Verdict: NOT CONFIRMED · PARKED (same sign, about half the size, below the bar).**

The lead came from an exploratory cell in WL-3a (2019-10 → 2026-09): +1.48pp vs same-date other-name breakouts,
t 2.87. The holdout is **2010-01 → 2019-09**, years the lead never saw, with identical definitions. It was
pre-registered before the 2009 panel was opened.

| | breakouts | gated | diff (same date, other names) | t | halves (<2015 / ≥2015) |
|---|---|---|---|---|---|
| **PRIMARY: holdout 2010-01 → 2019-09** | 12,802 | 3.5% | **+0.80pp** | **+1.49** | +0.06 / +1.49 |
| consistency: this panel, 2019-10+ | — | 4.7% | +1.40pp | +2.71 | +0.70 / +1.98 |

- **Holdout per year (diff, pp):** positive in 7 of 10 years: 2010 +0.23, 2011 +0.61, 2012 +0.43, 2013 +0.72, 2014 −1.85,
  2015 +2.29, 2016 +3.04, 2017 −5.32 (6 dates), 2018 +3.06, 2019 −0.97.
- **Held-the-level share:** 16.0% vs 14.5% (+1.5pp, t 0.74).
- **Harness on the holdout (paired rule):** vs `post` best arm ema20 paired t **2.68**, halves +0.14/+0.26,
  **p_search 0.038**. vs `xname` t 1.83, p 0.11. Neither passes.
- **Neighbourhood (holdout):** ADX ≤ 15 +0.76 (t 2.36), ADX(20) ≤ 12 +0.85 (t 2.26), ADX ≤ 10 −1.19 (t −1.19, 0.7%
  share), ADX(10) ≤ 12 +0.43 (t 0.53). A broad positive shoulder, not a sharp cell.
- **Mechanism medians:** gated breakouts are slightly *more* extended (0.37 vs 0.30 ADR) with wider stops (0.84 vs
  0.74 ADR), so this is not the entry-extension effect in disguise.

**Reading:** a breakout out of a trendless tape is *directionally* better in both eras, but the holdout effect is
about half the in-sample one and nowhere near t 3. By the pre-registered rule (t ≥ 3 = adopt; ~2 with both halves
positive = supported), this is **below "supported"**. Park it; don't gate the desk on it. It would be worth re-scoring
on the forward lockbox (data from 2026-09-22) alongside the two paired-rule candidates.

Side fact: the house breakout itself averaged **−0.27% per trade over 2010–2019** on this panel (vs +0.57% for
2019-10+), despite a universe that is survivorship-biased *toward* winners. The breakout's positive mean is a 2020s
phenomenon on this panel.

## 2. [WL-4] Qullamaggie's own partial-then-trail exit (`run_qullamaggie_exit.py`, log `logs/qullamaggie_exit.log`)

**Verdict: INVERTED · YIELD MECHANISM.** Every one of his variants loses to the house 20-EMA trail, significantly, in
both pools. Both halves are negative in the primary pool; in the generic pool the loss sits mostly in the 2023+ half.

His spec from the Chat With Traders interview:
- sell 20–25% into the first burst;
- stop to breakeven;
- trail the 10-day (ADR ≥ 5) or 20-day SMA, **only once the MA has caught up to the stop**;
- exit on the first close below it.

The pool is the profit-lock pool: 1,958 precision-tier trades, close entry, day-low stop, 2% risk floor. BASE
reproduces the in-book figure (R cap 20 = +0.402).

**Primary cell (pre-named): `Q_DAY5_P33` − BASE = −1.87pp per trade, t −4.39, halves −0.93 / −2.47; R −0.42 (t −4.17).**

| arm (precision pool) | % / trade | arm − BASE (pp) | t | halves | R − BASE | give-back |
|---|---|---|---|---|---|---|
| BASE (20-EMA trail) | **+2.72** | — | — | — | — | 38.4% |
| Q_NOPARTIAL (delayed trail only) | +1.54 | −1.18 | −3.47 | −0.63 / −1.53 | −0.27 | 35.8% |
| Q_BURST_P20 / P33 / P50 | +1.30 / +1.15 / +0.96 | −1.42 / −1.57 / −1.76 | −3.8 / −4.0 / −4.1 | all − | −0.33…−0.41 | 28–31% |
| Q_DAY3_P20 / P33 / P50 | +0.78 / +0.65 / +0.48 | −1.94 / −2.07 / −2.24 | −4.5 / −4.6 / −4.6 | all − | −0.43…−0.51 | 30–43% |
| Q_DAY5_P20 / P33 / P50 | +1.00 / +0.85 / +0.65 | −1.72 / −1.87 / −2.07 | −4.2 / −4.4 / −4.5 | all − | −0.38…−0.47 | 27–36% |
| SELLALL_D3 / D5 | −0.04 / +0.05 | −2.76 / −2.68 | −4.5 / −4.6 | all − | −0.63 / −0.61 | 24% / 21% |

- **Generic pool (7,641 trades):** same picture. Every arm is −0.37 to −0.71pp (t −3.55 to −4.46); BASE +0.57%.
  First halves are near zero (−0.24 to +0.28pp; the sell-all arms are slightly positive pre-2023). Second halves are
  all −0.45 to −1.26pp.
- **Per year (precision):** his arms trail BASE in essentially every year. The worst years are 2024–25
  (−3 to −5pp), the years big winners carried the book.
- **Drawdown:** the partials lower max drawdown only slightly (fixed-size curve 600–690 vs 670). Total return falls
  from 5,326 to 934–3,014.

**Reading:**
1. **The partial costs because the book's edge is in the right tail.** Selling 20–50% into the first burst caps
   exactly the trades that pay for everything else. Give-back falls (fewer round trips to ≤ 0), but that's the
   comfort, not the money. This is the profit-lock result (trims −0.25…−0.33R) again, on his exact spec.
2. **The delayed-activation trail is also worse (−1.18pp, t −3.47).** Waiting for the SMA to catch up to the stop
   leaves failing breakouts on the day-low stop longer. The house trail cuts them the first time they close under the
   20 EMA. The "fast trails lose" objection to the old test was fair in principle, but his version loses anyway.
3. **His sell-everything momentum-burst style is the worst of all (−2.7pp):** the house book is a trend-riding book.

This settles the queued "Qullamaggie partial-then-trail" row (TEST_INDEX §10) and the Breitstein relay claim.
**Keep the house 20-EMA trail.**
