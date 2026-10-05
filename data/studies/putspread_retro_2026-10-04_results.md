# Put spreads vs the same delta in stock (2026-10-04 19:28)

47 put-spread campaigns on the card; 31 closed and scored (16 open, not scored). Entries 2026-08-03 → 2026-09-28; median hold 7 days; median position delta 10 shares.

| per trade, % of max risk | mean | median | win |
|---|---|---|---|
| put spread (realized) | +29.7% | +13.7% | 68% |
| same delta in the stock | +10.3% | +6.5% | 61% |
| same dollar delta in SPY | -0.1% | +0.0% | 42% |

- **spread − delta-matched stock: +19.5pp per trade, t 1.64** (clustered by entry date, n 31); spread better on 48%
- spread − SPY at the same dollar delta: +29.8pp, t 2.10
- dollars: spreads +2,086 vs delta-matched stock +1,316 vs SPY +180; total max risk 18,896
- when the stock FELL over the hold (n 11): spread -14.2% vs stock -26.1%; when it ROSE (n 20): spread +53.9% vs stock +30.2%

⚠ Delta is backed out of fill prices with Black-Scholes (r 4%, no dividends); underlying = the fill-minute bar when cached, else the day's close. Two months, one up-trending tape.

## Trades

   tk      entry       exit     expiry  contracts  credit  max_risk  delta_sh  realized  stock   spy  spread_pct  stock_pct
  TLT 2026-08-03 2026-08-25 2026-09-18        2.0   153.0     847.0      59.1     112.7   75.6  52.8        13.3        8.9
  GLD 2026-08-10 2026-08-17 2026-08-28        1.0   477.0     173.0      25.0     250.0   73.9  -4.7       144.5       42.7
 COHR 2026-08-11 2026-08-17 2026-09-18        1.0   320.0     680.0       3.7      93.4   89.7   3.3        13.7       13.2
 ALAB 2026-08-12 2026-09-21 2026-09-18        1.0   168.0     832.0       2.7     347.5   31.5   1.2        41.8        3.8
 CBRS 2026-08-12 2026-08-20 2026-10-16        1.0   346.0     654.0       3.2    -181.6 -142.9 -10.5       -27.8      -21.8
 AAOI 2026-08-14 2026-08-17 2026-08-21        1.0   170.0    1630.0      12.6     112.8   72.8  -8.9         6.9        4.5
 AAOI 2026-08-18 2026-08-25 2026-09-18        1.0   514.0     486.0      15.4    -402.9 -318.0  -4.1       -82.9      -65.4
 NVDA 2026-08-25 2026-08-26 2026-10-16        1.0   215.0     785.0       9.1     -37.8  -23.7   0.4        -4.8       -3.0
 MRVL 2026-08-26 2026-08-27 2026-08-28        1.0  -226.0     226.0      -6.2      17.5   14.7  -9.8         7.7        6.5
 CBRS 2026-08-27 2026-09-04 2026-09-18        1.0   215.0     785.0       9.1     388.0  254.6  -1.9        49.4       32.4
 COHR 2026-08-27 2026-09-10 2026-09-18        1.0   226.0     774.0       5.8     127.1    3.0 -29.0        16.4        0.4
  HUT 2026-08-27 2026-08-27 2026-09-18        1.0   332.0     168.0      18.3     -11.2    0.0   0.0        -6.7        0.0
 COHR 2026-08-28 2026-09-21 2026-10-02        1.0   324.0     676.0       5.6     281.0  196.1   8.7        41.6       29.0
 CRWD 2026-08-28 2026-09-11 2026-09-18        1.0   179.0     821.0       9.8     176.8 -106.0 -14.0        21.5      -12.9
 INTU 2026-08-31 2026-09-08 2026-10-16        1.0   272.0     728.0       5.5    -344.0 -225.3  -2.8       -47.3      -30.9
 PLTR 2026-08-31 2026-09-02 2026-09-18        1.0   200.0     800.0      14.5    -378.5 -254.7  -6.7       -47.3      -31.8
 QCOM 2026-08-31 2026-09-15 2026-10-16        1.0   241.0     759.0      11.8     173.5  233.2 -24.9        22.9       30.7
  XLE 2026-08-31 2026-09-18 2026-09-18        3.0   230.0      70.0      88.8     332.6   61.3 -39.5       475.2       87.6
   CF 2026-09-01 2026-09-18 2026-09-18        2.0   204.0     196.0      24.3     201.4 -119.0  -0.4       102.7      -60.7
 COHR 2026-09-03 2026-09-03 2026-09-18        1.0   177.0     823.0       7.0     -20.6  -18.5   0.0        -2.5       -2.2
 CRWD 2026-09-03 2026-09-14 2026-09-18        1.0   126.0     874.0       9.2      96.5  199.4 -31.1        11.0       22.8
  GLW 2026-09-04        NaT 2026-10-16        1.0   167.0     833.0       8.2     107.5    NaN   NaN         NaN        NaN
  QQQ 2026-09-14 2026-09-17 2026-10-02        1.0   229.0     471.0       8.4      21.5   39.6  13.5         4.6        8.4
 DELL 2026-09-16        NaT 2026-10-16        1.0   219.0     781.0       2.9       0.0    NaN   NaN         NaN        NaN
 DINO 2026-09-16        NaT 2026-10-16        1.0   186.0     314.0      14.5       0.0    NaN   NaN         NaN        NaN
 MSFT 2026-09-16 2026-09-29 2026-10-16        1.0   256.0     744.0       8.6     175.5  165.2  56.9        23.6       22.2
 TWST 2026-09-16 2026-09-17 2026-10-16        1.0   321.0     679.0      11.8     120.1  146.9  19.1        17.7       21.6
  USO 2026-09-16 2026-09-21 2026-10-16        1.0   283.0     217.0      13.9    -135.9 -111.6  56.1       -62.6      -51.4
  GLW 2026-09-17        NaT 2026-10-09        1.0   287.0     213.0      16.1     167.5    NaN   NaN         NaN        NaN
 MRVL 2026-09-17        NaT 2026-10-30        1.0   275.0     725.0       6.0       0.0    NaN   NaN         NaN        NaN
 MSTR 2026-09-17 2026-09-18 2026-10-16        1.0   254.0     746.0      12.7     137.2  294.1  -2.0        18.4       39.4
 NBIS 2026-09-17 2026-09-29 2026-10-16        1.0   256.0     244.0       6.7     195.8  159.2   3.0        80.3       65.2
  QQQ 2026-09-17 2026-09-22 2026-10-02        1.0   247.0     553.0      11.1     199.5  343.4 112.8        36.1       62.1
 CRWD 2026-09-18 2026-09-29 2026-10-16        2.0   272.0     228.0      10.0     174.8  250.7   7.8        76.7      109.9
 PANW 2026-09-18        NaT 2026-10-16        1.0   304.0     696.0       6.8     107.2    NaN   NaN         NaN        NaN
  XOP 2026-09-18 2026-09-21 2026-10-16        1.0   173.0     527.0      11.8     -68.8  -69.2  34.9       -13.1      -13.1
 ASTS 2026-09-22        NaT 2026-10-30        1.0   304.0     196.0      21.2       0.0    NaN   NaN         NaN        NaN
 COHR 2026-09-23        NaT 2026-10-30        1.0   275.0     725.0       5.0       0.0    NaN   NaN         NaN        NaN
 AAPL 2026-09-24        NaT 2026-10-23        1.0   180.0     820.0      12.1       0.0    NaN   NaN         NaN        NaN
 OKTA 2026-09-25        NaT 2026-10-16        1.0   330.0     670.0      13.8       0.0    NaN   NaN         NaN        NaN
 CBRS 2026-09-28 2026-09-28 2026-10-30        1.0   300.0     700.0       8.9     -68.6    0.0   0.0        -9.8        0.0
   GH 2026-09-28        NaT 2026-10-16        1.0   178.0     822.0      12.4       0.0    NaN   NaN         NaN        NaN
GOOGL 2026-09-28        NaT 2026-10-23        1.0   243.0     757.0      11.4       0.0    NaN   NaN         NaN        NaN
  BBY 2026-09-29        NaT 2026-10-16        1.0    86.0     314.0      14.4       0.0    NaN   NaN         NaN        NaN
   KO 2026-09-29        NaT 2026-10-16        1.0   209.0      -9.0      82.6       0.0    NaN   NaN         NaN        NaN
  MRK 2026-09-29        NaT 2026-10-16        1.0   338.0     262.0      34.1       0.0    NaN   NaN         NaN        NaN
  XOM 2026-09-29        NaT 2026-10-16        1.0   184.0     316.0      24.5       0.0    NaN   NaN         NaN        NaN

## Robustness (post hoc, disclosed): 4 rows with impossible economics excluded
ALAB 08-12, MRVL 08-26 (a debit structure), CBRS 08-27, XLE 08-31: realized above the credit or below −max risk, i.e. rolls or several structures merged in one campaign, so their "% of max risk" is meaningless. On the 27 clean trades:
- spread +12.9% of max risk (median +13.3%) vs delta-matched stock +7.0% (median +4.5%); **difference +5.9pp, t 0.72, median −3.8pp, spread better on 41%**
- dollars: spreads +$1,000 vs delta-matched stock +$954
- stock fell (n 10): spread −16.4% vs stock −29.3%; stock rose (n 17): spread +30.1% vs stock +28.3%
