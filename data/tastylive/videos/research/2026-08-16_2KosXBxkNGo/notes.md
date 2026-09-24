# tastylive: "Julia Spina Breaks Down 20 Years of VIX Expansions" (2026-08-16, 12:58)

_Reviewed 2026-09-23 for the Sosnoff "sell vol when it's high" wave. Julia Spina presents a study by "Sahil"
(research desk) to two co-hosts. Transcript (`en-orig` auto-captions) in this folder. The per-bucket counts and
probabilities are on charts that are described, not read out._

## Verdict: 2.5 / 5

The most careful study in the batch on method:
- the event de-duplication (02:59-03:20: overlapping windows that spike to the same peak count as **one** event)
  is exactly the overlap correction most creator studies skip;
- Julia volunteers the caveats: averages only, speed not studied, black swans are the exception.

The content is descriptive VIX dynamics: mean reversion by level, volatility clustering, faster cycles at higher
VIX. None of it is a trade. The trading remarks bolted on afterwards are anecdotes: a co-host closing four
single-name strangles before VIX expiration, and "that's when we like to get into SVXY". Those are exactly the
jump the data doesn't license: from "the VIX level tends to fall from 25" to "selling vol at 25 pays".

Also internally inconsistent on the headline: the 50/50 point is "**22 to 25**" at 07:27 and "**20 to 21**"
at 09:38 and 11:37 (the description says ~20).

## Data audit

| item | what the video gives |
|---|---|
| sample | VIX daily **2005 → 2025** (02:39) |
| event | a **5-point** VIX move within a rolling window (00:53-00:57); expansion = up, contraction = down |
| windows | **7, 15 and 30-day** rolling (09:26) |
| buckets | starting VIX **10-13, 13-16, …** (07:00-07:04) |
| de-duplication | ✅ overlapping windows that hit the same peak = one event (02:59-03:20) |
| n | **not stated** (no event counts per bucket read out) |
| fills / costs | n/a, no trade |
| control | none needed for a descriptive study; none for the trading remarks |
| tail shown? | acknowledged verbally ("can go up to… 92", 08:33) |
| significance | none |
| selection | "5-point move" is an absolute threshold, so it's mechanically easier to hit at high VIX. That inflates both counts at high levels (she notes expansions and contractions both rise, 05:50-05:58) and biases "duration shrinks" |

## Their numbers (transcribed)

| @ | number |
|---|---|
| 00:24-00:32 | 2026: VIX **14 → 34** (20 pts) in **59 trading days**, contraction in **20** trading days ("inverted" vs the usual elevator-up/stairs-down) |
| 07:27 | 50/50 expansion/contraction split "around like the **22 to 25** range" (7-day) |
| 08:11 / 08:38 | from VIX **25**, contractions "much more likely"; recorded max "like **92**" |
| 09:32-09:40 / 11:37 | 50/50 at an average VIX of **20 to 21** across 7/15/30-day windows |
| 07:36-07:40 / 11:25 | average duration of expansions and contractions **shrinks** as the VIX rises |

**Check on the 2026 figure** (yfinance `^VIX`): prior low **13.38** (2025-12-24) → intraday high **35.3** (2026-03-09),
49 sessions. Closes peaked at **31.05** on 2026-03-27 and were back to ~17 in April. **Roughly consistent**; their
"59 days" likely uses a different start point. The recorded all-time VIX *close* high is 82.69 (2020-03-16); ~90 is
the 2008 intraday print.

## Claim-by-claim

| @ | claim | our evidence |
|---|---|---|
| 04:00 | vol clusters: large moves arrive together | ✅ Agrees. Post-shock test: clustering makes multi-day shorts worse (10d **−10.8pp**, t −1.8) (§2 post-shock row) |
| 07:06 / 08:11 | low VIX (10-13) → expansions dominate; VIX ≥ 25 → contractions dominate | ✅ **True of the VIX level, and priced.** Mean reversion of spot VIX is what a backwardated futures curve already discounts (see the term-structure video: 7 of 7 ≥10% drawdowns were backwardated). "VIX will fall from 25" is only worth money if it falls **faster than implied**. Our post-shock test is the operational answer: post-shock richness **is the VIX level**; nothing extra is left for a short straddle vs VIX-matched days |
| 08:58 | at high VIX, get into SVXY (short VIX futures) "in a defined-risk way" | **Vehicle untested; the bet is not.** Selling index put risk at VIX ≥ 20 after a selloff is our one certified cell (**SPY t 6.07 / SPX t 5.21**, Tier A/B row). ETF bull puts at **VIX ≥ 25: +4.5%/trade (n 1,123), +10.1% with the ETF above its 50-day**, but **2022 −3%** (`etf_put_spread_study.md` l.39-46). The nearest vol-ETP option trades died on friction: UVXY bear call −7.4% net (t −3.65), UVIX −8.8% (t −2.81) (§1) |
| 07:55-08:04 | "this chart is why I'm closing the AMD, INTC, SMH, BE strangles before VIX expiration" | Anecdote. A single-name strangle's exit keyed to *index* VIX expiration has no test and no mechanism. Per-name selling at his tenor shows no edge at real fills: 45/20Δ strangles across 44 names are ≈ flat held (+$0.23/share) and −$0.29 closed at 21 DTE (§1 21-DTE row; "negative in both arms" (corrected 2026-09-24, FIX-1: original run dropped worthless-expiry winners)) |
| 09:08-09:19 | capital preservation when VIX is low, so you have capital when premium is rich | ✅ Agrees in form: the only certified short-premium cell is the stress state; low-IV index cells are negative (QQQ bullish-low-IV −4.8%, t −0.87). Our localisation test adds that strategy "good stretches" aren't predictable except through mechanism-backed splits like this one (WL-2b: persistence ρ −0.011; regime sweep family-wise p 0.36) |
| 10:10-10:34 | longer windows (30d) mean longer cycles, "more time for things to go against you" | Descriptive. Consistent with the VRP panel's tenor finding: the premium is **10d** (+1.75vp, t 8.93) and absent at 30d/90d (t 2.08 / 1.30) |
| 11:23 | higher VIX → shorter duration, so duration is "the real decision" | Plausible (and partly the absolute-threshold artefact above). Our tenor evidence points to short tenor for index premium, for a different reason (VRP lives at 10d). Not tested as a VIX-conditional tenor rule |

## "Sell high vol": index-after-stress, per-name, or neither?

**Index-after-stress, indirectly, and only for the VIX *level*, not the premium.** "Above 25, contractions take
over" is the descriptive shadow of our certified cell. But the study never shows that selling at 25 earns more than
the market already charges for the expected contraction. On that point our post-shock test says no, beyond the VIX
level itself. The per-name remark (closing single-name strangles by the VIX calendar) has no support.
**Refines, doesn't overturn:** it's consistent with "the index-after-stress cell is real, and the level is the
signal, not the spike".

## What I would take

1. **The de-duplication method** (one event per peak) is the right unit for any VIX-episode study. Our certified
   bucket is already counted as episodes, not trades ("~43% of trades in one year"), for the same reason.
2. **Absolute-point thresholds on the VIX are level-biased.** Use log or percentage moves when conditioning on
   the level.

## Not tested, could be

- **Nothing genuinely new that's worth a slot.**
  - SVXY-as-vehicle for the stress-state bet is new *as a vehicle* but not as a hypothesis. It would be the same
    bet as the certified bucket, so no diversification.
  - Post-2018 SVXY is −0.5× and short-VIX-futures roll yield is a different premium from the index put VRP, so
    it's a separate study, not a transfer.
  - Data exists (yfinance `SVXY` 2011-10 → today, 3,763 rows; shares, no option friction).
  - I'd only propose it if Gabe wants a second, share-based expression of the stress bucket. ~2 h. Low priority.
- VIX-conditional tenor ("shorter tenor at high VIX") is adjacent to the VRP tenor row and the certified cell's
  own sweep, which already chose its DTE. Not new enough.
