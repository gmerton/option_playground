> **⚠ 2026-09-20: `data/cache/etf_putspread_recon.parquet` is SUPERSEDED. Do not use it.** It is a stale early build (its take-50 cfg gives SPY −0.3%, not the +5.4% below). The canonical roster trades are `data/cache/rsi_putspread.parquet` (from `etf_condor_recon.parquet` via `run_rsi_conditioning_study.py`; +5.68%/trade, n 6,739). A committed rebuild script is queued (TEST_INDEX §10).

> **⚠ ERRATUM 2026-09-16 (same day): the +6.92% headline is overstated.** The condor study
> (`etf_condor_call_side_2026-09-16.md` §0) found that 2.4% of credit-spread wings carry returns
> above the theoretical ceiling `credit/margin` — i.e. a negative exit value, which is a crossed or
> stale mark, not a trade. The `credit/width ≤ 0.50` and `margin ≥ 0.10` filters used here do NOT
> catch them. Re-scored with the ceiling filter the put spread is **+5.70%/trade, weekly t 4.87,
> monthly t 3.13**. It survives, smaller. That study also shows the edge is substantially long-beta:
> the mirror-image bear call spread earns −2.66%, and the direction-neutral condor earns +0.36%
> at monthly t 0.60.

# ETF bull put spreads: the exit rule is the edge (2026-09-16)

Follow-up to `etf_put_spread_study.md` (10 Sept), which concluded there is **no unconditional edge after costs**
(+0.6%/trade, weekly t 0.3) and that the "managed" exit *destroys* value (−4.3%/trade, t −5.4). That study tested
**30 DTE, 0.30Δ/0.15Δ, hold to expiry** against a managed rule that was **a 50% profit take *combined with* a 2×
stop**. This one separates the two halves of that managed rule, because the stop and the take are not the same thing
and everything else we have tested says stops are what destroy value.

**Setup.** Same 20 ETFs and the same `options_cache` source, every Friday 2018 → Feb 2026, sell the 0.35Δ put and buy
the 0.25Δ put at the expiry nearest 45 days, **take profit at 50% of the credit, no stop**, hold otherwise to expiry.
Return on margin (width − credit), house cost model. Script: session scratchpad `ps_recon.py`; trades in
`data/cache/etf_putspread_recon.parquet`.

## Result

| | n | mean / trade | win | weekly t | monthly t | months + |
|---|---|---|---|---|---|---|
| 45 DTE, 0.35/0.25, **50% take, no stop** | 6,852 | **+6.92%** | 87% | **5.80** | 3.68 | 70% |
| first half 2018-22 | 3,841 | +4.85% | 86% | 2.93 | 1.88 | 65% |
| second half 2022-26 | 3,011 | +9.56% | 88% | 5.42 | 3.37 | 77% |

By year: 2018 −2.8, 2019 +11.3, 2020 +11.6, 2021 +5.8, 2022 −4.0, 2023 −0.3, 2024 +13.6, 2025 +19.5 — six of eight
full years positive, the two losers being the bear years. **19 of 20 names positive** (median +7.2%, SPY +5.4%, only
TLT negative at −1.0%). Unlike the long straddle this edge is **not concentrated**: the top 1% of trades supply 15%
of total return and removing the worst 1% moves the mean from +6.92% to +8.0%.

**Reading.** The 10 Sept conclusion "hold put credit spreads to expiry" was drawn from a rule that bundled a stop with
the take. On this data the take alone is worth several points a trade and the stop is what was destroying the result —
consistent with the straddle stop study, the paid-to-wait break rule, and the calendar exit tests. The headline
difference is the exit, not the deltas or the tenor.

## ⚠ The result depends on how missing marks are treated

The engine assigns **max loss whenever it cannot find an exit** (`put_spread_study.py:562`, "worst-case fill for
missing data"). That convention decides the sign:

| treatment of the 7.1% of trades with no exit mark | mean | weekly t |
|---|---|---|
| assume max loss (engine default) | −0.70% | −0.36 |
| exclude them | +6.92% | 5.80 |

Exclusion is the defensible choice here because **the gaps are not outcome-related**: the missing-mark rate *falls*
as stress rises — 7.6% at VIX < 15, 8.0% at 15-20, 5.5% at 25-30, **3.3% above 30** — and COVID (5.2%) and April 2025
(3.7%) are below average. A gap that appears in calm markets and disappears in crashes is an ingestion artefact, not
a hidden loss. Trades whose expiry falls past the data end (2026-02-20) were dropped separately.

**Before sizing this, confirm on a more complete source.** SPY from `SPY_options.parquet` has a 1.5% gap rate against
5.6% from `options_cache` for the identical 409 trades, and that difference alone moves SPY's mean from −0.5% to
+3.3%. The parquet is the fuller export. Re-running the roster from parquet-grade data would settle the magnitude.

## Effect on the two-sleeve book

Replacing the SPY-only put leg in `audit_review_2026-09-16.md` §4 with this roster version, monthly, 92 months,
correlation still **−0.25**:

| sleeve | mean / month | t | months + | worst | best |
|---|---|---|---|---|---|
| 7-DTE long straddle | +5.74% | 1.9 | 57% | −52% | +120% |
| ETF put spread (roster, take-only) | +6.65% | 3.7 | 71% | −55% | +34% |
| **50 / 50 blend** | **+6.19%** | **4.0** | 66% | **−32%** | +59% |

The blend's t rises from 2.5 (SPY-only leg) to **4.0**, and its worst month improves to −32% against −52% and −55%
standalone. Worst blend months: 2018-11 (−32.5, both legs lost), 2019-04 (−23.2), 2022-08 (−20.1, straddle +14.5
against put spread −54.7). The put spread is now the better-measured leg of the two.

**Still open:** the gap-rate confirmation above; and both legs remain sleeve-level per-trade averages, not account
returns — size per `capital_allocation_framework.md`.
