# QQQ noise band: gamma-depth dose-response with a VIX control (2026-09-29)

## Pre-registration (written BEFORE anything was run; do not edit this section after the results)

**Why.** Audit step 3 item 4 (`audit_top_down_2026-09-25.md` list A #1; TEST_INDEX §10 row "QQQ noise band:
gamma-depth dose-response"). The sign split (`gex_noise_band_2026-09-21.md`) was a near miss: negative-gamma arm
+4.16 bps/session, t 2.92. A sign split can be one lucky bucket. If dealer short gamma is the mechanism, the edge
should grow **steadily** as gamma gets more negative, and it should survive holding the VIX level fixed (negative
gamma and high VIX travel together). Current regime (9/28): QQQ/SPY GEX negative, VIX ~16, so a pass would matter
for what we trade.

**Unit.** The unchanged engine output `data/cache/gex/noise_band_qqq_game_daily.csv` (`run_noise_band.py QQQ`,
default game mode: $10k fixed per session, IBKR commissions + $0.005/sh, lookback 14, long/short, VWAP stop,
:00/:30 decisions, flat at close). Net daily P&L, % of $10k; sessions with no trade count as 0. One obs per session.

**Gamma.** QQQ net GEX from `run_gex_regime_pin.gex_series` (naive sign, ±20% strikes), the PRIOR session's value
attached to day t, same as the 9/21 test. Because the dollar scale grows with price² and OI, GEX is converted to a
**trailing 252-session percentile rank** (known at t−1; min 252 sessions of history → window starts ~a year after
2010-11). **Quintiles Q1…Q5 of that rank, Q1 = most negative gamma.** Score = 5 − quintile (Q1 → 4 … Q5 → 0),
so a positive slope means "more P&L as gamma falls".

**VIX control.** VIX close at t−1 (`data/cache/vix_daily_long.parquet`), terciles over the window (a control, not a
signal, so full-sample cuts are acceptable).

**Primary (one test, two conditions, both required).**
1. **Dose-response:** OLS `net ~ score`, Newey-West 5 lags. Slope > 0 with **t ≥ 3.2**, and the slope positive in
   both halves (split 2018-01-01).
2. **Beyond VIX:** OLS `net ~ score + VIX-tercile dummies`, NW 5 lags. Gamma slope > 0 with **t ≥ 3.2**.

**Multiple-testing charge.** This is the second look at the same sessions (the sign split was the first): k = 2,
Šidák on the |t| ≥ 3 bar → t ≥ 3.2.

**Reported, exploratory only:** mean bps / t / share negative-GEX per quintile; per-VIX-tercile slopes; per-year
Q1−Q5; the sign split re-run on the rank window for comparability.

**What a pass means / doesn't.** A pass makes gamma-gated QQQ noise-band a HYPOTHESIS to run on paper from
2026-09-22 forward (no size). A fail leaves the 9/21 verdict UNDERPOWERED → NULL for the dose claim.

**Not tested:** any engine parameter change, SPY GEX substituted for QQQ's (that is the separate SPY-underlying
replication), raw-dollar GEX quintiles, pre/post-2022, day-of-week, event days.

---

## Results (run 2026-09-29, after the pre-registration above was committed in 8d35b53; `run_gex_noise_band_dose.py`, `.log`, `.csv`)

**Verdict: NULL — no dose-response. YIELD MECHANISM: whatever gamma does here, it does it by sign, not by depth.**
Window 2012-03-23 → 2026-02-27 (3,429 sessions after the 252-session rank warm-up).

- **Primary 1:** slope +1.36 bps per quintile step, **NW t 2.24** (bar 3.2); halves +1.31 (t 1.90) / +1.42 (t 1.54). Fails on t.
- **Primary 2 (with VIX-tercile dummies):** slope +1.07, **t 1.87**. Fails. Adding VIX shrinks the slope ~20%.
- **Not monotone.** Q1 (most negative) +3.74 bps t 1.42 · Q2 +0.50 · **Q3 +8.04 t 4.38** · Q4 +0.49 · Q5 −3.10 t −2.70.
  Q2 is 91% negative-GEX sessions and earns nothing; the best bucket is Q3, the zero-crossing quintile (54% negative).
  The depth story predicts Q1 > Q2 > Q3; the data give Q3 ≫ Q1 > Q2. Q3's t 4.38 is one of five buckets, post hoc — not a finding.
- **Within VIX terciles:** slope t 1.57 / 1.81 / 0.21 (low / mid / high VIX) — nothing inside any tercile.
- **Sign split on this shorter window:** NEG +4.57 bps t 3.07, POS −0.88 t −1.03 — essentially the 9/21 result
  (a second look at the same sessions; it does not upgrade that verdict). Per year Q1−Q5 is negative in 2015, 2023, 2024.

**What it means for the book now.** Today is a negative-gamma, mid-VIX tape. This test says deeper negative gamma does
not make the QQQ noise band better, and inside the mid-VIX tercile there is no gamma slope at all (t 1.81, Q1 −1.48 bps).
Nothing to trade. The sign-gated arm stays UNDERPOWERED; the only honest route left is a forward paper log from
2026-09-22 of NEG-day sessions, and the SPY-GEX replication (audit item 4b) is still unrun.
