# Long-side vetoes: below the 200 SMA / 6-month < −10% (2026-09-28)

`run_veto_ttest.py` (pre-registered; PRIMARY = the out-of-time 2010-19 holdout, since the vetoes were read off
2019-26 data). Generic house breakouts on liquid_panel_2009; 20-session forward % return, ADR-matched same-date
excess, 10 bp/side; OLS with date-clustered errors. Log `logs/veto_ttest.log`.

## Verdict: V1 (below 200 SMA) SUPPORTED, not certified · V2 (6-month < −10%) NULL out of time

| | 2010-19 holdout (PRIMARY) | 2019-26 |
|---|---|---|
| **V1 below 200 SMA**, 20d | vetoed −2.09% vs allowed −0.52% → **−1.58pp, t −2.23**, halves −2.88/−0.60, 7/10 yrs negative | **−1.83pp, t −2.76**, halves −2.32/−1.18, 6/8 yrs |
| V1, 60d | −2.94pp, t −2.27 | −3.07pp, t −2.81 |
| V1, house trade % | −0.66pp, t −1.31 | vetoed −1.58% vs allowed +0.71% |
| **V2 6-month < −10%**, 20d | −0.46pp, **t −0.62**, halves disagree, 5/10 yrs | −1.40pp, t −2.04 |
| share of breakouts vetoed | V1 9%, V2 9% | V1 8%, V2 7% |

Panel-wide (all eligible name-days), neither veto marks weak stocks in general: V1 +0.01pp (t 0.07) on 2010-19,
−0.26pp (t −0.77) on 2019-26. The effect is specific to BREAKOUTS: a breakout below the 200 SMA fails.

## Read
- **V1 is consistent and cheap:** two independent periods, the same sign and size (−1.6 to −1.8pp at 20 days, about
  −3pp at 60), both halves negative on the holdout, 7/10 years; it removes only 8–9% of breakouts. It misses the
  house |t| ≥ 3 in each sample alone (t −2.23 / −2.76), so it is SUPPORTED, not certified. Keep it.
- **V2 doesn't survive out of time:** −0.46pp, t −0.62, halves disagree on 2010-19. The 2019-26 lean (t −2.04) is
  the sample it was derived from. Drop it as a hard veto (it overlaps V1 for most names anyway).
- Survivor-biased panel flatters the vetoed side (names that died are missing), so V1's true effect is if anything
  larger.
- ⚠ Cosmetic: the 2019-26 house-trade t printed NaN (end-of-sample NaNs in the regression); the means are correct.
