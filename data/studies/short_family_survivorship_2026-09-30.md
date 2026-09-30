# Audit #9: the single-name short family on the survivorship-free series (2026-09-30)

**Verdict: NULL, both primaries · YIELD MECHANISM.** Adding the delisted names does not rescue the offering short or CRASH-H. The ledger's short nulls were not a survivorship artefact. This closes audit list A.

- Pre-registered in the docstring of `run_short_family_survivorship.py` and committed before the run (d099f4e). Log: `logs/short_family_survivorship.log`.
- Series: chain_spot closes, including delisted names, 2010-06 to 2025-11. Eligible = option volume ≥ 1,000/day and price ≥ $5.
- Parents' bars unchanged. Costs: 10 bp a side + 1%/yr borrow.

| cell | n | fwd | control | excess | t | halves | yrs neg | short P&L | verdict |
|---|---|---|---|---|---|---|---|---|---|
| **A offering ALL +20 (PRIMARY)** | 2,051 | +0.89% | +0.95% | **−0.18pp** | **−0.91** | +0.15/−0.49 | 7/16 | −1.17% | fail |
| A offering SURV +20 | 1,660 | +1.46 | +1.17 | +0.21 | +1.04 | | 6/16 | −1.74 | fail |
| A offering ALL +60 | 2,052 | +2.57 | +3.27 | −0.62 | −1.59 | −0.54/−0.69 | 11/16 | −3.01 | fail |
| A primary-issuer only +20 | 1,746 | +0.98 | +0.99 | −0.12 | −0.55 | | 9/16 | −1.26 | fail |
| **B CRASH-H ALL +20 (PRIMARY)** | 9,229 | +0.70 | +0.98 | **−0.28pp** | **−0.71** | −0.25/−0.31 | 7/16 | −0.98 | fail |
| B CRASH-H SURV +20 | 3,884 | +1.99 | +1.65 | −0.08 | −0.16 | | 9/16 | −2.27 | fail |
| B CRASH-H, 10%/yr borrow | 9,229 | | | | | | | −1.70 | fail |
| ⚠ A offering NONSURV +20 | 391 | −1.51 | −0.01 | −2.00 | −3.26 | −1.33/−2.65 | 12/16 | +1.23 | *(see below)* |

- **The survivorship effect is real and points the expected way.** Survivors' offering excess is +0.21 and non-survivors' is −2.00. Each primary still fails, because survivors outnumber non-survivors about 4:1 in the eligible events, and the combined effect is small.
- **⚠ The NONSURV offering cell is NOT a result.** "Non-survivor" means "not liquid in 2026", a label set by the outcome. It's conditioned on the future and can't be traded at entry. It is the survivorship mechanism itself, measured. No verdict.
- **Understatement caveat:** a bankrupt name's last exchange close sits above its eventual OTC value, so short outcomes are still somewhat understated. At this effect size it would not close a gap from t −0.9 to −3.

**MECHANISM.** Single-name directional shorts are now 0 for 11 on liquid names. Removing survivorship moves the offering excess by about 0.4pp, not enough. Weak and dilutive names still drift up in absolute terms.

**What it means for the book now.** No single-name directional shorts. The short side that remains is the parked gap-up fade in a stock's own downtrend (forward holdout running since 9/28) and the sector-momentum spread as a crisis hedge.
