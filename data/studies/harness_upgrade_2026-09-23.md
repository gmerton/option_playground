# Harness upgrade [WL-2]: paired edge t, label-permutation null, optimisation-aware grid — 2026-09-23

**Status: BUILT, VALIDATED, APPLIED.** `src/lib/studies/pattern_test.py` now scores daily patterns on a **paired
edge t** and a **permutation p_search**. `run_grid()` prices a whole parameter grid as one test (**p_opt**).

The re-score changes three verdicts:
- **The in-book precision-tier row's pass is a SELECTION pass, not a timing pass.**
- **Two PARKED/near-miss rows now clear the paired bar** (as candidates; see the caveats).
- **HYB-B is a moderate plateau at p_opt 0.039: stays PARKED.**

Design source: `data/neurotrader/videos/2025-03-03_NLBXgSmRBgU/notes.md` (items A, B, D; C, the block bootstrap,
was not built).

## What changed in the harness

| | before | now |
|---|---|---|
| "beats the control" | point check: `meanR − mean(all controls) > 0` | **paired**: each signal minus the mean of its own 3 controls, date-clustered **edge t** |
| the t in the bar | t of raw mean R vs 0 | **paired edge t ≥ 3** on the best arm |
| best-of-5-arms pick | uncharged | **p_search**: 2,000 permutations of the "signal" label inside each matched stratum (same name next 20 sessions for `post`, same date other names for `xname`), max over arms |
| parameter search | Šidák with a guessed k | **`run_grid`**: the whole pre-registered grid is re-run under each permutation (keys shared across cells) → **p_opt**; plus plateau share and median/best t |
| per-year | not printed | paired edge by year for the best arm |
| pass (daily) | \|t\| ≥ 3, halves > 0, edge > 0 | **edge t ≥ 3, both halves' paired edge > 0, p_search < 0.003** |

The permutation count must reach the bar: 1/(N+1) < 0.003 means N ≥ 333. The harness refuses a verdict below that.
Intraday runs and `run_level_trigger_test.py` keep the legacy rule, because the call is backward-compatible.
The ledger gains `edge_t`, `p_search` and `p_opt` columns.

## Validation (`data/studies/logs/harness_upgrade_validation_2026-09-23.log`)

| check | expected | result |
|---|---|---|
| 5 random-signal sets (2,500 each), 500 perms | spread p, no pass | p 0.61 / 0.83 / 0.62 / 0.02 / 0.24 ✅ (seed 4 reached paired t **2.76** on pure noise) |
| +0.3R planted | pass | t +5.91, p at the floor, PASS ✅ |
| 6-cell breakout grid, no plant | nothing | best t −0.75, p_opt 0.99 ✅ |
| +0.3R in 1 of 6 cells | found, "spike" | t +10.06, p_opt at the floor, plateau 17%, median/best −0.12 ✅ |
| +0.3R in all cells | "plateau" | plateau 100%, median/best 0.81 ✅ |

**Noise calibration worth remembering:** in a 6-cell × 5-arm grid on house breakouts, the null's 99th-percentile max
t is **4.03**. Searching even 30 cells produces t ≈ 4 by chance 1% of the time.

## Re-score of the rows nearest the bar (same signal builders, only the scoring changes)

`run_harness_rescore_2026_09_23.py`, logs `harness_rescore_2026-09-23.log`, `_row26_`, `_candidates_`.

| row (old verdict) | control | best arm | paired edge | paired t | halves | p_search | new |
|---|---|---|---|---|---|---|---|
| **Precision-tier breakout, as registered: cap 20, stop ≥ 2%** (t 3.29, PASSED, IN BOOK) | post (timing) | ema20 | +0.275R | 2.89 | **−0.009** / +0.481 | 0.033 | fails |
| | **xname (selection)** | ema20 | **+0.438R** | **3.52** | +0.160 / +0.615 | **0.0015** | **passes** |
| same, standard harness (cap 10, stop ≥ 0.5%) | post | ema20 | +0.139R | 1.36 | −0.085 / +0.302 | 0.32 | fails |
| | xname | ema20 | +0.237R | 1.81 | +0.048 / +0.356 | 0.11 | fails |
| **Earnings drift, good+MUTED** (t 2.65, PARKED) | post | t2R | +0.179R | 2.44 | +0.181 / +0.177 | 0.021 | fails |
| | **xname** | t1R | +0.186R | **3.17** | +0.126 / +0.224 | **0.0020** | **passes** · every year + (8/8) |
| **House breakout inside HYB-A** (t 2.84, not passed) | **post** | stop_hold | +0.347R | **4.15** | +0.068 / +0.497 | **0.0015** | **passes** · every year + (7/7), but 2020–21 ≈ +0.03 |
| | xname | ema20 | +0.248R | 2.98 | +0.061 / +0.343 | 0.006 | fails (narrowly) |
| VCP damped sine N3 (NULL today) | post / xname | — | +0.01 / −0.04 | 0.19 / −0.18 | — | 0.76 / 0.89 | NULL ✅ |
| Kell wedge pop (NULL today) | post / xname | ema20 | +0.04 / +0.03 | 0.08 / 0.80 | — | 0.82 / 0.51 | NULL ✅ |

### Reading

1. **The in-book row passes on selection, not timing.** The breakout name beats a random name on the same day
   (+0.44R, p 0.0015). The breakout *day* doesn't beat a random later day in the same name (first half −0.01R). That
   is "we select well, we enter badly" confirmed by the new rule. The row's recorded "PASS vs post" came from the
   unpaired statistic. The status stays IN BOOK, and the evidence behind it is now the xname cell.
2. **Two new passes, as CANDIDATES only.** Both come from a re-score of rows I **chose because they were near the
   bar**, under two controls each. That is a selection step the permutation can't see. Treat them as
   "passes the paired rule, awaiting the forward lockbox (queue #5, data from 2026-09-22)". They are not ADOPTED.
   - Earnings good+MUTED is a *selection* pass (vs a random name); its timing cell fails.
   - HYB-A breakouts is a *timing* pass (vs a later day in the same name), and back-loaded: 2020–21 ≈ 0, 2022–26
     +0.22…+0.84R. The HYB-A universe itself was NULL on selection.
3. **The sanity rows stay NULL** under both controls, as they should.

## HYB-B neighbourhood (method-queue #2) — `run_hybb_neighbourhood.py`

ADR ≥ {3.5, 4.0, 4.5} × ADDV ≥ {$75M, $100M, $150M}. The statistic is the per-date **ADR-matched** 20d excess (the
column the PARKED figure came from). The null is random names drawn within each ADR decile in the members' counts.
The registered cell (4.0 / $100M) reproduces at **+1.69%, t 2.51** (recorded +1.79 / 2.60; the small gap is in how
members without a forward return are counted).

| ADR \ ADDV | $75M | $100M | $150M |
|---|---|---|---|
| 3.5 | +0.87 (t 1.43) | +1.36 (2.09) | +1.45 (2.11) |
| 4.0 | +0.65 (0.96) | **+1.69 (2.51)** | +1.84 (2.26) |
| 4.5 | +0.71 (0.90) | +1.57 (1.93) | +1.54 (1.58) |

- **Plateau share 44%**, median/best 0.77: a **moderate plateau, not a spike**.
- The $75M floor is the weak column. The effect needs ≥ $100M liquidity.
- **p_opt 0.039** (null max t p50 0.97, p99 3.08). Charged for the threshold choice, HYB-B is real-looking but
  nowhere near 0.003. **Stays PARKED.**

## Not done

- Block-bootstrap null (design item C): optional, not built.
- Re-scoring the rest of the ledger: only the rows nearest the bar were re-scored. ⚠ The paired t is NOT always lower
  than the old raw t (HYB-A went 2.84 → 4.15), so rows below the bar could in principle move up. A full re-score is
  queued as a follow-up, not done.
- Intraday paired/permutation: `run_intraday` still uses the legacy rule.
