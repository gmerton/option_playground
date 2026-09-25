# 12-1 momentum portfolio (C): the academic baseline for buying stocks (2026-09-25)

Script: `run_momentum_portfolio.py` (pre-registered b20b0f6). Log: `data/studies/logs/momentum_portfolio.log`; table
`momentum_portfolio_2026-09-25.csv`.

## Verdict: UNDERPOWERED near-miss — PRIMARY t_NW 2.93 (bar 3), both halves positive, 12/16 years · the strongest stock-buying evidence in the ledger · not survivorship

Each month-end, buy the top decile of optionable names by their return from 12 months ago to 1 month ago, equal weight,
hold one month, 10 bp/side on turnover. Benchmark = the equal-weight portfolio of every eligible name. 180 months,
2011→2026-01; ~84 of ~837 names; turnover 31%/month.

| cell | momentum | EW universe | excess / mo | t_NW | halves | years + | alpha on EW (t) | max DD |
|---|---|---|---|---|---|---|---|---|
| **PRIMARY top decile 12-1, survivorship-free (chain_spot incl. delisted)** | +1.65% | +0.98% | **+0.67pp** | **2.93** | +0.38 / +0.92 | 12/16 | +0.56 (2.49), β 1.11 | 28.3% |
| top quintile 12-1 | +1.40% | +0.98% | +0.42pp | 2.64 | +0.29 / +0.53 | **14/16** | +0.44 (2.77), β 0.98 | 25.3% |
| top decile 6-1 | +1.46% | +0.98% | +0.47pp | 2.08 | +0.33 / +0.59 | 13/16 | +0.38 (1.71) | 31.4% |
| survivor panel top decile 12-1 (secondary) | +1.70% | +1.16% | +0.54pp | 2.34 | −0.00 / +1.01 | 12/16 | +0.39 (1.72) | 26.3% |

- **Method check passed:** chain_spot vs panel top-decile monthly returns correlate 0.96 over 180 months.
- **Not survivorship:** the survivorship-free run is *stronger* than the survivor panel (+0.67 vs +0.54pp; alpha t 2.49 vs
  1.72). Momentum is the opposite of a reversal test: dead names drag the *universe*, not the winners.
- **About +8%/year over owning everything**, with the top quintile the steadiest (14/16 years, alpha t 2.77, β ≈ 1.0).
  Every cell is positive in both halves. The miss is power: an edge of ~0.5–0.7%/month with this volatility needs
  ~20 years to reach t 3, and we have 15.
- **Where it hurts (the known crash risk):** the worst excess months are 2019-09 (−12.2, the momentum-to-value rotation),
  2023-01 (−9.1, the junk rally), 2021-03 and 2022-11; losing years 2011, 2016, 2021, 2023.
- **Exploratory:** a SPY > 200d filter makes it WORSE (excess +0.24pp, t 0.91; it sits out rebounds and then misses 2019/2023
  reversals). Don't add it.

## What it means for "a bread-and-butter way to buy stocks"
Compared with everything else we have tested:
- **Breakout:** month-weighted t −0.04; negative 2010–19 out of time.
- **Dip / pullback / confirmation entries:** no edge.
- **Momentum:** +0.67pp/month over the whole market, positive in both halves and 12–14 of 16 years, on a
  survivorship-free universe.

It clears no bar alone, but it matches a century of out-of-sample literature, which is the strongest prior any strategy
here has. Honest status: **SUPPORTED, not certified.** It is a candidate for the baseline stock sleeve, sized as such,
with a forward lockbox from 2026-10.
