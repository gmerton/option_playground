# "Good earnings, delayed bump" (Tito) — tested 2026-09-18

**Pattern:** a company reports well, the stock does not run that day, and the move comes later.

**Verdict: no edge.** Both expressions lose to a random entry in the same name that month.

**Method** (`run_delayed_earnings_study.py`, via `lib.studies.pattern_test`). 6,858 earnings reactions on the
241 panel names with earnings dates. No EPS-surprise data in the repo, so "good" is the tape's reaction:
reaction day = the session in [report, report+1] with the larger |move|; **GOOD** = positive return, volume
≥ 1.5x its 50-day average, close in the upper half of the bar (25% of reactions). **MUTED** = reaction ≤ +4%
(29% of the good ones).

| entry | n | mean R | control | edge |
|---|---|---|---|---|
| drift: buy the close after a good+MUTED reaction | 437 | +0.27 | +0.25 | +0.02 |
| drift: good+BIG | 1,069 | — | — | fails |
| drift: bad reaction | 3,684 | — | — | fails |
| **delayed bump: first close above the reaction-day high, 3–20 sessions later (good+MUTED)** | 335 | **+0.23** | **+0.69** | **−0.47** |
| delayed bump after good+BIG | 796 | — | — | fails |

81% of good+muted reactions eventually cleared the reaction-day high within 3–20 sessions, so the pattern is
common — it just is not informative. The drift entry does have a **positive median (+0.20R) and a 57% win
rate**, which is why it looks attractive in isolation; its control has almost the same mean, because these are
names in uptrends and any entry that month did as well.

**Same shape as everything else tested today:** the cohort is fine, the timing adds nothing.
