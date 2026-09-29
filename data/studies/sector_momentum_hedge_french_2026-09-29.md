# Industry-momentum 12-1 spread as a bear-market HEDGE, Ken French industries 1927→2026 (2026-09-29)

## Pre-registration (written BEFORE any spread return was computed; do not edit this section after the results)

**Why.** Audit List A #6 (`audit_top_down_2026-09-25.md`), audit step 3 item 3. The SPDR-sector 12-1 spread
(`run_sector_momentum_spread.py`, 2026-09-24) has ~zero return but paid in 3 of 4 bears (2008 +25%, 2020 +16%,
2022 +31%; 2000–02 −10.3%) and survived de-meaning as a book overlay (`run_sector_overlay_test.py`). Four episodes is
anecdote. Ken French's industry returns reach back to 1926 and give ~10 episodes. Breadth is OFF right now; this is
the only bear-leg candidate left in the ledger.

**Data.** `data/cache/french/10_Industry_Portfolios.csv` (value-weighted monthly, 1926-07 → 2026-08, CRSP 202608)
and `F-F_Research_Data_Factors.csv` (Mkt = Mkt-RF + RF), downloaded 2026-09-29; loader `src/lib/studies/french_data.py`.
10 value-weighted industries ≈ the 9–11 SPDR sectors, so K = 3 keeps the same breadth as the ETF test.

**Spread (fixed; the ETF test's primary cell).** For holding month h: rank industries on cumulative return over
months h−12 … h−2 (12-1, skip the latest month); long the top 3, short the bottom 3, equal weight, dollar-neutral.
Net of 20 bp/month + 0.25%/yr borrow, as in the ETF test. First holding month 1927-07.

**Bear episodes (defined from the market series only, listed before any spread return was seen).** Drawdowns of
the monthly Mkt total-return index of ≥ 20%, peak → trough, where an episode ends when the index regains its peak:

| # | peak | trough | market DD | seen before? |
|---|---|---|---|---|
| 1 | 1929-08 | 1932-06 | −83.7% | new |
| 2 | 1946-05 | 1947-05 | −24.3% | new |
| 3 | 1961-12 | 1962-06 | −23.1% | new |
| 4 | 1968-11 | 1970-06 | −33.6% | new |
| 5 | 1972-12 | 1974-09 | −46.5% | new |
| 6 | 1987-08 | 1987-11 | −29.9% | new |
| 7 | 2000-08 | 2002-09 | −45.0% | ETF test (−10.3%, failed) |
| 8 | 2007-10 | 2009-02 | −50.3% | ETF test (+) |
| 9 | 2020-01 | 2020-03 | −20.2% | ETF test (+) |
| 10 | 2021-12 | 2022-09 | −24.8% | ETF test (+) |

Episode window = holding months peak+1 … trough (the months the market was falling). ⚠ 1937–38 sits inside
episode 1's underwater period and is not a separate episode under this rule.

**Primary (both required).**
1. **Pays in bears:** the spread's cumulative net return over the episode window is **> 0 in ≥ 7 of 10** episodes.
   (Since 3 of the 4 seen episodes were positive on ETFs, this effectively needs ≥ 4 of the 6 new ones.)
2. **De-meaned drawdown cut:** host = the market; sleeve = the spread with its full-sample mean subtracted, scaled to
   50% of the market's full-sample volatility (the overlay test's primary size). Host + sleeve has a **smaller
   max drawdown inside the episode window than the host alone in ≥ 7 of 10** episodes.

**Label condition (required to call it more than a beta hedge).** The spread beats its **beta-equivalent market
short** (−β × market, β from the full-sample OLS of spread on Mkt) over the episode window in ≥ 7 of 10 episodes.
Pass 1+2 without this → "hedge, but no better than a cheaper index short".

**Reported, not part of the bar:** full-sample mean / t / β / alpha; per-decade mean (the carry); the 12 months after
each trough (momentum crashes happen in rebounds, e.g. 1932, 2009); the 6-new-episode count on its own.

**Caveats stated up front.** 20 bp/month is optimistic for the 1920s–70s (no ETFs; industry portfolios are not
tradeable instruments); the test is about the *hedge property*, not a live cost. Monthly data understate intra-month
drawdowns (1987 is one month). One cell, no grid.
