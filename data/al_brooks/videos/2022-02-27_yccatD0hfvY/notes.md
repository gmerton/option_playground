# Al Brooks: "Scalping — How to Enter" (London Price Action Symposium teaser, Trader Tom channel, 2022-02-27, 39:02)

_Reviewed 2026-09-24 at Gabe's request. A recorded 36-minute webinar by Al Brooks (Brooks Trading Course), introduced
by Tom Hougaard as a teaser for his paid London symposium (00:00–03:02 is the pitch). Transcript (`en-orig` auto
captions) in this folder. Charts are E-mini 5-minute bars; the slides are not in the transcript, so every chart
reference below is to an example we cannot see._

## Verdict: 2.5 / 5

**Half of this talk is the most useful thing a scalping video could say to this desk: most traders should not
scalp.** Brooks's own conclusion, repeated four times (16:16, 34:41, 35:07, 38:19): *"most traders should be looking
for trends, most traders should be swing trading, and most traders should be entering with stops."* His trader's
equation (16:34) is correct and explains the owner's measured leak exactly: a scalp takes a small reward against its
risk, so it needs a very high win rate ("a good scalper can win 80 or 90 percent of the time", 20:21) to be
profitable. Gabe's same-day round trips win **19%** (278 cycles, −$8.3k). No reward-to-risk rescues that.

**The other half is dangerous as stated.** The limit-order scalping method he describes — wide stops, scaling in
against the move, and *doubling the position* when a breakout goes against you ("an experienced trader might double
his position as soon as he sees the bull bar", 24:20; "I personally like to double my position size there", 25:55)
— is averaging down. He says beginners fail at it precisely because they cannot hold size through the big move
(24:45–26:18), which is a description of the strategy's tail, not of a beginner's flaw. Every chart is chosen after
the fact; no n, no win rate from data, no drawdown.

Capped by: no study anywhere; day-type (trend vs range) is classified from the finished chart; entry rules are exactly
the intraday-trigger family our ledger finds carries no edge.

## Data audit

| item | what the talk gives |
|---|---|
| instrument / bars | E-mini S&P (and forex mentioned), 5-minute chart |
| period | **not stated**; hand-picked example days |
| n | **none** — every claim is illustrated by one chart |
| entry rules | stop entry 1 tick above a bull signal bar / below a bear bar; limit entries at prior highs/lows, at big-bar closes, at the 20-bar EMA |
| management | trading range: scalp 1–10 pts scaled to bar size, wide stop (measured move), scale in, double on a breakout against; trend: buy and hold, stop below the prior bar / swing low, trail |
| fills / costs | none mentioned |
| control | none |
| win rate / avg / tail | "80 or 90 percent" asserted for good scalpers (20:21); tail described qualitatively ("one big loss can erase a whole bunch of winners", 20:38) |
| significance | none |
| selection | examples picked to show each pattern; trend vs range day identified in hindsight |
| conflicts | a paid-event teaser; Brooks sells a course |

## Numbers and claims as spoken

| time | claim | vs our ledger |
|---|---|---|
| 04:02–08:18 | Stop orders are a bet on trend, limit orders a bet on reversal; stops win in trends, limits in ranges | ✅ **Coherent framing, not testable as stated** (it is true by construction once the day is labelled). Its testable form is the day-type question below |
| 09:36–10:13 | Range day = overlapping bars, big tails, alternating colours, no consecutive big trend bars | ⚠ A real-time classifier would need these rules made mechanical; in the talk the label is applied to finished charts |
| 10:20–10:44, 16:16, 34:41, 38:19 | **Most traders make more money swing trading, entering with stops, in trends** | ✅ **AGREES — strongly.** `exit_timing_study_2026-09-18.md`: same-day exits are the negative bucket in both books (scalp −0.13R vs 20-EMA trail +0.89R); Gabe's 278 same-day cycles −$8.3k at 19% win (TEST_INDEX exit-timing row). Close entry beats every intraday entry (`project_entry_study`) |
| 11:46–12:10 | "Think opposite" in a range: buy big bear closes near the low, sell big bull closes near the high | ⚠ **Adjacent evidence is negative.** Intraday fades we have tested fail: VWAP double-rejection short worse than random (−0.26R, t −6.2); Tito exhaustion fade RETRACTED; capitulation scorecard fails both sides. None is his exact rule (range-conditioned bar-close fades), so UNTESTED as stated |
| 16:34–17:17 | Trader's equation: win% × avg win > loss% × avg loss; scalps have bad reward/risk, so need high probability | ✅ **Correct, and it is the diagnosis of the house leak** — see verdict |
| 17:45–18:04 | Wide stops + scaling in raise the win rate enough to overcome the bad reward/risk | ⚠ **Raising win rate by widening the stop is the R-vs-% trap** (CLAUDE.md: judge stop-width changes in percent). A wider stop raises the win rate and the size of the rare loss together; whether the equation improves is an empirical question he doesn't answer. Our tail-management variants other than SIZE all INVERTED (sosnoff_doctrine / tail-hedging rows) |
| 20:18–20:41 | Good scalpers win 80–90%; one big loss erases many winners | ✅ Consistent with every high-win-rate short-premium result here: win rate is priced, the tail pays for it |
| 24:13–26:18 | Experienced scalper **doubles** (1+1+1 → 6 contracts) into a breakout against him, and "got paid for that risk" | ❌ **Averaging down, shown on the one chart where it worked.** Contradicts the desk's rule "stop ≤ 2% or size down; never widen" (`daily_routine.md` entry rule 4) and the loss record behind it (August: 82 losers past 2% cost $13k) |
| 26:51–28:18 | Trade the "I don't care size" until you can handle surprises; goal is to stop losing, not to get rich | ✅ **AGREES** — the size lever (exclusion, not risk-spreading, +0.29R OOS) and "stay small" are the only non-inverted tail levers we have |
| 28:23–31:11 | Strong trend day: buy for any reason (above bull bars, at bear closes, at the 20 EMA, below prior lows) | ⚠ Every one of these is an intraday trigger. **Stage A: 11,227 alerts ≈ a random later minute**; ORB9 INVERTED vs a random minute in the same name-day (−0.425pp, t −8.50). On a real trend day any entry works — which is the point: the edge, if any, is the DAY, not the trigger |
| 31:18–32:39, 33:36–34:05 | Scalping a trend day gets you out and you never get back in → **don't scalp out, buy and hold with a wide stop** ("go to Walmart") | ✅ **AGREES** with the exit ledger: the 20-EMA trail beats every tighter exit; profit-lock and "tighten when extended" cost; Qullamaggie's sell-into-burst INVERTED (−1.87pp, t −4.39) |
| 34:44–35:26 | Tight range days: most traders should not trade at all | ✅ Consistent with the positive-gamma result below: on range-type days the paying side is SELLING the move (1-day short straddle), not trading direction |
| 36:03–36:16 | If it's trending without you, buy above any bull bar closing near its high, stop below that bar, hold | ⚠ On the DAILY scale this is the breakout-at-the-extended-end problem (entry buys ~2.6 ADR above a random later entry, `entry_vs_stop_2026-09-20.md`); on a 5-minute trend day it is untested here |

## The one idea worth carrying forward: day type is the variable, and we already have a pre-open proxy for it

Brooks's whole method hangs on one call — **is today a trend day or a range day?** — made from bar shapes, in
hindsight on every chart shown. Our ledger has a *pre-open, mechanical* input that sorts exactly this:
**SPY net dealer gamma at the prior close.**

- Negative gamma ≈ trend / expansion days: +8.1% realised vol beyond VIX (t 7.7, `gex_regime_pin_2026-09-21.md`);
  QQQ noise-band intraday momentum on negative-gamma days +4.16 bps/session, t 2.92 — a near miss
  (`gex_noise_band_2026-09-21.md`).
- Positive gamma ≈ range days: the SPY 1-day short straddle pays +13.7% of credit, t 5.6; the 2× fly +5.8%, t 3.4.

That is Brooks's "stops win in trends, limits win in ranges" with the day label known **before** the open instead of
after the close. Today (2026-09-24) SPY gamma was negative (−$7.8bn per 1%) — by his framework, a day to trade with
stops in the trend's direction or not at all, and not to fade.

## Not tested, could be (spec only — not queued)

**Brooks day-type × order type, gamma-labelled.** SPY (and QQQ) 1-minute bars 2018→, sessions labelled by the prior
close's net GEX sign. Arm S (stop-entry trend follow): enter on the first 5-minute bar that closes in its top 20% and
takes out the prior bar's high after 10:00, stop below that bar, exit at the close. Arm L (limit fade): buy the close
of the first 5-minute bar closing in its bottom 20% in the lower third of the day's range so far, scalp target = 1×
the 5-minute ATR, stop 2× ATR, no scaling. Pre-registered prediction from his framework: S beats L on negative-gamma
days and L beats S on positive-gamma days — a **difference-in-differences**, controls = the same arm on the other
gamma sign and a random-minute entry (the Stage A / ORB9 control). Costs: 1 tick + commissions per side. Charge the
2 arms × 2 regimes. ⚠ Prior is weak: our intraday triggers have not beaten a random minute, and the noise-band
momentum near-miss is the only intraday result with a positive sign — this test would mostly ask whether Brooks's
bar-shape entries add anything to it. **No scaling-in arm** — averaging down is not a candidate for this desk.

## What to take from it

1. **The advice aimed at you is the part he gets right:** don't scalp; swing trade in the trend direction, enter on
   a stop, hold with a structural stop, and stop exiting because a trade feels extended. That is what the exit and
   same-day round-trip data already say.
2. **Ignore the scaling-in / doubling method.** It is the averaging-down tail described from its winning side.
3. **"Trend day or range day?" is the real question, and the gamma sign is a mechanical, pre-open answer** that the
   ledger has already partly validated.
