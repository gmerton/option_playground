# Vol-scaled 12-1 momentum (2026-09-26)

`run_momentum_volscale.py` (pre-registered in its docstring, committed before the run). Log `logs/momentum_volscale.log`;
monthly series `momentum_volscale_2026-09-26.csv`. Same portfolio as momentum_portfolio_2026-09-25's PRIMARY
(chain_spot incl. delisted, top decile 12-1, monthly, 10 bp/side), 180 months 2011-02 → 2026-01.

## Verdict: NULL — leans harmful. Keep the sleeve at full, constant exposure.

| arm | %/mo | vol | Sharpe | maxDD | worst 5 | CAGR |
|---|---|---|---|---|---|---|
| UNSCALED (the sleeve) | 1.65 | 22.8 | 0.87 | 28.3 | −14.5 | 18.7 |
| **VOLSCALED cap 1.0 (PRIMARY)** | 1.22 | 19.1 | **0.76** | 28.3 | −13.5 | 13.6 |
| STATIC w 0.87 (control) | 1.43 | 19.8 | 0.87 | 24.9 | −12.6 | 16.4 |
| [expl] cap 1.5 | 1.28 | 20.3 | 0.76 | 28.3 | −14.7 | 14.2 |
| [expl] Daniel–Moskowitz bear state | 1.50 | 21.3 | 0.84 | 28.3 | −14.3 | 16.9 |

PRIMARY − STATIC: dSharpe −0.105, 95% block bootstrap [−0.245, +0.055]. Fails all three criteria: Sharpe lower,
maxDD higher (28.3 vs 24.9), worst-5 worse. Not even a risk reshaper.

## Why
- **The rule de-risks at the wrong moment for a long-only book.** After the March 2020 crash, realised vol peaked and
  the weight fell to 0.44 for April 2020, when the sleeve made **+23.7%** (scaled +10.5%). 2020 annual: +52.6%
  unscaled vs +10.3% scaled. The drawdown it was meant to prevent (March −18.9%) happened before vol rose, so the
  weight was still 0.98.
- The academic result is for the long-SHORT factor, whose crashes come from the short leg squeezing in rebounds
  (2009). A long-only top decile doesn't carry that leg; its worst months here (2019-09, 2020-03) arrived at low
  vol, so the scaler never saw them coming.
- ⚠ The window starts in 2011 and misses 2009, the canonical case. Survivorship-free data before 2010 doesn't exist
  here.

## What it taught
- **MECHANISM:** for a long-only momentum sleeve, own-vol scaling mostly sells the rebound. Crash protection has to
  come from outside the sleeve (the bear-leg work), not from sizing it.
- No change to the 9/30 formation: run it at full weight.
