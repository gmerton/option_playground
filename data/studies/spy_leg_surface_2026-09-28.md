# SPY leg-return surface — step 1 of the vol-selling structure search (2026-09-28)

**Why:** any structure's P&L is the sum of its legs' P&L, so step 1 maps where the premium lives, leg by leg, at real fills. Step 2 (a CVaR-constrained optimiser) waits on this map.
**Scripts:** `run_spy_chain_v3_pull.py` (11.46M rows, SPY puts + calls, DTE 0–70, 2010-01 → 2026-03, zero duplicate keys, `data/cache/spy_chain_v3/`) and `run_spy_leg_surface.py` (pre-registration in the docstring). **Logs:** `logs/spy_leg_surface.log`, `logs/spy_leg_surface_robust.log`. Full table: `spy_leg_surface_2026-09-28.csv` (400 cells).

## Design
- **Cells:** 2 types × 8 |delta| × 5 DTE, entered every trading day. Sell one contract at mid − 25% of the spread − commission, hold to expiry, settle on SPY's close. Units: bp of notional.
- **States:** ALL / STRESS (SPY < 50 SMA & VIX ≥ 20; 16.8% of days) / CALM / GAMMA± (dealer GEX sign).
- **Pre-registered bar:** Šidák 3.42 for ALL, 3.84 for a state, plus both halves positive.

⚠ **The pre-registered month clustering overstated t for tenors ≥ 30 DTE.** Daily entries overlap across months. The robustness pass uses **one entry per expiry** (non-overlapping), quarter clustering, and **episode clustering in STRESS** (37 episodes). Those t-stats govern below.

## What the map says
1. **Calls carry no premium.** Short calls at ≥ 0.16Δ lose money at every tenor and in every state (ALL 30-DTE 0.30Δ −19 bp, t −2.6). The only positive call cell is the 5Δ short-dated call on positive-gamma days: +1.5 bp, t 5.5 non-overlapping, economically tiny. **The call side of a strangle or condor is dead weight or worse.**
2. **Unconditionally, the premium is in short-dated far-OTM puts.**

   | cell | bp per trade (non-overlap) | t (non-overlap, quarter-clustered) | win | 1st percentile | worst |
   |---|---|---|---|---|---|
   | P 7d 5Δ | +3.8 | 5.24 | 98% | −79 | −616 |
   | P 7d 10Δ | +6.0 | 4.46 | 95% | −193 | −758 |
   | P 14d 5Δ | +5.8 | 2.90 | 98% | −144 | −778 |
   | P 1d 5Δ | +1.3 | 3.74 | 98% | −66 | −270 |

   Longer unconditional tenors fade once overlap is removed: P 30d 16Δ t 3.28 → **1.57**; P 45d 16Δ 2.90 → 2.64; P 14d 16Δ 3.19 → 2.25.
3. **In the stress regime, 45-DTE OTM puts are extraordinarily consistent:**

   | STRESS cell | bp | t (episode-clustered) | win | episodes negative | worst |
   |---|---|---|---|---|---|
   | P 45d 5Δ | +28.9 | 16.8 | 100% | 0 / 33 | +16 |
   | P 45d 10Δ | +57.3 | 17.0 | 100% | 0 / 33 | +32 |
   | P 45d 16Δ | +89.0 | 12.6 | 98% | 0 / 32 | −199 |
   | P 45d 25Δ | +124.1 | 9.2 | 93% | 0 / 33 | −409 |
   | P 30d 16Δ | +45.7 | 5.2 | 93% | 2 / 34 | −1,574 |

   This extends the certified cell (the always-on-put study's certified subset: 32/32 episodes positive). ⚠ **What this t-stat measures is consistency inside a sample where every stress episode recovered within ~45 days.** v3 has no 2008, which was a stress regime that kept falling for five months. One such episode would sit far outside this table's worst row. That is the tail the optimiser has to price, and the data cannot show it.
4. **Negative gamma:** 45-DTE puts are positive (10Δ +27 bp) but t falls from 8.1 to **3.07** non-overlapping, with a worst trade of −1,937 bp. Weaker than STRESS, and it overlaps it.
5. **Costs are small on SPY** (gross − net ≈ 0.3–1 bp, ~5% of edge), except 1-DTE far-OTM, where they take about a fifth (1.64 → 1.29 bp).

## Verdict (a map, not a strategy)
Premium after costs is concentrated in **(a) short-dated far-OTM puts, unconditionally** and **(b) 30–45-DTE OTM puts in the stress regime**. Calls add nothing. The multi-leg question is therefore a **risk-shaping** question: buying wings or calls costs edge. A 5- or 6-leg structure can only win on CVaR per unit of margin, not on mean.

**Step 2 inputs:** a per-contract $ and margin normalisation, the non-overlapping scenario matrix (one entry per expiry), shrinkage toward this map, a leg cap of about 4, walk-forward by year, and a synthetic 2008-style stress scenario, because the data has none.
