# Ariel-scan criteria inside the production INT universe (2026-09-28)

`run_ariel_ablation.py` (pre-registered; same method as the Trend Template ablation: leave-one-out, paired,
date-held-fixed, ADR-matched 20-day excess; 20 cells, Šidák |t| ≥ 3.02). Liquid panel 2020-26. Log
`logs/ariel_ablation.log`; table `ariel_ablation_2026-09-28.csv`.

## Verdict: a3 (≥ 2M shares/day) ADDS (certified) · a1 (≥ 70% off the low) leans ADDS · a2/a5 subsumed · a4 inert

| inside INT (35 names/day) | names without it | Δ 20d excess if dropped | t | halves | verdict |
|---|---|---|---|---|---|
| **a3 ≥ 2M shares/day** | 46 | **−0.49pp** | **−4.24** | −0.54 / −0.46 | **ADDS** (5d: −0.11pp, t −3.89) |
| a1 ≥ 70% above the 252d low | 49 | −0.62pp | −2.74 | −0.93 / −0.41 | leans ADDS, below the bar |
| a2 close > 50 SMA | 35 | 0.000 | — | — | subsumed by TT (sanity check ✓) |
| a5 ADDV ≥ $100M | 35 | 0.000 | — | — | subsumed by TT's $200M (sanity check ✓) |
| a4 price > $7 | 35 | +0.02pp | 0.81 | | inert |

Inside AH alone every criterion is unresolved (a3 −0.29pp t −2.17; a1 −0.53pp t −1.71).

## The a3 surprise (checked)
The queue suspected a3 was price-distorted and redundant. It isn't redundant: the names it excludes are liquid,
HIGH-PRICED stocks (median $319; 82% above $200): URI, SPOT, MELI, MPWR, HUBS, RH, PH, PWR, MDB, ALGN, HCA, FICO,
TEAM... and they lag the INT members in 6 of 7 years (2020 −5.0, 2023 −3.0, 2025 −3.7pp raw at 20 days). So a3
works as a "skip high-priced, low-share-turnover names" filter. Whether the mechanism is share count (retail
participation) or nominal price itself is not separated here; that would be its own test.

## Read
- **Keep both of Ariel's binding criteria.** INT's a1 costs 14 names a day and a3 11, and both pay for themselves.
  The worry that INT encodes his published rule rather than his practice is real (on 2026-09-25 a1 alone excludes
  AAPL at 1.38x and NVDA at 1.37x their 52-week lows, names he watches), but on the data, following the rule beats
  loosening it.
- Combined with the TT ablation: of INT's 15 criteria, the ones with evidence behind them are a3 (certified), a1
  (lean), and TT's c10 ADDV floor (the only TT criterion with a sizeable effect, though it discards 60% of names).
