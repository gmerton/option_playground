# Undervalued #2: insider cluster buying (2026-09-24)

`run_sec_insider_pull.py` (new data: SEC Form 4 structured data sets, 505,807 open-market purchase lines, filings
2010-01 → 2026-03, point-in-time on the filing date → `data/cache/insider_purchases.parquet`) and
`run_insider_clusters.py` (pre-registration in the docstring); log `data/studies/logs/insider_clusters.log`.
Cluster = ≥ 3 distinct insiders buying (≥ $10k each) within 30 days; entry at the first close after the filing;
liquid eligible names only (ADDV ≥ $50M).

| cell | n | 60d vs ADR-matched field | t | 60d vs same-industry peers | t |
|---|---|---|---|---|---|
| **CLUSTER** | 583 | **−1.68pp** | −2.23 | **−0.01** | −0.53 |
| CLUSTER, beaten-down | 246 | −4.21 | −2.48 | +0.54 | +0.15 |
| SINGLE (control) | 3,297 | +0.12 | +1.00 | +0.39 | +1.86 |

**NULL.** The pre-registered primary fails (and points the wrong way: −1.68pp, cluster − single −2.03pp, t −2.44), but
the post-run industry check explains it: clusters concentrate in Oil & Gas, regional banks, REITs, steel — sectors
that lagged — and against same-industry peers the effect is ≈ 0. Insiders' cluster buys carry a sector/value tilt,
not stock-level information, in names liquid enough for us to trade. (The literature's insider effect is mostly in
small caps.) Checks: ticker identity sound (2025 purchase prices within 10% of the panel close 89%; older drift = the
panel's split/dividend adjustment).
