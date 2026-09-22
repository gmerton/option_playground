# ICT sweep → 1-min FVG reversion on QQQ, paper vs queue-aware fills (2026-09-21)

## Pre-registration (written BEFORE any code ran; do not edit this section after the results)

**Question.** AI Pathways (video KML09tRtHM8, reviewed 3/5 in `data/ai_pathways/`) found one surviving ICT version
on 1-min NQ/ES: liquidity sweep → 1-minute fair-value-gap retrace entry, faded against the swept side, any hour, no
bias, traded often, ~+$251k on 1 NQ contract over their 2-year holdout. Their fills were paper fills (a touch of the
limit fills). **Does the edge survive (a) on QQQ over 2007–2026 and (b) when a limit only fills if price trades
THROUGH it by one tick?**

**Data.** QQQ 1-min regular-session bars (IBKR), 2007-01-03 → 2026-09-17, `data/cache/intraday_hist/QQQ_1min.parquet`.
QQQ tracks NQ; its $0.01 tick is a similar fraction of price to NQ's 0.25 point.

**My reading of their loose "as-traded" version (their exact dials are not published; fixed here, not tuned):**
- Liquidity = any recent 1-min swing: a swing low at bar j is a low strictly below the 3 bars on each side,
  confirmed at bar j+3, and live for 60 bars (swing highs mirrored).
- Sweep = a bar trades ≥ 1 tick beyond a live swing (low ≤ swing low − $0.01); that swing is consumed.
  Direction = fade the swept side (sweep a low → long; sweep a high → short).
- FVG = within 10 bars after the sweep, a 3-bar gap in the fade direction (long: low[k] > high[k−2]), size ≥ max($0.01,
  0.01% of price).
- Entry = limit at the gap midpoint (their "50% of the gap" default), live 20 bars, cancelled if the target trades
  first or after 15:30. Stop = the sweep's extreme − $0.01. Target = 2R. One position at a time; re-entry allowed
  after an exit. Flat at the 15:59 close. Entries 09:35–15:30.
- Exits: stop and target in the same bar = a loss; a stop exits at stop − 1 tick (or the bar open if it gaps through);
  the target exits at the target. Commission $0.0035/share each side.

**Fill models (the question).** PAPER: a buy limit fills when the bar's low ≤ the limit. QUEUE-AWARE: only when the
low ≤ limit − $0.01 (traded through). Fill price = the limit (or the open if the bar opens through it). Same for shorts.

**Control.** For every signal trade, 3 random minutes on the same day (09:35–15:30), same side, market entry at that
bar's open, same stop distance in %, same 2R target, same exit engine and costs. Edge = signal R − control R.

**Pass bar (queue-aware fills; paper reported for comparison).** Mean R > 0 AND beats the control AND |t| ≥ 3 on
day-clustered means AND positive in all three periods: 2007–2016, 2017–2023, 2024–2026 (their holdout era). Also
reported: trades per year, win rate, R per year.

**Not tested (named so they can't be added quietly):** displacement filter, the 3 ICT hour windows, daily/15-min bias,
other entry points in the gap, other targets, NQ/ES futures themselves. One configuration, two fill models, one run.

---

## Results (run 2026-09-21, after the pre-registration above; script `run_ict_sweep_fvg_qqq.py`, log `.log`, table `.csv`)

**Verdict: FAIL, both fill models, every year. No edge even gross of commission on paper fills. MECHANISM: the
queue-aware fill costs ~0.10R per trade, the adverse selection AI Pathways flagged.** Sanity: my reading of their loose
version fires ~6.7 times a day (~1,300 trades a year after one-position-at-a-time), near their ~2,000.

| fill model | trades | per year | win | mean R (net) | t (days) | same-day random minute | edge | gross R (no commission) | 2007–16 | 2017–23 | 2024–26 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| paper (touch fills) | 25,856 | 1,293 | 33.9% | **−0.109** | −8.2 | −0.169 | +0.060 | −0.046 (t −1.7) | −0.142 | −0.086 | −0.082 |
| **queue-aware (through by 1 tick)** | 24,590 | 1,230 | 30.6% | **−0.205** | −18.0 | −0.172 | **−0.033** | −0.144 | −0.319 | −0.141 | −0.103 |

- **Negative in all 20 years under both fill models**, including 2024–2026, the era of their sealed holdout.
- **Paper fills beat a random minute by +0.06R**: the sweep does time entries a little better than chance (their "the
  sweep is the only rule that adds"), but not enough to be positive even before commission.
- **Realistic fills remove even that.** Requiring the price to trade through the limit costs ~0.10R per trade and flips
  the edge vs random to −0.033R. Touches that bounce don't fill; touches that run through do.
- Stops are tight (median $0.16, ~10 bps of price), so commission is 0.044R a trade; it isn't the cause.

**What this does and doesn't show.** It kills this reading of their survivor on QQQ. It doesn't prove their NQ result
wrong: their dials aren't published, and futures fills, costs and micro-structure differ. But their positive result was
on paper fills over a 2-year bull holdout, and on 20 years of QQQ the paper-fill version is already negative before
costs. Consistent with Stage A and the level-trigger test: no intraday trigger we've tested beats a random minute at
realistic fills.
