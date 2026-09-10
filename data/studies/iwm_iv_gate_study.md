# IWM bull put spreads by regime x own-IV percentile (2018-2026, after costs)

Generated 2026-09-10 with `run_qqq_iv_gate_study.py --ticker IWM --iv data/cache/iwm_iv30.parquet` (20 DTE, Friday entries, 50% take / 2x stop, real bid/ask from options_cache 2018-01..2026-03, IV30 = BS-inverted ATM put 25-35 DTE, percentile vs trailing 252).

State on 2026-09-10: IWM 287.4 < 50MA 296.5 (Bearish), VIX 18.0 (LowIV), ATM IV30 ~20.6% (~40th pct vs the last 252 days on file) -> **Bearish_LowIV, IV 30-60: the losing cell for every pair.**

```
IWM bull put spreads, 20 DTE, Fridays 2018-2026, after costs. IV pct known on 94% of trades.

===== pair 0.30/0.15 =====
  ALL                                n= 412  roc net  +1.12%  gross  +1.86%  win  71.8%  med +18.83%  t +0.66  credit/width 18.0%  stops 15.0%
  by OWN IV percentile:
      IV pct <30                     n= 136  roc net  -3.13%  gross  -2.41%  win  66.9%  med +14.67%  t -1.00  credit/width 17.4%  stops 18.4%
      IV pct 30-60                   n= 110  roc net  +4.00%  gross  +4.68%  win  74.5%  med +19.97%  t +1.33  credit/width 18.1%  stops 13.6%
      IV pct 60-80                   n=  63  roc net  +3.81%  gross  +4.45%  win  76.2%  med +20.96%  t +0.87  credit/width 18.5%  stops 11.1%
      IV pct >=80                    n=  80  roc net  +4.84%  gross  +5.60%  win  72.5%  med +21.05%  t +1.38  credit/width 19.3%  stops 15.0%
  by VIX percentile (the proxy the playbook effectively uses):
      VIX pct <30                    n= 158  roc net  +0.08%  gross  +0.78%  win  70.9%  med +17.71%  t +0.03  credit/width 17.7%  stops 16.5%
      VIX pct 30-60                  n=  86  roc net  +4.65%  gross  +5.36%  win  74.4%  med +19.65%  t +1.51  credit/width 17.8%  stops 15.1%
      VIX pct 60-80                  n=  69  roc net  -3.75%  gross  -3.10%  win  65.2%  med +20.92%  t -0.78  credit/width 18.6%  stops 15.9%
      VIX pct >=80                   n=  75  roc net  +6.79%  gross  +7.53%  win  77.3%  med +20.98%  t +1.90  credit/width 19.3%  stops 10.7%
  regime x IV percentile:
      Bearish_HighIV  IV >=80        n=  45  roc net  +7.00%  gross  +7.81%  win  80.0%  med +22.54%  t +1.38  credit/width 19.6%  stops  6.7%
      Bearish_LowIV   IV <30         n=  30  roc net  -1.76%  gross  -1.07%  win  66.7%  med +18.32%  t -0.28  credit/width 17.6%  stops 23.3%
      Bearish_LowIV   IV 30-60       n=  18  roc net  -3.97%  gross  -3.14%  win  61.1%  med +11.37%  t -0.52  credit/width 17.9%  stops 27.8%
      Bearish_LowIV   IV >=80        n=  15  roc net  -0.60%  gross  +0.25%  win  53.3%  med +10.80%  t -0.10  credit/width 17.9%  stops 40.0%
      Bullish_HighIV  IV 30-60       n=  30  roc net  +8.68%  gross  +9.22%  win  80.0%  med +20.41%  t +1.66  credit/width 18.3%  stops 10.0%
      Bullish_HighIV  IV 60-80       n=  18  roc net +11.67%  gross +12.19%  win  83.3%  med +22.91%  t +1.74  credit/width 18.8%  stops  5.6%
      Bullish_LowIV   IV <30         n=  87  roc net  -6.68%  gross  -5.92%  win  63.2%  med +11.18%  t -1.64  credit/width 17.0%  stops 19.5%
      Bullish_LowIV   IV 30-60       n=  54  roc net  +3.58%  gross  +4.30%  win  74.1%  med +19.93%  t +0.85  credit/width 18.1%  stops 13.0%
      Bullish_LowIV   IV 60-80       n=  18  roc net  -4.76%  gross  -3.93%  win  66.7%  med +11.62%  t -0.52  credit/width 17.8%  stops 22.2%
  IV pct >= 60, by year:
      2018                           n=  16  roc net -13.55%  gross -12.41%  win  43.8%  med -18.14%  t -1.55  credit/width 18.2%  stops 37.5%
      2019                           n=  17  roc net +10.51%  gross +11.32%  win  82.4%  med +20.13%  t +2.00  credit/width 17.9%  stops 11.8%
      2020                           n=  24  roc net +11.20%  gross +12.08%  win  79.2%  med +24.36%  t +1.95  credit/width 20.1%  stops 12.5%
      2021                           n=   5  roc net +22.29%  gross +22.71%  win 100.0%  med +22.54%  t +28.74  credit/width 18.5%  stops  0.0%
      2022                           n=  29  roc net  -2.35%  gross  -1.78%  win  62.1%  med +21.05%  t -0.33  credit/width 19.4%  stops 17.2%
      2023                           n=   3  roc net +22.34%  gross +22.76%  win 100.0%  med +21.62%  t +27.11  credit/width 18.5%  stops  0.0%
      2024                           n=  27  roc net  +6.84%  gross  +7.42%  win  81.5%  med +21.75%  t +1.07  credit/width 19.1%  stops  7.4%
      2025                           n=  19  roc net +11.22%  gross +11.83%  win  89.5%  med +20.94%  t +1.66  credit/width 18.5%  stops  5.3%
      2026                           n=   3  roc net -37.44%  gross -36.88%  win  33.3%  med -33.78%  t -1.06  credit/width 18.1%  stops  0.0%
  IV pct < 60, by year:
      2018                           n=  12  roc net -14.13%  gross -13.04%  win  66.7%  med  +7.55%  t -1.14  credit/width 14.4%  stops 16.7%
      2019                           n=  34  roc net  -0.54%  gross  +0.35%  win  70.6%  med +14.51%  t -0.10  credit/width 16.4%  stops 11.8%
      2020                           n=  25  roc net  +0.16%  gross  +0.92%  win  72.0%  med +20.25%  t +0.02  credit/width 17.7%  stops 16.0%
      2021                           n=  45  roc net  +4.39%  gross  +4.95%  win  73.3%  med +19.77%  t +1.00  credit/width 17.5%  stops 20.0%
      2022                           n=  22  roc net  +0.23%  gross  +0.84%  win  68.2%  med +21.24%  t +0.03  credit/width 19.5%  stops 18.2%
      2023                           n=  48  roc net  -6.65%  gross  -5.92%  win  60.4%  med +13.89%  t -1.22  credit/width 17.7%  stops 25.0%
      2024                           n=  24  roc net  +9.53%  gross +10.20%  win  79.2%  med +21.65%  t +2.10  credit/width 19.0%  stops  8.3%
      2025                           n=  31  roc net  -0.92%  gross  -0.34%  win  71.0%  med +20.71%  t -0.14  credit/width 18.4%  stops  9.7%
      2026                           n=   5  roc net +22.91%  gross +23.41%  win 100.0%  med +23.08%  t +80.91  credit/width 19.0%  stops  0.0%

IWM bull put spreads, 20 DTE, Fridays 2018-2026, after costs. IV pct known on 94% of trades.

===== pair 0.25/0.15 =====
  ALL                                n= 412  roc net  +1.43%  gross  +2.50%  win  72.6%  med +14.30%  t +1.06  credit/width 16.0%  stops 20.6%
  by OWN IV percentile:
      IV pct <30                     n= 136  roc net  -1.22%  gross  -0.17%  win  68.4%  med  +9.95%  t -0.51  credit/width 15.4%  stops 25.7%
      IV pct 30-60                   n= 110  roc net  +3.27%  gross  +4.26%  win  74.5%  med +16.06%  t +1.33  credit/width 16.1%  stops 18.2%
      IV pct 60-80                   n=  63  roc net  +2.52%  gross  +3.46%  win  76.2%  med +17.34%  t +0.65  credit/width 16.5%  stops 15.9%
      IV pct >=80                    n=  80  roc net  +4.78%  gross  +5.89%  win  73.8%  med +17.44%  t +1.76  credit/width 17.3%  stops 20.0%
  by VIX percentile (the proxy the playbook effectively uses):
      VIX pct <30                    n= 158  roc net  +0.73%  gross  +1.76%  win  71.5%  med +12.62%  t +0.33  credit/width 15.6%  stops 22.8%
      VIX pct 30-60                  n=  86  roc net  +4.93%  gross  +5.97%  win  76.7%  med +15.64%  t +2.14  credit/width 15.9%  stops 18.6%
      VIX pct 60-80                  n=  69  roc net  -4.41%  gross  -3.45%  win  62.3%  med +17.18%  t -1.07  credit/width 16.6%  stops 24.6%
      VIX pct >=80                   n=  75  roc net  +6.91%  gross  +8.00%  win  80.0%  med +17.54%  t +2.56  credit/width 17.3%  stops 14.7%
  regime x IV percentile:
      Bearish_HighIV  IV >=80        n=  45  roc net  +6.24%  gross  +7.49%  win  80.0%  med +18.90%  t +1.70  credit/width 17.6%  stops 15.6%
      Bearish_LowIV   IV <30         n=  30  roc net  -0.63%  gross  +0.40%  win  66.7%  med  +9.16%  t -0.14  credit/width 15.5%  stops 30.0%
      Bearish_LowIV   IV 30-60       n=  18  roc net  +0.05%  gross  +1.15%  win  61.1%  med  +9.97%  t +0.01  credit/width 16.0%  stops 33.3%
      Bearish_LowIV   IV >=80        n=  15  roc net  +0.42%  gross  +1.50%  win  60.0%  med +14.31%  t +0.07  credit/width 16.2%  stops 40.0%
      Bullish_HighIV  IV 30-60       n=  30  roc net  +4.00%  gross  +4.89%  win  76.7%  med +17.16%  t +0.81  credit/width 16.3%  stops 16.7%
      Bullish_HighIV  IV 60-80       n=  18  roc net +13.97%  gross +14.73%  win  88.9%  med +19.40%  t +4.02  credit/width 16.8%  stops 11.1%
      Bullish_LowIV   IV <30         n=  87  roc net  -3.61%  gross  -2.51%  win  64.4%  med  +8.98%  t -1.17  credit/width 15.0%  stops 28.7%
      Bullish_LowIV   IV 30-60       n=  54  roc net  +3.94%  gross  +4.98%  win  75.9%  med +15.15%  t +1.19  credit/width 15.9%  stops 16.7%
      Bullish_LowIV   IV 60-80       n=  18  roc net  -8.27%  gross  -7.12%  win  61.1%  med  +9.67%  t -0.91  credit/width 15.8%  stops 27.8%
  IV pct >= 60, by year:
      2018                           n=  16  roc net -10.89%  gross  -9.13%  win  43.8%  med -19.81%  t -1.82  credit/width 16.4%  stops 50.0%
      2019                           n=  17  roc net  +9.35%  gross +10.52%  win  82.4%  med +17.18%  t +2.43  credit/width 15.9%  stops 17.6%
      2020                           n=  24  roc net +12.77%  gross +13.98%  win  83.3%  med +21.24%  t +3.40  credit/width 18.2%  stops 16.7%
      2021                           n=   5  roc net +17.14%  gross +17.84%  win 100.0%  med +19.52%  t +8.08  credit/width 16.5%  stops  0.0%
      2022                           n=  29  roc net  -3.85%  gross  -3.00%  win  65.5%  med +17.83%  t -0.60  credit/width 17.5%  stops 20.7%
      2023                           n=   3  roc net +15.71%  gross +16.52%  win 100.0%  med +18.89%  t +4.48  credit/width 16.2%  stops  0.0%
      2024                           n=  27  roc net  +4.23%  gross  +5.01%  win  77.8%  med +18.50%  t +0.71  credit/width 16.9%  stops 11.1%
      2025                           n=  19  roc net +10.83%  gross +11.76%  win  89.5%  med +16.72%  t +3.18  credit/width 16.6%  stops 10.5%
      2026                           n=   3  roc net -30.64%  gross -29.89%  win  33.3%  med -10.24%  t -0.85  credit/width 16.3%  stops  0.0%
  IV pct < 60, by year:
      2018                           n=  12  roc net -14.94%  gross -13.57%  win  66.7%  med  +6.10%  t -1.23  credit/width 12.7%  stops 16.7%
      2019                           n=  34  roc net  +3.99%  gross  +5.31%  win  79.4%  med +12.04%  t +1.24  credit/width 14.5%  stops 17.6%
      2020                           n=  25  roc net  -1.49%  gross  -0.29%  win  68.0%  med  +8.57%  t -0.26  credit/width 15.8%  stops 24.0%
      2021                           n=  45  roc net  +0.98%  gross  +1.85%  win  68.9%  med +10.54%  t +0.27  credit/width 15.6%  stops 28.9%
      2022                           n=  22  roc net  +3.09%  gross  +3.93%  win  72.7%  med +19.19%  t +0.46  credit/width 17.3%  stops 22.7%
      2023                           n=  48  roc net  -3.90%  gross  -2.86%  win  64.6%  med  +9.95%  t -0.85  credit/width 15.6%  stops 29.2%
      2024                           n=  24  roc net  +7.33%  gross  +8.30%  win  79.2%  med +17.88%  t +2.05  credit/width 16.5%  stops 12.5%
      2025                           n=  31  roc net  +2.45%  gross  +3.32%  win  67.7%  med +17.38%  t +0.54  credit/width 16.3%  stops 19.4%
      2026                           n=   5  roc net +19.53%  gross +20.22%  win 100.0%  med +19.44%  t +63.34  credit/width 16.8%  stops  0.0%

===== pair 0.35/0.25 =====
  ALL                                n= 412  roc net  -1.90%  gross  +0.02%  win  77.2%  med +18.56%  t -0.78  credit/width 25.4%  stops  0.5%
  by OWN IV percentile:
      IV pct <30                     n= 136  roc net  -6.08%  gross  -4.40%  win  73.5%  med +17.66%  t -1.36  credit/width 24.7%  stops  0.7%
      IV pct 30-60                   n= 110  roc net  -1.64%  gross  +0.19%  win  76.4%  med +18.93%  t -0.34  credit/width 25.6%  stops  0.0%
      IV pct 60-80                   n=  63  roc net  -4.04%  gross  -2.16%  win  77.8%  med +17.44%  t -0.64  credit/width 25.8%  stops  0.0%
      IV pct >=80                    n=  80  roc net  +6.43%  gross  +8.37%  win  82.5%  med +20.79%  t +1.25  credit/width 26.8%  stops  0.0%
  by VIX percentile (the proxy the playbook effectively uses):
      VIX pct <30                    n= 158  roc net  -1.91%  gross  -0.20%  win  75.9%  med +18.99%  t -0.48  credit/width 25.1%  stops  0.6%
      VIX pct 30-60                  n=  86  roc net  -4.34%  gross  -2.52%  win  75.6%  med +16.16%  t -0.80  credit/width 25.2%  stops  0.0%
      VIX pct 60-80                  n=  69  roc net  -9.46%  gross  -7.66%  win  72.5%  med +17.91%  t -1.42  credit/width 26.1%  stops  0.0%
      VIX pct >=80                   n=  75  roc net  +7.33%  gross  +9.34%  win  84.0%  med +19.75%  t +1.46  credit/width 26.5%  stops  0.0%
  regime x IV percentile:
      Bearish_HighIV  IV >=80        n=  45  roc net  +7.29%  gross  +9.40%  win  82.2%  med +20.78%  t +1.12  credit/width 26.9%  stops  0.0%
      Bearish_LowIV   IV <30         n=  30  roc net  -9.36%  gross  -8.03%  win  70.0%  med +18.93%  t -0.89  credit/width 24.7%  stops  0.0%
      Bearish_LowIV   IV 30-60       n=  18  roc net -12.53%  gross -10.54%  win  72.2%  med +15.83%  t -0.93  credit/width 25.2%  stops  0.0%
      Bearish_LowIV   IV >=80        n=  15  roc net  -9.27%  gross  -7.50%  win  73.3%  med +19.33%  t -0.62  credit/width 25.7%  stops  0.0%
      Bullish_HighIV  IV 30-60       n=  30  roc net  +7.92%  gross  +9.52%  win  83.3%  med +19.98%  t +1.10  credit/width 25.3%  stops  0.0%
      Bullish_HighIV  IV 60-80       n=  18  roc net  +6.60%  gross  +8.60%  win  88.9%  med +18.31%  t +0.71  credit/width 25.9%  stops  0.0%
      Bullish_LowIV   IV <30         n=  87  roc net  -8.51%  gross  -6.68%  win  72.4%  med +16.44%  t -1.51  credit/width 24.4%  stops  1.1%
      Bullish_LowIV   IV 30-60       n=  54  roc net  -4.87%  gross  -3.02%  win  72.2%  med +20.15%  t -0.68  credit/width 25.9%  stops  0.0%
      Bullish_LowIV   IV 60-80       n=  18  roc net -21.19%  gross -19.28%  win  61.1%  med +13.29%  t -1.59  credit/width 25.5%  stops  0.0%
  IV pct >= 60, by year:
      2018                           n=  16  roc net  -8.66%  gross  -6.36%  win  75.0%  med +16.56%  t -0.62  credit/width 25.5%  stops  0.0%
      2019                           n=  17  roc net  +8.24%  gross +10.30%  win  88.2%  med +19.95%  t +0.81  credit/width 24.9%  stops  0.0%
      2020                           n=  24  roc net  +3.21%  gross  +5.56%  win  83.3%  med +19.05%  t +0.33  credit/width 27.1%  stops  0.0%
      2021                           n=   5  roc net +14.62%  gross +16.25%  win  80.0%  med +19.23%  t +2.88  credit/width 24.9%  stops  0.0%
      2022                           n=  29  roc net  -3.74%  gross  -2.21%  win  75.9%  med +23.41%  t -0.36  credit/width 27.1%  stops  0.0%
      2023                           n=   3  roc net +23.03%  gross +24.65%  win 100.0%  med +17.28%  t +3.59  credit/width 25.7%  stops  0.0%
      2024                           n=  27  roc net +11.79%  gross +13.57%  win  85.2%  med +21.56%  t +1.53  credit/width 27.3%  stops  0.0%
      2025                           n=  19  roc net  -0.10%  gross  +1.81%  win  78.9%  med +17.32%  t -0.01  credit/width 25.7%  stops  0.0%
      2026                           n=   3  roc net -56.37%  gross -55.14%  win  33.3%  med -101.25%  t -1.25  credit/width 24.7%  stops  0.0%
  IV pct < 60, by year:
      2018                           n=  12  roc net -18.32%  gross -16.05%  win  58.3%  med +10.42%  t -1.20  credit/width 21.7%  stops  0.0%
      2019                           n=  34  roc net  -6.16%  gross  -3.95%  win  76.5%  med +15.10%  t -0.71  credit/width 23.7%  stops  0.0%
      2020                           n=  25  roc net  +4.16%  gross  +6.32%  win  84.0%  med +16.80%  t +0.48  credit/width 24.8%  stops  0.0%
      2021                           n=  45  roc net  +4.10%  gross  +5.49%  win  80.0%  med +19.22%  t +0.63  credit/width 24.7%  stops  2.2%
      2022                           n=  22  roc net -18.71%  gross -17.36%  win  59.1%  med +16.63%  t -1.48  credit/width 26.9%  stops  0.0%
      2023                           n=  48  roc net -10.30%  gross  -8.70%  win  70.8%  med +19.09%  t -1.25  credit/width 25.2%  stops  0.0%
      2024                           n=  24  roc net  +4.18%  gross  +6.06%  win  83.3%  med +19.93%  t +0.42  credit/width 26.9%  stops  0.0%
      2025                           n=  31  roc net  -5.88%  gross  -4.30%  win  71.0%  med +20.88%  t -0.59  credit/width 25.9%  stops  0.0%
      2026                           n=   5  roc net +24.36%  gross +26.35%  win 100.0%  med +20.57%  t +6.39  credit/width 25.8%  stops  0.0%

===== pair 0.45/0.35 =====
  ALL                                n= 412  roc net  -1.47%  gross  +1.39%  win  70.1%  med +27.07%  t -0.48  credit/width 35.1%  stops  0.0%
  by OWN IV percentile:
      IV pct <30                     n= 136  roc net  -9.10%  gross  -6.49%  win  64.0%  med +25.85%  t -1.63  credit/width 34.6%  stops  0.0%
      IV pct 30-60                   n= 110  roc net  +0.07%  gross  +2.74%  win  70.9%  med +28.35%  t +0.01  credit/width 35.4%  stops  0.0%
      IV pct 60-80                   n=  63  roc net  -3.28%  gross  -0.54%  win  69.8%  med +27.68%  t -0.42  credit/width 35.2%  stops  0.0%
      IV pct >=80                    n=  80  roc net  +9.80%  gross +12.82%  win  77.5%  med +29.31%  t +1.54  credit/width 36.1%  stops  0.0%
  by VIX percentile (the proxy the playbook effectively uses):
      VIX pct <30                    n= 158  roc net  -1.46%  gross  +1.12%  win  69.0%  med +28.97%  t -0.29  credit/width 35.1%  stops  0.0%
      VIX pct 30-60                  n=  86  roc net  -8.03%  gross  -5.30%  win  65.1%  med +25.30%  t -1.16  credit/width 35.0%  stops  0.0%
      VIX pct 60-80                  n=  69  roc net  -7.67%  gross  -4.99%  win  65.2%  med +28.00%  t -0.97  credit/width 35.5%  stops  0.0%
      VIX pct >=80                   n=  75  roc net  +9.98%  gross +13.07%  win  80.0%  med +28.41%  t +1.56  credit/width 35.6%  stops  0.0%
  regime x IV percentile:
      Bearish_HighIV  IV >=80        n=  45  roc net  +7.28%  gross +10.61%  win  77.8%  med +29.18%  t +0.87  credit/width 36.0%  stops  0.0%
      Bearish_LowIV   IV <30         n=  30  roc net -12.63%  gross -10.39%  win  60.0%  med +23.49%  t -1.03  credit/width 34.2%  stops  0.0%
      Bearish_LowIV   IV 30-60       n=  18  roc net  -9.62%  gross  -6.78%  win  66.7%  med +21.51%  t -0.63  credit/width 34.5%  stops  0.0%
      Bearish_LowIV   IV >=80        n=  15  roc net  -6.81%  gross  -3.74%  win  66.7%  med +24.47%  t -0.43  credit/width 34.9%  stops  0.0%
      Bullish_HighIV  IV 30-60       n=  30  roc net  +0.94%  gross  +3.17%  win  73.3%  med +27.77%  t +0.08  credit/width 34.8%  stops  0.0%
      Bullish_HighIV  IV 60-80       n=  18  roc net +16.53%  gross +19.79%  win  88.9%  med +27.84%  t +1.59  credit/width 34.9%  stops  0.0%
      Bullish_LowIV   IV <30         n=  87  roc net -10.29%  gross  -7.51%  win  64.4%  med +25.58%  t -1.47  credit/width 34.4%  stops  0.0%
      Bullish_LowIV   IV 30-60       n=  54  roc net  +1.29%  gross  +4.12%  win  70.4%  med +29.25%  t +0.14  credit/width 36.1%  stops  0.0%
      Bullish_LowIV   IV 60-80       n=  18  roc net -35.66%  gross -32.77%  win  44.4%  med -53.41%  t -2.25  credit/width 35.5%  stops  0.0%
  IV pct >= 60, by year:
      2018                           n=  16  roc net -18.65%  gross -15.19%  win  56.2%  med +21.90%  t -1.20  credit/width 35.3%  stops  0.0%
      2019                           n=  17  roc net +10.26%  gross +13.56%  win  82.4%  med +25.51%  t +0.84  credit/width 34.3%  stops  0.0%
      2020                           n=  24  roc net +12.33%  gross +16.14%  win  83.3%  med +27.84%  t +1.11  credit/width 35.7%  stops  0.0%
      2021                           n=   5  roc net  +0.66%  gross  +3.83%  win  80.0%  med +25.68%  t +0.03  credit/width 33.9%  stops  0.0%
      2022                           n=  29  roc net  +4.34%  gross  +6.54%  win  72.4%  med +31.87%  t +0.37  credit/width 36.5%  stops  0.0%
      2023                           n=   3  roc net +49.71%  gross +51.55%  win 100.0%  med +52.67%  t +9.16  credit/width 35.5%  stops  0.0%
      2024                           n=  27  roc net  +8.70%  gross +11.17%  win  74.1%  med +34.18%  t +0.70  credit/width 37.3%  stops  0.0%
      2025                           n=  19  roc net  +7.52%  gross +10.35%  win  78.9%  med +31.22%  t +0.56  credit/width 34.8%  stops  0.0%
      2026                           n=   3  roc net -83.64%  gross -81.75%  win   0.0%  med -101.81%  t -4.57  credit/width 33.8%  stops  0.0%
  IV pct < 60, by year:
      2018                           n=  12  roc net -38.39%  gross -34.82%  win  41.7%  med -33.54%  t -2.17  credit/width 31.3%  stops  0.0%
      2019                           n=  34  roc net  -6.57%  gross  -2.79%  win  67.6%  med +21.42%  t -0.64  credit/width 33.5%  stops  0.0%
      2020                           n=  25  roc net  -1.37%  gross  +1.57%  win  72.0%  med +27.50%  t -0.11  credit/width 34.5%  stops  0.0%
      2021                           n=  45  roc net -10.91%  gross  -8.86%  win  62.2%  med +25.58%  t -1.13  credit/width 34.1%  stops  0.0%
      2022                           n=  22  roc net -22.88%  gross -20.76%  win  54.5%  med +25.79%  t -1.44  credit/width 36.5%  stops  0.0%
      2023                           n=  48  roc net  -3.98%  gross  -1.62%  win  68.8%  med +27.39%  t -0.42  credit/width 35.3%  stops  0.0%
      2024                           n=  24  roc net +21.87%  gross +24.47%  win  83.3%  med +40.91%  t +1.85  credit/width 37.4%  stops  0.0%
      2025                           n=  31  roc net  -1.21%  gross  +1.17%  win  67.7%  med +32.35%  t -0.10  credit/width 36.1%  stops  0.0%
      2026                           n=   5  roc net +37.29%  gross +40.17%  win 100.0%  med +29.22%  t +6.33  credit/width 35.5%  stops  0.0%
```
