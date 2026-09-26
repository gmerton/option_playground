# Vol-decay (Hawkes) exit vs the house 20-EMA trail (2026-09-26)

`run_vol_decay_exit.py` (pre-registered in its docstring, committed before the run). Log `logs/vol_decay_exit.log`;
trades `logs/vol_decay_exit_{precision,generic}_trades.parquet`. Source: neurotrader `wdsiZBIhAFw`.

## Verdict: NULL (primary) · MECHANISM: the lookback is the whole story · ⚠ exploratory lead is a hold-longer / beta effect

**Primary cell** VD_k0.1_L60 − BASE on the precision pool (1,960 trades): **+0.05pp, t −0.76**, halves +1.34 / −0.77,
3/8 years negative. Held 13.2 vs 13.8 days. Top-decile trades +41.9% vs BASE +54.5%: it cuts the big winners, as the
prior expected.

**Grid (9 cells, both pools) is a lookback gradient, not a kappa effect:**
- L20 (exit when the burst decays below a 20-session low): exits after ~7 days and **loses significantly** — precision
  −1.56 to −1.76pp, t −3.5 to −3.7. This drives the precision grid's p_opt 0.0005 (a two-sided max-|t| statistic). The
  significance is in the WRONG direction.
- L120: precision +0.4 to +0.8pp, t ≤ 1.1 (null); **generic pool +0.95 to +0.98pp, t 3.4–4.1, halves +/+, 0/8 years
  negative** (p_opt 0.0005).

## ⚠ The generic L120 "pass" is not the vol-decay exit (exploratory check, not pre-registered)

A 120-session 5th percentile rarely triggers: the L120 exit fired on only ~30% of trades, and ~60% exit at the
initial stop. So L120 ≈ "no trail". The check added a STOP_ONLY arm (initial stop + 60-session time exit, no trail):

| pool | STOP_ONLY − BASE | VD_k0.2_L120 − BASE | VD_k0.2_L120 − STOP_ONLY |
|---|---|---|---|
| precision | +1.28pp, t +3.62 | +0.48pp, t +0.99 | −0.80pp, t −1.90 |
| generic | +1.25pp, t +5.20 | +0.98pp, t +3.68 | −0.27pp, t −1.87 |

The vol-decay exit is **worse than no trail at all** in both pools. Its "edge" over BASE is the portion of dropping
the 20-EMA trail that it keeps.

⚠ **STOP_ONLY beating the 20-EMA trail is NOT a finding yet.** It is exploratory, and it has an obvious confound: it
holds longer (up to 60 sessions) in a 2019–26 sample that rose, so it collects more market beta. Percent-per-trade
doesn't adjust for exposure. The O'Neil 8-week-hold test (2026-09-22) was NULL on this pool, which argues against a
simple hold-longer edge. A real test needs an exposure-matched control (SPY-hedged returns, or % per day held).
Queued in TEST_INDEX §10, not run.

## What it taught
- **MECHANISM:** a vol-decay exit only helps where it barely fires. Any lookback short enough to act cuts the trend
  early and gives up the tail (top-decile −12.6pp at the primary cell).
- **METHOD:** a grid p_opt with a two-sided statistic can be "significant" because of the losing cells. Report the
  direction of the max-|t| cell with the p.
