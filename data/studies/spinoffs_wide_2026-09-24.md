# Spin-offs beyond the S&P 500 (2026-09-24)

`run_spinoffs_wide.py` (pre-registration in the docstring); log `data/studies/logs/spinoffs_wide.log`; events
`spinoffs_wide_2026-09-24.csv`. Event list: SEC EDGAR form indexes, every Form 10-12B registrant 2009–2026
(`data/cache/edgar_form10_12b.csv`, 430 registrants) → a spin-off if its ticker first trades within −30 / +540 days of
its first 10-12B and is liquid (first-20-session dollar volume ≥ $50M). 45 events (25 S&P 500 spincos, 20 others);
entry at the 20th session; excess vs the ADR-matched field and vs same-industry peers.

| group | n | 120d excess | t | 120d vs industry | t |
|---|---|---|---|---|---|
| **ALL (primary)** | 38 | **+10.45pp** (median +5.3) | **+2.06** | +5.42 | +0.96 |
| S&P 500 spincos | 22 | +16.87 | +2.12 | +13.56 | +1.44 |
| other spincos | 16 | +1.62 | +0.36 | −3.87 | −0.78 |

**FAIL the bar — PARKED (right sign, both halves positive: +12.4 / +9.5; 66% of events positive).** Three things
keep it from being tradeable evidence: (1) the edge sits entirely in large spincos from S&P 500 parents; the other
16 are flat; (2) about half of it is industry — CEG +85, GEV +74, CARR +100 rode the power/AI and HVAC themes — and
against industry peers it falls to +5.4 (t 0.96); (3) survivor panel: 228 registrants are not in the panel (small,
illiquid, acquired or failed), and spincos have a known fat left tail, so the true figure is lower.
**Forward lockbox (proposed):** large-parent spincos from here on, entered at session 20, scored at 120 sessions —
~3–5 a year, so a verdict takes several years; cheap to log.
