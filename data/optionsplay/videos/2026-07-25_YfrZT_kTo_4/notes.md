# OptionsPlay — "The Three Filters That Make a Credit Spread Worth Trading" (Tony Zhang, 2026-07-25, 34 min)

_Reviewed 2026-09-22, the day 7 of our own credit spreads were retired for failing on cost._

## Verdict: 3.5 / 5 — the highest score any creator video has earned here, and the first published filter that survives our data

Still a platform demo (the "three filters" are what his Credit Spread Opportunity Report automates), and still
priced at the mid throughout. But the filters themselves are the right three, two of them match findings we paid
for, and the third **passes a pre-registered test on our own quotes**.

## The three filters

| @ | Filter | Our evidence |
|---|---|---|
| 20:19 | **1. Directional signal first** — only names his platform flags buy/sell (signal + relative strength + trend); a buy → bull put, a sell → bear call | Untestable as stated (proprietary). The family is tested and it does NOT rescue the structure on its own: our bullish-low-IV bull put is −4.8% month-weighted (t −0.87) even though every entry had a bullish trend |
| 24:01 | **2. Options liquidity — "we filter out 80–90% of the signals"** | ✅ **Strongly confirmed, and it is our single biggest cost finding.** Spread predicts outcomes far better than premium (R² 0.153 vs 0.027 gross / 0.005 net); the liquidity gate is what moved the earnings vol premium from dead to PARKED; and on 2026-09-22 thirteen screener spreads went from +3.8…+13.4% gross to −5.1…+5.9% net, with the worst being the thinnest chains (ASHR $0.12 credit vs $0.07 cost) |
| 19:02 | **3. Rank by PREMIUM-TO-WIDTH**, floor 2:1 risk-reward (credit ≥ 33% of width), prefer ~1.5:1 (≥ 40%) | ⭐ **TESTED 2026-09-22 and it PASSES** — see below |
| 15:11 | Corollary: **90%-win-rate spreads are "picking up pennies in front of a freight train"** — $9 risked per $1, and the fills at those strikes are bad | ✅ Agrees with our data and cuts against the wheel/CSP crowd. This is the failure mode of every spread we retired today |

## The test (`run_premium_to_width.py`, 27,404 spreads, 20 names, 395 Fridays, real fills, held to expiry)

**ARM A — his ranking with the structure held fixed (30Δ/20Δ bull put), quintiles of credit/width:**

| quintile | credit/width | entry IV | net ROC | win % | break-even win % |
|---|---|---|---|---|---|
| Q1 (cheapest) | 0.15 | 0.25 | **−2.96%** | 79.6 | 85.2 |
| Q3 | 0.20 | 0.29 | +3.59% | 79.7 | 79.8 |
| Q5 (richest) | 0.25 | 0.48 | **+4.07%** | 75.7 | 74.8 |

Top − bottom **+8.57pp, month-clustered t 3.74**, both halves (+10.07 / +6.69).
**Within-date** (cross-sectional, so the market-wide IV level is removed): **+7.64pp, t 4.15**, halves +10.35 / +4.23 —
and it works in both the low-VIX tercile (+9.17pp) and the high-VIX tercile (+7.84pp). **So it is name selection,
not regime timing.** The mechanism is visible in the IV column: credit/width is a proxy for how rich the name's
options are. Note the win rate FALLS as credit/width rises (79.6 → 75.7) while the payoff rises more — exactly his
argument, and the reverse of how most retail sellers pick strikes.

**ARM B — the coordinate check: same name, same date, only the wing moves** (0.25/0.20/0.15/0.10Δ long leg).
Net ROC is NOT monotone in credit/width (+2.98 / +3.10 / +2.66 / −0.04), and the realised win rate tracks the
break-even win rate within 0.5–3pp. **Dialling credit/width by changing your own width buys nothing** — which is the
caveat his presentation misses: the ratio informs when it varies ACROSS names, not when you dial it yourself.

Ledger status: Šidák p 0.00037 against a BH rank-1 line of 0.00038 at M=133 — it passes **by a hair**, and fails at
the stricter M=408. Call it SUPPORTED, one test, and re-test it before it sizes anything.

## What I would take

1. **A candidate filter for the spreads we just retired:** the names we killed today are the low credit/width ones.
   Ranking the survivors by credit/width, at a fixed 30Δ/20Δ structure, is the first published rule that has beaten
   our own data.
2. **Do not dial it with the wing** — ARM B is flat. It works as a cross-sectional chooser only.
3. His liquidity filter and his warning against 90%-win spreads are the same two lessons our cost work produced.
