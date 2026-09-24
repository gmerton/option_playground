# Wedge Pop (Cycle of Price Action) -- Oliver Kell

> **Verdict:** The most objective setup in the TraderLion KB. A 10/20 EMA state machine with a precise trigger
> that he separates from the MA cross himself: **the buy is the break of a tight mini-base's swing high after a
> higher low, not the move back above the averages**. That claim comes with its own same-date control, so it can
> be tested cleanly. Evidence: none (his own winners, no base rate). His honest "60-70% of trades are losers"
> matches our book. The adjoining parts (EMA crossback, RS during a correction, selling exhaustion extensions)
> are FAIL or INVERTED here.
> **Type:** swing · **Instrument:** US equities (high-beta, liquid)
> **Conviction:** 2/5 · **Risk:** 6/10 (his sizing of 30-35% in one name: 9/10) · **Tested?** **no**
> **Source:** [notes](../videos/interviews/2025-12-21_fYxSQvuwOQc/notes.md) (TraderLion conference talk, uploaded
> 2025-12-21, 66 min)

---

## 1. Who, and what's being sold

Oliver Kell, "2020 US Investing Champion and record holder" (host [02:00]; figure not given on camera, widely
reported ~+941%, not verified here). Sells a book (kelltrading.com), The Swing Report newsletter and a Swing
Trading Masterclass via TraderLion University [01:04:50].

## 2. Mechanics as stated

- **State:** 10 EMA (red) and 20 EMA (blue); above both = green light, below = red [03:00-04:00]. SMA vs EMA
  "doesn't really matter" [04:00].
- **Cycle:** reversal extension (capitulation stretched below the MAs) -> snap back to the MAs -> a
  high-volatility retest -> **tightening + higher low** -> **wedge pop** through the swing high -> EMA crossback
  (first pullback into the MAs) -> 1-3 base-and-breaks (1-3 week consolidations) -> exhaustion extension ->
  wedge drop [00:00-08:02].
- **Trigger:** "Typically you are moving through the moving averages, but technically that's not the buy area
  ... It's breaking through the price structure, the swing high. You want a tight area, a mini base, and that's
  really the key" [01:01, 05:27].
- **Timeframes:** weekly for context (no trades below the 20-week EMA [12:00]; not extended on the weekly [11:01]);
  daily + 65-min to manage; 10-30-min to execute using the *daily* EMAs [13:01-16:02].
- **Exit:** a close under the 20-day by default; after the MA "holds 3-4 times", switch to the one it respects
  (10 or 20) [36:01]; or sell into an obvious blow-off [56:02].
- **Size:** 30-35% in a top liquid name, 15-20% liquid core, 7-12% in volatile names [51:00].

## 3. Claimed edge and returns

None for the setup. "Most of your trades are going to be losers, probably 60 to 70%" [48:59].

## 4. Objective assessment

- Every example is a live or past winner in a hot theme (HOOD, COIN, NVDA, SMR). No failed wedge pop is shown as
  such; the NVDA scratches are shown as the prelude to a winner.
- "Fractal, works on any timeframe" [08:02] makes the framework unfalsifiable as a whole; only a fixed daily spec
  can be scored.
- 2020 was the ideal year for a fast-MA trend follower. One contest year is one draw.

## 5. What's genuinely sound

Buy the structure break, not the indicator; don't create trades on lower timeframes; never chase, wait for the
next cycle point; a 60-70% loss rate is normal. All four agree with our results.

## 6. Overlap with the existing book

- **Reclaim vs pullback-low (2026-09-23):** the reclaim arm (first close back above a 10-session high after a
  >= 1 ADR pullback) earned +0.048 to +0.178R (t 1.84-2.69), edge over its `post` control -0.004 to +0.108R,
  below the bar. The wedge pop is a stricter reclaim: after a *correction below the MAs*, out of a *tight base*
  with a *higher low*.
- **EMA crossback** = the Luk/Ariel EMA pullback: **FAIL** on daily bars.
- **Exit** = the house 20-EMA trail, already the best exit tested.

## 7. Codable spec (daily bars, pre-registerable) -- NOT RUN

Liquid panel, eligibility as of the signal date, 2019-10 onward; all windows end at the signal close.
**Default [discretionary range]**; (S) = he states it, (H) = house normalisation where he is vague.

| # | Element | Rule | Source |
|---|---|---|---|
| 1 | Weekly context | close >= EMA(100) (~20-week EMA) | (S) 12:00, conversion (H) |
| 2 | Not extended on the weekly | (close / EMA(50) - 1) / ADR <= **3** [2-5] | (S) 11:01, threshold (H) |
| 3 | Liquidity / beta | ADR >= **3** [3-4]; eligible | (S) 21:02 "high beta", (H) |
| 4 | Correction ("red light") | in the last **40** [30-60] sessions: >= **5** [3-10] closes below EMA(20) | (S) 03:00, counts (H) |
| 5 | Reversal extension | min low in that window <= EMA(20) - **1.5** [1-3] ADR at that session | (S) 00:00, 04:00, depth (H) |
| 6 | Higher low | min low of the mini base > the correction low (rule 5 low) | (S) 05:27, 25:01 |
| 7 | Mini base | the **5** [3-10] sessions before the trigger span <= **2.0** [1.5-3] ADR high-to-low | (S) 06:04, 29:00, size (H) |
| 8 | Volatility contraction | mean (high-low)/close over the base <= **0.8x** [0.6-1.0] the 20d ADR | (S) 00:00 "decreasing volatility" |
| 9 | Base at the MAs | base low within **1.0** [0.5-1.5] ADR of EMA(20) | (S) 01:01 "consolidates down into the 20-day" |
| **T** | **Trigger (PRIMARY)** | first close > max high of the base **and** close > EMA(10) and EMA(20), the first such close since rule 4's last sub-EMA(20) close | (S) 01:01, 05:27 |
| X | Crossback arm (secondary) | after T, the first close within **0.5** ADR of EMA(10) or EMA(20) that closes up on the day, within 15 sessions | (S) 06:04 |

- **Entry:** the trigger close (house convention; he buys intraday through the pivot).
- **Stop:** base low (his higher low), judged on the close; report stop/ADR; floor 0.5 ADR (widen, cut size).
- **Exit:** first close < EMA(20) **primary** [36:01]; arm: EMA(10); cap 120 sessions; 0.10% slippage a side.
- **One signal per name per correction.**

## 8. Pattern_test design (sketch, NOT RUN)

**Question 1 (primary): does the wedge pop beat an ordinary breakout on the same day?**
- Pattern function over `load_panel()` (+ volume from the parquet for optional RVOL covariates) ->
  `daily_signals(hit, stop)`; `run_daily(..., entry_at="close", control="post")` and `"xname"` for the ledger row
  only (see the HTF file for why neither is the primary comparison).
- **Primary control (custom, the VCP-script method):** all **house breakouts on the same date in other names**
  (close > prior 20d high, ADR >= 3, eligible), same entry at the close, same exit rule, own entry-day-low stop.
  Paired per-signal diff in **% return**, date-clustered t.
- Wedge pops mostly fire *below* the prior 20d high (after a correction), so this comparison also tests entry
  location: report `ext_above_level` (entry vs prior 20d high, in ADR) for both sides. The entry-extension
  mechanism predicts the wedge pop should win.

**Question 2 (his actual claim): is the structure the key, or just being back above the EMAs?**
- **Structure control (holds the name-state and date fixed):** same-date signals in other names that meet rules
  1-5 and cross back above EMA(10) and EMA(20) for the first time since the correction, but **fail rules 6-9**
  (no higher low or no tight base). Same entry, exit and stop definitions (stop = 5-session low). His claim
  [01:01] predicts wedge pop > MA-cross-only.

**Question 3 (exploratory):** crossback arm X vs the trigger T on the same events. The daily EMA-pullback FAIL
predicts X <= T.

- **Pre-registered bar:** primary = T vs same-date house breakouts, 20-EMA exit, % return. Date-clustered
  |t| >= 3, both halves the same sign, per-year signs reported, and T must also beat the structure control
  (Q2) with the same sign. Cells: 2 questions x 2 exits = 4 primary -> Sidak |t| >= 2.49; house 3.0 governs.
  Parameter neighbourhood: re-run rules 5, 7 and 9 at the ends of their ranges; the verdict needs a plateau, not
  a spike (method queue).
- **Power:** a correction-and-reclaim happens several times a year per name, so expect thousands of events on
  the liquid panel. This test can reach power; the HTF may not.
- **Prior:** ~65% NULL. The reclaim arm (its loose cousin) sits at t 1.84-2.69; VCP tightening added nothing;
  the house breakout is the negative-edge comparator, so a wedge pop that beats it only because it buys lower
  would restate the entry-extension finding, not validate Kell. The Q2 structure control is what separates the
  two.
- **Clean-result check:** a large positive is an artefact until excluded. Verify no rule reads past t (the
  "higher low" must be known at t: base low vs a correction low that is >= 3 sessions before the base starts).

## 9. Testability

EOD-testable now. The 65-min higher-low re-entry and 10-30-min execution need intraday bars beyond the ~2026 1-min
cache.
