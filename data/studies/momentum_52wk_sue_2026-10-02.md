# 12-1 momentum vs/with the 52-week high (George-Hwang) and earnings momentum (SUE) (2026-10-02)

Script: `run_momentum_52wk_sue.py` (pre-registered a23adb9, before the run). Log `data/studies/logs/momentum_52wk_sue.log`;
table `momentum_52wk_sue_2026-10-02.csv`. Diagnostic (after the run, descriptive): `run_momentum_52wk_diag.py`.
Same survivorship-free chain_spot panel, formations 2011-01 → 2026-01, top decile, monthly, 10 bp/side as the certified sleeve.

## Verdict: both NULL, both lean worse than plain 12-1 · keep the screener on 12-1

| cell | arm %/mo | excess over EW (t) | vs 12-1 base pp/mo | t_NW | halves | years + | verdict |
|---|---|---|---|---|---|---|---|
| **H1 [replication primary]** top decile by 52-week-high proximity | +0.82 | **−0.16 (−0.82)** | – | – | −0.07 / −0.23 | 9/16 | **fail (replication)** |
| H1v PTH decile vs the 12-1 decile | +0.82 | | **−0.83** | **−3.24** | −0.43 / −1.16 | 2/16 | **INVERTED** (passes the bar in the wrong direction) |
| H2 composite rank 12-1 + PTH | +1.17 | +0.19 (0.98) | −0.48 | −2.55 | −0.20 / −0.72 | 4/16 | NULL, leans worse |
| **E1 [primary #2]** composite rank 12-1 + SUE (covered names) | +1.39 | +0.21 (1.14) | **−0.48** | **−2.70** | −0.27 / −0.66 | 5/16 | NULL, leans worse (clears Šidák 2.57, not 3) |
| E2 12-1 decile, keep SUE above median | +1.82 | +0.65 (2.49) | −0.05 | −0.45 | −0.20 / +0.07 | 9/16 | NULL |
| E3 SUE alone top decile | +1.15 | −0.05 (−0.26) | −0.73 | −2.58 | −0.45 / −0.96 | 5/16 | NULL, leans worse |

Earnings cells run on the ~343 names with yfinance EPS and are differenced against 12-1 on the same covered names
(BASE-cov +1.87%/mo, +0.70pp over its EW), so the survivor-biased coverage is shared by both arms.

- **The 52-week-high premium does not replicate here.** The long side earns *less* than the equal-weight universe (−0.16pp, t −0.82),
  and it loses to 12-1 by 0.83pp a month in 14 of 16 years.
- **Mechanism (diagnostic, medians over formations):** names nearest their high are the *calm* ones: 63-day vol **22%** vs the
  universe's 30% and the 12-1 decile's **41%**; their 12-1 return is +21% vs +73% for the 12-1 decile; only **16%** overlap.
  Ranking on distance from the high selects quiet, slow-trending names; the long-only premium in this universe sits in the
  fast movers. (George-Hwang's result is long-short on 1963-2001; much of it came from the short leg far below the high.)
  Lower drawdown (21% vs 28%) is the same low-vol tilt, not a better strategy.
- **Earnings momentum adds nothing to price momentum.** Filtering the decile to above-median SUE is a wash (−0.05pp);
  blending SUE into the rank dilutes it (−0.48pp). Consistent with the PEAD and CAN SLIM "C" nulls: on this universe, by the
  month-end formation the earnings news is already in the 12-month return.
- Caveats: PTH uses the close, not the daily high; SUE uses yfinance adjusted EPS on today's names.
