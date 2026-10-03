# 12-1 momentum refinements: skip 15 vs 21, wait for the 20 EMA (2026-10-02)

Script: `run_momentum_entry_refine.py` (pre-registered 7a3606d, before the run). Log: `data/studies/logs/momentum_entry_refine.log`;
table `momentum_entry_refine_2026-10-02.csv`. Same survivorship-free chain_spot panel, universe, formations (2011-01 → 2026-01)
and 10 bp/side as the certified sleeve; every cell is differenced month by month against BASE (the certified rule, this
engine: +1.65%/mo, +0.65pp over EW).

## Verdict: both ideas NULL. Waiting for the EMA leans INVERTED · keep buying the whole decile at the formation close

| cell | arm %/mo | arm − BASE pp/mo | t_NW | halves | years + | invested | new names triggered |
|---|---|---|---|---|---|---|---|
| **S15 [primary 1]** skip 15 sessions | +1.67 | +0.02 | +0.36 | +0.07 / −0.03 | 9/16 | 100% | – |
| **E0.5 [primary 2]** new names wait for dist ≤ 0.5, else cash | +1.54 | **−0.11** | **−2.01** | −0.07 / −0.14 | **4/16** | 97% | 91% after ~3.6 sessions |
| E0.0 wait for close ≤ 20 EMA | +1.52 | −0.12 | −1.86 | −0.09 / −0.15 | 4/16 | 95% | 87% after ~4.2 |
| E1.0 wait for dist ≤ 1.0 (house band) | +1.58 | −0.06 | −1.40 | −0.04 / −0.08 | 6/16 | 98% | 95% after ~2.8 |
| E0.5-T [secondary] capital over held names | +1.65 | +0.01 | +0.13 | +0.03 / −0.02 | 8/16 | 97% | 91% |

Bar: discovery track, M = 5 (Šidák |t| ≥ 2.57), house |t| ≥ 3 governs. Nothing passes.

- **Idea 1 (skip 15 sessions): NULL.** The two scores pick almost the same book; the difference is noise (+0.02pp, t 0.36).
  The 1-month skip already handles "last month's leaders are extended"; trimming it changes nothing.
- **Idea 2 (wait for the 20 EMA): NULL, leaning INVERTED.** Every threshold is negative and the deeper the required
  pullback, the worse (E1.0 −0.06 → E0.5 −0.11 → E0.0 −0.12); both halves negative; 12/16 years negative at the primary.
  **Mechanism:** about 90% of new names pull back to the EMA within ~3–4 sessions anyway, so the wait buys very little
  discount; the ~10% that never pull back are the runners, and sitting them out in cash costs more than the discount earns.
  E0.5-T (spreading the idle cash across names that did pull back) erases the loss but adds nothing (+0.01, t 0.13).
- Same shape as the breakout ledger (`band_runaway_entry`, `pullback_entry_study`): **entry timing inside a good selection
  is irrelevant or harmful.** The parked confirmation-ladder P2 "dip beats non-dip" result does not carry over as an entry
  rule here.
- Cash earned 0 in the E-cells; the T-bill credit on ~3% idle capital is ~0.004pp/mo and changes nothing.

Caveat: chain_spot has closes only, so "ADR" is a close-to-close proxy (smaller than a true high-low ADR; a 0.5 proxy band is
tighter than 0.5 true ADR). The monotone threshold gradient says the conclusion does not hinge on the band width.
