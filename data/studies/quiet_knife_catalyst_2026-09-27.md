# Quiet knife × crowded short × scheduled catalyst — stock returns (2026-09-27)

`run_quiet_knife_catalyst.py` (pre-registered in its docstring; one method change declared and committed before the
run: exact `analyze()` on a loose vectorised shortlist). Log `logs/quiet_knife_catalyst.log`; episodes
`quiet_knife_catalyst_2026-09-27.csv`. Prompted by the Aug-2026 IBIT rebound (a pre-announced White House summit
plus a crowded short).

Liquid panel 2018-01 → 2026-06, weekly: 8,650 knife-weeks → **1,210 episodes on 419 names**; 1,164 with short interest
and a control. Buy the close, hold 60 sessions, 10 bp/side. Control = same-date eligible names that are clearly not
knives, in the SAME short-interest tercile and the SAME catalyst state.

## Verdict: NOT MET — and the hypothesised cell is the WORST one (leans INVERTED)

| cell (days-to-cover tercile × earnings within 30 d) | n | raw 60-d | excess vs control | t | years + |
|---|---|---|---|---|---|
| **HIGH short × catalyst — PRIMARY** | 132 | −1.28% | **−5.36pp** (median −7.01) | **−2.68** | 2/9 |
| HIGH short × no catalyst | 331 | +1.18% | −1.03pp | −0.63 | 3/9 |
| LOW short × catalyst | 61 | +3.01% | +0.99pp | +0.21 | 3/8 |
| LOW short × no catalyst | 274 | +2.79% | −0.66pp | −0.36 | 4/8 |
| MID × catalyst / no catalyst | 84 / 282 | +4.09 / +4.15% | −0.18 / +0.71pp | −0.07 / +0.47 | 5/9, 5/9 |
| all episodes | 1,164 | +2.31% | −0.29pp (median −3.77) | −1.05 | — |

Interaction [HIGH & CAT] − [LOW & NO CAT]: −2.17pp, Welch t −1.72.

## Read
- **When a quiet, beaten-down stock is heavily shorted and has earnings coming, the shorts are usually right.** The
  conjunction that fuelled the IBIT squeeze underperforms comparable heavily-shorted names with the same catalyst by
  5.4 points over 60 sessions, in 7 of 9 years. That fits the ledger's short-interest result (BB-1: high days-to-cover
  breakouts lag, the "squeeze" cell worst) and the classic finding that high short interest predicts low returns:
  on stocks, crowded shorts are more often informed than trapped.
- Just short of the |t| 3 bar in the negative direction, so it's recorded as NOT MET, leaning INVERTED; not a certified
  short signal.
- The quiet-knife state on its own is roughly neutral against like-for-like names over 60 days (−0.29pp, t −1.05),
  but the median episode lags by 3.8pp: a few rebounds, many drifts lower.
- ⚠ Survivor-biased panel (flatters buying low); negative anyway. Earnings dates are the stated proxy for "known in
  advance". Crypto policy catalysts can't be tested historically; what we can test at scale on stocks points against
  the idea.

## What IBIT was (and wasn't)
A policy event on a macro asset with a leveraged, liquidation-prone short base (perpetual futures) is structurally
different from a heavily shorted single stock into earnings. The stock version doesn't pay. Whether the crypto version
does can't be answered with a handful of episodes; treat it as discretionary and size it as such.
