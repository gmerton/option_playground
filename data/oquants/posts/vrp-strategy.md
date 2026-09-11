# VRP Strategy (posted 2025-06-02) — video `MAQBCz9ChkY`

**Thesis.** Implied vol overstates subsequent realized vol on average. It's a risk premium paid by insurance buyers, lottery-ticket speculators and mandate-constrained net buyers to a thin pool of sellers who bear jump risk. It's most reliable on **diversified ETFs**, not single stocks (the video shows AAPL where IV under-priced RV for two years, so short straddles lost).

**Measure (per ETF).** A rolling short-ATM-straddle backtest with a positive mean and win rate above ~60%. A rolling IV − subsequent RV series with a positive mean. Option volume as a demand/liquidity tilt. **IV percentile: sell at LOW-to-moderate IVP.** The video's regression and deciles show the top two IVP deciles are the only consistently negative ones, which contradicts "sell high IV". Avoid steep backwardation; contango or flat is favorable.

**Model (video).** A universe of ETFs with 20-day option volume ≥2,500. Features: log(IV30/RV30), 1y IV percentile, and their Flat Fwd Ratio (R² ≈ 1%, stronger than IV/RV). A linear regression with a train/test split, trading only when predicted return is ≥8% (a few hundred trades a year). It holds up on the test set. A logistic variant did not generalize, and he says so.

**Trade.** Retail default is a **wide iron condor**: sell 25-30Δ strangle, buy 1-5Δ wings, 30-45 DTE, no delta hedge. Alternative: a short straddle or strangle with delta hedging (band ±5-10Δ or ~15-20% of controlled shares, checked once or twice a day). Skew and shadow delta: lean strikes up (e.g. 30Δ put / 20Δ call) for the vol-down-on-rally effect. Sizing: 1-5% margin per trade (up to 10%); VRP book 40-60% of the account; stress-test a −20% gap with an IV spike.

**Manage.** Close or roll ~7 DTE. **Exit on IVP > 90-95% or a sharp term-structure inversion**, even at a loss. Profit targets are secondary. Leg out of the short strangle first if the full spread won't fill.

**Also in the video.** "Day-zero mentality": would I open this trade today? If not, exit whatever the P&L. Hypothesis → falsification → cheapest structure → Kelly-fraction sizing. Risk premia are the foundation; inefficiencies are opportunistic (example: a China ETF with IV 68 vs RV 52, 30→60 FF ≈ 0.8, rich vs SPY and vs a peer China ETF; short straddle closed in 3 days when IV hit the 50% target).

**Claimed stats (post chart).** Mean 17.1% / sd 55.1% / min −180% / win 64.4% per trade on their ETF short-vol backtest (2023-2025); ETF VRP mean 18.45 pts.

**Our cross-check.** Low-IVP-better matches our QQQ and IWM bull-put studies (IV pct ≥80 = VETO; best band 30-60). Our SPX condors and QQQ/SPY bull puts are the surviving short-vol legs after costs (playbook review Sept 2026). ⚠ Their Flat Fwd Ratio ≠ our `fvr_put_30_90`. Test idea: an ETF short-straddle or condor panel gated on log IV/RV + IVP<80 + term structure, with the house cost model.
