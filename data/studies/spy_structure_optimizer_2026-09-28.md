# SPY structure optimiser (step 2): NULL — the "optimal" multi-leg structure is set by crash assumptions, not data (2026-09-28)

**Question (Gabe):** treat a vol-selling strategy as a linear combination of options. Is there a better structure, possibly 5–6 legs?
**Script:** `run_spy_structure_optimizer.py` (pre-registration plus two disclosed amendments in the docstring). **Logs:** `logs/spy_structure_optimizer_v1.log`, `_v1_1.log`, `logs/spy_structure_optimizer.log` (final v1.2). OOS monthly series: `logs/spy_structure_optimizer_oos.csv`.

## Design
- **Universe:** 32 leg-sides (short or long × 30/45 DTE × 8 deltas), puts only, 1 contract a week on Fridays, held to expiry, real fills. Data: synthetic 1993–2009 plus v3 2010–2026.
- **Linear program:** maximise the shrunk mean monthly P&L subject to CVaR_5% ≤ 100 bp, at most 4 legs, one structure per state (STRESS / CALM).
- **Walk-forward:** fit through Y−1, trade Y, for 2000–2026. Every strategy is scaled to the same in-sample CVaR.
- **Primary:** OPT-STATE vs NAKED (short 45d 10Δ put, all-weather).

## Three looks, all disclosed (charged as 3 tests)
| version | change | what the LP did | OOS |
|---|---|---|---|
| v1 (pre-registered) | — | **Unbounded in 2000–11** (combos with no losing month → solver failure → flat). From 2012: a **2:1 put ratio spread** at 60–70 contracts/week | **Feb 2020 (a calm-state entry): −24,397 bp**. OPT-STATE −35 bp/mo vs NAKED +15.6 |
| v1.1 | + deterministic crash months (SPY −10/−20/−30% at expiry) + gross cap | Crash rows also entered the **mean**, implying a 2–6%/month crash rate → it **bought crash insurance** by the dozen | 2001: −52,105 bp. OPT −226 bp/mo |
| **v1.2 (final)** | crash rows in the CVaR constraint only | 2000–02 unstable (up to 97 contracts); from 2003 a stable **put diagonal**: short 45d 5Δ, long 30d 5–10Δ | OPT-STATE **+92 bp/mo, OOS CVaR 7,901 (budget 100)**; 2012–26 **−15.6 bp/mo** |

**PRIMARY (v1.2): OPT-STATE − NAKED +87 bp/month, t +0.36, halves +198 / −22 → NULL.**

## Out of sample 2000–2026, all scaled to in-sample CVaR_5% = 100 bp (v1.2)
| strategy | mean bp/mo | OOS CVaR_5% | mean ÷ CVaR | worst month | max DD | GFC 07–09 |
|---|---|---|---|---|---|---|
| **NAKED-S** (short 45d 10Δ put, stress months only) | 0.89 | 9.1 | **0.10** | −118 | −118 | −9 |
| **NAKED** (short 45d 10Δ put, every week) | 5.23 | 81 | **0.06** | −429 | −502 | −42 |
| CERT (30d 25Δ/16Δ vertical, stress only) | 1.00 | 48 | 0.02 | −156 | −268 | +59 |
| OPT-STATE | 92.5 | 7,901 | 0.01 | −43,499 | −69,732 | +12,548 |
| OPT-STRESS | 103.6 | 7,759 | 0.01 | −43,597 | −70,202 | +14,323 |

## Verdict
**NULL · YIELD REFRAME + METHOD.**
1. **The best out-of-sample return per unit of tail comes from the simplest structure:** one short 45-DTE 10Δ put, best in the stress regime. Every optimised multi-leg structure did worse per unit of tail by 6–10×. The certified-style vertical sits in between. Buying the wing costs more edge than it saves in tail.
2. **The optimiser's answer is decided by the crash assumption, not by the data.** No crash rows → ratio spreads (short convexity) that blow up. Crash rows in the mean → long insurance that bleeds. Crash rows in the tail only → a diagonal whose OOS tail was 79× its in-sample budget. With ~140 stress months and one GFC, the in-sample CVaR can't discipline a multi-leg LP. This is the estimation-error amplification the plan warned about, observed directly.
3. **The answer to "is there an exotic 5–6-leg structure":** not one that this data can find or certify. The premium is in single OTM puts (step 1), and extra legs only reshape the tail. Choosing that shape needs a view on crash frequency, which the sample can't supply.

**Not pursued:** calls (no premium, and no synthetic GFC), other tenors, and margin (v2 items). None would change point 2.
