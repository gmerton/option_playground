# Dealer gamma exposure (GEX): does it predict the day, the intraday trend, or the expiry close? (2026-09-21)

## Pre-registration (written BEFORE any data was pulled; do not edit this section after the results)

**Why.** Nick Ireland (review 2026-09-21, 2/5) and Chris Creamer (IQCapital review 2026-09-20, 2.5/5) both trade off
dealer gamma: negative gamma = bigger, trending days; positive gamma = calm, mean-reverting days; large-gamma strikes
pin price. Published work on dealer hedging supports the regime idea for index ETFs. We have never measured it.

**Data.** `silver.options_daily_v3` (open interest + vendor gamma, complete 2010-01 → 2026-02 for SPY/QQQ; the feed
loses OI in 2026-03/04 and gamma from 2026-05, so the window ends 2026-02-27). 1-min SPY and QQQ regular-session bars
(`data/cache/intraday_hist/`). VIX daily close from yfinance (^VIX). **SPY is primary; QQQ is a robustness check, not
independent evidence** (they move together).

**Gamma exposure for day t, from day t−1's close (no look-ahead).** Per strike, over every listed expiry:
GEX = Σ(call OI × call γ) − Σ(put OI × put γ), × 100 × S² × 0.01 (dollars per 1% move), S = day t−1's close, strikes
within ±20% of S. This is the standard "naive" convention (customers long calls, short puts; dealers the other side);
the true dealer sign is unobservable. Net GEX_t = sum over strikes. **Negative-gamma day = net GEX_t < 0.**
⚠ Known blind spot: 0DTE opened and closed intraday never shows in open interest.

**Test 1: the regime (PRIMARY).** Day t outcome = log realised volatility from 1-min log returns (09:30–16:00).
Regression: log RV_t = a + b·NEG_t + c·log VIX_{t−1} + d·log RV_{t−1} + e. Newey-West t on b (5 lags).
Also reported: the same with day range (high−low)/open, and b without the controls (to show how much VIX explains).
**Pass:** b > 0 with t ≥ 3 on the full sample, AND b > 0 in both halves (2010–2017, 2018–2026-02), on SPY.

**Test 2: intraday momentum.** r_first = prior close → 10:00; r_last = 15:30 → 16:00 close. Regression:
r_last = a + b·r_first + g·(r_first × NEG_t) + e, Newey-West t (5 lags). The claim: g > 0 (momentum stronger on
negative-gamma days). **Pass:** g > 0, t ≥ 3, positive in both halves, on SPY.

**Test 3: the pin, expiry days.** Expiry day = a listed SPY expiry equals day t (weekly/monthly early, daily from
2022). K* = the strike with the largest |GEX| (from day t−1) within ±2% of day t's open. Attraction =
(|open − K*| − |close − K*|) / open, in bps (> 0 = the close moved toward K*). Control: the same measure for a
uniformly random listed strike within ±2% of the open (20 draws per day, averaged). Also reported: K*_OI = the
largest-open-interest strike of the EXPIRING series, and non-expiry days (pre-2022) as a second control.
**Pass:** expiry-day attraction to K* > the random-strike control, t ≥ 3 (days), positive in both halves, on SPY.

**Not tested (named so they can't be added quietly):** alternative dealer-sign conventions, GEX magnitude buckets or
the "zero-gamma flip" level, any trading rule built on these, single stocks, entries at gamma levels.
One definition per test, one run.

---

## Results (run 2026-09-21, after the pre-registration above; script `run_gex_regime_pin.py`, log `.log`, table `.csv`)

**Verdicts: Test 1 (regime) PASS · Test 2 (momentum) FAIL, right sign, UNDERPOWERED · Test 3 (pin) FAIL as registered;
a labelled post-hoc diagnostic shows the pin is NULL, not inverted (the registered control was biased).**
Data: SPY 3,985 days (2010-01-05 → 2026-02-27, 57% negative-GEX days); QQQ 3,680 days (from 2010-11, 53% negative).

### Test 1 — regime (PRIMARY): PASS

log realised vol (1-min) on NEG, controlling for log VIX(t−1) and log RV(t−1), Newey-West t:

| | days | NEG effect on RV | t | halves (effect) | same, day range | no controls |
|---|---|---|---|---|---|---|
| **SPY** | 3,985 | **+8.1%** | **7.7** | +6.5% (t 4.6) / +9.5% (t 5.9) | t 8.7 | RV 0.84% vs 0.49% (t 20) |
| QQQ | 3,680 | +4.0% | 4.1 | +2.1% (t 1.8) / +6.4% (t 4.3) | t 6.9 | RV 1.05% vs 0.67% (t 17) |

Negative-gamma days are ~1.7× as volatile as positive-gamma days raw; most of that is the VIX (the two move
together), but **~8% extra realised vol on SPY survives both VIX and yesterday's vol**, in both halves.

### Test 2 — intraday momentum (first 30 min → last 30 min × NEG): FAIL

SPY interaction +0.057 (t 2.0), both halves positive (t 1.4 / 1.4); QQQ +0.051 (t 1.7). The sign the claim predicts,
not strong enough. UNDERPOWERED rather than null.

### Test 3 — expiry pin: FAIL as registered (−5.4 bps, t −4.2 on SPY expiry days: the close moved AWAY from K*)

⚠ **The registered control was biased, and that explains the sign.** The largest-|GEX| strike sits a median 64 bps
from the open (the ATM strikes carry the most gamma), while a uniformly random strike within ±2% sits ~100 bps away. Any
move away from the open then counts against K* more than against the random strike. **Post-hoc diagnostic (NOT the
verdict):** compare K* with its mirror strike, the same distance from the open on the other side. SPY expiry days
+0.6 bps (t 0.3), non-expiry −1.7 (t −0.8); QQQ +1.6 (t 0.5) / +0.6 (t 0.2); no half-period cell above |t| 1.6.
**There's no measurable pin toward the largest-gamma strike, on expiry days or otherwise.**

## What it means

- **Nick Ireland / Creamer's regime claim holds** as a volatility statement: negative-gamma days are more volatile than
  the VIX and yesterday's vol predict. It says nothing about direction.
- **"Gamma strikes are magnets" does not** show up in 16 years of SPY or QQQ closes.
- **For the desk:** a volatility input, not a signal. It supports smaller size or wider stops on negative-gamma days
  (his sizing rule), untested as a P&L rule.
- **Follow-up lead (queued):** if negative GEX raises realised vol beyond the VIX, short-dated index options may be
  UNDER-priced on those days. Test SPY 1–2 DTE implied vs realised (or ATM straddle P&L) by GEX sign, on real bid/ask.
- Live use needs today's GEX: Tradier chains carry OI and greeks, so it's computable daily going forward.
