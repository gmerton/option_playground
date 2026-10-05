# Long straddles: early exit vs hold to expiry, size-neutral (2026-10-04 19:08)

P&L as % of premium paid; hold = original legs settled at intrinsic on expiry (commissions ignored on the hold side).

## SYSTEMATIC (straddle screener): 55 closed straddles, 2026-08-07 → 2026-09-25

- **Dollars (what the page shows):** realized +1,408 vs hold-to-expiry -4,486 → early exits +5,894; total premium 27,293
- **Per $1,000 of premium:** early exit +52 vs hold -164
- **Equal-weighted (size-neutral):** early exit mean -6.8% (median -13.8%) vs hold mean -16.8% (median -44.0%)
- **Paired early − hold:** +9.9pp per trade, t 1.20 (clustered by entry date, 28 dates), n 55; early exit better on 55% of trades
- win rate: early exit 45% vs hold 29%; hold lost ≥ 75% of premium on 24%
- size check: corr(premium, early − hold) +0.23; dollar-weighted gap +21.6% of premium vs equal-weighted +9.9pp

By position size (premium quartile; mean % of premium):

              n   prem  exit  hold  diff
prem                                    
Q1 smallest  14  212.5 -22.4  -3.9 -18.5
Q2           14  323.0 -27.4 -45.5  18.2
Q3           13  445.0   6.8  10.6  -3.9
Q4 largest   14  946.5  16.6 -26.3  42.9

- where holding would have WON (n 16): early exit +40.0% vs hold +96.5% (early exit gave up -56.5pp)
- where holding would have LOST (n 39): early exit -26.1% vs hold -63.2% (early exit saved +37.2pp)

## DISCRETIONARY: 3 closed straddles, 2026-09-17 → 2026-09-21

- **Dollars (what the page shows):** realized +663 vs hold-to-expiry +1,628 → early exits -965; total premium 1,617
- **Per $1,000 of premium:** early exit +410 vs hold +1,007
- **Equal-weighted (size-neutral):** early exit mean +37.6% (median +51.5%) vs hold mean +67.6% (median +72.0%)
- **Paired early − hold:** -30.1pp per trade, t -1.36 (clustered by entry date, 2 dates), n 3; early exit better on 67% of trades
- win rate: early exit 67% vs hold 67%; hold lost ≥ 75% of premium on 0%
- size check: corr(premium, early − hold) -1.00; dollar-weighted gap -59.7% of premium vs equal-weighted -30.1pp

- where holding would have WON (n 2): early exit +66.3% vs hold +112.8% (early exit gave up -46.6pp)
- where holding would have LOST (n 1): early exit -19.8% vs hold -22.8% (early exit saved +3.0pp)

## ALL: 58 closed straddles, 2026-08-07 → 2026-09-25

- **Dollars (what the page shows):** realized +2,071 vs hold-to-expiry -2,858 → early exits +4,928; total premium 28,910
- **Per $1,000 of premium:** early exit +72 vs hold -99
- **Equal-weighted (size-neutral):** early exit mean -4.5% (median -8.3%) vs hold mean -12.4% (median -41.6%)
- **Paired early − hold:** +7.8pp per trade, t 0.91 (clustered by entry date, 28 dates), n 58; early exit better on 55% of trades
- win rate: early exit 47% vs hold 31%; hold lost ≥ 75% of premium on 22%
- size check: corr(premium, early − hold) +0.18; dollar-weighted gap +17.0% of premium vs equal-weighted +7.8pp

By position size (premium quartile; mean % of premium):

              n   prem  exit  hold  diff
prem                                    
Q1 smallest  15  214.0 -24.6 -10.2 -14.5
Q2           14  323.0 -17.0 -33.2  16.2
Q3           14  436.5   4.3   8.1  -3.8
Q4 largest   15  948.0  18.9 -14.3  33.2

- where holding would have WON (n 18): early exit +42.9% vs hold +98.3% (early exit gave up -55.4pp)
- where holding would have LOST (n 40): early exit -25.9% vs hold -62.2% (early exit saved +36.3pp)

## Trades

  tk      entry       exit  system   prem  realized    hold  exit_pct  hold_pct  diff_pct
 HPQ 2026-08-07 2026-08-14    True  445.0     -12.9    95.0      -2.9      21.3     -24.3
 PCG 2026-08-07 2026-08-31    True  211.0     196.6   164.7      93.2      78.0      15.2
ACHR 2026-08-11 2026-08-21    True  267.0     -78.2   -57.0     -29.3     -21.3      -8.0
 CVS 2026-08-11 2026-08-17    True  330.0    -100.8  -232.0     -30.5     -70.3      39.8
 BAC 2026-08-12 2026-08-20    True  294.0      85.1   430.6      28.9     146.5    -117.5
 NVO 2026-08-12 2026-08-19    True  382.0    -171.5  -234.0     -44.9     -61.3      16.4
RDDT 2026-08-12 2026-08-14    True 1062.0    1622.2  -983.0     152.7     -92.6     245.3
ETHA 2026-08-14 2026-08-21    True  240.0     541.3  1456.0     225.5     606.7    -381.1
QUBT 2026-08-14 2026-08-20    True  284.0      51.7  -252.0      18.2     -88.7     106.9
BBAI 2026-08-17 2026-08-20    True  330.0    -123.2  -280.0     -37.3     -84.8      47.5
 CLF 2026-08-18 2026-08-27    True   95.0    -109.2  -114.0    -114.9    -120.0       5.1
 WFC 2026-08-19 2026-08-28    True  260.0    -191.8  -191.0     -73.8     -73.5      -0.3
PLTR 2026-08-20 2026-08-27    True  973.0     -17.8   156.0      -1.8      16.0     -17.9
RDDT 2026-08-21 2026-08-25    True  948.0      59.2  -898.0       6.2     -94.7     101.0
  NU 2026-08-24 2026-08-31    True  498.0    -179.5  -276.0     -36.0     -55.4      19.4
QUBT 2026-08-24 2026-09-01    True  276.0    -155.2  -273.0     -56.2     -98.9      42.7
ACHR 2026-08-25 2026-09-03    True  290.0    -188.3  -145.0     -64.9     -50.0     -14.9
APLD 2026-08-25 2026-09-04    True  344.0    -134.4  -131.0     -39.1     -38.1      -1.0
 AIG 2026-08-26 2026-09-03    True  217.0    -135.9   -87.8     -62.6     -40.5     -22.2
PLTR 2026-08-26 2026-08-28    True 1083.0     228.2 -1016.0      21.1     -93.8     114.9
 CVS 2026-08-27 2026-08-28    True  377.0    -104.2   -95.0     -27.6     -25.2      -2.4
 TPR 2026-08-27 2026-09-04    True  511.0    -322.9  -225.0     -63.2     -44.0     -19.2
BBAI 2026-08-31 2026-09-08    True  300.0    -178.3  -170.0     -59.4     -56.7      -2.8
  NU 2026-08-31 2026-09-10    True  222.0       6.8  -247.0       3.1    -111.3     114.3
PLTR 2026-08-31 2026-09-03    True 1130.0    1050.5   647.0      93.0      57.3      35.7
 ELF 2026-09-01 2026-09-04    True  703.0    -218.5   506.0     -31.1      72.0    -103.1
 GAP 2026-09-01 2026-09-10    True  198.0      22.4  -100.0      11.3     -50.5      61.8
 IBM 2026-09-02 2026-09-04    True  856.0    -118.1   223.0     -13.8      26.1     -39.8
CSCO 2026-09-02 2026-09-04    True  383.0    -154.8   -70.0     -40.4     -18.3     -22.2
 BAC 2026-09-03 2026-09-10    True  157.0     -73.5   -88.0     -46.8     -56.1       9.3
 GAP 2026-09-08 2026-09-10    True  484.0     148.4   300.0      30.7      62.0     -31.3
QBTS 2026-09-08 2026-09-16    True  376.0      45.5  -198.0      12.1     -52.7      64.8
 NNE 2026-09-09 2026-09-18    True  409.0     224.2   245.0      54.8      59.9      -5.1
EBAY 2026-09-10 2026-09-18    True  428.0     278.0   256.0      65.0      59.8       5.2
 GAP 2026-09-10 2026-09-16    True  400.0      52.7  -216.0      13.2     -54.0      67.2
SRPT 2026-09-11 2026-09-17    True  198.0    -180.6  -315.0     -91.2    -159.1      67.9
PLTR 2026-09-14 2026-09-17    True 1132.0     122.5  1085.0      10.8      95.8     -85.0
UBER 2026-09-14 2026-09-25    True  364.0    -202.1  -226.0     -55.5     -62.1       6.6
ASTS 2026-09-15 2026-09-25    True  572.0      39.1  -291.0       6.8     -50.9      57.7
 WMT 2026-09-16 2026-09-24    True  316.0    -195.5  -314.0     -61.9     -99.4      37.5
TTWO 2026-09-17 2026-09-23    True  945.0    -395.9   -89.0     -41.9      -9.4     -32.5
TQQQ 2026-09-17 2026-09-21    True  386.0     260.2   474.0      67.4     122.8     -55.4
NFLX 2026-09-17 2026-09-18   False  282.0     228.5   203.0      81.0      72.0       9.1
COHR 2026-09-17 2026-09-18   False  980.0     504.4  1506.0      51.5     153.7    -102.2
 GAP 2026-09-17 2026-09-25    True  288.0    -122.4   -42.0     -42.5     -14.6     -27.9
PLTR 2026-09-18 2026-09-22    True  895.0     152.2   572.0      17.0      63.9     -46.9
RDDT 2026-09-18 2026-09-21    True  917.0      21.2  -651.0       2.3     -71.0      73.3
 FDX 2026-09-21 2026-09-24    True 1199.0     120.2  -735.0      10.0     -61.3      71.3
 WMT 2026-09-21 2026-10-02   False  355.0     -70.4   -81.0     -19.8     -22.8       3.0
PLTR 2026-09-25 2026-10-01    True  943.0    -560.5  -818.0     -59.4     -86.7      27.3
TTWO 2026-09-25 2026-10-01    True  775.0     225.6  -752.0      29.1     -97.0     126.1
NVDA 2026-09-25 2026-10-02    True  721.0     494.5   174.0      68.6      24.1      44.5
UBER 2026-09-25 2026-10-02    True  238.0     -53.2   -49.0     -22.3     -20.6      -1.7
 GAP 2026-09-25 2026-09-28    True  356.0     116.3  -152.0      32.7     -42.7      75.4
CELH 2026-09-25 2026-10-02    True  140.0     -88.1   -45.0     -62.9     -32.1     -30.8
AAPL 2026-09-25 2026-09-29    True  793.0      57.2  -162.0       7.2     -20.4      27.6
LUNR 2026-09-25 2026-10-02    True  138.0    -106.8  -118.0     -77.4     -85.5       8.1
USAR 2026-09-25 2026-10-02    True  214.0    -139.7    68.0     -65.3      31.8     -97.1

## Checks (2026-10-04)
- Contracts per straddle: 1 on 47 of 58 trades (2-6 on the rest), so most "size" differences are the OPTION PRICE (higher-priced / higher-IV underlyings), not a sizing decision.
- Concentration: the top 3 trades supply $4,827 of the systematic book's +$5,894 early-exit advantage (RDDT 8/12 +$2,605, PLTR 8/26, FDX 9/21 region). Without RDDT 8/12 the equal-weighted gap is +5.6pp.

## Exit-rule test NOT queued (2026-10-04) + entry-weekday conformance
- A "close at −40%, hold winners" rule is the −50% stop already measured on the full 2018-26 gated sample (TEST_INDEX §2 row 30 / straddle_recenter): stop REMOVED, −3.84pp on the book, −9.51pp on the breach cohort, 69.8% of breaches better held. Not re-tested (only-new-ideas rule).
- Conformance (descriptive): only 17 of 55 systematic entries were on a FRIDAY (Mon 9, Tue 10, Wed 10, Thu 9). The playbook enters Fridays only (tenor study 2026-09-21: Mon-Thu entries 5.7-8.5pp worse than Friday on the same name and expiry).
  Hold-to-expiry: Friday entries +1.6% mean (median −32.1%, n 17) vs Mon-Thu −25.0% (median −50.3%, n 38). Early exits: Friday +7.0% vs Mon-Thu −13.0%. Small samples, but the gap is the size the tenor study predicts.
