# calculator.py's pre-earnings vol gates, tested (2026-09-20)

**VERDICT: NULL for both volatility gates · MECHANISM · METHOD.** Of the screener's three gates, the
only one that adds value is the **liquidity** gate — and it works for a reason the script never
states. The two gates that carry its actual thesis do nothing or hurt.

**Source.** `~/Downloads/.../trade calculator/calculator.py` (Feb 2025), a live GUI screener with no
backtest in it, thresholds hardcoded from a video with no stated derivation. `yang_zhang` and
`build_term_structure` reimplemented verbatim, including the spline's endpoint clamping.

**Data.** 3,163 of the 4,477 earnings events (those with ≥3 expiries for a term structure), 284
names. Scored as the premium study was: short ATM straddle into the print, % of spot, at MID and at
the BID.

## The gates

| gate | n | share | MID | vs base | **BID** | **vs base** |
|---|---|---|---|---|---|---|
| — no gate — | 3,163 | 100% | +0.598 | | **−0.065** | |
| **avg_volume ≥ 1.5M** | 2,349 | 74% | +0.595 | −0.004 | **+0.163** | **+0.228** |
| **iv30_rv30 ≥ 1.25** | 1,534 | 48% | +0.462 | −0.136 | **−0.318** | **−0.253** |
| ts_slope ≤ −0.00406 | 2,862 | 90% | +0.616 | +0.018 | −0.029 | +0.036 |
| ALL THREE (the recommendation) | 973 | 31% | +0.536 | −0.062 | +0.086 | +0.151 |

- **`iv30_rv30 ≥ 1.25` is actively harmful** (−0.253pp at the bid). Its quintiles are non-monotonic
  and the **lowest** bucket is the best at both MID (+1.167) and BID (+0.618) — *cheap* IV relative to
  realised beat rich IV, inverting the gate's premise.
- **`ts_slope` barely filters** — it passes 90% of earnings events, because the front expiry is
  almost always in backwardation into a print. A gate that admits nine events in ten is a formality.
- **`avg_volume` carries the whole recommendation.** It is the only gate that turns the bid-side
  premium positive, and its quintiles sort **monotonically at the BID** (−0.760 → +0.334) while being
  **flat at MID** (~0.5–0.7 throughout). It does not predict the premium; it predicts the **cost of
  capturing** it.

## The regression says the same thing, precisely

| | pnl_MID (gross) | pnl_BID (net) | net + spread |
|---|---|---|---|
| `iv30_rv30` | t **0.07** | t −0.02 | t −0.14 |
| `ts_slope` | t 3.29, **coef +43** | t −1.37 | t −0.61 |
| `log_vol` | t 0.78 | t **3.16** | t 1.57 *(absorbed)* |
| `implied_pct` | t **8.43** | t −0.48 | t 0.52 |
| **`spread_pct`** | — | — | **t −5.04** |
| R² | 0.027 | **0.005** | 0.012 |

- **`iv30_rv30` is inert** — t 0.07 gross, −0.02 net. The script's central metric has no relationship
  to the premium in either direction.
- **`ts_slope`'s coefficient is the wrong sign for the gate**: +43 at mid means a *flatter* curve
  predicts a *larger* premium, while the gate demands a steeply negative slope.
- **`implied_pct` drives gross premium (t 8.43) and drives the spread (t 11.23).** They cancel, giving
  t −0.48 net. That is the exact mechanism behind the earlier finding that the implied-move sort
  inverts at the bid.
- **Volume is the only net predictor and it works entirely through the spread** — adding `spread_pct`
  knocks it from t 3.16 to 1.57, and corr(log_vol, spread) = −0.334.

## ⭐ The finding worth keeping

Regress the **spread itself** on the same variables and R² is **0.153** — against **0.027** for gross
premium and **0.005** for net. `log_vol` t −17.11, `implied_pct` t +11.23.

**The cost of trading these events is five to thirty times more predictable than the profit.** That is
the session's thesis stated as a number: on this data you can forecast what a trade will cost far
better than you can forecast what it will earn — so the tractable lever is cost selection, not
signal selection.

## What to take from the script

Keep the **liquidity filter**, which is the one empirically supported piece, and understand it as a
spread proxy rather than a quality proxy. Drop `iv30_rv30` — it is inert at best and inverted at the
quintile level. Treat `ts_slope` as descriptive; it does not discriminate at an earnings print.
