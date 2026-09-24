# Same-day theme co-breakouts (Corsellis "group confirmation") [WL-5h] — 2026-09-23

**Verdict: NULL (leans Corsellis's way, not significant) · YIELD REFRAME.** Breakouts on days when ≥ 30% of the
industry also breaks out beat lone breakouts on the same date by **+1.61pp per trade on the 20-EMA exit, t 1.80**.
Both halves are positive, but it's well short of |t| ≥ 3 and 2020-driven (+8.8pp that year). At fixed horizons the gap
vanishes (10d +0.01, 21d +0.51), and at 63 days it tips slightly toward lone names (−0.57, t −0.42), the rotation
study's direction. Win rates barely differ (34.0% vs 31.9%, t 1.14). So it's neither the "win rate up, expectancy
down" split the prior expected, nor a real edge.

Script: `run_theme_cobreakout.py` (pre-registration in the docstring, from the Corsellis review, version A).
Log: `data/studies/logs/theme_cobreakout.log`. Local, minutes.
- **Pool:** house breakouts (20d-high close, RVOL ≥ 1.8, above the 50/200 SMA), liquid panel 2019-10 → 2026-09.
  11,506 breakouts in 101 industries (`data/ticker_industry_map.csv`, groups ≥ 5).
- **Arms:** CONFIRMED 3,537 · LONE 3,492 · middle 4,477.

| CONFIRMED − LONE, same-date paired (661 dates) | diff | t | halves (<2023 / ≥2023) |
|---|---|---|---|
| **PRIMARY: 20-EMA trail, % per trade** | **+1.61pp** | **1.80** | +2.36 / +1.07 |
| R (stop floor 2%, cap 20) | +0.15 | 1.40 | +0.16 / +0.15 |
| fixed 10d | +0.01 | 0.02 | +0.52 / −0.36 |
| fixed 21d | +0.51 | 0.88 | +0.04 / +0.84 |
| fixed 63d | −0.57 | −0.42 | +0.73 / −1.50 |

- **Per year (20-EMA, pp):** 2019 +1.3, **2020 +8.8**, 2021 −0.2, 2022 +0.2, 2023 +1.2, 2024 +1.7, 2025 −0.2,
  2026 +1.7.
- **Theme-day control:** CONFIRMED breakouts vs same-group names that did *not* break out that day, same close and
  same stop %: +1.12pp (t 1.78), halves +1.84 / +0.56. Given the theme is running, the breakout itself adds about as
  much, which is not significant either.

## Reading

Group confirmation is at most a small, 2020-heavy tilt on the trend-following exit, and nothing at fixed horizons.
It doesn't clear the bar, and it doesn't reverse the rotation study (weak-group breakouts ahead at 63d). The
intraday version B (his actual 5-min ORB rule) isn't worth running: ORB triggers are NULL/INVERTED here at every
resolution tested, and B would be power-limited to ~150 curated sessions.
