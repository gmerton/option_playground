# Overnight-return persistence as a trade (2026-09-24)

`run_overnight_persistence.py` (pre-registration in the docstring); log `data/studies/logs/overnight_persistence.log`.
Top decile of trailing-252 mean overnight return, rebalanced monthly, liquid eligible names, 200 months 2010–2026.

| arm | %/month | t | halves |
|---|---|---|---|
| **A overnight-only, NET 2 bp/side (primary)** | **+0.35** | **+2.63** | +0.54 / +0.17 |
| A overnight-only, gross | +1.18 | +9.01 | +1.38 / +1.01 (17/17 years +) |
| A top − bottom decile, gross | +1.87 | +10.08 | |
| top decile INTRADAY (the give-back) | −0.76 | −3.49 | |
| B just hold the top decile | +0.42 | +1.62 | +0.12 / +0.69 |

**PARKED — real-looking, not tradeable here.** The gross effect is large and stable, and it matches Lou–Polk–Skouras
(overnight winners keep winning overnight and give it back intraday; total return +0.42%/month, t 1.62, not
significant). But: (1) net of 2 bp per side it fails the bar (t 2.63), and breakeven is only ~2.8 bp per side; (2) it
means buying ~120 names at the close auction and selling them at the open auction every day; (3) ⚠ data: the panel's
yfinance open differs from the first 1-minute bar's open by > 0.5% on 18.6% of sampled 2026 name-days (median
difference 0.002%). A name-specific bias in recorded opens would manufacture exactly this overnight / intraday mirror,
so certifying it needs official auction prices (paid data). Not a fit for this book either way.
