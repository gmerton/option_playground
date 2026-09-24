# Cash-secured puts ranked by yield across names: NULL (2026-09-24)

`run_csp_yield_rank.py` (pre-registered in its docstring). Log: `logs/csp_yield_rank_2026-09-24.log`; per-put CSV
`csp_yield_rank_2026-09-24.csv`. Source claim: OptionsPlay "Screen Both Legs of the Wheel" (VSLc-kHxFlw) ranks
short-put ideas by yield. New axis: the BCI study set each name's strike by a yield *target*; it never ranked names
against each other at a fixed delta.

**Setup.** BCI cache, 0.30Δ puts, ~326 names, Fridays 2018-01 → 2026-02, real bid/ask (sold at mid − 25% of spread
plus commission), held to expiry. Quintiles of yield = premium / (strike − premium), formed within each entry date.
The primary measure is the put's **excess over the stock held at the put's entry delta**, i.e. the part that is premium
and not direction.

## Result

| W (~7 DTE) | yield | IV | put return | median | excess vs delta-stock | win % | worst 1% |
|---|---|---|---|---|---|---|---|
| Q1 | 0.48% | 0.23 | +0.003% | +0.38% | −0.055 | 81.8 | −9.5% |
| Q3 | 0.91% | 0.35 | +0.008% | +0.73% | −0.070 | 78.1 | −15.8% |
| Q5 | 2.26% | 0.74 | +0.257% | +1.53% | −0.005 | 76.8 | **−29.0%** |

- **PRIMARY: Q5 − Q1 excess +0.04pp/week, t 0.65. Halves −0.08 / +0.16 (opposite signs). PRE-REGISTERED PASS: NO.**
- Secondary: raw put return Q5 − Q1 +0.25pp, t 3.02 (weekly); monthly tenor +1.03pp, t 3.73. **Monthly excess
  −0.10pp, t −0.38.** Q5's excess on its own: −0.02pp (t −0.21) weekly, −0.27pp (t −0.87) monthly.

## Reading

**NULL · YIELD: MECHANISM.** Ranking by yield at a fixed delta sorts on IV level (0.23 → 0.74), which sorts on
**beta**. In a rising 2018–26 sample the high-yield puts made more money, but exactly as much as holding those names'
stock at the same delta would have, and with a tail three times deeper. The premium beyond direction is zero in every
quintile. The raw-return t of 3 is the "high-vol names went up" effect, not a seller's edge.

It fits the rest of the ledger:
- BCI CSP = stock at delta minus costs;
- the credit/width bull-put play is −2.43pp vs delta-matched stock even in its top quintile (`cw_play_2026-09-22`).

⚠ **Implication for the credit/width result:** its cross-sectional sort was scored on ROC, not against delta-matched
stock. This test suggests that part of what credit/width ranks is beta too. The cw_play benchmark already pointed
that way. Treat credit/width as a filter that avoids the worst spreads, not as a premium harvest.
