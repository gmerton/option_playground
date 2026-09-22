# Long straddle at 7 / 8 / 9 / 10 / 11 DTE (2026-09-21)

**Verdict: NULL for 8–11 DTE. Friday entry (7 DTE) stays the only tenor. YIELD: METHOD (entry weekday = tenor).**
Prompted by the Monday 9/21 screen, which priced 11 DTE because it ran on a Monday.

## Design

With weekly Friday expiries the tenor is the entry weekday: Fri → next Friday = 7 DTE, Thu = 8, Wed = 9, Tue = 10,
Mon = 11. Every arm buys the ATM straddle (call delta nearest 0.50) on the following week's Friday expiry and holds
to expiry, no stop (the 2026-09-20 stop studies: every stop costs money).

- **Gates on each arm's own entry day**, same as the playbook: FVR (30→90d put forward vol ratio) ≥ 1.20 and
  10d put IV percentile ≤ 30 vs the name's prior 252 readings (no look-ahead). Source `silver.fwd_vol_daily`.
- Universe = the 317 tickers of the Friday study; min entry mid $0.50; 2018-04 → 2026-02 (bid/ask ends Feb 2026).
- Fill = mid + 25% of the bid-ask per leg + $0.0065/sh/leg; settle |S_T − K| from expiry-day parity. Also at mid and
  at the full ask.
- **t is clustered by entry date** (trades on one date share the market move): effective n ≈ 330 dates per arm.
- Script: `run_straddle_dte_study.py` (gates → pull → sim → report). Cache `data/cache/straddle_dte/`. Log:
  `straddle_dte_study_2026-09-21.log`.

**Validation:** the 7-DTE arm reproduces the audited number: **+6.91%/trade at a real fill** vs the honest arm-4
expectation of ~+6.7% (straddle_slippage_2026-09-20.md).

## A. Each arm on its own gates (returns in % of premium)

| DTE | entry day | n | dates | mid | real fill | full ask | t (dates) | trim top 0.1% | win | yrs + |
|---|---|---|---|---|---|---|---|---|---|---|
| **7** | Fri | 6,870 | 335 | +10.38 | **+6.91** | +4.50 | 0.83 | +4.51 | 42% | **8/9** |
| 8 | Thu | 5,860 | 327 | +2.15 | −0.81 | −2.87 | 0.07 | −2.92 | 39% | 5/9 |
| 9 | Wed | 5,667 | 329 | +6.07 | +2.97 | +0.78 | 1.58 | +1.16 | 41% | 6/9 |
| 10 | Tue | 5,825 | 329 | +5.74 | +2.67 | +0.52 | 0.02 | +2.14 | 42% | 6/9 |
| 11 | Mon | 6,048 | 318 | +3.55 | +0.76 | −1.24 | −0.19 | −0.04 | 41% | 4/9 |

Spreads are the same across arms (median bid-ask 5.8–6.5% of mid), so friction does not explain the gap.

## B. Paired against Friday (same ticker, same expiry, both days passed the gates)

| DTE | pairs | expiries | earlier entry | Friday entry | diff | t (expiries) |
|---|---|---|---|---|---|---|
| 8 | 3,031 | 278 | +0.92 | +6.59 | **−5.67** | −2.34 |
| 9 | 2,822 | 265 | +2.94 | +8.85 | −5.91 | −0.96 |
| 10 | 2,752 | 268 | +0.91 | +6.97 | −6.07 | −1.60 |
| 11 | 2,472 | 252 | −3.58 | +4.89 | **−8.48** | −1.91 |

On the same name and expiry, entering earlier is worse by 5.7–8.5pp in every arm, and worst on Monday. Each single
pair is only |t| 1–2.3, but all four point the same way. Half-by-date and by-year tables are in the log: 7 DTE is
positive in both halves (+6.3 / +7.4) and 8 of 9 years; no other arm is positive in both halves with more than 6 of 9 years.

## C. The right tail

Every arm is a right-tail book. At 7 DTE the top 1% of trades is 100% of the P&L (without it −0.02%/trade). At 8–11
the top 1% is worth *more* than the whole arm, meaning the other 99% lose −1.9 to −6.9%/trade. ⚠ This restates the
standing caveat: even the 7-DTE arm is t 0.83 on dates alone; it's in the book only as half of the pair with the
bull put spread.

## What changes

- **Enter only on Friday.** A straddle screen run Monday–Thursday is information, not an entry. Today's Monday
  screen (11 DTE) is the worst arm: +0.76% at a real fill, −1.24% at the ask, 4 of 9 years positive, −8.5pp vs
  the Friday entry on the same name and expiry.
- Not tested: names with daily expiries (SPY/QQQ), where weekday and tenor can be separated; and a Friday entry
  into a 14-DTE expiry (already NULL in the re-centering study).
