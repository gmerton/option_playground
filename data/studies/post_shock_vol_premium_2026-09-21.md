# Is SPY implied vol over-priced after a big move? (post-shock premium, 2026-09-21)

## Pre-registration (written BEFORE any data was pulled; do not edit this section after the results)

**Claim (Gabe, recalling Tito Adhikary):** after SPY moves a lot, implied volatility stays inflated while realised
volatility fades, so options are over-priced for a while afterwards. The literature says the variance premium is
largest after spikes; the danger is volatility clustering (realised stays high too).

**Data.** `silver.options_daily_v3` SPY bid/ask/delta, 2010-01 → 2026-02-27; SPY daily closes from the 1-min file;
^VIX from yfinance.

**Shock.** Day s is a shock day if |SPY close-to-close log return| ≥ 2 × the standard deviation of the prior 20 daily
log returns (through s−1). **Post-shock window** = entries at the close of days s, s+1, …, s+4. Shocks within 5 trading
days of each other merge into one **episode**; t-stats are clustered by episode (non-window days each form their own
cluster). Direction: DOWN if the (first) shock return < 0, else UP.

**Trade measured, at every day's close, for three horizons h = 1, 5, 10 trading days:** the ATM SPY straddle (call
delta nearest 0.50) in the listed expiry whose trading-days-to-expiry is closest to h (within ±2 for h = 5, 10; exactly
1 for h = 1), held to expiry, settled at |S_exp − K| with S_exp = SPY's close on the expiry date.
- **Primary outcome:** SHORT straddle return on the credit at the house real fill (sell at mid − 25% of the bid-ask,
  $0.0065/share/leg; no exit cost).
- Also: realised / implied move = |S_exp − K| / straddle mid.

**Control (VIX-matched).** Regression of the outcome on POST (1 = post-shock window) with VIX(entry-day close) DECILE
fixed effects, errors clustered by episode. The POST coefficient = post-shock minus normal days at the same VIX level.

**Pass bar (per horizon; 3 tries).** POST coefficient > 0 with t ≥ 3, positive in both halves (2010–2017 /
2018–2026-02), AND the post-shock short straddle's own mean return at the real fill > 0. Reported alongside: DOWN vs UP
shocks, the ten worst post-shock episodes by name/date (crash weeks), and the same for the 2× iron fly (wings at
K ± 2 × the straddle mid) as the defined-risk version.

**Diagnostic, NOT a verdict (weekend):** from the 1-day SPY straddle file already built
(gex_spy_straddle_2026-09-21.csv), realised/implied and the short return for entries whose expiry is 3 calendar days
later (Friday → Monday) vs 1 day.

**Not tested:** other shock sizes or windows, VIX-spike definitions, term-structure filters, single stocks, stops.

---

## Results (run 2026-09-21, after the pre-registration above; script `run_post_shock_premium.py`, log `.log`, table `.csv`)

**Verdict: FAIL at every horizon. At the same VIX level, SPY options are NOT richer after a big move; at 10 days the
post-shock short is WORSE (volatility clustering), especially after UP shocks.** 283 shock days in 156 episodes
(89 down), 2010 → 2026-02.

| horizon | entries (post-shock / episodes) | short straddle, post-shock | normal days | POST vs VIX-matched normal | t (episodes) | 2010–17 / 2018–26 | DOWN / UP | 2× fly POST |
|---|---|---|---|---|---|---|---|---|
| 1 day | 507 / 146 | +8.5% | +4.6% | +4.0pp | 1.0 | +17.1 (t 2.2) / 0.0 | +0.5 / +9.1 | +2.9pp (t 1.1) |
| 5 days | 932 / 148 | +3.9% | +3.8% | +0.1pp | 0.0 | +1.3 / −1.5 | +1.0 / −1.3 | −0.3pp |
| 10 days | 839 / 124 | −2.0% | +8.6% | **−10.8pp** | −1.8 | −4.5 / −14.3 | −3.5 / **−20.7 (t −2.1)** | −5.8pp (t −1.6) |

- The raw post-shock premium at 1 day (+8.5% vs +4.6%) is the VIX level, not the shock: matched on VIX decile it
  shrinks to +4.0pp (t 1.0) and vanishes in 2018–26.
- At 10 days, selling after a shock loses 10.8pp vs a normal day at the same VIX: realised volatility keeps coming.
  Worst windows: Aug 2015, Jan–Feb 2018 (the Volmageddon run-up), Feb 2017/Nov 2017 rallies, Oct 2018, Feb 2014,
  mid-2012, Jun 2010 — several start with UP shocks.
- **So "IV stays inflated after a big move" isn't an edge here:** the implied premium after shocks is the premium
  the VIX level already carries, and the clustering risk makes multi-day shorts worse.

## Diagnostic (NOT a verdict): the weekend

1-day SPY straddles from the GEX file, Friday → Monday (3 calendar days) vs 1-day:

| era | gap | entries | realised / implied | short straddle at real fill |
|---|---|---|---|---|
| before 2022-06 | 1 day | 847 | 0.94 | +4.5% |
| before 2022-06 | Fri → Mon | 195 | 0.89 | +10.2% |
| daily-expiry era | 1 day | 664 | 0.96 | +3.1% |
| daily-expiry era | Fri → Mon | 164 | 0.86 | +13.4% |

Friday → Monday options are consistently richer (realised 86–89% of implied vs 94–96%), in both eras, as calendar-time
decay predicts. Not pre-registered and a subset of an existing file → queued as its own test, including whether it
overlaps the positive-gamma fly (Friday entries are in that sample).
