# VWAP Trading Strategy Crash Course (Humbled Trader)

**Video:** `dgfQkFSzhiY` · 43 min · published 2023-05-25 · reviewed 2026-09-28 · auto-captions

> **2/5 · one NEW test (the VWAP side as a directional state, i.e. the "VWAP veto").** Tutorial, two recorded
> trades, course pitch [42:57]. Every rule is shown on a hand-picked chart after the fact; no win rate, sample or expectancy. Every VWAP *trigger* she teaches
> (reclaim, rejection, break-and-fade short, pullback-to-VWAP on a breakout day) is already NULL or worse in the
> ledger against a same-name-day random minute. **Both live entries were on the wrong side of VWAP by her
> own rule**. The only untested piece is the premise under all of it:
> does the *side* of VWAP predict the rest of the session? That is the queued, never-run Breitstein VWAP veto.

## Her rules as stated

| @ | rule | quote |
|---|---|---|
| 02:04, 09:21 | Bias: long names holding above VWAP, short names below | "you want a short stocks that's below v-wap and long stocks it's holding above" |
| 05:10–07:16 | **VWAP reclaim (long):** after 1–2 failed attempts, a reclaim "around 10:30 to 11 o'clock" with higher lows and rising 5-min buy volume, then buy pullbacks | "this is what we call a v what reclaim" |
| 07:16–08:19 | **Repeated rejection (short):** 3+ failed retests plus rising sell volume = "no bounce city", closes at the lows | NVDA example |
| 10:24–12:30 | **Daily-breakout long:** gap/break above the prior-day high at the open, buy dips that hold VWAP, "especially early in the morning"; small and large caps (INDO, OXY) | "use any dips towards a view up area as your long entries" |
| 12:30–15:36 | **Break-and-fade short / long exit:** a meme stock that loses VWAP "fade[s] all day"; she cuts longs on the break and rides shorts to the close | "once it breaks down v-wap it stays extremely heavy" |
| 16:40–21:56 | **Short trap (avoid shorting / long trigger):** higher lows *below* VWAP, midday (11:00–13:30), low volume, then a reclaim squeezes | "around 11 o'clock 12 o'clock that's like the prime time for short traps" |
| 37:42–41:54 | **Stops:** algos run stops around VWAP on small caps; "do not put stops Too Close to v-wap" | TNYA example |

2-min and 5-min charts. Other stops and all targets discretionary (HOD wick for front-side shorts [24:02]). No time stop.

## Evidence

- **COIN short, "Aug 4"** [22:59–30:18]: short ~110 into a parabolic open on catalyst news, after a −$3.6k cut on the same
  name; closed **+$15k**. ⚠ Entry was **above VWAP** (her "shorting the front side",
  waiting for it to "break down towards v-wap").
- **PYPL long, "Aug 3"** [30:18–36:40]: earnings gap, bought the first green 5-min candle ~100.73 **below VWAP** and
  waiting "to see the stock reclaim over v-wap"; added on the reclaim, rejected at 101.90, stopped at 100.20, **−$400**.
- n = 2, no base rate: a demonstration. Not winners-only (a loser and an APE stop-out are shown).

## Claims against the ledger

| claim | verdict | TEST_INDEX row |
|---|---|---|
| VWAP reclaim after a flush + higher lows = long entry | **CONTRADICTED** (NULL as a trigger) | Alert suite 2026-09-23: **UR** (VWAP reclaim after a flush + higher low) +0.033pp vs same-name-day random minute, t −0.31; Stage A 11,227 alerts ≈ a random later minute |
| Repeated VWAP rejection = short | **CONTRADICTED** | VWAP double-rejection short 2026-09-21: 2nd touch −0.26R (t −6.2) vs same-day random −0.17R |
| Loses VWAP → fades all day (short it / cut the long) | **CONTRADICTED** on tested populations | Tito exhaustion fade honest (short first close below VWAP): −0.02 vs random minute, t −0.15; Stage A "VWAP loss" exit +0.013R vs control |
| Breakout day (above the prior-day high) + VWAP-hold dips = long | **CONTRADICTED** as a timing edge | Level triggers NULL 0/12 incl. PDH, AVWAP ("the level picks the DAY, not the minute"); ORB9 INVERTED −0.425pp, t −8.50 |
| Midday short trap: higher lows below VWAP then reclaim squeezes | **UNTESTED as a midday-only cut**; parent (UR) NULL | a time split of UR trades = exploratory, not new |
| Don't set stops right at VWAP (too tight) | **AGREES** (mechanics) | ORB9 stop floor ADOPTED (structural stops median 0.15 ADR, 73% stopped) |
| **Side of VWAP is a directional state** (the premise) | **UNTESTED** | §10 "intraday versions of the daily nulls" (VWAP-veto arm); Breitstein `trend-definition-and-counter-trend-entry.md`: "not run" |

## New test: VWAP side as a state (the veto), not a trigger

**Pre-registrable spec.** Universe: liquid names, ADR ≥ 2%, $ADV ≥ $20M. At fixed check times **11:00 (primary)**, 10:00,
12:00, 13:30, classify each name-day ABOVE if price ≥ session VWAP + 0.1 ADR, BELOW if ≤ VWAP − 0.1 ADR, else skip.
Session VWAP must be `lib.journal.exit_kind.session_vwap(bars)`; ⚠ the cached `vwap` column is **per-bar**, and reading it
as session VWAP makes the state a coin flip. Outcome: return from the check-minute close to the 15:59 close, **minus SPY
over the same window**, in % (no stop, so no R denominator). Primary statistic: mean(ABOVE) − mean(BELOW), t clustered by
date. **Control that holds the confound fixed:** the same name at the same clock time on its opposite-state days
(name × clock fixed effects), so name drift and time-of-day seasonality cancel, with SPY removing the market's day. The
claim predicts **continuation** (positive spread); intraday mean reversion predicts negative. Bar: |t| ≥ 3 at 11:00,
both chronological halves and ≥ 70% of months the same sign; the other three check times are exploratory under
Šidák(4) |t| ≥ 2.5. Report gross and net of ~0.05–0.10% a round trip.

**Data.** Runs locally. Pilot on the 1-min watchlist cache (`data/cache/intraday_1min`, ~24.8k name-days Feb–Sep 2026;
curated names, so treat it as a pilot). Primary run on the Polygon 1-min backfill (~1,700 names, 2024-10 → 2026-09, still
filling; freeze the list first), SPY from `data/cache/intraday_hist`. ⚠ ~2 years only: per-month signs carry the weight.
