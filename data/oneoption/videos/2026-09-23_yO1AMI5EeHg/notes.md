# OneOption — "Stop Buying Shares in a Choppy Market (Do This Instead)" (Pete, 2026-09-23, 26 min)

_Reviewed 2026-09-23. Solo chart walk-through: two recent put-sale picks, an SPX market read, then MRNA as a
scale-in swing plus short puts / a bull put spread. Transcript (`en-orig` auto-captions) in this folder._

⚠ **The title and description don't match the video.** The description's timestamps ("1:45 market context… 11:20
share buying vs selling puts") describe a generic explainer that isn't there. No side-by-side comparison of shares
and puts is ever made. The title's claim is the channel's framing, not something the video argues.

## Verdict: 2 / 5

The process is coherent and more disciplined than most in this genre:
- he only sells puts on names he would own;
- he doesn't chase a fill that got away;
- he scales in by fifths;
- he tells people to hold cash against naked puts;
- he promises to review *all* his picks on Sunday.

The evidence is zero. The only outcomes shown are one winner (BMNR) and one unfilled trade (SMCI). Every return is
quoted as return on margin, with no probability of loss attached. The headline claim ("sell puts instead of buying
shares") is the trade our BCI test already failed: **a cash-secured put ≈ stock at the same delta, minus costs.**
His 1–3 week single-name horizon is exactly where our premium-selling evidence is worst.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| title | In a choppy market, sell OTM puts instead of buying shares | ❌ **Contradicted.** BCI CSP / covered-call test (326 names, 8 yrs): **FAIL**. The short put earns what the stock at the same delta earns, minus costs, and filters add nothing. A short put isn't an alternative to shares. It's a smaller, capped share position with a friction bill |
| 01:15 | BMNR: stock above all MAs, "test, test, test" of support + high IV → sold <2-week OTM puts, bought back for pennies in a week, "5–6% in one week" | **One winner, no denominator.** Selling puts on names in a confirmed uptrend at high IV is roughly our paid-to-wait IV≥60th-pct cell: +5.7% net, **MARGINAL**, gated-minus-ungated t 2.29, not certified; 2021–22 negative. Short-dated single-name selling is net **negative**: 10-DTE costs were 136% of gross, and liquidity is the gate (SPY + NVDA/AMZN/AAPL/V). BMNR at its IV is almost certainly outside that set |
| 02:47 | SMCI: the gap-up meant no fill at the target premium. With 2–3 weeks to expiry you must enter on day 1–2, and don't take the trade if price comes back later | **Untested, and harmless as a discipline.** Note what it does to his record: a trade that "did what we expected" but never filled is shown as a success, and it never enters a P&L |
| 03:55 | "This is absolutely not an option-premium buying environment"; sell puts and bull puts on strong stocks | **Half right, on the wrong object.** The only equity-option cell that certifies is index put selling after a selloff (SPY bull put bearish-high-IV **t 6.07**, SPX condor t 5.21, one bet). That is *index*, not single names. On single names, our long 7-DTE straddle behind an IV-percentile ≤30 gate is the book's other surviving leg, so "never buy premium" is a regime call we can't support unconditionally. The short-straddle mirror test found the long straddle's gates invert *at significance* for the seller |
| 05:33 | A break of the lower channel line = selling climax, which is often followed by a break of the upper descending trendline ("H-minus") | **Untested pattern, one instance.** No test here. Our index-timing work (FTD as a regime switch) is NULL, and nothing we tried forecasts the paying months |
| 06:37–11:15 | Fed hike + December dots, 10-yr at highs, oil, seasonality, quad witching "mechanical" selling; expect a rest after a 4-day, 230-point rally, hold half the long green candle (~770), 773 = resistance | **Narrative.** Our catalyst work: FOMC is noise (macro no, earnings yes). "Rest after a big move → don't get aggressively long" is untested here as stated. The adjacent post-shock-premium test (IV stays rich after a big move) FAILED against VIX-matched days |
| 12:30–15:46 | MRNA: huge news gap $60→$180. Took 1/5 on a close above the red candle, sat through $170→$130, and adds on a **high-volume close above the all-time high** ("blue sky") | ❌ **This is DR-EP arm B almost verbatim, which is NULL.** `run_drep_catalyst_retrace.py` (2026-09-22): catalyst = gap ≥3%, RVOL ≥1.8. Entry = first close above the post-catalyst high after a give-back: **−0.067R, t 0.21, fails 3 of 4 conditions**, and is *worse* than the same retrace rule with no catalyst gate. Buying the catalyst day itself: **−0.173R, t −4.70**. Only 38% of catalyst days ever give back and resume. ⚠ His discretionary read of *which* catalyst matters is the untested residual (catalyst classification, our open queue item) |
| 14:08 | Scale in by fifths so a pullback doesn't shake you out | **Fine as risk control, no edge.** O'Neil pyramid test (2026-09-22): adds earn the same edge as the base, and no add condition beats the unconditional add. Scaling scales the edge, it doesn't improve it. Its real value is the behavioural one he names |
| 15:54 | Choppy biotech: don't buy intraday breakouts, buy intraday pullbacks | **Contradicted on both halves.** Entry study: the **daily close beats every intraday entry** (t to −3.4). EMA-pullback entries on leaders came in **below** the breakout entry |
| 18:44 | Sell the 10-Oct (1.5-week) $165 put for ~$5 → own at an effective $160 or keep the premium; "$80 put up, $5 collected ≈ 6.5% in a week and a half" | **The arithmetic flatters it twice.** (1) $80 is *half* the strike, his reserve rule, not cash-secured. Fully secured it's $5/$160 ≈ 3.1%. (2) The $5 is the price he *hopes* to get on a pullback; the 160 put quotes ~$3. There's no loss probability anywhere, and on a choppy biotech the left tail is the whole question. He does name the real cost correctly: if it runs, the capped upside forces him to chase shares |
| 21:13 | A bull put spread is "leveraged" and only for people who can watch it; naked with half the strike in reserve means "you can always take assignment" | **Muddled, but the underlying point is right.** A $2.50-wide spread has *less* dollar risk than a naked put. The real hazard is sizing spreads by margin, so ten spreads ≈ one naked put's risk. Also, half the strike in reserve can't absorb a full assignment in cash; it needs margin |
| 22:10 | $160/$157.50 bull put for ≥$0.50 credit on $2 margin = "25% in a week and a half". Quote is $0.20 × $1.80 | ❌ **This is the UVXY/UVIX failure pattern.** The market is **$1.60 wide on a $0.50 target credit**. Our cost model charges 25% of the quoted spread on entry alone, ~$0.40, i.e. ~80% of the credit before any exit. UVIX bear calls went +11.0% gross → **−8.8% net (t −2.81)** on exactly this ratio. Credit/width here is 0.20. Our cw sort (the one cross-sectional selector that replicated, t 3.56) says take higher cw, and this is mid-to-low. "25% return" is max profit over max loss, not an expectation |
| 24:18 | "The odds of it going higher are much greater than the odds of it going lower, no matter what the market does" | **Unfalsifiable as stated.** Our breakout book says the post-breakout population is bimodal (23.6% never retest, +1.27R; 76.4% do, −0.37R), and **the split can't be called at entry** |
| 25:04 | Sunday: a review of *all* picks from the last two months, "I don't sweep them under the carpet" | ✅ **The one thing worth following up.** If he publishes a complete pick list with entry prices, it can be scored forward (like the Ariel nightly-call bookkeeping). It's still a scored list, not evidence of edge, and it has to be checked against the picks the videos actually made |

## What I would take

1. **Nothing to adopt.** The two testable claims we have evidence on (puts instead of shares; add on the post-catalyst
   high-volume breakout) are already a FAIL and a NULL here.
2. **Two disciplines consistent with our findings:** don't chase an unfilled short-premium entry, and size naked puts
   as if you'll be assigned. The second is our "size by max loss" rule in his words.
3. **A worked example of why quoted returns mislead:** the $0.20 × $1.80 spread he walks through is the clearest
   on-camera illustration yet of friction ≈ the premium. It's the same mechanism that retired 13 of 13 screener spreads.

## Not tested, could be

- **His put-sale filter as a gate on single-name bull puts:** above all major MAs + support tested ≥3 times + high IV,
  1–3 weeks, vs the paid-to-wait IV gate alone, at real fills. Low prior: the 10-DTE single-name null and the
  liquidity gate probably dominate. ~½ day on the existing put-spread engine. **Not queued** unless asked.
