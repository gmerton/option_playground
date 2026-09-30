# Reversal LONG: buy a fresh 15-close low in a downtrend (2026-09-30)

## Pre-registration (written BEFORE the run; do not edit this section after the results)

**Why.** The mirror-breakdown short came back INVERTED (9/29, `breakdown_survivorship_2026-09-29.md`): names making a fresh 15-close low in a downtrend beat random same-tercile names by 0.71pp as shorts, t −7.02, on the survivorship-free universe. That lead is **post hoc**, so this is charged as a NEW look. Gabe (2026-09-30) asked for it as test 1 of 3. Goal: a stock-buying strategy for the current regime.

**Data.** Same as the parent: `run_dip_survivorship.pull()` + `adjust_and_clean()` (chain-spot parity closes, split-adjusted, ~10.8k optionable tickers including delisted, 2010 to 2026-02). Closes only. Groups: SURV (in `liquid_panel_2009`), NONSURV, and **ALL**.

**Signal.** Identical to the parent short, byte for byte (`run_breakdown_survivorship.signals_and_trades` logic):
- Liquidity: 50-session mean option volume ≥ 1,000 and close ≥ $5.
- ADRp ≥ 3%.
- Downtrend: SMA10 < SMA20 < SMA50 on each of the last 5 sessions.
- Breakdown: close below the lowest close of the prior 15 sessions, first break only.
- Day's change ≥ −8%.

**Trade (long side, NOT the short's mirror).**
- **PRIMARY entry:** the close of the session AFTER the signal (t+1). This is declared to strip closing-print noise and bid-ask bounce. Parity closes are noisy, and a noisy low reverts mechanically. That is exactly the "clean result is a bug" artefact to rule out.
- **Exit:** a fixed hold of 10 sessions after entry, close to close. No stop (close-only data; the aim is to measure the effect, not manage it).
- **Costs:** 10 bp per side. A series that ends inside the window exits at its last close.

**Control.** 3 random names on the same date from the same group-universe and the same ADRp tercile, not signalling. They get the same entry day and the same hold. Excess = signal − control mean.

**PRIMARY (ALL, t+1 entry, 10-day hold).** Every condition must hold:
- excess > 0 with **t ≥ 3** on date-cluster means;
- both halves (2010–2017 / 2018–2025) > 0;
- a majority of years > 0;
- **absolute net mean > 0**.

**Pre-declared checks (each reported; for ADOPT each must keep the sign):**
- (a) **Crash-leader veto:** the excess and absolute net must stay > 0 in a HEALTHY tape (SPY close > its 50-day SMA and the SMA rising over 10 sessions) as well as in an unhealthy one. If the edge lives only in unhealthy tapes, it is a bear-rebound effect and is sized to that regime only.
- (b) **Concentration:** the share of summed excess from the top 1% of trades. Above 50% means one-off events, not a rule.
- (c) **Method check:** the same rule on `liquid_panel_2009`'s own closes (SURV) should give the same sign.

**Secondary (Sidak k = 4, |t| ≥ 2.8; the house bar of 3 governs any claim):**
- entry at the signal close t (how much the skip-day removes);
- 5-day and 20-day holds;
- SURV vs NONSURV.

**Also reported:** the cell matching today's regime (SPY just above its 50-day). Script: `run_reversal_long.py`. Local: the cache already exists.

---
## Results (run 2026-09-30, after 26c0f07; `run_reversal_long.py`, log `logs/reversal_long.log`, trades `logs/reversal_long_trades.csv`)

**Verdict: NULL · YIELD MECHANISM.** The lead does not survive as a long.

| cell | n | long net %/trade | excess vs random same-tercile | t | halves | yrs + |
|---|---|---|---|---|---|---|
| **PRIMARY** ALL, t+1 entry, 10d | 28,618 | +1.20 | **+0.34** | **2.91** | +0.36 / +0.34 | 10/16 |
| (a) HEALTHY tape | 10,012 | **+0.11** | +0.15 | 1.57 | | 9/16 |
| (a) UNHEALTHY tape | 18,606 | +1.78 | +0.44 | 2.91 | | 12/16 |
| (c) method check, panel closes (SURV) | 16,357 | +1.39 | +0.18 | **−0.73** | +0.09 / **−0.25** | |
| secondary: entry at t close | 28,648 | +1.22 | +0.41 | 3.15 | | |
| secondary: t+1, 5d | 28,618 | +0.68 | +0.28 | 3.20 | | 13/16 |
| secondary: t+1, 20d | 28,618 | +1.94 | +0.30 | 2.43 | | |

- **Primary misses** the bar (t 2.91 < 3), although both halves are positive and absolute net is > 0.
- **(b) Concentration fails outright:** the top 1% of trades carry **114%** of the summed excess. The other 99% net slightly negative vs control.
- **(c) The method check does not reproduce** on real exchange closes: t −0.73, back half negative. The chain-spot parity series is where the effect lives. The skip-day entry removed only ~0.07pp, so the remaining gap between the two price series is unexplained noise, not an edge I'd trade.
- **(a) Crash-leader veto:** in a healthy tape the trade is flat (+0.11% absolute, t 1.57). What there is lives in unhealthy tapes, which is ordinary bear-market rebound beta plus a little reversal.
- The 5-day secondary (t 3.20) is a secondary under k = 4 with the same concentration problem; no claim.

**MECHANISM.** Most of the parent short's t −7.02 was its asymmetric exit, not reversal. A 2% / prior-close stop plus a 20-EMA exit gets stopped on the first bounce; random names bounce less. A symmetric fixed hold leaves a small, concentrated, series-dependent residue.

**What it means for the book now.** No new stock-buying rule. Today's tape (SPY just above its 50-day, breadth OFF) sits between the two cells, and neither clears the bar. Do not buy fresh 15-day lows.
