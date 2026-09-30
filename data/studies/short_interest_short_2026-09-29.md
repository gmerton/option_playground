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

---

## Results (run 2026-09-29, after 9304781; `run_short_interest_short.py`, `.log`)

**Verdict: FAIL → NULL. Heavily shorted liquid names do not underperform matched names, and shorting them loses money
after costs and borrow in every cell. Short sellers' crowding carries no usable information at our liquidity.**

206 formations (2018-01 → 2026-07), 166k name-dates, ~81 names per HIGH decile per formation.

| signal | h | excess vs matched (%) | t | halves (2018–21 / 2022–26) | yrs neg | short P&L net (5% borrow) | t |
|---|---|---|---|---|---|---|---|
| **HIGH DTC (PRIMARY)** | **20** | **−0.15** | **−1.02** | +0.02 / −0.30 | 5/9 | **−1.40%** | −2.81 |
| HIGH DTC (1% borrow) | 20 | −0.15 | −1.02 | | | −1.08% | −2.17 |
| HIGH DTC | 60 | −0.51 | −1.30 | +0.05 / −1.00 | 5/9 | −4.28% | −3.48 |
| RISING DTC | 20 | +0.02 | 0.17 | | 2/9 | −1.58% | −3.11 |
| HIGH ∧ RISING | 20 | −0.09 | −0.39 | | 5/9 | −1.52% | −2.74 |

- Direction is right for HIGH (a mild lag, bigger since 2022 and at 60 sessions: −1.00pp in 2022–26) but nowhere near the
  bar, and the stocks still rise in absolute terms — the short P&L is negative in every cell (t −2.2 to −3.8).
- **Survivorship check (chain-spot incl. delisted):** ALL +0.07% (t 0.37); NONSURV −0.16% (t −0.65) with short P&L −0.76%
  (t −1.12). Dead names help a little, as with the breakdown test, and still don't make it a trade.
- Not even the veto fallback: the lag fails |t| ≥ 3 and the halves disagree.

**What it means for the book now.** No single-name short signal survives in our universe — price patterns, option
signals, flows, offerings, index deletions and now short interest: 0 for 11. The short side that exists here is
structural: the sector-momentum spread (a real hedge) and the gap-up fade in a stock's own downtrend (forward holdout).
