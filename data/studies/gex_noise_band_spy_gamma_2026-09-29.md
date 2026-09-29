# Noise band gated on SPY dealer gamma: QQQ re-gate + SPY-underlying replication (2026-09-29)

## Pre-registration (written BEFORE anything was run; do not edit this section after the results)

**Why.** Audit step 3 item 4b (`audit_top_down_2026-09-25.md` List A #1, named defect: "own-GEX gate when the
confirmed mechanism is SPY GEX"). The 9/21 QQQ sign split (t 2.92) gated on QQQ's own GEX; the certified regime
mechanism is SPY's (t 7.7). The dose-response (`gex_noise_band_dose_2026-09-29.md`) was NULL: gamma acts by sign, not
depth — so this test keeps the sign gate and changes only whose gamma it is, then checks the underlying.

**Engine.** `run_noise_band.py <TK>` default game mode, UNCHANGED (as in 9/21): $10k fixed/session, IBKR fixed +
$0.005/sh slippage, lookback 14, long/short, VWAP stop, :00/:30 decisions, next-bar-open fills, flat at close.
Net daily P&L % of $10k; no-trade sessions = 0.

**Gate.** SPY net GEX via `run_gex_regime_pin.gex_series("SPY", ...)` (naive sign, ±20% strikes), PRIOR session's
value attached to day t. Window = sessions with a prior-day SPY GEX, ≤ `base.END` (2026-02-27).

**Two cells, both pre-registered, each judged alone.**
- **Cell Q:** QQQ noise band, gated on SPY GEX < 0.
- **Cell S:** SPY noise band, gated on SPY GEX < 0 (the SPY-underlying replication).

**Metrics.** Same as 9/21: arms A (all), N (negative), P (positive); mean bps/session, t on daily P&L, Sharpe,
annualised own / flat-on-skipped, halves split 2018-01-01, by year; N − P Welch t.

**Pass bar (per cell).** Arm N mean > 0 with **t ≥ 3.4**, positive in both halves, and beats arm A.
**Charge:** this family has now had four looks (QQQ-own sign 9/21, dose 9/29, these two cells) → Šidák k = 4 on the
|t| ≥ 3 bar → 3.4.

**Reading.** Cell S passing = the gamma-gated noise band replicates on a second underlying with the certified gate —
the strongest result available here, still a HYPOTHESIS until it holds on paper from 2026-09-22. Cell Q alone passing
= the gate fix works but only on QQQ. Neither = the 9/21 near miss was QQQ-specific noise → NULL.

**Not tested:** engine parameters, magnitude/percentile buckets (dose was NULL), VIX conditioning, other tickers.
