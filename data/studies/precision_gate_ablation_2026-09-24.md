# Precision tier, gate by gate (2026-09-24)

**Question (Gabe, after the IONQ check):** have the tier's gates been tested individually?
**Script:** `run_precision_gate_ablation.py` (pre-registration in the docstring). Log `data/studies/logs/precision_gate_ablation.log`,
table `precision_gate_ablation_2026-09-24.csv`.

**Design.** Base = house breakout scan (eligible, ADR ≥ 3, close crosses the prior 15-session high). T = passes all 9
tier gates (n 2,019, 850 dates, 2019-10+). For each gate k, M_k = fails k but passes the other 8 — exactly what dropping
k would admit. PRIMARY = 20d return minus same-date eligible names in the same ADR band; T − M_k, Welch on date means.
House process (close entry, day-low stop floored 2% judged on the close, 20-EMA exit) in % alongside. Bar: t ≥ 3, both
halves (2023-01) positive. Prune only if M_k is worse in neither half AND not below T on the house process.

| gate | n admitted if dropped | T − M_k (pp) | t | halves | house % of M_k | verdict |
|---|---|---|---|---|---|---|
| ADR 4–7 | 3,051 | +0.59 | 1.10 | +1.64 / −0.21 | −0.33 | unproven |
| within 15% of 52wk high | 904 | +0.12 | 0.14 | −0.28 / +0.36 | −1.20 | unproven |
| 52wk range ≥ 17% | **0** | — | — | — | — | **never binds** (entailed by the other gates) |
| EMA stack ≥ 5 sessions | 1,070 | −0.13 | −0.18 | −0.19 / −0.08 | **+1.08** | **PRUNE candidate** |
| stack run ≤ 40 | 451 | +1.80 | 1.94 | +3.54 / +0.70 | −1.04 | unproven (strongest, short of bar) |
| RVOL ≥ 1.1 | 2,160 | +0.14 | 0.21 | +0.21 / +0.09 | −0.03 | unproven |
| close in upper half | 317 | −0.72 | −0.70 | +0.33 / −1.31 | +0.13 | unproven |
| gap < 5% | 30 | −0.23 | −0.06 | — | +1.67 | unproven (n 30, can't matter) |
| day < 8% | 439 | +0.19 | 0.18 | −0.54 / +0.69 | +1.58 | unproven |

Tier itself: excess +0.80pp, house +0.80%/trade (median −4.0%), 31% win.

## Verdicts

- **No gate earns its place (0 of 9 at t ≥ 3).** Largest is the stack-age cap ≤ 40 (+1.80pp, t 1.94, both halves +).
  Consistent with the freeze-forward (the tier is a regime finding) — the fifth angle saying the gates are not selection levers.
- **Within 15% of the 52wk high: NULL** (+0.12pp, t 0.14, halves disagree). What it excludes loses under the house
  process (−1.20%/trade) but not significantly worse than the tier on the primary.
- **52wk range ≥ 17%: redundant** — binds on zero events once the other gates apply. Safe to delete.
- **EMA stack ≥ 5 sessions: PRUNE candidate by the pre-registered rule** — the unstacked breakouts it rejects are no
  worse on the primary in both halves and earn +1.08%/trade under the house process. ⚠ Not adopted: per-year −5.9 to +4.2,
  in-sample, survivor panel; "no edge from the gate" is not "edge from removing it". Admitting them adds ~1,070 trades
  at the same (thin) expectancy — a recall change, and the owner rule is precision over recall.
- RVOL ≥ 1.1, upper-half close, gap, day caps: never tested alone before; all NULL. The gap cap binds on only 30 events.
