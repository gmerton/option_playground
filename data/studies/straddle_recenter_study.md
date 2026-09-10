# Long straddle: re-centering and the real stop (path simulation, 2018-2026)

Generated 2026-09-10 by run_straddle_recenter_pull.py / _sim.py / _report.py. 19,270 trades from the gated pool file (7-DTE: 13,415 FVR-passing, 5,886 of them both gates; 14-DTE: 5,855 both-gates trades re-entered at the next weekly expiry). Daily close bid/ask/delta from silver.options_daily_v3 (8.7M quotes). Executions at mid +/- 25% of that day's bid-ask + $0.0065/sh/leg; expiry settles at |S_T - K| by expiry-day put-call parity. Re-center = sell the held pair, buy the new ATM pair (call delta nearest 0.50), same expiry, only with >= 2 more trading days to expiry. Flat-take = sell at the same trigger and stay flat. Decisions at the daily close only (no intraday).

```

===== 7-DTE, both gates: n=5,886  median entry BA 5.9% of mid =====
  hold, POOL payout (playbook), mid  mean   +8.15%  med  -12.58%  win  43.7%  t +7.07
  hold, mid, no costs                mean   +6.82%  med  -13.92%  win  43.4%  t +5.90
  clip -50% (playbook model)         mean  +14.23%  med  -13.92%  win  43.4%  t +13.33
  hold, after costs                  mean   +4.14%  med  -16.30%  win  42.3%  t +3.68
  real path stop -50%, after costs   mean   +3.89%  med  -19.28%  win  41.3%  t +3.49  | vs hold  -0.25pp (paired t -1.37)  stopped 14.9%
  flat-take |net delta|>=0.35        mean   -1.69%  med   -3.70%  win  44.1%  t -2.49  | vs hold  -5.83pp (paired t -6.59)  fired 59.4%
  re-center |net delta|>=0.35 max 1  mean   -1.62%  med  -18.69%  win  39.6%  t -1.61  | vs hold  -5.76pp (paired t -8.44)  avg n 0.59  max cap 1.00x
  re-center |net delta|>=0.35 max unl mean   -2.87%  med  -19.49%  win  38.4%  t -2.91  | vs hold  -7.01pp (paired t -9.89)  avg n 0.69  max cap 1.00x
  flat-take |net delta|>=0.5         mean   -0.34%  med   +0.23%  win  50.1%  t -0.41  | vs hold  -4.48pp (paired t -5.98)  fired 38.9%
  re-center |net delta|>=0.5 max 1   mean   -0.74%  med  -17.48%  win  40.0%  t -0.73  | vs hold  -4.88pp (paired t -7.79)  avg n 0.39  max cap 1.00x
  re-center |net delta|>=0.5 max unl mean   -1.22%  med  -17.69%  win  39.7%  t -1.23  | vs hold  -5.36pp (paired t -8.39)  avg n 0.42  max cap 1.00x
  flat-take move>=x implied0.5       mean   -1.73%  med   -2.80%  win  45.3%  t -2.52  | vs hold  -5.87pp (paired t -6.67)  fired 56.0%
  re-center move>=x implied0.5 max 1 mean   -1.55%  med  -18.23%  win  39.7%  t -1.54  | vs hold  -5.69pp (paired t -8.40)  avg n 0.56  max cap 1.00x
  re-center move>=x implied0.5 max unl mean   -2.66%  med  -18.74%  win  38.9%  t -2.70  | vs hold  -6.80pp (paired t -9.70)  avg n 0.64  max cap 1.00x
  flat-take move>=x implied0.75      mean   +0.29%  med   +2.69%  win  52.9%  t +0.34  | vs hold  -3.85pp (paired t -5.26)  fired 35.5%
  re-center move>=x implied0.75 max 1 mean   -0.25%  med  -17.09%  win  40.6%  t -0.25  | vs hold  -4.40pp (paired t -7.16)  avg n 0.35  max cap 1.00x
  re-center move>=x implied0.75 max unl mean   -0.62%  med  -17.13%  win  40.5%  t -0.62  | vs hold  -4.76pp (paired t -7.59)  avg n 0.38  max cap 1.00x
  flat-take move>=x implied1.0       mean   +1.38%  med   -3.85%  win  48.7%  t +1.47  | vs hold  -2.76pp (paired t -4.65)  fired 20.2%
  re-center move>=x implied1.0 max 1 mean   +0.71%  med  -16.11%  win  41.4%  t +0.69  | vs hold  -3.43pp (paired t -6.60)  avg n 0.20  max cap 1.00x
  re-center move>=x implied1.0 max unl mean   +0.64%  med  -16.11%  win  41.4%  t +0.63  | vs hold  -3.50pp (paired t -6.61)  avg n 0.21  max cap 1.00x
  by year (hold / stop / re-center move>=0.75 max1 / flat-take move>=0.75), after costs:
    2018  n=  288  hold   +5.07  stop   +4.95  rc   +8.56  take   +8.14
    2019  n=  765  hold   -6.91  stop   -7.22  rc   -9.72  take   -6.20
    2020  n=  163  hold  +20.70  stop  +18.02  rc  +10.67  take   -0.48
    2021  n= 1156  hold   +4.04  stop   +3.47  rc   -0.81  take   -0.83
    2022  n=  296  hold   +6.91  stop   +6.46  rc   -1.14  take   +3.88
    2023  n= 1368  hold   +5.98  stop   +6.06  rc   +0.18  take   -0.60
    2024  n= 1031  hold   +4.05  stop   +4.29  rc   -1.04  take   +2.00
    2025  n=  719  hold   +5.60  stop   +5.10  rc   +2.91  take   +2.01
    2026  n=  100  hold  +17.45  stop  +17.46  rc  +17.46  take  +12.92

===== 7-DTE, FVR gate only (superset): n=13,415  median entry BA 6.4% of mid =====
  hold, POOL payout (playbook), mid  mean   +5.39%  med  -14.21%  win  42.8%  t +7.27
  hold, mid, no costs                mean   +3.96%  med  -15.25%  win  42.5%  t +5.39
  clip -50% (playbook model)         mean  +11.55%  med  -15.25%  win  42.5%  t +17.14
  hold, after costs                  mean   +1.26%  med  -17.58%  win  41.2%  t +1.77
  real path stop -50%, after costs   mean   +0.82%  med  -21.87%  win  40.1%  t +1.16  | vs hold  -0.44pp (paired t -3.48)  stopped 16.3%
  flat-take |net delta|>=0.35        mean   -3.57%  med   -4.75%  win  42.3%  t -8.28  | vs hold  -4.83pp (paired t -8.59)  fired 59.8%
  re-center |net delta|>=0.35 max 1  mean   -3.86%  med  -20.02%  win  38.9%  t -5.97  | vs hold  -5.13pp (paired t -11.34)  avg n 0.60  max cap 1.00x
  re-center |net delta|>=0.35 max unl mean   -5.06%  med  -20.65%  win  38.2%  t -8.05  | vs hold  -6.32pp (paired t -13.52)  avg n 0.70  max cap 1.00x
  flat-take |net delta|>=0.5         mean   -2.16%  med   -1.17%  win  48.5%  t -4.16  | vs hold  -3.43pp (paired t -7.19)  fired 39.1%
  re-center |net delta|>=0.5 max 1   mean   -2.86%  med  -18.94%  win  39.3%  t -4.43  | vs hold  -4.12pp (paired t -9.90)  avg n 0.39  max cap 1.00x
  re-center |net delta|>=0.5 max unl mean   -3.20%  med  -18.88%  win  39.2%  t -5.01  | vs hold  -4.46pp (paired t -10.54)  avg n 0.42  max cap 1.00x
  flat-take move>=x implied0.5       mean   -3.39%  med   -3.53%  win  44.0%  t -7.69  | vs hold  -4.66pp (paired t -8.36)  fired 56.0%
  re-center move>=x implied0.5 max 1 mean   -3.57%  med  -19.58%  win  39.1%  t -5.53  | vs hold  -4.83pp (paired t -10.73)  avg n 0.56  max cap 1.00x
  re-center move>=x implied0.5 max unl mean   -4.69%  med  -19.84%  win  38.5%  t -7.49  | vs hold  -5.96pp (paired t -12.79)  avg n 0.65  max cap 1.00x
  flat-take move>=x implied0.75      mean   -1.66%  med   +1.30%  win  51.3%  t -3.10  | vs hold  -2.92pp (paired t -6.30)  fired 34.9%
  re-center move>=x implied0.75 max 1 mean   -2.45%  med  -18.10%  win  39.8%  t -3.79  | vs hold  -3.72pp (paired t -9.12)  avg n 0.35  max cap 1.00x
  re-center move>=x implied0.75 max unl mean   -2.84%  med  -18.09%  win  39.7%  t -4.45  | vs hold  -4.11pp (paired t -9.88)  avg n 0.37  max cap 1.00x
  flat-take move>=x implied1.0       mean   -0.90%  med   -5.63%  win  47.8%  t -1.50  | vs hold  -2.16pp (paired t -5.72)  fired 20.0%
  re-center move>=x implied1.0 max 1 mean   -1.51%  med  -16.71%  win  40.7%  t -2.28  | vs hold  -2.77pp (paired t -7.97)  avg n 0.20  max cap 1.00x
  re-center move>=x implied1.0 max unl mean   -1.63%  med  -16.71%  win  40.7%  t -2.49  | vs hold  -2.90pp (paired t -8.24)  avg n 0.21  max cap 1.00x
  by year (hold / stop / re-center move>=0.75 max1 / flat-take move>=0.75), after costs:
    2018  n=  650  hold   +9.60  stop   +8.43  rc   +7.02  take   +5.89
    2019  n= 1640  hold   -6.39  stop   -7.02  rc   -6.41  take   -4.15
    2020  n= 1180  hold   -0.83  stop   -1.07  rc   -6.62  take   -7.86
    2021  n= 2064  hold   +0.42  stop   +0.17  rc   -3.14  take   -2.47
    2022  n= 1325  hold   +5.19  stop   +4.59  rc   -0.20  take   +2.30
    2023  n= 1817  hold   +4.92  stop   +4.81  rc   -0.41  take   -1.52
    2024  n= 2259  hold   -0.05  stop   -0.30  rc   -3.67  take   -0.96
    2025  n= 2235  hold   +1.02  stop   +0.37  rc   -1.87  take   -1.59
    2026  n=  245  hold  +13.44  stop  +12.24  rc   +3.30  take   +2.23

===== 14-DTE, both gates: n=5,855  median entry BA 5.7% of mid =====
  hold, mid, no costs                mean   +3.61%  med  -15.10%  win  42.9%  t +3.26
  clip -50% (playbook model)         mean  +11.44%  med  -15.10%  win  42.9%  t +11.27
  hold, after costs                  mean   +1.28%  med  -16.88%  win  42.0%  t +1.19
  real path stop -50%, after costs   mean   +0.20%  med  -26.73%  win  39.7%  t +0.19  | vs hold  -1.08pp (paired t -3.98)  stopped 33.2%
  flat-take |net delta|>=0.35        mean   -2.96%  med   -2.50%  win  43.7%  t -7.68  | vs hold  -4.25pp (paired t -4.17)  fired 93.2%
  re-center |net delta|>=0.35 max 1  mean   -2.44%  med  -18.55%  win  39.5%  t -2.58  | vs hold  -3.73pp (paired t -4.79)  avg n 0.93  max cap 1.00x
  re-center |net delta|>=0.35 max unl mean   -8.62%  med  -20.32%  win  36.0%  t -10.86  | vs hold  -9.91pp (paired t -10.95)  avg n 2.01  max cap 1.00x
  flat-take |net delta|>=0.5         mean   -1.80%  med   +0.42%  win  50.4%  t -3.44  | vs hold  -3.08pp (paired t -3.26)  fired 78.9%
  re-center |net delta|>=0.5 max 1   mean   -2.55%  med  -18.30%  win  38.7%  t -2.77  | vs hold  -3.83pp (paired t -4.56)  avg n 0.79  max cap 1.00x
  re-center |net delta|>=0.5 max unl mean   -5.31%  med  -16.66%  win  38.6%  t -6.46  | vs hold  -6.59pp (paired t -7.56)  avg n 1.21  max cap 1.00x
  flat-take move>=x implied0.5       mean   -2.52%  med   -1.36%  win  46.2%  t -6.08  | vs hold  -3.80pp (paired t -3.78)  fired 87.4%
  re-center move>=x implied0.5 max 1 mean   -2.16%  med  -18.36%  win  39.5%  t -2.28  | vs hold  -3.45pp (paired t -4.44)  avg n 0.87  max cap 1.00x
  re-center move>=x implied0.5 max unl mean   -7.00%  med  -18.30%  win  37.5%  t -8.69  | vs hold  -8.28pp (paired t -9.16)  avg n 1.68  max cap 1.01x
  flat-take move>=x implied0.75      mean   -1.14%  med   +5.86%  win  58.9%  t -1.96  | vs hold  -2.43pp (paired t -2.68)  fired 66.2%
  re-center move>=x implied0.75 max 1 mean   -1.83%  med  -17.16%  win  39.7%  t -1.97  | vs hold  -3.11pp (paired t -3.84)  avg n 0.66  max cap 1.00x
  re-center move>=x implied0.75 max unl mean   -3.97%  med  -15.14%  win  40.0%  t -4.69  | vs hold  -5.25pp (paired t -6.18)  avg n 0.92  max cap 1.00x
  flat-take move>=x implied1.0       mean   -0.36%  med  +12.30%  win  59.1%  t -0.50  | vs hold  -1.64pp (paired t -2.06)  fired 46.7%
  re-center move>=x implied1.0 max 1 mean   -1.27%  med  -14.00%  win  41.4%  t -1.36  | vs hold  -2.56pp (paired t -3.31)  avg n 0.47  max cap 1.00x
  re-center move>=x implied1.0 max unl mean   -2.33%  med  -13.29%  win  41.9%  t -2.60  | vs hold  -3.61pp (paired t -4.60)  avg n 0.55  max cap 1.00x
  by year (hold / stop / re-center move>=0.75 max1 / flat-take move>=0.75), after costs:
    2018  n=  288  hold   -2.89  stop   -6.87  rc   +7.37  take   +4.86
    2019  n=  764  hold  -12.03  stop  -12.96  rc  -12.01  take   -7.42
    2020  n=  163  hold  +39.03  stop  +37.51  rc  +25.32  take   -3.55
    2021  n= 1154  hold   -1.86  stop   -3.57  rc   -7.62  take   -2.63
    2022  n=  296  hold  +15.08  stop  +13.92  rc   +3.22  take   +2.44
    2023  n= 1368  hold   +1.08  stop   +1.29  rc   -1.53  take   -1.38
    2024  n= 1015  hold   +0.67  stop   +0.16  rc   +1.37  take   +0.75
    2025  n=  709  hold   +8.53  stop   +6.35  rc   +0.29  take   +1.28
    2026  n=   98  hold   +6.77  stop   +5.19  rc   +5.59  take   +6.75
```
