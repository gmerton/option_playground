# QQQ noise-band intraday momentum, gated by dealer-gamma sign (2026-09-21)

## Pre-registration (written BEFORE anything was run; do not edit this section after the results)

**Why.** GEX follow-up item 3. The regime test (gex_regime_pin_2026-09-21.md) found negative-gamma days more volatile
beyond the VIX (SPY t 7.7, QQQ t 4.1) and a same-sign but underpowered momentum interaction (t 2.0). The published
mechanism for intraday momentum is dealer short gamma. Our QQQ noise-band replication (qqq_noise_band_replication_
2026-09-17.md) made 2.5%/yr net, Sharpe 0.28, dead 2009–17. **Does trading it only on negative-gamma days revive it?**

**Engine.** `run_noise_band.py QQQ` with its DEFAULT configuration, unchanged: game mode ($10,000 fixed each session,
1x, no compounding, IBKR fixed commissions + $0.005/sh slippage), lookback 14, long/short, VWAP stop on, decisions
at :00/:30, next-bar-open fills, flat at the close. Run once over the full file; its per-session daily net P&L (% of
the $10k) is the unit. Sessions are independent in game mode, so gating = keeping or skipping whole sessions.

**GEX.** QQQ net GEX from `data/cache/gex/QQQ_gex_strikes.parquet`, computed exactly as
`run_gex_regime_pin.gex_series` (naive sign: calls +, puts −; strikes within ±20% of the close; × 100 × S² × 0.01),
the PRIOR session's value attached to day t. Window = sessions with a prior-day QQQ GEX: 2010-11-23 → 2026-02-27.

**Arms.** (A) all sessions in the window (baseline); (N) negative prior-close GEX only, flat otherwise; (P) positive
only. Sessions with no signal count as 0 in their arm.

**Metrics.** Mean daily net P&L, annualised (×252 over the arm's own sessions and over ALL window sessions, i.e.
sitting flat on skipped days), Sharpe, t on daily P&L (days are the unit; one observation per session), halves
2010–2017 / 2018–2026-02, by year.

**Pass bar.** Arm N: mean daily net > 0 with t ≥ 3, positive in both halves, AND its mean daily net beats arm A's.

**Not tested:** any parameter change (lookback, decision times, stops, sizing, long-only), SPY GEX substituted for
QQQ's, vol-targeted "paper" mode, GEX magnitude buckets. One run.

---

## Results (run 2026-09-21, after the pre-registration above; `run_gex_noise_band.py`, `.log`, `.csv`)

**Verdict: FAIL on the pre-registered bar, narrowly (arm N t 2.92 vs 3.0) → UNDERPOWERED / near-miss. MECHANISM
consistent: the strategy's P&L lives on negative-gamma sessions; positive-gamma sessions lose.** Baseline reproduced
(full file 2007–2026: net 2.5%/yr, Sharpe 0.28, t 1.22).

Window 2010-11-23 → 2026-02-27, 3,680 sessions, 52.6% negative-GEX. Net daily P&L as % of the fixed $10k:

| arm | sessions | mean / session | ann. (own sessions) | ann. (flat on skipped) | Sharpe | t | 2010–17 | 2018–26 |
|---|---|---|---|---|---|---|---|---|
| A all | 3,680 | +1.65 bps | 4.2% | 4.2% | 0.51 | 1.95 | −0.53 bps (t −0.5) | +3.46 (t 2.6) |
| **N negative GEX** | 1,936 | **+4.16 bps** | 10.5% | 5.5% | **1.05** | **2.92** | +1.21 (t 0.7) | +6.26 (t 3.0) |
| P positive GEX | 1,744 | −1.14 bps | −2.9% | −1.4% | −0.52 | −1.37 | −2.14 (t −2.0) | −0.15 (t −0.1) |

N minus P: +5.29 bps/session, Welch t 3.22. Arm N passes three of four conditions (positive, both halves positive,
beats A) and misses t ≥ 3 by 0.08.

**Caveats that change interpretation.** (1) Arm N's total is concentrated: 2018 (+28.7% of $10k) and 2022 (+20.2%)
are ~two-thirds of its summed P&L; the first half is +1.2 bps/session, t 0.7. (2) It still sits in the dead zone early:
2013, 2016, 2017 negative on negative-GEX days too. (3) Gating mostly works by SKIPPING positive-gamma sessions, which
lost in 2010–17 (t −2.0); "flat on skipped days" annualises to 5.5%/yr vs 4.2%. (4) One run, default engine, no
parameter changes; QQQ's own GEX, naive sign.
