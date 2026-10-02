# AVWAP confluence at Luk-style tight-stop entries (2026-10-01)

**Verdict: PRIMARY NULL; the swing-high anchor is INVERTED.** Script `run_luk_avwap_confluence.py` (pre-registered
f8c1ca4 before scoring), ECS, 2 min. Log `logs/luk_avwap_confluence.log`. Same 13,410 entries as the tight-stop test;
half of them (50%) have their pullback low within 0.25 ADR of at least one of four anchored VWAPs.

| cell (TIGHT net - BETA, date-cluster) | trades | mean | t | halves | quarters + |
|---|---|---|---|---|---|
| **PRIMARY: ANY anchor** | 6,646 | **-0.05pp** | **-0.26** | +0.20 / -0.31 | 3/8 |
| A1 swing high (60d) | 2,396 | **-0.48pp** | **-3.20** | -0.42 / -0.54 | 2/8 |
| A2 swing low (20d) | 3,737 | +0.22pp | +0.69 | +0.70 / -0.29 | 3/8 |
| A3 gap day | 1,949 | -0.36pp | -2.40 | -0.27 / -0.45 | 2/8 |
| A4 volume day | 2,266 | -0.33pp | -1.33 | -0.60 / -0.07 | 4/8 |

Reported: ANY minus NOT-ANY +0.01pp (t 0.05). By the number of confluent anchors: 0 -> -0.06, 1 -> +0.10, 2+ -> -0.23pp.
**More confluence is not better.** On the WIDE arm, ANY gives +0.06pp (t 0.23).

## Reading
- AVWAP confluence does not turn his entry into an edge. The one anchor that clears the Sidak bar (|t| 2.57) and the
  discovery bar (3) runs **the wrong way**: buying a pullback that sits on the VWAP anchored at the 60-day swing
  high loses 0.48pp per trade to its own exposure, in both halves. That level is overhead supply, the holders from
  the high getting back to even. Luk himself uses AVWAP-from-the-highs as a SHORT level ("traps breakout buyers").
  So the inversion is consistent with his short-side use and contradicts the long-side confluence rule.
- Verdict tags: PRIMARY NULL; A1 INVERTED (MECHANISM: overhead-supply AVWAP is resistance, not support). A3 (gap day)
  leans the same way, below the bar.
- ⚠ A subgroup test of a population already known to be null. Mechanical anchors stand in for his discretionary
  ones ("an art"). One tape, survivor-biased universe (affects levels more than these differences).
