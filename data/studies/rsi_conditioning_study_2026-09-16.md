# RSI(14) as a variable: put spreads, the long straddle, and Ryan's RSI swing (2026-09-16)

**Question (Gabe).** None of the strategy studies had tested RSI. Does daily RSI improve the two strategies that
survived, and does the Options With Ryan RSI swing on SPY/QQQ work?

**Set before running.** RSI = Wilder 14 on the adjusted daily close (yfinance), read at the entry-day close, which
is the same timestamp as the option marks. Buckets <30 / 30-40 / 40-50 / 50-60 / 60-70 / >=70. Main comparison:
RSI < 40 against the rest (put spreads) and extreme RSI (<30 or >=70) against the middle (straddle). The bar for a
new variable is |t| >= 3 on a week-clustered regression, because several cuts are being looked at.
**Ryan's signal** is taken from his video (`hC7AliOV9r0`, "How I Made $106,000 Using the RSI"): RSI <= 35 (his
NVDA level; 30 for ordinary names) **and** close below the lower Bollinger band (20, 2), with a bull market and an
uptrending name. Vehicles: 30-45 DTE ~0.28Δ cash-secured put, shares, or a 70Δ 365-DTE LEAP call.

Every regression is run twice. **Pooled** = does the variable help at all. **Within-week** = returns demeaned by entry
week, so it only asks whether RSI picks the better *name* on the same Friday, not whether it picks the better *week*.

Scripts: `run_rsi_prices.py` (closes → `data/cache/rsi_closes.parquet`), `run_rsi_conditioning_study.py`. Full
output: `rsi_conditioning_study_2026-09-16.log`.

## A. ETF bull put spreads: RSI adds nothing beyond VIX

20 ETFs, 45 DTE, 0.35/0.25, 50% take, no stop, ceiling-filtered. Baseline reproduces the erratum: **+5.68%, weekly
t 4.85** (published +5.70 / 4.87).

| RSI | n | mean | win | weekly t |
|---|---|---|---|---|
| <30 | 175 | +10.41% | 91% | 1.76 |
| 30-40 | 834 | +8.67% | 89% | 1.42 |
| 40-50 | 1,779 | +5.91% | 87% | 3.07 |
| 50-60 | 2,018 | +5.37% | 86% | 3.38 |
| 60-70 | 1,459 | +3.80% | 85% | 1.58 |
| >=70 | 474 | +4.86% | 86% | 2.72 |
| Ryan signal | 178 | +13.11% | 93% | 2.07 |
| Ryan + name & QQQ above 200d | 38 | +16.30% | 97% | 2.99 |

It looks monotone: lower RSI, better spread. It does not hold up.

| regression (week-clustered) | coefficient | t |
|---|---|---|
| RSI<40, pooled | +3.88 pp | 2.21 |
| RSI<40, **within-week** | −0.23 pp | −0.13 |
| RSI<40, **controlling for VIX** | +1.21 pp | 0.69 (VIX t 4.56) |
| Ryan signal, controlling for VIX | +4.04 pp | 1.35 |
| Ryan full, pooled | +10.68 pp | 3.18 (n = 38; within-week t 1.09) |

**Reading.** Low RSI on an ETF is mostly a market-wide selloff, and the spread does better in those weeks because
premium is higher (RSI vs VIX correlation −0.31). Once VIX is in the regression, RSI has nothing left. Within the
same week, choosing the most oversold ETF does no better than choosing any of them. This is the same finding as the
paid-to-wait IV≥60th-pct gate reached another way, **not a new edge**. The by-year gap does help in 2022 (+17 pp)
but hurts in 2025 (−9.8 pp). **Verdict: do not add an RSI gate; if a gate is wanted, gate on implied vol directly.**

## B. 7-DTE long straddle: skip names with RSI >= 70 (adopted after the walk-forward in D)

Gated sample, n = 5,886 (98.9% RSI coverage; SAVA / CTRA / CYBR / BK had no Yahoo history).

| RSI | n | mean | median | win | mean ex-top-1% |
|---|---|---|---|---|---|
| <30 | 63 | −2.99% | −14.7% | 43% | −5.17% |
| 30-40 | 467 | +1.08% | −16.3% | 41% | −2.01% |
| 40-50 | 1,350 | +3.95% | −15.0% | 43% | −0.19% |
| 50-60 | 1,813 | **+10.58%** | −11.0% | 45% | +6.34% |
| 60-70 | 1,493 | +1.96% | −16.8% | 41% | −1.31% |
| **>=70** | 636 | **−6.09%** | −29.2% | 36% | −10.60% |

| regression (week-clustered) | coefficient | t |
|---|---|---|
| extreme (<30 or >=70), pooled | −11.26 pp | **−3.11** |
| extreme, within-week | −11.95 pp | **−3.51** |
| RSI>=70, pooled | −11.47 pp | −2.90 |
| RSI>=70 + VIX | −12.15 pp | −3.13 |
| RSI>=70 + ext21 (panel subset, n 4,795) | −12.12 pp | −2.49 |
| RSI>=70, 2018-21 / 2022-26 | −11.29 / −12.04 pp | −1.56 / −2.55 |

**It passes the bar, but only just.** Extreme names lose in 8 of 9 years (the exception, 2020, has n = 20). The
effect is the same size in both halves and holds within-week, so it is picking names rather than timing. It is really
a **>=70 effect**: <30 has only 63 trades. Controlling for VIX does not move it. It **cannot be told apart from
extension above the 21 EMA** (RSI vs ext21 correlation 0.97 on this sample). It is the same "extended" flag in
different units, and a threshold works where the linear ext21 term does not (ext21 t 0.51).

Effect on the sleeve if RSI >= 70 entries are skipped:

| | n | mean | monthly t | mean ex-top-1% | share of return from top 1% |
|---|---|---|---|---|---|
| all gated | 5,886 | +4.14% | 1.78 | +0.33% | 92% |
| **ex RSI >= 70** | 5,250 | **+5.38%** | **2.17** | **+1.63%** | **70%** |

The main improvement is to the body of the distribution, not the tail: the 1% of huge winners are
under-represented at RSI >= 70 anyway (6.9% of top-1% trades vs 10.9% of all trades). That matters for this
strategy, whose weakness is that its mean depends on 58 trades.

The legs don't sort by RSI: the call leg shows no pattern, and the put leg is worse at both extremes but at t < 1.
**RSI does not choose the leg.**

**Verdict.** A **candidate straddle filter**: skip entries with RSI(14) >= 70 (equivalently, names stretched far above
their 21 EMA). It is not adopted yet. t ≈ 3 after looking at several cuts is borderline, so it needs a walk-forward
check (fix the 70 threshold, score each year out of sample) before the screen uses it.

## C. Ryan's RSI swing on SPY / QQQ: no reliable edge

Forward return of the ETF from the signal-day close, events de-duplicated so they don't overlap, excess = minus the
all-days mean of the same period. SPY 1993-2026, QQQ 1999-2026.

| signal | ticker | horizon | events | excess | t | 2010+ excess (t) | worst event |
|---|---|---|---|---|---|---|---|
| RSI<=35 & <lower BB | SPY | 21d | 76 | +0.60% | 0.84 | +0.95% (1.05) | −20.6% |
| RSI<=35 & <lower BB | QQQ | 21d | 70 | +1.49% | 1.29 | +1.83% (1.76) | −21.6% |
| + above 200d | SPY | 63d | 29 | +2.64% | 2.68 | +0.96% (0.83) | −6.4% |
| + above 200d | QQQ | 63d | 25 | +3.47% | 2.65 | +2.11% (1.38) | −6.8% |
| RSI<=30 | QQQ | 63d | 28 | +1.69% | 0.61 | +4.55% (2.13) | −29.1% |
| RSI>=70 (overbought) | SPY | 21d | 99 | −0.14% | −0.47 | −0.27% (−0.78) | — |

**Reading.** Buying the index after an RSI/Bollinger oversold signal earns a point or two more than buying on a
random day. None of it clears t 3. The best cut (with the 200d filter, 63 days) rests on 25-29 events, and the full
sample does better than 2010+ only because of the 1990s-2000s events: pre-2010 SPY has t 3.20 on 9 events. Worst
drawdowns after the signal reach −20% to −34%. **Overbought does not predict a decline.** On that one point Ryan is
right that you shouldn't short a stock just because RSI is high. His 96% win rate comes from the vehicle: 90% of his
trades are short puts. That is the put-spread result in section A. Selling puts wins about 87% of the time whether or
not RSI is low, and what low RSI adds is VIX.

**Verdict: 1.5 / 5.** Mild index mean reversion after selloffs is real but too small and too few events to trade on
its own. The option version is simply "sell puts when implied vol is high".

## Summary

| strategy | does RSI help? | action |
|---|---|---|
| ETF bull put spread | Only as a stand-in for VIX / high premium. No stock-selection value. | None. Gate on IV if anything. |
| 7-DTE long straddle | **Yes: RSI >= 70 entries lose ~12 pp** (t ≈ −3, both halves, 8/9 years). Same thing as extension above the 21 EMA. | **Adopted** after walk-forward (section D). |
| Ryan RSI swing, SPY/QQQ | Small, unstable mean reversion; overbought predicts nothing. | Not tradeable on its own. |

---

## D. Walk-forward of the RSI >= 70 straddle skip (same day)

Script `run_rsi_straddle_walkforward.py`, output `rsi_straddle_walkforward_2026-09-16.log`. Checks set in the
script docstring before running.

**1. Fixed 70, each year separately.** Skipping helped the mean in **7 of 8 full years**, the median in 7/8, and
the mean ex-top-1% in 7/8. 2026 to date helped too.

| year | n | skipped | all | kept | lift | skipped mean / median |
|---|---|---|---|---|---|---|
| 2018 | 288 | 18 | +5.06 | +5.68 | +0.62 | −4.2 / +2.0 |
| 2019 | 765 | 97 | −6.91 | −4.90 | +2.01 | −20.8 / −37.3 |
| **2020** | 163 | 19 | +20.70 | +17.57 | **−3.13** | **+44.4** / −31.5 |
| 2021 | 1,156 | 81 | +4.04 | +4.88 | +0.84 | −7.2 / −34.8 |
| 2022 | 296 | 30 | +6.90 | +9.73 | +2.82 | −18.1 / −24.0 |
| 2023 | 1,368 | 180 | +5.99 | +8.17 | +2.18 | −8.4 / −26.5 |
| 2024 | 1,031 | 135 | +4.05 | +4.89 | +0.83 | −1.5 / −23.2 |
| 2025 | 719 | 73 | +5.56 | +5.89 | +0.33 | +2.6 / −26.9 |
| 2026 YTD | 100 | 3 | +17.45 | +17.78 | +0.33 | +6.7 / −47.5 |

The one losing year shows the cost: in 2020, a few of the 19 skipped trades were huge winners (mean +44%, median
−31%). The skip gives up some tail to fix the body.

**2. Expanding window** (cutoff chosen from {60, 65, 70, 75, 80, none} on years before N, applied to N):

| test years 2020-2026 pooled | n | mean | median | ex-top-1% | monthly t |
|---|---|---|---|---|---|
| no filter | 4,833 | +5.83% | −15.4% | +1.95% | 2.15 |
| walk-forward cutoff (chose **60** every fold) | 3,143 | +7.76% | −12.4% | +3.78% | 2.41 |
| **fixed 70** | 4,312 | +6.95% | −13.5% | +3.13% | **2.51** |

A filter chosen only from past years still beats no filter out of sample: 5 of 7 test years, with 2020 worse and
2024 flat. Scoring by mean, the chooser always prefers the deeper 60 cut. That cut keeps only 65% of trades and does
not raise monthly t over 70. ⚠ Fixed 70 on 2020+ is not strictly out of sample, because the study that proposed it
saw those years. But 70 is the textbook overbought level, set as a bucket edge before any results, not tuned.

**3. Within-week placebo** (RSI shuffled among the same week's trades, 5,000 times): real mean lift **+1.24 pp vs
placebo 95th pct +0.56, p = 0.0002**. Median lift +1.80 pp vs +0.69, p < 0.0002. Which name gets skipped matters, not
just which week.

**4. Plateau (in-sample).** Skipping >=60 / >=65 / >=70 / >=75 / >=80 gives a mean of +6.74 / +6.19 / +5.38 / +4.69 /
+4.13 (none: +4.14), monthly t 2.15 / 2.21 / 2.17 / 1.92 / 1.77. A smooth slope, no spike at 70. The effect is
"high RSI is bad", fading to nothing by 80 because too few trades are skipped.

**5. Breadth.** 636 skipped trades across 176 tickers (largest: NFLX 20). Leave-one-ticker-out keeps the gap between
−10.9 and −12.7 pp. In 77% of the 98 tickers with >=3 trades on each side, the ticker's own RSI>=70 trades do worse
than its other trades.

**Verdict: ADOPT the skip at RSI(14) >= 70** for the 7-DTE straddle screen. It passes every check: 7/8 years on mean,
median and ex-top-1%; beats no filter out of sample; placebo p = 0.0002; broad across tickers; a smooth slope rather
than a tuned point. 70 is preferred over 60 because it keeps 89% of trades and has the best out-of-sample monthly t;
60 raises the mean but cuts capacity by a third for no t gain. Expected effect: roughly +1 pp/trade on the mean and
+1.2 to +1.6 pp ex-top-1%. **It does not fix the straddle's core weakness**: the sleeve is still carried by its tail
(top-1% share 92% → 70%).

## E. RSI vs extension above the 21 EMA: the same measure (checked same day)

On all 2.95M ticker-days in `liquid_panel_2019` (1,741 tickers), RSI(14) against ext21 = (close/EMA21 − 1)/ADR20:
**Spearman 0.984**, per-ticker Pearson median 0.974 (10th-90th pct 0.962-0.979). Pooled Pearson is only 0.07, but
that comes from a few near-zero-ADR rows blowing up ext21, not a real disagreement. Unscaled % above the 21 EMA is
looser (Spearman 0.951). Map: RSI 60-70 ≈ median **1.7 ADR** over the 21 EMA; RSI 70-80 ≈ **2.8 ADR**; RSI <30 ≈ −3.1.

As a straddle skip on the 4,795 panel-covered trades, the two rules are nearly interchangeable:

| skip rule | n kept | mean | median | ex-top-1% | monthly t |
|---|---|---|---|---|---|
| none | 4,795 | +4.34% | −15.9% | +0.66% | 1.94 |
| RSI >= 70 | 4,245 | +5.55% | −14.5% | +1.80% | 2.31 |
| ext21 >= 2.40 ADR (same count) | 4,245 | +5.41% | −14.5% | +1.66% | 2.30 |

The flags agree on 425 trades (mean −6.6%). Where they disagree (125 trades each), RSI-only trades average +0.6% and
ext21-only +5.3%, so RSI is marginally the sharper flag. Too few trades to call. Use either; RSI needs no high/low data.

## F. Why RSI >= 70 straddles lose: the put side and the size of the move, not the call

Hypothesis (Gabe): extended names lose because the call side can't work. **Rejected.** Within-week regressions of
the RSI >= 70 flag, SE clustered by week, n = 5,822:

| outcome | extended minus rest, same week | t |
|---|---|---|
| straddle ROC | −12.8 pp | −3.40 |
| **call leg ROC** | −5.5 pp | **−0.74** (no reliable difference) |
| **put leg ROC** | **−19.9 pp** | **−2.92** |
| straddle cost, % of spot | −0.39 | −6.92 (cheaper) |
| move to expiry, % | **−0.86** | **−5.47** (smaller still) |
| log(move / cost) | −0.15 | −2.84 |
| move beat breakeven | −8.1 pts | −3.54 |
| signed move, % | +0.26 | 1.17 |
| finished up | +4.1 pts | 1.60 |

Raw: call win rate 37.9% at RSI >= 70 vs 35.4% otherwise; put win rate 28.1% vs 34.2%; median week move 1.83% vs 2.42%.

**Mechanism.** Extended names are in orderly trends. Their straddles are cheaper, but they move even less than the
lower price implies, so the move beats breakeven less often. The slight upward drift (not significant on its own)
lands the loss on the put. The call does about as well as anywhere else. **Implication for the long-call project:**
RSI >= 70 / extension is not a reason to skip a call on this evidence. That is a separate test with its own
benchmark (always-call).
