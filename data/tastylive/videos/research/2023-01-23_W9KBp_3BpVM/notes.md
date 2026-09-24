# tastylive / Market Measures: "We Studied 17 Years of Rolling Trades... Here's What We Learned" (2023-01-23, 10 min)

_Reviewed 2026-09-23. Tom Sosnoff and Tony Battista in person, reading a research-desk slide deck. Transcript
(`en-orig` auto-captions) is in this folder. The captions garble a few words: "rolled to Australia" is "rolled to a
straddle" and "average pre-number" is "average P&L number". Numbers are read aloud; the slide table isn't visible._

## Verdict: 2.5 / 5

This is the one video in the batch where **Sosnoff himself** presents data, and the design is better than the genre
usually manages. All three arms run on the **same set of breached trades**, and the action is taken at the breach,
which is a decision-time event. So it isn't outcome-conditioned the way most "managed vs held" comparisons are.

It loses points on four things:
- only three numbers are read out;
- there's no n, no t-stat and no cost model. Sosnoff says outright that he "didn't want to get into a complete
  discussion on statistical significance";
- the roll arm adds a second short-premium sale, so its higher win rate is partly mechanical;
- **it measures a different roll from the one his doctrine forbids.** Rolling the *untested* side *in* isn't
  "rolling a loser out and wider".

## Data audit

| item | what the video gives |
|---|---|
| Underlying | SPY only. Sosnoff notes they do this "in every underlying", most with richer vol |
| Period | "since 2005, 17 years" (to ~end 2022) |
| Structure | 16Δ short strangle, 45 DTE, **held to expiry** (no 50% take, no 21-DTE close) |
| Sample | **only strangles where SPY breached the put or the call strike**; "roughly a third of all 16 Delta strangles saw at least one breach". **n not stated.** Entry cadence not stated (daily vs one per cycle) |
| Arms | (1) exit at the breach ("a stop order"); (2) hold to expiry, no action; (3) roll the untested side to the strike of the tested side (**make a straddle**) and hold to expiry |
| Fills / costs | Not stated. tastylive backtests are conventionally at mid with no commissions. Arm 3 has an extra round trip that a mid backtest doesn't charge for |
| Compared to | the other two arms. The within-trade pairing is the right control for the question |
| Win vs mean vs tail | win rate + average P&L per arm. **No worst trade, no distribution** |
| Significance | none. "I didn't want to get into a complete discussion on statistical significance" (07:58–08:09) |
| Selection | breach subset only. Fair for a management question, but "roughly a third" means the other two-thirds (the winners) are out of frame, so this says nothing about whether the strangle itself pays |

## Their numbers (as spoken)

| @ | number |
|---|---|
| 00:57–01:10 | Sosnoff that morning: 41 trades, 29 of them rolling up puts on existing positions "to adjust my deltas" |
| 01:35–01:42 | His prior: "the advantage is marginal but it can reduce your outlier risk dramatically" |
| 06:04–06:13 | Exit at breach (stop): **win rate 32%**, average P&L a loss (value not read out) |
| 07:06–07:13 | Hold to expiry: **58% success, $55 average loss** ("your 58 chance success with the 55 loss") |
| 07:22–07:31 | Roll the untested side to a straddle: **average P&L −$5, win rate 65%**, "doubled the win rate from using stop orders" |
| 08:41–08:45 | ~1/3 of all 16Δ strangles see at least one breach within the 45-day cycle |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 01:52–02:26 | Rolling the untested side = closing it and selling a strike nearer the money, i.e. **selling a vertical** in the direction of the move | ✅ Mechanically right. Note what it means for the arms: arm 3 is arm 2 **plus a new short credit spread** opened after the move. It's a second trade, not a repair |
| 02:32–02:53 | You "always collect a credit" and lower net delta; the goal is to "take about half the risk off" | ✅ Delta arithmetic is right. ⚠ "Risk off" here means delta. Gamma and vega go **up** when you move a short strike closer to spot |
| 06:04–06:53 | Exiting at the breach (a stop) is "the absolute worst way", 32% win | ✅ **Agrees with the whole exit ledger.** Our straddle −50% stop costs −3.84pp (−9.51pp on the breach cohort, 69.8% better held). Profit-locks, BE stops, trims and "extended → tighten" all lose. Every loser-removing exit rule we've tested is negative. ⚠ But their stop is "exit at the breach", which crosses the spread at the worst moment. At mid (their likely pricing) it's *understated* |
| 07:06–07:13 | Hold: 58% win, −$55 average on breached trades | **Plausible, not comparable.** Our nearest number is unconditional, not the breach subset. SPY 45-DTE 20Δ strangle held to expiry at real fills, corrected for the settlement bug found in this batch (the 21-DTE study drops both-legs-worthless expiries; see `2025-07-25_NhgIYLeCA3U/notes.md`): **+$1.13/share, median +$3.72, 75% win, n 402**, worst −$82.88 on a $3.71 credit (2020-02-07). Their breached third losing ~$55/lot (~$0.55/share) on average fits a profitable-overall strangle whose losses sit in the breached subset |
| 07:22–07:31 | Roll to a straddle: −$5 average, 65% win. **Best of the three** | **Untested here, and the direction isn't obvious.** (a) Win rate rises mechanically: the added credit moves both break-evens, and "win rate ≠ edge" is our most-replicated finding (premium-to-width: net ROC rises −2.96 → +4.07 while win *falls* 79.6 → 75.7). (b) The −$55 → −$5 improvement is a **mean** claim with no n and no t. With ~1/3 of ~17 years of SPY cycles it could be a few dozen independent trades. (c) At real fills the roll pays a fresh spread crossing on two legs. That's cheap on SPY and expensive on single names (our measured straddle-entry spread across the single-name universe is a median 6.5% of mid). For a ~$50 gap on SPY it's small, so this one **could survive costs**. Worth a test |
| 07:38–07:54 | "This isn't exactly what I do. We roll early… when we get towards the straddle we buy back the guts and sell the wings… re-center" | ⚠ **Their real process isn't the one tested.** His actual adjustment (roll before the breach, then re-center) is more active than the study arm. Our only re-centering evidence is on the **long** straddle: re-center / flat-take **REJECTED**, and "roll at −50%" is a stop plus a fresh entry, NULL (`project_straddle_recenter_study`). Different sign of gamma, so it doesn't transfer |
| 08:17–08:27 | "Doing something is better than doing nothing… nothing from our research has ever shown anything different" | ❌ **Too broad, and our ledger contradicts it for most "somethings".** Every P&L-conditioned exit we've tested is negative. The only management rule on file as certified is the **21-DTE time exit** (+$1.53/strangle, t 4.26), which removes gamma symmetrically at a fixed date. ⚠ It needs a re-run: its sample drops the both-worthless winners, which biases it toward the early exit (see the settlement caveat in `2025-07-25_NhgIYLeCA3U/notes.md`). It doesn't react to the loser. On our data, "do something" helps only when the something isn't conditioned on P&L |
| 08:52–09:06 | Rolling reduces delta, raises the net credit and the chance to break even, at the cost of max profit | ✅ Correctly framed as a **risk trade-off**, not an edge claim. That's the honest reading of their own numbers too |
| 09:36–09:53 | "You're getting rid of a lot of outlier risk" | **Half right.** Delta falls, but the straddle you end up in has *more* short gamma at the money. Their table doesn't show the worst trade per arm, which is the number that would settle it |

### The question Gabe asked: does this support or undercut "don't roll losers wider"?

**Neither. It tests a different roll.**

- **Sosnoff's "don't roll out and wider"** (More Tom `qo9466KD_u8`, our ledger §5) is about a *defined-risk* loser: pushing the
  tested spread to a later expiry and widening the strikes, which multiplies max loss ("a $3 spread became a $9 spread").
- **This study rolls the untested side IN**, same expiry, and keeps the tested side where it is. It adds a short
  vertical against the move. It doesn't extend duration or widen the tested side.

So it's consistent with his doctrine rather than evidence for it: tastylive's playbook is "roll the untested side in,
don't push the tested side out". ⚠ **Our own "don't roll wider" support is weaker than §5 of
`data/more_tom/claims_strategy.md` makes it look.** That support comes from the **long 7-DTE straddle** stop-and-re-enter
test (a long-gamma position, stop half −3.84pp, re-entry NULL t 1.55). It's a different structure and a different sign
of gamma. **We have never tested any roll on a short strangle or a short put spread.** The "sell the call spread
above a losing put spread" test (claims_strategy.md "Worth queueing" #1) is the closest queued item. This video's arm 3 is
the same idea on a strangle.

## What I would take

1. **The pairing design.** Same trades, action at a decision-time event, three arms. That's the right way to test a
   management rule, and it's how our 21-DTE test was built.
2. **"Stops at the breach are the worst option"** is a fourth independent statement of our exit-ledger finding.
3. **Nothing to adopt yet.** The roll arm's gain is a mean with no n or t, likely at mid, and its win-rate gain is partly
   mechanical.

## Not tested, could be

**Roll-the-untested-side on the breached subset, at real fills** (codable from `silver.options_daily_v3` EOD):
- **Universe:** SPY first (`data/cache/SPY_puts_v3_2018_2026.parquet` covers puts only, so pull calls from v3 for
  2018–2026), then the liquid ETF subset of the 21-DTE panel.
- **Entry:** every Friday, 45 DTE, 16Δ put + 16Δ call, sell the bid.
- **Breach:** first EOD close beyond a short strike.
- **Arms:** at that close, (A) hold to expiry; (B) buy the whole strangle back at the ask; (C) buy the untested leg at the
  ask and sell the same-expiry option at the tested strike at the bid, then hold; (D, Sosnoff's real process) C but
  triggered at a 30Δ tested leg rather than the breach.
- **Settle at intrinsic from the chain-recovered spot** (`chain_spot.py`), **not** from the expiry-day option print (see the
  settlement caveat).
- **Primary:** C − A paired, month-clustered t ≥ 3, both halves the same sign. Report the worst trade and CVaR per arm,
  since the claim is about the tail.
- **Effort:** ~½ day on the 21-DTE harness plus a v3 call pull (~2 h Athena, local).
- **Prior:** C − A small positive at mid; after costs roughly zero. The yield would be a MECHANISM on "roll = second trade".
