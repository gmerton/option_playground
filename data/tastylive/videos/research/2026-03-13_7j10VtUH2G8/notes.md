# tastylive / Market Measures: "We Tested 10 Years of SPY Strangles Across Every Volatility Regime, Here's What We Found" (2026-03-13, 13:51; sponsored by Cboe)

_Reviewed 2026-09-23 for the Sosnoff-doctrine batch (Tier 1). The study runs 04:33 to 13:44. Transcript (`en-orig`
auto-captions) in this folder. The per-bucket P&L tables are on slides that aren't in the transcript, so only the
ratios the host read aloud are available._

## Verdict: 2 / 5

**What it claims:** on a 16Δ SPY strangle (45 DTE, managed at 21), high IV at entry gives a higher mean P&L and a
*less* negatively skewed P&L distribution. So in high IV, sell **closer** to the money, because "your loss is
basically the same across the board".

**Why it scores low:**

- **The key statistic is the wrong one for the question.** "Skew" here is the third moment of the trade P&L
  distribution. The host concedes at 11:03 that "skew and maximum loss are entirely different things… it doesn't
  really tell you much about the wins and losses". The decision-relevant numbers (mean, worst loss, n per bucket)
  are on slides that were never read out. The exception is the delta cut: +24% average, +38% largest loss.
- **It contradicts itself on the tail.** 07:24: in high IV "your big losses, tail type losses… tighten up".
  13:04: "the distribution is much wider when volatility expands". 13:21: "your average losses are going to be much
  wider when volatility is low". These can't all be true of the same slide.
- **The 40+ IV bucket is a handful of episodes.** VIX closed ≥ 40 on just **40 days since 2015**, spread over 2015-08,
  2020-02/03/04/06/10 and 2025-04 (`data/cache/vix_daily_long.parquet`, quick lookup). "40-plus IV reduces skew
  magnitude by roughly 85%" is a statement about ~3 stress episodes, with no n and no t. The host says it himself at
  13:42: "those occurrences are rare".
- **"More aggressive delta in high IV" (09:15) is the opposite of our own sweep's pick** for the one regime that
  certifies (see the claim table).

## Data audit

| item | what the video gives |
|---|---|
| underlying | SPY only |
| period | **2015 → 2026** ("10–11 years") |
| n | **not stated** (overall or per bucket) |
| entry rule | "short 16-delta SPY strangle, 45 days, manage at 21 days" (04:42); deltas **10 → 50** in the delta cut |
| buckets | SPY IV at entry: **<10, 10–20, 20–30, 30–40, 40+** (five buckets; the host first says four) |
| management | 21 DTE |
| fills | **unstated.** Channel disclaimer: "Performance is not presented net of all commissions, fees, and expenses." No slippage mentioned. Treat as mid. |
| control | the buckets are compared with each other; no hold-to-expiry arm, no buy-and-hold, no equal-exposure benchmark |
| win rate / avg / tail | mean P&L and "largest loss" are on the slides but **not read out** except as % changes; no drawdown, no loss clustering |
| significance | none |
| selection | overlapping entries (frequency unstated) + a 40+ bucket dominated by 2020 and April 2025 → effective n for the high bucket ≈ a few episodes |

## Numbers as spoken

| @ | number |
|---|---|
| 04:33 | SPY **2015 → 2026**, short **16Δ** strangle, **45 DTE**, managed at **21 DTE** |
| 05:04–06:45 | IV buckets **<10, 10–20, 20–30, 30–40, 40+**. At recording SPY 30-day IV ≈ **25%** (March ≈ 27%) → "middle bucket" |
| 06:56 | "as the VIX rises, the magnitude of negative skew in the P&L distribution generally becomes smaller" |
| 08:29–08:45 | delta **10 → 50**: P&L skew magnitude **−57%**, **largest losses +38%**, **average P&L +24%** |
| 09:44–10:02 | in high IV, "your loss between a 20 delta option and a 50 delta option is… a couple hundred bucks. Whereas your reward is double" → "**2× the reward** with… about the same loss" |
| 10:11–10:20 | trading at **IV 40+** vs **10–20** "reduces skew magnitude by roughly **85%**" |
| 13:00 | takeaway: "The 40 plus IV range, skew drops by **85%** compared to the 10 to 20 range" |

## Claim by claim

| @ | claim | our evidence |
|---|---|---|
| 05:43 / 07:47 | Selling a 45-DTE strangle in high IV has a higher mean P&L because implied is over-stated | **Partly supported, at a different tenor and structure.** VRP panel: **10d +1.75 vp, t 8.93**, but at their tenor **30d +0.78 (t 2.08) and 90d +0.84 (t 1.30)** don't clear, and "not one IV-percentile bucket, not one VIX regime" does at 30d. The **post-shock SPY vol premium FAILS** vs VIX-matched days (10d **−10.8pp, t −1.8**): the post-shock premium is just the VIX level. What *does* certify is narrower than "high IV": **SPY bull put in Bearish_HighIV (below 50MA and VIX ≥ 20), 0.25/0.15, 20 DTE, t 6.07** (75 trades, +6.76% net of max loss, 94.7% win, worst −100.7%, 8/9 years, **42.7% of trades in 2022**; re-read at `tierab_significance_2026-09-22.csv`). SPX condor in the same regime t 5.21. That's one bet, and it's a defined-risk **put** sale conditioned on trend **and** VIX, not a naked strangle on IV alone. |
| 07:24 vs 13:04/13:21 | Tail losses tighten in high IV / the distribution is wider in high IV / average losses are wider in low IV | ⚠ **Self-contradictory**; can't be scored as stated. Our nearest measurement: the 21-DTE study's SPY held arm lost **−$8.48/share on average in 2020 entries** vs ≈ 0 in 2021–22 (`exit_21dte_2026-09-23.csv`, 20Δ, real fills). The high-IV year had the tail, which cuts against "tails tighten". |
| 08:29 | 10Δ → 50Δ: average P&L +24%, largest loss +38% | **The tail grows faster than the mean.** That's their own number, and it's the opposite of their conclusion. No per-bucket n, so the bucket-conditional version ("in high IV the loss is about the same") can't be checked. |
| 09:15 | When IV is high, sell a higher delta (20–50Δ rather than 10Δ): ~2× the reward for about the same loss | ⚠ **Opposite of our own regime sweep.** In Bearish_HighIV the sweep picked a **0.25Δ** short put (SPY and QQQ), versus **0.45Δ** in the Bullish regimes. The certified SPX cell is 0.20c/0.30p. Caveat: those picks carry k ≈ 52 of search each, so this is weak evidence. It still doesn't support moving toward ATM in stress. The single-name short **7-DTE ATM straddle** mirror is **NULL**: IVpct ≥ 85 +3.19% at mid, CI [−2.86, +8.57], worst trade **−1,193% of credit**. |
| 11:37 | "Implied volatility as a general statement is usually overstated" | ✅ **Agrees at 10 days** (17/17 years); ⚠ **not measurable at 30–90 days** in our panel, which is their tenor. |
| 12:00 | Delta drives max loss; at very high IV the 50Δ vs 10Δ loss gap narrows | Plausible mechanically (at IV 40+ even a 10Δ strike is close in ATR terms). Our `ema_strike_breach` study: **breach odds depend only on cushion in ADR (2 ADR ≈ 21%, 3 ≈ 13%)**. If the cushion in vol units is the same, high IV doesn't protect the far strike. Untested on P&L. |

## What I would take

1. **Nothing to adopt.** The one conditional short-premium cell we certify is narrower (trend + VIX, defined-risk
   put side, 20 DTE) than "sell SPY strangles in high IV", and it didn't pick higher delta.
2. **Their delta cut is worth keeping as their own admission:** going 10Δ → 50Δ raised the average P&L 24% and the
   largest loss 38%. More premium buys proportionally more tail.
3. **Reading rule for Market Measures:** a "skew of P&L" slide isn't a risk-adjusted-return slide. Ask for the mean,
   the n and the worst trade per bucket.

## Not tested, could be

- **SPY 45/21 16Δ strangle by entry IV bucket, at real fills, with the worst trade and n per bucket.** Codable:
  Friday entries 2018-01 → 2026-03 (bid/ask coverage ends ~Mar 2026), 16Δ put from
  `data/cache/SPY_puts_v3_2018_2026.parquet`, 16Δ call from a v3 pull (`run_spy_puts_v3_pull.py` with
  `cp='C'`), sell bid / buy ask at the first session ≤ 21 DTE, buckets by VIX at entry. Report mean, win%, worst,
  and month-clustered t per bucket. Also cross it with the 50-DMA to see whether IV alone or IV × downtrend does
  the work.
  - **Effort:** ~½ day, plus the call pull (a few Athena chunks).
  - **Coverage:** 2015–2017 isn't in the SPY cache (starts 2018), so the August 2015 high-IV episode can't be
    covered without a wider pull.
  - **Prior:** the IV-only split will look positive and fail t ≥ 3 once the Šidák charge applies; the trend × VIX
    split (our certified shape) is where any signal is.
  - **Not queued unless asked.** This overlaps the certified cell and the 21-DTE row.
