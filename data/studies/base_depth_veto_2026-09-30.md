# Base depth as a veto on the house breakout — 2026-09-30

**Verdict: NULL · YIELD MECHANISM.** A breakout out of a >33% correction does no worse than a same-date breakout out of a shallow one. A deep base is not disqualifying, and in our data it isn't qualifying either.

- Pre-registered in `run_base_depth_veto.py` and committed before the run (434724e). Log: `data/studies/logs/base_depth_veto.log`. Trades: `logs/base_depth_veto_trades.csv`.
- Origin: the COHR discussion (35% below its June high). Gabe asked whether a base is a positive signal; it isn't (five base definitions are NULL). O'Neil's "deep bases fail" was the one depth axis the ledger hadn't touched.
- Sample: 53,994 house breakouts across 1,428 names, 2010-01 to 2026-09, on `liquid_panel_2009`. Entry at the close, day-low stop judged on the close, EMA20 exit, maximum 60 sessions, % return per trade.
- Depth = peak-to-trough of the prior 252 sessions, using bars up to t−1 only. The median is 34%, so 52% of house breakouts count as DEEP; the ADR ≥ 3% universe corrects hard.

| cell | diff DEEP − not (pp) | t | halves (<2018 / ≥2018) |
|---|---|---|---|
| **PRIMARY**, same date | **−0.02** | **−0.13** | −0.57 / +0.26 |
| R metric | +0.009R | +0.17 | |
| (a) ADR-tercile-matched | −0.03 | −0.15 | +0.04 / −0.06 |
| (b) dist from peak, near / mid / far | +1.32 / −0.07 / +0.49 | +1.33 / −0.26 / +0.60 | |
| (c) O'Neil form, within 10% of the peak | +0.27 | +0.80 | −0.51 / +0.49 |
| COHR cell: depth >33% and ≥20% below the peak | +0.00 | +0.01 | −0.26 / +0.14 |
| depth >50% | −0.02 | −0.06 | |
| depth in ADR units, top vs bottom tercile | −0.08 | −0.39 | |

The per-year diffs alternate in sign (2018 +3.43, 2012 −2.69, 2024 −2.05), which looks like noise, not a regime. Held-the-level share: DEEP 13.5% vs 12.7% (t +1.44).

**MECHANISM.** The payoff of the house breakout does not depend on where the name came from: not the base shape (VCP, Wedge Pop, RMV), not base length (EP base-break, beaten-down), and now not base depth. That is six base definitions NULL. Consistent with Kell/VCP, the date carries the return, not the structure.

**For COHR specifically:** its 35% drawdown is neither a reason to avoid a future breakout nor a reason to want one. The crash-leader veto (buying deep drawdowns *without* a breakout) is a different object and is untouched by this test.

Caveat: `liquid_panel_2009` is not a point-in-time index; the same caveat applies to every row built on it.
