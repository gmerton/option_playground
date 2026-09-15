# Calendar path study (single put calendars)

*2026-09-15. `run_calendar_path_{pull,sim,report}.py`. 5,920 calendars on 10 ETFs, Friday entries 2018-11-02 -> 2026-02-13, real daily bid/ask (options_daily_v3), house cost model (mid +/- 25% BA + $0.0065/sh/leg). ROC = P&L / entry cost. Halves split at 2022-07-01. `d_vs_hold` = paired mean difference vs holding to the short expiry.*

### DCAL structure, all names: variants

```
group    variant    n    roc    med   win      t      A      B  d_vs_hold  t_paired
  all       hold 2969 -12.33 -28.18 39.27  -5.65 -13.28 -11.39       0.00       NaN
  all       pt25 2969 -17.60  -3.52 46.78  -9.82 -19.52 -15.71      -5.27     -3.63
  all       pt50 2969 -16.32  -7.10 46.88  -8.36 -16.30 -16.34      -3.99     -3.41
  all       pt75 2969 -15.09 -20.12 43.08  -7.33 -15.02 -15.17      -2.77     -2.87
  all     stop40 2969 -21.36 -45.92 34.05 -11.26 -13.34 -29.28      -9.03     -4.88
  all     stop60 2969 -20.53 -36.06 36.98 -10.31 -12.79 -28.18      -8.20     -4.54
  all recenter1s 2969 -35.77 -40.10 34.62 -14.96 -31.50 -39.99     -23.44    -12.25
  all recenter2s 2969 -26.62 -27.67 38.70 -11.19 -25.76 -27.46     -14.29     -7.58
  all  inversion 2969 -29.30 -22.91 24.01 -15.73 -29.51 -29.09     -16.97     -9.86
```

### DCAL: by ticker

```
          n    hold    pt50  win_hold  debit  ba_pct  gap
ticker                                                   
GLD     369   -2.97   -9.16     39.57   0.46   17.82  7.0
IWM     367    9.51    4.88     47.68   0.89    9.94  7.0
QQQ     368    6.71    3.11     44.84   1.51    6.63  7.0
SPY     367    2.19    4.12     47.14   1.43    4.55  7.0
TLT     368  -15.49  -17.69     37.50   0.33   34.89  7.0
XLE      22 -372.29 -325.94      0.00   0.16  274.48  7.0
XLF     365  -22.51  -25.40     31.51   0.12   35.29  7.0
XLP     364  -28.37  -39.35     33.79   0.15   80.43  7.0
XLU      18 -227.48 -215.91      0.00   0.23  323.38  7.0
XLV     361  -15.90  -23.17     36.29   0.30   64.29  7.0
```

### DCAL: by fvf_b

```
           n   hold  hold_med    win   pt50      A      B
fvf_b                                                    
<=0.8    148   1.91    -26.39  41.89 -26.03  13.83 -14.16
0.8-0.9  329   0.81    -28.60  39.21 -12.47   1.29   0.16
0.9-1.0  736  -6.79    -27.92  40.62  -8.49  -0.57 -15.34
1.0-1.1  785 -10.99    -33.74  37.58 -12.48 -11.32 -10.68
>1.1     947 -13.35    -22.94  40.23 -15.38 -18.34 -10.12
```

### DCAL: by ivp_b

```
          n   hold  hold_med    win   pt50      A      B
ivp_b                                                   
<=30   1120 -12.90    -26.05  39.55 -16.06 -16.52 -10.52
30-60   673  -9.57    -28.69  39.67 -14.35  -4.44 -14.02
60-80   455  -7.72    -29.21  38.46  -9.56  -3.81 -11.35
>80     481   7.93    -15.38  43.24  -4.81  12.39   1.78
```

### DCAL: by regime

```
               n   hold  hold_med    win   pt50      A      B
regime                                                       
Bear_HiVIX   556  -9.71    -32.42  38.67 -13.70 -17.87  -0.06
Bear_LoVIX   248 -18.51    -40.64  32.66 -21.84 -15.88 -20.98
Bull_HiVIX   584 -16.35    -28.40  38.53 -17.65 -11.99 -25.24
Bull_LoVIX  1581 -10.80    -25.00  40.80 -15.89 -11.49 -10.30
```

### DCAL: by ba_b

```
          n   hold  hold_med    win   pt50      A      B
ba_b                                                    
<=10%   874   4.42     -9.63  46.00   3.33  -0.87   7.54
10-25%  753  -5.39    -28.73  40.37  -9.85  -3.89  -7.35
25-50%  541 -11.04    -34.97  35.86 -14.14  -4.43 -20.26
>50%    801 -38.00    -44.58  33.21 -45.31 -39.75 -36.18
```

### DCAL: by year

```
        n   hold   pt50    win
year                          
2018   72 -22.48 -12.69  31.94
2019  408 -14.70 -17.11  38.48
2020  389   0.83 -11.34  42.42
2021  412 -18.90 -16.98  39.81
2022  410 -20.01 -22.07  37.80
2023  408 -15.71 -21.46  36.52
2024  410  -6.62  -5.62  41.22
2025  400  -6.02 -16.87  40.50
2026   60 -29.81 -38.34  36.67
```

### DCAL: FVF <= 0.90 gate (the playbook gate): variants

```
group    variant   n    roc    med   win      t      A      B  d_vs_hold  t_paired
  all       hold 477   1.16 -28.18 40.04   0.23   5.15  -4.33       0.00       NaN
  all       pt25 477 -21.61 -13.64 38.16  -8.06 -17.28 -27.57     -22.77     -4.88
  all       pt50 477 -16.68  -4.49 47.38  -5.10 -13.94 -20.44     -17.83     -4.25
  all       pt75 477 -10.38  -6.30 47.59  -2.61  -7.95 -13.71     -11.53     -3.28
  all     stop40 477 -15.82 -47.60 34.59  -2.72  -2.89 -33.56     -16.97     -5.22
  all     stop60 477 -13.65 -35.83 37.74  -2.24   2.22 -35.43     -14.80     -4.58
  all recenter1s 477 -40.43 -49.15 32.08  -6.41 -21.49 -66.44     -41.59     -6.60
  all recenter2s 477 -20.14 -30.74 38.16  -3.59 -18.66 -22.18     -21.30     -4.00
  all  inversion 477 -35.80 -28.90  7.55 -15.95 -29.45 -44.52     -36.96     -7.29
```

### ETF structure, all names: variants

```
group    variant    n    roc    med   win      t      A      B  d_vs_hold  t_paired
  all       hold 2951 -14.08 -40.55 34.23  -6.83 -15.46 -12.70       0.00       NaN
  all       pt25 2951 -20.63  -8.41 43.61 -15.93 -20.61 -20.65      -6.55     -3.90
  all       pt50 2951 -17.23  -7.38 46.76 -11.31 -15.52 -18.93      -3.15     -2.12
  all       pt75 2951 -15.39 -22.44 43.21  -9.08 -15.34 -15.44      -1.31     -1.03
  all     stop40 2951 -31.42 -55.93 26.74 -15.22 -23.78 -39.00     -17.34    -10.48
  all     stop60 2951 -29.87 -54.82 30.46 -13.38 -22.53 -37.15     -15.79     -9.95
  all recenter1s 2951 -44.64 -62.16 30.06 -16.96 -37.53 -51.69     -30.57    -12.92
  all recenter2s 2951 -38.80 -46.33 33.28 -14.18 -34.79 -42.79     -24.73     -9.08
  all  inversion 2951 -34.14 -31.50 24.60 -21.90 -29.04 -39.19     -20.06    -10.12
```

### ETF: by ticker

```
          n    hold    pt50  win_hold  debit  ba_pct  gap
ticker                                                   
GLD     369   -0.66   -7.45     37.67   0.36   27.52  7.0
IWM     367   10.70    6.66     44.14   0.60   15.58  7.0
QQQ     368   -3.07    3.25     36.96   1.05   10.03  7.0
SPY     368   -2.04    1.86     38.04   1.01    7.53  7.0
TLT     369  -15.00  -23.17     32.25   0.25   51.69  7.0
XLE      24 -203.06 -187.68      0.00   0.09  470.00  7.0
XLF     365  -24.17  -30.44     29.86   0.10   52.63  7.0
XLP     361  -40.29  -47.10     26.59   0.13  103.45  7.0
XLU       6  -94.84  -89.01      0.00   0.08  784.21  7.0
XLV     354  -25.44  -30.30     30.79   0.26   86.73  7.0
```

### ETF: by fvf_b

```
           n   hold  hold_med    win   pt50      A      B
fvf_b                                                    
<=0.8    167 -16.01    -49.75  34.13 -37.20 -10.16 -22.07
0.8-0.9  364  -5.34    -37.60  36.26  -9.96  -5.40  -5.29
0.9-1.0  808  -2.01    -37.09  36.14  -8.57  -5.62   1.66
1.0-1.1  878 -17.19    -44.00  33.71 -17.98 -16.64 -17.80
>1.1     719 -22.71    -37.81  32.41 -20.78 -21.57 -23.71
```

### ETF: by ivp_b

```
          n   hold  hold_med    win   pt50      A      B
ivp_b                                                   
<=30   1071 -14.52    -39.07  33.99 -17.02 -19.04 -11.50
30-60   644 -15.72    -43.00  33.70 -19.75 -17.21 -14.42
60-80   466  -6.04    -36.24  35.62 -12.57  -5.12  -6.97
>80     540  -1.15    -33.38  37.22  -7.21   8.54 -12.73
```

### ETF: by regime

```
               n   hold  hold_med    win   pt50      A      B
regime                                                       
Bear_HiVIX   554 -15.64    -40.82  29.42 -18.51  -4.82 -28.43
Bear_LoVIX   246 -23.24    -60.47  32.11 -19.46 -21.63 -24.78
Bull_HiVIX   579  -8.85    -28.34  38.17 -13.41  -8.25 -10.04
Bull_LoVIX  1572 -14.02    -43.00  34.80 -17.84 -23.36  -7.20
```

### ETF: by ba_b

```
           n   hold  hold_med    win   pt50      A      B
ba_b                                                     
<=10%    511   4.16    -23.15  39.53   5.04  -8.26  12.01
10-25%   763  -0.12    -30.24  38.79   0.18  -2.33   2.30
25-50%   599 -15.01    -47.32  33.56 -16.42 -15.49 -14.54
>50%    1078 -32.08    -55.52  28.85 -40.57 -27.11 -37.70
```

### ETF: by year

```
        n   hold   pt50    win
year                          
2018   72 -35.71 -21.72  30.56
2019  408 -28.17 -20.84  31.62
2020  388   5.26  -6.30  38.40
2021  408 -24.41 -21.76  33.58
2022  410 -14.17 -17.19  31.22
2023  408 -20.24 -23.27  32.35
2024  407  -4.17  -5.36  34.64
2025  389  -7.56 -21.16  38.56
2026   61 -14.09 -41.12  36.07
```

### ETF: FVF <= 0.90 gate (the playbook gate): variants

```
group    variant   n    roc    med   win      t      A      B  d_vs_hold  t_paired
  all       hold 531  -8.69 -40.84 35.59  -1.67  -7.03 -10.15       0.00       NaN
  all       pt25 531 -25.79 -13.01 37.29 -10.24 -23.07 -28.18     -17.10     -3.59
  all       pt50 531 -18.53  -7.09 46.52  -5.98 -14.76 -21.82      -9.83     -2.24
  all       pt75 531 -12.69  -8.43 46.70  -3.76 -10.81 -14.34      -4.00     -0.97
  all     stop40 531 -35.13 -59.10 29.19  -5.43 -12.76 -54.72     -26.43     -5.63
  all     stop60 531 -33.05 -51.50 32.02  -4.83 -14.17 -49.59     -24.35     -5.35
  all recenter1s 531 -58.29 -72.56 25.61  -7.67 -40.42 -73.95     -49.60     -7.18
  all recenter2s 531 -31.81 -44.43 35.78  -4.20 -25.42 -37.41     -23.11     -3.24
  all  inversion 531 -44.30 -35.38  9.42 -13.83 -36.69 -50.97     -35.61     -6.26
```

## The deployable cut: SPY / QQQ / IWM with entry bid-ask <= 10% of the debit

### DCAL structure, liquid cut

```
   variant   n   roc    med   win     t     A     B  d_vs_hold  t_paired
      hold 793  5.92  -7.44 47.29  1.92 -0.96 10.13       0.00       NaN
      pt25 793  5.39  22.99 68.35  2.51 -0.03  8.71      -0.53     -0.25
      pt50 793  4.54  13.49 53.85  1.70  1.19  6.59      -1.38     -0.97
      pt75 793  4.63  -4.54 48.93  1.61 -0.73  7.91      -1.30     -1.34
    stop40 793  2.88 -21.29 42.37  1.00 -2.94  6.45      -3.04     -2.21
    stop60 793  4.06 -11.90 45.27  1.35 -3.27  8.54      -1.87     -1.88
recenter1s 793 -1.96  -8.77 46.15 -0.64 -3.04 -1.29      -7.88     -2.43
recenter2s 793  2.80  -1.57 49.18  0.88  1.12  3.83      -3.12     -0.95
 inversion 793 -2.14  -3.92 41.74 -1.22 -6.10  0.28      -8.06     -3.15
```

### DCAL liquid cut: hold by ivp_b

```
         n   hold    win      A      B
ivp_b                                 
<=30   372   5.85  51.61  -6.93  12.71
30-60  180   1.80  43.89 -11.37   8.73
60-80  139   5.91  43.88  14.09   0.56
>80     84  12.60  41.67   6.25  17.37
```

### DCAL liquid cut: hold by fvf_b

```
           n   hold    win     A      B
fvf_b                                  
<=0.9     42  16.23  45.24  0.53  26.91
0.9-1.0  138   7.56  44.20  7.14   7.92
1.0-1.1  229   9.81  44.10  3.27  13.39
>1.1     384   1.89  50.52 -7.33   7.12
```

### DCAL liquid cut: by ticker

```
          n  hold    win     A      B
ticker                               
IWM     186  9.00  48.92 -0.63  12.34
QQQ     286  6.18  45.10  2.29   8.77
SPY     321  3.91  48.29 -3.73   9.75
```

### ETF structure, liquid cut

```
   variant   n   roc    med   win     t      A     B  d_vs_hold  t_paired
      hold 503  4.82 -22.71 39.96  1.03  -7.23 12.45       0.00       NaN
      pt25 503  3.35  21.82 73.76  1.41  -0.45  5.76      -1.47     -0.37
      pt50 503  5.46  39.77 57.26  1.73  -2.82 10.70       0.64      0.18
      pt75 503  6.80  -5.82 48.31  1.78  -5.85 14.82       1.98      0.70
    stop40 503 -1.20 -44.07 32.01 -0.28  -9.75  4.21      -6.02     -2.51
    stop60 503  1.19 -30.04 36.58  0.26  -9.98  8.27      -3.63     -2.40
recenter1s 503 -8.27 -30.47 39.76 -1.64  -6.48 -9.40     -13.09     -2.71
recenter2s 503 -3.01 -16.66 43.34 -0.56 -13.37  3.55      -7.84     -1.35
 inversion 503 -3.45  -5.75 43.94 -1.40  -9.78  0.55      -8.28     -2.02
```

### ETF liquid cut: hold by ivp_b

```
         n   hold    win      A      B
ivp_b                                 
<=30   268   3.87  41.79  -4.40   8.71
30-60   99   5.42  40.40 -24.63  22.60
60-80   83   4.87  32.53 -11.33  16.68
>80     50  10.27  42.00  17.04   4.95
```

### ETF liquid cut: hold by fvf_b

```
           n   hold    win      A      B
fvf_b                                   
<=0.9     27  -2.72  25.93 -67.10   8.47
0.9-1.0   94  29.94  48.94  25.43  31.49
1.0-1.1  173  -0.24  39.31  -8.37   5.28
>1.1     209  -1.31  38.28 -12.01   7.96
```

### ETF liquid cut: by ticker

```
          n   hold    win      A      B
ticker                                 
IWM      57  13.67  40.35   1.21  20.94
QQQ     184  -1.66  38.04 -16.53   7.89
SPY     262   7.45  41.22  -2.40  13.73
```

## Conclusions (2026-09-15)

1. **Unconditional single put calendars lose after costs on the pooled ETF set** (hold −12% DCAL / −14% ETF structure,
   5,920 trades). The loss is the thin names: XLU / XLV / XLP / XLF / TLT / XLE carry entry bid-asks of 35–470% of the
   debit, and every one is deeply negative -- the same verdict as the September playbook review, now on real paths.
   XLE and XLU have single-digit trade counts (6% strike window + monthlies): ignore their rows.
2. **On the liquid names it is a small positive:** SPY / QQQ / IWM with bid-ask <= 10% of the debit (tables above).
   IWM is the best of the three in both structures, ~+10% held to the short expiry; SPY and QQQ are ~0 to +7%.
3. **Every exit rule tested is WORSE than holding to the short expiry, on paired tests** (t −2 to −13): profit takes at
   25/50/75% raise the win rate and the median and cut the mean (the 50% take the SPY dcal playbook prescribes in
   Bullish_LowIV costs ~4pp paired); stops at 40/60% of the debit cost 8–17pp; re-centering once on a 1- or 2-sigma move
   costs 14–31pp; the oquants term-structure-inversion exit costs 17–20pp. Same shape as the straddle study: on a
   defined-risk debit structure, path management only adds cost.
4. **Gates:** the FVF <= 0.90 playbook gate is ~flat (DCAL +1.2%, halves +5 / −4; ETF −5%). Own-IV percentile > 80 is
   the one lean that helps the DCAL structure (+7.9%, halves +12 / +2) but it flips in the ETF structure (+8.5 / −12.7).
   Regime (SPY trend x VIX) separates nothing. No gate clears both halves in both structures.
5. **Not yet tested:** rolling the short leg forward at expiry (the calendar as a campaign), the call side / double
   calendars, and intraday exits. Next step: the double calendar on these same paths (add the call chain pull).

## Double calendars (step 4, 2026-09-15): IWM / SPY / QQQ, 5,812 trades

Put calendar below + call calendar above, same two expiries; strike sets by the short legs' delta: sym25 (0.25/0.25), sym35 (0.35/0.35 = the SPY playbook's Bullish_LowIV cell), asym35_10 (0.35P/0.10C = its Bearish_HighIV cell). Extra variants: drop_far (when the close crosses a short strike, close the far side, hold the tested side), close_far50 (close a side at half its entry debit). Costs on all four legs.

### HOLD by ticker x structure x strike set

```
                           n   hold    med    win     t      A      B  debit     ba
ticker struct dset                                                                 
IWM    DCAL   asym35_10  327   7.98   3.70  56.57  3.68   4.69  10.98   1.35   8.82
              sym25      328   9.80   3.36  55.18  5.20   6.43  12.68   1.58   7.91
              sym35      342  15.44  12.87  62.57  5.48  12.91  17.71   1.76   8.00
       ETF    asym35_10  311  -5.13  -6.73  38.26 -2.51  -3.71  -6.40   0.97  13.33
              sym25      310  -1.29  -5.55  41.94 -0.62   3.21  -4.86   1.06  11.89
              sym35      335  25.57  17.41  64.48  8.94  22.82  28.05   1.20  12.39
QQQ    DCAL   asym35_10  302   7.45   2.59  55.30  3.25   6.65   8.30   2.26   6.12
              sym25      317  10.23   3.30  55.21  4.62   9.24  11.21   2.76   5.02
              sym35      331  14.26  13.70  60.12  4.45  14.66  13.86   3.10   5.36
       ETF    asym35_10  303   3.62   0.78  52.81  1.39   4.58   2.66   1.61   9.06
              sym25      299   7.42   2.87  54.85  3.28   7.58   7.25   1.89   7.77
              sym35      326  19.37  14.11  58.59  6.09  10.64  28.43   2.14   8.11
SPY    DCAL   asym35_10  324   7.98   2.59  54.32  3.04   3.21  12.63   2.13   3.99
              sym25      328   3.61   2.74  53.66  1.63  -1.32   8.08   2.57   3.42
              sym35      345   7.53  11.89  56.81  2.46   2.56  12.24   2.90   3.60
       ETF    asym35_10  318   7.10  -0.32  49.69  1.97   5.57   8.54   1.49   6.38
              sym25      327  11.45   3.62  55.05  4.09  10.99  11.85   1.80   5.36
              sym35      339  12.51   9.32  55.16  3.51  11.01  13.88   2.05   5.80
```

### DCAL asym35_10: variants, all three names

```
    variant   n  roc   med   win    t    A     B  d_vs_hold  t_paired
       hold 953 7.81  2.87 55.40 5.71 4.83 10.72       0.00       NaN
       pt25 953 6.39  9.12 62.75 5.89 2.93  9.75      -1.42     -1.75
       pt50 953 7.77  3.33 55.93 6.01 3.90 11.52      -0.05     -0.10
       pt75 953 7.83  2.97 55.51 5.91 4.44 11.12       0.01      0.04
     stop40 953 7.27  2.55 54.67 5.35 4.34 10.12      -0.55     -1.62
     stop60 953 7.72  2.82 55.30 5.65 4.86 10.51      -0.09     -0.73
 recenter2s 953 6.85  3.13 54.35 4.68 4.60  9.05      -0.96     -0.80
  inversion 953 1.82 -0.72 48.69 2.53 0.48  3.12      -6.00     -4.84
   drop_far 953 6.86  2.90 54.98 4.90 4.38  9.28      -0.95     -2.33
close_far50 953 5.73  3.66 55.82 3.90 2.33  9.05      -2.08     -3.66
```

### DCAL sym25: variants, all three names

```
    variant   n   roc   med   win     t     A     B  d_vs_hold  t_paired
       hold 973  7.85  3.07 54.68  6.44  4.77 10.66       0.00       NaN
       pt25 973  6.13  8.64 59.40  6.06  4.60  7.53      -1.72     -2.65
       pt50 973  7.63  3.19 54.88  6.52  4.13 10.83      -0.22     -0.70
       pt75 973  7.74  3.07 54.68  6.45  4.54 10.66      -0.11     -0.66
     stop40 973  7.31  2.84 54.37  5.97  4.44  9.93      -0.54     -2.13
     stop60 973  7.79  3.07 54.68  6.37  4.70 10.60      -0.07     -0.84
 recenter2s 973  3.15  1.91 53.75  2.51  1.31  4.84      -4.70     -4.23
  inversion 973 -0.15 -3.13 41.01 -0.23 -1.19  0.80      -8.00     -7.18
   drop_far 973  6.35  1.91 52.93  5.35  4.15  8.37      -1.50     -2.23
close_far50 973  5.52  1.91 52.52  4.34  1.81  8.90      -2.34     -3.78
```

### DCAL sym35: variants, all three names

```
    variant    n   roc   med   win     t     A     B  d_vs_hold  t_paired
       hold 1018 12.37 13.28 59.82  7.07  9.98 14.64       0.00       NaN
       pt25 1018  7.49 20.45 67.98  5.56  4.96  9.88      -4.89     -4.86
       pt50 1018 10.42 15.18 60.71  6.47  8.55 12.20      -1.95     -3.76
       pt75 1018 11.93 13.47 59.82  7.01  9.11 14.61      -0.44     -1.78
     stop40 1018 10.76  9.95 57.56  6.23  8.61 12.79      -1.62     -2.95
     stop60 1018 11.48 12.43 59.14  6.54  9.42 13.43      -0.90     -2.61
 recenter2s 1018  9.18 14.04 59.43  5.09 10.70  7.73      -3.20     -1.99
  inversion 1018 -0.27 -1.63 46.37 -0.32 -1.14  0.55     -12.65     -8.12
   drop_far 1018  6.01  2.56 52.06  4.45  3.96  7.95      -6.36     -5.53
close_far50 1018 10.61  8.17 56.97  6.41  7.95 13.13      -1.76     -3.54
```

### ETF asym35_10: variants, all three names

```
    variant   n   roc   med   win     t     A     B  d_vs_hold  t_paired
       hold 932  1.89 -2.41 46.89  1.14  2.22  1.58       0.00       NaN
       pt25 932  1.57 10.87 60.30  1.36  2.16  1.01      -0.32     -0.27
       pt50 932  1.83 -0.51 49.68  1.29  1.76  1.89      -0.06     -0.07
       pt75 932  1.84 -2.12 47.21  1.16  1.83  1.86      -0.05     -0.10
     stop40 932  1.77 -3.04 46.35  1.09  2.18  1.37      -0.12     -0.38
     stop60 932  1.98 -2.41 46.89  1.21  2.41  1.58       0.09      0.92
 recenter2s 932  2.70 -2.56 46.14  1.53  1.22  4.10       0.82      0.48
  inversion 932  0.52 -1.08 47.96  0.61  0.23  0.79      -1.37     -0.94
   drop_far 932  1.11 -2.87 46.57  0.66  0.99  1.22      -0.78     -1.94
close_far50 932 -0.39 -2.56 46.46 -0.22 -0.13 -0.63      -2.27     -3.02
```

### ETF sym25: variants, all three names

```
    variant   n  roc   med   win    t    A     B  d_vs_hold  t_paired
       hold 936 5.94  0.42 50.64 4.23 7.42  4.62       0.00       NaN
       pt25 936 4.20  7.96 59.08 4.22 5.31  3.20      -1.74     -1.76
       pt50 936 5.49  1.44 52.14 4.39 7.29  3.88      -0.45     -0.71
       pt75 936 5.41  0.54 50.85 4.09 6.62  4.33      -0.53     -1.27
     stop40 936 5.63  0.29 50.43 3.99 7.61  3.85      -0.32     -0.98
     stop60 936 5.68  0.42 50.64 3.99 7.39  4.14      -0.27     -1.36
 recenter2s 936 2.99 -2.04 47.01 1.98 2.42  3.50      -2.95     -2.08
  inversion 936 0.14 -2.99 42.41 0.20 0.56 -0.23      -5.80     -4.68
   drop_far 936 5.39 -0.18 49.89 3.80 6.72  4.20      -0.55     -0.91
close_far50 936 3.76 -0.93 48.61 2.47 5.76  1.97      -2.18     -3.20
```

### ETF sym35: variants, all three names

```
    variant    n   roc   med  win     t     A     B  d_vs_hold  t_paired
       hold 1000 19.12 14.04 59.4 10.26 14.74 23.28       0.00       NaN
       pt25 1000 10.65 19.71 73.2  9.71  9.05 12.18      -8.47     -6.01
       pt50 1000 14.95 20.67 62.8  9.99 13.23 16.59      -4.17     -4.34
       pt75 1000 17.22 15.57 60.1 10.23 13.76 20.50      -1.90     -3.00
     stop40 1000 17.53 11.05 58.1  9.44 12.59 22.22      -1.59     -2.83
     stop60 1000 18.05 13.48 58.9  9.62 13.38 22.47      -1.08     -2.48
 recenter2s 1000 15.08 14.79 60.7  7.11 14.89 15.27      -4.04     -2.08
  inversion 1000  2.86 -1.17 47.7  2.81  2.94  2.79     -16.26     -9.92
   drop_far 1000  9.37  0.07 50.2  5.74 10.02  8.75      -9.75     -7.00
close_far50 1000 15.88  7.78 56.9  8.76 12.67 18.93      -3.24     -4.22
```

### sym35: HOLD by regime (the SPY playbook cells) x structure

```
                     n   hold    med    win     t      A      B  debit     ba
struct regime                                                                
DCAL   Bear_HiVIX  170  25.61  18.04  68.82  6.18  23.80  27.65   2.87   6.24
       Bear_LoVIX   90   1.64  -0.39  50.00  0.26  -1.51   4.52   1.92   5.18
       Bull_HiVIX  196  18.08  10.69  61.73  4.61  28.44  -4.83   2.57   5.95
       Bull_LoVIX  562   8.10  13.77  58.01  3.47  -4.30  16.50   2.34   5.29
ETF    Bear_HiVIX  186  31.54  23.20  74.73  9.29  32.13  30.91   2.04  10.10
       Bear_LoVIX   82  16.33   4.14  54.88  2.35  33.11   0.35   1.29   8.50
       Bull_HiVIX  194  26.08  17.98  63.92  6.80  30.43  17.84   2.09   8.77
       Bull_LoVIX  538  12.74   6.35  53.16  4.68  -4.73  25.30   1.52   8.31
```

### asym35_10: HOLD by regime (the SPY playbook cells) x structure

```
                     n  hold    med    win     t      A      B  debit     ba
struct regime                                                               
DCAL   Bear_HiVIX  158  8.81   2.54  55.70  2.44  11.66   5.88   2.27   6.32
       Bear_LoVIX   85  7.17   4.68  60.00  1.80   1.20  12.22   1.41   5.93
       Bull_HiVIX  181  4.04   0.57  50.83  1.47   3.88   4.44   1.94   6.69
       Bull_LoVIX  529  8.91   4.23  56.14  4.68   3.55  12.78   1.71   6.06
ETF    Bear_HiVIX  167  3.84   2.71  56.89  1.61   2.15   5.44   1.59   9.72
       Bear_LoVIX   79  5.03 -10.33  36.71  0.74  13.72  -3.44   1.05  10.06
       Bull_HiVIX  181  1.46   0.03  50.83  0.46   5.82  -6.72   1.61   8.90
       Bull_LoVIX  505  0.90  -6.35  43.76  0.36  -1.84   2.92   1.09   9.32
```

### sym25: HOLD by regime (the SPY playbook cells) x structure

```
                     n  hold   med    win     t      A      B  debit    ba
struct regime                                                             
DCAL   Bear_HiVIX  152  7.28 -0.88  48.03  2.39   6.82   7.78   2.54  6.21
       Bear_LoVIX   88  5.22  2.73  54.55  1.42   2.04   8.40   1.69  5.05
       Bull_HiVIX  179  6.87  2.63  53.63  2.63   7.07   6.48   2.33  5.57
       Bull_LoVIX  554  8.75  5.50  56.86  5.18   3.35  12.35   2.07  4.95
ETF    Bear_HiVIX  156  1.13 -2.02  45.51  0.70  -0.42   2.42   1.87  8.75
       Bear_LoVIX   80  0.69 -2.93  48.75  0.17  10.75  -9.37   1.13  8.51
       Bull_HiVIX  171  3.75 -0.48  47.95  1.37   9.97  -7.47   1.84  8.05
       Bull_LoVIX  529  8.86  3.52  53.31  4.06   8.06   9.44   1.31  8.33
```

### sym35: HOLD by entry bid-ask x structure

```
                 n   hold    med    win     t      A      B  debit     ba
struct ba_b                                                              
DCAL   <=10%   845  11.29  13.22  60.47  6.06   7.56  13.86   2.66   4.91
       10-25%  161  15.97  10.55  55.90  3.21  13.68  30.40   1.38  12.24
       >25%     12  40.48  31.07  66.67  2.29  39.12  55.44   1.59  48.77
ETF    <=10%   601  18.20  15.61  59.57  7.56  10.80  22.82   2.07   6.53
       10-25%  366  21.29  13.94  59.84  6.80  19.13  24.90   1.22  13.33
       >25%     33  11.84   1.10  51.52  1.47  11.21  14.71   1.35  31.11
```

### sym35 DCAL: HOLD by year

```
        n   hold    med    win     t      A      B  debit     ba
year                                                            
2018   25  20.80   8.34  56.00  1.45  20.80    NaN   1.20  13.59
2019  139  -6.05  -8.54  47.48 -1.14  -6.05    NaN   1.04   8.48
2020  130  22.85  13.52  60.77  4.32  22.85    NaN   2.20   7.83
2021  143   7.04   7.92  57.34  1.57   7.04    NaN   2.24   6.32
2022  119  17.67  13.36  65.55  3.90  22.14  13.42   3.08   5.13
2023  152   9.26  14.54  58.55  2.30    NaN   9.26   2.90   3.22
2024  149  13.38  17.71  59.73  3.13    NaN  13.38   3.10   3.82
2025  140  20.05  19.55  68.57  4.20    NaN  20.05   4.20   4.44
2026   21  29.97  40.79  76.19  3.57    NaN  29.97   5.10   4.79
```

### sym35 ETF: HOLD by year

```
        n   hold    med    win     t      A      B  debit     ba
year                                                            
2018   25  42.16  35.73  64.00  3.42  42.16    NaN   0.98  18.05
2019  134 -11.08 -17.78  42.54 -2.07 -11.08    NaN   0.91  11.13
2020  125  24.53  10.45  62.40  4.96  24.53    NaN   1.84  10.31
2021  138  12.97   5.41  54.35  2.67  12.97    NaN   1.89   8.31
2022  142  36.25  33.18  78.87  9.96  42.34  31.12   2.24   7.50
2023  144   8.68   0.44  50.69  1.90    NaN   8.68   1.61   6.12
2024  135  26.72  17.34  60.00  4.80    NaN  26.72   1.82   7.61
2025  136  25.63  15.57  61.03  4.92    NaN  25.63   2.45   8.73
2026   21  57.37  50.22  90.48  5.52    NaN  57.37   2.98   9.23
```

## Double-calendar conclusions (2026-09-15)

1. **Symmetric 0.35-delta double calendars are the best structure tested, on all three liquid names, both
   structures, both halves, 8 of 9 years.** Held to the short expiry, after costs on four legs:

   | sym35, hold | n | ROC | win | halves | IWM | QQQ | SPY |
   |---|---|---|---|---|---|---|---|
   | 12 / 19 days | 1,018 | +12.4% (t 7.1; monthly-mean t 5.1) | 60% | +10.0 / +14.6 | +15.4 | +14.3 | +7.5 |
   | 20 / 27 days | 1,000 | +19.1% (t 10.3; monthly-mean t 6.3) | 59% | +14.7 / +23.3 | +25.6 | +19.4 | +12.5 |

   The single ATM calendar on the same names was +6% / +2%. 31 of 2,018 trades print below −100% of the debit,
   which is impossible for the structure and marks stale long-leg quotes on big-move days; winsorizing at [−100, +300]
   moves the means by +0.4pp, trimming 5% each side by −1pp. 2019 is the one negative year (−6% / −11%).
2. **The strike set matters more than anything else.** sym25 (wider) is +8% / +6%; asym35_10 (the SPY playbook's
   Bearish_HighIV structure) is +8% / +2% and negative on IWM in the long structure. The far 0.10 call adds debit and
   almost no zone.
3. **Hold to the short expiry, again.** Every variant is worse on paired tests (t −2 to −10). Profit takes lift the
   win rate to 68–73% and cost 2–8pp. Stops rarely trigger. Re-centering −3 to −4pp. Closing the far side when a
   strike is tested (`drop_far`) −6 to −10pp; closing a side at half its debit −2 to −3pp. The oquants term-structure
   inversion exit is the worst rule in the study, −13 to −16pp.
4. **Regime.** sym35 in the high-VIX regimes is the strongest cell (Bear_HiVIX +25.6 / +31.5%, 69–75% win, both halves
   +; Bull_HiVIX +18 / +26%), and it beats the playbook's asymmetric structure in the playbook's own regime
   (asym35_10 Bear_HiVIX +8.8 / +3.8%). Bull_LoVIX, the most common regime, is +8 / +13% overall but NEGATIVE in the
   first half (−4.3 / −4.7) and strongly positive in the second -- the one cell that is regime-of-the-decade dependent.
   Bear_LoVIX is weak (+1.6 / +16%, small n).
5. **Caveats.** Weekly entries with 12–27-day holds overlap, so trade-level t-stats overstate independence; the
   monthly-mean t (5.1 / 6.3, 70–75% of months positive) is the honest one. bid/ask end 2026-07-10. Not tested: the
   call-side-only calendar, unequal deltas other than 0.35/0.10, rolling at the short expiry.

**Proposed changes (NOT applied):** (a) the IWM screener entry becomes a symmetric 0.35Δ DOUBLE calendar, 20/27 days,
hold; (b) the SPY double-calendar playbook drops the 0.35P/0.10C asymmetric structure in Bearish_HighIV for 0.35/0.35,
and drops the 50% take in Bullish_LowIV for hold; (c) QQQ symmetric 0.35Δ double calendar joins as a candidate
(+14 / +19%, both halves +).

## Double calendars (2026-09-15): 60 liquid stocks from the straddle pool, 98,318 trades

Put calendar below + call calendar above, same two expiries; strike sets by the short legs' delta: sym25 (0.25/0.25), sym35 (0.35/0.35 = the SPY playbook's Bullish_LowIV cell), asym35_10 (0.35P/0.10C = its Bearish_HighIV cell). Extra variants: drop_far (when the close crosses a short strike, close the far side, hold the tested side), close_far50 (close a side at half its entry debit). Costs on all four legs.

### HOLD by earnings-in-window x structure x strike set

```
                                  n   hold    med    win      t      A      B  debit     ba
earn_in_win struct dset                                                                    
False       DCAL   asym35_10  11446 -21.00 -17.57  20.21 -25.65 -24.18 -16.76   0.87  39.52
                   sym25      13079 -17.29 -15.23  23.90 -57.89 -19.32 -14.42   1.00  34.57
                   sym35      13207  -5.87  -5.08  44.23 -15.99  -7.69  -3.23   1.14  35.29
            ETF    asym35_10  11726 -28.84 -26.22  14.71 -83.99 -33.48 -23.77   0.85  61.68
                   sym25      12671 -24.48 -21.49  19.31 -71.99 -28.23 -20.39   0.98  53.39
                   sym35      12721 -11.47 -11.03  39.17 -24.99 -14.74  -7.84   1.12  53.66
True        DCAL   asym35_10   3122 -25.12 -19.20  23.09 -18.99 -26.51 -23.31   0.92  46.34
                   sym25       3364 -20.02 -16.38  27.35 -27.84 -22.26 -16.96   1.05  40.00
                   sym35       3397  -9.06  -7.30  41.36 -11.50 -11.08  -6.29   1.18  41.86
            ETF    asym35_10   4305 -33.26 -30.11  17.47 -25.39 -35.61 -30.76   0.84  76.92
                   sym25       4618 -26.63 -25.07  21.26 -41.04 -29.48 -23.61   0.92  69.01
                   sym35       4662 -13.88 -14.62  36.68 -17.58 -16.27 -11.28   1.06  68.97
```

_Tables below EXCLUDE entries with an earnings date inside (entry, long expiry] (23468 of 98318)._

### HOLD by ticker x structure x strike set

```
                           n   hold    med    win      t       A      B  debit      ba
ticker struct dset                                                                    
AAL    DCAL   asym35_10  259 -34.32 -33.33   3.86 -26.87  -26.34 -43.71   0.21   42.42
              sym25      312 -27.61 -28.81   7.37 -22.90  -20.79 -35.78   0.25   34.15
              sym35      316 -16.66 -18.75  29.75  -7.73  -10.32 -24.33   0.30   34.12
       ETF    asym35_10  220 -46.32 -44.11   4.09 -26.30  -37.81 -56.16   0.18   66.67
              sym25      254 -38.52 -40.36   4.33 -28.65  -31.70 -46.76   0.21   56.57
              sym35      254 -26.22 -27.27  22.05 -10.57  -22.44 -30.73   0.24   53.33
AAOI   DCAL   asym35_10  129 -78.47 -74.77   0.78 -25.14  -87.80 -54.37   0.26  206.90
              sym25      168 -71.95 -67.67   1.79 -20.97  -81.54 -48.67   0.25  195.60
              sym35      172 -63.79 -62.20   3.49 -20.13  -70.20 -45.14   0.28  186.67
       ETF    asym35_10  122 -92.68 -87.85   2.46 -12.58 -107.76 -63.96   0.24  266.67
              sym25      149 -87.91 -74.54   1.34 -16.01  -98.38 -70.03   0.25  224.24
              sym35      147 -68.08 -66.02   5.44 -16.48  -75.54 -54.05   0.30  224.49
AAPL   DCAL   asym35_10  207   2.70  -2.40  47.34   1.73    2.91   2.26   1.07   10.13
              sym25      237   4.67   0.28  51.90   2.80    5.32   3.46   1.29    7.92
              sym35      232  12.44   8.18  60.34   5.43   12.92  11.47   1.47    9.87
       ETF    asym35_10  225  -1.12  -8.07  37.78  -0.60    0.43  -3.03   0.88   16.82
              sym25      239  -0.59  -4.65  40.59  -0.33    0.22  -1.51   1.08   13.02
              sym35      242   4.36  -1.03  47.93   1.90    3.63   5.28   1.27   16.30
ABBV   DCAL   asym35_10  199 -71.40 -25.57  10.55  -1.64  -95.19 -22.35   0.66   58.82
              sym25      232 -23.88 -20.71  14.66 -10.53  -28.17 -14.90   0.76   52.04
              sym35      226 -12.70 -12.85  34.96  -4.70  -19.02  -0.22   0.88   51.14
       ETF    asym35_10  199 -41.61 -37.94   7.04 -15.87  -48.76 -33.47   0.60   98.31
              sym25      223 -32.31 -30.74  11.21 -15.18  -37.07 -26.76   0.68   83.33
              sym35      222 -24.40 -22.00  31.53  -6.86  -33.47 -13.73   0.80   83.60
ADI    DCAL   asym35_10  183 -42.51 -29.62   6.56  -9.59  -58.29 -18.17   0.97   84.06
              sym25      205 -39.12 -28.43  11.22 -10.72  -52.57 -14.29   1.17   79.07
              sym35      221 -26.89 -15.90  33.48  -6.58  -41.74   0.33   1.30   82.35
       ETF    asym35_10  186 -46.77 -37.51   3.23 -15.93  -64.16 -26.99   0.90  110.66
              sym25      207 -46.11 -34.60   5.80 -13.22  -63.70 -25.76   1.07  104.76
              sym35      212 -29.89 -24.06  29.25  -7.41  -50.78  -5.60   1.25   98.15
AMAT   DCAL   asym35_10  192 -14.56 -12.18  22.92  -8.42  -20.89  -8.24   1.02   30.51
              sym25      210  -9.25  -9.99  29.05  -6.45  -13.74  -3.80   1.23   26.93
              sym35      215   1.15  -1.62  48.37   0.52   -2.34   5.56   1.38   27.16
       ETF    asym35_10  208 -23.58 -22.02  11.54 -13.13  -31.53 -14.48   0.90   52.59
              sym25      220 -17.67 -15.85  21.36 -11.83  -22.69 -11.66   1.03   45.01
              sym35      224  -8.21  -6.89  42.86  -2.93  -13.11  -2.46   1.18   43.06
AMD    DCAL   asym35_10  307  -5.67  -5.44  38.44  -4.29  -11.77   2.20   0.94   14.61
              sym25      341  -5.20  -6.02  38.12  -3.85   -9.71   1.28   1.11   11.58
              sym35      353   8.37   6.93  60.34   4.39    5.19  12.82   1.28   14.25
       ETF    asym35_10  314 -11.54 -11.63  29.30  -7.93  -19.09  -3.06   0.81   24.62
              sym25      332  -9.51 -10.02  33.13  -6.41  -16.65  -0.85   0.98   20.48
              sym35      331   3.31  -1.19  49.24   1.45   -1.31   8.76   1.12   22.22
AVGO   DCAL   asym35_10  209 -11.74 -11.76  25.84  -7.62  -17.96  -1.70   3.03   41.38
              sym25      239  -9.07  -9.87  27.62  -5.18  -15.40   2.39   3.35   40.00
              sym35      224   4.21   2.45  54.46   1.76   -3.95  20.44   3.60   42.04
       ETF    asym35_10  219 -19.91 -18.55  18.72 -10.89  -31.78  -5.26   2.58   59.26
              sym25      232 -16.27 -14.71  24.14  -8.97  -27.64  -3.44   3.10   52.44
              sym35      231  -1.62  -5.12  45.45  -0.61  -12.40  12.25   3.35   56.00
BAC    DCAL   asym35_10  194 -26.84 -28.07   8.25 -21.23  -28.05 -24.14   0.20   28.57
              sym25      224 -21.31 -23.74  13.39 -14.28  -21.22 -21.52   0.24   24.12
              sym35      222  -6.84  -9.22  36.94  -2.96   -8.52  -2.59   0.28   22.54
       ETF    asym35_10  236 -34.43 -37.94   6.36 -23.80  -36.28 -32.12   0.18   43.44
              sym25      252 -27.10 -27.51  11.11 -18.71  -28.68 -24.99   0.21   37.50
              sym35      250 -14.86 -19.45  31.60  -6.36  -15.91 -13.47   0.24   37.04
C      DCAL   asym35_10  224 -16.42 -18.58  17.86 -12.49  -16.36 -16.49   0.40   26.87
              sym25      267 -12.81 -14.93  19.85  -9.79  -13.13 -12.39   0.48   25.00
              sym35      266  -0.70  -0.52  49.25  -0.34   -2.26   1.55   0.56   24.71
       ETF    asym35_10  228 -24.78 -26.78  11.84 -15.86  -27.75 -21.30   0.32   47.62
              sym25      237 -17.95 -19.59  17.72 -11.25  -21.12 -14.11   0.38   41.38
              sym35      236  -5.62  -5.61  44.07  -2.05   -7.89  -2.88   0.45   40.00
CAT    DCAL   asym35_10  189 -11.51 -13.15  21.69  -6.46  -12.57  -9.44   1.26   37.93
              sym25      202  -9.77 -10.42  27.23  -6.34   -9.94  -9.32   1.42   32.49
              sym35      231   0.66  -0.52  48.92   0.30    2.20  -2.49   1.68   34.15
       ETF    asym35_10  210 -22.41 -22.73  11.90 -14.27  -19.97 -25.67   1.15   64.33
              sym25      226 -18.39 -17.00  16.81 -12.22  -17.23 -20.07   1.29   52.93
              sym35      226  -7.31  -5.56  43.81  -2.78   -5.70  -9.52   1.55   52.31
COHR   DCAL   asym35_10   67 -62.41 -52.72   4.48 -10.84     NaN -62.41   0.90  123.08
              sym25       80 -56.74 -45.00   8.75  -9.56     NaN -56.74   1.10   89.59
              sym35       82 -35.67 -30.68  18.29  -5.81     NaN -35.67   1.31   89.45
       ETF    asym35_10   51 -69.45 -64.19   0.00 -16.08     NaN -69.45   0.92  165.59
              sym25       68 -51.68 -53.97   4.41 -11.19     NaN -51.68   0.86  142.08
              sym35       65 -38.76 -36.80  13.85  -6.28     NaN -38.76   1.02  128.57
COST   DCAL   asym35_10  231  -8.84 -12.32  25.97  -5.20  -11.86  -4.09   1.93   39.11
              sym25      252  -5.67 -10.07  30.16  -2.97   -7.52  -2.85   2.39   35.49
              sym35      239   2.10  -1.60  49.79   0.83   -0.01   6.15   2.52   36.56
       ETF    asym35_10  240 -17.26 -19.47  21.67  -7.91  -23.15 -10.53   1.99   63.49
              sym25      258 -14.96 -16.17  21.32  -9.50  -17.78 -11.71   2.34   57.43
              sym35      254  -7.70  -7.31  42.13  -3.12  -14.21  -0.32   2.91   55.68
CRM    DCAL   asym35_10  258 -15.90 -14.04  23.64 -10.77  -18.26 -11.73   1.34   39.59
              sym25      286 -11.89 -11.75  28.67  -8.79  -13.20  -9.25   1.58   33.56
              sym35      291  -0.04  -2.03  47.42  -0.02   -1.37   2.57   1.83   35.29
       ETF    asym35_10  305 -22.46 -22.50  18.03 -13.08  -26.54 -17.38   1.20   66.67
              sym25      325 -16.51 -15.74  26.15 -10.22  -17.99 -14.58   1.38   53.11
              sym35      321  -7.00  -5.09  44.24  -3.27   -8.50  -4.93   1.67   55.07
CRWD   DCAL   asym35_10  167 -11.61 -13.72  22.75  -7.40  -19.01  -5.72   2.25   40.61
              sym25      165 -10.29 -10.44  29.70  -5.31  -18.60  -3.18   2.62   36.31
              sym35      173   0.27   1.00  52.60   0.10   -8.06   7.44   2.95   37.93
       ETF    asym35_10  164 -21.71 -20.42  14.63 -12.18  -31.36 -14.16   2.07   79.28
              sym25      181 -16.57 -15.96  22.10  -9.02  -25.49 -10.11   2.45   60.80
              sym35      176  -2.74  -3.36  46.59  -0.93   -7.65   1.09   2.74   66.12
CRWV   DCAL   asym35_10   18 -19.20 -21.38  22.22  -3.25     NaN -19.20   2.32   59.85
              sym25       20 -18.88 -23.79  25.00  -4.43     NaN -18.88   2.66   75.08
              sym35       25 -14.92 -12.17  40.00  -2.13     NaN -14.92   3.17   70.66
       ETF    asym35_10   21 -29.24 -26.35  14.29  -4.27     NaN -29.24   1.88   91.46
              sym25       21 -23.98 -23.77  14.29  -4.38     NaN -23.98   1.98  102.94
              sym35       23 -24.25 -31.16  17.39  -3.51     NaN -24.25   2.30  108.57
CSCO   DCAL   asym35_10  210 -27.12 -27.55  10.00 -19.82  -23.44 -32.12   0.25   46.15
              sym25      241 -21.58 -24.30  18.67 -14.41  -17.94 -27.49   0.30   40.00
              sym35      243  -6.07 -10.58  39.92  -2.36   -3.70  -9.51   0.34   38.20
       ETF    asym35_10  205 -40.02 -39.12   3.41 -20.72  -37.76 -42.96   0.22   70.97
              sym25      214 -30.26 -31.11   7.48 -20.01  -28.78 -32.02   0.26   58.20
              sym35      218 -18.05 -19.92  27.98  -6.09  -15.83 -20.66   0.30   61.14
CVX    DCAL   asym35_10  211 -13.40 -15.09  19.91  -9.57  -13.51 -13.21   0.71   33.63
              sym25      246  -9.78 -12.03  23.98  -6.75   -9.13 -10.79   0.85   29.26
              sym35      251  -2.24  -2.76  45.82  -1.06   -0.72  -4.86   0.97   31.45
       ETF    asym35_10  213 -21.35 -20.88  13.15 -12.16  -22.72 -19.59   0.59   55.56
              sym25      238 -16.86 -17.69  19.75 -10.51  -17.86 -15.73   0.73   46.43
              sym35      233  -1.68  -5.97  41.20  -0.65   -3.02  -0.06   0.83   48.65
DELL   DCAL   asym35_10   89 -28.53 -29.18  10.11 -12.00     NaN -28.53   1.00   81.99
              sym25      102 -25.21 -21.82  11.76  -6.49     NaN -25.21   1.23   58.23
              sym35      111  -9.69  -8.80  39.64  -2.87     NaN  -9.69   1.36   60.24
       ETF    asym35_10   72 -35.83 -35.93   9.72 -11.27     NaN -35.83   0.85  126.14
              sym25       83 -33.34 -29.07  13.25  -6.23     NaN -33.34   0.96   90.20
              sym35       86 -17.94 -19.45  36.05  -3.41     NaN -17.94   1.12   95.65
GE     DCAL   asym35_10  230 -31.85 -30.96  11.30 -18.05  -44.59 -13.43   0.52   47.23
              sym25      280 -30.17 -27.30  11.43 -18.67  -40.80 -13.48   0.52   44.23
              sym35      269 -18.33 -19.55  30.48  -8.43  -29.58   1.63   0.33   40.00
       ETF    asym35_10  221 -42.48 -44.11   5.88 -21.78  -57.43 -26.83   0.47   76.92
              sym25      247 -37.55 -38.98   9.31 -20.56  -50.49 -21.18   0.55   66.67
              sym35      247 -21.83 -24.48  27.94  -8.84  -34.48  -6.57   0.64   66.67
GEV    DCAL   asym35_10   28 -24.75 -19.94   7.14  -4.98     NaN -24.75   5.39   55.39
              sym25       29 -16.13 -15.73  13.79  -3.20     NaN -16.13   6.75   52.75
              sym35       23   0.82  -6.86  30.43   0.07     NaN   0.82   6.40   50.51
       ETF    asym35_10   38 -34.78 -31.46   0.00 -11.24     NaN -34.78   4.68  117.15
              sym25       37 -28.24 -28.13  13.51  -7.48     NaN -28.24   5.40   85.71
              sym35       37 -12.20 -16.15  35.14  -2.35     NaN -12.20   6.80   76.29
GLW    DCAL   asym35_10  226 -65.58 -60.75   2.21 -17.19  -66.79 -63.82   0.22  133.33
              sym25      288 -65.11 -53.85   3.12 -15.52  -70.88 -57.37   0.25  111.29
              sym35      288 -46.57 -43.93  11.46 -14.41  -45.16 -48.57   0.28  101.28
       ETF    asym35_10  207 -83.83 -71.49   0.48 -16.89  -84.93 -82.45   0.18  193.22
              sym25      256 -77.20 -68.31   1.95 -20.10  -73.49 -81.83   0.21  163.64
              sym35      255 -58.53 -56.49   7.84 -19.31  -53.90 -64.17   0.25  150.00
GOOG   DCAL   asym35_10  204  -5.31  -7.76  37.25  -3.68  -11.38   2.22   5.42   24.91
              sym25      228  -4.06  -5.93  35.53  -2.46   -6.91   0.23   6.85   23.65
              sym35      245   8.43   5.40  58.78   3.53    5.11  13.57   7.75   23.08
       ETF    asym35_10  230 -12.10 -14.92  24.35  -7.25  -19.41  -3.25   4.16   37.24
              sym25      235 -10.77 -10.92  26.38  -6.37  -16.55  -3.97   4.85   33.33
              sym35      243   3.34   1.03  51.44   1.37    0.38   6.93   5.80   34.48
GOOGL  DCAL   asym35_10  271  -5.20  -7.89  34.32  -4.39   -9.84   1.28   5.60   24.56
              sym25      303  -3.54  -4.65  36.96  -2.46   -6.24   0.41   6.75   20.90
              sym35      312   8.90   5.65  57.69   4.27    5.63  13.93   7.75   21.47
       ETF    asym35_10  312  -9.81 -12.12  26.60  -6.67  -16.24  -2.21   3.88   35.78
              sym25      340  -6.51  -9.10  32.94  -4.31  -10.39  -1.88   4.55   31.26
              sym35      345   7.65   4.11  55.65   3.50    4.18  11.85   5.65   33.68
GS     DCAL   asym35_10  213  -9.58 -11.63  29.11  -7.08   -8.81 -10.78   1.94   33.07
              sym25      244  -4.68  -6.73  38.93  -3.37   -5.19  -3.78   2.28   29.10
              sym35      237   4.43   2.13  54.43   2.21    3.79   5.72   2.48   32.45
       ETF    asym35_10  247 -18.42 -19.73  17.81 -12.88  -21.55 -14.77   1.71   52.32
              sym25      262 -12.41 -16.05  23.66  -8.00  -14.83  -9.42   1.99   45.11
              sym35      256  -1.55  -5.69  43.36  -0.61   -3.85   1.27   2.33   47.45
HD     DCAL   asym35_10  200 -12.30 -14.43  27.00  -6.40  -12.21 -12.50   1.49   41.55
              sym25      225  -8.27 -12.20  28.00  -4.07   -8.04  -8.77   1.80   34.44
              sym35      219   3.31   1.27  52.05   1.18    1.68   7.72   2.02   38.06
       ETF    asym35_10  228 -23.37 -25.64  12.72 -12.42  -23.10 -23.70   1.31   60.89
              sym25      234 -16.39 -17.38  23.08  -7.16  -17.47 -15.10   1.62   50.17
              sym35      241  -4.46  -6.21  44.40  -1.62   -5.57  -3.07   1.85   52.38
HOOD   DCAL   asym35_10  146 -29.84 -31.12   8.90 -15.87  -29.73 -29.87   0.26   42.64
              sym25      163 -25.33 -27.47  11.66 -13.90  -26.92 -24.92   0.30   34.48
              sym35      167 -16.23 -17.81  29.94  -6.48  -18.14 -15.75   0.36   37.50
       ETF    asym35_10  124 -39.05 -40.42   8.06 -15.91  -42.88 -38.17   0.21   73.21
              sym25      138 -37.29 -38.60   8.70 -14.37  -35.37 -37.74   0.26   60.43
              sym35      142 -24.16 -27.82  24.65  -8.09  -24.61 -24.05   0.29   60.56
HPE    DCAL   asym35_10  150 -77.48 -77.99   0.67 -25.03  -83.65 -66.53   0.12  169.80
              sym25      205 -72.36 -73.02   3.41 -23.65  -82.70 -51.54   0.13  150.00
              sym35      210 -62.09 -64.64   3.81 -21.02  -72.90 -40.48   0.15  142.86
       ETF    asym35_10  133 -94.58 -90.35   0.75 -19.51 -100.11 -82.99   0.10  226.67
              sym25      164 -83.88 -83.41   0.61 -29.84  -87.50 -76.89   0.12  193.55
              sym35      164 -89.19 -75.73   3.66  -5.59 -102.78 -59.94   0.13  170.00
IBM    DCAL   asym35_10  238 -15.35 -17.62  19.33  -8.92  -15.62 -14.93   0.67   46.31
              sym25      270 -11.96 -14.23  24.44  -7.56  -12.55 -10.93   0.77   40.00
              sym35      276  -0.88  -5.10  44.93  -0.37   -0.99  -0.72   0.91   41.40
       ETF    asym35_10  220 -26.05 -27.40  14.55 -14.44  -28.70 -22.93   0.55   74.17
              sym25      233 -19.94 -21.39  17.17 -11.01  -19.72 -20.19   0.67   60.32
              sym35      242  -7.70 -12.15  38.84  -2.72   -6.86  -8.70   0.78   63.32
INTC   DCAL   asym35_10  204 -18.46 -21.05  15.20 -12.73  -17.79 -19.46   0.30   28.57
              sym25      235 -12.67 -13.69  21.28  -9.89  -10.19 -16.39   0.36   22.86
              sym35      219  -0.63  -1.01  47.49  -0.30    1.12  -3.34   0.41   23.62
       ETF    asym35_10  204 -28.44 -28.78   6.37 -18.77  -29.62 -27.10   0.23   41.76
              sym25      222 -22.75 -22.09  13.51 -14.79  -21.71 -23.96   0.29   33.33
              sym35      227  -6.87  -4.95  43.61  -2.75    0.45 -14.94   0.33   33.85
INTU   DCAL   asym35_10  153 -28.71 -25.34   9.80 -12.37  -35.01 -21.81   3.20   69.28
              sym25      174 -25.96 -23.63  13.79 -11.88  -32.42 -17.01   3.55   67.89
              sym35      158 -15.15 -18.90  35.44  -4.92  -20.66  -7.27   4.17   72.77
       ETF    asym35_10  182 -38.80 -33.52   4.95 -18.22  -47.26 -31.71   2.84  111.49
              sym25      191 -30.79 -26.88  11.52 -13.30  -40.05 -22.88   3.40   90.20
              sym35      196 -20.56 -20.50  31.12  -6.52  -31.33 -11.22   4.00   95.76
JNJ    DCAL   asym35_10  185 -20.07 -20.91  22.16  -7.67  -19.92 -20.37   0.62   44.44
              sym25      217 -13.84 -14.98  23.96  -7.40  -12.65 -16.81   0.73   38.46
              sym35      237  -6.88  -7.07  40.51  -2.85   -2.68 -15.11   0.84   42.86
       ETF    asym35_10  220 -32.97 -33.33  16.82 -11.08  -34.55 -30.85   0.54   77.66
              sym25      241 -24.90 -26.83  19.92 -11.40  -23.63 -26.47   0.60   70.90
              sym35      239  -7.42  -9.79  38.08  -2.53   -6.22  -8.98   0.73   68.39
JPM    DCAL   asym35_10  210  -9.19 -10.74  25.24  -7.23  -10.84  -6.45   0.73   25.20
              sym25      258  -6.05  -8.14  31.40  -4.41   -6.28  -5.69   0.89   21.66
              sym35      254   4.30   3.17  53.94   2.18    4.03   4.80   1.02   23.15
       ETF    asym35_10  228 -17.06 -18.23  20.18 -10.24  -21.88 -11.20   0.69   42.45
              sym25      247 -11.02 -12.40  29.15  -7.17  -14.24  -7.07   0.78   36.89
              sym35      243   1.39  -0.70  49.38   0.58    2.03   0.60   0.89   35.29
KLAC   DCAL   asym35_10  124 -42.50 -38.03   1.61 -17.43  -51.90 -29.91   3.24  124.70
              sym25      134 -33.84 -29.23   7.46 -13.64  -40.42 -23.14   3.75   99.75
              sym35      134 -24.37 -25.60  23.13  -8.39  -29.38 -15.09   4.10   99.84
       ETF    asym35_10  127 -52.18 -45.40   0.79 -18.18  -62.30 -40.52   2.78  160.00
              sym25      136 -43.67 -38.94   5.15 -13.75  -55.11 -30.41   3.25  135.32
              sym35      132 -25.77 -25.92  22.73  -6.91  -34.01 -15.89   3.80  137.43
KO     DCAL   asym35_10  240 -34.14 -33.93   7.92 -14.73  -34.44 -33.82   0.22   53.20
              sym25      273 -25.54 -30.39  13.55 -16.81  -27.61 -23.19   0.26   45.16
              sym35      286 -14.72 -16.49  29.02  -5.61  -14.52 -14.93   0.31   45.44
       ETF    asym35_10  209 -46.05 -44.79   5.74 -15.22  -50.88 -39.91   0.17   76.92
              sym25      231 -35.21 -37.53  10.39 -17.21  -35.27 -35.13   0.21   66.67
              sym35      235 -16.63 -14.81  33.19  -5.11  -18.01 -15.06   0.25   64.29
LITE   DCAL   asym35_10  125 -55.33 -44.19   1.60 -12.15  -57.16 -40.82   0.75  123.40
              sym25      151 -52.26 -41.32   3.97 -10.20  -49.41 -80.19   0.85  113.04
              sym35      152 -38.99 -27.95  11.84  -8.24  -39.51 -33.37   0.95  107.18
       ETF    asym35_10  110 -61.26 -56.55   0.91 -15.47  -57.87 -77.50   0.62  159.02
              sym25      132 -69.92 -53.39   0.76 -14.59  -67.51 -79.76   0.74  154.70
              sym35      131 -49.85 -45.27   8.40 -10.82  -45.15 -69.78   0.82  144.83
LLY    DCAL   asym35_10  211 -35.54 -28.71  12.80  -6.65  -47.18 -20.49   1.64   90.11
              sym25      230 -31.68 -25.17  15.22 -11.42  -40.23 -18.37   1.59   77.14
              sym35      225 -22.45 -17.68  35.11  -5.74  -29.25 -10.37   1.86   73.58
       ETF    asym35_10  206 -47.76 -44.85  11.17 -16.44  -60.95 -33.23   1.53  142.78
              sym25      229 -46.57 -38.11  11.79 -11.83  -65.59 -25.25   2.18  115.38
              sym35      227 -26.98 -25.66  31.28  -6.55  -34.88 -17.11   2.23  117.07
LRCX   DCAL   asym35_10  247 -17.05 -16.08  19.84 -12.78  -20.22 -13.04   3.49   44.90
              sym25      271 -12.80 -11.88  23.62  -9.83  -14.92  -9.98   4.25   40.78
              sym35      268  -2.39  -2.11  48.13  -1.09   -3.49  -0.87   4.49   43.11
       ETF    asym35_10  246 -24.52 -24.62  14.63 -15.52  -30.01 -17.96   3.34   73.16
              sym25      256 -20.17 -19.81  16.41 -13.96  -23.12 -16.50   3.80   63.01
              sym35      261 -10.43 -10.53  38.70  -4.47  -14.98  -4.91   4.20   68.27
META   DCAL   asym35_10  219  -0.48  -3.09  39.73  -0.38   -2.57   2.24   1.94   13.73
              sym25      240   1.62   0.48  50.83   1.29    0.37   3.53   2.27   11.99
              sym35      240  11.92  10.81  66.67   5.69   11.94  11.87   2.58   13.59
       ETF    asym35_10  240  -6.34  -8.19  31.67  -4.39   -7.47  -5.08   1.69   20.72
              sym25      253  -3.66  -6.54  38.34  -2.61   -5.28  -1.87   2.04   18.71
              sym35      247   6.72   5.04  58.70   2.96    5.68   7.96   2.38   20.34
MRK    DCAL   asym35_10  250 -28.38 -25.72  10.00 -10.62  -32.21 -24.23   0.45   56.13
              sym25      296 -21.24 -20.44  17.57 -10.02  -25.62 -16.48   0.55   47.96
              sym35      300 -10.71  -6.16  43.00  -3.62  -15.23  -5.48   0.62   48.33
       ETF    asym35_10  201 -43.70 -35.12   5.47 -10.12  -48.51 -38.64   0.38  105.26
              sym25      230 -39.71 -31.81  11.74  -7.80  -49.83 -28.87   0.44   82.69
              sym35      232 -28.24 -20.85  29.31  -5.65  -35.12 -20.61   0.54   80.26
MRVL   DCAL   asym35_10  248 -25.44 -24.98  13.31 -15.00  -35.09 -12.08   0.50   44.56
              sym25      266 -20.59 -20.19  16.17 -14.44  -29.24  -9.06   0.57   40.75
              sym35      283  -8.55  -7.94  39.22  -3.60  -18.43   4.67   0.68   39.08
       ETF    asym35_10  202 -41.89 -36.91   7.92 -14.64  -57.70 -20.58   0.43   83.36
              sym25      228 -35.09 -31.18  12.72 -10.65  -51.54 -14.04   0.51   66.67
              sym35      224 -19.09 -18.02  34.38  -5.69  -32.84  -2.05   0.61   65.34
MSFT   DCAL   asym35_10  206  -6.21  -8.60  26.21  -3.90   -9.10  -0.59   1.51   17.28
              sym25      227   0.65  -4.50  39.65   0.32   -1.09   4.24   1.75   14.46
              sym35      223  10.46   8.44  60.54   3.84    8.72  14.42   2.02   17.02
       ETF    asym35_10  243 -10.05 -12.01  25.93  -7.22  -13.64  -5.42   1.34   26.87
              sym25      244  -5.40  -9.15  37.70  -3.71   -7.64  -2.71   1.65   22.66
              sym35      243   8.39   5.65  58.85   3.23    4.58  13.49   1.94   24.78
MSTR   DCAL   asym35_10  108 -18.16 -21.63  13.89  -9.72  -32.10 -13.04   7.04   65.73
              sym25      126 -19.93 -19.83  15.08 -10.86  -29.82 -15.50   8.91   57.77
              sym35      123 -11.02 -12.22  34.96  -4.16  -20.22  -7.36   9.55   61.64
       ETF    asym35_10  133 -27.21 -31.96   9.77  -8.56  -52.77 -20.40   5.15   89.36
              sym25      144 -23.89 -28.28  13.19  -9.70  -41.50 -18.02   6.55   81.09
              sym35      142 -17.56 -18.48  30.28  -6.09  -29.52 -13.94   7.46   81.68
MU     DCAL   asym35_10  234  -7.14  -8.92  27.78  -6.94  -10.93  -2.56   0.62   17.89
              sym25      270  -6.53  -7.59  30.00  -6.50   -8.29  -4.38   0.75   15.50
              sym35      267   6.93   7.03  59.18   3.61    6.88   7.00   0.84   15.38
       ETF    asym35_10  204 -10.84 -15.18  23.04  -6.72  -16.47  -4.25   0.52   31.33
              sym25      222 -10.95 -14.51  24.77  -7.34  -14.89  -6.31   0.63   25.83
              sym35      225   3.88   3.25  52.89   1.58    2.50   5.53   0.73   27.18
NBIS   DCAL   asym35_10   29 -29.90 -26.78   6.90  -6.86     NaN -29.90   1.25   80.00
              sym25       39 -27.17 -29.61  12.82  -7.67     NaN -27.17   1.45   73.68
              sym35       38 -23.98 -28.12  28.95  -5.16     NaN -23.98   1.59   72.79
       ETF    asym35_10   29 -46.21 -45.31  10.34  -9.06     NaN -46.21   1.05  160.00
              sym25       31 -37.75 -33.96   6.45  -7.65     NaN -37.75   1.30  130.43
              sym35       32 -35.76 -37.57  12.50  -5.80     NaN -35.76   1.39  120.37
NFLX   DCAL   asym35_10  220  -2.81  -5.10  40.00  -2.21   -1.70  -4.79   3.29   25.59
              sym25      257  -1.30  -3.87  39.69  -0.90   -0.32  -2.86   3.88   23.26
              sym35      248  13.05   8.41  60.89   5.31   16.84   6.17   4.55   24.22
       ETF    asym35_10  247  -7.57 -11.35  26.72  -5.21   -6.83  -8.44   2.67   36.47
              sym25      259  -3.43  -6.29  37.45  -2.10   -2.44  -4.61   3.32   34.15
              sym35      258  11.49   6.89  59.30   4.36   14.52   8.02   3.81   35.54
NOW    DCAL   asym35_10  221 -22.32 -22.59  12.22 -13.28  -26.03 -17.40   4.15   71.63
              sym25      259 -19.16 -19.32  13.13 -14.41  -20.29 -17.57   4.85   60.67
              sym35      246  -6.07  -5.05  43.09  -2.66   -8.59  -1.91   5.60   63.56
       ETF    asym35_10  227 -31.85 -31.18   8.81 -20.62  -34.71 -28.46   3.42  100.92
              sym25      243 -25.58 -25.12  11.52 -16.70  -27.45 -23.39   4.15   84.06
              sym35      237 -10.33 -10.36  36.71  -4.41   -9.69 -11.10   4.70   87.50
NVDA   DCAL   asym35_10  224   2.51  -1.69  48.66   1.89    1.41   4.04   2.14   12.92
              sym25      238   1.80  -0.97  48.32   1.31    1.56   2.13   2.47   10.58
              sym35      249  13.69  12.22  65.46   6.83   13.29  14.24   2.80   12.90
       ETF    asym35_10  228  -3.25  -6.67  35.53  -2.29   -8.93   3.77   1.81   19.43
              sym25      239  -0.89  -2.88  42.26  -0.64   -4.38   3.41   2.05   16.83
              sym35      236  11.09   7.50  60.59   4.96    8.19  14.70   2.40   20.38
PANW   DCAL   asym35_10  205 -24.38 -23.11  12.20 -15.06  -28.88 -14.67   1.74   64.29
              sym25      224 -23.06 -17.65  19.20 -10.82  -27.89 -11.97   2.06   53.41
              sym35      232  -9.80  -7.08  40.95  -3.73  -12.39  -4.47   2.40   56.80
       ETF    asym35_10  205 -34.61 -31.66   9.76 -17.63  -46.73 -19.71   1.45   94.58
              sym25      216 -24.74 -23.38  15.28 -12.37  -31.55 -15.89   1.71   78.55
              sym35      220 -13.54 -11.33  36.82  -4.77  -21.33  -3.84   1.98   77.71
PLTR   DCAL   asym35_10  159 -21.20 -20.15  15.72 -11.67  -24.12 -19.70   0.26   25.00
              sym25      186 -17.60 -18.54  16.67  -9.17  -18.92 -17.03   0.31   21.35
              sym35      185  -4.86  -8.06  40.00  -1.81   -6.85  -3.96   0.36   20.00
       ETF    asym35_10  153 -30.49 -29.09   8.50 -14.76  -35.66 -28.47   0.22   42.86
              sym25      155 -23.54 -26.04  18.71 -11.23  -28.28 -21.65   0.26   35.90
              sym35      162 -13.69 -13.76  35.19  -5.17  -21.17 -10.63   0.31   34.51
QCOM   DCAL   asym35_10  237 -14.86 -13.29  21.52  -6.91  -20.09  -8.73   0.93   27.59
              sym25      265 -10.50  -8.37  28.68  -6.79  -13.50  -6.59   1.04   23.08
              sym35      284   1.22   0.72  51.06   0.52   -1.90   5.07   1.25   25.15
       ETF    asym35_10  304 -26.13 -21.38  15.46 -14.75  -33.80 -18.05   0.82   57.81
              sym25      322 -21.06 -16.70  21.12 -10.09  -27.51 -14.03   0.96   52.42
              sym35      322  -5.46  -1.91  47.20  -2.19  -12.41   1.84   1.14   51.54
SNDK   DCAL   asym35_10    9 -20.62 -49.94  11.11  -0.66     NaN -20.62   5.00  154.00
              sym25       12 -29.27 -41.16  16.67  -2.75     NaN -29.27   5.70  108.59
              sym35       10 -27.49 -24.17  20.00  -2.72     NaN -27.49   6.87  114.51
       ETF    asym35_10   10 -58.35 -60.18   0.00  -5.20     NaN -58.35   3.65  247.88
              sym25       11 -58.62 -47.66   0.00  -4.19     NaN -58.62   5.30  131.31
              sym35       11 -30.38 -44.38   9.09  -3.62     NaN -30.38   5.65  153.28
STX    DCAL   asym35_10  242 -32.20 -31.55   9.50 -18.93  -35.47 -28.09   0.59   67.74
              sym25      276 -27.64 -25.94  11.23 -16.88  -30.70 -24.10   0.67   55.43
              sym35      293 -17.18 -14.20  32.76  -6.98  -20.38 -13.21   0.76   54.55
       ETF    asym35_10  202 -47.29 -42.63   4.46 -17.31  -49.51 -44.73   0.52  104.49
              sym25      222 -42.88 -35.99   7.21 -14.29  -45.98 -39.54   0.60   80.17
              sym35      232 -25.15 -24.50  27.16  -7.88  -28.30 -21.40   0.70   85.71
TSLA   DCAL   asym35_10  266   5.45   0.05  51.13   3.76    5.72   4.96   4.56   11.08
              sym25      282   5.89   0.53  51.06   3.62    6.49   4.53   5.84   10.94
              sym35      293  14.40  12.18  62.80   7.38   13.91  15.49   6.70   11.20
       ETF    asym35_10  333   0.07  -4.28  42.04   0.04   -1.00   1.35   3.74   16.52
              sym25      348   0.19  -1.02  47.13   0.13   -0.46   0.96   4.45   16.55
              sym35      349  13.04   8.20  59.89   5.67   11.40  15.23   5.22   16.09
UNH    DCAL   asym35_10  273 -21.32 -19.66  18.32 -10.32  -25.38 -14.52   2.07   59.50
              sym25      308 -18.68 -16.87  20.13 -11.01  -20.36 -15.57   2.49   52.40
              sym35      289  -7.07  -6.46  43.25  -3.05   -7.45  -6.21   2.70   55.78
       ETF    asym35_10  325 -32.82 -31.90   9.23 -21.99  -37.19 -27.40   1.80  103.45
              sym25      334 -28.35 -26.72  13.47 -16.68  -33.12 -22.50   2.17   77.46
              sym35      336 -13.68 -17.00  33.33  -5.61  -15.41 -11.48   2.54   80.04
V      DCAL   asym35_10  196 -10.34 -12.34  23.47  -7.29  -10.59  -9.79   1.06   32.19
              sym25      214  -4.86  -6.41  36.92  -3.39   -5.33  -3.83   1.24   26.56
              sym35      223   8.54   8.70  62.33   3.72    8.25   9.24   1.51   27.56
       ETF    asym35_10  229 -19.93 -20.69  18.34 -12.90  -22.38 -16.89   0.93   55.42
              sym25      242 -14.59 -17.84  25.62  -8.19  -15.57 -13.38   1.11   43.42
              sym35      246  -1.54  -5.88  45.53  -0.63   -2.68  -0.11   1.34   45.01
VRT    DCAL   asym35_10   55 -21.32 -18.91   5.45  -8.93     NaN -21.32   1.35   62.07
              sym25       69 -18.39 -17.27  15.94  -5.52     NaN -18.39   1.55   48.00
              sym35       74  -5.27  -7.30  40.54  -1.30     NaN  -5.27   1.76   47.17
       ETF    asym35_10   59 -36.29 -36.61   5.08 -12.65     NaN -36.29   1.12  101.89
              sym25       67 -27.69 -28.56   7.46 -10.86     NaN -27.69   1.39   78.65
              sym35       68 -15.47 -17.73  32.35  -4.08     NaN -15.47   1.52   74.92
WDC    DCAL   asym35_10  204 -24.30 -24.23  11.27 -13.30  -17.50 -32.90   0.54   52.20
              sym25      235 -23.93 -22.49  18.72  -9.89  -17.40 -32.91   0.66   45.33
              sym35      249 -12.68 -10.29  38.55  -4.62   -4.84 -23.62   0.75   44.66
       ETF    asym35_10  199 -43.40 -40.02   2.01 -18.05  -38.04 -49.04   0.45   96.91
              sym25      212 -36.79 -32.04  10.85 -11.60  -29.76 -44.52   0.52   78.79
              sym35      217 -24.95 -26.92  28.11  -8.34  -20.69 -30.11   0.62   76.92
WMT    DCAL   asym35_10  249 -11.55 -14.89  26.51  -5.28  -14.41  -7.80   0.50   31.03
              sym25      287  -7.03 -10.41  31.36  -4.31   -8.12  -5.61   0.61   26.55
              sym35      289   4.48   4.02  55.02   2.21    4.31   4.71   0.70   25.93
       ETF    asym35_10  208 -22.54 -25.39  15.87 -13.47  -28.02 -15.76   0.42   46.79
              sym25      227 -17.84 -19.88  20.26 -10.72  -18.17 -17.46   0.51   42.86
              sym35      228  -3.31  -2.61  48.25  -1.39   -3.67  -2.88   0.62   40.96
XOM    DCAL   asym35_10  244 -13.31 -16.80  20.08  -8.31  -12.38 -14.31   0.48   31.01
              sym25      296 -11.87 -13.87  22.64  -8.98  -13.18 -10.39   0.58   26.87
              sym35      297  -0.68  -3.68  46.80  -0.34   -2.04   0.86   0.67   27.37
       ETF    asym35_10  215 -25.41 -26.84  11.16 -18.36  -28.02 -22.35   0.40   48.89
              sym25      232 -18.36 -19.28  13.79 -12.48  -19.73 -16.91   0.50   42.22
              sym35      240  -4.84  -8.20  40.42  -1.95   -9.57   0.47   0.57   40.00
```

### DCAL asym35_10: variants, all three names

```
    variant     n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 11446 -21.00 -17.57 20.21 -25.65 -24.18 -16.76       0.00       NaN
       pt25 11446 -20.52 -17.32 19.96 -72.16 -23.14 -17.04       0.47      0.61
       pt50 11446 -20.04 -17.43 20.42 -65.84 -22.64 -16.58       0.95      1.25
       pt75 11446 -20.00 -17.47 20.35 -65.17 -22.63 -16.50       1.00      1.31
     stop40 11446 -21.48 -17.67 20.10 -55.56 -23.78 -18.43      -0.49     -0.63
     stop60 11446 -21.94 -17.60 20.16 -26.23 -24.80 -18.13      -0.94     -4.34
 recenter2s 11446 -25.62 -19.78 18.07 -26.87 -28.75 -21.44      -4.62     -9.40
  inversion 11446 -24.83 -20.91 13.44 -86.12 -27.18 -21.70      -3.83     -4.87
   drop_far 11446 -21.81 -18.13 19.35 -26.69 -24.97 -17.61      -0.82    -10.20
close_far50 11446 -23.10 -18.35 19.42 -27.59 -25.90 -19.37      -2.10     -9.55
```

### DCAL sym25: variants, all three names

```
    variant     n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 13079 -17.29 -15.23 23.90 -57.89 -19.32 -14.42       0.00       NaN
       pt25 13079 -18.22 -15.11 23.14 -70.76 -20.29 -15.30      -0.93     -6.46
       pt50 13079 -17.43 -15.22 24.02 -62.50 -19.36 -14.71      -0.14     -1.43
       pt75 13079 -17.25 -15.23 23.95 -60.56 -19.16 -14.55       0.04      0.45
     stop40 13079 -18.73 -15.36 23.76 -53.16 -20.73 -15.93      -1.45     -7.99
     stop60 13079 -18.30 -15.28 23.82 -52.18 -20.31 -15.46      -1.01     -5.93
 recenter2s 13079 -24.92 -19.26 20.09 -65.37 -27.51 -21.27      -7.63    -31.25
  inversion 13079 -24.98 -21.09 12.00 -91.64 -27.31 -21.72      -7.70    -30.71
   drop_far 13079 -19.94 -17.20 20.41 -66.64 -21.95 -17.11      -2.65    -16.86
close_far50 13079 -20.73 -17.24 21.86 -60.59 -22.70 -17.94      -3.44    -17.15
```

### DCAL sym35: variants, all three names

```
    variant     n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 13207  -5.87  -5.08 44.23 -15.99  -7.69  -3.23       0.00       NaN
       pt25 13207 -11.77  -6.79 40.62 -41.45 -13.52  -9.23      -5.90    -28.63
       pt50 13207  -7.78  -5.30 43.89 -23.54  -9.55  -5.20      -1.91    -13.88
       pt75 13207  -6.55  -5.11 44.16 -18.94  -8.35  -3.94      -0.68     -6.57
     stop40 13207  -8.15  -5.82 43.45 -20.59 -10.12  -5.28      -2.28    -13.11
     stop60 13207  -7.11  -5.27 44.03 -17.86  -9.13  -4.19      -1.24     -7.74
 recenter2s 13207 -16.87 -11.31 37.84 -38.13 -19.55 -12.98     -11.00    -33.00
  inversion 13207 -22.15 -20.36 20.60 -80.90 -24.37 -18.94     -16.28    -54.91
   drop_far 13207 -15.52 -13.98 29.42 -55.16 -17.24 -13.03      -9.65    -46.90
close_far50 13207  -9.44  -8.37 40.80 -25.05 -11.38  -6.63      -3.57    -24.30
```

### ETF asym35_10: variants, all three names

```
    variant     n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 11726 -28.84 -26.22 14.71 -83.99 -33.48 -23.77       0.00       NaN
       pt25 11726 -29.30 -25.85 13.07 -99.30 -33.82 -24.36      -0.46     -2.67
       pt50 11726 -28.67 -25.98 14.69 -88.87 -33.15 -23.77       0.17      1.19
       pt75 11726 -28.43 -25.99 14.97 -81.63 -33.18 -23.24       0.41      2.98
     stop40 11726 -31.43 -26.39 14.58 -64.82 -36.27 -26.15      -2.59     -7.70
     stop60 11726 -30.88 -26.33 14.62 -64.23 -35.60 -25.71      -2.04     -6.20
 recenter2s 11726 -37.27 -31.04 12.10 -81.40 -43.62 -30.33      -8.43    -30.05
  inversion 11726 -33.98 -29.31 10.50 -98.46 -38.88 -28.64      -5.15    -20.57
   drop_far 11726 -29.99 -26.97 13.70 -87.75 -34.71 -24.84      -1.16    -13.32
close_far50 11726 -33.14 -27.98 13.58 -71.06 -37.60 -28.28      -4.31    -13.23
```

### ETF sym25: variants, all three names

```
    variant     n    roc    med   win       t      A      B  d_vs_hold  t_paired
       hold 12671 -24.48 -21.49 19.31  -71.99 -28.23 -20.39       0.00       NaN
       pt25 12671 -24.77 -21.47 17.16  -49.22 -27.99 -21.25      -0.29     -0.65
       pt50 12671 -24.04 -21.43 19.13  -46.36 -27.28 -20.50       0.44      1.02
       pt75 12671 -23.86 -21.38 19.33  -45.31 -26.95 -20.50       0.61      1.45
     stop40 12671 -27.57 -21.95 19.10  -55.03 -31.68 -23.09      -3.09     -8.20
     stop60 12671 -26.61 -21.66 19.24  -53.29 -30.59 -22.28      -2.14     -5.78
 recenter2s 12671 -38.28 -30.15 14.78  -80.68 -45.16 -30.76     -13.80    -40.33
  inversion 12671 -32.70 -28.14 10.63 -107.26 -37.05 -27.96      -8.22    -32.85
   drop_far 12671 -27.20 -24.06 16.04  -85.01 -31.26 -22.76      -2.72    -18.23
close_far50 12671 -30.65 -25.83 16.06  -65.12 -34.52 -26.43      -6.17    -17.28
```

### ETF sym35: variants, all three names

```
    variant     n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 12721 -11.47 -11.03 39.17 -24.99 -14.74  -7.84       0.00       NaN
       pt25 12721 -19.36 -14.25 30.93 -53.22 -22.88 -15.43      -7.89    -29.54
       pt50 12721 -14.53 -11.73 37.79 -35.53 -18.02 -10.65      -3.06    -15.50
       pt75 12721 -12.57 -11.25 38.90 -28.96 -15.89  -8.87      -1.10     -6.94
     stop40 12721 -16.77 -13.07 37.50 -34.77 -20.58 -12.53      -5.30    -15.87
     stop60 12721 -14.27 -11.59 38.72 -27.65 -18.05 -10.06      -2.80    -11.61
 recenter2s 12721 -29.22 -22.99 30.69 -45.29 -35.43 -22.30     -17.75    -33.85
  inversion 12721 -29.62 -27.62 20.05 -72.91 -33.93 -24.82     -18.15    -52.47
   drop_far 12721 -22.43 -20.86 24.05 -68.02 -25.84 -18.63     -10.96    -40.54
close_far50 12721 -18.12 -17.51 33.42 -41.10 -21.78 -14.04      -6.65    -28.56
```

### sym35: HOLD by regime (the SPY playbook cells) x structure

```
                      n   hold    med    win      t      A      B  debit     ba
struct regime                                                                  
DCAL   Bear_HiVIX  2302 -10.95 -10.95  38.23 -11.06 -15.47  -3.82   1.30  45.52
       Bear_LoVIX  2226  -4.25  -4.16  45.78  -4.75  -4.53  -3.20   0.84  32.76
       Bull_HiVIX  2488  -8.37  -7.72  40.76 -10.29  -8.64  -7.69   1.37  41.56
       Bull_LoVIX  6191  -3.56  -2.35  47.31  -6.92  -5.21  -2.15   1.12  30.99
ETF    Bear_HiVIX  2301 -18.53 -17.03  33.38 -12.34 -24.86 -10.78   1.33  71.26
       Bear_LoVIX  2022  -8.62  -9.41  41.10  -8.18 -10.15  -3.41   0.74  46.15
       Bull_HiVIX  2201 -13.70 -13.54  35.67 -14.36 -13.88 -13.35   1.27  67.61
       Bull_LoVIX  6197  -8.99  -8.54  41.94 -15.42 -12.92  -6.44   1.15  48.28
```

### asym35_10: HOLD by regime (the SPY playbook cells) x structure

```
                      n   hold    med    win      t      A      B  debit     ba
struct regime                                                                  
DCAL   Bear_HiVIX  2030 -24.02 -21.30  17.39 -29.13 -28.87 -17.33   1.00  47.85
       Bear_LoVIX  1881 -22.02 -18.16  17.86 -23.76 -24.20 -14.97   0.62  39.25
       Bull_HiVIX  2134 -26.58 -20.66  17.34  -6.49 -29.88 -18.49   1.08  45.33
       Bull_LoVIX  5401 -17.30 -15.04  23.22 -40.30 -18.28 -16.51   0.86  34.86
ETF    Bear_HiVIX  2094 -35.33 -30.98  11.80 -37.65 -42.09 -27.37   1.02  77.80
       Bear_LoVIX  1836 -29.17 -26.84  13.02 -35.13 -32.21 -19.58   0.55  55.91
       Bull_HiVIX  2048 -32.85 -31.02  11.28 -38.46 -35.97 -27.08   1.00  76.92
       Bull_LoVIX  5748 -24.93 -22.94  17.54 -55.13 -28.49 -22.62   0.86  55.41
```

### sym25: HOLD by regime (the SPY playbook cells) x structure

```
                      n   hold    med    win      t      A      B  debit     ba
struct regime                                                                  
DCAL   Bear_HiVIX  2263 -21.96 -18.75  18.78 -25.69 -25.60 -16.50   1.16  43.64
       Bear_LoVIX  2191 -16.17 -14.86  24.97 -24.44 -16.77 -13.97   0.71  33.33
       Bull_HiVIX  2443 -20.56 -18.32  18.79 -28.36 -21.93 -17.02   1.22  40.00
       Bull_LoVIX  6182 -14.67 -12.91  27.42 -36.56 -16.21 -13.41   1.00  30.30
ETF    Bear_HiVIX  2258 -29.65 -25.26  15.63 -36.06 -34.49 -23.95   1.15  69.72
       Bear_LoVIX  2009 -22.79 -20.81  21.15 -26.09 -25.05 -15.19   0.63  47.62
       Bull_HiVIX  2184 -29.48 -27.10  13.10 -34.78 -31.42 -25.91   1.11  66.67
       Bull_LoVIX  6220 -21.39 -18.65  22.23 -45.82 -25.24 -18.92   0.99  47.19
```

### sym35: HOLD by entry bid-ask x structure

```
                   n   hold    med    win      t      A      B  debit     ba
struct ba_b                                                                 
DCAL   <=10%     747  10.19   8.66  64.12   9.25   7.74  11.99   1.50   7.85
       10-25%   3637   6.63   5.19  56.45  11.44   5.91   7.60   1.21  17.72
       >25%     8823 -12.38 -11.60  37.52 -26.29 -13.87 -10.02   1.06  50.00
ETF    <=10%     196   8.60   5.91  54.59   3.44   6.51   9.28   2.06   8.57
       10-25%   1934   7.46   5.73  56.46   8.97   6.94   7.81   1.39  18.71
       >25%    10591 -15.30 -14.80  35.73 -29.41 -17.80 -12.19   1.05  63.83
```

### sym35 DCAL: HOLD by year

```
         n   hold    med    win      t      A      B  debit     ba
year                                                              
2018  1749  -6.77  -6.77  43.05  -6.31  -6.77    NaN   0.74  40.00
2019  1864  -3.11  -2.22  47.32  -3.50  -3.11    NaN   0.81  25.53
2020  1806 -11.57 -10.24  38.10 -10.23 -11.57    NaN   1.33  49.60
2021  1723 -11.41  -8.89  39.47 -10.92 -11.41    NaN   1.34  39.32
2022  1454  -2.61  -2.25  47.80  -2.58  -2.89  -2.37   1.31  35.12
2023  1514  -1.83  -2.87  46.96  -2.05    NaN  -1.83   1.02  26.77
2024  1453  -3.05  -2.55  47.76  -2.89    NaN  -3.05   1.28  30.86
2025  1498  -4.29  -3.86  45.53  -3.70    NaN  -4.29   1.70  40.84
2026   146 -13.13 -12.65  39.04  -3.43    NaN -13.13   2.15  82.25
```

### sym35 ETF: HOLD by year

```
         n   hold    med    win      t      A      B  debit      ba
year                                                               
2018  1485 -12.71 -10.16  39.93  -5.93 -12.71    NaN   0.63   57.82
2019  1568 -11.29  -9.69  39.41 -10.76 -11.29    NaN   0.68   43.48
2020  1452 -18.43 -18.06  33.13 -12.11 -18.43    NaN   1.20   86.79
2021  1485 -18.95 -18.20  32.46 -14.60 -18.95    NaN   1.30   64.79
2022  1555  -9.75 -11.28  39.23  -9.36 -10.19  -9.38   1.37   56.00
2023  1602  -6.01  -5.50  43.51  -6.45    NaN  -6.01   0.99   40.00
2024  1677  -5.42  -4.30  45.56  -5.12    NaN  -5.42   1.29   45.00
2025  1681  -9.86 -11.42  39.68  -8.69    NaN  -9.86   1.67   56.57
2026   216 -18.38 -26.03  32.87  -4.52    NaN -18.38   2.44  102.93
```

## Double calendars (2026-09-15): 60 liquid stocks from the straddle pool, 98,318 trades

Put calendar below + call calendar above, same two expiries; strike sets by the short legs' delta: sym25 (0.25/0.25), sym35 (0.35/0.35 = the SPY playbook's Bullish_LowIV cell), asym35_10 (0.35P/0.10C = its Bearish_HighIV cell). Extra variants: drop_far (when the close crosses a short strike, close the far side, hold the tested side), close_far50 (close a side at half its entry debit). Costs on all four legs.

### HOLD by earnings-in-window x structure x strike set

```
                                  n   hold    med    win      t      A      B  debit     ba
earn_in_win struct dset                                                                    
False       DCAL   asym35_10  11446 -21.00 -17.57  20.21 -25.65 -24.18 -16.76   0.87  39.52
                   sym25      13079 -17.29 -15.23  23.90 -57.89 -19.32 -14.42   1.00  34.57
                   sym35      13207  -5.87  -5.08  44.23 -15.99  -7.69  -3.23   1.14  35.29
            ETF    asym35_10  11726 -28.84 -26.22  14.71 -83.99 -33.48 -23.77   0.85  61.68
                   sym25      12671 -24.48 -21.49  19.31 -71.99 -28.23 -20.39   0.98  53.39
                   sym35      12721 -11.47 -11.03  39.17 -24.99 -14.74  -7.84   1.12  53.66
True        DCAL   asym35_10   3122 -25.12 -19.20  23.09 -18.99 -26.51 -23.31   0.92  46.34
                   sym25       3364 -20.02 -16.38  27.35 -27.84 -22.26 -16.96   1.05  40.00
                   sym35       3397  -9.06  -7.30  41.36 -11.50 -11.08  -6.29   1.18  41.86
            ETF    asym35_10   4305 -33.26 -30.11  17.47 -25.39 -35.61 -30.76   0.84  76.92
                   sym25       4618 -26.63 -25.07  21.26 -41.04 -29.48 -23.61   0.92  69.01
                   sym35       4662 -13.88 -14.62  36.68 -17.58 -16.27 -11.28   1.06  68.97
```

_Tables below EXCLUDE entries with an earnings date inside (entry, long expiry] (23468 of 98318)._

### HOLD by ticker x structure x strike set

```
                           n   hold    med    win      t       A      B  debit      ba
ticker struct dset                                                                    
AAL    DCAL   asym35_10  259 -34.32 -33.33   3.86 -26.87  -26.34 -43.71   0.21   42.42
              sym25      312 -27.61 -28.81   7.37 -22.90  -20.79 -35.78   0.25   34.15
              sym35      316 -16.66 -18.75  29.75  -7.73  -10.32 -24.33   0.30   34.12
       ETF    asym35_10  220 -46.32 -44.11   4.09 -26.30  -37.81 -56.16   0.18   66.67
              sym25      254 -38.52 -40.36   4.33 -28.65  -31.70 -46.76   0.21   56.57
              sym35      254 -26.22 -27.27  22.05 -10.57  -22.44 -30.73   0.24   53.33
AAOI   DCAL   asym35_10  129 -78.47 -74.77   0.78 -25.14  -87.80 -54.37   0.26  206.90
              sym25      168 -71.95 -67.67   1.79 -20.97  -81.54 -48.67   0.25  195.60
              sym35      172 -63.79 -62.20   3.49 -20.13  -70.20 -45.14   0.28  186.67
       ETF    asym35_10  122 -92.68 -87.85   2.46 -12.58 -107.76 -63.96   0.24  266.67
              sym25      149 -87.91 -74.54   1.34 -16.01  -98.38 -70.03   0.25  224.24
              sym35      147 -68.08 -66.02   5.44 -16.48  -75.54 -54.05   0.30  224.49
AAPL   DCAL   asym35_10  207   2.70  -2.40  47.34   1.73    2.91   2.26   1.07   10.13
              sym25      237   4.67   0.28  51.90   2.80    5.32   3.46   1.29    7.92
              sym35      232  12.44   8.18  60.34   5.43   12.92  11.47   1.47    9.87
       ETF    asym35_10  225  -1.12  -8.07  37.78  -0.60    0.43  -3.03   0.88   16.82
              sym25      239  -0.59  -4.65  40.59  -0.33    0.22  -1.51   1.08   13.02
              sym35      242   4.36  -1.03  47.93   1.90    3.63   5.28   1.27   16.30
ABBV   DCAL   asym35_10  199 -71.40 -25.57  10.55  -1.64  -95.19 -22.35   0.66   58.82
              sym25      232 -23.88 -20.71  14.66 -10.53  -28.17 -14.90   0.76   52.04
              sym35      226 -12.70 -12.85  34.96  -4.70  -19.02  -0.22   0.88   51.14
       ETF    asym35_10  199 -41.61 -37.94   7.04 -15.87  -48.76 -33.47   0.60   98.31
              sym25      223 -32.31 -30.74  11.21 -15.18  -37.07 -26.76   0.68   83.33
              sym35      222 -24.40 -22.00  31.53  -6.86  -33.47 -13.73   0.80   83.60
ADI    DCAL   asym35_10  183 -42.51 -29.62   6.56  -9.59  -58.29 -18.17   0.97   84.06
              sym25      205 -39.12 -28.43  11.22 -10.72  -52.57 -14.29   1.17   79.07
              sym35      221 -26.89 -15.90  33.48  -6.58  -41.74   0.33   1.30   82.35
       ETF    asym35_10  186 -46.77 -37.51   3.23 -15.93  -64.16 -26.99   0.90  110.66
              sym25      207 -46.11 -34.60   5.80 -13.22  -63.70 -25.76   1.07  104.76
              sym35      212 -29.89 -24.06  29.25  -7.41  -50.78  -5.60   1.25   98.15
AMAT   DCAL   asym35_10  192 -14.56 -12.18  22.92  -8.42  -20.89  -8.24   1.02   30.51
              sym25      210  -9.25  -9.99  29.05  -6.45  -13.74  -3.80   1.23   26.93
              sym35      215   1.15  -1.62  48.37   0.52   -2.34   5.56   1.38   27.16
       ETF    asym35_10  208 -23.58 -22.02  11.54 -13.13  -31.53 -14.48   0.90   52.59
              sym25      220 -17.67 -15.85  21.36 -11.83  -22.69 -11.66   1.03   45.01
              sym35      224  -8.21  -6.89  42.86  -2.93  -13.11  -2.46   1.18   43.06
AMD    DCAL   asym35_10  307  -5.67  -5.44  38.44  -4.29  -11.77   2.20   0.94   14.61
              sym25      341  -5.20  -6.02  38.12  -3.85   -9.71   1.28   1.11   11.58
              sym35      353   8.37   6.93  60.34   4.39    5.19  12.82   1.28   14.25
       ETF    asym35_10  314 -11.54 -11.63  29.30  -7.93  -19.09  -3.06   0.81   24.62
              sym25      332  -9.51 -10.02  33.13  -6.41  -16.65  -0.85   0.98   20.48
              sym35      331   3.31  -1.19  49.24   1.45   -1.31   8.76   1.12   22.22
AVGO   DCAL   asym35_10  209 -11.74 -11.76  25.84  -7.62  -17.96  -1.70   3.03   41.38
              sym25      239  -9.07  -9.87  27.62  -5.18  -15.40   2.39   3.35   40.00
              sym35      224   4.21   2.45  54.46   1.76   -3.95  20.44   3.60   42.04
       ETF    asym35_10  219 -19.91 -18.55  18.72 -10.89  -31.78  -5.26   2.58   59.26
              sym25      232 -16.27 -14.71  24.14  -8.97  -27.64  -3.44   3.10   52.44
              sym35      231  -1.62  -5.12  45.45  -0.61  -12.40  12.25   3.35   56.00
BAC    DCAL   asym35_10  194 -26.84 -28.07   8.25 -21.23  -28.05 -24.14   0.20   28.57
              sym25      224 -21.31 -23.74  13.39 -14.28  -21.22 -21.52   0.24   24.12
              sym35      222  -6.84  -9.22  36.94  -2.96   -8.52  -2.59   0.28   22.54
       ETF    asym35_10  236 -34.43 -37.94   6.36 -23.80  -36.28 -32.12   0.18   43.44
              sym25      252 -27.10 -27.51  11.11 -18.71  -28.68 -24.99   0.21   37.50
              sym35      250 -14.86 -19.45  31.60  -6.36  -15.91 -13.47   0.24   37.04
C      DCAL   asym35_10  224 -16.42 -18.58  17.86 -12.49  -16.36 -16.49   0.40   26.87
              sym25      267 -12.81 -14.93  19.85  -9.79  -13.13 -12.39   0.48   25.00
              sym35      266  -0.70  -0.52  49.25  -0.34   -2.26   1.55   0.56   24.71
       ETF    asym35_10  228 -24.78 -26.78  11.84 -15.86  -27.75 -21.30   0.32   47.62
              sym25      237 -17.95 -19.59  17.72 -11.25  -21.12 -14.11   0.38   41.38
              sym35      236  -5.62  -5.61  44.07  -2.05   -7.89  -2.88   0.45   40.00
CAT    DCAL   asym35_10  189 -11.51 -13.15  21.69  -6.46  -12.57  -9.44   1.26   37.93
              sym25      202  -9.77 -10.42  27.23  -6.34   -9.94  -9.32   1.42   32.49
              sym35      231   0.66  -0.52  48.92   0.30    2.20  -2.49   1.68   34.15
       ETF    asym35_10  210 -22.41 -22.73  11.90 -14.27  -19.97 -25.67   1.15   64.33
              sym25      226 -18.39 -17.00  16.81 -12.22  -17.23 -20.07   1.29   52.93
              sym35      226  -7.31  -5.56  43.81  -2.78   -5.70  -9.52   1.55   52.31
COHR   DCAL   asym35_10   67 -62.41 -52.72   4.48 -10.84     NaN -62.41   0.90  123.08
              sym25       80 -56.74 -45.00   8.75  -9.56     NaN -56.74   1.10   89.59
              sym35       82 -35.67 -30.68  18.29  -5.81     NaN -35.67   1.31   89.45
       ETF    asym35_10   51 -69.45 -64.19   0.00 -16.08     NaN -69.45   0.92  165.59
              sym25       68 -51.68 -53.97   4.41 -11.19     NaN -51.68   0.86  142.08
              sym35       65 -38.76 -36.80  13.85  -6.28     NaN -38.76   1.02  128.57
COST   DCAL   asym35_10  231  -8.84 -12.32  25.97  -5.20  -11.86  -4.09   1.93   39.11
              sym25      252  -5.67 -10.07  30.16  -2.97   -7.52  -2.85   2.39   35.49
              sym35      239   2.10  -1.60  49.79   0.83   -0.01   6.15   2.52   36.56
       ETF    asym35_10  240 -17.26 -19.47  21.67  -7.91  -23.15 -10.53   1.99   63.49
              sym25      258 -14.96 -16.17  21.32  -9.50  -17.78 -11.71   2.34   57.43
              sym35      254  -7.70  -7.31  42.13  -3.12  -14.21  -0.32   2.91   55.68
CRM    DCAL   asym35_10  258 -15.90 -14.04  23.64 -10.77  -18.26 -11.73   1.34   39.59
              sym25      286 -11.89 -11.75  28.67  -8.79  -13.20  -9.25   1.58   33.56
              sym35      291  -0.04  -2.03  47.42  -0.02   -1.37   2.57   1.83   35.29
       ETF    asym35_10  305 -22.46 -22.50  18.03 -13.08  -26.54 -17.38   1.20   66.67
              sym25      325 -16.51 -15.74  26.15 -10.22  -17.99 -14.58   1.38   53.11
              sym35      321  -7.00  -5.09  44.24  -3.27   -8.50  -4.93   1.67   55.07
CRWD   DCAL   asym35_10  167 -11.61 -13.72  22.75  -7.40  -19.01  -5.72   2.25   40.61
              sym25      165 -10.29 -10.44  29.70  -5.31  -18.60  -3.18   2.62   36.31
              sym35      173   0.27   1.00  52.60   0.10   -8.06   7.44   2.95   37.93
       ETF    asym35_10  164 -21.71 -20.42  14.63 -12.18  -31.36 -14.16   2.07   79.28
              sym25      181 -16.57 -15.96  22.10  -9.02  -25.49 -10.11   2.45   60.80
              sym35      176  -2.74  -3.36  46.59  -0.93   -7.65   1.09   2.74   66.12
CRWV   DCAL   asym35_10   18 -19.20 -21.38  22.22  -3.25     NaN -19.20   2.32   59.85
              sym25       20 -18.88 -23.79  25.00  -4.43     NaN -18.88   2.66   75.08
              sym35       25 -14.92 -12.17  40.00  -2.13     NaN -14.92   3.17   70.66
       ETF    asym35_10   21 -29.24 -26.35  14.29  -4.27     NaN -29.24   1.88   91.46
              sym25       21 -23.98 -23.77  14.29  -4.38     NaN -23.98   1.98  102.94
              sym35       23 -24.25 -31.16  17.39  -3.51     NaN -24.25   2.30  108.57
CSCO   DCAL   asym35_10  210 -27.12 -27.55  10.00 -19.82  -23.44 -32.12   0.25   46.15
              sym25      241 -21.58 -24.30  18.67 -14.41  -17.94 -27.49   0.30   40.00
              sym35      243  -6.07 -10.58  39.92  -2.36   -3.70  -9.51   0.34   38.20
       ETF    asym35_10  205 -40.02 -39.12   3.41 -20.72  -37.76 -42.96   0.22   70.97
              sym25      214 -30.26 -31.11   7.48 -20.01  -28.78 -32.02   0.26   58.20
              sym35      218 -18.05 -19.92  27.98  -6.09  -15.83 -20.66   0.30   61.14
CVX    DCAL   asym35_10  211 -13.40 -15.09  19.91  -9.57  -13.51 -13.21   0.71   33.63
              sym25      246  -9.78 -12.03  23.98  -6.75   -9.13 -10.79   0.85   29.26
              sym35      251  -2.24  -2.76  45.82  -1.06   -0.72  -4.86   0.97   31.45
       ETF    asym35_10  213 -21.35 -20.88  13.15 -12.16  -22.72 -19.59   0.59   55.56
              sym25      238 -16.86 -17.69  19.75 -10.51  -17.86 -15.73   0.73   46.43
              sym35      233  -1.68  -5.97  41.20  -0.65   -3.02  -0.06   0.83   48.65
DELL   DCAL   asym35_10   89 -28.53 -29.18  10.11 -12.00     NaN -28.53   1.00   81.99
              sym25      102 -25.21 -21.82  11.76  -6.49     NaN -25.21   1.23   58.23
              sym35      111  -9.69  -8.80  39.64  -2.87     NaN  -9.69   1.36   60.24
       ETF    asym35_10   72 -35.83 -35.93   9.72 -11.27     NaN -35.83   0.85  126.14
              sym25       83 -33.34 -29.07  13.25  -6.23     NaN -33.34   0.96   90.20
              sym35       86 -17.94 -19.45  36.05  -3.41     NaN -17.94   1.12   95.65
GE     DCAL   asym35_10  230 -31.85 -30.96  11.30 -18.05  -44.59 -13.43   0.52   47.23
              sym25      280 -30.17 -27.30  11.43 -18.67  -40.80 -13.48   0.52   44.23
              sym35      269 -18.33 -19.55  30.48  -8.43  -29.58   1.63   0.33   40.00
       ETF    asym35_10  221 -42.48 -44.11   5.88 -21.78  -57.43 -26.83   0.47   76.92
              sym25      247 -37.55 -38.98   9.31 -20.56  -50.49 -21.18   0.55   66.67
              sym35      247 -21.83 -24.48  27.94  -8.84  -34.48  -6.57   0.64   66.67
GEV    DCAL   asym35_10   28 -24.75 -19.94   7.14  -4.98     NaN -24.75   5.39   55.39
              sym25       29 -16.13 -15.73  13.79  -3.20     NaN -16.13   6.75   52.75
              sym35       23   0.82  -6.86  30.43   0.07     NaN   0.82   6.40   50.51
       ETF    asym35_10   38 -34.78 -31.46   0.00 -11.24     NaN -34.78   4.68  117.15
              sym25       37 -28.24 -28.13  13.51  -7.48     NaN -28.24   5.40   85.71
              sym35       37 -12.20 -16.15  35.14  -2.35     NaN -12.20   6.80   76.29
GLW    DCAL   asym35_10  226 -65.58 -60.75   2.21 -17.19  -66.79 -63.82   0.22  133.33
              sym25      288 -65.11 -53.85   3.12 -15.52  -70.88 -57.37   0.25  111.29
              sym35      288 -46.57 -43.93  11.46 -14.41  -45.16 -48.57   0.28  101.28
       ETF    asym35_10  207 -83.83 -71.49   0.48 -16.89  -84.93 -82.45   0.18  193.22
              sym25      256 -77.20 -68.31   1.95 -20.10  -73.49 -81.83   0.21  163.64
              sym35      255 -58.53 -56.49   7.84 -19.31  -53.90 -64.17   0.25  150.00
GOOG   DCAL   asym35_10  204  -5.31  -7.76  37.25  -3.68  -11.38   2.22   5.42   24.91
              sym25      228  -4.06  -5.93  35.53  -2.46   -6.91   0.23   6.85   23.65
              sym35      245   8.43   5.40  58.78   3.53    5.11  13.57   7.75   23.08
       ETF    asym35_10  230 -12.10 -14.92  24.35  -7.25  -19.41  -3.25   4.16   37.24
              sym25      235 -10.77 -10.92  26.38  -6.37  -16.55  -3.97   4.85   33.33
              sym35      243   3.34   1.03  51.44   1.37    0.38   6.93   5.80   34.48
GOOGL  DCAL   asym35_10  271  -5.20  -7.89  34.32  -4.39   -9.84   1.28   5.60   24.56
              sym25      303  -3.54  -4.65  36.96  -2.46   -6.24   0.41   6.75   20.90
              sym35      312   8.90   5.65  57.69   4.27    5.63  13.93   7.75   21.47
       ETF    asym35_10  312  -9.81 -12.12  26.60  -6.67  -16.24  -2.21   3.88   35.78
              sym25      340  -6.51  -9.10  32.94  -4.31  -10.39  -1.88   4.55   31.26
              sym35      345   7.65   4.11  55.65   3.50    4.18  11.85   5.65   33.68
GS     DCAL   asym35_10  213  -9.58 -11.63  29.11  -7.08   -8.81 -10.78   1.94   33.07
              sym25      244  -4.68  -6.73  38.93  -3.37   -5.19  -3.78   2.28   29.10
              sym35      237   4.43   2.13  54.43   2.21    3.79   5.72   2.48   32.45
       ETF    asym35_10  247 -18.42 -19.73  17.81 -12.88  -21.55 -14.77   1.71   52.32
              sym25      262 -12.41 -16.05  23.66  -8.00  -14.83  -9.42   1.99   45.11
              sym35      256  -1.55  -5.69  43.36  -0.61   -3.85   1.27   2.33   47.45
HD     DCAL   asym35_10  200 -12.30 -14.43  27.00  -6.40  -12.21 -12.50   1.49   41.55
              sym25      225  -8.27 -12.20  28.00  -4.07   -8.04  -8.77   1.80   34.44
              sym35      219   3.31   1.27  52.05   1.18    1.68   7.72   2.02   38.06
       ETF    asym35_10  228 -23.37 -25.64  12.72 -12.42  -23.10 -23.70   1.31   60.89
              sym25      234 -16.39 -17.38  23.08  -7.16  -17.47 -15.10   1.62   50.17
              sym35      241  -4.46  -6.21  44.40  -1.62   -5.57  -3.07   1.85   52.38
HOOD   DCAL   asym35_10  146 -29.84 -31.12   8.90 -15.87  -29.73 -29.87   0.26   42.64
              sym25      163 -25.33 -27.47  11.66 -13.90  -26.92 -24.92   0.30   34.48
              sym35      167 -16.23 -17.81  29.94  -6.48  -18.14 -15.75   0.36   37.50
       ETF    asym35_10  124 -39.05 -40.42   8.06 -15.91  -42.88 -38.17   0.21   73.21
              sym25      138 -37.29 -38.60   8.70 -14.37  -35.37 -37.74   0.26   60.43
              sym35      142 -24.16 -27.82  24.65  -8.09  -24.61 -24.05   0.29   60.56
HPE    DCAL   asym35_10  150 -77.48 -77.99   0.67 -25.03  -83.65 -66.53   0.12  169.80
              sym25      205 -72.36 -73.02   3.41 -23.65  -82.70 -51.54   0.13  150.00
              sym35      210 -62.09 -64.64   3.81 -21.02  -72.90 -40.48   0.15  142.86
       ETF    asym35_10  133 -94.58 -90.35   0.75 -19.51 -100.11 -82.99   0.10  226.67
              sym25      164 -83.88 -83.41   0.61 -29.84  -87.50 -76.89   0.12  193.55
              sym35      164 -89.19 -75.73   3.66  -5.59 -102.78 -59.94   0.13  170.00
IBM    DCAL   asym35_10  238 -15.35 -17.62  19.33  -8.92  -15.62 -14.93   0.67   46.31
              sym25      270 -11.96 -14.23  24.44  -7.56  -12.55 -10.93   0.77   40.00
              sym35      276  -0.88  -5.10  44.93  -0.37   -0.99  -0.72   0.91   41.40
       ETF    asym35_10  220 -26.05 -27.40  14.55 -14.44  -28.70 -22.93   0.55   74.17
              sym25      233 -19.94 -21.39  17.17 -11.01  -19.72 -20.19   0.67   60.32
              sym35      242  -7.70 -12.15  38.84  -2.72   -6.86  -8.70   0.78   63.32
INTC   DCAL   asym35_10  204 -18.46 -21.05  15.20 -12.73  -17.79 -19.46   0.30   28.57
              sym25      235 -12.67 -13.69  21.28  -9.89  -10.19 -16.39   0.36   22.86
              sym35      219  -0.63  -1.01  47.49  -0.30    1.12  -3.34   0.41   23.62
       ETF    asym35_10  204 -28.44 -28.78   6.37 -18.77  -29.62 -27.10   0.23   41.76
              sym25      222 -22.75 -22.09  13.51 -14.79  -21.71 -23.96   0.29   33.33
              sym35      227  -6.87  -4.95  43.61  -2.75    0.45 -14.94   0.33   33.85
INTU   DCAL   asym35_10  153 -28.71 -25.34   9.80 -12.37  -35.01 -21.81   3.20   69.28
              sym25      174 -25.96 -23.63  13.79 -11.88  -32.42 -17.01   3.55   67.89
              sym35      158 -15.15 -18.90  35.44  -4.92  -20.66  -7.27   4.17   72.77
       ETF    asym35_10  182 -38.80 -33.52   4.95 -18.22  -47.26 -31.71   2.84  111.49
              sym25      191 -30.79 -26.88  11.52 -13.30  -40.05 -22.88   3.40   90.20
              sym35      196 -20.56 -20.50  31.12  -6.52  -31.33 -11.22   4.00   95.76
JNJ    DCAL   asym35_10  185 -20.07 -20.91  22.16  -7.67  -19.92 -20.37   0.62   44.44
              sym25      217 -13.84 -14.98  23.96  -7.40  -12.65 -16.81   0.73   38.46
              sym35      237  -6.88  -7.07  40.51  -2.85   -2.68 -15.11   0.84   42.86
       ETF    asym35_10  220 -32.97 -33.33  16.82 -11.08  -34.55 -30.85   0.54   77.66
              sym25      241 -24.90 -26.83  19.92 -11.40  -23.63 -26.47   0.60   70.90
              sym35      239  -7.42  -9.79  38.08  -2.53   -6.22  -8.98   0.73   68.39
JPM    DCAL   asym35_10  210  -9.19 -10.74  25.24  -7.23  -10.84  -6.45   0.73   25.20
              sym25      258  -6.05  -8.14  31.40  -4.41   -6.28  -5.69   0.89   21.66
              sym35      254   4.30   3.17  53.94   2.18    4.03   4.80   1.02   23.15
       ETF    asym35_10  228 -17.06 -18.23  20.18 -10.24  -21.88 -11.20   0.69   42.45
              sym25      247 -11.02 -12.40  29.15  -7.17  -14.24  -7.07   0.78   36.89
              sym35      243   1.39  -0.70  49.38   0.58    2.03   0.60   0.89   35.29
KLAC   DCAL   asym35_10  124 -42.50 -38.03   1.61 -17.43  -51.90 -29.91   3.24  124.70
              sym25      134 -33.84 -29.23   7.46 -13.64  -40.42 -23.14   3.75   99.75
              sym35      134 -24.37 -25.60  23.13  -8.39  -29.38 -15.09   4.10   99.84
       ETF    asym35_10  127 -52.18 -45.40   0.79 -18.18  -62.30 -40.52   2.78  160.00
              sym25      136 -43.67 -38.94   5.15 -13.75  -55.11 -30.41   3.25  135.32
              sym35      132 -25.77 -25.92  22.73  -6.91  -34.01 -15.89   3.80  137.43
KO     DCAL   asym35_10  240 -34.14 -33.93   7.92 -14.73  -34.44 -33.82   0.22   53.20
              sym25      273 -25.54 -30.39  13.55 -16.81  -27.61 -23.19   0.26   45.16
              sym35      286 -14.72 -16.49  29.02  -5.61  -14.52 -14.93   0.31   45.44
       ETF    asym35_10  209 -46.05 -44.79   5.74 -15.22  -50.88 -39.91   0.17   76.92
              sym25      231 -35.21 -37.53  10.39 -17.21  -35.27 -35.13   0.21   66.67
              sym35      235 -16.63 -14.81  33.19  -5.11  -18.01 -15.06   0.25   64.29
LITE   DCAL   asym35_10  125 -55.33 -44.19   1.60 -12.15  -57.16 -40.82   0.75  123.40
              sym25      151 -52.26 -41.32   3.97 -10.20  -49.41 -80.19   0.85  113.04
              sym35      152 -38.99 -27.95  11.84  -8.24  -39.51 -33.37   0.95  107.18
       ETF    asym35_10  110 -61.26 -56.55   0.91 -15.47  -57.87 -77.50   0.62  159.02
              sym25      132 -69.92 -53.39   0.76 -14.59  -67.51 -79.76   0.74  154.70
              sym35      131 -49.85 -45.27   8.40 -10.82  -45.15 -69.78   0.82  144.83
LLY    DCAL   asym35_10  211 -35.54 -28.71  12.80  -6.65  -47.18 -20.49   1.64   90.11
              sym25      230 -31.68 -25.17  15.22 -11.42  -40.23 -18.37   1.59   77.14
              sym35      225 -22.45 -17.68  35.11  -5.74  -29.25 -10.37   1.86   73.58
       ETF    asym35_10  206 -47.76 -44.85  11.17 -16.44  -60.95 -33.23   1.53  142.78
              sym25      229 -46.57 -38.11  11.79 -11.83  -65.59 -25.25   2.18  115.38
              sym35      227 -26.98 -25.66  31.28  -6.55  -34.88 -17.11   2.23  117.07
LRCX   DCAL   asym35_10  247 -17.05 -16.08  19.84 -12.78  -20.22 -13.04   3.49   44.90
              sym25      271 -12.80 -11.88  23.62  -9.83  -14.92  -9.98   4.25   40.78
              sym35      268  -2.39  -2.11  48.13  -1.09   -3.49  -0.87   4.49   43.11
       ETF    asym35_10  246 -24.52 -24.62  14.63 -15.52  -30.01 -17.96   3.34   73.16
              sym25      256 -20.17 -19.81  16.41 -13.96  -23.12 -16.50   3.80   63.01
              sym35      261 -10.43 -10.53  38.70  -4.47  -14.98  -4.91   4.20   68.27
META   DCAL   asym35_10  219  -0.48  -3.09  39.73  -0.38   -2.57   2.24   1.94   13.73
              sym25      240   1.62   0.48  50.83   1.29    0.37   3.53   2.27   11.99
              sym35      240  11.92  10.81  66.67   5.69   11.94  11.87   2.58   13.59
       ETF    asym35_10  240  -6.34  -8.19  31.67  -4.39   -7.47  -5.08   1.69   20.72
              sym25      253  -3.66  -6.54  38.34  -2.61   -5.28  -1.87   2.04   18.71
              sym35      247   6.72   5.04  58.70   2.96    5.68   7.96   2.38   20.34
MRK    DCAL   asym35_10  250 -28.38 -25.72  10.00 -10.62  -32.21 -24.23   0.45   56.13
              sym25      296 -21.24 -20.44  17.57 -10.02  -25.62 -16.48   0.55   47.96
              sym35      300 -10.71  -6.16  43.00  -3.62  -15.23  -5.48   0.62   48.33
       ETF    asym35_10  201 -43.70 -35.12   5.47 -10.12  -48.51 -38.64   0.38  105.26
              sym25      230 -39.71 -31.81  11.74  -7.80  -49.83 -28.87   0.44   82.69
              sym35      232 -28.24 -20.85  29.31  -5.65  -35.12 -20.61   0.54   80.26
MRVL   DCAL   asym35_10  248 -25.44 -24.98  13.31 -15.00  -35.09 -12.08   0.50   44.56
              sym25      266 -20.59 -20.19  16.17 -14.44  -29.24  -9.06   0.57   40.75
              sym35      283  -8.55  -7.94  39.22  -3.60  -18.43   4.67   0.68   39.08
       ETF    asym35_10  202 -41.89 -36.91   7.92 -14.64  -57.70 -20.58   0.43   83.36
              sym25      228 -35.09 -31.18  12.72 -10.65  -51.54 -14.04   0.51   66.67
              sym35      224 -19.09 -18.02  34.38  -5.69  -32.84  -2.05   0.61   65.34
MSFT   DCAL   asym35_10  206  -6.21  -8.60  26.21  -3.90   -9.10  -0.59   1.51   17.28
              sym25      227   0.65  -4.50  39.65   0.32   -1.09   4.24   1.75   14.46
              sym35      223  10.46   8.44  60.54   3.84    8.72  14.42   2.02   17.02
       ETF    asym35_10  243 -10.05 -12.01  25.93  -7.22  -13.64  -5.42   1.34   26.87
              sym25      244  -5.40  -9.15  37.70  -3.71   -7.64  -2.71   1.65   22.66
              sym35      243   8.39   5.65  58.85   3.23    4.58  13.49   1.94   24.78
MSTR   DCAL   asym35_10  108 -18.16 -21.63  13.89  -9.72  -32.10 -13.04   7.04   65.73
              sym25      126 -19.93 -19.83  15.08 -10.86  -29.82 -15.50   8.91   57.77
              sym35      123 -11.02 -12.22  34.96  -4.16  -20.22  -7.36   9.55   61.64
       ETF    asym35_10  133 -27.21 -31.96   9.77  -8.56  -52.77 -20.40   5.15   89.36
              sym25      144 -23.89 -28.28  13.19  -9.70  -41.50 -18.02   6.55   81.09
              sym35      142 -17.56 -18.48  30.28  -6.09  -29.52 -13.94   7.46   81.68
MU     DCAL   asym35_10  234  -7.14  -8.92  27.78  -6.94  -10.93  -2.56   0.62   17.89
              sym25      270  -6.53  -7.59  30.00  -6.50   -8.29  -4.38   0.75   15.50
              sym35      267   6.93   7.03  59.18   3.61    6.88   7.00   0.84   15.38
       ETF    asym35_10  204 -10.84 -15.18  23.04  -6.72  -16.47  -4.25   0.52   31.33
              sym25      222 -10.95 -14.51  24.77  -7.34  -14.89  -6.31   0.63   25.83
              sym35      225   3.88   3.25  52.89   1.58    2.50   5.53   0.73   27.18
NBIS   DCAL   asym35_10   29 -29.90 -26.78   6.90  -6.86     NaN -29.90   1.25   80.00
              sym25       39 -27.17 -29.61  12.82  -7.67     NaN -27.17   1.45   73.68
              sym35       38 -23.98 -28.12  28.95  -5.16     NaN -23.98   1.59   72.79
       ETF    asym35_10   29 -46.21 -45.31  10.34  -9.06     NaN -46.21   1.05  160.00
              sym25       31 -37.75 -33.96   6.45  -7.65     NaN -37.75   1.30  130.43
              sym35       32 -35.76 -37.57  12.50  -5.80     NaN -35.76   1.39  120.37
NFLX   DCAL   asym35_10  220  -2.81  -5.10  40.00  -2.21   -1.70  -4.79   3.29   25.59
              sym25      257  -1.30  -3.87  39.69  -0.90   -0.32  -2.86   3.88   23.26
              sym35      248  13.05   8.41  60.89   5.31   16.84   6.17   4.55   24.22
       ETF    asym35_10  247  -7.57 -11.35  26.72  -5.21   -6.83  -8.44   2.67   36.47
              sym25      259  -3.43  -6.29  37.45  -2.10   -2.44  -4.61   3.32   34.15
              sym35      258  11.49   6.89  59.30   4.36   14.52   8.02   3.81   35.54
NOW    DCAL   asym35_10  221 -22.32 -22.59  12.22 -13.28  -26.03 -17.40   4.15   71.63
              sym25      259 -19.16 -19.32  13.13 -14.41  -20.29 -17.57   4.85   60.67
              sym35      246  -6.07  -5.05  43.09  -2.66   -8.59  -1.91   5.60   63.56
       ETF    asym35_10  227 -31.85 -31.18   8.81 -20.62  -34.71 -28.46   3.42  100.92
              sym25      243 -25.58 -25.12  11.52 -16.70  -27.45 -23.39   4.15   84.06
              sym35      237 -10.33 -10.36  36.71  -4.41   -9.69 -11.10   4.70   87.50
NVDA   DCAL   asym35_10  224   2.51  -1.69  48.66   1.89    1.41   4.04   2.14   12.92
              sym25      238   1.80  -0.97  48.32   1.31    1.56   2.13   2.47   10.58
              sym35      249  13.69  12.22  65.46   6.83   13.29  14.24   2.80   12.90
       ETF    asym35_10  228  -3.25  -6.67  35.53  -2.29   -8.93   3.77   1.81   19.43
              sym25      239  -0.89  -2.88  42.26  -0.64   -4.38   3.41   2.05   16.83
              sym35      236  11.09   7.50  60.59   4.96    8.19  14.70   2.40   20.38
PANW   DCAL   asym35_10  205 -24.38 -23.11  12.20 -15.06  -28.88 -14.67   1.74   64.29
              sym25      224 -23.06 -17.65  19.20 -10.82  -27.89 -11.97   2.06   53.41
              sym35      232  -9.80  -7.08  40.95  -3.73  -12.39  -4.47   2.40   56.80
       ETF    asym35_10  205 -34.61 -31.66   9.76 -17.63  -46.73 -19.71   1.45   94.58
              sym25      216 -24.74 -23.38  15.28 -12.37  -31.55 -15.89   1.71   78.55
              sym35      220 -13.54 -11.33  36.82  -4.77  -21.33  -3.84   1.98   77.71
PLTR   DCAL   asym35_10  159 -21.20 -20.15  15.72 -11.67  -24.12 -19.70   0.26   25.00
              sym25      186 -17.60 -18.54  16.67  -9.17  -18.92 -17.03   0.31   21.35
              sym35      185  -4.86  -8.06  40.00  -1.81   -6.85  -3.96   0.36   20.00
       ETF    asym35_10  153 -30.49 -29.09   8.50 -14.76  -35.66 -28.47   0.22   42.86
              sym25      155 -23.54 -26.04  18.71 -11.23  -28.28 -21.65   0.26   35.90
              sym35      162 -13.69 -13.76  35.19  -5.17  -21.17 -10.63   0.31   34.51
QCOM   DCAL   asym35_10  237 -14.86 -13.29  21.52  -6.91  -20.09  -8.73   0.93   27.59
              sym25      265 -10.50  -8.37  28.68  -6.79  -13.50  -6.59   1.04   23.08
              sym35      284   1.22   0.72  51.06   0.52   -1.90   5.07   1.25   25.15
       ETF    asym35_10  304 -26.13 -21.38  15.46 -14.75  -33.80 -18.05   0.82   57.81
              sym25      322 -21.06 -16.70  21.12 -10.09  -27.51 -14.03   0.96   52.42
              sym35      322  -5.46  -1.91  47.20  -2.19  -12.41   1.84   1.14   51.54
SNDK   DCAL   asym35_10    9 -20.62 -49.94  11.11  -0.66     NaN -20.62   5.00  154.00
              sym25       12 -29.27 -41.16  16.67  -2.75     NaN -29.27   5.70  108.59
              sym35       10 -27.49 -24.17  20.00  -2.72     NaN -27.49   6.87  114.51
       ETF    asym35_10   10 -58.35 -60.18   0.00  -5.20     NaN -58.35   3.65  247.88
              sym25       11 -58.62 -47.66   0.00  -4.19     NaN -58.62   5.30  131.31
              sym35       11 -30.38 -44.38   9.09  -3.62     NaN -30.38   5.65  153.28
STX    DCAL   asym35_10  242 -32.20 -31.55   9.50 -18.93  -35.47 -28.09   0.59   67.74
              sym25      276 -27.64 -25.94  11.23 -16.88  -30.70 -24.10   0.67   55.43
              sym35      293 -17.18 -14.20  32.76  -6.98  -20.38 -13.21   0.76   54.55
       ETF    asym35_10  202 -47.29 -42.63   4.46 -17.31  -49.51 -44.73   0.52  104.49
              sym25      222 -42.88 -35.99   7.21 -14.29  -45.98 -39.54   0.60   80.17
              sym35      232 -25.15 -24.50  27.16  -7.88  -28.30 -21.40   0.70   85.71
TSLA   DCAL   asym35_10  266   5.45   0.05  51.13   3.76    5.72   4.96   4.56   11.08
              sym25      282   5.89   0.53  51.06   3.62    6.49   4.53   5.84   10.94
              sym35      293  14.40  12.18  62.80   7.38   13.91  15.49   6.70   11.20
       ETF    asym35_10  333   0.07  -4.28  42.04   0.04   -1.00   1.35   3.74   16.52
              sym25      348   0.19  -1.02  47.13   0.13   -0.46   0.96   4.45   16.55
              sym35      349  13.04   8.20  59.89   5.67   11.40  15.23   5.22   16.09
UNH    DCAL   asym35_10  273 -21.32 -19.66  18.32 -10.32  -25.38 -14.52   2.07   59.50
              sym25      308 -18.68 -16.87  20.13 -11.01  -20.36 -15.57   2.49   52.40
              sym35      289  -7.07  -6.46  43.25  -3.05   -7.45  -6.21   2.70   55.78
       ETF    asym35_10  325 -32.82 -31.90   9.23 -21.99  -37.19 -27.40   1.80  103.45
              sym25      334 -28.35 -26.72  13.47 -16.68  -33.12 -22.50   2.17   77.46
              sym35      336 -13.68 -17.00  33.33  -5.61  -15.41 -11.48   2.54   80.04
V      DCAL   asym35_10  196 -10.34 -12.34  23.47  -7.29  -10.59  -9.79   1.06   32.19
              sym25      214  -4.86  -6.41  36.92  -3.39   -5.33  -3.83   1.24   26.56
              sym35      223   8.54   8.70  62.33   3.72    8.25   9.24   1.51   27.56
       ETF    asym35_10  229 -19.93 -20.69  18.34 -12.90  -22.38 -16.89   0.93   55.42
              sym25      242 -14.59 -17.84  25.62  -8.19  -15.57 -13.38   1.11   43.42
              sym35      246  -1.54  -5.88  45.53  -0.63   -2.68  -0.11   1.34   45.01
VRT    DCAL   asym35_10   55 -21.32 -18.91   5.45  -8.93     NaN -21.32   1.35   62.07
              sym25       69 -18.39 -17.27  15.94  -5.52     NaN -18.39   1.55   48.00
              sym35       74  -5.27  -7.30  40.54  -1.30     NaN  -5.27   1.76   47.17
       ETF    asym35_10   59 -36.29 -36.61   5.08 -12.65     NaN -36.29   1.12  101.89
              sym25       67 -27.69 -28.56   7.46 -10.86     NaN -27.69   1.39   78.65
              sym35       68 -15.47 -17.73  32.35  -4.08     NaN -15.47   1.52   74.92
WDC    DCAL   asym35_10  204 -24.30 -24.23  11.27 -13.30  -17.50 -32.90   0.54   52.20
              sym25      235 -23.93 -22.49  18.72  -9.89  -17.40 -32.91   0.66   45.33
              sym35      249 -12.68 -10.29  38.55  -4.62   -4.84 -23.62   0.75   44.66
       ETF    asym35_10  199 -43.40 -40.02   2.01 -18.05  -38.04 -49.04   0.45   96.91
              sym25      212 -36.79 -32.04  10.85 -11.60  -29.76 -44.52   0.52   78.79
              sym35      217 -24.95 -26.92  28.11  -8.34  -20.69 -30.11   0.62   76.92
WMT    DCAL   asym35_10  249 -11.55 -14.89  26.51  -5.28  -14.41  -7.80   0.50   31.03
              sym25      287  -7.03 -10.41  31.36  -4.31   -8.12  -5.61   0.61   26.55
              sym35      289   4.48   4.02  55.02   2.21    4.31   4.71   0.70   25.93
       ETF    asym35_10  208 -22.54 -25.39  15.87 -13.47  -28.02 -15.76   0.42   46.79
              sym25      227 -17.84 -19.88  20.26 -10.72  -18.17 -17.46   0.51   42.86
              sym35      228  -3.31  -2.61  48.25  -1.39   -3.67  -2.88   0.62   40.96
XOM    DCAL   asym35_10  244 -13.31 -16.80  20.08  -8.31  -12.38 -14.31   0.48   31.01
              sym25      296 -11.87 -13.87  22.64  -8.98  -13.18 -10.39   0.58   26.87
              sym35      297  -0.68  -3.68  46.80  -0.34   -2.04   0.86   0.67   27.37
       ETF    asym35_10  215 -25.41 -26.84  11.16 -18.36  -28.02 -22.35   0.40   48.89
              sym25      232 -18.36 -19.28  13.79 -12.48  -19.73 -16.91   0.50   42.22
              sym35      240  -4.84  -8.20  40.42  -1.95   -9.57   0.47   0.57   40.00
```

### DCAL asym35_10: variants, all three names

```
    variant     n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 11446 -21.00 -17.57 20.21 -25.65 -24.18 -16.76       0.00       NaN
       pt25 11446 -20.52 -17.32 19.96 -72.16 -23.14 -17.04       0.47      0.61
       pt50 11446 -20.04 -17.43 20.42 -65.84 -22.64 -16.58       0.95      1.25
       pt75 11446 -20.00 -17.47 20.35 -65.17 -22.63 -16.50       1.00      1.31
     stop40 11446 -21.48 -17.67 20.10 -55.56 -23.78 -18.43      -0.49     -0.63
     stop60 11446 -21.94 -17.60 20.16 -26.23 -24.80 -18.13      -0.94     -4.34
 recenter2s 11446 -25.62 -19.78 18.07 -26.87 -28.75 -21.44      -4.62     -9.40
  inversion 11446 -24.83 -20.91 13.44 -86.12 -27.18 -21.70      -3.83     -4.87
   drop_far 11446 -21.81 -18.13 19.35 -26.69 -24.97 -17.61      -0.82    -10.20
close_far50 11446 -23.10 -18.35 19.42 -27.59 -25.90 -19.37      -2.10     -9.55
```

### DCAL sym25: variants, all three names

```
    variant     n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 13079 -17.29 -15.23 23.90 -57.89 -19.32 -14.42       0.00       NaN
       pt25 13079 -18.22 -15.11 23.14 -70.76 -20.29 -15.30      -0.93     -6.46
       pt50 13079 -17.43 -15.22 24.02 -62.50 -19.36 -14.71      -0.14     -1.43
       pt75 13079 -17.25 -15.23 23.95 -60.56 -19.16 -14.55       0.04      0.45
     stop40 13079 -18.73 -15.36 23.76 -53.16 -20.73 -15.93      -1.45     -7.99
     stop60 13079 -18.30 -15.28 23.82 -52.18 -20.31 -15.46      -1.01     -5.93
 recenter2s 13079 -24.92 -19.26 20.09 -65.37 -27.51 -21.27      -7.63    -31.25
  inversion 13079 -24.98 -21.09 12.00 -91.64 -27.31 -21.72      -7.70    -30.71
   drop_far 13079 -19.94 -17.20 20.41 -66.64 -21.95 -17.11      -2.65    -16.86
close_far50 13079 -20.73 -17.24 21.86 -60.59 -22.70 -17.94      -3.44    -17.15
```

### DCAL sym35: variants, all three names

```
    variant     n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 13207  -5.87  -5.08 44.23 -15.99  -7.69  -3.23       0.00       NaN
       pt25 13207 -11.77  -6.79 40.62 -41.45 -13.52  -9.23      -5.90    -28.63
       pt50 13207  -7.78  -5.30 43.89 -23.54  -9.55  -5.20      -1.91    -13.88
       pt75 13207  -6.55  -5.11 44.16 -18.94  -8.35  -3.94      -0.68     -6.57
     stop40 13207  -8.15  -5.82 43.45 -20.59 -10.12  -5.28      -2.28    -13.11
     stop60 13207  -7.11  -5.27 44.03 -17.86  -9.13  -4.19      -1.24     -7.74
 recenter2s 13207 -16.87 -11.31 37.84 -38.13 -19.55 -12.98     -11.00    -33.00
  inversion 13207 -22.15 -20.36 20.60 -80.90 -24.37 -18.94     -16.28    -54.91
   drop_far 13207 -15.52 -13.98 29.42 -55.16 -17.24 -13.03      -9.65    -46.90
close_far50 13207  -9.44  -8.37 40.80 -25.05 -11.38  -6.63      -3.57    -24.30
```

### ETF asym35_10: variants, all three names

```
    variant     n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 11726 -28.84 -26.22 14.71 -83.99 -33.48 -23.77       0.00       NaN
       pt25 11726 -29.30 -25.85 13.07 -99.30 -33.82 -24.36      -0.46     -2.67
       pt50 11726 -28.67 -25.98 14.69 -88.87 -33.15 -23.77       0.17      1.19
       pt75 11726 -28.43 -25.99 14.97 -81.63 -33.18 -23.24       0.41      2.98
     stop40 11726 -31.43 -26.39 14.58 -64.82 -36.27 -26.15      -2.59     -7.70
     stop60 11726 -30.88 -26.33 14.62 -64.23 -35.60 -25.71      -2.04     -6.20
 recenter2s 11726 -37.27 -31.04 12.10 -81.40 -43.62 -30.33      -8.43    -30.05
  inversion 11726 -33.98 -29.31 10.50 -98.46 -38.88 -28.64      -5.15    -20.57
   drop_far 11726 -29.99 -26.97 13.70 -87.75 -34.71 -24.84      -1.16    -13.32
close_far50 11726 -33.14 -27.98 13.58 -71.06 -37.60 -28.28      -4.31    -13.23
```

### ETF sym25: variants, all three names

```
    variant     n    roc    med   win       t      A      B  d_vs_hold  t_paired
       hold 12671 -24.48 -21.49 19.31  -71.99 -28.23 -20.39       0.00       NaN
       pt25 12671 -24.77 -21.47 17.16  -49.22 -27.99 -21.25      -0.29     -0.65
       pt50 12671 -24.04 -21.43 19.13  -46.36 -27.28 -20.50       0.44      1.02
       pt75 12671 -23.86 -21.38 19.33  -45.31 -26.95 -20.50       0.61      1.45
     stop40 12671 -27.57 -21.95 19.10  -55.03 -31.68 -23.09      -3.09     -8.20
     stop60 12671 -26.61 -21.66 19.24  -53.29 -30.59 -22.28      -2.14     -5.78
 recenter2s 12671 -38.28 -30.15 14.78  -80.68 -45.16 -30.76     -13.80    -40.33
  inversion 12671 -32.70 -28.14 10.63 -107.26 -37.05 -27.96      -8.22    -32.85
   drop_far 12671 -27.20 -24.06 16.04  -85.01 -31.26 -22.76      -2.72    -18.23
close_far50 12671 -30.65 -25.83 16.06  -65.12 -34.52 -26.43      -6.17    -17.28
```

### ETF sym35: variants, all three names

```
    variant     n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 12721 -11.47 -11.03 39.17 -24.99 -14.74  -7.84       0.00       NaN
       pt25 12721 -19.36 -14.25 30.93 -53.22 -22.88 -15.43      -7.89    -29.54
       pt50 12721 -14.53 -11.73 37.79 -35.53 -18.02 -10.65      -3.06    -15.50
       pt75 12721 -12.57 -11.25 38.90 -28.96 -15.89  -8.87      -1.10     -6.94
     stop40 12721 -16.77 -13.07 37.50 -34.77 -20.58 -12.53      -5.30    -15.87
     stop60 12721 -14.27 -11.59 38.72 -27.65 -18.05 -10.06      -2.80    -11.61
 recenter2s 12721 -29.22 -22.99 30.69 -45.29 -35.43 -22.30     -17.75    -33.85
  inversion 12721 -29.62 -27.62 20.05 -72.91 -33.93 -24.82     -18.15    -52.47
   drop_far 12721 -22.43 -20.86 24.05 -68.02 -25.84 -18.63     -10.96    -40.54
close_far50 12721 -18.12 -17.51 33.42 -41.10 -21.78 -14.04      -6.65    -28.56
```

### sym35: HOLD by regime (the SPY playbook cells) x structure

```
                      n   hold    med    win      t      A      B  debit     ba
struct regime                                                                  
DCAL   Bear_HiVIX  2302 -10.95 -10.95  38.23 -11.06 -15.47  -3.82   1.30  45.52
       Bear_LoVIX  2226  -4.25  -4.16  45.78  -4.75  -4.53  -3.20   0.84  32.76
       Bull_HiVIX  2488  -8.37  -7.72  40.76 -10.29  -8.64  -7.69   1.37  41.56
       Bull_LoVIX  6191  -3.56  -2.35  47.31  -6.92  -5.21  -2.15   1.12  30.99
ETF    Bear_HiVIX  2301 -18.53 -17.03  33.38 -12.34 -24.86 -10.78   1.33  71.26
       Bear_LoVIX  2022  -8.62  -9.41  41.10  -8.18 -10.15  -3.41   0.74  46.15
       Bull_HiVIX  2201 -13.70 -13.54  35.67 -14.36 -13.88 -13.35   1.27  67.61
       Bull_LoVIX  6197  -8.99  -8.54  41.94 -15.42 -12.92  -6.44   1.15  48.28
```

### asym35_10: HOLD by regime (the SPY playbook cells) x structure

```
                      n   hold    med    win      t      A      B  debit     ba
struct regime                                                                  
DCAL   Bear_HiVIX  2030 -24.02 -21.30  17.39 -29.13 -28.87 -17.33   1.00  47.85
       Bear_LoVIX  1881 -22.02 -18.16  17.86 -23.76 -24.20 -14.97   0.62  39.25
       Bull_HiVIX  2134 -26.58 -20.66  17.34  -6.49 -29.88 -18.49   1.08  45.33
       Bull_LoVIX  5401 -17.30 -15.04  23.22 -40.30 -18.28 -16.51   0.86  34.86
ETF    Bear_HiVIX  2094 -35.33 -30.98  11.80 -37.65 -42.09 -27.37   1.02  77.80
       Bear_LoVIX  1836 -29.17 -26.84  13.02 -35.13 -32.21 -19.58   0.55  55.91
       Bull_HiVIX  2048 -32.85 -31.02  11.28 -38.46 -35.97 -27.08   1.00  76.92
       Bull_LoVIX  5748 -24.93 -22.94  17.54 -55.13 -28.49 -22.62   0.86  55.41
```

### sym25: HOLD by regime (the SPY playbook cells) x structure

```
                      n   hold    med    win      t      A      B  debit     ba
struct regime                                                                  
DCAL   Bear_HiVIX  2263 -21.96 -18.75  18.78 -25.69 -25.60 -16.50   1.16  43.64
       Bear_LoVIX  2191 -16.17 -14.86  24.97 -24.44 -16.77 -13.97   0.71  33.33
       Bull_HiVIX  2443 -20.56 -18.32  18.79 -28.36 -21.93 -17.02   1.22  40.00
       Bull_LoVIX  6182 -14.67 -12.91  27.42 -36.56 -16.21 -13.41   1.00  30.30
ETF    Bear_HiVIX  2258 -29.65 -25.26  15.63 -36.06 -34.49 -23.95   1.15  69.72
       Bear_LoVIX  2009 -22.79 -20.81  21.15 -26.09 -25.05 -15.19   0.63  47.62
       Bull_HiVIX  2184 -29.48 -27.10  13.10 -34.78 -31.42 -25.91   1.11  66.67
       Bull_LoVIX  6220 -21.39 -18.65  22.23 -45.82 -25.24 -18.92   0.99  47.19
```

### sym35: HOLD by entry bid-ask x structure

```
                   n   hold    med    win      t      A      B  debit     ba
struct ba_b                                                                 
DCAL   <=10%     747  10.19   8.66  64.12   9.25   7.74  11.99   1.50   7.85
       10-25%   3637   6.63   5.19  56.45  11.44   5.91   7.60   1.21  17.72
       >25%     8823 -12.38 -11.60  37.52 -26.29 -13.87 -10.02   1.06  50.00
ETF    <=10%     196   8.60   5.91  54.59   3.44   6.51   9.28   2.06   8.57
       10-25%   1934   7.46   5.73  56.46   8.97   6.94   7.81   1.39  18.71
       >25%    10591 -15.30 -14.80  35.73 -29.41 -17.80 -12.19   1.05  63.83
```

### sym35 DCAL: HOLD by year

```
         n   hold    med    win      t      A      B  debit     ba
year                                                              
2018  1749  -6.77  -6.77  43.05  -6.31  -6.77    NaN   0.74  40.00
2019  1864  -3.11  -2.22  47.32  -3.50  -3.11    NaN   0.81  25.53
2020  1806 -11.57 -10.24  38.10 -10.23 -11.57    NaN   1.33  49.60
2021  1723 -11.41  -8.89  39.47 -10.92 -11.41    NaN   1.34  39.32
2022  1454  -2.61  -2.25  47.80  -2.58  -2.89  -2.37   1.31  35.12
2023  1514  -1.83  -2.87  46.96  -2.05    NaN  -1.83   1.02  26.77
2024  1453  -3.05  -2.55  47.76  -2.89    NaN  -3.05   1.28  30.86
2025  1498  -4.29  -3.86  45.53  -3.70    NaN  -4.29   1.70  40.84
2026   146 -13.13 -12.65  39.04  -3.43    NaN -13.13   2.15  82.25
```

### sym35 ETF: HOLD by year

```
         n   hold    med    win      t      A      B  debit      ba
year                                                               
2018  1485 -12.71 -10.16  39.93  -5.93 -12.71    NaN   0.63   57.82
2019  1568 -11.29  -9.69  39.41 -10.76 -11.29    NaN   0.68   43.48
2020  1452 -18.43 -18.06  33.13 -12.11 -18.43    NaN   1.20   86.79
2021  1485 -18.95 -18.20  32.46 -14.60 -18.95    NaN   1.30   64.79
2022  1555  -9.75 -11.28  39.23  -9.36 -10.19  -9.38   1.37   56.00
2023  1602  -6.01  -5.50  43.51  -6.45    NaN  -6.01   0.99   40.00
2024  1677  -5.42  -4.30  45.56  -5.12    NaN  -5.42   1.29   45.00
2025  1681  -9.86 -11.42  39.68  -8.69    NaN  -9.86   1.67   56.57
2026   216 -18.38 -26.03  32.87  -4.52    NaN -18.38   2.44  102.93
```

## Stocks (step 5, 2026-09-15): symmetric 0.35Δ double calendars on the straddle pool's 60 most liquid stocks

Pull by DELTA band (the option table's strikes are unadjusted for splits; strike windows around Tradier's adjusted
closes returned nothing for NVDA/AVGO/GOOGL/TSLA/...), spot from put-call parity in the chain (same basis as the strikes),
FB→META alias, both sides, 2018-11 → 2026-07. 98,318 double calendars; every entry flagged for an earnings date inside
(entry, long expiry]. Full tables: `data/cache/calendar_path/report_dcal_stocks.txt`.

**Pooled, ex-earnings, sym35: NEGATIVE** (12/19d −5.9%, 44% win; 20/27d −11.5%, 39% win) -- because the median entry
bid-ask on single names is 35–54% of the debit. The cut that mattered on ETFs matters more here:

| sym35, ex-earnings, hold | n | ROC | win | halves | monthly-mean t | months + | years + |
|---|---|---|---|---|---|---|---|
| entry bid-ask ≤ 25% of debit, 12/19d | 4,384 | **+7.2%** | 58% | +6.2 / +8.6 | 8.1 | 81% | 9 of 9 |
| entry bid-ask ≤ 25% of debit, 20/27d | 2,130 | **+7.6%** | 56% | +6.9 / +8.0 | 5.4 | 66% | 9 of 9 |
| entry bid-ask ≤ 10% of debit, 12/19d | 747 | +10.2% | 64% | +7.7 / +12.0 | | | |
| entry bid-ask > 25% of debit | 8,823 / 10,591 | −12 / −15% | 36–38% | | | | |
| earnings inside the window (all markets) | 3,397 / 4,662 | −9.1 / −13.9% vs −5.9 / −11.5 ex-earnings | | | | | |

Hold beats every variant on the tight cut too (paired t −2 to −32): pt25 −5pp, re-center −6pp, drop_far −10pp,
inversion −12pp. Regime separates nothing on the tight cut (every cell +5 to +9%). **Which stocks:** the tight-market
edge lives in the high-priced mega-caps -- NFLX +18%, AVGO +22% (n=44), TSLA +15%, NVDA +13%, META +13%, AAPL +13%,
GOOG +13%, MSFT +12%, AMD +11% (12/19d) -- and dies in cheap names whose debit is a few cents: AAL −14%, BAC −8%,
CSCO −7%, XOM −3%, PLTR −1%, INTC +1%. The debit's DOLLAR size is the real gate: below ~$1 the bid-ask eats it.

**Read against the ETFs:** stocks at +7% vs IWM +26% / QQQ +19% / SPY +13% (20/27d). Single names work, at about a
third of the index edge, only on tight markets, outside earnings, on names whose debit is $1.50+. Not run: the single
ATM calendar on stocks (the process was killed for memory after the double-calendar pass; low value given the above).
Caveat: the parity spot jumps across a split date, so the re-center variant's sigma is wrong for ~20 sessions around
each split (affects only that variant).

## Double calendars (2026-09-15): 30 high-priced non-pool names (generalisation test), 40,438 trades

Put calendar below + call calendar above, same two expiries; strike sets by the short legs' delta: sym25 (0.25/0.25), sym35 (0.35/0.35 = the SPY playbook's Bullish_LowIV cell), asym35_10 (0.35P/0.10C = its Bearish_HighIV cell). Extra variants: drop_far (when the close crosses a short strike, close the far side, hold the tested side), close_far50 (close a side at half its entry debit). Costs on all four legs.

### HOLD by earnings-in-window x structure x strike set

```
                                 n   hold    med    win      t      A      B  debit      ba
earn_in_win struct dset                                                                    
False       DCAL   asym35_10  4782 -33.98 -28.79  11.46 -65.90 -36.33 -30.40   2.02   84.54
                   sym25      5491 -30.44 -26.38  15.01 -62.64 -32.18 -27.57   2.40   75.00
                   sym35      5475 -19.52 -17.70  31.80 -33.07 -21.53 -16.02   2.72   75.18
            ETF    asym35_10  5453 -46.87 -42.35   7.50 -82.07 -49.61 -43.93   1.82  133.33
                   sym25      6017 -40.82 -37.30  11.10 -78.95 -43.64 -37.81   2.14  115.29
                   sym35      6036 -28.94 -28.21  24.98 -45.53 -31.24 -26.45   2.50  115.10
True        DCAL   asym35_10   920 -40.63 -35.73  15.43 -27.48 -42.45 -37.45   2.10  109.62
                   sym25      1013 -37.35 -31.90  17.08 -27.28 -39.20 -34.06   2.60   97.60
                   sym35       998 -27.09 -23.58  28.86 -18.62 -28.05 -25.10   2.75   98.81
            ETF    asym35_10  1333 -52.96 -49.35  11.63 -37.60 -54.70 -50.81   1.82  167.57
                   sym25      1460 -47.98 -44.63  11.92 -39.36 -49.49 -46.06   2.10  147.74
                   sym35      1460 -36.37 -35.81  23.42 -26.56 -37.73 -34.69   2.45  150.80
```

_Tables below EXCLUDE entries with an earnings date inside (entry, long expiry] (7184 of 40438)._

### HOLD by ticker x structure x strike set

```
                           n   hold    med    win      t      A       B  debit      ba
ticker struct dset                                                                    
ADBE   DCAL   asym35_10  276 -10.63 -10.90  30.07  -7.80 -11.32   -9.35   2.93   38.22
              sym25      327  -9.20 -10.29  30.28  -7.59  -9.31   -9.03   3.38   33.11
              sym35      300   4.38   4.47  56.33   2.38   3.51    6.14   3.93   33.71
       ETF    asym35_10  352 -21.02 -20.84  21.02 -13.04 -22.21  -19.60   2.33   58.98
              sym25      368 -14.66 -13.00  28.53  -9.91 -14.01  -15.42   2.90   52.71
              sym35      369  -3.85  -4.68  45.53  -1.99  -6.02   -1.18   3.35   57.14
AMGN   DCAL   asym35_10  228 -30.51 -23.97  16.67 -11.68 -29.48  -32.69   1.26   81.49
              sym25      267 -27.64 -26.15  21.35 -13.33 -27.34  -28.35   1.48   74.84
              sym35      263 -17.88 -14.00  36.12  -6.10 -15.92  -22.97   1.67   69.66
       ETF    asym35_10  286 -43.88 -42.74  11.19 -18.09 -43.45  -44.44   1.07  142.23
              sym25      348 -39.17 -38.92  13.51 -19.68 -39.33  -38.99   1.28  129.49
              sym35      336 -28.52 -27.21  24.70 -11.75 -28.10  -29.05   1.45  130.33
ANET   DCAL   asym35_10  209 -36.58 -29.17   6.22 -14.88 -48.62  -22.14   1.77   82.05
              sym25      248 -31.87 -27.61  10.08 -15.31 -41.72  -17.28   2.06   84.58
              sym35      264 -23.82 -20.93  24.62  -9.81 -34.65   -7.66   2.46   85.39
       ETF    asym35_10  198 -51.78 -45.04   3.03 -17.89 -69.33  -34.23   1.46  112.26
              sym25      224 -46.13 -40.91   8.48 -14.74 -63.04  -26.28   1.78  104.88
              sym35      229 -31.30 -27.81  23.58  -9.18 -48.20  -11.36   2.00  105.45
APP    DCAL   asym35_10   49 -23.98 -22.89  18.37  -5.51    NaN  -23.98   5.35   62.86
              sym25       66 -22.17 -17.42  21.21  -4.95    NaN  -22.17   5.42   55.98
              sym35       60 -11.26  -8.01  40.00  -2.13    NaN  -11.26   3.75   56.51
       ETF    asym35_10   68 -35.97 -37.01  13.24  -9.18    NaN  -35.97   4.21  118.67
              sym25       70 -29.85 -32.47  18.57  -7.80    NaN  -29.85   5.17  105.06
              sym35       77 -16.19 -17.12  33.77  -2.68    NaN  -16.19   5.55  106.98
ASML   DCAL   asym35_10  143 -24.63 -17.88  12.59  -8.73 -58.91  -13.09   5.80   56.07
              sym25      156 -20.43 -16.88  19.23  -7.72 -49.17   -9.84   6.72   54.37
              sym35      145 -10.31  -8.80  41.38  -2.96 -48.50    4.75   7.65   56.20
       ETF    asym35_10  146 -40.48 -35.96   6.16 -14.16 -72.81  -29.91   4.64  111.90
              sym25      152 -31.15 -24.80  12.50 -11.57 -61.16  -18.93   5.65   97.12
              sym35      150 -17.35 -14.41  32.00  -5.04 -40.78   -8.24   6.60   91.17
AZO    DCAL   asym35_10  137 -46.64 -44.85   1.46 -22.95 -45.49  -53.01   7.55  170.59
              sym25      146 -43.41 -44.24   4.11 -20.05 -42.42  -50.01   8.36  152.40
              sym35      147 -31.48 -31.04  14.97 -11.70 -30.37  -40.02   8.70  148.72
       ETF    asym35_10  137 -61.18 -59.49   2.19 -25.26 -60.87  -62.65   7.05  227.64
              sym25      145 -56.53 -55.92   1.38 -25.31 -55.28  -63.48   7.50  206.78
              sym35      149 -41.76 -40.90  12.08 -14.30 -40.05  -50.67   9.20  209.24
BKNG   DCAL   asym35_10  190 -36.14 -36.65   4.21 -23.26 -32.61  -40.14  17.68  121.22
              sym25      224 -35.01 -35.33   6.70 -22.26 -31.43  -39.80  20.95  107.92
              sym35      223 -23.37 -26.83  22.42 -10.05 -16.83  -32.52  23.05  107.93
       ETF    asym35_10  209 -46.21 -44.43   2.39 -27.54 -39.26  -54.23  14.25  172.95
              sym25      225 -41.62 -43.33   5.78 -25.85 -36.22  -47.79  17.60  147.00
              sym35      229 -32.36 -37.65  18.34 -14.07 -26.51  -39.05  20.00  150.00
BLK    DCAL   asym35_10  204 -37.33 -35.19   7.84 -18.98 -40.46  -29.06   3.56  117.97
              sym25      241 -33.41 -27.86  11.20 -17.74 -34.41  -30.71   4.28   98.95
              sym35      234 -23.35 -21.07  26.50  -9.79 -25.31  -17.53   4.93  102.03
       ETF    asym35_10  297 -48.81 -47.40   3.03 -30.08 -51.46  -45.63   3.40  165.00
              sym25      325 -43.88 -42.07   4.62 -25.45 -48.81  -38.13   4.00  142.42
              sym35      327 -34.99 -36.05  20.49 -15.37 -39.82  -29.00   4.75  145.21
CI     DCAL   asym35_10  181 -34.22 -33.23   8.84 -15.74 -35.95  -30.54   1.48  100.00
              sym25      202 -30.59 -28.29  13.37 -13.64 -33.52  -22.57   1.63   85.13
              sym35      218 -22.60 -21.30  27.06  -8.27 -24.72  -17.15   1.90   79.86
       ETF    asym35_10  215 -46.36 -44.96   5.12 -23.91 -45.49  -47.41   1.30  152.54
              sym25      217 -43.33 -39.02   6.91 -20.33 -46.88  -38.78   1.49  122.22
              sym35      226 -28.51 -25.93  26.11 -10.32 -33.34  -22.31   1.78  125.09
DE     DCAL   asym35_10  190 -20.01 -17.14  14.21 -10.27 -19.01  -21.82   1.83   59.92
              sym25      217 -16.54 -16.43  21.20  -9.37 -14.18  -21.82   2.22   49.22
              sym35      225  -6.31  -4.48  45.33  -2.46  -3.24  -12.45   2.54   50.00
       ETF    asym35_10  218 -34.59 -31.54  10.09 -15.55 -35.42  -33.48   1.73  104.91
              sym25      234 -27.41 -27.28  13.25 -13.22 -25.01  -30.56   2.11   82.64
              sym35      227 -14.35 -13.83  33.04  -5.08 -11.93  -17.32   2.50   75.00
ELV    DCAL   asym35_10   49 -48.45 -52.60   4.08  -9.74    NaN  -48.45   2.80  181.40
              sym25       49 -43.19 -41.07   8.16  -9.21    NaN  -43.19   3.32  108.97
              sym35       49 -29.35 -25.80  22.45  -5.03    NaN  -29.35   3.75  128.49
       ETF    asym35_10   55 -63.55 -60.78   1.82 -15.65    NaN  -63.55   2.08  317.24
              sym25       61 -61.11 -66.83   0.00 -14.82    NaN  -61.11   2.82  252.63
              sym35       56 -49.98 -47.62   8.93  -9.32    NaN  -49.98   3.18  242.58
FDX    DCAL   asym35_10  186 -13.42 -12.03  20.97  -8.30 -12.58  -15.12   1.31   41.20
              sym25      215 -11.08 -10.73  26.05  -6.91  -9.36  -14.73   1.56   35.71
              sym35      224  -2.10  -2.51  46.43  -0.99  -0.11   -5.96   1.81   38.47
       ETF    asym35_10  207 -28.41 -27.34   8.70 -16.90 -28.01  -28.99   1.16   68.66
              sym25      221 -21.03 -23.01  16.74 -12.27 -19.00  -23.57   1.38   63.76
              sym35      224  -6.69  -8.47  41.96  -2.56  -9.81   -2.52   1.60   59.43
HUM    DCAL   asym35_10  257 -54.30 -51.88   4.67 -21.98 -58.38  -46.21   2.18  179.66
              sym25      292 -48.03 -47.34   8.22 -21.33 -52.23  -38.77   2.68  147.78
              sym35      291 -37.97 -38.09  15.81 -14.82 -40.16  -33.50   3.15  154.93
       ETF    asym35_10  312 -59.63 -58.35   5.77 -25.25 -71.30  -44.52   1.95  242.91
              sym25      339 -57.80 -57.96   5.90 -25.10 -70.29  -42.44   2.35  200.00
              sym35      346 -43.99 -46.13  14.45 -16.67 -56.38  -28.18   2.75  193.08
ISRG   DCAL   asym35_10  206 -39.95 -35.66   7.77 -16.74 -46.64  -29.19   2.95  113.18
              sym25      230 -37.25 -32.32   8.70 -17.78 -43.10  -26.09   3.44   95.65
              sym35      232 -21.91 -20.32  30.60  -7.08 -30.14   -6.85   4.00   97.72
       ETF    asym35_10  221 -55.53 -51.41   4.07 -22.93 -63.03  -46.45   2.52  175.22
              sym25      246 -44.41 -43.79   7.32 -17.43 -55.12  -31.81   2.96  145.80
              sym35      254 -34.42 -33.23  19.29 -11.09 -43.94  -22.91   3.42  144.97
LIN    DCAL   asym35_10   14 -53.19 -61.55   0.00  -6.39 -67.18  -52.12   1.66   89.18
              sym25       16 -34.90 -31.18   0.00  -5.22 -27.02  -36.03   1.88   77.22
              sym35       15 -37.73 -30.97   6.67  -4.44 -37.56  -37.74   2.15   84.06
       ETF    asym35_10   21 -62.13 -61.57   0.00 -10.56    NaN  -62.13   1.27  153.72
              sym25       20 -47.38 -41.27   0.00  -7.15    NaN  -47.38   1.58   90.19
              sym35       23 -46.98 -49.17  13.04  -5.75  13.06  -49.71   1.85  123.08
LMT    DCAL   asym35_10  208 -25.69 -24.58  14.90 -11.90 -28.59  -20.55   1.92   71.08
              sym25      234 -21.70 -19.61  19.66  -9.41 -22.90  -19.00   2.20   60.39
              sym35      244 -12.70 -13.85  35.25  -4.76 -10.20  -17.81   2.50   66.67
       ETF    asym35_10  230 -35.36 -33.77  10.87 -15.06 -39.17  -30.49   1.66   97.56
              sym25      253 -31.84 -27.25  11.46 -13.88 -31.94  -31.73   1.90   84.75
              sym35      256 -21.67 -21.60  28.12  -7.89 -20.98  -22.52   2.30   94.00
MA     DCAL   asym35_10  270 -13.89 -14.36  23.70 -10.33 -11.37  -18.44   1.92   42.50
              sym25      284  -7.42  -9.82  32.04  -4.81  -6.38   -9.55   2.28   35.88
              sym35      290   2.93  -0.89  48.97   1.36   4.98   -1.55   2.58   37.88
       ETF    asym35_10  326 -25.33 -26.64  13.50 -16.69 -24.51  -26.30   1.65   67.56
              sym25      353 -16.39 -19.75  23.80 -11.05 -14.05  -19.14   1.99   57.81
              sym35      344  -2.90  -5.33  41.86  -1.38  -3.44   -2.24   2.30   58.68
MCD    DCAL   asym35_10  185 -16.89 -18.69  16.22 -10.81 -18.96  -11.58   0.96   49.79
              sym25      213 -11.75 -16.26  25.35  -5.30 -10.87  -14.00   1.09   41.94
              sym35      212  -0.14  -1.09  49.06  -0.05  -1.53    3.86   1.33   44.20
       ETF    asym35_10  207 -27.62 -28.60  11.59 -14.27 -28.88  -26.07   0.90   76.92
              sym25      232 -21.10 -24.23  16.81 -10.19 -20.04  -22.36   1.04   65.02
              sym35      233  -9.56 -11.13  35.19  -3.35  -8.49  -10.94   1.20   66.67
MCK    DCAL   asym35_10  174 -57.34 -48.98   2.30 -18.72 -61.65  -48.93   1.29  150.00
              sym25      212 -55.70 -47.38   2.36 -20.26 -59.32  -48.20   1.46  143.80
              sym35      207 -49.58 -45.70  13.53 -15.03 -52.57  -42.89   1.63  140.00
       ETF    asym35_10  185 -76.01 -73.39   0.54 -26.02 -79.62  -71.28   1.30  251.43
              sym25      220 -68.64 -66.35   2.27 -25.49 -72.38  -63.62   1.47  237.92
              sym35      210 -55.45 -55.45   9.05 -17.21 -57.67  -52.67   1.85  200.00
MELI   DCAL   asym35_10  198 -40.22 -37.49   1.52 -19.97 -41.89  -38.74  13.12  137.30
              sym25      226 -36.30 -34.88   4.87 -22.69 -36.36  -36.26  15.98  120.70
              sym35      219 -26.75 -29.02  20.09 -11.44 -27.47  -26.08  18.25  118.64
       ETF    asym35_10  235 -51.43 -49.43   0.43 -30.49 -55.89  -48.56  10.98  181.66
              sym25      269 -45.03 -45.24   4.09 -24.58 -46.09  -44.31  13.20  162.75
              sym35      261 -33.42 -34.71  15.33 -13.22 -35.22  -32.17  15.15  158.58
NOC    DCAL   asym35_10  171 -39.21 -37.43   6.43 -17.81 -38.13  -41.98   1.98  135.71
              sym25      202 -36.82 -33.24  10.40 -12.31 -37.63  -34.19   2.21  108.11
              sym35      198 -23.65 -20.50  26.26  -7.85 -24.27  -21.20   2.54  100.88
       ETF    asym35_10  187 -52.82 -46.71   4.28 -18.98 -51.65  -55.02   1.70  173.33
              sym25      208 -48.73 -46.87   8.65 -15.86 -47.20  -51.74   1.94  149.37
              sym35      209 -31.02 -28.10  23.92  -9.51 -31.08  -30.91   2.20  146.67
ORCL   DCAL   asym35_10  304 -23.48 -23.00  16.12 -14.68 -30.00  -15.75   0.47   45.61
              sym25      331 -19.14 -17.92  19.94 -11.27 -24.45  -12.73   0.57   41.32
              sym35      339  -4.68  -4.55  43.07  -2.02  -8.64    0.20   0.65   43.04
       ETF    asym35_10  293 -36.64 -34.32  10.92 -14.36 -50.03  -22.60   0.40   73.68
              sym25      325 -29.24 -27.81  15.08 -16.61 -38.84  -18.32   0.46   65.06
              sym35      328 -16.93 -18.69  31.71  -7.33 -22.60  -10.52   0.56   61.88
REGN   DCAL   asym35_10  159 -55.59 -55.46   4.40 -19.39 -49.35  -69.19   3.88  215.21
              sym25      184 -47.42 -47.81   5.43 -18.99 -43.32  -59.03   4.15  180.52
              sym35      191 -35.44 -35.92  17.28 -12.53 -30.07  -51.89   4.90  160.00
       ETF    asym35_10  186 -71.86 -75.15   2.15 -22.78 -56.88  -92.15   3.20  322.21
              sym25      210 -66.48 -69.30   4.29 -22.65 -56.64  -77.51   4.10  293.93
              sym35      213 -49.39 -55.23  12.21 -16.57 -36.37  -64.38   4.80  280.00
SPGI   DCAL   asym35_10  191 -62.89 -52.27   3.14 -17.97 -59.73  -70.91   1.68  172.73
              sym25      222 -59.24 -52.22   4.50 -20.64 -52.76  -74.23   2.11  154.65
              sym35      213 -46.93 -47.42  13.15 -15.59 -47.49  -45.43   2.40  152.38
       ETF    asym35_10  193 -88.89 -70.97   1.04 -13.59 -73.73 -108.97   1.50  242.67
              sym25      225 -74.35 -66.50   2.67 -20.09 -67.02  -84.02   1.85  218.60
              sym35      224 -72.15 -55.88   6.70 -12.09 -55.44  -94.44   2.15  215.86
TMO    DCAL   asym35_10   64 -39.71 -34.28   4.69  -8.79    NaN  -39.71   2.92   93.22
              sym25       75 -37.56 -28.76   5.33 -10.06    NaN  -37.56   3.75   85.71
              sym35       70 -24.72 -22.32  32.86  -3.72    NaN  -24.72   4.20   78.32
       ETF    asym35_10  125 -60.51 -53.68   0.80 -15.76    NaN  -60.51   2.45  148.24
              sym25      139 -49.57 -47.79   5.76 -15.53    NaN  -49.57   3.05  118.75
              sym35      146 -35.82 -32.76  19.18  -9.57    NaN  -35.82   3.43  120.66
TSM    DCAL   asym35_10  174 -13.32 -14.29  21.84  -7.46 -23.99   -4.85   0.73   25.47
              sym25      191 -10.80 -10.38  25.13  -6.13 -18.47   -4.51   0.87   22.53
              sym35      196   1.39   0.63  51.02   0.57  -6.50    8.23   1.04   25.00
       ETF    asym35_10  172 -20.89 -21.10  22.67  -7.26 -39.07   -7.49   0.70   42.51
              sym25      184 -15.00 -17.28  25.54  -6.91 -28.44   -5.75   0.82   38.05
              sym35      178  -2.32  -8.07  43.82  -0.81 -13.55    5.31   0.95   38.59
VRTX   DCAL   asym35_10  165 -71.95 -66.58   1.82 -20.65 -68.95  -77.50   1.90  239.22
              sym25      221 -64.90 -58.82   3.62 -22.18 -62.97  -68.57   2.15  228.07
              sym35      206 -57.62 -57.69   6.80 -17.14 -59.75  -52.67   2.39  200.00
       ETF    asym35_10  172 -86.58 -82.76   1.16 -28.20 -85.44  -88.66   1.66  342.56
              sym25      204 -78.53 -75.64   4.41 -24.38 -77.34  -80.33   1.91  300.85
              sym35      212 -70.97 -69.68   4.25 -21.41 -68.20  -75.27   2.43  287.90
```

### DCAL asym35_10: variants, all three names

```
    variant    n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 4782 -33.98 -28.79 11.46 -65.90 -36.33 -30.40       0.00       NaN
       pt25 4782 -34.09 -28.64 10.39 -73.18 -36.56 -30.33      -0.11     -0.45
       pt50 4782 -33.59 -28.46 11.21 -69.01 -35.80 -30.23       0.39      2.14
       pt75 4782 -33.67 -28.62 11.48 -67.24 -35.99 -30.13       0.31      2.11
     stop40 4782 -36.49 -29.22 11.31 -63.21 -38.88 -32.86      -2.52    -11.12
     stop60 4782 -35.69 -28.99 11.33 -63.00 -38.02 -32.14      -1.71     -8.66
 recenter2s 4782 -40.35 -32.52  9.68 -66.14 -43.69 -35.26      -6.37    -18.73
  inversion 4782 -39.47 -32.38  7.15 -78.20 -42.22 -35.28      -5.49    -16.78
   drop_far 4782 -34.63 -29.31 10.81 -67.41 -36.95 -31.11      -0.65     -6.77
close_far50 4782 -37.82 -30.58 10.50 -67.15 -40.46 -33.81      -3.85    -16.14
```

### DCAL sym25: variants, all three names

```
    variant    n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 5491 -30.44 -26.38 15.01 -62.64 -32.18 -27.57       0.00       NaN
       pt25 5491 -30.49 -26.07 13.55 -72.57 -32.45 -27.25      -0.05     -0.19
       pt50 5491 -30.10 -26.15 14.75 -66.98 -31.87 -27.17       0.35      1.81
       pt75 5491 -29.96 -26.10 15.08 -64.35 -31.75 -27.00       0.49      3.12
     stop40 5491 -33.19 -27.00 14.81 -62.26 -34.78 -30.56      -2.74    -12.87
     stop60 5491 -31.99 -26.54 14.92 -61.57 -33.54 -29.42      -1.54     -8.87
 recenter2s 5491 -41.43 -31.84 12.18 -65.02 -43.99 -37.21     -10.99    -27.55
  inversion 5491 -38.51 -32.47  7.21 -87.98 -41.17 -34.11      -8.07    -23.05
   drop_far 5491 -32.52 -28.22 12.68 -69.84 -34.36 -29.47      -2.08    -13.10
close_far50 5491 -35.16 -29.19 13.51 -67.51 -36.86 -32.34      -4.71    -20.86
```

### DCAL sym35: variants, all three names

```
    variant    n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 5475 -19.52 -17.70 31.80 -33.07 -21.53 -16.02       0.00       NaN
       pt25 5475 -23.94 -19.89 25.77 -52.64 -26.22 -19.99      -4.43    -12.65
       pt50 5475 -20.61 -18.09 30.58 -39.35 -22.86 -16.71      -1.10     -4.14
       pt75 5475 -19.74 -17.69 31.32 -35.75 -21.73 -16.29      -0.22     -1.14
     stop40 5475 -23.89 -19.48 30.83 -36.71 -26.00 -20.23      -4.37    -15.76
     stop60 5475 -21.28 -17.93 31.65 -33.85 -23.36 -17.67      -1.77     -8.87
 recenter2s 5475 -35.81 -27.22 25.64 -46.56 -39.13 -30.03     -16.29    -29.78
  inversion 5475 -36.18 -32.55 12.95 -73.94 -38.90 -31.44     -16.66    -35.83
   drop_far 5475 -28.06 -25.92 19.36 -57.42 -30.19 -24.36      -8.54    -28.68
close_far50 5475 -24.65 -22.43 28.60 -39.95 -26.97 -20.62      -5.13    -22.26
```

### ETF asym35_10: variants, all three names

```
    variant    n    roc    med  win      t      A      B  d_vs_hold  t_paired
       hold 5453 -46.87 -42.35 7.50 -82.07 -49.61 -43.93       0.00       NaN
       pt25 5453 -46.45 -41.76 5.30 -92.53 -49.22 -43.47       0.42      1.42
       pt50 5453 -45.75 -41.69 7.37 -87.30 -48.37 -42.92       1.13      4.49
       pt75 5453 -45.95 -41.90 7.52 -84.70 -48.86 -42.80       0.93      4.28
     stop40 5453 -52.69 -43.37 7.37 -64.91 -54.91 -50.31      -5.82     -9.17
     stop60 5453 -51.33 -42.87 7.41 -63.79 -53.30 -49.22      -4.46     -7.18
 recenter2s 5453 -58.79 -48.92 6.11 -79.50 -64.10 -53.09     -11.92    -26.47
  inversion 5453 -54.32 -47.40 5.02 -98.15 -57.31 -51.10      -7.45    -17.70
   drop_far 5453 -48.06 -43.06 6.80 -82.97 -50.93 -44.97      -1.18     -7.55
close_far50 5453 -54.22 -47.19 6.62 -71.28 -56.67 -51.59      -7.35    -12.57
```

### ETF sym25: variants, all three names

```
    variant    n    roc    med   win       t      A      B  d_vs_hold  t_paired
       hold 6017 -40.82 -37.30 11.10  -78.95 -43.64 -37.81       0.00       NaN
       pt25 6017 -40.73 -36.51  8.44  -94.54 -43.82 -37.43       0.09      0.30
       pt50 6017 -39.89 -36.37 10.90  -85.68 -42.88 -36.70       0.93      3.76
       pt75 6017 -39.91 -36.55 11.23  -82.38 -42.96 -36.67       0.90      4.25
     stop40 6017 -47.31 -39.13 10.74  -77.65 -49.68 -44.77      -6.49    -20.34
     stop60 6017 -44.89 -37.96 10.97  -74.95 -47.47 -42.14      -4.07    -14.83
 recenter2s 6017 -60.13 -49.60  7.86  -81.80 -67.60 -52.15     -19.31    -37.58
  inversion 6017 -52.31 -46.39  5.22 -104.26 -55.69 -48.70     -11.49    -29.23
   drop_far 6017 -43.33 -39.95  9.14  -88.15 -46.25 -40.20      -2.51    -12.42
close_far50 6017 -49.36 -45.03  9.12  -89.31 -51.94 -46.60      -8.54    -29.66
```

### ETF sym35: variants, all three names

```
    variant    n    roc    med   win      t      A      B  d_vs_hold  t_paired
       hold 6036 -28.94 -28.21 24.98 -45.53 -31.24 -26.45       0.00       NaN
       pt25 6036 -35.68 -31.79 14.55 -72.93 -38.12 -33.03      -6.73    -17.02
       pt50 6036 -31.41 -28.86 22.40 -56.16 -34.02 -28.58      -2.47     -7.64
       pt75 6036 -29.72 -28.60 24.04 -50.12 -32.38 -26.83      -0.77     -2.88
     stop40 6036 -37.97 -33.20 23.43 -53.64 -41.34 -34.32      -9.03    -22.17
     stop60 6036 -33.43 -29.30 24.55 -48.39 -36.47 -30.13      -4.49    -13.65
 recenter2s 6036 -52.61 -44.33 18.56 -62.56 -60.88 -43.66     -23.67    -35.66
  inversion 6036 -49.79 -47.15 10.92 -90.58 -53.71 -45.53     -20.85    -39.49
   drop_far 6036 -38.66 -36.68 13.82 -77.32 -41.84 -35.22      -9.72    -26.83
close_far50 6036 -38.95 -38.32 20.00 -60.36 -41.65 -36.03     -10.01    -29.26
```

### sym35: HOLD by regime (the SPY playbook cells) x structure

```
                      n   hold    med    win      t      A      B  debit      ba
struct regime                                                                   
DCAL   Bear_HiVIX   952 -27.97 -27.20  24.26 -20.26 -31.95 -21.06   3.11  110.85
       Bear_LoVIX   976 -12.72 -11.86  37.70  -9.79 -12.21 -15.00   1.95   65.05
       Bull_HiVIX  1103 -27.25 -24.63  23.93 -20.97 -30.21 -17.60   3.40  109.09
       Bull_LoVIX  2444 -15.45 -13.63  35.92 -17.17 -16.51 -14.38   2.60   59.88
ETF    Bear_HiVIX  1122 -36.33 -36.44  18.27 -26.56 -39.76 -32.14   2.92  165.67
       Bear_LoVIX   924 -20.56 -20.92  32.58 -13.18 -20.81 -19.74   1.73   87.87
       Bull_HiVIX  1058 -34.75 -33.63  19.57 -24.18 -37.77 -29.46   2.95  152.49
       Bull_LoVIX  2932 -26.66 -24.77  27.11 -27.97 -29.26 -25.00   2.45  100.00
```

### asym35_10: HOLD by regime (the SPY playbook cells) x structure

```
                      n   hold    med    win      t      A      B  debit      ba
struct regime                                                                   
DCAL   Bear_HiVIX   838 -41.49 -38.22   6.68 -35.31 -45.33 -35.49   2.33  124.11
       Bear_LoVIX   798 -29.14 -25.32  13.91 -24.30 -30.31 -24.71   1.42   72.07
       Bull_HiVIX   963 -42.56 -37.58   7.48 -36.02 -45.46 -34.88   2.60  125.45
       Bull_LoVIX  2183 -29.08 -23.70  14.15 -38.53 -29.46 -28.72   1.92   66.67
ETF    Bear_HiVIX  1021 -56.25 -51.22   3.92 -45.45 -61.09 -50.72   2.10  189.87
       Bear_LoVIX   850 -38.28 -35.32   9.76 -29.01 -40.43 -31.81   1.30  100.00
       Bull_HiVIX   954 -57.99 -52.32   4.09 -44.82 -61.95 -51.07   2.20  182.28
       Bull_LoVIX  2628 -41.97 -37.82   9.40 -49.37 -42.01 -41.95   1.78  112.26
```

### sym25: HOLD by regime (the SPY playbook cells) x structure

```
                      n   hold    med    win      t      A      B  debit      ba
struct regime                                                                   
DCAL   Bear_HiVIX   977 -38.61 -34.84   8.70 -33.48 -41.80 -33.27   2.78  111.45
       Bear_LoVIX   949 -23.15 -21.71  18.55 -23.23 -23.18 -23.02   1.68   63.41
       Bull_HiVIX  1090 -40.82 -36.01   9.91 -35.00 -44.24 -31.06   2.99  112.95
       Bull_LoVIX  2475 -25.45 -22.07  18.38 -36.06 -25.13 -25.76   2.32   59.23
ETF    Bear_HiVIX  1114 -49.14 -45.68   7.81 -40.20 -53.70 -43.73   2.50  168.30
       Bear_LoVIX   935 -32.86 -31.39  15.08 -25.88 -34.72 -27.16   1.50   89.11
       Bull_HiVIX  1047 -50.31 -47.08   5.64 -40.28 -53.30 -45.05   2.55  163.90
       Bull_LoVIX  2921 -36.79 -33.86  13.04 -51.06 -38.11 -35.96   2.08   97.44
```

### sym35: HOLD by entry bid-ask x structure

```
                  n   hold    med    win      t      A      B  debit      ba
struct ba_b                                                                 
DCAL   <=10%     25   9.71   9.11  64.00   1.34  -8.16  16.67   5.61    8.70
       10-25%   430   7.20   4.19  55.35   4.94   5.62   9.88   1.62   19.35
       >25%    5020 -21.95 -20.16  29.62 -35.45 -23.87 -18.60   2.80   83.69
ETF    <=10%      8   6.40   8.29  62.50   0.49    NaN   6.40   9.65    8.46
       10-25%   124   4.21   5.92  57.26   1.49   3.86   4.43   1.66   19.78
       >25%    5904 -29.69 -28.95  24.25 -46.12 -31.78 -27.38   2.50  118.18
```

### sym35 DCAL: HOLD by year

```
        n   hold    med    win      t      A      B  debit      ba
year                                                              
2018  793 -15.76 -16.59  34.43 -10.60 -15.76    NaN   1.75   78.38
2019  830  -9.77  -8.84  38.43  -7.02  -9.77    NaN   1.92   53.79
2020  841 -30.28 -27.82  21.88 -19.02 -30.28    NaN   3.20  111.58
2021  725 -30.83 -28.76  24.69 -18.44 -30.83    NaN   3.05  114.29
2022  606 -19.58 -14.53  33.00 -11.82 -22.41 -17.07   3.56   89.83
2023  582 -11.54 -12.04  36.60  -7.94    NaN -11.54   2.74   52.01
2024  556  -9.55  -9.27  38.67  -5.45    NaN  -9.55   2.96   57.24
2025  485 -24.39 -19.89  29.90 -11.03    NaN -24.39   3.80   75.27
2026   57 -47.52 -44.43  22.81  -5.83    NaN -47.52   4.15  131.71
```

### sym35 ETF: HOLD by year

```
        n   hold    med    win      t      A      B  debit      ba
year                                                              
2018  672 -23.84 -26.03  31.99 -12.96 -23.84    NaN   1.45  113.66
2019  710 -21.91 -21.67  27.04 -14.57 -21.91    NaN   1.64   87.86
2020  719 -36.98 -39.00  16.13 -19.80 -36.98    NaN   2.80  178.38
2021  700 -40.20 -39.45  17.71 -22.28 -40.20    NaN   2.76  157.89
2022  781 -32.58 -31.51  21.90 -20.39 -34.82 -30.88   3.05  142.11
2023  799 -23.33 -22.26  26.66 -15.79    NaN -23.33   2.43   83.72
2024  833 -21.80 -19.78  31.09 -13.36    NaN -21.80   2.65   86.79
2025  723 -29.08 -25.41  28.22 -11.48    NaN -29.08   3.23  115.56
2026   99 -51.66 -52.53  14.14 -11.34    NaN -51.66   4.00  183.67
```

## Generalisation test (step 6, 2026-09-15): 30 high-priced names chosen WITHOUT reference to option activity

BKNG, ORLY, AZO, MELI, ASML, TMO, ISRG, ADBE, ORCL, MA, AMGN, LMT, DE, REGN, VRTX, NOC, TSM, ANET, APP, MCD, ELV, CI,
BLK, SPGI, MCK, TDG, FDX, LIN, HUM, AXON (27 with results). 40,438 sym35 double calendars.

Pooled: **−19.5% / −28.9%** (12/19 / 20/27, ex-earnings) with a median entry bid-ask of **75–115% of the debit** --
price does not buy a tight market; the $1,000 names (BKNG, AZO, MELI, TDG, MCK) have $5–20 wide options. Only 587 of
~12,000 ex-earnings entries (5%, vs 33% in the straddle-pool set) clear the 25%-of-debit gate:

| sym35, ex-earnings, BA ≤ 25% | n | ROC | win | halves | monthly-mean t | years + |
|---|---|---|---|---|---|---|
| 12 / 19 days | 455 | **+7.3%** | 56% | +5.3 / +10.6 | 4.2 (69% months +) | 7 of 8 (2020 −8) |
| 20 / 27 days | 132 | +4.4% | 58% | +3.9 / +4.6 | 0.7 | thin |

Same number as the straddle-pool set (+7.2%), same management verdict (hold; inversion −11pp, drop_far −10pp,
re-center −6pp), and NO sector dependence on the tight cut (financials +10.9, consumer +9.2, tech +8.4, industrials
+7.0; healthcare +1.0, n=55). Names that qualify often enough to trade: MA +11.8, ADBE +10.4, MCD +8.6, AMGN +6.5,
FDX +4.5, ORCL +4.5, TSM +3.7.

**Conclusion for the stock version:** the edge generalises to whatever name has a tight market that Friday; the
gate is the live bid-ask (≤ 25% of the debit, ideally ≤ 10%) plus debit ≥ ~$1.50 and no earnings in the window --
not the sector, not the price, not the pool. Expect ~+7% held, ~56% win, about a third of the index-ETF edge.

## Term structure at entry (2026-09-15 evening): short-leg IV / long-leg IV on the sym35 ETF doubles

Question: does the relationship between the two expiries' IV predict the hold return? Ratio = mean of (short IV / long IV)
on the put side and the call side, from the same bid/ask-IV chain rows the sim priced off. 2,018 IWM/QQQ/SPY sym35 entries.
Median ratio 0.99 (10th pct 0.92, 90th pct 1.04) -- for a 7-day gap the two expiries almost always price within 5% of each
other; a real inversion (>1.10) is 16 entries.

| sym35 HOLD ROC by ratio | 12/19d n | ROC | halves | 20/27d n | ROC | halves |
|---|---|---|---|---|---|---|
| ≤ 0.90 (steep contango, "textbook" calendar entry) | 132 | +3.8% | +0.5 / +4.6 | 10 | +24.8 | thin |
| 0.90–0.97 | 335 | +6.3% | −0.4 / +11.6 | 202 | +12.6 | +6.0 / +20.2 |
| 0.97–1.03 (flat) | 424 | +15.3% | +13.9 / +17.1 | 668 | +20.7 | +16.6 / +24.9 |
| 1.03–1.10 (mild inversion) | 115 | +25.7% | +19.5 / +40.5 | 120 | +20.8 | +21.0 / +20.6 |
| > 1.10 | 12 | +46.4 | thin | 0 | | |

Within-ticker terciles (removes the ticker level): 12/19d low +4.1 / mid +12.1 / high +20.9 (both halves monotone:
+0.3/+10.1/+15.6 and +6.0/+14.3/+30.1); 20/27d low +15.2 / mid +20.5 / high +21.7. Above-1.0 entries beat below-1.0
in 6 of 9 years. Ratio correlates +0.36 with VIX, so part of this is "buy the double when vol is elevated"; the
rest is that a steep front discount means the short leg has little premium to decay relative to what the long leg
bleeds. SPY is the exception (flat across buckets, n small in the tails).

**Reading:** the textbook rule "enter calendars when the front is cheap relative to the back" is inverted here, the
same way the inversion EXIT was the worst rule in the study. Do not avoid a flat or mildly inverted term structure;
if anything it is the better entry. A steep contango (ratio ≤ 0.90) is the one cell to treat as a soft veto on the
12/19 structure (+4% and one half at zero). Not added to the playbook gate yet -- 16 true inversions is too few to
rule on, and the ratio is partly a VIX proxy that the regime cells already carry. Cut data: `dcal_iv_ratio_cut.parquet`.

## Double DIAGONAL vs double calendar (step 7, 2026-09-15 evening): same entries, long legs one step wider

Prompted by the Options With Ravish video (`data/options_with_ravish/`). `run_ddiag_path_sim.py`: identical Friday
entries, expiries and 0.35-delta SHORT strikes as the sym35 doubles on IWM / QQQ / SPY; the long put moves to the
largest long-expiry strike <= Kp x (1 - w) and the long call to the smallest >= Kc x (1 + w), w = 0.5% and 1.0% of
spot (w = 0 is the calendar itself, the paired control). 1,971 paired entry triples. Max risk = cost + wider wing
width (only one wing can be breached at the short expiry); ROC below is on MAX RISK, the fair convention for a
diagonal -- ROC on the debit is meaningless once the structure is near-zero cost or a credit.

| hold | debit | max risk | $ P&L / spread | ROC on max risk | win | halves A / B | breach loss ($, ST > 1% past a short) |
|---|---|---|---|---|---|---|---|
| 12/19d calendar (w=0) | 2.66 | 2.73 | +0.36 | +12.1% | 60% | +9.6 / +14.6 | −0.49 |
| 12/19d diagonal w=0.5% | 1.16 | 3.46 | +0.52 | +14.4% | 63% | +13.0 / +15.7 | −0.42 |
| 12/19d diagonal w=1.0% | 0.19 | 4.19 | +0.65 | +15.6% | 67% | +15.2 / +16.0 | −0.35 |
| 20/27d calendar (w=0) | 1.81 | 1.87 | +0.41 | +19.1% | 60% | +14.8 / +23.4 | |
| 20/27d diagonal w=0.5% | 0.36 | 2.69 | +0.60 | +20.9% | 68% | +16.4 / +25.2 | |
| 20/27d diagonal w=1.0% | −0.61 (credit) | 3.45 | +0.79 | +22.5% | 72% | +19.1 / +25.9 | |

Paired on the same entries: w=1.0% beats the calendar by $0.33/spread (t = 19.6), better in 72% of entries; w=0.5%
by $0.18 (t = 16.1), 69%. Better on all three tickers (IWM 15→20 / 26→30, QQQ 14→18 / 20→24, SPY 7→9 / 12→14), in
every regime cell except 20/27d Bear_HiVIX (32 → 30, flat), in 8 of 9 years (2019, the calendar's losing year, goes
−6 → +2 and −11 → +2). Tail: worst 5% is −51% of max risk vs −74% for the calendar (in dollars −2.00 vs −1.61, on a
max risk 1.5x larger); the worst single trade is smaller in dollars. The vega claim holds: when VIX fell > 3 points
over the trade the calendar made +0.2 / +6.0% and the diagonal +5.7 / +12.6%; when VIX rose 0.5–3 the calendar is
1–4pp better. Management: pt25 still −3 to −7pp, stops ~0, hold still wins.

**Reading:** widening the longs one step is a straight improvement on these three ETFs -- more dollars per spread,
higher ROC on a fairly measured risk, higher win rate, smaller breach losses, and the weak-year / falling-VIX cells
are where it helps most. The cost is a bigger max risk per spread (4.19 vs 2.73 on 12/19d), which is what the ROC
already divides by. Not yet checked: stocks (the tight-market cut), w beyond 1%, and whether the wider long strikes
stay ≤ 25% bid-ask on thinner names. Results: `results_ddiag.parquet`.

**Proposal for `double_calendar_playbook.md`:** long legs 1% of spot wider than the shorts on IWM / QQQ / SPY
(double diagonal), size on max risk = net debit + wing width, everything else unchanged (hold to short expiry, every
regime, bid-ask gate on the four legs).

## Earnings position (2026-09-15 evening, prompted by the tastylive "double calendar vs iron condor" segment)

The blanket "no earnings inside (entry, long expiry]" stock rule (−3pp pooled) was a wide-market artefact. On the
tight cut (BA ≤ 25%, sym35, 90 names, hold) split by WHERE the earnings date falls:

| earnings | 12/19d n | ROC | win | A / B | 20/27d n | ROC | win | A / B |
|---|---|---|---|---|---|---|---|---|
| before the short expiry | 311 | +1.4% | 50% | +1.2 / +1.7 | 178 | +10.4% | 60% | +12.5 / +9.5 |
| between short and long expiry | 851 | +10.4% | 66% | +8.4 / +13.0 | 540 | +15.1% | 66% | +9.6 / +19.1 |
| none | 4,839 | +7.2% | 58% | +6.1 / +8.7 | 2,262 | +7.4% | 56% | +6.8 / +7.8 |

"Between" is positive every year 2018–2026 (+4 to +19), 3–4 days from short expiry to the event beats 5–7 (+15.1 vs
+10.9, n=453 / 931); hold beats pt25/pt50/stop40/drop_far in every cell. Mechanism: the short decays into a rising
pre-event IV and the long is sold at the IV peak; the tastylive placement (short absorbs the crush) puts the crush on
the long leg too and its extra front premium is what the bid-ask eats. **Proposal for the stock rule: allow (prefer)
earnings between the expiries; avoid earnings before the short expiry on 12/19d.** Not applied to the playbook yet.

### Step 7b: the double diagonal on stocks (2026-09-15, `run_ddiag_path_sim.py --universe-file ...`)

Same paired design on the 60-name straddle pool and the 30-name generalisation set, tight cut defined on the
same-strike calendar row (BA ≤ 25% of debit, ex-earnings) so the three widths are compared on identical entries.
ROC on max risk.

| set | structure | calendar | diagonal 0.5% | diagonal 1.0% | win (cal → 1%) | halves (1%) | paired $ / t | better in |
|---|---|---|---|---|---|---|---|---|
| 60 stocks | 12/19d, n=3,094 | +6.5% | +9.4% | **+9.9%** | 57 → 66% | +9.5 / +10.4 | +$0.17 / 12.0 | 72% |
| 60 stocks | 20/27d, n=1,565 | +6.3% | +9.7% | **+10.1%** | 55 → 63% | +7.4 / +11.8 | | |
| 30 stocks | 12/19d, n=455 | +7.3% | +9.5% | **+9.8%** | 56 → 65% | +8.3 / +11.8 | +$0.17 / 10.1 | 71% |
| 30 stocks | 20/27d, n=131 | +4.5% | +7.6% | **+7.8%** | 58 → 63% | +7.0 / +8.2 | | |

By year: 60-set 8 of 9 years ≥ the calendar (2018 the exception, both > +16%); 30-set 8 of 8. By ticker: the lift
comes from the middle and bottom of the roster (PLTR −1 → +5, BAC −7 → +3, INTC +1 → +8, CVX 0 → +8, QCOM +7 → +11;
30-set FDX +4 → +8, ORCL +3 → +7, TSM +7 → +11) while the top mega-caps are flat (TSLA / META / GOOG ~+15 either
way, ADBE / MA +12). It does not rescue AAL (−13 → −4) or ANET / CVX-type wide names outside the cut.

**Gate note:** the diagonal's own bid-ask cannot be expressed as % of debit (debit → 0 or a credit), so the stock
gate stays defined on the SAME-STRIKE calendar's four-leg bid-ask (≤ 25% of its debit) or on max risk; use the
calendar quote as the liquidity test, then place the diagonal.

**Conclusion:** the 1% diagonal is a straight improvement on stocks as well as ETFs: +3 to +3.5pp ROC on max risk,
+8-10pp win rate, more dollars per spread, both halves, both universes, nearly every year. The stock playbook entry
(queued screener build) should be the diagonal, sized on max risk, with the calendar-quote liquidity gate.
