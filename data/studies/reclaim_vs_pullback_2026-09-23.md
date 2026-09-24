# Reclaim vs pullback-low: the creators' entry vs ours

_Ran 2026-09-23 (`run_reclaim_vs_pullback.py`); written up 2026-09-24 from the log and CSV only, with nothing
re-run. Sources: `data/studies/logs/reclaim_vs_pullback.log` and `data/studies/reclaim_vs_pullback_2026-09-23.csv`
(best exit per arm and cell). The pre-registration is the script docstring._

**Verdict: NULL · YIELD METHOD.** The reclaim (the creators' version) does not beat its own control, and neither
does the pullback-low. The dip-matched arm "passes" at t ≈ 30, but it conditions on the outcome, so it is not a
result.

## Question

Ariel ("it would also have to take out that 199 spot") and Mari Trades ("the first green print") both wait for the
pullback and then buy the **recovery**. Our retrace arm buys the **lower** price (`run_retrace_entry.py`, PARKED at
t 0.48). Both camps say "wait for the pullback", but they are different trades. The entry-extension mechanism
(paying 2.6 ADR costs about 0.4R) predicts that the lower entry wins.

## Setup (pre-registered)

- **Panel:** the liquid panel from 2019-10 to 2026-09. Eligible means ADDV ≥ $50M, price ≥ $5, not suspect,
  close > 20 EMA and ADR ≥ 3.
- **Event:** a session that sets the 10-session high (the PEAK), then a close at least PB_ADR ADR below that peak
  high within WAIT sessions. The grid is PB_ADR ∈ {1.0, 1.5} × WAIT ∈ {5, 10, 20}, which gives 6 cells.
- **Arms.** Every arm uses the same stop (1 ADR under the entry), the same close entry and the same 20-session
  horizon. Only the entry differs.
  - **A, pullback-low:** buy the close of the first bar that is ≥ PB_ADR below the peak high.
  - **B, reclaim:** buy the first close back **above** the peak high, within WAIT sessions of the pullback.
  - **C, dip-matched:** arm A restricted to the events that **later** reclaimed. It is not tradeable. It was
    declared only to separate timing (B vs C) from population (C vs A).
- **Control:** `post`, the same name on a random later session.
- **Pre-registered pass for the creators' version:**
  - B beats C with date-clustered |t| ≥ 3 and both halves the same sign.
  - B must also beat its `post` and `xname` controls.
  - The grid is 12 comparisons, so Šidák gives |t| ≥ 2.87. The house bar of 3.0 governs.
- **Prior:** about 70% that B loses to C on the mean. The interesting outcome would be B winning the win rate while
  losing the mean.

## Results (best exit per arm by edge; `t` is the harness's raw-R t against zero, **not** an edge t)

| PB / WAIT | pullbacks → reclaimed | ext at entry A / B (ADR) | A meanR (edge) | B meanR (edge), t | C meanR (edge), t |
|---|---|---|---|---|---|
| 1.0 / 5  | 41,679 → 10,949 (26%) | −1.33 / +0.27 | +0.043 (+0.020) | +0.071 (+0.043), 2.68 | +1.911 (+1.681), 29.6 |
| 1.0 / 10 | 49,909 → 20,924 (42%) | −1.33 / +0.25 | +0.033 (+0.010) | +0.048 (−0.004), 1.93 | +1.655 (+1.307), 32.5 |
| 1.0 / 20 | 57,121 → 31,200 (55%) | −1.33 / +0.23 | +0.039 (+0.024) | +0.051 (+0.008), 1.84 | +1.273 (+0.735), 27.5 |
| 1.5 / 5  | 26,484 → 4,424 (17%)  | −1.83 / +0.30 | +0.070 (+0.043) | +0.178 (+0.108), 2.69 | +2.666 (+2.296), 29.4 |
| 1.5 / 10 | 35,860 → 11,230 (31%) | −1.82 / +0.27 | +0.059 (+0.037) | +0.096 (+0.054), 2.05 | +2.300 (+1.828), 34.2 |
| 1.5 / 20 | 44,528 → 20,411 (46%) | −1.82 / +0.24 | +0.064 (+0.040) | +0.082 (+0.036), 2.47 | +1.802 (+1.075), 31.9 |

The best exit for A is `trail_bar` (`ema20` in the 1.0/5 cell), for B it is `ema20`, and for C it is `stop_hold`.
The counts in the "pullbacks → reclaimed" column are signals after the harness drops unfillable events.

### Reclaim (B), the creators' arm

- **Edge against `post` ranges from −0.004 to +0.108R.** The largest raw-R t is 2.69, in the 1.5 / 5 cell, which
  is below 3 even before the control is subtracted. The edge t would be smaller.
- **It fails both halves in every cell.** Before 2023 the `ema20` exit is negative in all six cells (−0.037 to
  −0.099R) and `stop_hold` is about zero. Everything positive sits in the back half, 2023 and later (+0.14 to
  +0.33R). That is the regime-in-the-back-half pattern, not a stable edge.

### Pullback-low (A)

- **Also flat against control:** edges run from +0.010 to +0.043R, with t ≤ 2.04 on raw R.
- The `stop_hold` exit earns +0.13 to +0.18R, but the control earns the same (edge −0.035 to +0.015).

### Win rate: the risk-versus-return split did not appear

On the **same exit** the two arms are indistinguishable. With `stop_hold`, A wins 35.1–35.4% and B wins 34.4–36.5%.

⚠ The Fit Mom Trader row (§9) quotes "39% vs 31–34%". That compares A's `trail_bar` exit with B's `ema20` exit, so
the gap is the exit, not the entry.

### Primary (B vs C)

- **B loses to C by 1.2 to 2.5R in every cell**, so the creators' version (B > C) fails as registered.
- The script never computed a paired B − C t. The sign is not in doubt, but the size is forced by construction.
  See the next section.

## Why arm C is an artefact, not a finding

- **C selects on the outcome.** C keeps only the pullbacks whose close **later** rose back above the peak high.
  Its entry is ≥ PB_ADR (1.0 or 1.5) ADR **below** that high, and the stop is 1 ADR. So every C trade is
  guaranteed a later close at least 1–1.5R above its entry within WAIT sessions. The sample was chosen for the
  move that it then "earns".
- **The signatures of outcome conditioning:**
  - The `t1R` exit wins **97–98%** in the 5-session cells. A 1R target is almost certain because the sample
    guaranteed it.
  - The advantage shrinks as WAIT grows: the edge falls from +1.68 to +0.74R at PB 1.0. A longer window leaves
    more room for the stop to hit before the guaranteed reclaim.
  - The deeper pullback (PB 1.5) gives the bigger "edge": +2.30R at 5 sessions. A deeper dip with the same
    required recovery guarantees a larger move.
- **The harness printed "passes the bar: YES" for C in all six cells** (t 27–34, both halves positive). The t is
  real arithmetic on a non-tradeable sample.
- **It is the same error as the UR band sweep retracted the same day.** That sweep produced t 27.8, with 84% of
  entries on the dip low of a reclaim that the sample guaranteed. `pmcc_study_2026-09-23.md` names it "the arm-C
  error".
- **What C still tells us:** the reclaim cohort's paths were very good *from the dip*. Nothing observable at the
  dip identifies that cohort in advance: A, which includes every pullback, is flat.

## Deviations and caveats

- **The `xname` control was pre-registered but not run.** Only `post` was run. This does not change the verdict:
  B already fails `post` and fails both halves.
- **The harness used the legacy report:** a raw-R t and a point `edge > 0`. The paired edge t and `p_search` from
  the same day's WL-2 upgrade were not applied.
- **Equity close-to-close with no option legs.** The house option cost model does not apply. Fills are at the
  close.
- **Survivor panel:** the liquid panel is names that are liquid as of 2026.
- **The ext_above_level mechanism did not show up here.** A enters about 1.6 ADR lower than B, but the two
  returns are the same within noise. The population also differs (A includes the pullbacks that kept falling), so
  this is not a test of the mechanism. It is noted, not claimed.

## Verdict

- **NULL** for the reclaim entry (the creators' version) and for the pullback-low entry. Both are about zero
  against the same-name random-later control, both fall short of t 3 even on raw R, and B's pre-2023 half is
  negative.
- **YIELD METHOD:** a "later succeeded" subset can never be a comparator arm. Use a tradeable population, or
  measure timing on a matched set chosen by information available at entry.
- **Not changed:** the retrace-entry row in §4 stays PARKED (t 0.48). That is a different design, anchored on the
  house breakout level.
