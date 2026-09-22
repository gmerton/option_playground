# Book long straddles (7 DTE) by SPY dealer-gamma sign on the entry Friday (2026-09-21)

## Pre-registration (written BEFORE any code ran; do not edit this section after the results)

**Question.** GEX follow-up item 4. Do the long-straddle book's trades earn more when SPY's net dealer gamma at the
ENTRY day's close was negative? Conditioning only, no new strategy.

**Trades.** The honest arm-4 book: `data/cache/straddle_recenter/recenter_results.parquet`, arm == 7 (7-DTE, Friday
entry into next Friday's expiry), both == True (FVR ≥ 1.20 AND IV pct ≤ 30). **Return = `hold`**: hold to expiry, entry
at mid + 25% of the bid-ask + $0.0065/sh/leg, settled at |S_T − K| by expiry-day parity (the recenter/slippage studies'
real-fill hold return), as a fraction of entry cost.

**Gamma.** SPY net GEX at the entry date's close, computed exactly as `run_gex_regime_pin.gex_series` (per strike
Σ call OI×γ − Σ put OI×γ, ×100×S²×0.01, strikes within ±20% of the close, naive sign). NEG = net GEX < 0. The GEX
series ends 2026-02-26; trades whose entry date has no GEX are dropped (counted).

**Statistic.** Effective n = entry dates. Per entry date, the mean return of that date's trades; each date is NEG or
POS (one SPY value per date). Difference = mean over NEG dates − mean over POS dates; t = Welch t across dates.
**Halves = entry dates split in half by count** (first half of the sorted distinct dates vs the second).

**Pass bar.** NEG − POS difference > 0, |t| ≥ 3 across dates, and > 0 in both halves.

**Also reported:** per group trades, dates, trade-level mean / median / win rate, and the share of the group's total
P&L from its top 1% of trades (the book is a right-tail book).

**Not tested:** GEX magnitude buckets, GEX on the underlying single names, the zero-gamma flip level, changing the
gates, sizing rules, exits other than hold-to-expiry, the 14-DTE arm.

---

## Results (run 2026-09-21, once; script `run_gex_book_straddles.py`, log `.log`, table `.csv`)

**Verdict: FAIL / NULL.** 5,684 of 5,886 arm-7 both-gate trades had SPY GEX at entry (202 dropped: entries after the
GEX series ends or missing days); 315 entry dates, 2018-04-20 → 2026-02-13. Half cut 2022-08-19.

| | NEG dates | POS dates | NEG − POS (date means) | Welch t |
|---|---|---|---|---|
| full | 139 (2,059 trades) | 176 (3,625 trades) | **+3.0pp** | **0.55** |
| first half | 58 | 99 | +8.6pp | 0.86 |
| second half | 81 | 77 | **−2.2pp** | −0.35 |

Trade level: NEG mean +3.4% / median −15.6% / win 43.1% / top 1% = 123% of the group's P&L; POS mean +4.5% / median
−16.2% / win 42.1% / top 1% = 79%. The sign flips between halves and between the date-level and trade-level means;
both groups are carried by their right tails (NEG's top 1% is more than all of its P&L). Market gamma at entry does
not sort the book's single-name straddle returns. No change to the straddle playbook.
