# IV rank vs credit/width: which sorts single-name bull put spreads? (2026-09-22) — **cw wins, ivr NULL**

**Verdict: credit/width survives, IV rank does not.** Pre-registered in `run_ivrank_vs_cw.py` before the
first run. Log + cells: `ivrank_vs_cw_2026-09-22.log` / `.csv`.
6,419 spreads · 20 names · 365 dates · 90 months. 30Δ short / 20Δ wing held fixed, credit at a real fill
(short bid − long ask − commissions), held to expiry, RAW spot from the chain.

## Why

Two creators give two different cross-sectional sorts for the same trade and we had tested only one.
OptionsPlay ranks by **credit / width** — tested and ADOPTED (top−bottom +8.57pp t 3.74; within-date
+7.64pp t 4.15; cleared Šidák by a hair). Sosnoff, in the 2024-10-14 OptionsPlay interview, selects by
**IV rank** ("only sell premium in high-IV-rank names") — and in the same hour denies cross-sectional
richness exists at all. The question was never "does IV rank work" but **"does it add anything beyond
credit/width"**, since cw's mechanism *is* entry IV.

⭐ It mattered even under a hostile prior: **IV rank needs no option chain**, so if it were competitive it
would be far cheaper to screen live.

## Primary (one cell, declared in advance): the joint fit

Month-clustered regression of net ROC on both standardised sorts.

| model | | |
|---|---|---|
| `roc ~ zcw` | zcw **+2.36pp (t +2.40)** | |
| `roc ~ zivr` | zivr −1.54pp (t −1.00) | |
| **`roc ~ zcw + zivr`** | zcw **+2.62pp (t +2.81)** | zivr −1.89pp (t −1.25) |
| within-date (date-demeaned) | zcw **+2.97pp (t +4.01)** | zivr +0.25pp (t +0.22) |

**cw survives. ivr does not, and within-date it is flat.**

Credit/width also **replicated**: marginal top−bottom +7.84pp, month-clustered **t +3.56**, both halves
positive (+9.16 / +6.40); the within-date +2.97pp t 4.01 matches the +7.64pp t 4.15 of the original run.

## ⚠ IV rank produced exactly the trap the pre-registration existed to catch

Its marginal quintile spread reads **+13.32pp, t +3.47** — and it is an artefact.

| ivr quintile | 0 (low) | 1 | 2 | 3 | 4 (high) |
|---|---|---|---|---|---|
| net ROC % | **+6.37** | +1.53 | +6.80 | −0.93 | **+1.03** |
| win % | 83.5 | 79.0 | 82.8 | 75.5 | 76.7 |

Non-monotone, and **pooled it runs backwards from the claim** — the *lowest* IV-rank quintile earned the
most. The +13.32pp comes from month-matching two extreme buckets that live in different months (IV rank is
high market-wide during stress), so an extremes comparison manufactures a spread that the full-sample and
within-date fits both reject. Without the declared primary this would have been read as a finding.

**Methodological note worth keeping: a month-matched extremes spread is not evidence when the underlying
quintile shape is non-monotone.** Same family of error as the dollar-volume cell in the within-date
ranking study, which looked significant pooled and collapsed by year.

## ⭐ The double sort makes the mechanism visible

Mean net ROC %, rows = credit/width quintile, columns = IV-rank quintile:

| | ivr 0 | ivr 1 | ivr 2 | ivr 3 | ivr 4 |
|---|---|---|---|---|---|
| **cw 0** | 2.51 | −3.29 | 5.20 | −13.29 | −3.93 |
| **cw 1** | 5.15 | 5.98 | 6.53 | 0.15 | −0.14 |
| **cw 2** | 8.43 | 3.66 | 4.35 | −2.26 | 2.86 |
| **cw 3** | 8.81 | 1.70 | 6.34 | 5.14 | 1.65 |
| **cw 4** | **9.83** | 0.78 | 11.49 | 0.94 | 2.30 |

Down the **lowest**-IV-rank column, credit/width sorts perfectly monotonically (2.51 → 9.83).
⟹ **Credit/width works best precisely where Sosnoff says not to trade.** Across any cw row, IV rank
sorts nothing.

## Why ivr cannot rank cross-sectionally

`corr(cw, iv) = +0.474` but `corr(cw, ivr) = only +0.136`.

Credit/width is an absolute, dimensionless price of implied richness and is therefore comparable across
names. **IV rank is own-history-relative**: a 90th-percentile TLT and a 90th-percentile TSLA are not the
same object, so the sort has no common scale. That is the whole result, and it was the stated prior.

## What to do

* **Keep ranking on credit/width.** Unchanged.
* **Do not adopt IV rank as a cross-sectional screen.** The cheap alternative is not a real one — keep
  paying for the chain.
* ⚠ Not tested here: IV rank as a **within-name timing** gate (is *this* name rich versus its own
  history?). That is a different claim, it is the form our own straddle gate uses, and this study says
  nothing about it. The IV-percentile column (`ivp`, corr 0.842 with ivr) is in the CSV for that work.
