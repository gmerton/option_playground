# Level triggers: which prices are worth entering at? (2026-09-21)

## Pre-registration (written BEFORE any code ran; do not edit this section after the results)

**Question.** Is the 15-day pivot the right intraday trigger price, or do other important prices give better long
entries, either as a BREAK or as a HOLD (pull back to the level, hold it, turn up)? Prompted by ANET 9/21 (LVL alert
at 14:15, 1.7 ADR over the 21 EMA) and the standing finding that entry LOCATION, not the trigger, carries the return
(entry_vs_stop_2026-09-20, retrace-entry PARKED, Stage A triggers ≈ random minute).

**Data.** Cached 1-min bars, 192 names × 165 sessions (2026-02-02 → 09-18): curated alert universe + the 39-name
no-hindsight control set (`universe_study_extra.txt`), reported separately. Daily levels from the liquid panel,
using data through the PRIOR session only. ADR = the harness's 20-day ADR. Long side only.

**Levels (6 families).**
| family | level for day D |
|---|---|
| PDH | prior session high |
| PDL | prior session low |
| EMA21 | 21-day EMA at the prior close |
| SMA50 | 50-day SMA at the prior close |
| AVWAP | VWAP anchored at the lowest low of the prior 20 sessions (daily typical price × volume from the anchor day through D−1, plus today's session running sums) — moves intraday |
| ORH | 15-minute opening-range high (09:30–09:44), live from 09:45 |
Comparator (not one of the 12): **PIVOT** = highest high of the prior 15 sessions, BREAK only (≈ today's LVL detector).

**Two behaviours per level (12 arms).** Window 09:45–15:30 ET, one signal per name-day per arm, entry = next bar's
open (harness), stop = level − 0.5 ADR for every arm (the LVL detector's stop, so arms differ only in the level and
the behaviour).
- **BREAK:** first 1-min close > level × 1.0005 whose prior 1-min close was ≤ level.
- **HOLD:** price first closes ≥ level + 0.1 ADR (any time from 09:30); later a 1-min low ≤ level + 0.1 ADR (the
  touch); trigger = the first later 1-min close ≥ level + 0.1 ADR, provided no close < level − 0.1 ADR happened
  during the touch (if one does, the hold failed and that arm is done for the day).

**Scoring.** `lib.studies.pattern_test` intraday arms and its control (same name-day, 3 random minutes 09:45–15:30,
same stop %). **Primary exit = `stop_close`** (hold to the close with the stop). Other exits reported, not used for
the verdict (picking the best exit after the fact is a forking path).

**Pass bar (all five, on the primary exit).** (1) beats the random-minute control; (2) |t| ≥ 3 on day-clustered
means; (3) positive in both halves (split 2026-06-01); (4) positive on the no-hindsight control set; (5) beats the
PIVOT comparator's mean R. 12 arms = 12 tries: expect ~0.6 false passes at 5%, so a single marginal pass is weak.

**Location, recorded for every signal.** Entry distance above the 21 EMA in ADR units, stop distance in ADR, and
distance from the pivot, so a winner can be read as timing or as location.

**Not tested here (named so they can't be added quietly):** prior-week high, gap edge / prior close, round
numbers, base low, short side. Any of them is a new pre-registered row.

---

## Results (run 2026-09-21, after the pre-registration above; script `run_level_trigger_test.py`, log `.log`, table `.csv`)

**Verdict: NULL, 0 of 12 pass. MECHANISM: a level picks the DAY, not the MINUTE. The pivot break is the worst-timed
entry of all 13 arms.** 20,148 name-days scored (4,580 minute files had no daily levels, mostly names outside the
liquid panel); 12 ledger rows added.

Primary exit = hold to the close with the stop at level − 0.5 ADR. "Random minute" = the harness control on the
SAME name-days as the arm, so it measures the day the level selects; "edge" = arm minus that control.

| arm | n | mean R | t | random minute, same days | edge | halves | curated / control set | entry vs 21 EMA (ADR) |
|---|---|---|---|---|---|---|---|---|
| PDH break | 5,784 | −0.085 | −5.4 | −0.027 | −0.058 | −0.05 / −0.12 | −0.06 / −0.16 | +0.7 |
| PDH hold | 5,532 | −0.060 | −3.7 | −0.032 | −0.028 | −0.03 / −0.09 | −0.04 / −0.11 | +0.8 |
| PDL break | 4,834 | −0.072 | −2.7 | −0.109 | +0.037 | −0.02 / −0.13 | −0.06 / −0.10 | −0.2 |
| PDL hold | 5,607 | −0.070 | −2.6 | −0.103 | +0.033 | −0.02 / −0.12 | −0.06 / −0.09 | −0.1 |
| 21 EMA break | 2,736 | −0.085 | −3.7 | −0.082 | −0.003 | −0.06 / −0.11 | −0.06 / −0.15 | 0.0 |
| 21 EMA hold | 2,943 | −0.095 | −5.0 | −0.084 | −0.011 | −0.06 / −0.13 | −0.07 / −0.15 | +0.1 |
| 50 SMA break | 1,550 | −0.059 | −3.0 | −0.049 | −0.010 | −0.02 / −0.10 | −0.03 / −0.14 | −0.1 |
| 50 SMA hold | 1,562 | −0.089 | −4.2 | −0.064 | −0.025 | −0.05 / −0.12 | −0.07 / −0.14 | −0.1 |
| AVWAP break | 3,696 | −0.071 | −2.6 | −0.073 | +0.002 | −0.02 / −0.13 | −0.06 / −0.10 | −0.6 |
| AVWAP hold | 4,039 | −0.071 | −3.2 | −0.076 | +0.005 | −0.03 / −0.11 | −0.06 / −0.10 | −0.4 |
| ORH break | 10,427 | −0.066 | −3.5 | −0.023 | −0.043 | −0.01 / −0.13 | −0.05 / −0.12 | +0.5 |
| ORH hold | 7,746 | −0.065 | −4.4 | +0.005 | −0.069 | −0.02 / −0.11 | −0.05 / −0.11 | +0.7 |
| *PIVOT break (comparator)* | 2,174 | −0.086 | −4.5 | **+0.007** | **−0.093** | −0.04 / −0.15 | −0.06 / −0.17 | +2.0 |

## What it says

1. **No price is a good intraday trigger.** Every arm is negative, in both halves and on both universe sets, and no arm
   beats a random minute on its own days by more than +0.04R. Break vs hold makes no difference anywhere.
2. **The level selects the day, not the minute.** The random-minute control swings with the level: on days a name
   crosses its prior-day LOW the random minute is −0.10R (weak days); on pivot-break and opening-range days it's ~0.
   The signal itself tracks its own day's random minute within a few hundredths of R. This is Stage A again, now for
   six more kinds of price.
3. **The pivot break is the worst-timed entry tested.** On pivot-break days a random minute is +0.007R; buying the
   break is −0.086R (edge −0.093, the worst of 13). It buys 2.0 ADR above the 21 EMA. That's the intraday version of
   the daily finding: we pick the right names and days, then pay up at the worst moment.
4. **Entering near the 21 EMA doesn't rescue an intraday entry.** The 21 EMA arms enter at ~0 ADR from the EMA and are
   still −0.09R. The daily location result (distance to the 21 EMA as a gate) does not carry down to a minute trigger.

**For the desk.** The ANET worry ("the alert came too late") doesn't have a better-priced answer: an earlier or
different level would not have been an edge either. Consistent with the entry study (a CLOSE entry beats every
intraday entry), alerts stay information, and entries on names already selected are better at the close than on an
intraday level.
