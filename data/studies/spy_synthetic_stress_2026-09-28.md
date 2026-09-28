# Synthetic SPY puts 1993–2009: the 2008 stress scenario for the structure search (2026-09-28)

**Why:** the leg surface shows stress-regime 45-DTE puts with 0/33 losing episodes, but v3 starts in 2010, and no provider we hold has 2008 option chains. Here the put legs are priced synthetically from VIX with a fitted skew and settled on SPY's real 1993–2009 path.
**Script:** `run_spy_synthetic_stress.py` (pre-registration in the docstring). **Log:** `logs/spy_synthetic_stress.log`. **Scenario matrix for step 2:** `data/cache/spy_synthetic_puts_1993_2009.parquet` (682k rows: 40 put cells × 3 skew scenarios, plus a 2×-spread variant).

## Method and validation
- **IV model:** each cell's IV = VIX × exp(a + b·log VIX + skew residual), fitted on v3 put entries (Black-Scholes IV of the mid, T-bill rate, q = 2%). Spread model: log(ba/mid) vs log VIX. The strike is solved from the target delta.
- **Out-of-sample check** (fit 2010–17, predict 2018–26):

  | tenor | median mid error | synthetic ÷ actual credit |
  |---|---|---|
  | 30–45 DTE | 6–9% | 1.00–1.08 |
  | 7 DTE | 16–20% | 1.13–1.18 |

  **Bias factor** (actual ÷ synthetic net bp, STRESS 30/45-DTE) = **0.888** → every scenario credit is scaled by 0.888, as pre-registered.
- ⚠ **Short tenors are unreliable.** 7/14-DTE synthetic credits run about 15% rich. 1-DTE Friday entries span a weekend priced as one day, so after the fix below they are biased *negative*. Only 30/45-DTE carry weight.
- **Two bugs fixed after the first run, disclosed:**
  1. `X.skew` resolved to the pandas method, so the window tables were empty.
  2. Strategy stats now use one contract per week, entered Fridays (the certified cadence). Synthetic expiries are daily, so "one per expiry" had summed about 5 overlapping positions a week.

  Separately, 1-DTE Friday entries had rolled to a same-day settle and now settle on the next session.

## Result: STRESS-regime puts, one contract per week, central skew (bp of notional per contract)
| window | cell | mean/trade | lose % | worst trade | worst episode | cumulative | max DD |
|---|---|---|---|---|---|---|---|
| **v3 actual 2010–26** | P 45d 10Δ | +58.5 | 0% | +35 | +40 | +6,846 | 0 |
| **synthetic GFC 2007–09** | P 45d 10Δ | **+1.0** | 7% | **−1,997** | −1,406 | +67 | **−4,143** |
| synthetic GFC | P 45d 5Δ | +5.1 | 3% | −1,466 | −392 | +344 | −1,795 |
| synthetic GFC | P 45d 16Δ | −0.4 | 15% | −2,332 | −2,266 | −29 | −6,068 |
| synthetic GFC | P 30d 10Δ | −22.5 | 9% | −1,878 | −2,573 | −1,504 | −4,501 |
| synthetic 1993–2006 | P 45d 10Δ | +39.8 | 4% | −797 | +40 | +5,335 | −900 |

**The 2008 path (45d 10Δ):** Jun–Aug 2008 earned about +40 bp a trade. **September 2008 lost −4,000 bp across 4 trades** (worst −1,997 ≈ −20% of notional on one contract): the regime switched on, puts were sold at about 40% IV, and October fell ~30%. Then **October 2008 through March 2009 earned +78 to +119 bp a trade** at 50–80% IV. Over the full 2007–09 window it roughly breaks even.

**Skew sensitivity (GFC, 45d 10Δ):** thin skew (q10) gives cumulative −2,993 bp; rich skew (q90) +1,593. A 2× spread changes almost nothing. The result hinges on how rich OTM puts were in September 2008, which is the one thing we can't observe.

## What it means for step 2
1. **The certified stress-put edge does not disappear in 2008, but it can be erased for a whole cycle.** One regime-entry month ate a year or more of premium. The damage is concentrated in the **first weeks after the regime switches on**, before implied vol has caught up with the decline.
2. **Lower delta and longer tenor survive best:** 45d 5Δ stays positive with the shallowest drawdown. 30-DTE is worse than 45-DTE throughout the GFC.
3. **Sizing:** −4,143 bp is per single-contract stream. With about 6 contracts open at once (45 DTE, weekly entries), that is roughly **−6 to −7% of deployed notional**. The optimiser must size to survive this scenario, not to the 2010–26 drawdown of 0.
4. **Hypotheses the scenario raises (not tested):** a delay after the regime switches on, or wings bought only in the first N weeks of an episode. Candidates for the optimiser to evaluate.
