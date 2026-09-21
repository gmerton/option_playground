# Retrace entry: the tradeable version of the control (2026-09-20)

Built off `entry_vs_stop_2026-09-20.md`, which measured that a house breakout enters +0.52 ADR above
the prior 20-session high while the same-name random-later control enters −2.09 ADR below it. This
makes that control tradeable: take the same breakout, then **defer entry until price retraces to
within RETRACE ADR of the breakout level**, abandoning it if it has not come back within WAIT sessions.

Three arms. **A** = every breakout, entered on the breakout close (the current rule). **B** = entered
on the retrace close (tradeable). **C** = the *same* breakouts as B, entered on the breakout close —
not tradeable, since it conditions on a retrace that has not happened yet, and present only to
isolate entry timing from the change in which breakouts get taken.

## Result

Best arm (`stop_hold`) per cell, meanR:

| retrace | wait | came back | n | A | **B** | C | A edge | **B edge** | B t |
|---|---|---|---|---|---|---|---|---|---|
| 0.0 ADR | 5d | 50.8% | 22,372 | −0.074 | **+0.027** | −0.798 | −0.102 | +0.046 | 0.77 |
| 0.0 ADR | 20d | 65.6% | 28,890 | −0.074 | **+0.051** | −0.478 | −0.101 | **+0.065** | 0.48 |
| 0.5 ADR | 20d | 77.7% | 34,235 | −0.074 | **+0.028** | −0.289 | −0.106 | +0.027 | 1.03 |

**B beats A in all six cells**, and the edge over its own control flips sign: **−0.101 → +0.065**.
Both halves are positive (+0.028 / +0.067). **B − C = +0.53R** on the same breakouts, which confirms
the mechanism is entry timing, not cohort change.

## But it does not pass the bar

The house bar is: beats its control, **both halves positive**, **|t| ≥ 3**. B clears the first two and
fails the third — **t 0.48** at the best cell, 0.46–1.20 across cells. **Not adoptable.** The effect is
real in direction and consistent across six parameter cells, but the resulting edge (+0.065R) is small
and the day-clustered t does not support it.

## The finding that matters more

Splitting the breakout population by whether it ever returned to the level within 20 sessions:

| cohort | n | share | meanR |
|---|---|---|---|
| **held** (never returned) | 10,358 | **23.6%** | **+1.273** |
| **failed** (returned) | 33,612 | **76.4%** | **−0.374** |
| all | 43,970 | 100% | +0.014 |

The breakout book is **bimodal**, and its average is a blend of two completely different populations.
The retrace rule works by rescuing the failing 76% from −0.374R to roughly flat — it never touches the
+1.27R cohort, because those never come back to be bought.

⚠ **This is survivorship and is NOT a rule.** "Never returned" is only knowable afterwards. It is
stated because it redefines the question: the breakout entry is not uniformly bad, and the return to
chase is not the lever. **The lever is whether the 24/76 split can be called at entry.** Everything
the book already knows about location (within 1 ADR of the 21 EMA), volume pace, and the precision
tier is a candidate predictor of that split, and none has been tested against *this* target.

## What changes

Nothing adopted. Two things carried forward:
1. **Retrace entry is a live candidate, parked below the bar** — positive, consistent across six cells,
   both halves positive, t too weak. Re-test if the panel extends before 2019.
2. **The next question is better than the last one:** stop asking whether the breakout entry is good,
   and start asking what predicts holding versus returning to the level.
