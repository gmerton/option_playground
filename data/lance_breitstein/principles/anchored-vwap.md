# Anchored VWAP — as trend context, not as a level

> **Verdict:** Coherent mechanism and unusually honest presentation, but it is a *context* tool by
> his own explicit statement — not the entry-location technique this KB was opened to find. One
> genuinely testable rule falls out of it: catalyst-anchored AVWAP as a trailing exit.
> **Type:** regime / trend-context (NOT entry-location, NOT sizing)
> **Conviction:** 2/5 · **Testability:** EOD-testable (the exit rule) · **Tested?** no
> **Source:** `D2P-0xh6aEM`@05:44, @06:06, @07:39 — "The Anchored VWAP Edge Most Traders Never
> Discover" (published 2025-07-15). Raw notes: [`notes/anchored-vwap-video.md`](../notes/anchored-vwap-video.md)

---

## 1. Mechanics

- **Instrument / universe:** any; he applies it to post-catalyst names on intraday and swing
  horizons alike.
- **The tool:** VWAP with a chosen start point instead of a daily reset. From the anchor forward
  it reports the volume-weighted average price paid since that moment.
- **Anchor selection:** high-volume catalyst events only — earnings, major headlines,
  capitulation days, key breakout days, IPO day, episodic pivots. He explicitly **rejects
  time-based anchors** for his timeframes.
- **Usage — stated negatively and unambiguously:**
  > "I personally don't use anchored VWAP or VWAP as a literal level… I am not buying or selling
  > simply because we get above or below that line. Instead, I am more so viewing it as an
  > indicator of trend."
- **The one hard rule:** don't short above (A)VWAP unless the name has capitulated; don't long
  below it unless it has capitulated. A **directional veto**, not a trigger.
- **Swing application (his UNH example):** anchor to the catalyst day, hold the long while price
  holds above the anchored line, treat a break as the exit.
- **Discretionary joint:** "capitulated" is never defined. That is the unfalsifiable hinge of
  the whole rule.

## 2. ⚠ The sizing-lever question

**Not addressed, and the video actively argues the other way.** This KB's priority queue put
this video first on the hypothesis that AVWAP was his precise entry-location reference — the
candidate mechanism behind the ~6× sizing lever in
[`HOW_THEY_DO_IT.md`](../../carter_mastering_the_trade/backtests/risk_architecture/HOW_THEY_DO_IT.md).
He explicitly refuses to use it as a level, so:

- **Stop distance implied:** none — no stop is derived from AVWAP.
- **Position size implied:** none.
- **Bearing on the 91%-stop-out-at-1.5% problem:** none.
- **What would settle the open question:** still 1-minute bars, or a video where he specifies
  entry trigger and invalidation to the tick. **Hypothesis not supported; re-queue elsewhere.**

## 3. Claimed edge & evidence

No performance claim is attached to AVWAP itself. He is reviewing **Brian Shannon's** tool and
grading it ("this indicator passes the BS test"), not selling it as his edge. Evidence offered is
two chart anecdotes:

- **CRCL** post-IPO — held above AVWAP from ~$110 to ~$300; the rule kept him from shorting into
  it. Capitulation on 2025-06-23 then permitted shorts.
- **UNH** — anchored to the 2025-05-15 fraud-investigation headline; held above since, offered as
  a swing-long structure not yet stopped out.

⚠ Both are **winners shown after the fact**, the standard red flag. No losing example is carried
through. Opening credential claim — "8-figure P&L per year, over $100 million in verified
profits" — is asserted, not evidenced here.

## 4. ⚠ Prop-infrastructure dependency

**None.** AVWAP is available in ThinkorSwim, TradingView, TrendSpider, Sierra Chart. This is one
of the few things in his corpus with no infrastructure barrier — fully retail-viable as stated.

## 5. Decay risk

**Low, unusually.** The mechanism is not an exploitable inefficiency that gets arbitraged away —
it is a positioning/cost-basis statistic, and the reflexive behaviour it describes (holders
underwater behave differently) is structural. The institutional-benchmark argument for *standard*
VWAP is stronger than for anchored VWAP, which no algo is benchmarked to. Published 2025-07, so
no staleness yet.

## 6. Objective assessment

- **The null hypothesis is strong and he doesn't address it.** AVWAP is a volume-weighted moving
  average with a hand-picked start. "Holding above AVWAP" is close to "still trending since the
  catalyst," which a plain moving average also tells you. **Nothing in the video establishes that
  the volume weighting or the anchor adds information over a fixed-lookback trend filter** — and
  that is precisely the comparison the repo can already run.
- **The anchor choice is discretionary**, so in its general form the rule is unfalsifiable. It
  becomes testable the moment the anchor is defined mechanically (e.g. highest-volume session of
  the trailing 60 days).
- **"Capitulated" is undefined** and carries the entire veto rule.
- **Credit where due:** he is grading someone else's tool, states its limits, says "there is no
  one right way," and closes by telling viewers to test it themselves or backtest simple rules.
  That is the opposite of the pattern in the Carter and Theta Profits KBs, and it should raise
  the prior on his other material being honestly presented.

## 7. What's genuinely sound

The reframe is the valuable part: **an indicator as a read on holder positioning rather than as
a line to trade off.** "People who are underwater behave differently" is a real mechanism with a
named counterparty, which is the test this repo applies to separate live edges from dead setups.

And one rule survives extraction in fully mechanical form:

> **Anchor to the highest-volume session of the trailing N days; remain long while price closes
> above the anchored VWAP; exit on the first close below it.**

## 8. Overlap / conflict with the rest of the repo

- **⭐ Directly testable against work already done.** `risk_architecture/` measured six exits
  across 320 configurations and found the *slow* trail `close<50EMA` best, with fast trails
  (`close<10EMA`) negative in all ten stop rows. Catalyst-anchored AVWAP is a slow trail with a
  smarter anchor — so it slots straight into that harness as a seventh exit rule, on data already
  on disk. **This is the cheapest open test in the repo.**
- **Conflicts with [[martin_luk]] on usage.** Luk cites AVWAP for *stop placement* — i.e. as a
  level. Breitstein explicitly refuses to use it as a level. Same tool, opposite application.
  Do not merge; the disagreement is itself informative about which use is load-bearing.
- **Supports the regime findings.** The veto ("don't fight the side of the line the crowd is
  on") is the single-name analogue of the market-regime gate that produced the largest
  improvement in the whole study ([`REGIME.md`](../../carter_mastering_the_trade/backtests/risk_architecture/REGIME.md)).
