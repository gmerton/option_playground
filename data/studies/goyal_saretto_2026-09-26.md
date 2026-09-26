# Goyal–Saretto HV − IV sort on delta-hedged single-stock straddles (2026-09-26)

`run_goyal_saretto.py` (pre-registered in its docstring, committed before the run). Log `logs/goyal_saretto.log`;
monthly net spread `goyal_saretto_2026-09-26.csv`; per-straddle table `logs/goyal_saretto_straddles.parquet`
(gitignored); option pulls cached in `data/cache/goyal_saretto/` (333 MB, reused by the Cao–Han and HAR siblings).

## Verdict: FAIL — no gross edge; the traded spread loses its costs · MECHANISM

55,067 eligible ATM ~30-DTE straddles, 167 months (2011-01 → 2026-01), ~330 liquid names a month, ~33 per decile;
median quoted spread 6.1% of mid.

| HV252 − IV sort | %/month | NW t |
|---|---|---|
| **NET spread (D10 long + D1 short, hedged) — PRIMARY** | **−4.73** | **−4.99** (halves −4.44 / −4.96, 1/16 years positive) |
| gross (mid) spread, hedged | +0.71 | +0.75 |
| D10 long alone, net | −5.45 | −4.40 |
| D1 short alone, net | +0.71 | +0.77 |
| unhedged gross spread (descriptive) | +4.28 | — |

Decile gradient, gross hedged LONG return: D1 −3.3 · D2 −1.0 · … · D9 −0.6 · D10 −2.6 — **U-shaped, not rising.**
Exploratory HV63: same picture (net −4.32, t −4.43; gross +1.12, t 1.14).

## Read
- **The published effect isn't there in liquid names after 2011, even before costs.** Goyal–Saretto's ~20%/month (1996–2006,
  mid prices, all optionable names) shrinks to +0.7%/month gross here, t 0.75. Liquid names with tight spreads are
  where a mispricing would be arbitraged first; the paper found it strongest in less liquid names, which the 10%
  spread rule excludes on purpose (they can't be traded at these costs).
- **Every decile's hedged long straddle loses gross (−0.6 to −3.3%/month):** the single-name volatility premium is
  real and broad (agrees with the VRP panel). But selling the richest decile earns only +0.7% net (t 0.77): costs
  (~2.6–2.9pp a month per leg: entry slippage, commissions, hedge turnover) eat almost all of it. Same conclusion as
  every single-name vol trade in the ledger.
- **Both extremes are the worst longs** (U-shape): names whose realised vol is far from implied in either direction
  carry the richest options. Not a tradeable sort after costs.
- The unhedged spread (+4.28%/month gross) is a directional/trend effect in high-HV names, not a vol mispricing; not
  pre-registered and not costed. Noted only.

## Checks
- Delta coverage complete (0 missing hedge days per straddle); splits inside the holding period excluded; raw strikes
  hedged and settled on raw chain spot.
- Hedged long returns negative across deciles = the expected sign of the vol premium, so the P&L machinery behaves.

## Implication for the queued siblings
Cao–Han (IVOL) and HAR-RV share this cache and run locally in < 1 h each. With no gross HV−IV edge and ~5pp/month of
round-trip cost on the long-short, the prior for both is now low: either would need a gross spread above ~5%/month
to net positive.
