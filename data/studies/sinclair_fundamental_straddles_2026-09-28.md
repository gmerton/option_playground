# Sinclair: fundamental-factor straddle portfolios, S&P 100 ex-financials (2026-09-28)

Source: Euan Sinclair, *Positional Option Trading* (2020), as typed by Gabe. Each Friday, rank on P/E, P/B, market cap, P/CF, D/E, RoE and RoA; sell ATM straddles (second monthly expiry) on the top quartile and buy them on the bottom quartile, $10,000 notional each. Unstated in the book, so defaulted per Gabe: **one-week hold, delta-hedged daily**; held-to-expiry and unhedged are secondaries. Script `run_sinclair_fundamental_straddles.py` (pre-registered; plumbing fixes after the pre-registration: SEC facts per name with predecessor CIKs, a column-name bug, and a ≥ 20-names-per-Friday guard). ⚠ Universe = today's S&P 100 (survivor bias, declared).

```
universe 85 names; straddles with fundamentals 61,455 over 841 Fridays (2010-01-08 -> 2026-02-13); median premium 7.0% of spot; median entry cost 1.0% of premium; dropped for no exit quote 0.3%
units: weekly portfolio P&L in bp of $10,000 notional per straddle (long-quartile mean + short-quartile mean); to-expiry = same cohorts held to expiry (entry cost only, NW lag 9)

  P/E   NET -46.08bp/wk t -18.66 halves -52.19/-40.28 yrs+  0/17 | gross  -0.92 (t -0.41) | long leg -17.19 short leg -28.89 | unhedged -42.01 (t -16.42) | to-expiry -109.47 (t -4.68) | ~18/quartile 
  P/B   NET -45.32bp/wk t -18.49 halves -49.00/-41.77 yrs+  0/17 | gross  +0.41 (t +0.19) | long leg -20.37 short leg -24.94 | unhedged -44.73 (t -18.00) | to-expiry  -96.59 (t -4.05) | ~19/quartile 
  P/CF  NET -43.74bp/wk t -17.88 halves -47.65/-40.03 yrs+  0/17 | gross  +1.46 (t +0.64) | long leg -16.07 short leg -27.66 | unhedged -40.07 (t -15.58) | to-expiry -126.21 (t -4.39) | ~18/quartile 
  MCAP  NET -42.03bp/wk t -19.48 halves -50.61/-33.76 yrs+  0/17 | gross  +4.57 (t +2.26) | long leg -28.02 short leg -14.00 | unhedged -40.99 (t -17.61) | to-expiry  -36.21 (t -1.43) | ~19/quartile 
  D/E   NET -47.19bp/wk t -18.07 halves -55.04/-39.64 yrs+  0/17 | gross  -1.36 (t -0.65) | long leg -20.91 short leg -26.29 | unhedged -48.48 (t -16.50) | to-expiry  -19.48 (t -1.21) | ~19/quartile 
  RoE   NET -41.13bp/wk t -19.25 halves -45.05/-37.41 yrs+  0/17 | gross  +2.50 (t +1.34) | long leg -22.57 short leg -18.55 | unhedged -41.21 (t -18.09) | to-expiry  -60.54 (t -3.76) | ~17/quartile 
  RoA   NET -43.02bp/wk t -20.58 halves -47.60/-38.67 yrs+  0/17 | gross  +2.30 (t +1.25) | long leg -22.93 short leg -20.09 | unhedged -40.73 (t -18.21) | to-expiry  -74.56 (t -4.26) | ~18/quartile 

NET by year (bp/wk):
trade_date  2010  2011  2012  2013  2014  2015  2016  2017  2018  2019  2020  2021  2022  2023  2024  2025  2026
P/E        -60.1 -52.4 -51.7 -48.3 -49.5 -61.5 -59.9 -36.3 -34.8 -29.7 -48.5 -28.1 -48.4 -29.2 -40.5 -60.2 -60.4
P/B        -56.9 -48.4 -54.5 -50.2 -53.7 -57.0 -37.5 -35.1 -34.9 -34.2 -57.0 -47.9 -42.6 -27.5 -36.5 -50.8 -59.5
P/CF       -53.2 -48.6 -47.3 -47.5 -53.1 -58.2 -38.8 -35.9 -29.9 -29.5 -37.5 -42.5 -55.5 -28.4 -36.2 -58.2 -58.9
MCAP       -41.5 -46.8 -56.0 -52.3 -61.9 -74.7 -37.7 -31.9 -46.2 -28.6 -38.9 -44.5 -33.3 -22.7 -22.1 -31.9 -48.4
D/E        -48.6 -58.0 -59.0 -51.7 -57.4 -69.4 -61.8 -33.0 -35.9 -35.7 -73.8 -24.3 -39.9 -25.1 -29.9 -46.1 -82.6
RoE        -46.0 -48.9 -52.9 -42.0 -53.5 -47.6 -26.7 -43.0 -35.5 -41.5 -45.3 -50.1 -28.7 -25.0 -22.9 -44.4 -80.3
RoA        -43.7 -46.6 -52.4 -43.8 -57.0 -56.0 -35.3 -44.7 -40.2 -36.6 -44.7 -55.5 -37.8 -27.0 -22.9 -41.4 -60.9
```

## Reading

- **Gross, there is nothing to harvest.** Every factor's mid-to-mid weekly spread is within ±5bp of notional per
  week, and none reaches |t| 3. MCAP comes closest (+4.57bp, t 2.26, in the book's direction: sell the largest, buy
  the smallest), still below the bar.
- **Net, every factor loses about 41–47bp of notional per week (t ≈ −18 to −21), 0/17 years positive.** That is the
  friction: a ~45-DTE ATM straddle costs ~1% of premium to enter, and the portfolio round-trips a long and a short
  straddle every week. Unhedged is the same.
- **Held to expiry** (one cost per cohort) the losses shrink but stay negative: −19 to −126bp per cohort, 5 of 7 with
  t ≤ −3.8.
- Survivor bias affects both legs equally and cannot explain a gross spread of zero.

**Verdict: NULL (gross) · INVERTED as traded (net t ≈ −19) · MECHANISM.** On mega-caps, fundamentals carry no
vol-pricing error the option market leaves on the table. The weekly re-formation turns a zero-edge sort into a pure
cost drain. This is the third single-stock vol sort to fail after Goyal–Saretto and Vasquez, and the first where even
the gross spread is zero.
