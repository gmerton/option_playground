# Qullamaggie's complete stated system — as relayed by Breitstein

> **Verdict:** ⭐ The single most valuable document ingested. Contains Kristjan Qullamaggie's
> entry, stop, partial-exit, trail and market-filter rules **in his own quoted words** — and
> three of them contradict or reframe results already produced in `risk_architecture/`.
> **Type:** setup + execution + regime (complete system)
> **Conviction:** 3/5 as an accurate *record* of his method · **0/5 as validated edge — untested here**
> **Testability:** mostly EOD-testable ⭐ · **Tested?** no
> **Source:** `H01JbbEY7ac` — "Reacting to Kristjan Qullamaggie's Moving Average Trading Strategy"
> (2025-11-05). Quotes are Qullamaggie's, played as clips inside Breitstein's video.

⚠ **Second-hand.** These are clips Breitstein selected and captioned, transcribed by auto-captions.
Treat as a high-quality lead, not a primary source. Where it matters, verify against Qullamaggie's
own streams before trusting a specific number.

---

## 1. The rules, verbatim

### Entry + stop (his words)

> "You **buy the opening range highs of a breakout**, or at least as soon as you possibly can once
> you identify a good setup and a good breakout. Then you use the **lows of that breakout day as
> your stop**." (11:04)

### Partial exit + trail (his words, same clip)

> "After **three to five days** — you can choose yourself, day three, four or five — you **sell a
> third to half**, **move your stop to break even**, and then you start **trailing with a 10-day
> moving average**, and once you get the **first close below the 10-day**, you sell it." (11:15)

Refinement he adds elsewhere: **10-day for fast movers, 20-day for slow movers.**

> "I'm going to trail NIO with the 10-day moving average since it's a fast-moving stock. The faster
> moving names, I'm trailing with a faster moving average." (11:38)

And the exit is **on the close only**, never intraday:

> "Look at how nicely NVIDIA has been surfing the 20-day this whole move… this thing hasn't closed
> below the 20-day since March 23. It's been **undercutting** the 20-day a couple of times, right?
> But it's **never closed** below it… They don't close below the 10 and 20 day for a long, long
> period." (12:37)

### Market filter (his words)

> "An easy market filter is just use the **10 and the 20-day**. If the 10-day is above the 20-day
> and they **both are trending higher**, that's a very good market. If the 10-day gets below the
> 20-day, you should be a bit cautious. If the 10-day starts sloping down, more cautious. If the
> 10-day slopes down, the 20-day slopes down, and the 10-day is below the 20-day, you should
> **probably not buy any breakouts at all**." (05:42)

### Setup shape (his words)

Stair-step: "step higher, sideways, step higher, sideways… your job is to buy at the exact moment
when the next step higher is forming." Looks for higher lows "getting tighter and tighter," names
"surfing the 10/20-day," moving averages acting as support in uptrends and resistance in
downtrends. Add on each subsequent step.

### On why it works

> "I don't know why. It just does… Maybe it's magic. I don't really care. They worked really well
> a hundred years ago and they still work really well." (02:41)

---

## 2. ⚠ Three direct collisions with results already in this repo

### (a) His entry is INTRADAY. Mine was not. This is the open question, answered.

`HOW_THEY_DO_IT.md` concluded the whole gap likely rests on whether intraday entry location
decouples stop *tightness* from stop *fragility*, and that daily bars can't test it. **Here is the
mechanism, stated explicitly:**

- He enters at the **opening-range high on the breakout day**.
- His stop is the **low of that same day** — a level already established by the time he enters.

Every simulation in `risk_architecture/` entered at the **next day's open** with the stop at the
**prior** bar's low. That is a materially different and much looser structure. The `bar low` stop
I tested was therefore **not** his rule, which is very likely why it came out indistinguishable
from an arbitrary stop of the same width.

**This is the highest-value testable difference found so far**, and it needs intraday data to
settle — but the *specification* is no longer vague. It is: enter at ORB high, stop at day's low.

### (b) His exit is a partial-then-trail. I only ever tested full exits.

I tested `close<10EMA` as a **complete** exit and found it **negative in all ten stop rows** — the
most consistently bad exit in the study. That is **not his rule.** His sequence is:

1. Days 3–5: **sell a third to a half** into strength.
2. **Move the stop to breakeven** on the remainder.
3. *Then* trail the rest with the 10-day, exiting on the first close below.

By the time the fast trail is active, the trade is de-risked and partially banked. My test applied
a fast trail to a full position from day one with the original stop still in place. **The
comparison was never fair, and my "fast trails are the reliable way to lose" conclusion does not
apply to his rule as stated.** This is EOD-testable right now and should be.

### (c) His market filter is 10/20-day, not 200-day.

`REGIME.md` tested SPY > 200SMA (and rising) and found it the single most valuable variable in the
study. **His filter is far faster** — 10-day vs 20-day, both slope and cross, on a four-level
caution scale. Directly comparable, cheap to add, and it may capture chop the 200-day misses.
Note his rule is graduated (caution → don't buy at all), not binary.

---

## 3. What Breitstein adds, and where he differs

- **He exits immediately on the MA break; Qullamaggie waits for the close.** Breitstein's reason:
  he trades a shorter/intraday timeframe where he "can afford to be more nimble," whereas
  Qullamaggie is harvesting asymmetric multi-week trends where looseness pays. A clean statement
  of why the same indicator needs a different rule per horizon.
- **Both use very few indicators.** Qullamaggie: 10/20/50 SMA (occasionally 200). Breitstein: 20
  SMA and 200 SMA only, the 20 arriving via his Bollinger Bands.
- **Neither uses moving-average crossovers.** Qullamaggie: "I don't really look at moving average
  crosses ever." Breitstein: doesn't either, but concedes the logic (a rate-of-change signal) and
  says he hasn't backtested it.
- **Breitstein's mechanism story**, which Qullamaggie declines to give: price alternates between
  expansion (trend) and equilibrium (consolidation); an MA measures equilibrium, so breaking it
  signals the prior rate of change has stopped.
- **Self-fulfilling-prophecy argument for default parameters:** "if 90% of traders are using a 20
  SMA, then I want to know where 90% of traders are looking for support."

## 4. ⚠ Parameter insensitivity — an admission worth more than it looks

> "There is one comical stream where Christian accidentally set up his charting platform wrong and
> was using the wrong moving average. **It made minimal difference to his trading.**" (07:25)

If the specific MA is nearly irrelevant, the edge is not in the parameter — it is in the setup
selection and the exit discipline wrapped around it. **This independently corroborates the repo's
own finding** that the Squeeze's Keltner-multiplier sensitivity was flat from 1.0–2.5 (all
negative), i.e. results were not a calibration artifact, and the broader pattern that indicator
parameters are not where edge lives. It also argues against spending any effort optimizing MA
lengths.

## 5. Red flags

- **Winners only.** Every chart shown (PLUG, NVDA, NIO, AMD, PLTR, SMCI) is a worked example after
  the fact. No losing trade is carried through, in either trader's clips.
- **Course plug** twice, plus repeated subscribe asks.
- **The credibility argument is by association** — Swedish tax records, Market Wizards profile,
  "I was profiled alongside him." That establishes he made money; it establishes nothing about
  which rule made it.
- **"It's magic, I don't care why"** is honest but is exactly the epistemic stance this repo
  exists to resist. A rule with no mechanism is the profile of the Carter setups that died.
- ⚠ Breitstein credits **James Munan** with compiling the Qullamaggie clips — so this is
  third-hand in places, not second.

## 6. Testable extractions, ranked

1. ⭐⭐ **Partial-exit-then-trail** — sell ⅓–½ on day 3–5, stop to breakeven, trail remainder on
   the 10-day (fast names) / 20-day (slow), exit on first *close* below. **Fully EOD-testable on
   data already on disk**, and it directly re-tests a conclusion I got wrong.
2. ⭐⭐ **The 10/20-day market filter** vs the 200-day gate already measured in `REGIME.md`.
3. ⭐ **Stop at the breakout day's low with same-day entry** — needs intraday bars, but is now
   precisely specified rather than vague.
4. **Add-on-each-step pyramiding** — untested anywhere in the repo.
5. **Fast-vs-slow trail keyed to the stock's own speed** (ADR/ATR) rather than a fixed rule —
   trivially testable, and my harness used one trail for all names.

## 7. Overlap with the rest of the repo

- **[[martin_luk]] is downstream of this.** Luk is explicitly "in the Qullamaggie lineage," and his
  0.3%-risk / tight-stop / EMA-pullback structure is a variant of these rules. Where Luk and this
  document agree, the claim is corroborated across two independent relays.
- **`risk_architecture/` collides with it in three places** — see §2. Two of the three are
  testable today and one of them (the partial exit) means a published conclusion of mine needs
  revisiting.
- **[[project-minervini-scan]]** implements the trend-template universe these setups assume.
