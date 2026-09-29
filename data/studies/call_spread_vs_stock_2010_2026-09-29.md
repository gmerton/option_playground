# 30/15Δ call debit spread vs delta-matched stock, extended to 2010 (2026-09-29)

## Pre-registration (written BEFORE the pull; do not edit this section after the results)

**Why.** Audit List A #8 (`audit_top_down_2026-09-25.md`). `run_vehicle_benchmark.py` (2026-09-22) found the 30/15Δ call
debit spread beat holding its own entry delta in shares by **+$97/contract (t 2.29)**, most in down months (+$204,
t 2.45) — i.e. the capped downside, not beta — but failed its own bar with SPY < 200 SMA (+$144, t 1.25). Its sample was
2019-10 → 2026-01, one bull run with few down markets. v3 reaches back to 2010: ~3× the down-market months, all unseen.
Goal relevance: a bullish vehicle that beats stock on its own delta would change how the book expresses longs now.

**Design (frozen from `run_vehicle_benchmark.py`; only the window and one settlement detail change).** Same 20 names
(SPY QQQ IWM AAPL MSFT NVDA AMD META AMZN GOOGL TSLA NFLX JPM XOM GLD SMH COST AVGO CRM WMT; each from its own first
listed date), every Friday, expiry nearest 30 DTE (25–40), legs by delta within 0.07 of target: long C30 at the ask,
short C15 at the bid, $0.0065/leg; put credit P30/P20 (bid/ask) reported alongside. Held to expiry, settled at the
chain-implied spot (`lib.studies.chain_spot`, RAW, so strikes match). Delta-matched stock = (Δc30 − Δc15) × 100 shares
over the same window. Stat = option $ − stock $ per contract, **month-clustered t**.
- **Settlement change (declared):** pre-2015 monthly expiries are dated Saturday; settle at the chain spot of the last
  trading day on or before the expiry date (post-2015 this is the expiry date itself, as before).
- Regime: SPY vs its 200 SMA from `liquid_panel_2009`; VIX from `vix_daily_long`.

**Window.** PRIMARY = entries **2010-01-01 → 2019-09-30** (never seen; the original sample starts 2019-10).

**Primary (all required).**
1. Call − delta-matched stock > 0 with **t ≥ 3**, both halves positive (split 2015-01-01).
2. The original's failed condition, on unseen data: **SPY < 200 SMA** cell > 0 with **t ≥ 2**.
Pass → the call debit spread is SUPPORTED as a long vehicle (beats its own delta, incl. in weak markets).

**Reported, not in the bar:** the pooled 2010–2026 result; down months; per year; VIX terciles; the put credit spread's
vs-stock number; the share of entries dropped for missing legs/spot.

**Cost of the pull.** One Athena query on `options_daily_v3`, 20 tickers × Fridays 2009-06 → 2019-12, DTE 25–40,
|Δ| 0.10–0.40 (the original query's filters), cached to `data/cache/call_spread_vs_stock_2010_chains.parquet`.
Approved by Gabe 2026-09-29.
