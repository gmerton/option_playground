# Alert detectors over 20 sessions: what fails, what survives (2026-09-10)

Replayed the current (9/10) detector rules over every session with Tradier 1-min bars on file, 2026-08-13 .. 2026-09-10 (20 sessions, 68-name long+short universe, 1,073 alerts). Each alert scored identically: alert price -> stop hit before the close (-1R) or the close, R = |price - stop|. No management, no costs (median UR risk 1.69% of price, so a 0.10% round trip = ~0.06R). Filters were judged on the first 10 sessions (A: 8/13-8/26) and checked on the last 10 (B: 8/27-9/10).

## Baseline by detector

| Detector | n | avg R | t | stopped | A | B |
|---|---:|---:|---:|---:|---:|---:|
| UR (VWAP reclaim, long) | 494 | +0.00 | +0.01 | 36% | +0.04 | -0.03 |
| ORB9 (opening-range break, long) | 97 | +0.40 | +1.07 | 75% | +0.90 | -0.05 |
| ORB9 without its top 3 winners | 94 | -0.14 | -0.67 | 78% | -0.25 | -0.05 |
| BIR (bounce into resistance, short) | 238 | -0.15 | -2.76 | 31% | -0.03 | -0.23 |
| FBO (failed breakout, short) | 244 | -0.07 | -1.76 | 15% | -0.03 | -0.10 |

No detector has an edge on its own. ORB9's mean is three trend-day outliers (DE 8/21 +21.6R, CRM 8/19 +18.7R, IBIT 8/19 +11.7R). The shorts that looked good on 9/8-9/10 are negative over 20 sessions.

## What survives both halves (UR only)

| UR filter | n | avg R | t | stopped | A | B |
|---|---:|---:|---:|---:|---:|---:|
| all | 494 | +0.00 | +0.01 | 36% | +0.04 | -0.03 |
| alert before 10:00 | 232 | negative | | 50%+ | 09:40 -0.26, 09:41-10:00 -0.11 | 09:40 -0.37, 09:41-10:00 -0.11 |
| **alert after 10:00** | 262 | **+0.16** | **+2.54** | 22% | +0.18 | +0.14 |
| after 10:00, SPY below VWAP | 109 | +0.24 | +2.53 | 17% | +0.14 | +0.34 |
| after 10:00, SPY above VWAP | 153 | +0.10 | +1.18 | 25% | +0.20 | +0.01 |
| SPY below VWAP (any time) | 191 | +0.17 | +2.03 | 28% | +0.21 | +0.14 |
| SPY above VWAP (any time) | 303 | -0.11 | -1.82 | 42% | -0.07 | -0.13 |
| 10+ names reclaiming in the same minute | 35 | -0.73 | | 76% | -1.00 | -0.63 |

- The whole UR loss is the first 30 minutes. After 10:00 it is positive in both halves (t 2.5), ~+0.10R after costs.
- The index gate is INVERTED for UR: a reclaim while SPY is still under its VWAP is relative strength and does better. Same shape as the Part III rotation finding (leading-group filtering inverted).
- The same-minute flood filter is real (-0.73R) but redundant once the floor is 10:00 (every flood minute was before 10:00).
- ORB9 late-fire artifact (alerts released when the hard index gate opens, 25-65 min after the break) is real in the code but did NOT hurt: late alerts scored better than fresh ones. Not a priority fix.
- Profit targets (+0.5R/+1R/+2R) do not rescue any detector. RS vs SPY and level type (MA vs PDH/OR) do not separate outcomes. The relative-strength short gate is not supported either way.

## Caveats
One 20-session period (late Aug to early Sep 2026). The universe was assembled from names that had recently moved (hindsight). Replays use bar VWAP, the live monitor uses all-prints VWAP. Hold-to-close scoring with no management. +0.16R is modest: keep scoring live before sizing up.

Scripts: `run_alert_study.py` (harness in `src/lib/alerts/study.py`: parse shown + out-of-play logs, score, enrich, reports `filters` / `extension` / `daystate`); replay logs `data/watchlist/logs/universe_alerts_<date>_replay[_oop].log`; scores cached in `logs/alert_study_scores.csv`.

## Daily in-play gate (added 2026-09-10, after Gabe's INTC 9/10 critique)

Every universe name gets a daily state from its chart at the prior close
(`src/lib/alerts/daily_state.py`, carried on `DailyCtx`, cache `alert_ctx_v5_<date>.parquet`):

- **LONG**: within ±1 ADR of the 21 EMA, not a falling-EMA downtrend, not "over the 9 but still
  under the 21", and at least 0.5 ADR under the nearest prior swing high. In practice, a pullback
  into rising EMAs or a base near the 21.
- **SHORT**: a trend-down (under falling 9/21 EMAs, not stretched more than 1.5 ADR under), or
  exhaustion (2+ ADR over the 21 and within 1 ADR under / 0.5 ADR over the nearest prior swing high).
- **OUT**: everything else.

Alerts against the name's state are dimmed as "out of play" (`--no-day-gate` turns this off).
SHORT-state names also get BIR, and the swing high is a named BIR/FBO level ("prior high").

INTC is the reference case. On 9/9 and 9/10 it's SHORT: 2.5 ADR over the 21 and under the 8/13-8/17
highs, 106.9-107.6. The 9/10 VWAP-reclaim long is out of play.

| Long alerts (UR + ORB9), 20 sessions | n | avg R | first half | second half |
|---|---:|---:|---:|---:|
| no gate | 591 | +0.07 | +0.20 | −0.03 |
| state LONG, first version | 256 | +0.17 | +0.19 | +0.16 |
| **state LONG, shipped** (no unconfirmed reclaim, room ≥ 0.5 ADR) | 176 | **+0.34** | +0.35 | +0.33 |
| blocked by the shipped gate | 415 | −0.05 | +0.12 | −0.17 |
| UR after 10:00, no gate | 262 | +0.16 | +0.18 | +0.14 |
| UR after 10:00, shipped gate | 92 | +0.28 | +0.24 | +0.32 |

Rejected sub-states (both halves negative): "reclaiming the 9 under the 21" −0.48R (n=22; mostly
early-morning UR failures) and bases within 0.5 ADR of a prior high −0.11R (n=60). A cap on
extension at alert time adds little for UR and removes nearly every ORB9, so it's not used.

Shorts: restricting to SHORT-state names cuts the worst losers. BIR on LONG-state names was −0.23R
(t −2.7) and on OUT names −0.42R (t −3.2). The kept shorts are still −0.06R (n=197), so shorts stay
informational. FBO exhaustion n=10, not enough to judge.

⚠ The sub-state choices were made on these same 20 sessions. Both halves agree, but it's still
in-sample. Keep scoring the live alerts.
Not built: a daily-21-EMA reclaim trigger, which is the kind of move INTC made on 9/4.

## Setup grade rubric v1 (2026-09-10) -- one rubric for the alerts AND the journal

**Why:** on 9/10, 24 of 25 entries were alert-driven, yet the journal's prose verdicts and the alert engine's gates disagreed both ways (DE/SPCX graded "good" but hidden by the day gate; AAOI/PANW/TSLA shown but graded "gray"). Fix: a single function, `src/lib/alerts/grading.py::setup_grade()`, used by the monitor (A/B loud, C dimmed, F saved as out of play) and by the journal (`src/lib/journal/entry_grades.py` -> `journal_entry_grades` -> review verdicts A/B good, C gray_area, F bad -> report card entry points).

| side | grade | rule | n | R | half A | half B |
|---|---|---|---|---|---|---|
| long | A | ORB9 at/after 10:00, day LONG | 20 | +2.41 | +2.60 | +2.18 |
| long | B | ORB9 before 10:00, or UR/other after 10:00, day LONG | 101 | +0.22 | +0.22 | +0.21 |
| long | C | UR/other before 10:00, day LONG | 55 | -0.18 | -0.51 | +0.02 |
| long | F | daily chart not LONG | 415 | -0.05 | +0.12 | -0.17 |
| short | C | day SHORT, at/after 10:30 (cap: no short edge yet) | 98 | +0.07 | +0.20 | -0.05 |
| short | F | daily chart not SHORT, or before 10:30 | 385 | -0.15 | -0.09 | -0.20 |

Reproduce: `PYTHONPATH=src .venv/bin/python3 run_alert_study.py --since 2026-08-13 --report grades`.

**Tested and left OUT of the rubric** (no stable signal in the same 1,073 alerts): SPY vs VWAP (the old index gate; within day-SHORT names, shorts with SPY *under* VWAP did worse in both halves), relative strength vs SPY or vs group (inverted for longs: weaker-than-group +0.45R vs stronger +0.11R), STOP IN NOISE, still-below-9-EMA. They stay in the alert text as context; `--index-gate` is now a no-op.

**Caveats:** cut points (10:00 / 10:30, ORB9 vs UR) were chosen on the full sample -- the halves test stability, not out-of-sample skill; A is n=20. Re-run the report weekly; if the grades stop ranking R, change `grading.py` and both consumers follow.

**Journal side:** each stock entry (opening fills of one symbol/side within 5 min) is matched to a same-side alert 0-30 min earlier (live logs when present, else replay). Grade from the alert's time; execution = fill vs alert price in ADR (<=0.25 ok) and delay (<=10 min ok). Report-card entry component = setup 20 (share A/B) + execution 10 (share of alert entries ok). Re-grade 8/13-9/10: every session but 8/19 (B), 8/24 and 8/26 (C) is still D; 9/10 = 0 A / 1 B / 3 C / 21 F with execution ok on 18 of 22 alert entries -- the alerts were followed well; the wrong alerts were followed.

---

## Extension to 153 sessions (2026-02-02 → 2026-09-10), run 2026-09-13

Same detectors (current code, LVL included), same scoring (1-min bars, hold to stop or close, R on the alert's own
stop), same hindsight universe (today's 87-name focus list + the short list). Bars for 2/2–8/12 came from Polygon
(`run_fetch_intraday_polygon.py` → `data/cache/intraday_1min/`; Tradier keeps ~20 sessions). 13,002 alerts, 9,424 of
them out of play. Halves = first / last 76 sessions. Log: `logs/long_study_2026-02-02_2026-08-12.log`.

### Rubric v1 over 153 sessions

| grade | n | avg R | t | half A | half B |
|---|---|---|---|---|---|
| A (ORB9 ≥10:00, day LONG) | 96 | +1.00 | 2.4 | +0.40 | +1.53 |
| B | 745 | +0.08 | 2.0 | +0.07 | +0.09 |
| C | 2,147 | −0.03 | −1.2 | −0.06 | +0.02 |
| F | 10,014 | +0.05 | 1.4 | +0.09 | −0.01 |
| long F (out of play) | 4,575 | **+0.17** | 2.4 | +0.28 | +0.04 |
| short C (allowed) | 1,580 | −0.02 | | −0.07 | +0.05 |
| short F | 5,439 | −0.06 | −5.1 | | |

A > B > C still ranks. **The long-side day gate does not:** hidden longs made +0.17R vs +0.09R for the allowed
ones; by sub-state "extended" +0.24 (n=1,905), "near the 21" +0.32, "no room" −0.06. ⚠ This is the direction the
hindsight universe is biased in (names picked because they trended in 2026 keep trending), so it is NOT a licence
to buy extended names — it is a reason to re-test the gate on a point-in-time universe before trusting it either way.

### Time of day, all long alerts (UR + ORB9 + LVL)

| bucket | n | avg R | win | half A | half B |
|---|---|---|---|---|---|
| 09:30–09:40 | 408 | **−0.16** | 33% | −0.07 | −0.23 |
| 09:41–09:50 | 1,285 | +0.10 | 39% | +0.06 | +0.15 |
| 09:51–10:00 | 866 | +0.04 | 40% | +0.16 | −0.08 |
| 10:01–10:30 | 1,508 | +0.08 | 40% | +0.08 | +0.08 |
| 10:31–12:00 | 1,451 | **+0.47** | 46% | +0.72 | +0.18 |
| after 12:00 | 471 | −0.01 | 48% | −0.02 | −0.01 |

**The "before 10:00 = C" cut is too broad.** Over 7 months only the first ten minutes are negative in both halves;
09:41–09:50 is as good as 10:00–10:30. The best window is 10:30–12:00 (ORB9 there +1.77R, n=308), and the afternoon
is flat. UR same-minute flood: 10+ names −0.18R, 5–9 names +0.22R. UR on a day-SHORT name +0.11R (t 2.6) vs +0.04 on
a day-LONG name — the reclaim in a downtrend did best, the gate is inverted for UR too.

### By kind

| kind | n | avg R | t | stopped | win | note |
|---|---|---|---|---|---|---|
| ORB9 | 807 | +0.77 | 2.0 | 73% | 26% | late fires +1.62 vs fresh +0.23: trend days carry it |
| UR | 4,761 | +0.06 | 3.0 | 40% | 44% | robust but small |
| LVL | 415 | +0.04 | 1.2 | 15% | 48% | flat; precision tag +0.02 (n=80), catalyst-size days +0.11 (n=101) |
| BIR | 3,488 | −0.05 | −3.4 | 32% | 44% | negative in every day-state |
| FBO | 3,085 | −0.04 | −3.2 | 22% | 46% | negative |
| PARA | 446 | −0.05 | −1.2 | 20% | 44% | negative |

Shorts have no positive cell in 153 sessions: the cap at C is generous. LVL has no intraday edge yet; the precision
tier, which quadrupled R on daily bars, does not separate on a 1-min alert scored to the close — the daily-close
entry and the 20-EMA hold are what the validation measured, not a same-day trade.

### Recommendations (NOT implemented — change `grading.py` only after a point-in-time universe re-test)

1. Time cell for longs: C = 09:30–09:40 and after 12:00, not "before 10:00". Consider A for ORB9 only from 10:30.
2. Long day gate: keep it as display context; do not widen it from this data (hindsight bias points the same way).
3. Shorts stay informational; FBO remains the long-exit tell.
4. LVL: informational until it has its own study on entries held past the day (the recipe's edge is multi-day).

### Control set: 39 large caps chosen without hindsight (added 2026-09-13, same 153 sessions)

`data/watchlist/universe_study_extra.txt` = the largest stocks by 50-day dollar volume as of 2026-01-30 that were not on
the curated lists (AVGO, META, GOOG, WMT, LLY, JPM, ... IBM), study-only. 19,456 alerts on the 134-name universe; the
split below is curated (focus + short lists, 95 names) vs control (39).

| | curated n | curated R | halves | control n | control R | halves |
|---|---|---|---|---|---|---|
| all longs | 6,569 | **+0.14** | +0.23 / +0.06 | 2,615 | **−0.05** | +0.02 / −0.11 |
| ORB9 | 891 | **+0.70** | +1.08 / +0.33 | 195 | **−0.39** | −0.41 / −0.37 (83% stopped) |
| UR | 5,203 | +0.05 | +0.10 / +0.02 | 2,317 | −0.02 | +0.05 / −0.08 |
| LVL | 475 | +0.07 | +0.04 / +0.11 | 103 | −0.10 | −0.00 / −0.21 |
| all shorts | 7,748 | −0.05 | | 3,313 | −0.01 | |
| longs 09:30–09:40 | 457 | −0.15 | −0.07 / −0.21 | 189 | −0.15 | −0.18 / −0.12 |
| longs 09:41–10:00 | 2,351 | +0.07 | +0.10 / +0.05 | 958 | +0.07 | +0.14 / 0.00 |
| longs 10:01–10:30 | 1,640 | +0.09 | | 622 | −0.16 | +0.01 / −0.31 |
| longs 10:31–12:00 | 1,603 | +0.42 | +0.72 / +0.14 | 642 | −0.09 | −0.12 / −0.07 |
| longs after 12:00 | 518 | 0.00 | | 204 | −0.05 | |
| longs day-LONG (allowed) | 1,867 | +0.07 | | 699 | −0.11 | |
| longs out of play | 4,702 | +0.17 | | 1,916 | −0.03 | |

**What survives on the control set:** (1) the first ten minutes are negative on both sets and in every half (−0.15 /
−0.15); (2) 09:41–10:00 is fine on both sets (+0.07 / +0.07, no negative half); (3) shorts have no edge anywhere;
(4) the long day gate does not rank on either set (day-LONG names were the *worst* control cell, −0.11).

**What does NOT survive — it was the curated universe, not the pattern:** ORB9's whole return (+0.70 curated,
−0.39 control: the A grade is a universe artifact), the 10:30–noon "best window" (+0.42 vs −0.09), UR's small edge,
and LVL's. On names picked without hindsight every long detector is ≈ 0 to negative. The alert engine is a pattern
surfacer; the return came from WHICH names were on the list ([[feedback_conviction_selection_is_the_strategy]]).

Caveat on the control itself: mega-caps are a different population (lower ADR, slower intraday trends), so "no edge
on large caps" is not the same as "no edge on liquid 3–7% ADR names picked point-in-time". That test (a point-in-time
universe built from the Adhikary/Minervini gates as of each month) is the next one to run before any rubric cell
other than the time floor is trusted.

**Rubric v2 that this supports (NOT applied):** C for longs only in 09:30–09:40 and after 12:00; B for everything
else that is day-LONG. The ORB9-after-10:00 A grade is unsupported on the control set and should drop to B until a
point-in-time test says otherwise. Shorts stay capped at C; day gate stays as display context.

**Rubric v2 APPLIED 2026-09-13** (`grading.py`, `RUBRIC_VERSION = v2-2026-09-13`): longs C = 09:30–09:40 or after
12:00, B = 09:41–12:00 on a day-LONG name (any kind), F = not day-LONG; ORB9's A dropped; shorts unchanged. Check on
the same 153 sessions: curated B +0.09 (halves +0.09 / +0.10) vs C −0.19 (−0.31 / −0.10) — ranks. Control B −0.12 vs
C −0.08 — nothing positive and no separation, i.e. the rubric grades the time floor, it does not claim an edge on
names picked without hindsight. Journal entries re-grade under v2 on the next `run_journal_grades.py` run.

### Shorts: search for any cell that earns a B (2026-09-13, 11,061 short alerts, curated + control)

No short cohort is positive on both universes and both halves: not by kind, time bucket, day state, SPY vs VWAP,
extension, level type, or in-play vs hidden. Profit-target covers (cover at +0.25R … +2R if the MFE reaches it, else
hold-to-close) do not fix it either: best −0.01R at +0.25R (73% win, losers eat it), and every target is negative on
the curated set in both halves. Half the shorts do reach +0.5R MFE, a quarter reach +1R, so the entries are not
random — the exits and the losers are the problem, and no simple exit rescues them. Nearest to a cell, 3 of 4 splits
positive but small: PARA 10:30–12:00 (+0.05 / +0.11, n=160), FBO 10:30–11:00 (n=1,079). Worst cell anywhere:
shorts on names >4 ADR over the 21 EMA, −0.22R, negative in all four splits (n=274) — the BWET-shaped trade.
Shorts stay capped at C = "unproven setup"; the journal keeps scoring trader-selected shorts separately so a
discretionary cohort can earn its own cell if it accumulates a positive record.

### Gap days and the VWAP reclaim (2026-09-14, `run_gap_reclaim_study.py`, 153 sessions, curated + control)

Prompted by 9/14: MRVL / TER / LITE / DRAM / SNDK fired UR after semis gapped ~7% down and were still tagged day-LONG
from Friday's close. Gap = open vs prior close in ADR units; group gap = mean of the name's group; halves × sets.

| UR cohort | n | R | win | stopped | 4 splits |
|---|---|---|---|---|---|
| name gap-down 1–1.5 ADR | 163 | **−0.13** | 33% | 44% | 3 of 4 negative |
| name gap-down 0.5–1 ADR | 1,048 | +0.10 | 42% | 45% | mixed |
| name gap-down 0.15–0.5 ADR | 2,880 | +0.06 | 42% | 44% | mixed |
| flat open | 1,955 | 0.00 | | | |
| name gap-UP 0.15–0.5 / >0.5 ADR | 937 / 446 | −0.02 / −0.01 | | | ~0 everywhere |
| gap-down ≥0.5 ADR, alert 09:30–09:40 | 204 | **−0.31** | 25% | 63% | |
| gap-down ≥0.5 ADR, alert 09:41–10:00 | 537 | **+0.22** | 42% | 49% | **all 4 positive** |
| group gap ≤ −2%, alert 09:30–09:40 | 150 | **−0.41** | 22% | 69% | curated only |
| group gap ≤ −2%, alert 09:41–10:00 / 10–12 | 445 / 405 | +0.16 / +0.11 | | | curated only |
| group ≤ −2% AND name ≤ −1 ADR (the MRVL/TER case), 09:41–10:00 | 50 | +0.11 | 40% | 44% | both halves + (curated only) |
| QQQ gap ≤ −1.5% (a broad gap-down day) | 380 | **+0.41** | 53% | 31% | **all 4 positive** |
| QQQ gap −1.5..−0.75% | 1,711 | −0.05 | 37% | 49% | |

Readings. (1) The asymmetry is real but reversed from the intuition: gap-UP reclaims are the flat ones (~0 in every
split); modest gap-DOWN reclaims are the better cohort. (2) Timing dominates direction: a reclaim in the first ten
minutes on a gapped-down name or group is the worst cell in the whole study (−0.31 / −0.41, 63–69% stopped); the same
reclaim after 09:40 is the best robust UR cell (+0.22, positive on both universes and both halves). (3) A name gap of
1–1.5 ADR is negative regardless of time → the open-time re-classification at 1 ADR (built 9/14) is supported; the
MRVL/TER sub-cell after 09:40 is +0.11 on n=50, so the gate costs a little recall there — precision over recall.
(4) The biggest index gap-downs (QQQ ≤ −1.5%, 9/14 qualified at −1.6%) are the best UR days, +0.41 robust; the
9/14 losses (ZETA 09:40, NUE 10:13) were the opening-window and the ordinary-failure cases, not the gap cases.
Being under the daily 9 EMA at the reclaim does not separate on ≥1 ADR gaps (−0.00 vs −0.23 above it).

### ORB9 with the index gate OFF (2026-09-14 evening re-replay, 153 sessions, every break collected and tagged)

Until 9/14 ORB9 could not fire while SPY was under its VWAP, so there was no data on that cell (0 of 1,086). With the
gate off the replay yields 1,431 ORB9 alerts, 319 of them with SPY under VWAP. Group-leading = the name's industry
ETF above its own VWAP, or 2/3+ of 3+ tracked peers green (control-set names carry no group, so their cells are NaN).

| ORB9 cohort | n | R | win | stopped | curA | curB | ctlA | ctlB |
|---|---|---|---|---|---|---|---|---|
| SPY above VWAP (the old shown set) | 1,112 | +0.49 | 23% | 75% | +1.05 | +0.32 | −0.41 | −0.39 |
| SPY below VWAP, all | 319 | +0.07 | 23% | 76% | −0.41 | +0.36 | −0.55 | +1.05 |
| SPY below, group NOT leading | 159 | −0.09 | 20% | 79% | −0.34 | −0.40 | −0.55 | +1.05 |
| SPY below, group LEADING | 160 | +0.24 | 26% | 73% | −0.46 | +0.68 | n/a | n/a |
| SPY below, 10:00–10:30 | 99 | +0.35 | 25% | 74% | −0.61 | +0.61 | −1.00 | +2.56 |
| SPY below, 10:30–12:00 | 101 | −0.12 | 16% | 82% | −0.86 | +0.61 | −1.00 | +0.24 |

Reading. The group-aware rule shipped 9/14 (suppress only when SPY is under VWAP AND the group is not leading) is
DIRECTIONALLY supported: leading +0.24R / 26% win / 73% stopped vs not-leading −0.09R / 20% / 79%. It is NOT robust:
the leading cell flips sign across halves (−0.46 / +0.68) on n=160, and every ORB9 cell is negative on the control set
regardless of the index, which restates the earlier finding that ORB9's return is the curated universe. Decision: keep
the group-aware gate live (a loosening the data does not contradict, and it restores the leaders on divergence days
such as CRWD 9/14), keep every ORB9 tagged, and re-cut this table when the second half has more sessions. Do not
promote "SPY below + group leading" to a grade cell.
