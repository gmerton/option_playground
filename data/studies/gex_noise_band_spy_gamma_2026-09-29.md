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

---

## Results (run 2026-09-29, after the pre-registration above was committed in 739f4be; `run_gex_noise_band_spy_gamma.py`, `.log`, `.csv`; SPY engine log `logs/noise_band_spy_game.log`)

**Verdict: NULL, both cells. The 9/21 QQQ near miss does not survive the audit's fix: switching to the certified SPY
gate WEAKENS it, and it does not replicate on SPY. Family verdict (4 looks): NULL.** Window 2010-01-05 → 2026-02-27,
SPY GEX negative on 57.4% of sessions.

| cell | arm N mean | t (bar 3.4) | halves bps (t) | N − P (Welch t) | beats A |
|---|---|---|---|---|---|
| Q: QQQ engine, SPY gate | +2.75 bps | **2.16** | −0.34 (−0.25) / +6.75 (2.85) | +3.55 (2.35) | yes (A +1.24) |
| S: SPY engine, SPY gate | +1.04 bps | **1.01** | −0.33 (−0.28) / +2.81 (1.56) | +1.73 (1.44) | yes (A +0.30) |

- The certified gate does worse than QQQ's own gate (t 2.16 vs 2.92), and the first half turns negative in both cells.
- What does replicate is the weak shape — positive-gamma sessions lose a little (t −0.98 / −1.10), so skipping them
  helps — but nothing on negative days clears any bar. Both N arms are carried by 2018 and 2022 (cell Q: 23.8% + 18.3%
  of $10k out of a 2010–26 sum of ~62%).
- SPY and QQQ gamma signs agree on 76.8% of days, so the gates differ enough for this to be a real change of test.

**What it means for the book now.** Today is a negative-gamma tape, and gamma-gated noise-band momentum is not a trade on
either index. Close the family: the GEX regime stays a certified *volatility* mechanism (t 7.7) that does not
convert into intraday momentum P&L. No paper log is warranted.
