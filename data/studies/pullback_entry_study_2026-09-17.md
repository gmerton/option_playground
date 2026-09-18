# Pullback entries on leaders, daily bars (2026-09-17)

**Claim tested.** Luk (20 mentions / 16 videos) and Ariel Hernandez: buy the pullback into a rising EMA (9/21, or 50) on a leader, trigger = reclaim (close above the prior day's high) with the pullback low as the stop; first pullback is best; skip entries > ~3% above the low; no gap-ups. Gabe's variant: buy once price is back above the midpoint of the pullback ("confirmed"). Intraday triggers/stops are the parked entry study; this is the DAILY-bar version on the same panel and hold as the breakout pool (`run_pullback_entry_study.py`, 2019-10 .. 2026-09; leader = ADDV >= $50M, within 15% of the 52wk high, stacked w/ house slack, rising 21 EMA; pullback = low touched the EMA within 3 sessions after the close had been >= 1 ADR above the 21 EMA in the prior 10). R = (exit - entry) / (entry - pullback low). SEs month-clustered.

| entry, ADR 4-7 | n | R | t | win | ret | stop away | halves | 2022 |
|---|---|---|---|---|---|---|---|---|
| reclaim, 9 EMA | 7,327 | +0.13 | 0.5 | 33% | +1.2% | 7.5% | +0.10 / +0.17 | -0.20 |
| reclaim, 21 EMA | 3,203 | +0.12 | 0.8 | 32% | +1.3% | 8.0% | +0.14 / +0.10 | 0.00 |
| reclaim, 50 EMA | 558 | +0.16 | 0.6 | 33% | +1.7% | 9.0% | +0.04 / +0.28 | +0.28 |
| confirmed (midpoint), 9 EMA | 3,787 | +0.17 | 1.0 | 33% | +1.3% | 6.9% | +0.11 / +0.24 | -0.16 |
| confirmed, 21 EMA | 1,869 | +0.17 | 1.4 | 31% | +1.5% | 7.9% | +0.20 / +0.14 | +0.02 |
| confirmed, 50 EMA | 319 | +0.26 | 1.2 | 32% | +2.4% | 9.2% | +0.14 / +0.39 | +0.20 |
| Luk <= 3% above the low (any ADR), 9 / 21 EMA | 31,494 / 13,583 | +0.06 / +0.06 | -1.2 / -0.4 | 32 / 29% | +0.1% | 2.2% | ~0 / +0.1 | -0.56 / -0.47 |
| ADR 4-7 & first & <= 3% above low, 9 / 21 EMA | 78 / 21 | **-0.74 / -0.92** | -2.2 / -5.3 | 21 / 5% | -1.9 / -2.4% | 2.8% | both halves negative | -- |
| first vs later pullback (any ADR, 21 EMA) | 30,881 / 8,590 | +0.06 / +0.00 | | | +0.29 / -0.02% | | | |
| exit: 20 EMA trail / +2R sell-strength / **stop only 60d** (9 EMA, ADR 4-7) | 7,327 | +0.13 / +0.07 / **+0.43** | 0.5 / -0.5 / 1.3 | | +1.2 / +0.7 / **+3.4%** | | C: +0.42 / +0.44 | C: -0.44 |
| control: random leader-days, no signal, close entry, stop = day's low | 2,114 | (+2.17, 1.6% stop) | 0.3 | 27% | **+0.8%** | 1.6% | | -1.39 |
| **benchmark: breakout pool** (pivot break, ADR 4-7, near highs) | 3,539 | **+0.55** | | 31% | **+2.6%** | 5.7% | | |

Year by year, 21 EMA reclaim ADR 4-7 (R): 2019 -0.30 · 2020 +0.60 · 2021 -0.13 · 2022 0.00 · 2023 -0.34 · 2024 +0.16 · 2025 +0.46 · 2026 -0.06.

**Reading.**
1. On daily bars the pullback entry on a leader is roughly break-even to mildly positive (+1.2 to +2.4% per trade, R +0.12 to +0.26, no t above 1.4), about +0.5 to +1.5pp better than buying the same leaders on a random day, and **below the breakout entry on every cut** (+2.6%, R +0.55). No year-to-year consistency.
2. **Luk's tight version is the worst on daily bars.** Entries within 3% of the pullback low (stop 2-3% away) return ~0 overall and the full recipe (ADR 4-7, first pullback, <= 3%) is -0.74 to -0.92R with 5-21% winners. Judged on daily closes, a 2-3% stop on a 4-7% ADR name is hit by noise before the trend resumes. Same lesson as the alert-funnel test and the stop study: the tight-stop size lever does not survive daily-close management.
3. **Gabe's "confirmed" entry is marginally better than the early reclaim** (R +0.17 vs +0.12; +0.26 vs +0.16 on the 50 EMA) -- the opposite of the theory's tight-stop advantage, because here the failure rate of the early entry outweighs its size benefit.
4. **Exit mismatch:** the house 20 EMA trail suits breakout entries; a pullback entry is bought AT the EMA, so the trail sits under the entry and shakes it out. Stop-only 60-session holds return +3.4-3.8% vs +1.2-1.3% with the trail, both halves (+0.42 / +0.44) -- but 2022 -0.44. This matches Luk's own rule: entry location dictates exit style (EMA buys held on stops, not trailed).
5. First pullback beats later pullbacks by a hair (+0.06 vs 0.00R), consistent with the claim, immaterial in size.

**Verdict.** On daily bars the pullback entry does not replace the breakout entry and Luk's tight-stop version fails. This is NOT a refutation of what they do: their edge, if real, is intraday -- a 5/15-min trigger after the flush with the intraday low as the stop and intraday management -- which is the parked entry study ([[feedback_timeframe_agnostic_patterns]]: a daily-bar null is not a refutation). Two usable pieces now: (a) if a pullback entry is taken, manage it on the pullback low, not the 20 EMA trail; (b) the "confirmed" midpoint entry is at least as good as the early reclaim on daily data.
