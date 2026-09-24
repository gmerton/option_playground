# tastylive: "3 Years of SPX Jade Lizard Data. The $30 Wide Put Spread Wins Every Time." (2026-05-16, 10:04)

_Reviewed 2026-09-23 for the Sosnoff "sell vol when it's high" wave. Two hosts read a research-desk deck; the
senior host has been trading short-term SPX jade lizards live on the show. Transcript (`en-orig` auto-captions) in
this folder. The P&L / win-rate grids are on slides; only a few cells are read aloud._

## Verdict: 1.5 / 5

**"Every combination tested came back positive"** over three years in which, as the hosts say twice, "anything that
leans bullish… has been really, really high-performing" (03:37-03:51) and "the data here is really, really skewed…
it's just the market, what has happened" (08:13-08:21). That's the whole audit: a short-put-dominant structure
scored only on a bull market, at **mid** ("how often the credit **mid price** was at least the width of the call
spread", 02:09), with a 25% profit take that a rising tape triggers almost automatically. There's no loss
distribution, no n, and no control. "Wins every time" (title) compares widths with each other, not with anything
outside the structure.

The honest part: they volunteer the bull-market caveat and that the wider put spread "puts more risk on the table"
(06:13, 06:34). But the comparison they then make ($40 vs $100 average P&L) is in **dollars, not return on risk**.
A 30-wide put spread risks ~50% more than a 20-wide, so the bigger dollar P&L is partly just the bigger position.

## Data audit

| item | what the video gives |
|---|---|
| underlying | **SPX**, short-term options |
| period | **3 years** (01:33), ending ~May 2026, i.e. roughly 2023-2026, a bull market by their own account |
| trade | **7-day jade lizard**: short put spread + short call spread, credit ≥ call-spread width so there's no upside loss |
| widths | put **$20 / $30**, call **$5 / $10** (01:39-01:57; the description says "six combinations", the transcript names three or four) |
| strikes | short strikes at **ATM, 0.25×, 0.5× … 1.5× the expected move** (03:17-03:23) |
| entry filter | a lizard is "valid" only if the **mid** credit ≥ the call width (02:09) |
| management | close at **25% of max profit**, checked at each day's close and **every 10 min on expiry day** (02:33-03:05); otherwise presumably expiry |
| n | **not stated** (per cell or overall) |
| fills / costs | **mid** (explicit for the validity test; P&L convention unstated; channel disclaimer "not net of all commissions") |
| control | none: no hold-to-expiry arm, no put-spread-alone arm, no buy-and-hold / delta-matched benchmark |
| tail shown? | **no**: no max loss, no worst week |
| significance | none |
| selection | the sample period, bullish throughout, is the dominant selection; widths compared in $ not ROC |

## Their numbers (transcribed)

| @ | number |
|---|---|
| 01:33 | **3 years** of data, **7-day** lizards |
| 02:33 | winners closed at **25%** of max profit |
| 04:20-04:29 | $5 call spread: collect ~**$1.50**; $10 call spread: ~**$2-3**, so the put spread must supply ~**$7** |
| 04:33-04:47 | with the $10 call spread you can't fill ≥ $10 credit **past the expected move** (N/A cells) |
| 05:24 | win rate "**70%**", "spectacular across the board" |
| 06:15-06:20 | $30/$10 viable to ~**1.25× EM**, not 1.5× |
| 07:36-07:41 | average P&L "**$40**" vs "the **100**" (the $30-wide) |
| 09:06-09:11 | $30/$10 viable to about the expected move; $20/$10 must sit inside it |

## Claim-by-claim

| @ | claim | our evidence |
|---|---|---|
| 08:50 | every width combination is positive over 3 years | ❌ **Not evidence: one bull regime, mid, $ not ROC.** Our index short-put cells outside stress are **not certified**: QQQ bullish-low-IV **−4.8% month-weighted, t −0.87**; SPX bullish-high-IV + 200MA condor t 2.26 with 51% of P&L in one year; QQQ bullish-high-IV t 1.04 (Tier A/B row, §0/§1). Only the **bearish-high-IV** cell certifies (SPY t 6.07, SPX t 5.21) |
| 04:00 / 06:24 | wider put spread → better P&L and win rate | **Mostly size, not edge.** Compared in dollars, and a 30-wide risks more. Ledger adjacent (ROC-normalised, single-name bull puts): the **narrowest** wing loses (−0.04% net) and anything from 0.20Δ out is flat (+2.66/+3.10/+2.98%, t 0.83 across them) (doctrine rule 16, `premium_to_width_2026-09-22.csv` recut). Direction agrees for "not the narrowest"; "wider keeps winning" isn't supported |
| 09:29 | once the width is fixed, go as far OTM as the credit allows; further OTM performed better | **Contradicted on our index evidence at 1 day, untested at 7 days.** SPY 1-day on positive-gamma days: 16/5Δ condor +1.8% (t 2.4) and 16/5Δ put spread +1.9% (t 3.5) vs the ATM 2× fly **+5.8%**: "the edge is AT the money" (§2 condor/put-spread row). Their "further OTM better" is scored with a 25% take in a rising tape, which mechanically favours OTM puts |
| 00:37 / 08:27 | the call spread funded by put credit = "no upside risk" | ⚠ **Only at mid.** A 4-leg structure pays four half-spreads each way; at real fills (sell bid / buy ask, `lib.studies.costs`) the credit ≥ call-width condition fails on some of the "valid" cells, and the upside risk comes back. Every small-credit spread in our screener turned out to be a mid-pricing artefact (13 of 13 not certified; UVIX +11.0% gross → −8.8% net) (§1). SPX 7-DTE spreads are tighter than those, so the damage is smaller, but unmeasured |
| 00:52 | the call side is "an iron condor plus an extra put spread" | ✅ Correct decomposition. Our call-side evidence is uniformly flat-to-negative: ETF condor call side +0.36%/trade, t 0.6 (§1). The lizard's P&L will be the put spread's |
| 05:24 / 05:43 | 65-70% win rate is the target | ❌ Win rate is a dial, not an edge. Across credit/width quintiles the win rate *falls* 79.6→75.7 while net ROC *rises* −2.96→+4.07 (t 3.74) (doctrine rule 14) |
| 08:00 | "if you have a choppy market, the $20 and $30 wide with the $10 call spread will be way, way better" | Untested and unsupported by their own sample, which has no choppy market in it |

## "Sell high vol": index-after-stress, per-name, or neither?

**Neither. The study has no volatility condition at all.** It's unconditional index short premium in a bull market,
which is exactly the cell our ledger **does not** certify (bullish-low-IV QQQ −4.8%, bullish-high-IV SPX/QQQ
unearned). If anything it illustrates the opposite of the doctrine: a 3-year low-to-moderate-VIX sample made
*everything* short-put look good. That's regime beta, not a vol premium. **Neither refines nor overturns our
reading.**

## What I would take

1. **Nothing to adopt.** The positive result is the sample period.
2. Two reminders it illustrates well:
   - compare widths in **return on max risk**, not dollars;
   - a "no upside risk" condition defined at **mid** isn't the same condition at the fill.

## Not tested, could be

- **Nothing genuinely new.** The jade lizard is a skewed condor, which the ledger has by regime: SPX condor
  (certified only bearish-high-IV), ETF condor call side (nothing), 1-day SPY put spread vs fly.
- Their intraday 10-minute management needs intraday option quotes; v3 is EOD, so we couldn't replicate it at
  real fills anyway.
- A 7-DTE SPX lizard *inside the certified bearish-high-IV state* would be a new structure on the one live cell.
  But it's best-of-k on the same episodes (like the overlay [WL-5f], which found the bucket better left alone).
  Not proposed.
