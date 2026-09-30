# Short interest as a standalone single-name SHORT signal (2026-09-29)

## Pre-registration (written BEFORE the run; do not edit this section after the results)

**Why.** Gabe: "stay focused on shorts". Price-pattern shorts are 0 for 9 (incl. dead names); option-implied and
flow-based shorts NULL. Short sellers are the best-documented informed sellers (Boehmer–Jones–Zhang 2008; Asquith–
Pathak–Ritter 2005), and our two hints point that way (crowded shorts into catalysts right, t −2.68; high DTC a drag on
breakouts, t −1.40). Short interest has never been tested here as a standalone short.

**Data.** `data/cache/short_interest.parquet` (FINRA via Polygon, bi-monthly, 2017-12 → 2026-08). No float history →
the measure is **days to cover (DTC = SI / avg daily volume)**. Publication lag: settlement + 8 business days (as BB-1).
Prices: `liquid_panel_2009` (adjusted OHLC). Eligible: ADDV ≥ $50M, price ≥ $5, a DTC value with ADV > 0.

**Formation.** For each settlement date, on the first panel session ≥ publication: rank eligible names on DTC.
- **HIGH (PRIMARY)** = top decile of DTC. Secondary: **RISING** = top decile of DTC / prior-report DTC; **HIGH ∧ RISING**.
**Trade.** Short at that session's close; cover at the close of session +20 (PRIMARY); +10 and +60 reported.
Costs 10 bp per side + **borrow 5%/yr** pro-rated (crowded names are often special; 1%/yr reported too).
**Control.** Same-date eligible non-signal names in the same prior-20-session-return quintile × ADR tercile cell
(the skew test's matching; there is no panel-wide sector map). Excess = signal forward return − its cell's mean.

**PRIMARY (HIGH, +20).** Excess < 0 with **|t| ≥ 3** (t on formation-date means, Newey-West 1 lag for the overlap),
both halves (2018–2021 / 2022–2026) negative, negative in a majority of years, **AND absolute short P&L after costs and
5% borrow > 0**. Fallback declared now: (a)+(b)+(majority) without the absolute condition = a long-book VETO, not a short.
**Multiple testing:** 3 signals × 3 horizons reported, one primary; the house |t| ≥ 3 governs the primary only.
**Survivorship check (reported):** the same HIGH +20 on `chain_spot_daily` closes (incl. delisted; option-volume
liquidity as in the dip test), ALL vs NONSURV — shorts are the side survivor panels hurt.
Window: formations 2018-01 → 2026-07. Local.
