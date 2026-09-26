# Weak-market gap-up fade x breadth (SMB SE1r3UlzWss) -- 2026-09-26

`run_gap_fade_breadth.py` (pre-registered in its docstring, committed before the run). Log `logs/gap_fade_breadth.log`;
events `logs/gap_fade_breadth_events.parquet`. Daily proxy: short the open, cover the close, net 10 bp/side, excess vs
same-date eligible no-gap names (|gap| < 1%), t on date-cluster means. Panel liquid_panel_2009, 2010-01 -> 2026-09.

## Verdict: PRIMARY PASS · ⚠ cost-fragile · the breadth condition is NOT shown to matter → PARKED for a forward paper test

**Primary** (gap >= 5% and >= 1.5 ADR, stock below a declining 50-day SMA, breadth falling): 1,738 events on 711 dates,
**excess +0.54% per date, t 3.87**, halves +0.66 / +0.28, 12/17 years positive, raw net short +0.49%, win 55%.
It clears the pre-registered bar (t >= 3, both halves > 0, majority of years).

**What carries it is the stock's own down-cycle, not the market:**
- Same filter with breadth RISING: +0.16%, t 0.91. SECONDARY falling − rising: +0.40pp, **Welch t 1.70 (not significant)**.
- No down-cycle filter: +0.10% (falling breadth) / +0.02% (all gaps), i.e. an unconditional single-name gap fade is
  flat, agreeing with the SPY gap study.
- Exploratory weak-tape variants all land at t 3.4–3.6: breadth level < 40% +0.71%; SPY < 50-day SMA +0.61% (16/17 yrs
  positive); 10-day MA down-cycle +0.48%. Gap size: 8–15% gaps strongest (+0.70%, t 3.1).

## Checks (a clean result is a bug until proven otherwise)
- **Bad prints:** 0 of 1,738 opens lie outside the day's [low, high]; only 0.1% of events move > 20% open→close.
- **Outliers:** median +0.47%, 5%-trimmed +0.40%, winsorised-1% t 3.97. But the top 20 trades are 49% of the
  per-trade total, so the tail matters.
- **One event per date** (largest gap): +0.81%, t 4.68, n 711. Not a many-events-on-one-day artefact.
- **Look-ahead:** eligibility, down-cycle, ADR and breadth are all read at t−1; the gap is known at the open.
- ⚠ **Costs are the binding constraint.** Extra slippage beyond the 10 bp/side: +10 bp → +0.15%, t 2.44; +20 bp →
  −0.05%. It survives only if the fills are the auction prints (market-on-open short, market-on-close cover), where
  slippage against the print is near zero. Any intraday entry into a gapping name at a wider spread erases it.
- ⚠ **Year 2020** −2.1% (the COVID squeeze year) and 2024 −0.09%: the short's tail risk is real.
- Survivorship: the panel holds only names liquid in 2026, which biases AGAINST shorts, so this is conservative.

## Read
The SMB claim as stated ("in a weak market") is not established: the market condition adds +0.4pp at t 1.7. What
passes is narrower: **fade a big gap-up in a stock that is in its own downtrend, at the auction prints.** Consistent
with the overnight/intraday "tug of war" literature (overnight gains reverse intraday). Not ADOPTED: one pass, fragile
to 10 bp of cost. Next: paper-track it forward with MOO/MOC fills to measure real auction slippage and borrow, and
re-cut breadth-free (down-cycle only) as its own pre-registration rather than reading the exploratory row as a result.
