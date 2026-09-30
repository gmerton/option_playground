# Is RVOL a proxy? (1) dollar-volume ranking on the unused 2010–19 holdout; (2) up/down volume ratio (2026-09-29)

## Pre-registration (written BEFORE either run; do not edit this section after the results)

**Why.** Gabe: "is RVOL a proxy for a more powerful underlying variable?" The one volume-type feature that ever sorted
breakouts is ABSOLUTE dollar volume (`breakout_within_date_rank_2026-09-22.md`: top-2 by dollar volume within each day,
+0.089R, t 3.48 — but PARKED as era-bound, all of it 2025–26). The 2010-01 → 2019-09 period of `liquid_panel_2009` has
never been used for it. Separately, multi-week ACCUMULATION (IBD's up/down volume ratio) is the one volume story not yet
tested.

### D1 — dollar-volume ranking, holdout replication (frozen from the 9/22 script)
Breakouts = `run_retrace_entry.masks(P, 20, 0.0)` on `load_panel("data/cache/liquid_panel_2009.parquet")`; R = the 9/22
definition (5-session hold, stop 1 ADR below entry hit on the LOW, else exit at the 5th close). Feature = signal-day
dollar volume (close × volume). Per date with M ≥ 5 candidates: mean R of the top 2 by dollar volume minus the day's
mean R; t across dates. Window: signal dates 2010-01-01 → 2019-09-30.
**PASS:** delta > 0, **t ≥ 3** (one pre-specified cell, confirmation of a lead), both halves > 0, **positive in a
majority of years** (the era test the original failed). Reported: N = 1/3/5; within ADR tercile; the house-trade R
(close entry, day-low/2% stop on the close, 20-EMA exit, 60 cap) version of the same cell.

### D2 — up/down volume ratio (UDVR) as a selection variable
UDVR = total volume on up-close days ÷ total volume on down-close days over the prior 50 sessions (known at the signal
close), as a cross-sectional percentile among eligible names that day. Population (PRIMARY): the broad breakout pool of
`run_rvol_drop_and_score.py` (first close ≥ prior-15-session high; 226,668 events 2010–26), house trade, excess R vs 3
same-date ADR-tercile non-breakout controls (that script's `Ctl`, same seed). Statistic: monthly mean excess of TOP-tercile
UDVR breakouts minus BOTTOM-tercile, t on months ≥ 3, both halves (2010–2017 / 2018–2026) > 0. Reported: the precision
tier alone (thin); a dose-response across UDVR quintiles.
**Charge:** two primaries (D1, D2) → Šidák-2 at |t| ≥ 3 → **3.2 governs both.**
**Prior:** D1 low (the lead was era-bound); D2 low (volume stories 0/12 at lows, abnormal volume NULL today).
Local, ~1.5 h.

---

## Results (run 2026-09-29, after 6220099; `run_dolvol_holdout_udvr.py`, `.log`)

**Verdict: both FAIL → NULL. RVOL is not standing in for a stronger volume variable that we can find: absolute dollar
volume was a 2025–26 regime, and multi-week accumulation doesn't sort breakouts.**

**D1 — dollar-volume ranking on the unused 2010–19 holdout** (12,802 breakouts, 838 dates):
| cell | delta vs day mean | t (bar 3.2) | halves | yrs + |
|---|---|---|---|---|
| **top 2 by dollar volume (PRIMARY)** | **−0.023R** | **−0.97** | −0.044 / −0.002 | 6/10 |
| top 1 / 3 / 5 | −0.017 / −0.028 / −0.015 | −0.49 / −1.35 / −0.73 | | |
| top 2, house-trade R | −0.034 | −0.57 | | |
| top 2 within ADR tercile | +0.035 | 1.20 | −0.05 / +0.12 | 5/10 |
Per year: 2010 +0.002 … 2012 −0.135, 2013 −0.090 … 2019 +0.029. The 9/22 lead (+0.089R, t 3.48) was 2025–26; out of
time it's zero-to-negative. This also resolves the queued "mega-cap tension": nothing out of time says the biggest
names break out better, so the INT universe dropping mega-caps is not contradicted.

**D2 — up/down volume ratio (50-day)** (226,668 breakouts, 198 months):
| population | top − bottom tercile excess | t (bar 3.2) | halves |
|---|---|---|---|
| **broad pool (PRIMARY)** | **+0.014R** | **0.39** | +0.006 / +0.021 |
| precision tier | +0.88R | 1.92 | −1.19 / +1.07 (36 months) |
Dose by quintile: −0.015, +0.038, +0.078, +0.086, +0.062R — the worst-accumulation fifth is slightly weaker, the top
fifth is not better than the middle. No gradient worth a gate.

**What it means for the book now.** Stop looking for "the real variable behind volume": abnormal volume, relative volume,
dollar volume out of time, volume at lows and multi-week accumulation are all NULL. Volume is information the price has
already absorbed. RVOL stays a liveness filter at most (Gabe's call on dropping it).
