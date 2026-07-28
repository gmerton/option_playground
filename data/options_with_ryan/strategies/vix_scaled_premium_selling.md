# "Swing Trading" — VIX-scaled allocation + short-premium entries (CSPs, bull put spreads, CCs)

> **Verdict:** Despite the title, this is not directional swing trading — it's the wheel's put side plus
> bull put spreads, sized by a VIX ladder that goes ALL-IN (plus outside cash) when VIX > 30. The ladder has
> a defensible buy-fear kernel but no exit half, and the "$24,199 in 30 days, 88% win rate" is exactly what
> unstressed short premium looks like right before it isn't.
> **Conviction 2/5 · Risk 7/10 · Tested: no**
> Source: `videos/swing/2025-02-07_FPDDV_R55tI` ("$24,000/month swing trading strategy").

## Mechanics (as stated)

1. **Universe:** high-FCF, upward-drifting charts (NVDA in; AMD out — FCF < debt, 6% margins, flat/down chart).
2. **VIX allocation ladder (2025 revision):** VIX 10–12 → ~20% invested; 12–15 → 20–60%; 15–20 → ~80%;
   20–30 → 100%; **30+ → everything in, plus move savings into the brokerage.** Rationale: fear = discount;
   he cites Aug-5-2024 (VIX 67 print) as the template.
3. **Entries via Bollinger bands:** long bias at/below the lower band; above the upper band, do nothing or
   keep put strikes inside the bands.
4. **Structures:** CSPs 25–35Δ, 30–45 DTE, target 3–5%/mo (PLTR example: 29Δ ≈ 3.2%); **bull put spreads**
   for small accounts: ≤20Δ short, 30–45 DTE, ~5-wide, close at 25–50% max profit, manage before expiry week;
   **covered calls** 20–30Δ, 7–14 DTE.
5. Claimed result: +$24,199 net in 30 days, "88% gain/loss ratio," "win 9 of 10, losses very very small."

## What checks out

- The bull-put-spread parameters (≤20Δ, 30–45 DTE, 25–50% PT, exit before expiry week) are textbook-sane and
  match structures we run and have tested ourselves.
- The FCF-vs-debt universe screen is a real, checkable criterion — the one fundamental gate across his videos
  that's actually mechanical.
- "Buy fear, sell greed" scaling in *direction* is defensible; VIX 10–12 → keep cash is a fair complacency guard.

## Red flags

1. **The ladder is all-accelerator, no brakes.** Full allocation at VIX 20–30 and everything-plus-savings at
   30+ assumes every vol spike is 2020/Aug-2024 (instant V-recovery). In 2008 VIX held >30 for ~6 months while
   the market halved — this ladder is fully invested, in short puts, the entire way down. No de-risking rule,
   no stop, no regime distinction between a 3-day spike and a repricing.
2. **"Win 9 of 10, small losses" is the short-premium siren song.** 88% win rate over 30 bullish days says
   nothing about expectancy; the distribution's left tail hasn't been sampled. (Same critique as every
   theta_profits interviewee — and his own account was −18% two months after this video, per the March 2026
   underwater-CC video.)
3. **"Swing trading" branding on an income book** — win-rate and monthly-income framing borrowed from premium
   selling, marketed as trading skill. The $24K screenshot is one account, one month, unverifiable.
4. Macro justification ("very bullish because pro-business administration") is vibes, and the Bollinger
   containment stat is by construction.

## Relevance to us

- The VIX ladder is the interesting artifact: it's a crude cousin of our regime gates, but **sizing-only**
  (our gates switch *structure*; his scales *exposure*). Testable head-to-head: VIX-laddered 25–35Δ CSP book
  vs our 50MA×VIX regime switching on the same underlyings — does exposure scaling alone capture the regime
  edge, or do you need the strategy switch?
- His observation that CSP entries "work" above the upper Bollinger band iff strikes stay inside the bands is
  an implicit strike-placement rule worth one cheap test on SPY/QQQ.

## Testability

**High (the sizing question); medium (the claims).** The ladder + 25–35Δ 30–45DTE CSP book is EOD-clean on
Athena data across 2018–2025 — crucially including 2022, where "100% in at VIX 20–30" meets an 11-month bear.
His personal P&L claims are untestable by design.
