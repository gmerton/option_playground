# Variance risk premium panel — stage-one screen

Generated 2026-09-15. Universe: GLD, IWM, QQQ, SPY, TLT, XLE, XLF, XLP, XLU, XLV.
Sample 2010-01-04 to 2026-05-01, 89,200 ticker-days with a complete forward window.

`vrp = ATM implied vol - realized vol over the matching forward window`, in annualized vol points. Positive means implied was rich and a vol SELLER was paid. Negative means implied was cheap and a vol BUYER was paid.

**Inference.** Rows overlap (a 30-day window observed daily repeats 29/30 of itself) and tickers are cross-sectionally correlated, so a plain t-test is badly wrong here. Each cell is collapsed to a daily cross-sectional mean, then corrected with Newey-West at the overlap lag and a moving-block bootstrap. `t_naive` is printed only to show the size of the error. The hurdle is Bonferroni at 50 declared trials: **t >= 3.29**, not 2.0.

## 1. Premium by tenor (pooled)

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  10d pooled               29,248   3,776    1.75%   2.31%    75%     19.9    8.93     7.54    [ +1.34, +2.09]    3.29  YES
  30d pooled               32,365   3,654    0.78%   1.68%    71%      7.8    2.08     1.73    [ -0.04, +1.41]    3.29  -
  90d pooled               27,587   3,928    0.84%   2.08%    71%      7.9    1.30     1.11    [ -0.58, +1.95]    3.29  -
```

## 2.10 Premium by ticker — 10d

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  XLF                       1,519   1,519    2.52%   3.47%    72%      8.4    4.50     3.34    [ +1.36, +3.48]    3.29  YES
  IWM                       3,578   3,578    2.40%   3.20%    71%     18.7    8.67     7.06    [ +1.83, +2.90]    3.29  YES
  XLE                       3,297   3,297    2.00%   3.13%    68%     11.0    5.01     4.18    [ +1.21, +2.73]    3.29  YES
  XLP                       1,953   1,953    1.90%   2.36%    73%     11.8    5.45     4.47    [ +1.18, +2.49]    3.29  YES
  XLV                       2,737   2,737    1.79%   2.49%    72%     14.8    6.62     5.62    [ +1.28, +2.27]    3.29  YES
  XLU                       2,241   2,241    1.54%   2.31%    68%      9.2    4.09     3.48    [ +0.80, +2.20]    3.29  YES
  GLD                       3,595   3,595    1.48%   2.14%    68%     14.4    6.87     5.43    [ +1.06, +1.88]    3.29  YES
  QQQ                       3,332   3,332    1.38%   2.61%    67%     10.6    4.78     4.00    [ +0.80, +1.91]    3.29  YES
  SPY                       3,654   3,654    1.26%   2.35%    70%     11.6    5.22     4.40    [ +0.78, +1.71]    3.29  YES
  TLT                       3,342   3,342    1.21%   1.53%    66%     12.8    6.88     4.98    [ +0.88, +1.53]    3.29  YES
```

## 2.30 Premium by ticker — 30d

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  IWM                       3,643   3,643    1.27%   2.24%    69%     10.3    2.78     2.27    [ +0.33, +2.07]    3.29  -
  XLF                       2,337   2,337    1.22%   2.32%    70%      6.3    1.95     1.54    [ -0.24, +2.24]    3.29  -
  XLP                       2,773   2,773    1.02%   1.72%    70%      9.1    2.48     2.00    [ +0.11, +1.70]    3.29  -
  XLV                       3,153   3,153    0.87%   1.89%    69%      8.0    2.10     1.74    [ +0.02, +1.59]    3.29  -
  SPY                       3,644   3,644    0.69%   1.86%    69%      5.9    1.57     1.30    [ -0.25, +1.45]    3.29  -
  XLE                       3,476   3,476    0.61%   2.29%    67%      3.5    0.93     0.80    [ -0.86, +1.70]    3.29  -
  QQQ                       3,416   3,416    0.61%   1.96%    66%      4.7    1.25     1.05    [ -0.41, +1.51]    3.29  -
  TLT                       3,405   3,405    0.44%   0.70%    60%      5.6    1.67     1.26    [ -0.10, +0.90]    3.29  -
  GLD                       3,596   3,596    0.39%   1.04%    63%      4.6    1.30     1.02    [ -0.25, +0.93]    3.29  -
  XLU                       2,922   2,922    0.39%   1.26%    65%      2.8    0.73     0.61    [ -0.77, +1.24]    3.29  -
```

## 2.90 Premium by ticker — 90d

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  XLP                       1,239   1,239    1.66%   2.22%    76%     11.2    3.61     2.20    [ +0.69, +2.55]    3.29  YES
  IWM                       3,816   3,816    1.18%   2.71%    71%      9.1    1.45     1.22    [ -0.60, +2.68]    3.29  -
  SPY                       3,883   3,883    1.15%   2.66%    73%      9.5    1.57     1.25    [ -0.50, +2.51]    3.29  -
  XLU                       1,385   1,385    1.11%   1.75%    72%      7.0    1.90     1.58    [ -0.29, +2.09]    3.29  -
  XLV                       1,716   1,716    0.89%   2.15%    73%      5.2    1.03     1.18    [ -1.09, +2.29]    3.29  -
  QQQ                       3,565   3,565    0.79%   2.15%    70%      6.4    1.08     0.87    [ -0.74, +2.12]    3.29  -
  XLF                       2,035   2,035    0.70%   2.46%    68%      3.2    0.65     0.80    [ -1.84, +2.40]    3.29  -
  GLD                       3,686   3,686    0.46%   1.33%    68%      5.8    0.95     0.76    [ -0.54, +1.38]    3.29  -
  TLT                       3,510   3,510    0.38%   0.85%    65%      5.0    0.85     0.70    [ -0.58, +1.19]    3.29  -
  XLE                       2,752   2,752   -0.03%   2.23%    68%     -0.1   -0.02     0.03    [ -3.11, +2.26]    3.29  -
```

## 3. Conditioning on state observable at entry

Every column used here is known at t. `iv_pctile` is own-IV rank vs its trailing 252 observations, the gate that works on the paid-to-wait put spreads. `vrp_trail` is implied minus TRAILING realized, the naive richness proxy a desk can see without forecasting anything.

### 10d by own IV percentile

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  IVpct 80-100              6,072   1,641    2.30%   3.00%    71%      9.7    4.76     3.72    [ +1.32, +3.17]    3.29  YES
  IVpct 40-60               5,053   2,246    2.02%   2.53%    74%     20.0   11.47     7.55    [ +1.67, +2.35]    3.29  YES
  IVpct 60-80               5,043   2,035    1.97%   2.78%    73%     15.5    8.34     5.86    [ +1.49, +2.41]    3.29  YES
  IVpct 20-40               5,148   2,307    1.77%   2.27%    72%     17.8   10.15     6.78    [ +1.42, +2.08]    3.29  YES
  IVpct 0-20                7,342   2,121    1.28%   1.61%    68%     15.7    8.78     6.00    [ +1.01, +1.56]    3.29  YES
```

### 10d by VIX regime

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  VIX 20-25                 4,740     568    2.60%   3.31%    78%     12.1    7.34     4.71    [ +1.87, +3.23]    3.29  YES
  VIX 15-20                 9,886   1,292    1.84%   2.29%    75%     15.8    8.73     6.09    [ +1.44, +2.23]    3.29  YES
  VIX>25                    4,179     483    1.82%   3.79%    75%      3.8    1.68     1.47    [ -0.49, +3.56]    3.29  -
  VIX<15                   10,443   1,433    1.31%   1.91%    74%     14.0    7.07     5.44    [ +0.94, +1.67]    3.29  YES
```

### 10d by implied vs trailing realized

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  trail Q4 (rich)           7,312   2,586    2.33%   2.86%    73%     16.5    9.01     6.33    [ +1.82, +2.83]    3.29  YES
  trail Q1 (cheap)          7,312   2,581    1.83%   2.49%    72%     14.9    7.39     5.66    [ +1.30, +2.25]    3.29  YES
  trail Q2                  7,312   3,040    1.50%   2.06%    70%     15.3    8.99     5.83    [ +1.16, +1.81]    3.29  YES
  trail Q3                  7,312   3,015    1.42%   2.06%    70%     13.5    7.46     5.28    [ +1.03, +1.76]    3.29  YES
```

### 30d by own IV percentile

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  IVpct 40-60               5,483   2,253    0.90%   1.76%    69%      7.6    2.64     2.02    [ +0.14, +1.46]    3.29  -
  IVpct 20-40               5,595   2,253    0.86%   1.54%    69%      7.8    2.69     2.13    [ +0.16, +1.46]    3.29  -
  IVpct 80-100              6,613   1,622    0.83%   2.00%    66%      3.6    1.24     0.80    [ -0.57, +2.00]    3.29  -
  IVpct 0-20                8,673   2,227    0.51%   1.07%    68%      5.4    1.80     1.35    [ -0.10, +1.00]    3.29  -
  IVpct 60-80               5,411   2,041    0.42%   1.66%    66%      2.8    0.92     0.83    [ -0.53, +1.18]    3.29  -
```

### 30d by VIX regime

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  VIX 20-25                 5,111     557    1.75%   2.75%    76%      8.7    3.24     2.05    [ +0.56, +2.67]    3.29  -
  VIX>25                    4,313     468    1.17%   3.26%    72%      2.3    0.77     0.92    [ -2.44, +3.36]    3.29  -
  VIX 15-20                10,861   1,225    0.87%   1.89%    73%      5.8    2.44     1.53    [ +0.08, +1.48]    3.29  -
  VIX<15                   12,080   1,404    0.17%   1.05%    68%      1.4    0.49     0.52    [ -0.56, +0.81]    3.29  -
```

### 30d by implied vs trailing realized

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  trail Q4 (rich)           8,091   2,345    1.09%   1.91%    69%      8.0    2.70     1.84    [ +0.20, +1.77]    3.29  -
  trail Q1 (cheap)          8,092   2,416    0.83%   1.84%    69%      5.6    1.74     1.53    [ -0.23, +1.60]    3.29  -
  trail Q3                  8,091   2,933    0.46%   1.33%    67%      4.4    1.37     1.02    [ -0.24, +1.05]    3.29  -
  trail Q2                  8,091   2,998    0.45%   1.19%    66%      4.0    1.25     1.06    [ -0.36, +1.05]    3.29  -
```

### 90d by own IV percentile

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  IVpct 80-100              5,594   1,650    1.11%   1.99%    67%      7.6    2.10     1.09    [ -0.09, +1.98]    3.29  -
  IVpct 60-80               4,368   1,911    0.56%   1.64%    65%      3.8    0.85     0.54    [ -0.92, +1.65]    3.29  -
  IVpct 0-20                7,694   2,225    0.35%   1.58%    71%      2.3    0.45     0.77    [ -1.39, +1.56]    3.29  -
  IVpct 20-40               4,781   2,273    0.32%   1.79%    72%      1.9    0.36     0.48    [ -1.70, +1.69]    3.29  -
  IVpct 40-60               4,560   2,216    0.29%   1.95%    69%      1.8    0.34     0.34    [ -1.67, +1.59]    3.29  -
```

### 90d by VIX regime

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  VIX>25                    3,921     529    3.45%   4.06%    82%     13.2    4.85     3.16    [ +1.84, +4.69]    3.29  YES
  VIX 20-25                 4,386     621    2.53%   3.35%    79%     13.4    4.10     2.09    [ +1.18, +3.63]    3.29  YES
  VIX 15-20                 9,841   1,396    0.44%   2.14%    71%      2.5    0.65     0.61    [ -0.94, +1.74]    3.29  -
  VIX<15                    9,439   1,382   -0.51%   1.04%    62%     -2.6   -0.51     0.05    [ -2.87, +1.10]    3.29  -
```

### 90d by implied vs trailing realized

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  trail Q2                  6,897   2,937    0.75%   1.49%    72%      6.5    1.52     1.27    [ -0.33, +1.61]    3.29  -
  trail Q1 (cheap)          6,897   2,294    0.57%   1.41%    66%      4.6    0.89     0.64    [ -0.80, +1.71]    3.29  -
  trail Q4 (rich)           6,897   2,179    0.53%   2.67%    71%      2.9    0.52     0.59    [ -1.76, +2.22]    3.29  -
  trail Q3                  6,896   2,796    0.28%   1.82%    68%      1.9    0.35     0.56    [ -1.49, +1.69]    3.29  -
```

## 4. Stability by year

### 10d by year

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  2010                        369     118    3.76%   4.25%    82%      9.9    7.21     3.85    [ +2.65, +4.78]    3.29  YES
  2011                        655     147    1.84%   2.34%    71%      3.6    2.21     1.65    [ -0.01, +3.18]    3.29  -
  2012                        726     160    2.87%   3.36%    81%      9.4    6.48     3.57    [ +2.01, +3.71]    3.29  YES
  2013                      1,265     251    1.63%   2.49%    77%      6.0    3.06     2.40    [ +0.43, +2.52]    3.29  -
  2014                      1,821     252    1.17%   1.65%    70%      5.6    2.60     2.14    [ +0.36, +2.06]    3.29  -
  2015                      2,058     252    1.13%   1.89%    70%      4.0    1.93     1.56    [ -0.04, +2.20]    3.29  -
  2016                      2,088     252    2.47%   2.85%    81%     10.1    5.33     3.89    [ +1.63, +3.39]    3.29  YES
  2017                      1,843     251    2.08%   2.27%    82%     15.4    8.45     5.78    [ +1.59, +2.57]    3.29  YES
  2018                      2,074     251    0.20%   1.52%    65%      0.7    0.32     0.28    [ -1.11, +1.38]    3.29  -
  2019                      2,049     252    1.92%   2.22%    80%      9.9    4.78     3.83    [ +1.10, +2.62]    3.29  YES
  2020                      2,330     253    0.51%   3.57%    74%      0.6    0.24     0.26    [ -3.75, +3.92]    3.29  -
  2021                      2,260     252    2.51%   2.99%    78%     11.0    5.60     4.14    [ +1.65, +3.36]    3.29  YES
  2022                      2,390     251    1.60%   2.23%    67%      5.9    2.86     2.28    [ +0.49, +2.66]    3.29  -
  2023                      2,155     250    1.79%   1.70%    74%     10.1    5.01     3.83    [ +1.10, +2.46]    3.29  YES
  2024                      2,129     252    1.42%   2.03%    71%      7.1    3.44     2.68    [ +0.60, +2.15]    3.29  YES
  2025                      2,358     249    2.12%   3.06%    82%      4.7    2.09     1.82    [ -0.15, +3.74]    3.29  -
  2026                        678      83    3.34%   2.96%    84%      7.3    4.04     2.83    [ +1.69, +4.83]    3.29  YES
```

### 30d by year

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  2010                        559     109    3.20%   3.79%    86%      7.0    3.03     2.94    [ +0.63, +4.76]    3.29  -
  2011                        652     106    0.13%   1.36%    68%      0.2    0.08     0.69    [ -4.13, +2.32]    3.29  -
  2012                        671     113    2.50%   2.45%    88%     14.1   11.53     4.11    [ +2.03, +2.59]    3.29  YES
  2013                      1,353     228    0.89%   1.47%    73%      3.8    1.25     0.91    [ -0.81, +2.02]    3.29  -
  2014                      2,150     250    0.53%   0.65%    56%      2.9    0.88     0.62    [ -0.47, +1.85]    3.29  -
  2015                      2,306     252   -0.09%   0.79%    62%     -0.4   -0.11    -0.12    [ -1.84, +1.57]    3.29  -
  2016                      2,351     252    1.70%   2.32%    72%      8.7    3.00     1.92    [ +0.63, +2.76]    3.29  -
  2017                      2,200     251    1.98%   1.91%    97%     24.6    8.31     5.36    [ +1.55, +2.46]    3.29  YES
  2018                      2,332     251   -1.11%   0.60%    55%     -3.9   -1.19    -0.86    [ -2.84, +0.78]    3.29  -
  2019                      2,342     252    1.46%   2.24%    76%      7.7    2.19     1.70    [ -0.17, +2.49]    3.29  -
  2020                      2,482     253   -2.57%   3.22%    67%     -2.3   -0.58    -0.49    [-12.50, +4.18]    3.29  -
  2021                      2,488     252    2.14%   2.13%    78%     12.9    4.67     2.75    [ +1.20, +3.06]    3.29  YES
  2022                      2,491     251    0.29%   0.96%    56%      1.2    0.37     0.28    [ -1.34, +1.77]    3.29  -
  2023                      2,404     250    1.45%   1.41%    76%      9.8    3.08     2.13    [ +0.51, +2.40]    3.29  -
  2024                      2,422     252    0.87%   1.01%    69%      5.7    1.82     1.18    [ -0.16, +1.75]    3.29  -
  2025                      2,464     249    0.63%   2.37%    78%      1.5    0.42     0.38    [ -2.81, +3.05]    3.29  -
  2026                        698      83    1.96%   2.27%    76%      5.2    1.57      nan    [ +0.22, +4.51]    3.29  -
```

### 90d by year

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  2010                        988     235    3.93%   5.65%    77%     11.5    2.00      nan    [ -0.61, +7.34]    3.29  -
  2011                      1,490     242   -0.37%   2.79%    64%     -0.6   -0.10      nan    [ -9.70, +3.84]    3.29  -
  2012                      1,501     241    4.06%   4.10%    95%     29.7    7.45      nan    [ +2.67, +4.99]    3.29  YES
  2013                      1,479     233    1.04%   1.48%    67%      6.0    1.06      nan    [ -1.09, +2.90]    3.29  -
  2014                      1,541     232    0.69%   0.83%    62%      4.8    0.82      nan    [ -0.96, +2.60]    3.29  -
  2015                      1,565     232    0.05%   0.90%    54%      0.2    0.04      nan    [ -2.18, +2.09]    3.29  -
  2016                      1,701     242    2.72%   2.50%    91%     19.4    5.37      nan    [ +1.58, +3.07]    3.29  YES
  2017                      1,667     251    2.29%   3.00%    85%     13.9    2.52     0.96    [ +1.59, +3.56]    3.29  -
  2018                      1,729     242   -1.00%  -0.41%    45%     -3.7   -0.71      nan    [ -3.61, +2.08]    3.29  -
  2019                      1,697     233   -1.03%   0.29%    53%     -1.8   -0.49      nan    [ -1.59, +2.64]    3.29  -
  2020                      1,903     233   -4.34%   3.24%    80%     -3.5   -0.64      nan    [-10.64, +4.85]    3.29  -
  2021                      1,887     237    2.58%   2.89%    82%     15.5    2.76      nan    [ +1.42, +4.34]    3.29  -
  2022                      2,025     241    0.11%   0.05%    50%      0.5    0.10      nan    [ -2.04, +1.97]    3.29  -
  2023                      1,932     250    2.06%   1.74%    87%     15.6    3.07     3.47    [ +0.78, +3.64]    3.29  -
  2024                      1,964     252    0.69%   1.01%    72%      5.7    1.36     0.68    [ -0.62, +1.55]    3.29  -
  2025                      1,956     249   -0.42%   1.50%    65%     -1.0   -0.18    -0.29    [ -3.47, +3.98]    3.29  -
  2026                        562      83    1.44%   1.84%    75%      4.7    1.35      nan    [ +0.51, +2.41]    3.29  -
```

## 5. Term-structure premium (the calendar question)

Forward implied vol between day 30 and day 90, minus the realized vol that then shows up in exactly that window. This is what a 30/90 calendar or a forward-factor trade is reaching for. The calendar path study found no capturable edge on these same names; this says whether the premium was absent in the first place or present but uncapturable.

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  fwd 30->90 pooled        24,038   3,511    1.01%   2.38%    70%      7.9    1.45     1.22    [ -0.50, +2.18]    3.29  -
```

### forward 30->90 premium by ticker

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  XLP                       1,050   1,050    2.15%   2.45%    78%     12.7    4.16     2.51    [ +1.17, +3.22]    3.29  YES
  XLU                       1,191   1,191    1.78%   2.03%    77%      9.2    3.20     2.54    [ +0.61, +2.82]    3.29  -
  SPY                       3,481   3,481    1.58%   3.24%    75%     10.8    1.99     1.68    [ -0.08, +3.07]    3.29  -
  XLF                       1,485   1,485    1.46%   2.73%    69%      6.4    1.75     1.90    [ -0.31, +2.93]    3.29  -
  QQQ                       3,205   3,205    1.24%   2.73%    70%      8.0    1.51     1.27    [ -0.35, +2.78]    3.29  -
  IWM                       3,412   3,412    1.21%   2.81%    70%      7.8    1.42     1.21    [ -0.59, +2.73]    3.29  -
  XLV                       1,527   1,527    1.20%   2.70%    73%      5.6    1.16     0.94    [ -1.16, +2.88]    3.29  -
  TLT                       3,032   3,032    0.63%   1.09%    68%      7.0    1.31     1.09    [ -0.42, +1.46]    3.29  -
  GLD                       3,257   3,257    0.46%   1.61%    67%      4.7    0.90     0.75    [ -0.66, +1.39]    3.29  -
  XLE                       2,398   2,398   -0.15%   2.67%    70%     -0.5   -0.10    -0.08    [ -3.76, +2.39]    3.29  -
```

### forward 30->90 premium by forward vol ratio

```
  cell                      n_obs   dates     mean     med    pos  t_naive    t_NW  t_nolap        boot 95% CI  hurdle  ok
  ------------------------------------------------------------------------------------------------------------------------
  FVR Q4 (steep)            6,010   2,076    0.99%   2.51%    74%      5.7    1.20     1.12    [ -0.79, +2.40]    3.29  -
  FVR Q3                    6,009   2,582    0.98%   2.30%    71%      6.3    1.39     1.25    [ -0.62, +2.18]    3.29  -
  FVR Q2                    6,009   2,561    0.97%   2.07%    71%      7.1    1.69     1.25    [ -0.31, +1.92]    3.29  -
  FVR Q1 (flat/inv)         6,010   1,950    0.77%   1.74%    64%      4.5    1.04     0.95    [ -0.84, +2.08]    3.29  -
```

## How to read this

- A cell only counts as a finding when `t_NW` clears the hurdle AND the bootstrap interval excludes zero. The `ok` column marks those.
- The gap between `t_naive` and `t_NW` is the overlap correction. Where it is large, any past study that ran a plain t-test on daily rows was reading noise.
- A positive premium is a screen result, not a trade. It says a vol seller was paid gross. Whether a real structure keeps any of it after spreads, commissions, gamma weighting and direction risk is the stage-two path backtest's job.
- A premium near zero is the informative null: no structure over those names and that tenor can manufacture an edge, so stop building them.

## What this estimator is not

- **Vol, not variance.** It compares ATM implied vol to realized vol. An option position's P&L is linear in variance, not vol, so the mapping to dollars is not one to one. Fine for ranking and for sign, wrong for sizing.
- **ATM, not the whole smile.** A variance swap rate integrates every strike and sits above ATM implied because of the smile. The true premium is therefore a bit LARGER than what is printed here, which makes this a conservative screen.
- **No costs.** Gross of spreads, commissions and assignment. The put-spread and straddle engines already carry `lib.studies.costs`; nothing here does, by design.
- **Realized vol is close-to-close.** It ignores intraday range and overnight gaps priced separately, so it slightly understates what a gamma position actually experiences.
- **Split adjustment is correct here.** Closes are yfinance auto-adjusted, which is right for returns. The usual split-vs-strike caveat does not apply because this panel never touches a strike.

---

# Findings — first run, 2026-09-15

Universe: the 10 ETFs the calendar path study ran on, deliberately chosen so the cheap
estimator can be checked against a stage-two answer we already have. 2010-01-04 to
2026-05-01. Hurdle: Bonferroni at 50 declared trials, t >= 3.29.

## 1. The premium is real, and it lives at the short end

| tenor | mean premium | t_NW | clears t 3.29 |
|-------|--------------|------|---------------|
| 10d   | +1.75 vol pts | 8.93 | yes |
| 30d   | +0.78 vol pts | 2.08 | no |
| 90d   | +0.84 vol pts | 1.30 | no |

The 10-day result is the most robust number this repo has produced. All ten tickers clear
the hurdle individually, including GLD and TLT, which are not equity-beta names. It is
positive in **17 of 17 calendar years**, weakest in 2018 (+0.20) and 2020 (+0.51) — the two
years a vol seller expects to be hurt — and it survives every conditioning cut except
VIX > 25, where the sample thins to 483 dates and the interval widens through zero.

At 30 and 90 days there is no cell anywhere in the report that clears the hurdle. Not one
IV-percentile bucket, not one VIX regime, not one year. ⚠ **Correction 2026-09-23:** that is wrong for the 90d VIX regimes. The table above shows VIX 20–25 (t_NW 4.10) and VIX > 25 (t_NW 4.85) marked YES on the Newey-West t. On the non-overlapping t they miss (2.09 and 3.16 vs the 3.29 bar). So at 90 days the premium is supported, not certified, when VIX ≥ 20 — consistent with "sell index vol when VIX is high".

## 2. The overlap correction is the whole story at 30d

30d pooled prints t_naive 7.8 and t_NW 2.08. That is a factor of 3.75. Anything in this
repo that ran a plain t-test over daily overlapping rows was overstating its significance
by roughly that factor. The 10d finding survives the correction; the 30d one does not.

## 3. The term-structure premium is absent, and the forward-vol ratio does not sort it

Forward implied vol between day 30 and day 90, against the realized vol that then arrives
in that window: **+1.01 vol points, t_NW 1.45**. Split by forward vol ratio quartile:

| FVR quartile | premium | t_NW |
|--------------|---------|------|
| Q4 (steep)   | +0.99%  | 1.20 |
| Q3           | +0.98%  | 1.39 |
| Q2           | +0.97%  | 1.69 |
| Q1 (flat/inverted) | +0.77% | 1.04 |

Flat. The steep quartile beats the flat quartile by 0.22 vol points, which is noise.

This is the answer to research queue item #1. The oquants forward-factor claim is that a
steep forward factor marks a good calendar entry. On this universe the premium a calendar
reaches for is not measurably there at all, and the ratio that was supposed to find it does
not sort it. The calendar path study already found no *capturable* edge; this says there was
nothing to capture in the first place, which is the stronger and more useful null.

**Proposal, not applied:** close queue item #1 rather than run the replication. Cost of this
answer was one evening against the planned multi-hour Athena pull plus two simulators.

## 4. What this says about the long straddle

The best-evidenced strategy in the book is a **long** 7-DTE straddle at +4.1%/trade. This
panel says implied vol at 10 days is **rich** by 1.75 points — a vol seller is paid there.
A long straddle is on the other side of that.

These do not formally contradict. A straddle held to expiry pays on the **terminal** move,
while realized vol sums **daily** squared moves; a name can realize high vol and still finish
at the strike. But it does relocate the edge. The straddle's return is not a variance-premium
harvest, so it must come from the terminal distribution (fat tails, gaps) or from selection
by its own entry gates. That matters, because a convexity edge and a premium edge decay
differently and want different sizing.

**Worth testing next:** split the straddle's historical trades by the sign of the 10d premium
measured here. If the winners concentrate where the premium was negative, the gate is the
strategy. If they are spread evenly, the edge is convexity and the IV gate is doing less than
assumed.

## 5. The honest tension before anyone trades this

Gross premium being richest at 10 days does **not** mean short-dated selling nets the most.
Short-dated options carry small absolute premium against a bid-ask that does not shrink
proportionally, so the cost drag is worst exactly where the gross edge is best. This panel
carries no costs by design. Nothing here is tradeable until a stage-two path backtest with
`lib.studies.costs` says the net survives.

That is the correct division of labour, and it is now in place: this screen says *where to
point the expensive simulator*, and the simulator still decides what gets capital.
