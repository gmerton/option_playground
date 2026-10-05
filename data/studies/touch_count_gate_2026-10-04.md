# Resistance touch count as a breakout gate — NULL (2026-10-04)

Pre-registered in `run_touch_count_gate.py` (commit 80fe9d7, before any outcome). Log: `data/studies/logs/touch_count_gate.log`;
trades: `data/studies/logs/touch_count_gate_trades.csv`. Origin: TEST_INDEX §10 (SMB FdMcPKGtFgA), re-raised by Breitstein
UAlhNPmvB14 ("clean levels price has respected"). Weekly-squeeze half of the queued row NOT run.

**Setup.** 52,983 house breakouts (close > prior 20d high, ADR ≥ 3, eligible), liquid_panel_2009 survivors, 2010-01 → 2026-06,
close entry, day-low stop on the close / EMA20 exit / 60 sessions, 0.10%/side. Touch = episode of sessions with
|high − level| ≤ 0.25 ADR in t−60..t−1 (the high that set the level counts). MANY ≥ 5 = 13.1%, FEW 2–4 = 47.4%, 1 = 39.6%.

| cell | MANY | FEW | diff | t | halves (2010–17 / 2018–26) |
|---|---|---|---|---|---|
| **PRIMARY, same date, % per trade** | +0.71% | +0.37% | **+0.34pp** | **1.36** | +0.16 / +0.42 |
| held-the-level share (20 sessions) | 14.2% | 14.0% | +0.1pp | 0.17 | |
| R (floor 2%, cap 20) | +0.150 | +0.060 | +0.090 | 1.38 | |
| same date × ADR tercile | +0.76% | +0.64% | +0.21pp | 0.68 | +0.17 / +0.22 |
| low / mid / high extension tercile | | | +0.41 / +0.58 / **−0.69** | 1.10 / 1.32 / −1.32 | |

Years positive 10 of 17 (2012–13, 2016–20 negative). Harness: paired edge t +1.86 best arm, p_search 0.14 (post); −0.33 (xname). No confound
(MANY and FEW have the same extension, stop/ADR and ADR medians). Power: SE 0.25pp → MDE ≈ 0.75pp at t 3; the measured +0.34pp would
not be worth having at this book's goal even if real.

Exploratory (Šidák k 6, |t| ≥ 2.63): E1 ≥ 3 vs 1–2 +0.39pp t 2.03 (halves +0.58/+0.28 — the best lean, below the bar); touch DAYS
+0.36 t 1.79; 0.5-ADR band +0.25 t 1.16; 120-session lookback −0.02 t −0.08; Breitstein "respected" (≥ 3 touches, never closed
through) +0.02 t 0.06. Dose 1/2/3/4/5+: −0.23 / −0.19 / +0.20 / −0.05 / +0.32pp — not monotone.

**Verdict: NULL · YIELD MECHANISM.** A level tested more often is not a better level: the breakout holds it no more often (14.2% vs
14.0%), and the small raw lean halves under ADR matching and flips sign on extended entries. Joins RMV / VCP / squeeze: no daily
base-geometry feature we have measured selects breakouts.
