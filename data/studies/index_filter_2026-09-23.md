# Qullamaggie's index 10/20-day filter on the house breakout [WL-5e] — 2026-09-23

**Verdict: NULL · YIELD REFRAME.** "Breakouts don't exist in a falling market" doesn't hold on 55,429 house breakouts,
2010–2026. Breakouts taken while QQQ's 10-day is below a falling 20-day are −0.86pp worse per trade, but not
significantly (month-clustered t −1.68), and the halves **flip sign** (+0.83 / −1.18). Skipping them makes the monthly
book slightly *worse* and its drawdown *larger*. The SPY > 200-day comparator also fails. Breakouts **below** the 200-day
did *better* (+1.18pp, t 1.33, halves flip), driven by V-rebound years.

This settles the Carter-vs-regime-feedback split for the breakout book. Carter's "SPY > 200 halves drawdown" doesn't
carry over to it. It agrees with the 2019–26 regime-feedback null and with the localisation sweep ([WL-2b]): market
state doesn't sort breakout outcomes.

Script: `run_index_filter.py` (pre-registration in the docstring). Log: `data/studies/logs/index_filter.log`. Local,
minutes, on `liquid_panel_2009.parquet`. Trade: close entry, day-low stop on the close, 20-EMA trail, max 60, % per
trade. State at the prior close.

| state | share | in-state mean | rest | diff | month-clustered t | halves (<2018 / ≥2018) |
|---|---|---|---|---|---|---|
| **PRIMARY: QQQ 10 < 20, both falling** | 11.0% | −0.45% | +0.41% | **−0.86pp** | **−1.68** | +0.83 / −1.18 |
| QQQ 10 > 20, both rising | 60.1% | +0.50% | +0.04% | +0.45pp | +0.77 | −0.56 / +0.67 |
| SPY < 200-day SMA | 22.7% | +1.23% | +0.05% | +1.18pp | +1.33 | −0.74 / +1.67 |

- **Per year (RED − rest):** 9 of 17 years negative, 8 positive, no run.
- **Monthly book** (equal-weight mean of each month's breakouts):

| book | months | mean per month-trade | t | max DD of cumulative | worst month |
|---|---|---|---|---|---|
| unfiltered | 201 | −0.66% | −2.84 | 164 | −7.24 |
| skip RED | 200 | −0.79% | −3.35 | 183 | −6.78 |
| skip SPY < 200 | 187 | −0.82% | −3.38 | 174 | −9.12 |

⚠ **Side fact worth knowing:** the per-trade mean is +0.32%, but the *equal-weight monthly* mean is **negative**
(−0.66%, t −2.84). The house breakout's positive average comes from a few very busy months (2020, 2025, 2026 carry
thousands of breakouts); the typical month loses. That's the "paying months" finding
(`project_breakout_regime_feedback`) seen from the 2010–26 side.
