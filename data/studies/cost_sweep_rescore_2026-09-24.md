# False-negative check: the 9/22 cost-sweep casualties re-scored at the MEASURED slippage (2026-09-24)

**Question.** `fill_slippage_2026-09-24` found real fills pay **0.20 of the quoted spread against the arrival quote**
(0.13 at the fill minute), against the model's 0.25. Did the cost model kill any strategy that would survive at 0.20?

**Method.** No engine reruns were needed. Slippage enters `costs.leg_cost` linearly, and commission is part of the
same gap, so moving from 0.25 to 0.20 recovers **at most 20% of each trade's gross-minus-net gap**. Each strategy was
re-scored per trade at that **best case** (net + 0.2 × (gross − net)), from the saved 9/22 trade files, with the same
month-clustered t. UUP was priced by crossing the full spread, not through `leg_cost`, so it was re-run directly at
mid − 0.20 × spread on its cached chain (no file written). XLF (2026-09-08 playbook review) has no per-trade file;
bounded from its table.

## Result: none revives

| strategy | n | gross | net @ 0.25 | **best case @ 0.20** | t (best) |
|---|---|---|---|---|---|
| ASHR bull put | 284 | +6.04% | −5.10% | **−2.87%** | −0.50 |
| XOP bull put | 374 | +3.79% | −3.09% | **−1.71%** | −0.23 |
| SQQQ bear call | 271 | +10.04% | −2.29% | +0.18% | −0.49 |
| TMF bear call | 148 | +9.63% | −1.66% | +0.60% | −0.48 |
| ASHR bear call | 232 | +8.19% | +1.18% | +2.58% | 0.31 |
| UVXY combined | 374 | | −3.46% (t −2.65) | **negative** | −1.49 |
| UVIX bear call | 139 | +11.0% | −8.8% (t −2.81) | **negative** | −1.29 |
| UUP straddle (re-run at 0.20) | 148 | | +0.52% (t −0.31) | +1.02%, month-wtd +0.26% | 0.35 |
| XLF regime (bound from the table) | | +6.1% | −4.6% | ≤ −2.5% | — |

Even at a cost model that flatters them, the nine are negative or indistinguishable from zero. **The 9/22 retirements
stand.**

The non-retired Tier U spreads also stay uncertified at the best case: BJ t 1.78, SOXX 1.08, CLS 1.40, GLD 1.64,
TLT 1.30, INDA 0.96, USO 1.40.

⚠ **One flag, not a revival: GEV bull put, best case +7.40%, t 3.55, halves +9.1 / +10.4.**
- It is an upper bound on 76 trades over **23 months (2024+ only)**, picked from a **60-cell sweep** (Šidák p 0.16 at
  0.25).
- With 22 degrees of freedom, a t of 3.55 is below the ~3.9 a 60-cell correction would demand.
- Per `optionsplay_spec_2026-09-24` and `cw_play_2026-09-22`, single-name bull puts in a runaway uptrend are largely
  **beta**. GEV's 2024–25 run is exactly that case.
- **Not reopened.** If anyone wants it, the test is GEV bull put vs delta-matched GEV stock, not another sweep.
