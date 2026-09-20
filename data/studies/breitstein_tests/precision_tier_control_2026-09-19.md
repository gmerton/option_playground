# The house entry against a random control — and a flaw in the control

_2026-09-19 · `run_precision_tier_control.py` (+ `--close`), `breitstein_tests/precision_tier_unclipped.py`,
`breitstein_tests/precision_tier_controls.py` · logs in `logs/precision_tier_*` · summaries
`precision_tier_*_2026-09-19.csv` · pool = `run_exit_timing_study.py`'s precision tier (n 2,023 close entries,
1,944 next-open, 2019-10 → 2026-09)_

## Verdict

**The house entry survives, smaller than advertised, and the harness's control was wrong.**

1. The +0.79R headline (exit-timing study) was inflated by trades with near-zero stops. With a tradeable
   2% stop floor the close-entry, 20-EMA-trail process earns **+0.63R unclipped (t 3.9)**, **+0.39R with
   R capped at 20 (t 3.3)**, and only **+0.15R at the harness's ±10R cap (t 1.5)**. Median −1.08R, 30% win.
   The return IS the right tail: 4.5% of trades exceed 10R and the top 1% carry 26% of gross gains.
2. Against **honest controls** it wins: +0.60R over a random other name on the same date (selection),
   +0.30R over a random later session in the same name (timing). Both halves positive, though the timing
   edge is 2023+ (pre-2023 signal ≈ later-day control).
3. The harness's original **same-month control has look-ahead**: it draws sessions from *before* the
   signal in a name that is about to fire. For this pattern it "earns" +1.70R, three times the signal, in
   every year. **Every one of the 25 ledger rows to date used that control.** The "0 for 25, random beats
   the pattern" conclusion is partly the control, not the patterns. Re-run queued (see below).

## Reconciling the +0.79R

`data/cache/exit_timing_trades.parquet`, precision tier, `book_close` (close entry, 20 EMA trail, 60-cap):

| risk floor | R cap 10 | R cap 20 | R cap 50 | no cap |
|---|---|---|---|---|
| none (as reported) | +0.22 (t 1.9) | +0.40 | +0.46 (t 3.1) | **+0.79 (t 4.3)** |
| ≥ 2% of price | +0.18 (t 1.7) | +0.40 (t 3.4) | +0.59 (t 3.8) | +0.62 (t 3.7) |
| ≥ 3% of price | +0.25 (t 2.4) | +0.45 (t 3.7) | +0.57 (t 3.9) | +0.57 (t 3.9) |

The largest raw trades were 762R on a 0.4% stop, 127R on 0.2%, 92R on 0.1%: unfillable stops. A 2–3%
floor removes them and the mean settles at +0.4 to +0.6R depending only on how far the right tail is
allowed to count. **The harness's ±10R winsorisation is too tight for a breakout book** (it removes a
quarter of the gross), which is why the first harness pass read −0.04R at hold 5 and +0.08R at hold 60.

## The house process vs three controls (close entry, stop = day low, 20 EMA trail, hold 60, risk ≥ 2%)

| control | what it asks | ctrl ema20 (no cap / cap 20 / cap 10) | edge (no cap / cap 20 / cap 10) | ctrl win |
|---|---|---|---|---|
| **xname**: random eligible other name, same date, same stop % | is the NAME selection worth anything? | +0.03 / +0.01 / −0.04 | **+0.60 / +0.39 / +0.18** | 33% |
| **post**: random session in the 20 after the signal, same name | is the signal DAY better than a later day in a name known to have fired? | +0.33 / +0.25 / +0.10 | **+0.30 / +0.14 / +0.05** | 32% |
| **month** (original): random session in the same calendar month, same name | ⚠ includes pre-signal days → look-ahead | +1.70 / +1.41 / +1.10 | −1.07 / −1.01 / −0.95 | 48% |

Signal: +0.63 / +0.39 / +0.15, win 30%, n 1,968.

By year (ema20, no cap): signal −0.59 / +0.46 / −0.26 / +0.11 / +0.29 / +1.45 / +1.96 / +0.44 (2019→26);
post control −0.12 / +0.70 / −0.30 / +0.06 / −0.12 / +0.86 / +0.74 / +0.30; xname control +0.36 / +0.22 /
−0.04 / −0.37 / +0.29 / −0.12 / +0.17 / −0.04; month control +1.17 / +1.96 / +0.67 / +0.94 / +1.50 / +2.35 /
+2.42 / +1.76. The month control beats the signal in every year: that is the look-ahead, not a market fact.

Next-open entry (the harness default) is uniformly ~0.05–0.1R worse than the close entry, consistent with
the entry study.

## Reading

- **Selection is real, timing is modest.** Most of the edge over a random name is the name (the tier's ADR
  4–7 / near-high / stacked filters); the breakout day adds +0.1 to +0.3R over a later day in the same
  name, and that part is concentrated in 2023–26.
- **Honest expectation for the equity book:** +0.4R per trade with a 30% win rate and a −1.08R median,
  assuming the right tail is allowed to run to 20R+ and stops are ≥ 2% of price. Not +0.79R. Sizing must
  assume long strings of −1R.
- **The bar was not "passed" under the harness's own convention** (±10R cap: t 1.5). It passes at cap 20
  with a 2% floor. Record it as MARGINAL-PASS with the cap stated, not as a clean pass.

## ⚠ Consequence for the pattern ledger

`lib.studies.pattern_test` now has three control modes (`control="month" | "post" | "xname"`) and a
`entry_at="close"` option. The `month` control stays the default only for comparability; **new rows should
use `post` (timing) and `xname` (selection), and the 25 existing rows need a re-run** — especially the
continuation patterns (in-play movers, earnings drift, Stage A's random-minute-same-day control, which
has the same pre-trigger look-ahead) and the bouncy-ball short, whose "control +0.34/+0.48" was random
sessions in a month the name was known to break down. Queued as the top item in `TEST_INDEX.md` §10.

Ledger: the two next-open rows written today used the month control (kept, flagged in the note); one
additional row records the house process against the `post` control at cap 20 / floor 2%.
