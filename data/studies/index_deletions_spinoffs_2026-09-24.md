# Undervalued #5: forced selling — S&P 500 deletions and spin-offs (2026-09-24)

`run_index_deletions_spinoffs.py` (pre-registration in the docstring); log `data/studies/logs/index_deletions_spinoffs.log`.
Events: Wikipedia S&P 500 selected-changes table (revision 1365256480, 2026-07-21; since removed from the live page) →
`data/cache/sp500_changes_wikipedia.csv`. Excess = forward return vs the same-date ADR-matched eligible field.

**(a) Deletions for market cap — NULL.** 124 since 2010, 76 with panel prices. 60d excess from the rebalance close
**−0.94pp, t −0.44**, 41% +, halves +2.61 (n 11) / −1.57 (n 62); 20d −0.61, 120d +2.20 (t 0.61). No visible forced-
selling footprint either (−0.32% in the 20 sessions into the rebalance). Demoted names get absorbed by MidCap-400 buying.

**(b) Spin-offs added to the S&P 500 — UNDERPOWERED, the right sign.** 20 since 2010, 17 in the panel. Entry at the 20th
session (after parent holders dump; the first 20 sessions average −2.6%). 60d **+10.2pp (t 1.26)**, 120d **+22.9pp
(t 2.12, n 16)**. Spread is huge: CEG +97, CARR +78, GEV +74, TRIP +62, Q +56, SOLS +53 vs VNT −55, ADT −37, FOXA −12.
Below the bar and n = 16, but the only positive result in the undervalued batch and it matches the literature
(spincos outperform after the initial dumping). ⚠ First filter pass mis-tagged non-spin-offs (TSLA, MPWR, NVR); fixed
to require the ADDED company be the one named as spun off.

**Follow-up worth queuing:** widen (b) beyond S&P 500 spincos — all US spin-offs via SEC Form 10-12B registrations
(EDGAR full-text search, 2001 →), liquid names only. That is the only way to get n into the hundreds.
