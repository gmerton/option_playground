# 1-DTE long ATM straddle -- the COHR trade, generalized

_Run 2026-09-19. 152,995 trades, 1,645 names, 2019-01-03 to 2026-02-19; real bid/ask from `silver.options_daily_v3`, exits settled from the underlying, costs = IBKR commission + 25% of the entry bid/ask per traded side. Return = P&L / premium paid. Hurdle: 0DTE long strangle base rate -26%/trade._

**Trade:** buy the ATM straddle at the ask at the close before expiry. **Exits:** `open` = sell the winning leg at intrinsic at the expiry-day open; `extreme` = same at the day's best extreme (upper bound); `close` = settle. **Gate:** `ratio_max` = largest |close/close| move in the prior 5 sessions / implied move (straddle mid / spot).

`open @intrinsic` sells the winning leg at intrinsic at 09:30 (ignores the session's remaining time value -- a floor). `open @fair value` sells BOTH legs at a Black-Scholes price with 75% of the day's implied variance still ahead (the realistic morning sale). `open win%` and `open>close` use the intrinsic arm.

## 1. Base rate and the realized/implied gate (ratio_max buckets)

| cut | n | open @intrinsic | open @fair value | extreme exit | close exit | open win% | open>close | med implied |
|---|---|---|---|---|---|---|---|---|
| ALL | 152,995 | -72.0% (t -79.5) | -30.2% (t -37.4) | +9.6% (t +7.2) | -30.3% (t -26.9) | 5% | 29% | 1.8% |
| ratio_max <1.0 | 22,051 | -79.4% (t -56.7) | -41.3% (t -26.4) | -14.6% (t -6.1) | -44.0% (t -26.2) | 5% | 31% | 2.3% |
| ratio_max 1.0-1.5 | 36,763 | -73.7% (t -78.3) | -32.4% (t -36.0) | +5.4% (t +3.8) | -32.7% (t -28.2) | 4% | 29% | 1.8% |
| ratio_max 1.5-2.0 | 37,968 | -70.6% (t -75.5) | -28.1% (t -39.2) | +13.3% (t +9.8) | -27.9% (t -20.3) | 5% | 28% | 1.8% |
| ratio_max 2.0-3.0 | 39,437 | -69.0% (t -68.0) | -26.1% (t -34.8) | +17.4% (t +13.2) | -26.2% (t -21.5) | 5% | 29% | 1.8% |
| ratio_max >=3.0 | 16,485 | -68.8% (t -68.8) | -25.4% (t -38.4) | +22.8% (t +14.7) | -23.0% (t -16.4) | 5% | 28% | 1.8% |

By `ratio_mean` (5-day MEAN move / implied):

| cut | n | open @intrinsic | open @fair value | extreme exit | close exit | open win% | open>close | med implied |
|---|---|---|---|---|---|---|---|---|
| ratio_mean <1.0 | 97,992 | -73.9% (t -77.5) | -32.8% (t -35.2) | +4.0% (t +2.7) | -33.4% (t -28.3) | 5% | 29% | 1.9% |
| ratio_mean 1.0-1.5 | 43,279 | -68.5% (t -68.5) | -25.6% (t -36.7) | +18.2% (t +14.2) | -25.6% (t -21.5) | 5% | 29% | 1.8% |
| ratio_mean 1.5-2.0 | 8,904 | -68.8% (t -58.1) | -25.6% (t -28.9) | +21.3% (t +11.3) | -24.7% (t -14.5) | 5% | 28% | 1.8% |
| ratio_mean 2.0-3.0 | 2,256 | -69.3% (t -48.2) | -25.7% (t -26.1) | +28.0% (t +14.5) | -19.2% (t -10.1) | 5% | 26% | 1.7% |
| ratio_mean >=3.0 | 273 | -72.5% (t -37.4) | -25.9% (t -16.0) | +40.8% (t +8.6) | -8.0% (t -1.6) | 3% | 20% | 1.8% |

## 2. The gated trade by year (ratio_max >= 2.0) -- 2020 and 2022 must appear

| cut | n | open @intrinsic | open @fair value | extreme exit | close exit | open win% | open>close | med implied |
|---|---|---|---|---|---|---|---|---|
| 2019 | 6,541 | -66.6% (t -30.2) | -23.7% (t -25.7) | +25.3% (t +14.9) | -20.4% (t -11.2) | 6% | 27% | 1.3% |
| 2020 | 7,781 | -63.9% (t -14.9) | -24.2% (t -7.8) | +21.0% (t +4.0) | -25.8% (t -6.5) | 8% | 31% | 2.1% |
| 2021 | 7,852 | -69.3% (t -59.6) | -26.2% (t -36.4) | +19.4% (t +8.2) | -26.6% (t -13.2) | 5% | 28% | 1.6% |
| 2022 | 8,056 | -70.3% (t -32.1) | -27.1% (t -22.8) | +19.4% (t +7.1) | -20.5% (t -5.2) | 4% | 26% | 2.2% |
| 2023 | 7,604 | -66.9% (t -32.6) | -23.2% (t -22.0) | +19.3% (t +8.2) | -26.1% (t -10.4) | 6% | 30% | 1.7% |
| 2024 | 8,507 | -69.9% (t -105.8) | -24.1% (t -31.2) | +19.9% (t +11.8) | -26.5% (t -13.8) | 4% | 28% | 1.6% |
| 2025 | 8,270 | -72.4% (t -32.7) | -29.2% (t -17.3) | +13.6% (t +3.3) | -28.1% (t -8.7) | 5% | 28% | 2.0% |
| 2026 | 1,311 | -84.7% (t -88.2) | -44.8% (t -22.8) | -2.6% (t -1.0) | -37.6% (t -25.0) | 3% | 24% | 2.3% |
| half 1 | 27,932 | -68.1% (t -45.7) | -25.6% (t -25.9) | +21.0% (t +11.8) | -23.4% (t -14.9) | 6% | 28% | 1.7% |
| half 2 | 27,990 | -69.9% (t -61.3) | -26.2% (t -27.2) | +17.0% (t +9.5) | -27.2% (t -16.8) | 5% | 29% | 1.8% |

Ungated, by year:

| cut | n | open @intrinsic | open @fair value | extreme exit | close exit | open win% | open>close | med implied |
|---|---|---|---|---|---|---|---|---|
| 2019 | 17,098 | -66.5% (t -38.7) | -24.7% (t -29.5) | +22.5% (t +9.1) | -21.0% (t -8.0) | 6% | 27% | 1.3% |
| 2020 | 20,309 | -67.6% (t -20.3) | -27.8% (t -12.1) | +10.7% (t +2.4) | -31.3% (t -9.5) | 7% | 31% | 2.1% |
| 2021 | 21,317 | -73.7% (t -54.7) | -32.0% (t -34.0) | +8.1% (t +3.7) | -32.7% (t -19.7) | 4% | 28% | 1.7% |
| 2022 | 23,035 | -74.9% (t -33.2) | -34.2% (t -24.2) | +4.9% (t +2.0) | -29.3% (t -8.7) | 4% | 27% | 2.3% |
| 2023 | 21,822 | -70.6% (t -40.8) | -28.1% (t -25.3) | +10.1% (t +4.2) | -30.6% (t -11.2) | 5% | 30% | 1.7% |
| 2024 | 22,686 | -70.3% (t -108.6) | -25.9% (t -37.8) | +12.9% (t +8.7) | -30.0% (t -17.9) | 5% | 29% | 1.6% |
| 2025 | 23,100 | -75.5% (t -28.1) | -33.8% (t -11.8) | +5.3% (t +1.2) | -32.4% (t -9.4) | 5% | 29% | 2.1% |
| 2026 | 3,628 | -88.7% (t -679.3) | -50.5% (t -90.1) | -15.8% (t -23.3) | -45.7% (t -76.7) | 2% | 26% | 2.5% |

## 3. Expiry weekday (Fri = weeklies; Mon/Wed = index/ETF and mega-cap dailies)

| cut | n | open @intrinsic | open @fair value | extreme exit | close exit | open win% | open>close | med implied |
|---|---|---|---|---|---|---|---|---|
| Fri | 146,302 | -72.0% (t -76.3) | -30.4% (t -36.0) | +9.7% (t +6.8) | -30.1% (t -25.2) | 5% | 29% | 1.8% |
| Thu | 5,431 | -74.7% (t -18.6) | -31.3% (t -8.0) | +1.2% (t +0.2) | -39.7% (t -8.8) | 5% | 31% | 1.8% |
| Tue | 397 | -52.8% (t -23.7) | -2.3% (t -1.8) | +35.4% (t +8.6) | -11.1% (t -2.7) | 10% | 29% | 0.7% |
| Wed | 865 | -52.0% (t -23.3) | -1.6% (t -1.5) | +37.7% (t +10.8) | -9.0% (t -2.2) | 13% | 27% | 0.9% |

## 4. Liquidity cut (both legs' bid/ask as % of the straddle mid)

| cut | n | open @intrinsic | open @fair value | extreme exit | close exit | open win% | open>close | med implied |
|---|---|---|---|---|---|---|---|---|
| bid/ask <5% | 10,768 | -49.5% (t -52.4) | -1.7% (t -3.1) | +41.1% (t +28.1) | -6.8% (t -4.2) | 12% | 29% | 1.6% |
| bid/ask 5-10% | 20,084 | -57.0% (t -54.2) | -8.9% (t -16.1) | +36.9% (t +25.6) | -12.3% (t -8.5) | 9% | 28% | 1.8% |
| bid/ask 10-20% | 37,224 | -62.4% (t -71.2) | -16.1% (t -36.2) | +29.9% (t +23.8) | -17.5% (t -12.8) | 6% | 28% | 1.7% |
| bid/ask >20% | 84,919 | -82.5% (t -98.3) | -45.0% (t -60.3) | -9.8% (t -7.2) | -43.1% (t -40.3) | 3% | 29% | 1.9% |
| bid/ask <10% AND ratio_max >= 2 | 12,698 | -56.4% (t -50.1) | -7.4% (t -12.1) | +39.0% (t +26.4) | -12.0% (t -7.7) | 9% | 29% | 1.7% |
| bid/ask <10% AND ratio_max >= 3 | 3,893 | -57.5% (t -45.2) | -8.1% (t -11.7) | +42.5% (t +21.7) | -9.2% (t -4.6) | 8% | 28% | 1.8% |

## 5. Where the P&L lives (gated, ratio_max >= 2, open @fair value, net)

- n 55,922; mean -25.9%, median -25.7%, p10 -56.0%, p90 -0.3%, max +1083%
- positive sum is zero or negative
- ex top 1%: mean -27.4%
- largest expiry-day moves included (no truncation): GME 2021-01-22 +51%, QBTS 2025-03-14 +47%, IBRX 2026-01-16 +40%, SMMT 2025-04-25 +36%, SRPT 2025-07-18 +36%

## 6. The mean-reversion claim: is the morning move bigger than the close-to-close move?

Share of expiry days with |open - K| > |close - K|, and the mean of each, by gate bucket (trade set):

| bucket | n | open>close | mean |open-K| % | mean |close-K| % | mean extreme % | implied % |
|---|---|---|---|---|---|---|
| ALL | 152,995 | 29% | 1.06 | 1.97 | 3.09 | 2.28 |
| <1.0 | 22,051 | 31% | 1.47 | 2.34 | 3.54 | 3.13 |
| 1.0-1.5 | 36,763 | 29% | 0.98 | 1.85 | 2.89 | 2.17 |
| 1.5-2.0 | 37,968 | 28% | 0.99 | 1.90 | 2.99 | 2.13 |
| 2.0-3.0 | 39,437 | 29% | 1.00 | 1.92 | 3.05 | 2.11 |
| >=3.0 | 16,485 | 28% | 1.02 | 2.03 | 3.26 | 2.17 |

All panel days 2019-2026 (3,056,123 name-days): open beats close on 25%; mean |open-K| 0.95% vs |close-K| 1.98%. By prior-5d realized tercile: low: 25% (0.56 vs 1.20); mid: 25% (0.80 vs 1.69); high: 25% (1.48 vs 3.03).

## 7. 1-min calibration of the morning exit (2026 cache, K = prior close, % of K)

| sessions | n | open | 09:45 | 10:00 | 10:30 | 11:00 | 12:00 | 14:00 | close | extreme |
|---|---|---|---|---|---|---|---|---|---|---|
| all cached sessions | 19,366 | 1.61 | 2.08 | 2.22 | 2.37 | 2.45 | 2.59 | 2.75 | 2.87 | 4.42 |
| &nbsp;&nbsp;share of extreme | | 37% | 45% | 47% | 49% | 51% | 53% | 55% | 59% | 100% |
| &nbsp;&nbsp;beats the close | | 29% | 36% | 37% | 39% | 40% | 42% | 45% |  |  |
| Fridays (weekly expiries) | 3,549 | 1.56 | 2.12 | 2.19 | 2.31 | 2.39 | 2.52 | 2.71 | 2.90 | 4.39 |
| &nbsp;&nbsp;share of extreme | | 36% | 46% | 47% | 48% | 50% | 52% | 55% | 59% | 100% |
| &nbsp;&nbsp;beats the close | | 30% | 37% | 36% | 38% | 39% | 40% | 43% |  |  |
| high prior-5d realized (top tercile) | 6,453 | 2.31 | 2.99 | 3.17 | 3.42 | 3.53 | 3.76 | 4.02 | 4.18 | 6.40 |
| &nbsp;&nbsp;share of extreme | | 36% | 44% | 46% | 49% | 50% | 53% | 56% | 59% | 100% |
| &nbsp;&nbsp;beats the close | | 29% | 36% | 37% | 38% | 40% | 42% | 45% |  |  |
| high realized x Friday | 1,173 | 2.27 | 3.13 | 3.18 | 3.39 | 3.47 | 3.69 | 3.98 | 4.24 | 6.42 |
| &nbsp;&nbsp;share of extreme | | 36% | 47% | 47% | 49% | 50% | 51% | 55% | 59% | 100% |
| &nbsp;&nbsp;beats the close | | 29% | 38% | 37% | 39% | 39% | 39% | 43% |  |  |

Mean |px - K| in % of K (K = prior close). Extreme falls in the first hour (by 10:30) on 39% of sessions; median extreme time 09:30 (mode).


## 8. Read (2026-09-19)

**No edge, and the premise is false.** Buying the 1-DTE ATM straddle at the close before expiry loses about 30% of the premium on average however it is exited: settle at the close -30%, sell both legs at the open at fair value -30%, and the realized/implied gate only moves that from -44% (ratio <1) to -23/-25% (ratio >=3). The best cell in the study, liquid names (both legs' bid/ask under 10% of the straddle) with ratio_max >= 2 or 3, is still -7 to -8% net (t -12), and its close exit is -9 to -12%. 2020 and 2022 are -24% and -27%; both halves are -26%. This is the 0DTE long-strangle base rate (-26%/trade) in a different costume, not a new trade.

**"Chaos in the first hour" is not what expiry mornings look like.** On the 153k trade days the open is farther from the strike than the close only 29% of the time; on all 3.06M panel name-days 2019-26 it is 25%, in every realized-vol tercile. The mean move at the open is 1.06% of spot against 1.97% at the close and 2.28% implied. The day keeps going after the open far more often than it reverses.

**The hindsight arm is the only positive number, and it is unattainable.** Selling the winning leg at the day's extreme is +10% ungated and +23% gated (t 7-15), but the 1-min cache says a fixed 10:30 exit captures ~49% of the extreme and beats the close on only 39% of sessions; the extreme sits in the first hour on 39% of sessions (mode 09:30, i.e. the gap itself). There is no clock time that turns the extreme arm into a rule.

**COHR was a 1-in-20 draw.** Selling at the open at intrinsic wins on 5% of trades; the right tail exists (max +1083%) but the gated set ex the top 1% is -27%. Size accordingly: this is a lottery ticket with a negative expectation, not a hedge with a positive one.

Caveats: greeks in v3 end 2026-02-19 (delta-filtered rows), so the sample stops there; the fair-value open assumes 25% of the day's implied variance is spent by the gap (at 10% the open arm is ~8pp better, still ~-22%; at 40% it is worse); the intrinsic-open arm is a floor, not a price.

