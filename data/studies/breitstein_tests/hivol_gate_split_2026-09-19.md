# Breitstein test 4: the high-volatility regime gate as a split of the house breakout

_2026-09-19 · `run_hivol_gate_split.py` · log `logs/hivol_gate_split_2026-09-19.log` · summary
`hivol_gate_split_summary_2026-09-19.csv` · spec `data/lance_breitstein/principles/high-volatility-playbook.md`_

## Verdict

**No switch.** The high-vol and low-vol halves of the 20-day breakout produce the same per-arm
results to within ±0.02R, and the fast exit (`t1R`) is the **worst** arm in both halves in every
configuration. Breitstein's claim (fast exits in a high-vol tape, slow ones otherwise) does not show
up on this book; the exit-timing result (slow exits beat fast ones) generalises across regimes.
Both arms are negative and both lose to the same-name random control, so there is nothing to gate.

## What was run

- Signal: close above the prior 20 sessions' highs, ADR ≥ 3, liquid panel (1,743 names, 2019–2026). Long.
- Stop: 1 ADR below the signal close (sweep 2 ADR). Entry next open, 10 bps slippage.
- Regime: cross-sectional median 20-day realised vol (from the panel) above its own expanding
  trailing-252 80th percentile. Point-in-time; defined 2020-02-12 onward (warm-up excluded from BOTH arms).
  HIGH = 25.4% of sessions, 21 episodes; longest: 2026-04-08→08-26 (98), 2020-02-12→06-16 (87),
  2022-04-29→07-12 (50), 2026-02-03→03-24 (35), 2022-02-15→04-01 (33), 2025-04-03→05-08 (25).
- Sweeps: pct 0.70 / 0.90; stop 2 ADR; hold 20; VIX close as the regime series.
- Harness: `lib.studies.pattern_test.run_daily`; control = same name, random session, same month
  (so the control shares the regime). Ledger rows written for the primary config only.

## Primary config (p80, 1 ADR, hold 5) — per exit arm

| arm | HIGH meanR | HIGH ctrl | HIGH t | LOW meanR | LOW ctrl | LOW t | H−L |
|---|---|---|---|---|---|---|---|
| stop_hold | −0.087 | +0.561 | −1.2 | −0.070 | +0.575 | −0.8 | −0.02 |
| t1R | −0.216 | +0.150 | −5.7 | −0.224 | +0.144 | −10.5 | +0.01 |
| t2R | −0.151 | +0.356 | −2.9 | −0.153 | +0.360 | −5.3 | 0.00 |
| trail_bar | −0.083 | +0.484 | −1.8 | −0.089 | +0.498 | −1.4 | +0.01 |
| ema20 | −0.087 | +0.399 | −1.2 | −0.070 | +0.431 | −0.7 | −0.02 |

n = 17,281 HIGH / 24,514 LOW. Win rates 38–48% in both. Halves: HIGH is −0.28 pre-2023 and
+0.05 after (all slow arms); LOW is −0.08 / −0.06. Neither arm passes.

## Sweeps — best arm by mean R per half

| regime src | pct | stop | hold | HIGH best (meanR) | HIGH t1R | LOW best (meanR) | LOW t1R |
|---|---|---|---|---|---|---|---|
| panel | 0.80 | 1 ADR | 5 | trail_bar (−0.08) | −0.22 | ema20 (−0.07) | −0.22 |
| panel | 0.70 | 1 ADR | 5 | ema20 (−0.09) | −0.22 | stop_hold (−0.07) | −0.23 |
| panel | 0.90 | 1 ADR | 5 | stop_hold (+0.03) | −0.04 | ema20 (−0.09) | −0.24 |
| panel | 0.80 | 2 ADR | 5 | trail_bar (−0.03) | −0.08 | stop_hold (−0.02) | −0.06 |
| panel | 0.80 | 1 ADR | 20 | stop_hold (−0.02) | −0.24 | stop_hold (+0.02) | −0.29 |
| VIX | 0.80 | 1 ADR | 5 | trail_bar (−0.13) | −0.24 | ema20 (−0.07) | −0.22 |

The fast exit is the worst arm in all 12 cells. The slow arms tie for best in all 12.

## Reading

1. **The horizon switch is folklore on daily bars.** His prediction (HIGH → `t1R`, LOW → `ema20`)
   fails in the direction it needed: `t1R` is the worst arm in the high-vol half too, by the same
   margin as in the low-vol half. Same-day/fast exits are the negative bucket regardless of regime.
2. **The p90 cell is the only sign of life, and it is beta, not horizon.** At the extreme (top decile,
   n 3,363), every arm is +0.12 to +0.20R better in HIGH than LOW and the slow arms turn marginally
   positive (+0.03). But the control is +0.50 in that cell, so the breakout entry still loses to a
   random same-name entry by 0.24–0.47R. That matches the gap study's high-VIX tercile: a high-vol
   tape lifts everything, it does not make a trigger good. The Aug-2026 retrospective already found
   this direction (weak breadth = mild BUY); it is not a size or horizon rule.
3. **The VIX version is worse for HIGH**, not better (−0.13 vs −0.07 all slow arms). Cross-sectional
   realised vol and the VIX pick different days (VIX HIGH = 12% of sessions vs 25%), and neither
   flips an exit arm.
4. **Control > signal by 0.4–0.7R in every cell** is the familiar harness result: a mechanical 20-day
   breakout with a 1-ADR stop is tagged 52–62% of the time, so a random session in the same name and
   month, with the same stop distance, does better. This is the *generic* breakout, not the
   precision-tier house entry (+0.79R, ADR 4–7, <15% off high, stack 5–40d), which has not been run
   through this harness yet.

## Consequence for the repo

- `feedback_weight_current_conditions` / breakout-regime feedback stand: **regime management = fixed
  small sizing, no switch.** The volatility carve-out the spec allowed for is not needed.
- The one thing worth carrying: if a regime split is ever re-run, do it on the **precision-tier**
  signal (the only cell with a positive mean), not on the generic breakout, and only at the p90 level.
  Expect beta, not an exit rule.
- Not tested here, still open from the video: "spend the loss limit late" (journal, process) and
  overnight-size reduction (our return IS the overnight hold; the entry study already says no).

Ledger rows: `data/studies/pattern_ledger.md` 2026-09-19 (2 rows, both `passed = False`).
