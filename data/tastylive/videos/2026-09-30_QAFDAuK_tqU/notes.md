# tastylive: "Cem Karsan Explains the Quarter-End Flow Most Traders Never See" (2026-09-30, 12:47)

_Reviewed 2026-09-30. Cem Karsan (Kai Volatility) on "Last Call", recorded live in the final ~30 minutes of the last
trading day of Q3. Transcript (`en-orig` auto-captions, "Jim Hson"/"Jean" = Cem Karsan) in this folder. No chart, no
table, no number beyond the illustration._

## Verdict: 2 / 5

- **A mechanism story with no evidence behind it.** Leverage turns gains into collateral; the collateral is
  "re-leveraged" at month, quarter and year end, so those windows are "structurally supported" [00:35–02:34]. That is
  a plausible story, but he gives no statistic, sample, or control, and he states it as known ("not always, just
  structurally in general").
- **Its testable core has already failed here.** The turn-of-the-month window (last day plus the first three) is
  **NULL in SPY 2000–26 and negative since 2013** (−0.60 bp/day; `turn_of_month_2026-09-24.md`). His window is
  narrower (a "48-hour" end/start pair) and he claims quarters are stronger, conditional on the quarter being up.
  Those two cuts are new but have a low prior: they are subsets of a faded effect.
- **The one new and specific claim is the JPM hedged-equity roll** [07:07–09:19]. The quarterly collar sells a lot
  of implied vol, and because everyone front-runs it, "quarter end tends to be a very critical bottom in implied
  volatility". That can be checked on VIX, and no row in the ledger has touched it.
- The closing views (FX/rates vol, left-tail 6–12 month index vol, "a correlation-of-one tail event early next
  year", sell dispersion to fund index vol) are **forecasts, not rules**. None can be scored except forward.
- The political-influence remark (the administration "squeezed" the March quarter-end print [03:44–04:46]) is one
  anecdote attached to a motive.

## Data audit

| item | what the video gives |
|---|---|
| sample | none. No backtest, no period |
| statistic | none. "Pretty bullish", "structurally very very positive historically" |
| illustration | a 10% rally on "$30 trillion of equity exposure" creates $30T of "new collateral" [01:02–01:13]. The arithmetic is garbled: 10% of $30T is $3T, and the description says "10% on ~300 trillion" |
| window | end of month + start of month "as a 48-hour period" [02:22–02:27]; quarter > month; year end = the biggest (Santa Claus / January effect [01:30–01:47]) |
| conditioning | "if you have a quarter where the market is net up" [01:49–01:59] |
| JPM collar | buys the ~5% OTM put, sells the ~20% OTM put, sells a call financed to ~zero, expiring at the next quarter end; ~$30–40B notional [07:59–08:29]. This matches the public JHEQX structure; the notional was not checked |
| control | none |
| costs | n/a |

## Claims against our ledger

| @ | claim | our evidence |
|---|---|---|
| 00:35–02:34 | End of month + start of month (48 h) is "structurally very very positive"; quarters more so; strongest at year end | ❌ **The month version fails.** TOM (last day + first 3) in SPY 2000–26: **+3.26 bp/day vs other days, t 0.94**, halves **+7.33 / −0.60** (gone since 2013); QQQ t 1.02. Trading only the window: Sharpe 0.36 vs 0.51 buy-and-hold (`turn_of_month_2026-09-24.md`, TEST_INDEX §7). The residual: day +1 alone is +17.7 bp SPY, exploratory and never tested. **Not tested:** the quarter-end cut, the "quarter net up" condition, and the narrower 2-day window. Those are new, with a low prior (spec A) |
| 01:49–01:59 | The effect is larger after an up quarter (re-leveraging needs gains) | **Untested.** It is the only cut that ties the calendar to his mechanism rather than to the calendar alone. It is in spec A as the primary interaction |
| 04:46–04:55 | "A bigger print up [into quarter end] is net positive for the quarter ahead" | Untested, and underpowered by construction: ~105 quarters since 2000, one observation each. Exploratory row in spec A; no verdict possible at the house bar |
| 07:07–09:19 | **The JPM hedged-equity quarterly roll sells a lot of implied vol; front-running now makes quarter end "a very critical bottom in implied volatility"** (vol compresses into the roll week, then rises) | **Untested; nothing in the ledger touches it.** The nearest work: the vanna/charm flow test (2026-09-30) found both dealer-flow greeks NULL, with an opex-calendar lead that is exploratory only (expiry day −21.6 bp t −3.13, day −3 +22.8 bp t 3.21, Šidák ~3.4; `vanna_charm_flow_2026-09-30.md`). The GEX regime is certified as a *mechanism* for realised vol (SPY t 7.7), not for implied. Spec B tests the IV-bottom claim directly |
| 05:52–06:50 | Stock/bond rebalancing (risk parity, pensions) is real but "secondary" | Agrees in shape with the TOM null (a small, faded effect). No separate test. §10's order-flow row lists "month-end / quarter-end rebalancing" as a candidate (a); spec A would settle it |
| 03:44–04:46 | The administration pushed the March quarter-end print up; banks and companies benefit from higher quarter-end marks | An anecdote (n = 1) plus a motive. Not testable as stated |
| 10:00–12:33 | FX/rates vol will outperform; equity index vol "structurally compressed" for a couple of months; a correlation-of-one tail event "early next year"; sell dispersion to fund index vol | Forecasts. Only forward scoring is possible. ⚠ The equity-vol leg partly contradicts itself: vol is "very compressed" and a "tough trade", yet 6–12 month index vol and the left tail are recommended |

## Not tested, could be

> **RAN 2026-09-30 → UNDERPOWERED × 2** (`data/studies/quarter_end_pair_2026-09-30.md`): A +14.6 bp/day t 1.49, up-quarter interaction wrong sign (t −0.79); B +5.2 pts t 1.23, placebo −3.0.

### A. Quarter-end vs month-end turn, conditional on the quarter (pre-registerable; low prior)

- **Data:** yfinance SPY adjusted daily closes, same pull as `run_turn_of_month.py`. PRIMARY window 2000-01 →
  2026-09 (out of sample for the 1987–88 papers); 1993–99 is an in-sample check only.
- **Window W (his 48 h):** the close-to-close returns of the last trading day of the period (day −1) and the first
  trading day of the next (day +1).
- **Cells, named in advance:**
  - **PRIMARY:** quarter-end W days minus other month-end W days. HAC(5) OLS on daily returns with dummies
    `QE_W`, `ME_W` (non-quarter month ends), baseline = all other days. The test is b(QE_W) − b(ME_W).
  - Secondary S1: QE_W after an **up quarter** (SPY quarter return > 0 through day −2) minus QE_W after a down
    quarter: his interaction.
  - Secondary S2: year-end W minus other QE_W (the n is tiny, so descriptive only).
  - Exploratory, no verdict: the day −1 return vs the next-quarter return (~105 points).
- **Control:** what it varies is the **calendar position** (quarter vs non-quarter month ends); the tape is held by
  using the same years. Also report both W dummies against all other days, so the TOM null is re-anchored on his
  narrower window.
- **Bar:** |t| ≥ 3 on the primary, both halves (2000–12 / 2013–26) the same sign, per-year sign table. Šidák over 2
  secondaries (|t| ≥ 2.24) for S1/S2, with the house 3 still the floor for any adoption. Report in bp/day.
- **n:** ~107 QE_W pairs and ~214 ME_W pairs. MDE at t 3 ≈ 3 × σ_day / √107 ≈ 35 bp per day. Only a large effect
  can pass, so say so up front: a null here is UNDERPOWERED, not NULL, unless the point estimate is ≤ 0.
- **Effort:** ~1 h, local, yfinance only.

### B. Quarter-end IV bottom from the JHEQX roll (pre-registerable; the one new axis)

- **Data:** `data/cache/vix_daily_long.parquet` (~2008 →) and `vix_term_cboe.parquet` (VIX, VIX3M). JHEQX has been
  large since ~2017, so PRIMARY = 2017 → 2026-09 and 2008–16 = the pre-size placebo.
- **Event:** the last trading day of each calendar quarter (the roll date; ~39 events 2017+).
- **Claim, operationalised:** VIX reaches a local trough around the roll: it falls in the 5 sessions before
  (ΔlogVIX[−5 → −1] < 0) and rises in the 5 after (ΔlogVIX[0 → +5] > 0).
- **PRIMARY:** the V-shape statistic `V = ΔlogVIX[0 → +5] − ΔlogVIX[−5 → 0]` at quarter ends minus the same
  statistic at **non-quarter month ends** in the same years. The control holds the month-end calendar fixed and
  varies only whether the collar rolls. Welch t, plus a per-year sign table.
- **Secondary:** the same with VIX3M, where the collar's roughly 3-month tenor should show it more. The 2017+ minus
  2008–16 difference in the primary is the dose check: the collar grew, so the effect should grow.
- **Confound to pre-declare:** SPX quarterly expiry, index rebalancing and window dressing all share the date. The
  month-end control removes the month-end part only. If B passes, it is a calendar MECHANISM, not attributable to
  JHEQX alone.
- **Bar:** |t| ≥ 3, both halves of 2017–26 (split 2022-01-01) the same sign, and the placebo 2008–16 smaller. With
  ~39 events, expect UNDERPOWERED unless the effect is large.
- **Effort:** ~1 h, local, no new pull.

Neither test is a trade until it passes. Even then the tradeable form would be an index vol purchase at the quarter
end (VIX options or SPY straddles at house fills), which is a separate test.
