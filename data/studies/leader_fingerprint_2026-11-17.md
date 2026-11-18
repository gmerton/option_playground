# Which fresh leaders double? Fingerprint fit 2011-18, tested 2019-25 (2026-11-17)

**Verdict: NULL (primary fails) · YIELD: MECHANISM.** The fingerprint finds the right tail, but it finds the
left tail with it. On the untouched 2019–25 test it is a volatility sorter, not a selector.

- PRIMARY: Q5 − Q1-4 12-month excess **+9.8%/event, t_NW 1.88** (bar 3). Halves +16.0% / +4.2%, 6/7 years.
  Without forward-break events: +5.9%, t 1.05, second half negative. 2020 alone contributes +30pp.
- Q5 doubled **10.1% vs 2.3%** (ratio 4.3, test AUC 0.746). It also halved **9.8% vs 3.9%**, and its *median*
  return is lower (+5.2% vs +6.4%).
- Exploratory (after the result, not graded): **ADR alone** predicts doubling (AUC 0.752) as well as the
  7-feature composite, and predicts halving equally (0.755), so the composite is mostly volatility.
  ~~The one asymmetric feature is **low share price**~~ (RETRACTED: `logpx` used split-adjusted prices, i.e. look-ahead; on nominal price there is no effect, see `low_price_leaders_2026-11-17.md`): doubling AUC 0.674, halving 0.513. That is a search-found
  lead for a fresh pre-registered test, not a finding.
- For the triple-digit goal: fresh leaders sorted by observable shape do not give a doubling rate above ~10%,
  and that comes with an equal blow-up rate. At equal-risk sizing (smaller size in high-ADR names, which is how
  the book sizes), the tail edge mostly washes out. The lever is still unidentified.

Pre-registration: docstring of `run_leader_fingerprint.py`. Events 4,712 (4,601 with all features); fit 2,776 (double rate 1.8%), test 1,825 (double rate 3.9%).

## Fit coefficients (logit on within-year ranks; month-clustered z, for reading only)

| feature | coef | z |
|---|---|---|
| adr | +0.86 | +1.09 |
| logpx | -2.09 | -3.43 |
| ret63 | +1.64 | +1.90 |
| ret252 | +1.35 | +2.68 |
| depth3y | +0.78 | +1.63 |
| baselen | +0.92 | +1.35 |
| optshift | -0.16 | -0.28 |

Fit AUC 0.811; **test AUC 0.746**.

## PRIMARY (all test events)

- xs(Q5) − xs(Q1-4) = **+9.82%/event, t_NW +1.88**; halves 2019-21 +15.95% / 2022-25 +4.20%; years same sign 6/7 → **fail**
- DOUBLE rate Q5 10.1% (n 367) vs Q1-4 2.3% (n 1,458); ratio 4.32
- fwd 252d: Q5 mean +19.7% median +5.2%; Q1-4 mean +9.9% median +6.4%; P(fwd ≤ −50%) Q5 9.8% vs 3.9%

| year | Q5 − Q1-4 xs |
|---|---|
| 2019 | +8.15% |
| 2020 | +30.69% |
| 2021 | +6.39% |
| 2022 | +5.30% |
| 2023 | -10.68% |
| 2024 | +18.74% |
| 2025 | +13.16% |

## Sensitivity: excluding forward-break events

- xs(Q5) − xs(Q1-4) = **+5.93%/event, t_NW +1.05**; halves 2019-21 +13.57% / 2022-25 -1.28%; years same sign 5/7 → **fail**
- DOUBLE rate Q5 9.4% (n 342) vs Q1-4 2.2% (n 1,425); ratio 4.17
- fwd 252d: Q5 mean +18.9% median +4.4%; Q1-4 mean +10.6% median +6.7%; P(fwd ≤ −50%) Q5 9.1% vs 3.0%

| year | Q5 − Q1-4 xs |
|---|---|
| 2019 | +4.21% |
| 2020 | +30.31% |
| 2021 | +3.67% |
| 2022 | -4.72% |
| 2023 | -10.05% |
| 2024 | +19.24% |
| 2025 | +13.16% |

