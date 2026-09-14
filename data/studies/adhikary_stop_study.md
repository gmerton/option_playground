# Adhikary breakout: initial-stop study

*2026-09-13. `run_adhikary_stop_study.py` on the liquid panel (1738 names, 2019-01-02..2026-09-11), events 2019-10 on. Entry = breakout close; exit = first close under the 20 EMA (capped 60 sessions) unless the initial stop hits first. Survivorship as in the validation doc: read the comparisons, not the levels.*


## A_breakout15 (every recipe breakout): n = 6712

| rule | n | risk_med | ret | ret_med | win | stopped | avg_win | avg_loss | PF | ret_adr | R | R_med | false_stop | ret_adr_19_22 | ret_adr_23_26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| entry_low | 6712.00 | 3.79 | 0.72 | -3.50 | 28.71 | 58.09 | 15.87 | -5.38 | 1.19 | 0.14 | 0.15 | -1.08 | 6.85 | -0.16 | 0.31 |
| entry_low_ID | 6712.00 | 3.79 | 0.30 | -3.05 | 21.54 | 70.99 | 16.17 | -4.05 | 1.10 | 0.06 | 0.03 | -1.00 | 14.02 | -0.19 | 0.20 |
| pivot | 6683.00 | 1.78 | 0.50 | -2.53 | 22.21 | 72.65 | 16.19 | -3.98 | 1.16 | 0.10 | -112.13 | -1.45 | 13.38 | -0.16 | 0.25 |
| piv-0.5adr | 6712.00 | 3.91 | 0.66 | -3.57 | 29.11 | 57.45 | 15.80 | -5.55 | 1.17 | 0.13 | 0.13 | -1.07 | 6.45 | -0.17 | 0.31 |
| piv-1adr | 6712.00 | 5.96 | 0.79 | -3.98 | 33.28 | 40.81 | 15.59 | -6.60 | 1.18 | 0.16 | 0.10 | -0.70 | 2.28 | -0.15 | 0.34 |
| base_low10 | 6712.00 | 15.87 | 0.94 | -3.48 | 35.56 | 2.47 | 15.79 | -7.26 | 1.20 | 0.18 | 0.04 | -0.22 | 0.00 | -0.15 | 0.37 |
| fixed5 | 6712.00 | 5.00 | 0.63 | -4.67 | 31.29 | 48.42 | 15.28 | -6.04 | 1.15 | 0.12 | 0.13 | -0.93 | 4.28 | -0.21 | 0.31 |
| fixed8 | 6712.00 | 8.00 | 0.79 | -3.79 | 34.39 | 25.43 | 15.43 | -6.89 | 1.17 | 0.16 | 0.10 | -0.47 | 1.18 | -0.19 | 0.35 |
| sma10 | 6712.00 | 7.53 | 0.08 | -2.24 | 36.46 | 99.66 | 9.58 | -5.37 | 1.02 | 0.02 | 0.01 | -0.29 | 35.37 | -0.17 | 0.12 |
| trail_only | 6712.00 | nan | 0.94 | -3.48 | 35.56 | 0.00 | 15.79 | -7.26 | 1.20 | 0.18 | nan | nan | 0.00 | -0.15 | 0.37 |

`risk_med` = median initial risk % from entry; `stopped` = % exited by the initial stop (not the trail); `ret_adr` = mean return in ADR units; `R` = return / initial risk; `false_stop` = % of ALL trades the stop took out that the trail alone would have closed green.


### Winners' heat (A_breakout15): how far under the entry the eventual trail_only winners traded, n = 2387

Row = share of winners whose worst point stayed ABOVE this level; a stop inside it ejects the rest.

| pctile | worst close vs entry (ADR) | worst low vs entry (ADR) |
|---|---|---|
| 50 | -0.24 | -0.70 |
| 70 | -0.63 | -1.11 |
| 80 | -0.90 | -1.38 |
| 90 | -1.28 | -1.81 |
| 95 | -1.59 | -2.13 |

Winners that never closed under the entry: 38%; never traded under it intraday: 11%.


## PRECISION cohort (ADR 4-7, <15% off high, stack 5-40): n = 1841

| rule | n | risk_med | ret | ret_med | win | stopped | avg_win | avg_loss | PF | ret_adr | R | R_med | false_stop | ret_adr_19_22 | ret_adr_23_26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| entry_low | 1841.00 | 4.16 | 2.57 | -3.87 | 31.07 | 56.44 | 21.26 | -5.85 | 1.64 | 0.50 | 0.64 | -1.07 | 6.95 | 0.03 | 0.80 |
| entry_low_ID | 1841.00 | 4.16 | 1.51 | -3.43 | 22.22 | 71.05 | 21.96 | -4.34 | 1.45 | 0.31 | 0.35 | -1.00 | 15.81 | -0.13 | 0.58 |
| pivot | 1835.00 | 1.95 | 1.78 | -2.75 | 23.32 | 72.37 | 21.53 | -4.23 | 1.55 | 0.36 | -89.75 | -1.44 | 14.82 | -0.04 | 0.60 |
| piv-0.5adr | 1841.00 | 4.40 | 2.34 | -3.91 | 31.18 | 56.00 | 20.86 | -6.05 | 1.56 | 0.47 | 0.47 | -1.06 | 6.84 | 0.04 | 0.73 |
| piv-1adr | 1841.00 | 6.86 | 2.71 | -4.23 | 35.69 | 39.33 | 20.60 | -7.22 | 1.58 | 0.53 | 0.34 | -0.62 | 2.34 | 0.08 | 0.81 |
| base_low10 | 1841.00 | 18.65 | 2.98 | -3.41 | 38.02 | 2.12 | 20.61 | -7.84 | 1.61 | 0.59 | 0.12 | -0.19 | 0.00 | 0.12 | 0.87 |
| fixed5 | 1841.00 | 5.00 | 2.31 | -5.07 | 32.27 | 51.77 | 20.45 | -6.33 | 1.54 | 0.45 | 0.46 | -1.01 | 5.76 | -0.03 | 0.75 |
| fixed8 | 1841.00 | 8.00 | 2.65 | -3.99 | 36.45 | 30.09 | 20.24 | -7.45 | 1.56 | 0.52 | 0.33 | -0.50 | 1.58 | 0.05 | 0.81 |
| sma10 | 1841.00 | 8.80 | 0.45 | -2.34 | 37.43 | 99.51 | 10.76 | -5.71 | 1.13 | 0.08 | 0.02 | -0.26 | 37.64 | -0.12 | 0.20 |
| trail_only | 1841.00 | nan | 2.98 | -3.41 | 38.02 | 0.00 | 20.61 | -7.84 | 1.61 | 0.59 | nan | nan | 0.00 | 0.12 | 0.87 |

`risk_med` = median initial risk % from entry; `stopped` = % exited by the initial stop (not the trail); `ret_adr` = mean return in ADR units; `R` = return / initial risk; `false_stop` = % of ALL trades the stop took out that the trail alone would have closed green.


### Winners' heat (PRECISION cohort): how far under the entry the eventual trail_only winners traded, n = 700

Row = share of winners whose worst point stayed ABOVE this level; a stop inside it ejects the rest.

| pctile | worst close vs entry (ADR) | worst low vs entry (ADR) |
|---|---|---|
| 50 | -0.27 | -0.71 |
| 70 | -0.63 | -1.08 |
| 80 | -0.84 | -1.36 |
| 90 | -1.26 | -1.86 |
| 95 | -1.58 | -2.14 |

Winners that never closed under the entry: 36%; never traded under it intraday: 10%.

