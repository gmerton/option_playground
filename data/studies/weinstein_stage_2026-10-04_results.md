# Weinstein stage analysis (2026-10-04 10:49)

chain_spot weekly, 2010-01-08 -> 2026-02-20, 10836 tickers (incl. delisted).

## H1 Stage 1->2 breakout (2A) [replication bar t >= 2.24]

**NULL** — 26-week excess -0.22pp, t -0.69, n 5616; halves +0.25 / -0.66; years + 7/16; raw 26-week return +3.81%
- 13 weeks: -0.06pp t -0.27
- payoff with the base-low stop (weekly closes): mean R +0.17, median R +0.13, win 55%, stopped 21%, R >= 3 2% (n 5615)
- signals per year: 2010:47 2011:149 2012:309 2013:284 2014:317 2015:382 2016:697 2017:549 2018:405 2019:445 2020:240 2021:214 2022:521 2023:475 2024:357 2025:225

## H2 4B-minus reclaim, not a falling knife [discovery bar t >= 3.0]

**UNDERPOWERED / LEAN** — 26-week excess -1.94pp, t -3.51, n 3110; halves -2.82 / -1.36; years + 3/15; raw 26-week return +3.74%
- 13 weeks: -1.91pp t -4.58
- payoff with the base-low stop (weekly closes): mean R +0.09, median R -0.13, win 46%, stopped 36%, R >= 3 4% (n 3110)
- signals per year: 2011:45 2012:192 2013:73 2014:91 2015:208 2016:462 2017:179 2018:193 2019:277 2020:193 2021:36 2022:560 2023:271 2024:149 2025:181

- H1 without the RS condition: -0.34pp t -1.20 n 7446
- [V] H1 + Weinstein volume rule, survivor panel: -0.76pp t -0.97 n 737

## Driver assets (descriptive): every signal, 13 / 26-week return %

- H1 USO 2011-04-01: -13.9 / -29.4
- H1 USO 2013-08-30: -13.0 / -4.5
- H1 BTC-USD 2015-10-30: +15.7 / +38.7
- H1 GLD 2016-02-12: +2.8 / +7.6
- H1 SLV 2016-03-18: +10.4 / +18.8
- H1 USO 2016-12-16: -10.6 / -20.0
- H1 USO 2017-11-24: +8.3 / +16.0
- H1 USO 2018-06-29: +3.1 / -36.7
- H1 GLD 2019-01-25: -1.2 / +8.8
- H1 SLV 2019-07-19: +8.2 / +10.9
- H1 GLD 2019-08-02: +4.9 / +9.9
- H1 SLV 2020-02-21: -7.2 / +44.1
- H1 GLD 2022-02-18: -2.9 / -8.1
- H1 SLV 2022-12-23: -2.9 / -5.8
- H1 GLD 2022-12-30: +8.0 / +5.1
- H1 USO 2023-09-01: -10.0 / -2.5
- H1 GLD 2023-10-20: +2.4 / +20.4
- H1 GLD 2024-05-17: +3.7 / +5.8
- H1 SLV 2024-05-17: -8.2 / -4.2
- H1 SLV 2025-03-14: +7.4 / +24.8
- H1 USO 2025-06-13: -8.6 / -14.2
- H1 USO 2026-02-20: +74.3 / +66.5
- H2 USO 2010-10-08: +4.2 / +24.9
- H2 SLV 2012-02-24: -19.6 / -13.5
- H2 GLD 2012-08-24: +4.7 / -5.6
- H2 SLV 2012-08-24: +10.9 / -6.4
- H2 SLV 2013-10-25: -11.7 / -12.8
- H2 SLV 2015-01-23: -14.0 / -19.9
- H2 USO 2015-06-12: -27.7 / -45.4
- H2 GLD 2015-10-16: -7.5 / +4.8
- H2 USO 2016-04-29: -13.6 / -2.6
- H2 GLD 2018-12-07: +4.0 / +7.2
- H2 SLV 2018-12-28: -1.7 / -0.6
- H2 BTC-USD 2019-04-05: +118.0 / +62.9
- H2 USO 2020-11-13: +42.0 / +58.9
- H2 SLV 2022-11-04: +6.8 / +22.4
- H2 BTC-USD 2023-01-13: +53.1 / +52.4
- H2 BTC-USD 2026-08-21: +nan / +nan
- H2 IBIT 2026-08-21: +nan / +nan

## Live (survivor panel, week of 2026-09-25)

H1: META VKTX WBD
H2: CHKP

## Verdict note (2026-10-04)
The script printed "UNDERPOWERED / LEAN" for H2 because only a positive PASS was coded. By the house verdict scheme a t <= -3 cell with both halves negative is **INVERTED**: H2 on stocks -1.94pp, t -3.51, halves -2.82 / -1.36, 3/15 years positive; 13 weeks -1.91pp, t -4.58.
