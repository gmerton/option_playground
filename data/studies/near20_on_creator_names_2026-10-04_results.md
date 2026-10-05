# Near the 20 EMA on Luk's / Ariel's names vs our breakout (2026-10-04 18:53)

200 events (t0 2025-04-17 → 2026-07-02); NEAR20 filled 98%, BREAKOUT fired 20%.

**PRIMARY NEAR20 − BREAKOUT: NULL** — +6.83pp per event, t 1.39, n 200; halves +8.59 / +5.06; MDE 13.78pp

- per event: NEAR20 +8.33% · BREAKOUT +1.51% · COPY +9.39%

## Reported, not a pass

- NEAR20 − COPY: -1.06pp t -1.30 n 200
- BREAKOUT − COPY: -7.89pp t -1.47 n 200
- beta check, excess vs same-date ADR field: NEAR20: +1.27pp t 0.30 n 200
- … BREAKOUT: +0.98pp t 0.90 n 200
- … COPY: +1.66pp t 0.37 n 200
- band 0.5 ADR: NEAR20 − BREAKOUT +5.88pp t 1.16; NEAR20 +7.39% (filled 96%), BREAKOUT +1.51%
- wait 10: NEAR20 − BREAKOUT +7.17pp t 1.37; NEAR20 +8.19% (filled 96%), BREAKOUT +1.02%
- wait 40: NEAR20 − BREAKOUT +6.56pp t 1.45; NEAR20 +8.54% (filled 100%), BREAKOUT +1.98%
- MANAGED (stops + 20-EMA exit): NEAR20 − BREAKOUT +0.86pp t 0.50; NEAR20 +2.65% (filled 98%), BREAKOUT +1.80%
- Ariel: NEAR20 − BREAKOUT +10.68pp t 2.06 n 158
- Luk: NEAR20 − BREAKOUT -7.66pp t -2.73 n 42

Per month (mean pp, n):

          mean  count
month                
2025-04  22.18      3
2025-05   8.76     13
2025-06  20.42     17
2025-07  40.88      7
2025-08  27.43      3
2025-09  14.01     10
2025-10 -21.26     12
2025-11  12.08     10
2025-12   8.58     14
2026-01   4.59     20
2026-02   8.55      8
2026-03  78.02      8
2026-04   0.69     25
2026-05 -11.78     27
2026-06  -6.57     19
2026-07  -3.89      4

## Notes (2026-10-04)
- Execution fixes before the first result printed: `R.copy` hit the pandas method; a string replace then broke `R.copy_ex`. No outcome was seen before the fixes.
- Post-hoc read (disclosed): NEAR20 fills 98% (their names already sit near the 20 EMA), so NEAR20 ≈ COPY; BREAKOUT is in cash ~80% of events. On excess vs the same-date ADR field, NEAR20 − BREAKOUT is about zero (see the line printed above in the session log / TEST_INDEX): the raw +6.8pp is mostly being invested in a rising tape.

## EXPLORATORY exit sweep (post hoc, Gabe: a 60-session common exit is not realistic; 5 looks, no pass bar)
Excess vs the same-date ADR-band field held over the SAME window; unfilled = 0. `tight` = 1.5% intraday stop, else exit on the first close below the 9 EMA, cap 20.

| exit | NEAR20 | BREAKOUT | NEAR20 − BREAKOUT |
|---|---|---|---|
| 1 session | −0.80pp (t −2.37) | +0.36pp (t 2.18) | −1.16pp (t −3.75) |
| 5 sessions | −0.53 (t −1.07) | +0.23 (t 0.87) | −0.76 (t −1.36) |
| 10 sessions | −0.12 (t −0.14) | +0.22 (t 0.78) | −0.33 (t −0.44) |
| 20 sessions | +0.70 (t 0.41) | +0.96 (t 2.12) | −0.26 (t −0.18) |
| tight stop + 9-EMA exit | −0.77 (t −1.58) | +0.34 (t 2.04) | −1.11 (t −1.92) |

By trader, NEAR20: Ariel −0.52 / −0.16 / +0.46 / +1.72 / −0.56; Luk −1.82 / −1.93 / −2.30 / −3.12 / −1.57. Per-event rows: `near20_on_creator_names_2026-10-04_exit_sweep.csv`.
