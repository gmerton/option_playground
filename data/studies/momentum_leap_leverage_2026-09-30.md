# Momentum sleeve: LEAPs vs margin as the leverage vehicle (2026-09-30)

**Verdict: margin wins clearly. LEAPs lose −1.12pp/month to the same exposure held as stock on margin (t −5.41,
15/16 years) · MECHANISM: the spread, paid on ~⅓ monthly turnover.** Pre-registration: `run_momentum_leap_leverage.py`
docstring. Log `logs/momentum_leap_leverage.log`; months `logs/momentum_leap_leverage_months.csv`.

**Setup:**
- **Formation:** the certified sleeve (top decile 12-1, survivorship-free chain_spot, 2011–2026-01, 177 months).
- **LEAP arm:** a ~0.80Δ, ~1-year call, bought when the name enters at mid + 25% of spread. Held while the name
  stays in the decile, rolled under 180 DTE, sold when it leaves.
- **Control:** the same name-months as stock at the call's dollar delta (median leverage **2.46×**), financed at the
  T-bill + 1.5%.
- **Coverage:** name-months without a quotable LEAP (45% of requests) or a month-end mark were dropped from both arms.

| monthly | LEAP book | levered stock (same exposure) | unlevered momentum | SPY |
|---|---|---|---|---|
| mean | +2.27% | +3.39% | +1.72% | +1.20% |
| max drawdown | 76.5% | **82.8%** | 39.5% | |

**PRIMARY LEAP − levered stock: −1.12pp/month, t_NW −5.41**, halves −1.43 / −0.86, positive in 1 of 16 years
(2020). Decision rule (≥ −0.25pp and t > −2) → **margin is the cheaper leverage.**

- The two books move together (monthly correlation 0.99), so the gap is a steady drag, not noise. The median entry
  spread is 5.9% of mid, so 25% on each side ≈ 3% a round trip. At the sleeve's ~⅓ monthly turnover that is about
  1pp a month, essentially the whole gap. Time value and forgone dividends make up the rest.
- Even at the calibrated real-fill slippage (0.13 of spread instead of 0.25), the gap would still be about −0.6pp a
  month. The verdict doesn't depend on the cost model.
- ⚠ **Sizing warning, more important than the vehicle:** 2.5× leverage on this sleeve had an **83% max drawdown**
  (unlevered: 40%). Momentum's crash months (2011-08/09, 2020-03, 2022) compound under leverage. Leverage should be
  sized off the drawdown: about 1.25–1.5× keeps the historical worst near 50–60%.

**Consequence:** if the momentum sleeve is levered, use margin, modestly. No LEAP vehicle.
