# OptionsPlay's own credit-spread spec vs delta-matched stock: NULL, negative sign (2026-09-24)

`run_optionsplay_spec.py` (pre-registered in its docstring). Log: `logs/optionsplay_spec_2026-09-24.log`; per-spread
CSV `optionsplay_spec_2026-09-24.csv`. Chains cached in `data/cache/optionsplay_spec_chains.parquet` (one Athena
query). Source: Tony Zhang, "Finding the Optimal Credit Spreads" (bk9Co7V6AI4, 2020): **sell the ~50Δ put, buy the
~25Δ, ~45 DTE, take only spreads with credit ≥ 33% of width.**

**Setup.**
- 20 liquid names (the premium-to-width panel), Fridays 2018-01 → 2026-01, 7,356 spreads.
- Both spreads crossed at real fills, held to expiry, settled at intrinsic against the chain-implied spot.
- Benchmark: the stock held at the spread's entry **net delta** (mean 0.25) on the same max-loss capital.

## Result (real fill)

| arm | n | return on capital | delta-matched stock | **excess** | win % |
|---|---|---|---|---|---|
| all of his structure | 7,356 | +7.75% (t 2.14) | +11.94% | **−4.18pp (t −3.31)** | 69 |
| **his floor, cw ≥ 0.33** | 3,910 | +9.45% (t 2.81) | +12.13% | **−2.68pp (t −2.21)** | 67 |

- **PRIMARY: floor excess, month-weighted, −3.32pp, t −2.21 (97 months). Halves −1.76 / −5.28. PRE-REGISTERED PASS: NO.**
- By year, the excess is negative in 7 of 8 full years. The exception is **2020 (+9.2)**, the one year the capped loss
  beat a crashing stock.
- The floor is reachable at his geometry: median credit/width is 0.334 and 53% of spreads clear 0.33, against 0.07% at
  our 30Δ/20Δ. It selects NVDA, AMD, TSLA and NFLX first, i.e. high IV.
- Within-date quintiles of credit/width (secondary): **return on capital Q5 − Q1 +9.43pp, t 3.49, but excess +2.50pp,
  t 1.00.** The sort ranks beta, not premium.
- Re-priced at the **20% of spread measured on Gabe's real fills**: the floor arm's excess is −1.10pp (t −1.18). It is
  still no better than the stock.

## Reading

**NULL · YIELD: MECHANISM (the third time today).** His spec makes money (+9.45% per spread), and a ROC-only test
would have called it a winner. But it makes **less** than just holding a quarter-delta of the same stock, because
selling the 50Δ put gives away the upside while keeping most of the downside down to the long strike. The
credit/width floor and quintiles pick **higher-IV, higher-beta names**, and those went up in 2018–26. The option
structure adds nothing on top.

This is the same result as `csp_yield_rank_2026-09-24` (yield rank on puts = beta) and `cw_play_2026-09-22`
(top-quintile bull puts −2.43pp vs delta-matched stock). ⚠ **It sharpens the read on our own credit/width finding:
scored on ROC it "passes"; scored against the stock it doesn't, at either geometry.** Credit/width is a way to avoid
the worst-priced spreads, not a source of edge. The only short-premium result that beats its benchmark is still the
index put sale after a selloff.
