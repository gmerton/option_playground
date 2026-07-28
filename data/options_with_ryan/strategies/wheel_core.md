# Wheel Core — CSPs → assignment → covered calls on mega-cap tech

> **Verdict:** Standard wheel mechanics, competently described, on a survivorship-blessed universe —
> but the headline income math (4%/month "to retire on $200K") doesn't survive his own on-screen examples.
> **Conviction 2/5 · Risk 6/10 · Tested: no**
> Source: `videos/wheel/2024-10-14_THpAzr-UKxo` ("The Wheel Strategy 101"). Portfolio shown: ~$600K, "up 50% for the year" (unverified).

## Mechanics (as stated)

- **Universe:** top-10/20 S&P mega-caps he "believes in": AAPL, AMZN, GOOGL, NVDA, TSLA, PLTR (higher risk), QQQ.
  Explicit anti-example: SNAP (multi-year downtrend, cheap ≠ wheelable). Min account $15–25K; "retire" target $200K+.
- **Put leg:** sell CSPs ~30 DTE (monthly cadence), typically **25–35Δ**, up to 37–42Δ when chasing the
  4%/mo income target. Get assigned → fine, "paid to dollar-cost average."
- **Call leg:** after assignment, sell covered calls ~30 DTE at a strike he'd happily sell at (~+8% above basis).
  Called away = double profit (premium + appreciation). Restart puts.
- **Income claim:** 3–5%/mo typical, 4%/mo the planning number; "25–35%/yr doing super-safe far-OTM" ; NVDA
  put example = 4.16%/mo at 37Δ; QQQ variant "safer," roughly 1/3 of his portfolio normally.

## What checks out

- The structural rules are orthodox and sane: only wheel stocks you'd own, monthly cadence, reject
  downtrending/cheap junk, CC strike above basis. Nothing exotic or hidden.
- He is honest that QQQ premium is thinner: his own on-screen math got **2.0%** on a 42Δ QQQ put and ~1.3% on
  the 34Δ call — and he concedes you need 40Δ+ and $400K to "retire" on QQQ.

## Red flags

1. **The retirement math requires the aggressive tail of his own range.** 4%/mo needs 37Δ+ puts on NVDA-class
   vol — that's a ~40% assignment rate on a name that can gap 20%. The "super-safe far-OTM" framing and the
   4%/mo framing are different strategies; the video slides between them.
2. **Premium yield ≠ return.** The 4.16% NVDA example is premium/collateral *if nothing happens*. No accounting
   for assignment marked-to-market below strike — the only loss mechanism the wheel has — anywhere in the video.
   The "12% in one month" example needs the stock to rally +8% first (contingent, capped upside counted as income).
3. **Survivorship universe:** the approved list is precisely the stocks that went up the most 2023–2025.
   Selection criterion is affinity ("I have Apple products"), not a testable screen.
4. **Compounding slippage:** 4%/mo = 60%/yr compounded, quoted next to "25–35%/yr" without noticing the gap.
5. Claims (portfolio +50% YTD, +$41K month) are account screenshots — no separable, auditable track record.

## Salvageable for us

- The universe rule (quality + uptrend only) and CC-above-basis discipline match how we already run CSPs.
- Realistic expectancy for 25–35Δ monthly wheel on mega-tech is a testable question our put-spread machinery
  can answer (short put ≈ put spread with 0Δ wing). Expect low-teens annual with equity-like drawdowns, not 48%+.

## Testability

**High (EOD-clean).** 30-45 DTE, 25–35Δ short puts + 20–30Δ CC after breach, on NVDA/AAPL/QQQ from Athena
options_daily_v3. Assignment layer needs stock-path accounting but no intraday data. Compare vs buy-and-hold
same names — the honest benchmark he never shows.
