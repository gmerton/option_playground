# Mirror-breakdown short on the SURVIVORSHIP-FREE series (2026-09-29)

## Pre-registration (written BEFORE the run; do not edit this section after the results)

**Why.** Every single-name short in the ledger (0 for 8) ran on survivor panels, which omit the names that collapsed
and delisted — a short's best outcomes (audit List A #9). And the plain mirror of the house breakout has never been
tested as a short (only the FDX failed-retest template). `chain_spot_daily` has parity closes for ~10.8k optionable
tickers INCLUDING delisted, 2010 → 2026-02. Gabe (2026-09-29): "still interested in identifying breakdown setups".

**Data.** `run_dip_survivorship.pull()` + `adjust_and_clean()` unchanged (split-adjusted closes, unexplained ±45% jumps
cut the series, option volume). **Closes only** — no highs, lows or share volume exist in this series.
**Groups:** SURV = tickers in `liquid_panel_2009`; NONSURV = all others; **ALL** = both.
**Eligible:** 50-session mean option volume ≥ 1,000 contracts and close ≥ $5 (the dip test's liquidity proxy).

**Setup (close-only mirror of the house breakout; declared now).**
- ADRp = 20-session mean |close-to-close return| × k (k = `run_dip_survivorship.k_scale()`), ≥ 3%.
- Downtrend stack: SMA10 < SMA20 < SMA50 on each of the last 5 sessions.
- Breakdown: close < the lowest close of the prior 15 sessions, and the prior close was not (first break).
- Day's change ≥ −8% (mirror of the house < +8% cap; excludes crash days). No volume gate (none available).
**Trade.** Short at the signal close. Stop = max(prior close, close × 1.02), judged on the close. Exit on the first close
above the stop or above the 20 EMA; 60-session cap. If the series ends (delisting / acquisition), exit at its last close.
Cost 10 bp per side (incl. borrow). Return = short P&L % of entry.
**Control.** Same date, same group-universe, same ADRp tercile, not signalling that day: 3 random names shorted at the
same close with the same exit rule. Excess = signal − control mean.

**PRIMARY (ALL, the survivorship-free universe).** Excess > 0 with **t ≥ 3** on date-cluster means, both halves
(2010–2017 / 2018–2025) positive, majority of years positive, **AND absolute net mean > 0** (a short that only loses
less than random names is not a trade).
**Reported:** SURV vs NONSURV vs ALL (the survivorship read: how much did survivor panels understate shorts?); the same
close-only rule on `liquid_panel_2009` closes (method check vs SURV); holds, win rate, share of trades ended by delisting.
Window: signals 2010-06 → 2025-11 (60-session room before the series ends). Local.

---

## Results (run 2026-09-29, after b276450; `run_breakdown_survivorship.py`, `.log`, trades `logs/breakdown_survivorship_trades.csv`)

**Verdict: FAIL — INVERTED · MECHANISM + REFRAME. The mirror breakdown loses as a short on the survivorship-free universe
and does WORSE than shorting random same-date names. Survivorship was not why the ledger's shorts failed.**

| group | trades | names | short net %/trade | t (abs) | control (random short) | **excess** | t | halves | yrs + | win | ended by delisting |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **ALL (PRIMARY)** | 28,648 | 2,810 | **−1.90** | −12.0 | −1.19 | **−0.71** | **−7.02** | −0.89 / −0.62 | 1/16 | 22% | 0.1% |
| SURV | 13,864 | 1,100 | −2.28 | −9.3 | −1.48 | −0.80 | −4.02 | | 1/16 | 21% | 0% |
| NONSURV | 14,784 | 1,710 | −1.55 | −8.1 | −0.93 | −0.63 | −4.46 | | 3/16 | 24% | 0.3% |
| method check (panel closes) | 16,378 | 1,169 | −2.09 | −8.2 | −1.46 | −0.64 | −2.85 | | 1/16 | 21% | 0% |

- **Survivorship effect is real but small:** non-survivors lose 0.7pp/trade less than survivors (−1.55 vs −2.28), and
  delisting ends only 0.1% of trades inside 60 sessions. It does not turn the short positive.
- **Method check passes:** the same close-only rule on the survivor panel's own closes gives −2.09 vs −2.28 on chain-spot.
- **Every year but 2020 is negative** (2020 +0.98% abs, +0.97pp excess). Win rate 22%: the 2%/prior-close stop and the
  20-EMA exit get hit on the first bounce.
- **Inverted vs random names (t −7.0):** names making a fresh 15-close low in a downtrend bounce more than random names
  in the same volatility tercile — the short-term reversal the dip-in-uptrend and gap-fade work kept touching. Not a
  long signal by itself (post hoc, and the long side of breakdowns is a separate test).

**What it means for the book now.** Stop looking for single-name breakdown SHORTS as a pattern: 0 for 9, now on the
universe that includes the names that died. The short side that has worked here is (a) the gap-up fade in a stock's
own downtrend (PARKED, forward holdout running since 9/28) and (b) the sector-momentum spread as a hedge. If Gabe
wants the reversal lead, it needs its own pre-registration as a LONG ("buy the fresh 15-day low in a downtrend vs a
random same-tercile name"), charged as a new look.
