# Calm-regime SPY weekly put sale with a positive-gamma gate — CERTIFIED-CANDIDATE, paper trade first (2026-09-28)

**Goal context:** Gabe's organising question is what to run NOW. On 9/28 the regime is calm (VIX ~16, SPY above its 50-day), and the stress bucket is PARKED and can't fire anyway.
**Script:** `run_spy_calm_weekly_put.py`, pre-registered and committed (d35becc) before the run. **Log:** `logs/spy_calm_weekly_put.log`. Entries: `logs/spy_calm_weekly_put_entries.csv`.

## Rule tested
- **Entry:** every **Friday** close in the **CALM** regime (not [SPY < 50 SMA & VIX ≥ 20]) **with SPY dealer gamma > 0**.
- **Trade:** sell the **7-DTE 10Δ put** (next Friday), hold to expiry, house fills.
- **Data:** v3 2010–2026-02.
- **Primary statistic:** net P&L minus the delta-matched SPY move (carry-adjusted), month-clustered.

## Result
| cell | n | net bp/trade | t | **excess over beta** | t | halves | years + | win | worst trade | worst 4 wk |
|---|---|---|---|---|---|---|---|---|---|---|
| **PRIMARY N10 CALM & G+** | 362 | +6.56 | 6.49 | **+5.12** | **5.25** | +4.23 / +5.78 | **94%** | 96% | −170 | −156 |
| N10 CALM, no gate | 671 | +5.93 | 3.99 | +4.65 | 3.51 | +6.09 / +3.23 | 82% | 96% | **−758** | −719 |
| **N05 CALM & G+** | 362 | +4.23 | 12.44 | **+3.49** | **7.14** | +2.93 / +3.91 | **100%** | 99% | **−86** | −78 |
| Vertical 10/5 CALM & G+ | 362 | +1.59 | 1.98 | +0.89 | 1.28 | +0.19 / +1.41 | 71% | 96% | −137 | −123 |
| N10 CALM & G− (the skipped days) | 309 | +5.19 | 1.71 | +4.10 | 1.52 | +7.68 / **−0.89** | 76% | 95% | −758 | −740 |
| N10 all Fridays | 798 | +7.46 | 5.49 | +4.93 | 3.88 | | 94% | 96% | −758 | −719 |

**PRIMARY: +5.12 bp/trade beyond beta, t 5.25, both halves positive, 94% of years positive → CERTIFIED-CANDIDATE** (the pre-registered status: forward paper trade before any size).

## Reading
- **Mostly premium, not beta.** Only 1.44 of the 6.56 bp is the delta's share of SPY's move, which is the opposite of the stress bucket (60–80% beta).
- **The gamma gate earns its place through the tail.**
  - It removed the one catastrophe in the sample: **2020-02-21** was a calm-state Friday with **negative** gamma, and the 10Δ put lost −758 bp.
  - The skipped negative-gamma cell has t 1.52 and a negative second half.
  - The gate is the book's certified mechanism, chosen before this test, not fitted here.
- **5Δ has the cleaner profile:** t 7.1 excess, 100% of years positive, worst trade −86 bp, but a smaller credit. The 10/5 vertical buys back most of the premium (+0.9 bp, t 1.3), so defined risk here costs the edge.
- **Tail cases:**
  - The primary's worst trade (2018-01-26, the Volmageddon week) was calm with positive gamma at entry: −170 bp.
  - Tariffs, 2025-03-28: the regime flag was **not calm** (flipped to stress), so no entry; −465 bp avoided.
  - COVID, 2020-02-21: the gate skipped it.
- **Economics:** about 23 qualifying Fridays a year; +0.38% on Reg-T margin per trade.

## Caveats
- **No 2008 test.** Short-tenor synthetic pricing failed validation (+15% rich), so v3's 2010–26 is the whole sample.
- **The cell was chosen from the step-1 map on the same data.** t 5.25 clears the 80-cell Šidák bar (3.42), but there's no out-of-sample year → the **forward paper trade is the real test.**
- **Gamma history ends 2026-02.** Live use needs the Tradier GEX computation that `run_gex_fly_paper.py` already has.
- **Naked short puts.** Size to the worst trade (−170 bp primary; −758 is what an ungated week can do), not to the mean.
