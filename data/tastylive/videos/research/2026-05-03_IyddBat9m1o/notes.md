# tastylive / Options Jive: "Most Traders Hold Options to Expiration. Data Shows Managing at 21 Days Doubles Your Odds." (2026-05-03, 8:52)

_Reviewed 2026-09-23 for the Sosnoff-doctrine batch (Tier 1). Two hosts discussing research slides; the study runs
00:56 to 08:14, followed by a market update. Transcript (`en-orig` auto-captions) in this folder. The slides aren't in
the transcript, so every number below is one the hosts said out loud._

## Verdict: 1.5 / 5

**There's no P&L anywhere in this video.** The title promises that 21-DTE management "doubles your odds". The odds
in question are the probability that **SPY's price returns to or stays near a reference price**, not the odds of a
winning trade. Both headline results are close to true by construction:

- **"Managing at 21 days doubles the chance of a return to the initial price."** Rolling at 21 DTE resets the
  reference price to wherever SPY is on the roll date (their words: "re-centering"). The managed arm therefore gets
  two short windows with a fresh anchor each, and the held arm gets one 45-day window with a stale anchor. More
  anchors and shorter windows mean more returns. That's arithmetic, not an edge.
- **"68%. One standard deviation is exactly what it should be."** Staying inside ±1 SD 68% of the time is the
  definition of 1 SD under a normal distribution. It's also odd on its own terms. They describe the 1-SD strangle
  as ~4% above and ~12% below spot. With implied above realized, the realized stay-inside rate for implied-SD
  strikes should come out **above** 68%. Our VRP panel has the 10d premium at +1.75 vol points (t 8.93). A
  measurement landing exactly on 68% suggests the band was drawn from realized vol, i.e. a tautology.

The one thing worth keeping is the framing at 00:57: "is there some sort of tradeability to a retracement in price? I
would say there isn't. But there is in options." That's their honest statement that the stock-price pattern carries
no edge.

## Data audit

| item | what the video gives |
|---|---|
| underlying | SPY only (NVDA, RIVN and XLRE are named as "three stock types" at 00:00 but never shown) |
| period | **not stated** |
| n | **not stated** ("each 45-day cycle") |
| entry rule | start of each 45-day cycle; no IV, regime or weekday rule stated |
| strikes / DTE | "45-day one standard deviation strangle", ~4% upside / ~12% downside strike distance (05:05) |
| management | managed = closed or rolled at 21 DTE (rolling re-centres the reference price); comparison = held to expiry |
| fills | **no P&L is computed, so there are no fills.** The channel disclaimer on every video: "Performance is not presented net of all commissions, fees, and expenses." |
| control | held-to-expiry vs managed. Both arms measure a price statistic, and the managed arm gets a new reference price |
| win rate / avg / tail | none; no trade outcome is reported |
| significance | none |
| selection | SPY only; they say themselves that single names behave differently ("stocks are binary", 04:14) |

## Numbers as spoken

| @ | number |
|---|---|
| 02:44 | "on average, prices revert back to the original trading value **twice** within a period of 45 days" (SPY) |
| 03:09 | "the probability **doubles** if the positions are managed at 21 days" |
| 05:05 | 45-day 1-SD strangle strikes ≈ **4% upside to 12% downside** |
| 05:24 | question posed: probability SPY stays within **1, 2 or 3%** of the stock price at 21 DTE |
| 06:42–06:57 | answer: **68%** ("the one standard deviation, it ends up being 68%") |
| 07:46 | "managing positions at 21 days has **twice the chance** of a stock price returning to its initial price point compared to holding to expiration" |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 00:57 | Price retracement isn't tradeable in the stock; options change that | ✅ **Agrees on the stock half.** Our equity-timing ledger is full of this (breakout +0.014R, intraday triggers ≈ a random later minute). The options half is asserted here, not shown. |
| 03:09 / 07:46 | 21-DTE management doubles the probability of a return to the initial price | ⚠ **Mechanical, not a finding.** The managed arm resets its anchor at the roll and gets two shorter windows. The quantity that matters is P&L, and we have measured it directly. **21-DTE management on a 45 DTE / 20Δ short strangle** (TEST_INDEX §1, `exit_21dte_2026-09-23_fixed.csv`, 14,367 strangles, 44 names, real fills): ~~PASS, paired +$1.53/share, t +4.26; both arms lose (−$2.55 / −$1.02)~~ (corrected 2026-09-24, FIX-1: original run dropped worthless-expiry winners). Fixed: **21-DTE close − hold −$0.52/share, month-clustered t −2.42** (NULL on return, leaning INVERTED; risk reducer only: sd $9.33 vs $17.09, worst −$291 vs −$617). Held **+$0.23/share, 74% win**; managed **−$0.29, 64% win**. So "more likely to stay in range" becomes a variance and tail reduction, **paid for with return**: managing earns less than holding. |
| 05:05 | 1-SD 45-day strangle ≈ +4% / −12% | Plausible for put skew on SPY (a 16Δ put sits much further OTM than a 16Δ call). Not checked; descriptive only. |
| 06:57 | 68% stay within 1 SD | ⚠ **68% is the textbook normal-distribution figure**, not a result. If the band is implied 1 SD, our VRP panel says realized should beat it: 10d premium **+1.75 vp, t_NW 8.93, 17/17 years**. The 30d premium is only +0.78 (t 2.08), so at their tenor the excess is small. Either way, "exactly 68%" is more likely a band drawn from realized vol. |
| 07:56–08:14 | "Exiting a position before expiration increases the probability of the stock remaining within a narrow range, which is beneficial for premium sellers" | **Half right, on risk only.** The 21-DTE exit cuts variance and the tail, but on return it is *worse* than holding (−$0.52/share, t −2.42; managed −$0.29 vs held +$0.23 across the panel; corrected 2026-09-24, FIX-1 — the old "beneficial relative to holding, t 4.26" was the buggy run). They never show the managed trade's absolute P&L. |

## What I would take

1. **Nothing new.** The part of the claim that matters (21-DTE management beats holding) was measured at real fills
   with a paired control, and after FIX-1 (2026-09-24) the answer is **no on return** (−$0.52/share, t −2.42), yes on risk. This video's version is a price-path statistic that
   doesn't reach P&L.
2. **A caution for reading tastylive:** "doubles your odds" here means the odds of a price event, not of a winning
   trade. Check which "probability" a slide is about before relaying it.

## Not tested, could be

- **Nothing worth queuing.** The price-return probability has no P&L content, and the P&L version has already run.
- The only live open question it touches: **does the managed 45/21 strangle turn positive under a forward-knowable
  liquidity filter?** Our 21-DTE row's lead has the hold arm at +$1.74/share / 72% win when mark coverage ≥ 90% (fixed run: +$2.75 / 86% at ≥ 90%, FIX-1 2026-09-24),
  but coverage is not knowable at entry. That's already recorded in TEST_INDEX §1; nothing new here.
