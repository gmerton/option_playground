# Review: "25 Years Of Brutal Options Trading Advice In 17 Minutes" (The Cashflow Academy, Corey Halliday, 2026-06-03, PM1JE3QbsjA) — 2/5

Reviewed 2026-09-23. 17:28, 215k views. **First video from this channel**; KB folder created for it.
Transcript: `videos/education/2026-06-03_PM1JE3QbsjA/`.

A beginner lecture: five "brutal truths", one live example (the NVDA chain the day after its print), and a
closing funnel to the channel's covered-call video. No trade is taken, no record is shown, no number is
backtested. What's here is **options mechanics plus a stance that selling beats buying**. The mechanics are
mostly correct. The stance is the part our ledger can test, and it contradicts it.

## Evidence class

**Educational lecture, zero track record.** Nothing in it is evidence. It gets scored on whether each claim
is correct against our ledger at real fills, and whether it's framed honestly. "25 years" is stated, not
shown.

## Claim ledger

| # | claim | ledger | verdict |
|---|---|---|---|
| 1 | Buying options puts you at a *strategic disadvantage*; "we prefer to live as the option seller" [06:41, 09:27] | **The only premium-selling bucket that certifies is index put selling in stress** (SPY bull put t 6.07 + SPX condor t 5.21, one bet). 10-DTE single-name selling **FAIL**: costs = 136% of gross (`vrp_shortdte_names_study.md`). The VRP exists at 10d (+1.75 vp, t 8.9), but **30d and 90d show nothing**. One of the two legs that survived the 9/16 audit is a **7-DTE LONG straddle**. The call debit beats delta-matched stock by +$97/contract (t 2.29); the put credit beats it by +$7 (t 0.26) | **CONTRADICTED as a blanket rule.** Selling pays in one narrow, liquid, index-level cell; outside it, the spread eats the premium |
| 2 | Don't buy far-OTM "lottery tickets"; you'll lose 100% [03:56] | Event convexity (0.12Δ/0.25Δ calls before FOMC/elections) is **MARGINAL, a real tail**. But the 0.12Δ-over-0.25Δ preference is a **mid-price artefact**: +19.5pp at mid vs **+1.9pp (t 0.29) at real fills**. SPY 1-day structures: "the edge is AT the money; OTM wins more often but collects little". Cheap-convexity index put overlay **NULL** (carry −20…−34%/month) | **AGREE, for a different reason.** Far OTM rarely pays at real fills, because the spread is a larger share of a cheap premium. His reason (probability of expiring worthless) is priced in and doesn't show an edge either way |
| 3 | Size on max loss and its probability, never on reward; no single loss should be memorable [07:46] | Hygiene, not a testable edge. Consistent with our size-lever result: the lever is **exclusion**, not a wide risk spread | **AGREE (untestable)** |
| 4 | Buying into earnings buys priced-in vol and eats the crush [10:32–13:55] | Pre-earnings ramp: front straddle loses **even at mid** (−3.4/−6.9/−14.3%, 8/8 years negative), with theta > vega. Earnings vol premium: real at mid (+0.601%), so the average straddle buyer overpays | **AGREE for the buyer.** ⚠ The implied remedy, "take profits from the crush as a seller" [13:55], **dies on the spread**: −0.428% at the bid, 7/8 years negative, crossing = 171% of gross. Only PARKED on the top ~40% by volume (+0.284%, t 1.1). The richest events are the worst sells at the bid |
| 4a | NVDA example: "priced to move well over 10%", calls −$6 / puts −$2.50 [12:15–13:22] | Stock is down 1.5% in the example, so the calls also lost **delta**, not just vega. Part of the asymmetry he shows as "crush" is direction. The ">10%" implied move isn't shown on screen, and our stored IV ends mid-May 2026, so we can't check it | **MUDDLED.** Vega and delta are conflated in the one live example |
| 5 | Theta is steepest near expiry: sell short-dated [16:05] | 10-DTE single-name selling = **FAIL** net of costs (above). BCI covered calls / CSPs vs stock at the same delta = **FAIL**. That's the video his CTA sends viewers to next | **CONTRADICTED** outside liquid index products |
| 5a | If buying, buy ~3 months out and exit with ~2 left [16:05] | Mechanically consistent with the ramp finding (theta > vega on the front tenor). **Not tested here** as a rule. Our long-call benchmark (always-call +9.5%) doesn't split by tenor/exit window | **UNTESTED — plausible, cheap to test** |

## What's wrong with it

1. **It treats the theta mechanism as if it were the edge.** "Wednesday becomes Thursday … the most
   predictable thing in the market" [14:59] is true and already priced in. Theta is what the seller gets
   paid to carry gamma risk. Our ledger shows that payment beats costs only in a narrow cell. The video
   never mentions bid/ask, which is the thing that decides every one of his claims here.
2. **It points to a strategy our ledger fails.** The CTA is covered calls, which lost to stock at the same
   delta after costs, and filters didn't help (`bci_csp_study_2026-09-17.md`).
3. **The one live example conflates vega and delta** (4a).

## What's right

Claims 2–4 are correct advice for a retail buyer, and 3 is the house's own view. Claim 5a is the one
concrete, falsifiable rule, and it's cheap to test.

## Score: 2/5

The mechanics are correct and the risk hygiene is sound, which is enough to rule out a 1. The central
thesis, sellers beat buyers, is contradicted by our ledger in its general form, and the funnel points to a
FAIL.

## Queued

- **Tenor-window long call**: buy ~90 DTE, exit at ~60, vs buy ~60 exit ~30 vs buy ~30 hold to expiry,
  same names/dates, real fills, `call_spread_study`/long-call engine. Settles claim 5a. Low prior on an
  *edge*; the question is whether the window reduces the theta bleed enough to beat the always-call
  benchmark after the wider spread on longer tenors. ½ day. **Not run.**
