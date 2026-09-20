# 0DTE only into expansion events

> **Verdict:** Correct on the base rate, correct on frequency, and pointed at the wrong
> instrument. His gate (a *forward* catalyst) is genuinely untested here — but the repo's own
> event-convexity result says buy that convexity with **five days** of runway, not five hours,
> and the 153k-trade 1-DTE study says the bid/ask, which he never mentions, is the entire P&L.
> **Type:** setup + universe gate (options)
> **Conviction:** 2/5 · **Testability:** partly EOD ⭐ (the exhaustion-gap arm), intraday-needed for the rest · **Tested?** partial — the *adjacent* trade is tested and negative; **his exact gate is not**
> **Source:** `U9UZ2U6bozQ`@[04:33]–[08:31] — "Watch Before Trading 0DTE Options" (2026-04-04)

---

## 1. Mechanics

- **Instrument / universe:** 0DTE options — index (his SPX worked example) or single names with
  same-day expiries. He does not restrict the universe by liquidity or by spread at any point.
- **Session / timeframe:** same session, entry any time, forced exit at 16:00.
- **Setup condition — the gate.** Only into a **volatility *expansion* event**, i.e. a move that
  has not happened yet and is about to. Three named arms [06:56]–[07:17]:
  1. "Exceptional breakout setups in a strong momentum market"
  2. "Breaking news headlines that haven't yet been priced into the market"
  3. "Exhaustion gap daily patterns"
- **Trigger:** "ahead of major daily breakouts or right during breaking news events" [04:33]. He
  requires the entry to be *early in* the expansion, not after it: "if you buy options after
  volatility is already exploded, and then the move stalls, implied vol can collapse just as
  quickly" [06:33].
- **Entry — relative to what reference:** ⚠ **Not specified.** "Before or right as that breakout
  started" [05:24] is the whole of it. This is the discretionary joint.
- **Stop:** none in the options sense — risk is capped at the premium [09:02]. But there is a
  stated **invalidation**, which is the mechanical part [08:10]:
  > "If the breakout fails and reclaims the prior range, you need to be out. If the news-driven
  > move stalls and momentum fades, you're also out."
- **Implied position size:** not given as a rule, only as a veto — "if you're allocating a large
  portion of your account to one short-dated idea, you are not thinking like a professional. It's
  just gambling at that point" [07:56]. He expects **50/70/90% drawdowns in minutes** as normal
  [07:47], which is the sizing input.
- **Exit:** the invalidation above, or expiry.
- **Vetoes / conditions:** ⭐ a **frequency cap** — "I'm only using zero DTE options as a tool a
  few times per year" [07:02]; and a regime veto — "there will be entire weeks where conditions do
  not justify this kind of leverage. Low volume, no catalysts, no panic" [08:31].

**Is it precise enough to test?** Arm 3 alone. "Exhaustion gap daily patterns" is already
mechanized in this repo twice (the gap study's ≥1 ATR prior move; the capitulation definition of
bar range ≥2× prior *and* volume ≥2× prior). Arms 1 and 2 need a catalyst tag and an intraday
option quote we do not have. **Two of the three arms are untestable as stated; one is testable
today.**

## 2. ⚠ The sizing-lever question

Not applicable in the usual form — there is no stop distance, because a long option's
invalidation is the premium. What *is* relevant to the open question:

- **Stop distance as % of entry:** n/a. Max loss = 100% of premium by construction.
- **Position at a 0.3% risk budget:** trivially 0.3% of the account in premium, if you treat total
  loss as the risk. He implicitly agrees (the "large portion of your account" veto).
- **Does he state a stop-out rate?** No. Our panel gives it: on the 1-DTE ATM straddle, the
  **open win rate is 5%** and p10 is −56% of premium. Whatever the equivalent of a stop-out is
  here, it is most trades.
- **What would settle it:** intraday option quotes on catalyst days (the IBKR minute bid/ask pull,
  currently ⏸ paused at 4 GOOG expiries) plus a catalyst tag with better than the current
  241/1,743-name earnings coverage.

## 3. Claimed edge & evidence

**None.** There is no number in the video that is a result — no win rate, no P&L, no trade count,
no base rate, no example trade. The only quantity about his own behaviour is "a few times per
year" [07:02], and the only quantity about outcomes is the *negative* one, "50, 70%, or even 90%
drawdown in minutes" [07:47]. The SPX 5,000/$50 example is a hypothetical theta illustration.

⚠ **The claim doubles as course marketing.** [09:24]–[09:43]: "If you want to learn exactly how I
identify high-probability expansion events, how I filter for the real breakouts versus the fake
ones, and how I start to assess whether these zero DTEs are expensive or cheap, I go deep on that
inside my trading course." The three things withheld are precisely the three things that would
make the rule testable — the selection filter, the false-breakout filter, and the cheap/expensive
assessment. **The mechanism is behind the paywall by construction.**

## 4. ⚠ Prop-infrastructure dependency

- **Depends on:** speed, mostly. "Timing and being fast still matters" [06:33] — entering *before
  or as* the vol expansion rather than after is a latency requirement, and a retail click on a
  headline is on the wrong side of it. Nothing else here needs locates, borrow or firm routing.
- **Retail-viable as stated?** **Partly.** The instrument is retail-accessible and the risk is
  defined. The *timing* requirement is not obviously retail-achievable, and the spread cost (which
  he omits) falls hardest on the retail-accessible single-name expiries.

## 5. Decay risk

**Moderate-to-high, and running the wrong way for him.** 0DTE volume has exploded since 2022 and
the instrument is far more heavily traded than when his intuitions formed on Wall Street. Our own
panel shows the trade getting *worse* over time: the 2026 partial year is the worst in the sample
on every arm (ungated close exit −45.7%, open @fair value −50.5%, even the hindsight extreme arm
−15.8%). Whatever premium was once there is being competed away, not opening up.

## 6. Objective assessment

- **The "paid two ways" argument is wrong at 0DTE.** [05:18]: "you can get paid two ways. First,
  from the stock moving in your direction and second, from the expansion in implied volatility."
  Vega on a same-day option is near zero; the payoff is gamma/delta almost entirely. This is a
  30-DTE argument imported without adjustment, and it is the technical error in the video.
- **The gate is stated but not operationalized.** "Clean technical breakouts with some urgency"
  [06:11] is not a rule. "The real breakouts versus the fake ones" is explicitly deferred to the
  course.
- **⚠⚠ The spread is never mentioned.** On the most spread-sensitive instrument in the market, in
  a video with three minutes on theta and two on IV. See §8.
- **Zero examples.** Unlike the TIGR trade in `eWeGAYvjxh4`, not one actual 0DTE trade of his is
  shown, winning or losing.

## 7. What's genuinely sound

- **The base rate is stated correctly and up front**, which is rare. "Used too frequently, and
  they will drain your account faster than you can refresh your P&L" [00:20]; "I have had hundreds
  of these expire worthless on me" [00:54].
- **The frequency cap is the actual content.** "A few times per year" plus "entire weeks where
  conditions do not justify" is a stronger statement of selectivity than almost anything in the
  options-education space, and it is the part that makes the rest defensible: a negative-EV
  instrument used four times a year on your highest-conviction expansion setups is a rounding
  error on the book; used weekly it is the account.
- **The invalidation is pre-stated** [08:10] — the reclaim of the prior range, the stalling of the
  news move. That is the shape our grading rubric demands.
- **The failure mode he names is the right one** [05:39]: right on direction, not fast or far
  enough, theta and vol-down cancel the delta. That is the modal losing 0DTE trade and most
  content does not name it.

## 8. Overlap / conflict with the rest of the repo

### ✅ The base rate — he is right, and we have it to 3 decimals

`data/studies/one_day_straddle_study.md` (2026-09-19; 152,995 trades, 1,645 names, 2019-01-03 to
2026-02-19, real bid/ask from `silver.options_daily_v3`, exits settled off the underlying, costs =
IBKR $0.65/contract + 25% of the bid/ask per traded side). Buying the ATM straddle at the close
before expiry:

| exit | all 152,995 | gated ratio_max ≥3 |
|---|---|---|
| settle at the close | **−30.3%** (t −26.9) | −23.0% |
| sell both legs at the open @fair value | **−30.2%** (t −37.4) | −25.4% |
| sell the winner at the day's extreme (hindsight) | +9.6% | +22.8% |

Every year 2019–2026 is negative; 2020 and 2022 are −24% and −27%. The 0DTE long strangle base
rate is **−26%/trade** (Theta Profits KB). The study's own read: *"this is the 0DTE
long-strangle base rate in a different costume, not a new trade."* **His "not a shortcut to easy
money" is the correct sign from a practitioner with no data.**

### ⚠⚠ The bid/ask is the whole P&L, and it is the one thing he never mentions

Study §4, same trade, same exits, split only by liquidity:

| both legs' bid/ask as % of straddle mid | n | open @fair value | close exit |
|---|---|---|---|
| <5% | 10,768 | **−1.7%** | −6.8% |
| 5–10% | 20,084 | −8.9% | −12.3% |
| 10–20% | 37,224 | −16.1% | −17.5% |
| >20% | 84,919 | **−45.0%** | −43.1% |

A 43-point swing from nothing but the spread. The short side is identical in structure: selling
the same straddle is **+1.1% of premium net in the tightest decile and −89.5% in the widest**
(`data/studies/one_day_straddle/logs/short_side_2026-09-19.log`). **Liquidity, not the setup, is
the first-order variable in this instrument** — the same conclusion the short-dated single-name
selling study reached independently (10 DTE net negative; costs 136% of gross; tradeable set =
SPY + ~4 mega-caps). Any version of his rule that survives must carry a spread gate, and his does
not have one.

### ⚠⚠ 0DTE forces the trade into the one bucket measured negative twice

A 0DTE position is a **same-day round trip** by construction. The **exit-timing study**
(2026-09-18) found same-day exits are the negative bucket in both books — our pool: scalp −0.13R
vs trail +0.89R; Gabe's own: 278 same-day cycles, −$8.3k, 19% win, alert-triggered ones no better.
**Stage A** (2026-09-18) fired 11,227 intraday triggers of exactly the families in his arms 1 and
3 (unfilled-gap reclaim, ORB above the 9 EMA, level breaks): every arm −0.10 to −0.13R, and a
**random** entry in the same name-day beat the trigger on every arm. The **entry study**
(2026-09-17) found buying the **daily close** beats every intraday entry (paired −0.9 to −2.3pp,
t up to −3.4).

**Two known negatives compounded:** an intraday trigger family with no measured edge, expressed
through the most decay- and spread-hostile instrument available.

### ⭐ The one place the repo argues FOR him — and it argues for a longer tenor

The catalyst/convexity study (2026-09-18) is the repo's strongest pro-convexity result:
**OTM calls bought before events beat random-date buys on every exit** — 0.12Δ, sell after 5
sessions: **+30.7% vs −3.6%**; election-eve median **+59%**. That is his thesis (buy convexity
into an expansion event) **confirmed at a 5-session horizon and sized as a lottery ticket**. The
repo's guidance from that study is "sell within 5 sessions," which is 5 *days*, not 5 *hours*.
⚠ In the same study, **earnings *proximity* was RETRACTED** (−0.06R vs +0.73 control) — the
apparent edge was bucket mix.

**Synthesis:** his gate is probably pointing at something real, and the instrument he chose to
express it discards the runway that makes it work. The 0DTE version has no time for the thesis to
be right slowly, which is exactly the failure mode he himself names at [05:39].

### ✅ Exhaustion gaps — third statement of the same pattern

Arm 3 is ORB use case 1 ([`opening-range-break.md`](opening-range-break.md)) and the gap study's
only strong positive condition (day after a ≥1 ATR move: **+11.91 bp, t=6.53** vs +0.84
otherwise). ⚠ And note he wants to be **long** premium into the exhaustion gap here while in
`eWeGAYvjxh4`@[08:28] he **sells** the calls into one (TIGR). The reconciliation is his own rule 1
from that video — long *before* the expansion, short *after* it — but he never states it, and
getting that ordering wrong is the difference between the two signs.

### Testable extraction, ranked

1. ⭐ **Catalyst-gated long 1-DTE/0DTE straddle or OTM call, liquid names only.** The panel is
   already built; the missing input is a catalyst tag. Hurdle: beat −7 to −8% net (the best cell
   in the study: bid/ask <10% AND ratio_max ≥2). Note the earnings tag covers only 241/1,743 names.
2. **Exhaustion-gap arm on daily bars** — the ≥1 ATR / 2× range / 2× volume definition against
   the same panel. Fully testable now.
3. **ΔIV's share of 0DTE P&L variance** — settles the "paid two ways" claim in one query.
4. ⛔ Arms 1 and 2 as stated: **do not fund intraday data for these.** Stage A already said so.
