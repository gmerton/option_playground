# Short interest as a filter on the house breakout [BB-1] — 2026-09-23

**Verdict: NULL, leans negative (the "informed shorts" side, not the "squeeze fuel" side) · YIELD MECHANISM.**
The first short-interest test in the ledger. Breakouts in heavily shorted names (days-to-cover top quintile) did
**worse** than same-date breakouts in lightly shorted names: **−0.55pp per trade, t −1.40**. Both halves are
negative (−0.45 / −0.62), but it's short of the bar and year-dependent. The **squeeze variant** (high DTC plus a
heavy-volume breakout, i.e. forced covering) is *more* negative, not less: −1.33pp (t −1.48). Off-breakout, the
classic short-interest anomaly is faintly there too (top vs bottom DTC quintile, 20-day forward, −0.32pp, t −1.48,
all in the back half). High short interest isn't fuel for our breakouts; if anything the shorts are mildly right.

Script: `run_short_interest_breakouts.py` (pre-registered in the docstring). Log:
`data/studies/logs/short_interest_breakouts.log`. Trades: `logs/short_interest_breakouts_trades.csv`. Data: new
**`data/cache/short_interest.parquet`** — FINRA bi-monthly SI via Polygon, 3.87M rows, 44,921 tickers, 2017-12 →
2026-08 (`run_short_interest_pull.py`; the endpoint 429s when rushed, so it's paced at ~12 s). Local, minutes.

## Spec

- **Measure:** days to cover (SI ÷ average daily volume); there's no float history. Ranked cross-sectionally among
  liquid-panel names in each report.
- **⚠ Publication lag:** a report is usable only from settlement + 8 business days, and each breakout uses the
  latest report published by t−1.
- **Trade:** house breakouts (20d-high close, ADR ≥ 3, eligible), 2018-02 → 2026-09, 44,986 with a published report.
  Close entry, day-low stop on the close, 20-EMA trail, % per trade.

## Results

| arm | n | mean % | median % | win | held the level |
|---|---|---|---|---|---|
| HIGH DTC (top quintile) | 6,590 | +0.21 | −3.35 | 26.9% | 12.9% |
| LOW DTC (bottom quintile) | 11,628 | +0.92 | −3.25 | 28.0% | 13.7% |
| middle | 26,768 | +0.26 | −3.19 | 27.1% | 12.8% |

| cell (same-date paired) | diff | t | notes |
|---|---|---|---|
| **PRIMARY: HIGH − LOW** | **−0.55pp** | **−1.40** | 1,321 dates; halves −0.45 / −0.62 |
| held-the-level share | +0.6pp | +0.71 | |
| squeeze: HIGH DTC & RVOL ≥ 2 − LOW | −1.33pp | −1.48 | 634 dates |
| DTC rising (≥ 1.25×) − falling (≤ 0.8×) | −0.19pp | −0.54 | |
| classic anomaly, all names, 20d fwd, top − bottom DTC | −0.32pp | −1.48 | 108 dates; halves −0.01 / −0.60 |

**Per year (primary, pp):** 2018 +0.8, 2019 +1.0, **2020 −3.0**, 2021 +0.9 (the meme year is *positive*, as the
squeeze story predicts, but it's one year), 2022 −1.0, **2023 −3.1**, 2024 −1.4, 2025 +0.6, 2026 +1.0. Mixed, no run.

## Reading

- The forced-buyer story (shorts must cover on a breakout) doesn't show up on liquid names. Among $50M+ ADDV
  stocks, days to cover is rarely extreme enough for covering to dominate, and the squeeze cell is the worst one.
  Squeezes live in small caps, which this panel excludes (same blocker as the HTF / dilution fade).
- Direction and size agree with the academic short-interest anomaly (high SI → underperformance), but the effect is
  small here and not significant.
- Not a filter to add. A weak veto on high-DTC breakouts is the most the data allows, and it doesn't clear the bar.
