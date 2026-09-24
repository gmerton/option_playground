# tastylive / Market Measures: "Why After This Study We Won't Ever Trade Volatility Expansion" (2025-02-11, 8:03)

_Reviewed 2026-09-23 for the Sosnoff "sell vol when it's high" wave. Two hosts (Tony Battista plus a senior host
who references "the research we did yesterday") read a research-desk deck. Transcript (`en-orig` auto-captions) in
this folder. The P&L-by-VIX-bucket table (02:58-04:22) is on a slide that is only partly read aloud, and the last
slide (08:00) is cut off._

## Verdict: 2 / 5

This is the purest statement of the Sosnoff doctrine in the batch: "**the return on investment is a negative number
when volatility is low**. That's why we use IV rank to tell us when to get into positions" (03:43-03:55). The
second half of the study (VIX change over 45 days by starting VIX) is ordinary mean reversion: from a low VIX the
next move is more often up, from VIX > 30 it's down.

**Where it's right:** index short premium at low vol is a poor trade on our data too.

**Where it overreaches:**
- It generalises from **SPY and TSLA** (TSLA gets the *VIX* change, not its own IV change, as read at 06:22) to
  "we use IVR for individual stocks". Per-name IV rank is exactly where our data says the rule fails.
- The title's conclusion, "we won't ever trade volatility expansion", is the one our book refutes. Our surviving
  long leg **buys** single-name vol at **low** IV percentile.

## Data audit

| item | what the video gives |
|---|---|
| underlying | **SPY and TSLA** only (01:17-01:51, chosen as the two most-traded option names) |
| trade | short **16Δ strangle, 45 DTE, managed at 21 DTE** (01:54) |
| buckets | VIX at entry **< 15, 15-30, > 30** (02:00-02:10) |
| period | P&L study unstated; VIX-change study "every trading day since **2017**", ~8 years (04:35-04:42) |
| n | **not stated** for any bucket. The > 30 bucket is ~7% of days (host recollection, verified below), i.e. a handful of episodes |
| fills / costs | **unstated**; channel disclaimer "not presented net of all commissions, fees". Treat as mid |
| control | the buckets are compared with each other; no hold-to-expiry arm, no benchmark |
| tail shown? | **no.** "probability of profit, everything's going to be kind of the same" (04:14); no worst trade, no loss distribution |
| significance | none |
| selection | daily overlapping 45-day windows (VIX study): heavy overlap, so the effective n is far below the row count |

## Their numbers (transcribed)

| @ | number |
|---|---|
| 02:15-02:36 | VIX > 30 "around **7%** of the time"; 15-30 "about **40 to 50%**" (host recollection) |
| 03:13-03:19 | SPY 16Δ strangle credit: IV 15% → **$3.35**, IV 25% → **$5.05**, IV 35% → **$7.35** |
| 03:43 | "the return on investment is a **negative number** when volatility is low" (value not read) |
| 04:14 | POP and buying power "kind of the same" across buckets; average P&L and ROI better at higher IV (values not read) |
| 04:49-04:53 | SPY, very low IV: **75%** of 45-day periods saw a VIX change of **< 3.7 points** |
| 06:22-06:29 | TSLA, very low IV: **75%** of 45-day periods saw a (read as) "vix change" of **< 3.8 points** |
| 00:31-00:39 | high VIX usually lasts "five or six days", 2008-09 "two, 300 days" |

**Verified:** VIX close > 30 on **6.9%** of sessions 2017-01 → 2025-02-10 (n 2,038; `data/cache/vix_daily_long.parquet`).
< 15 is **37.0%** and 15-30 is **56.1%**, so his 40-50% for the middle bucket is low.

**Credit arithmetic:** credit / IV = 0.223, 0.202, 0.210. The premium scales ~linearly with IV, as it must. A
bigger credit is **not** a bigger edge: the question is premium minus expected payout, which this slide doesn't show.

## Claim-by-claim

| @ | claim | our evidence |
|---|---|---|
| 00:06 | selling premium in high IV is ideal because vol mean-reverts | **PARTIAL, split by level.** Index after stress ✅: SPY bull put bearish-high-IV **t 6.07**, SPX condor t 5.21, one bet (§0/§1 Tier A/B certification row). Per name ❌: IV rank on single-name bull puts **zivr −1.89pp, t −1.25**, and the lowest-ivr quintile earned most (§1 "IV rank vs credit/width" row) |
| 03:43 | ROI negative on 16Δ strangles when VIX is low | ✅ **Agrees on the index, in direction.** QQQ bullish-low-IV **−4.8% month-weighted, t −0.87** (Tier A/B row); IWM Bearish_LowIV negative in every IV band (§1 own-IV row); SPX/QQQ bullish-high-IV not certified either. Our nearest same-trade row (SPY 16Δ strangles by IV bucket, `2026-03-13_7j10VtUH2G8`, §9 tastylive batch row) found the buckets' n and tails never shown. Not re-tested |
| 03:52 | "that's why we use IV rank" for individual stocks | ❌ **Contradicted per name.** IV rank vs credit/width (6,419 spreads): ivr NULL in both fits, quintiles non-monotone and **backwards** (lowest ivr earned most); cw works best *in the lowest-ivr column* (§1). Straddle IV gate: OptionsPlay's range IV rank is worse than our percentile at every threshold (§2) |
| 04:30-06:15 | low VIX → 75% of 45-day changes < 3.7 pts; the biggest upside risk is from VIX < 15; VIX > 30 contracts "long term" | ✅ **Descriptive and true** (mean reversion). But mean reversion of the VIX *level* isn't a premium: the VIX futures curve prices it. At high VIX the curve is backwardated, i.e. the market already expects the drop. Our post-shock test is the operational version: **post-shock richness is just the VIX level; 10d short straddle −10.8pp vs VIX-matched days (t −1.8), after UP shocks −20.7pp (t −2.1)** (§2 post-shock row) |
| 05:08-05:30 | "you cannot time a VIX expansion", so you can't inventory long VIX | ✅ Agrees: cheap-convexity overlay NULL (carry −20…−34%/month, 2022 must-pass fails, §2); tail overlay [WL-5f] 5Δ same-expiry −100% on all 75 trades (§1) |
| title | "we won't ever trade volatility expansion" (don't buy vol) | ❌ **Contradicted on single names.** The 7-DTE long straddle gated on **low own-IV percentile** (≤20th pct mid +9.19 vs +5.05 ungated, monotone plateau) is the book's surviving long leg (SUPPORTED t 3.7). The short 7-DTE straddle **mirror** confirms it: **IVpct ≤ 30 short −4.51 [−9.02, −0.47]**, significant *against* the seller (§5 short-straddle row). At low IV on single names the edge is to **buy**, which is exactly what this video rules out |
| 07:06 | P&L comes from delta and theta more than vega | ✅ Consistent with the VRP-panel method note (a simulated structure's P&L is dominated by the terminal price) |
| 07:34-07:54 | in low IV, reduce contracts and hold some short delta to offset vega | Size-down agrees (low-IV index cells negative). "Short delta" is an untested hedge; our call-side results are all negative (ETF condor call side t 0.6; UVXY/UVIX bear calls −7.4% / −8.8% net) |

## "Sell high vol": index-after-stress, per-name, or neither?

- **Index: supports the low-vol half ("don't sell cheap index vol")**, which matches QQQ bullish-low-IV and IWM
  Bearish_LowIV. It doesn't isolate the *after-stress* condition. The VIX > 30 bucket is ~7% of days and a handful
  of episodes, which is where our certified cell lives.
- **Per-name: the extension to IV rank on individual stocks is contradicted.** Our strongest per-name vol result
  runs the other way (buy low-IV single-name straddles, and the seller's mirror loses there at significance).
- **Refines, doesn't overturn:** the video is the index half of the doctrine plus an unsupported per-name
  extrapolation. That's our reading exactly.

## What I would take

1. "Don't sell index premium at low VIX" is **consistent with** our uncertified/negative low-IV index cells. Nothing
   to change: the screener already tags them Tier U.
2. The credit-scales-with-IV slide is a good teaching example of **premium ≠ edge**.

## Not tested, could be

- **Nothing genuinely new.**
  - VIX-bucketed SPY 45/16Δ strangles: already specced as the VIX-rank sweep in
    `2025-02-25__QYaqicT5dg/notes.md` "Not tested, could be" and adjacent to the 21-DTE row, where both arms lose.
  - TSLA per-name IV buckets: answered by the IV rank vs cw row.
  - VIX mean reversion: descriptive, priced by the futures curve, and answered operationally by the post-shock row.
