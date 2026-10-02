# Is a diversified basket of put spreads smoother than the same exposure in SPY? (2026-10-01)

**Verdict: FAIL. The basket is LESS smooth than simply holding its market exposure in SPY.** Sharpe 0.59 vs 1.07,
difference -0.48 (95% block bootstrap [-1.13, +0.09]). Against the same names held at the spreads' delta it is
significantly worse: -0.61, 98.3% interval [-0.97, -0.19]. Script `run_putspread_basket_smoothness.py`
(pre-registered 91c0a13), log `logs/putspread_basket_smoothness.log`.

Sample: the 20-name Friday 30/20-delta bull put study (real bid/ask fills, held to expiry, 28 DTE), 345 Fridays,
85 months, 2019-02 -> 2026-02. One spread per name per Friday at equal max loss, four overlapping weekly cohorts.

| arm | mean / month | vol / month | **Sharpe** | % months up |
|---|---|---|---|---|
| A basket (all names) | +3.86% | 22.6% | **0.59** | 67% |
| T5 top-5 by credit/width | +6.70% | 26.0% | 0.89 | 73% |
| B1 same names at delta | +7.17% | 20.7% | 1.20 | 68% |
| **B2 SPY at the same dollar delta** | +5.33% | 17.2% | **1.07** | 69% |

Returns are on committed max-loss capital (the whole collateral at risk), so the absolute levels and drawdowns
describe a 100% allocation and are not meaningful as sizes. Sharpe is scale-free and is the test.

- **Where the spreads help:** the crash month. In March 2020 the defined risk capped the basket at -67% of its
  collateral, against -90% for SPY at the same dollar delta.
- **Where they hurt:** the grind. 2022's slow decline cost the basket -194% (summed monthly) against -69% for SPY.
  Spread after spread went to max loss as the names fell through the short strikes month after month, and
  diversification did not help because they all fell together.
- The credit/width top-5 (S2) is closer to SPY (-0.18) but not better.
- "% months positive" is the retail feel of smoothness, and it is the same (67-73%) in every arm. The win rate is not
  extra smoothness. It comes bundled with larger losing months.

⚙ Disclosed implementation fix: the first run took SPY prices from SPY's own spread rows and silently dropped 57% of
the Fridays, including March 2020 (log kept as `..._run1_BUGGY.log`; its verdict was also FAIL, -0.33). The fix
takes SPY closes from the price panel, which starts in 2019, so 2018 is out of both arms.

## Reading
For a parking-lot sleeve, the same market exposure held in SPY (or the certified momentum sleeve) is smoother than a
diversified put-spread basket, and costs less to run (no 4-leg fills). If the goal is "earn something while waiting",
the evidence favours T-bills plus the calm weekly SPY put (t 7.1, the one premium sale that beat its own beta), sized
to a crash-week loss budget.
