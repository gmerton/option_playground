# Tail hedging KB (deep-OTM puts, crash convexity)

Skeptic-default reviews of tail-risk / "black swan" hedging content. The standing question for every entry here:
**does the hedge improve *our* book's risk-adjusted return after real fills, or is it negative carry that pays only in
the episode the creator picked?**

## Leaderboard

| date | creator | video | claim | score | tested? | notes |
|---|---|---|---|---|---|---|
| 2026-01-15 | Nichol Hermel | HC6GKtqNZHc, "Black Swan Hedges Explained" | 1–5Δ index puts, 0.5–2%/yr budget, rolled every 1–4 months, protect against crashes | **2.5/5** | **Already tested (adjacent), NULL.** Cheap-convexity overlay: carry −26% to −32% per month on premium, book ΔSharpe −0.05…0.00. His 2020 example re-priced on v3 = 36.7× at real fills, but it's the best window of 16 years and the put was worth zero at expiry | [notes](videos/2026-01-15_HC6GKtqNZHc/notes.md) |

## What our data already says

- **The hedge alone costs carry, not friction.** SPY 5% OTM 75-DTE puts lose **−25.6%/month** on premium (10% OTM
  **−32.3%**) and pay in about 1 month in 5. Bid-ask is ~0.8% of mid, so fills are not the issue.
  [put_overlay_2026-09-20.md](../studies/put_overlay/put_overlay_2026-09-20.md)
- **On our book it moves nothing.** At budgets of ≤ 5%/yr, max DD changes ≤ 2pp. The 2022 must-pass fails when the
  hedge is gated on low VIX. The book's bad months are mostly not index crashes (corr with SPY 0.22). **The 7-DTE
  straddle is the bear leg (~13pp of DD).**
- **Far-OTM "more convexity per dollar" is a mid-price effect in our one direct test.** Event calls at 0.12Δ vs 0.25Δ:
  +19.5pp at mid → +1.9pp at fills (TEST_INDEX §2).
- **The certified index put-sale bucket already caps its own tail** with the 0.15Δ long leg (3 of 75 SPY trades
  at −100% of max loss). An overlay there is a crash-continuation bet, not insurance. The spec is in the Hermel notes
  ("Not tested, could be"), with a prior of NULL / UNDERPOWERED.

## Not covered yet

- Deep (1–5Δ) puts specifically, and any hedge bought in **high**-VIX states. Our overlay tested 5–10% OTM, gated on
  low VIX.
- VIX calls / VIX call spreads as the tail leg (closest review: AJ Brown's VIX double vertical,
  `data/theta_profits/strategies/vix_crash_hedge.md`, 2/5).
- A monetisation rule (sell the hedge into the spike). The Hermel 2020 example shows the payoff decays ~80% within
  four weeks of the low.
