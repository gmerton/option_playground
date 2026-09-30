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
