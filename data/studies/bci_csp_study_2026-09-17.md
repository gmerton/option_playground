# BCI cash-secured puts vs holding the stock at the same delta (2026-09-17)

**Question.** Alan Ellman (Blue Collar Investor, TraderLion 2026-09-06) sells weekly and 3–4-week OTM puts, and ITM
covered calls (the same payoff by put-call parity), on stocks passing a fundamental + technical screen, never
through earnings. Review: `data/traderlion/setups/bci_covered_calls_cash_secured_puts.md`. Three things tested:
1. Do his **public filters** make the puts better?
2. Does the put beat simply **holding the stock at the put's delta** on the same collateral, i.e. is there premium
   beyond direction?
3. His "most important rule": **no earnings before expiry**. And the seller's side of our RSI study: do puts on
   **RSI ≥ 70** names win?

**Set before running** (`run_bci_csp_study.py` docstring):
- **Data:** straddle pool (326 names with data), every Friday 2018-01 → 2026-02, bid/ask from `options_daily_v3`.
- **Tenors:** W = nearest 7 DTE; M = nearest 28 DTE. Hold to expiry, no management.
- **Strikes:**
  - **his rule:** OTM put nearest a 0.75%/week or 3%/month yield on collateral
  - **0.30Δ:** house comparator
- **Fills:** sell at mid − ¼ spread, $0.0065/share. Settle at intrinsic from the raw close (split-reversed yfinance,
  checked against the ATM strike: median gap 0.4%).
- **Benchmark:** `stock_d` = |entry delta| × stock move on the same collateral. `excess` = put − stock_d.
- **His filters:**
  - trend: EMA20 > rising EMA100, price ≥ EMA20
  - MACD histogram > 0
  - slow stochastic > 80
  - volume holding
  - 63-day return beats SPY
  - ATM IV 30–60%
  - no earnings from entry through expiry
  - Industry rank, analyst rating and the curated BCI list can't be rebuilt, so they're not tested.
- **Stats:** t clustered by entry week (W) or month (M). Bar |t| ≥ 3.

Scripts: `run_bci_csp_pull.py` → `data/cache/bci_csp/chain_*.parquet`; `run_bci_csp_prices.py`; `run_bci_csp_study.py`.
Full output: `bci_csp_study_2026-09-17.log`.

## 1. The put earns about what the stock would have, minus costs

| tenor · strike | trades | put return / trade | win | worst 1% | stock at same delta | **excess** (t) |
|---|---|---|---|---|---|---|
| W · his 0.75%/wk (~0.25Δ) | 100,914 | +0.03% | 82% | −15% | +0.07% | **−0.04% (−1.7)** |
| W · 0.30Δ | 101,205 | +0.06% | 79% | −19% | +0.12% | **−0.06% (−1.8)** |
| M · his 3%/mo (~0.33Δ) | 100,038 | +0.26% | 78% | −39% | +0.45% | **−0.19% (−1.4)** |
| M · 0.30Δ | 100,644 | +0.36% | 80% | −41% | +0.56% | **−0.20% (−1.4)** |

The put collects a 0.74%/week headline yield (his target). What it keeps is +0.03%. The rest goes to assignments
(22% of weeks) and the tail. Everything it does keep is **direction**: holding a quarter-share of the same stock
earned more, every tenor and strike.

**Fill sensitivity:**
- **At bid:** clearly negative (W excess t −4.2).
- **At a perfect mid:** excess ≈ 0 (W +0.03%, t 0.8; M ≈ 0).
- **Stocks ≥ $10 only:** unchanged (W excess −0.05%, t −1.8).

Best case, a short put on these names is a delta-equivalent stock position, not a premium harvest. That matches
`vrp_shortdte_names_study.md`: short-dated single-name premium is real gross and gone after costs.

**As a book** (W, his strike, 100% of collateral each week, compounded, 2018 → 2026-02):

| | CAGR | worst week | max drawdown |
|---|---|---|---|
| all pool names | +1.2% | −9.5% | −21% |
| **BCI filter** | **−1.4%** | **−28.9%** | **−34%** |
| SPY buy & hold | +10.5% | −15.1% | −32% |

## 2. His filters add nothing

| W · his strike | trades | put return | excess | within-week vs the rest |
|---|---|---|---|---|
| all | 100,914 | +0.03% | −0.04% | — |
| trend + MACD + stochastic + volume | 12,893 | +0.03% | −0.01% | put +0.01 (t 0.4) |
| **BCI full** (+ RS + IV 30–60% + earnings clear) | 3,416 | +0.05% | +0.01% | put −0.03 (t −0.5), excess −0.00 (t −0.1) |

Monthly is worse: BCI full +0.12% vs +0.26% for all names. Worst 1% is **−51%** vs −39%; within-week t −1.4. In
2022 the BCI monthly arm lost −1.3%/trade while the pool made +0.15%. The filter concentrates on high-momentum,
30–60%-IV names, which fall hardest in a de-rating. The March-2020 entries lost −15.5%/trade (pool −13.9%).

## 3. The earnings rule doesn't protect returns

| W · 0.30Δ | trades | put return | yield | worst 1% | excess |
|---|---|---|---|---|---|
| earnings clear | 77,531 | +0.05% | 1.06% | −17.8% | −0.05% |
| earnings in window | 7,039 | **+0.26%** | 1.78% | −22.3% | +0.02% |

Within-week, selling through earnings earned **more** (put +0.19 pp, t +3.6). That's not beyond direction (excess
t +1.3), and the monthly tenor agrees in sign (t +2.3). The rich pre-earnings premium more than paid for the gap on
average; the tail is somewhat worse (−22% vs −18%). **The rule is a risk preference, not a return edge.** Caveats:
the earnings table has no before/after-market timing (entry-day and expiry-day reports count as in the window), and
275 of 326 names have coverage.

## 4. RSI ≥ 70 puts: right sign, not confirmed

W · his strike: excess +0.06 pp within-week, **t +1.8**. W · 0.30Δ: t +1.0. Monthly: t +1.1. That's the direction
the RSI study predicted (extended names under-move, and the put buyer loses), but nowhere near the bar. On the
seller's side, costs eat most of what the buyer loses. **Not a tradeable filter.**

## Verdict

- **The core claim fails on a mechanical version of his public method.** Over eight years, weekly and monthly OTM
  puts on 326 optionable stocks earn about what holding the stock at the same delta earns, minus costs. At his
  weekly strike the whole-pool book compounds at +1.2%, and with his filters at −1.4%.
- **The ITM covered call is the same trade.**
- **Not tested:** the proprietary pieces (industry rank, analyst rating, the curated list) and his 20+ exit rules.
  A curated list could differ, but the burden is on the unshown track record.
- **What survives:**
  - **Hold-to-expiry short puts are a lower-beta way to own a stock, not an income stream.** Choose them only if
    you want that exposure.
  - **Liquidity and fills decide the sign:** bid fills are clearly negative.
  - **Skipping earnings changes the risk shape,** not the expected return.

**For the book:** no change to the ETF bull put spread, which is a separate result with a wing, 45 DTE and a 50%
take. This adds evidence against naked single-name weeklies.
