# Profit-lock exits on the house breakout — 2026-09-20

**Question (Gabe):** the rule stop (entry-day low on the close, then the 20-EMA close trail) can hand back a
whole open gain — AMD was +10% in two days with the stop still at the entry-day low. Do breakeven / lock-in /
trim rules beat the plain trail?

**Data.** `run_profit_lock_study.py` → `profit_lock_2026-09-20.log`, `profit_lock_trades_2026-09-20.parquet`.
The house process exactly (precision-tier mask from `run_precision_tier_control.py`): buy the breakout CLOSE
(+10 bps), stop = breakout-day low judged on the close, risk floor 2%, hold cap 60. **1,968 trades, 554 names,
837 entry dates, 2019-10 → 2026-09.** Every arm runs on the same trades → paired diff vs BASE, t clustered by
entry date. All arms keep the 20-EMA close exit; rule changes take effect from the next close.

## Result (no cap / cap 20 — the honest reference for a right-tail book)

| arm | meanR | diff vs BASE | t | 2019–22 / 2023–26 | give-back* | max DD (R) |
|---|---|---|---|---|---|---|
| **BASE** 20-EMA close trail | +0.63 / +0.39 | — | — | — | 38.8% | 162 |
| **BE_2R** stop → entry after a +2R close | +0.64 / +0.40 | **+0.01** | 1.3 | +0.005 / +0.014 | 40.1% | 157 |
| BE_1R stop → entry after +1R | +0.55 / +0.31 | −0.08 | −2.0 | − / − | **46.2%** | 182 |
| LOCK_2R_1R stop → +1R after +2R | +0.53 / +0.33 | −0.10 | −1.6 | − / − | 30.6% | 174 |
| BE_EXT2 stop → entry once ≥ 2 ADR over the 20 EMA | +0.44 / +0.23 | −0.19 | **−2.8** | − / − | **59.0%** | 122 |
| EMA10_EXT2 10-EMA trail once ≥ 2 ADR extended | +0.16 / +0.13 | **−0.47** | **−4.8** | − / − | 33.7% | 184 |
| TRIM_2R sell half at +2R | +0.37 / +0.32 | −0.26 | −3.8 | − / − | 24.4% | 121 |
| TRIM_EXT2 sell half at 2 ADR extension | +0.30 / +0.26 | −0.33 | −4.2 | − / − | 27.1% | 97 |
| TRIM_EXT3 sell half at 3 ADR extension | +0.38 / +0.33 | −0.25 | −3.8 | − / − | 30.7% | 112 |

\* give-back = share of trades that CLOSED ≥ +1R at some point and still finished ≤ 0.

**Where the cost comes from.** Every lock/trim wins on the trades BASE loses (BE_EXT2 +547R summed on BASE ≤ 0)
and loses more on the 167 trades BASE takes to > 5R (−613R). The rules sell the tail to buy comfort.
2024–25 (the big-tail years) are where they bleed most (TRIM −0.56…−0.97R/trade).

**Cap-10 caveat.** At the harness's ±10R clip, TRIM_2R *beats* BASE (+0.07R, t 3.4). That is the clip, not the
rule: capping the base's tail at 10R is exactly the trim's effect, so the clip pre-applies it. The
precision-tier control note already set cap 20 / no cap as the reference for this book.

## Verdicts
- **BE_2R — NULL (harmless).** +0.01R, t 1.3, 7 of 8 years ≥ 0, slightly lower drawdown. Allowed as a comfort
  rule: once a trade has closed ≥ +2R, move the stop to entry. It neither adds nor costs.
- **BE_1R, LOCK_2R_1R — FAIL** (−0.08 / −0.10R). A +1R breakeven *raises* the give-back rate (46% vs 39%):
  it converts winners that would have dipped and recovered into scratches.
- **BE_EXT2, EMA10_EXT2 — INVERTED (vetoes).** "It's extended, tighten up" is the worst family tested
  (−0.19R t −2.8; −0.47R t −4.8). Extension is where the tail starts, not where it ends.
- **Trims — FAIL on expectancy, real on smoothness.** −0.25…−0.33R/trade (−40…−52% of total R) for −25…−40%
  max drawdown; return per unit drawdown falls (BASE 7.6, trims 6.0–6.7, BE_2R 8.0). Half size on every trade
  gets the same smoothing with no selection cost.

**Desk rule:** keep the entry-day-low stop + 20-EMA close trail; optionally BE after a +2R close. If the
give-back is unbearable, cut size at entry, not the stop afterwards.
