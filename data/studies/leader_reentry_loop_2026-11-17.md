# Re-entry loop on fresh leaders (2026-11-17)

**Verdict: INVERTED (primary) · NULL vs buy-and-hold · YIELD: MECHANISM.** On the full population of fresh
52-week-high names, re-entering after a 21-EMA exit makes things **worse** than a single trip, and no management
arm beats buy-and-hold. Buy-and-hold itself is roughly SPY.

| | pre-registered (log excess) | post-hoc arithmetic excess | liquid panel, arithmetic (robustness) |
|---|---|---|---|
| **B1 − A (PRIMARY)** | −2.43%, t −9.06, halves −/−, 15/15 yrs | −1.30%, t −4.93, 14/15 | −1.16%, t −3.15, 12/15 |
| B1 − C | +4.58%, t +5.87 (vol-drag artefact) | +0.20%, t +1.08 | −1.27%, t −1.12 |
| B3 (50-SMA exit loop) − C | +4.36%, t +6.79 (artefact) | +0.62%, t +1.88 | −0.66%, t +0.03 |
| buy-and-hold C vs SPY | — | −1.98%/event, t −2.55 | −0.39%, t −0.74 |

**Why the pre-registered metric misleads.** Summing log daily returns docks every in-position day about σ²/2 of
a volatile single name. Arms with more exposure look worse, and C looks worst of all, which manufactures the
"loop beats hold" cells. The primary cell keeps its sign under the arithmetic re-score, which is labelled
post-hoc. The B1 − C and B3 − C "passes" do not survive it, so they are retracted.

**Mechanism.** The re-entries are new-50-day-high closes on names already past their first 52w high. Per 100
in-position days they earn about −2% vs SPY: below the market, and below simply holding (−0.2% to −0.8%). The
loop does recover winners: on the 2.6–2.9% of events where buy-and-hold more than doubled, B1 kept 41–42% of the
move against 2% for a single trip. But it pays for that on the other 97%. The winners-list reading ("re-entry is
the lever", `top_gainers_chart_study_2026-11-17.md` §3.3) was **outcome conditioning**, the exact failure that
study warned about.

**For the triple-digit goal.** No arm doubled more than 1.1% of events (buy-and-hold: 2.6–2.9%). A fresh 52w
high plus mechanical management is not a path to triple digits. Selection has to do the work.

⚠ Caveats: chain_spot cleaning drops 26.4% of ticker-days (4,191 tickers, unexplained >45% one-day breaks), which
plausibly censors explosive names. The liquid-panel run (adjusted, no cleaning, but survivors only) gives the same
answer. Close fills, 10 bp per side, beta-1 SPY match (no beta estimate).

Scripts: `run_leader_reentry_loop.py` (pre-registered 7eae6c9), `run_leader_reentry_loop_posthoc.py`,
`run_leader_reentry_loop_liquid.py`. Events: `leader_reentry_loop_2026-11-17_events*.csv` (+ `_liquid`).
Liquid-panel tables: `leader_reentry_loop_2026-11-17_liquid.md`.

---
## Raw output (survivorship-free run)
# Re-entry loop on fresh leaders -- results (2026-11-17)

Pre-registration: docstring of `run_leader_reentry_loop.py`. Events: 4,233 on 1,774 names, 2011-01-03 -> 2025-02-14; delisted inside H: 5.5%.

## Cells (excess vs exposure-matched SPY, log, per event; month-averaged, NW t lag 12)

| cell | mean | t_NW | 2011-17 | 2018-25 | years same sign | bar |
|---|---|---|---|---|---|---|
| B1 - A (PRIMARY) | -0.0243 | -9.06 | -0.0235 | -0.0249 | 15/15 | PASS (|t|>=3.0) |
| B1 - C | +0.0458 | +5.87 | +0.0387 | +0.0523 | 12/15 | PASS (|t|>=3.2) |
| B2 - A | -0.0597 | -10.00 | -0.0576 | -0.0617 | 15/15 | PASS (|t|>=3.2) |
| B3 - A | -0.0264 | -7.73 | -0.0219 | -0.0306 | 13/15 | PASS (|t|>=3.2) |
| B3 - C | +0.0436 | +6.79 | +0.0404 | +0.0466 | 14/15 | PASS (|t|>=3.2) |

## Arms (per event)

| arm | raw mean | raw median | raw p90 | P(raw > +100%) | excess mean | exposure | trades |
|---|---|---|---|---|---|---|---|
| A | +0.0% | -1.7% | +8.8% | 0.0% | -0.0087 | 9% | 1.0 |
| B1 | +1.0% | -2.1% | +20.4% | 0.5% | -0.0330 | 33% | 4.7 |
| B2 | +1.4% | -2.5% | +28.9% | 1.1% | -0.0684 | 53% | 12.7 |
| B3 | +3.2% | -1.3% | +29.2% | 1.0% | -0.0351 | 45% | 3.3 |
| C | +11.1% | +6.2% | +51.8% | 2.9% | -0.0787 | 100% | 1.0 |

## Exploratory: B1 - A and B1 - C by SPY trend at the event, and by year

- SPY below SMA200 (n 287): B1-A -0.0496, B1-C +0.0555
- SPY above SMA200 (n 3,946): B1-A -0.0224, B1-C +0.0451

|   year |   n |    B1-A |    B1-C |   C raw |
|-------:|----:|--------:|--------:|--------:|
|   2011 | 235 | -0.0228 |  0.0643 | -0.017  |
|   2012 | 238 | -0.0167 | -0.0001 |  0.2026 |
|   2013 | 236 | -0.0128 | -0.0025 |  0.2187 |
|   2014 | 196 | -0.0203 |  0.0702 |  0.0166 |
|   2015 | 173 | -0.0149 |  0.1332 | -0.0974 |
|   2016 | 578 | -0.0333 |  0.0178 |  0.1523 |
|   2017 | 377 | -0.0258 |  0.0452 |  0.1016 |
|   2018 | 289 | -0.0348 |  0.0654 | -0.0043 |
|   2019 | 303 | -0.0188 |  0.0598 |  0.0765 |
|   2020 | 266 | -0.017  | -0.0272 |  0.397  |
|   2021 | 386 | -0.0142 |  0.0541 |  0.0411 |
|   2022 | 207 | -0.0316 |  0.0403 |  0.0095 |
|   2023 | 390 | -0.0159 |  0.0916 |  0.1954 |
|   2024 | 327 | -0.0422 |  0.0539 |  0.1178 |
|   2025 |  32 | -0.0788 |  0.0851 |  0.0318 |

## Right tail: the 123 events where buy-and-hold > +100%

| arm | median share of C's log return kept |
|---|---|
| A | 2% |
| B1 | 41% |
| B2 | 64% |
| B3 | 63% |

## POST-HOC re-score: ARITHMETIC excess (not pre-registered; see run_leader_reentry_loop_posthoc.py)

| cell | mean | t_NW | 2011-17 | 2018-25 | years same sign | bar |
|---|---|---|---|---|---|---|
| B1 - A | -0.0130 | -4.93 | -0.0159 | -0.0104 | 14/15 | PASS (|t|>=3.0) |
| B1 - C | +0.0020 | +1.08 | +0.0093 | -0.0047 | 7/15 | fail (|t|>=3.2) |
| B2 - A | -0.0377 | -5.58 | -0.0426 | -0.0331 | 14/15 | PASS (|t|>=3.2) |
| B3 - A | -0.0089 | -2.18 | -0.0099 | -0.0079 | 12/15 | fail (|t|>=3.2) |
| B3 - C | +0.0062 | +1.88 | +0.0153 | -0.0022 | 7/15 | fail (|t|>=3.2) |

| arm | arithmetic excess per event | t_NW (vs 0) | excess per 100 in-position days | exposure |
|---|---|---|---|---|
| A | -0.0048 | -2.86 | -0.0250 | 9% |
| B1 | -0.0178 | -5.23 | -0.0229 | 33% |
| B2 | -0.0424 | -5.62 | -0.0333 | 53% |
| B3 | -0.0136 | -2.97 | -0.0127 | 45% |
| C | -0.0198 | -2.55 | -0.0081 | 100% |
