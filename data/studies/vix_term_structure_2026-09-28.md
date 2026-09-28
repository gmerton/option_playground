# Sinclair: VIX term structure as a vol-selling gate (2026-09-28)

Source: Euan Sinclair, *Positional Option Trading* (2020), rule as typed by Gabe: "Sell VIX futures or index options when the term structure is in contango. Buy VIX futures or index options when the term structure is in backwardation." Script `run_vix_term_structure.py` (pre-registered in the docstring, committed before the run). Curve = VIX/VIX3M (CBOE; from 2009-09, so **2008 is not in the sample**).

```
curve: VIX/VIX3M 2009-09-18 -> 2026-09-25; backwardation on 8% of days

## PRIMARY: certified stress bucket, 113 entries (median R 0.977; 35% in backwardation)
  20-DTE spread (ROC on width-credit)  *PRIMARY*: backwardation n 40 ROC +6.32% (worst -100.0) | contango n 73 ROC +9.16% (worst -100.0) -> diff -2.84pp t -0.59 halves -6.24 / -2.27
  45-DTE 12d naked (ROC on Reg-T)     (a): backwardation n 40 ROC +3.81% (worst -26.7) | contango n 73 ROC +2.79% (worst -18.6) -> diff +1.01pp t +1.31 halves +0.41 / +1.08
  EXPLORATORY R >= 1.05, spread       : backwardation n 19 ROC +2.07% (worst -100.0) | contango n 94 ROC +9.38% (worst -100.0) -> diff -7.31pp t -0.93 halves -17.92 / -1.68

## SECONDARY (b): all 748 weekly 45-DTE 12d put sales (% of Reg-T), month-clustered OLS
  const -1.793 (t -3.29)  backwardation +0.116 (t +0.18)  vix +0.164 (t +6.12)  cert +0.402 (t +0.86)
  backwardation alone: +2.67pp t +4.25 (bw n 54, contango n 694)
  (c) contango weeks (Sinclair SELL rule) n 694: +0.96%/trade t +2.75 halves +1.33 / +0.85 yrs+ 15/17 worst -107.0%
  (c) certified regime (book rule)       n 122: +3.38%/trade t +11.33 halves +4.06 / +2.78 yrs+ 14/14 worst -26.7%
  (c) backwardation weeks                n  54: +3.59%/trade t +7.72 halves +3.97 / +3.50 yrs+ 12/12 worst -26.7%
  (c) contango AND not certified         n 616: +0.60%/trade t +1.52 halves +1.12 / +0.59 yrs+ 14/17 worst -107.0%
  (d) BUY leg in backwardation weeks ≈ -(sale) - round-trip cost: -4.04% of the same margin (the sale earned +3.73%)

## TERTIARY: UVXY weekly 2018-03-02 -> 2026-09-11 (446 weeks, 26 backwardation)
  Sinclair rule (short contango / long backwardation) mean +0.57%/wk NW t +0.94 worst week -86.3% compounded -95%
  always short (carry, no timing)                  mean +0.65%/wk NW t +0.92 worst week -86.3% compounded -96%
  short in contango only, flat otherwise           mean +0.63%/wk NW t +1.13 worst week -86.3% compounded -87%
  long in backwardation only, flat otherwise       mean -0.06%/wk NW t -0.18 worst week -32.2% compounded -62%
  timing value = rule - always short: -0.08%/wk NW t -0.12

VERDICT (PRIMARY): NOT MET (backwardation worse but not at the bar)
```

## Reading

- **PRIMARY NULL.** Inside the certified stress bucket, backwardation entries earn −2.84pp less than contango
  entries on the spread (t −0.59). Both halves are negative but tiny next to the noise. On the naked 45-DTE put they
  earn *more* (+1.01pp, t 1.31). No gate.
- **The BUY leg is contradicted.** Selling the 45-DTE 12Δ put in backwardation weeks earned **+3.59%/trade, t 7.72,
  12/12 years**, so buying it there loses about −4% of margin a trade. Buying vol in backwardation is the wrong side
  of the book's one certified edge.
- **The curve carries nothing beyond the VIX level.** In the joint regression, backwardation adds +0.12 (t 0.18)
  while VIX itself carries t 6.1. Alone, backwardation looks strong (+2.67pp, t 4.25) only because it is a high-VIX
  proxy.
- **The SELL leg is weak.** Selling in every contango week makes +0.96%, t 2.75, with a −107% worst trade. Contango
  weeks outside the certified regime make +0.60%, t 1.5: the always-on complement again.
- **The VIX-futures leg (UVXY 2018+):** the timing adds nothing over always-short (−0.08%/wk, t −0.12). Every short
  arm has an −86% week and compounds to −87…−96%. Long-in-backwardation alone is −0.06%/wk.

**Verdict: NULL (primary) · buy leg INVERTED on this book · YIELD MECHANISM:** the curve is a noisier VIX level. The
certified VIX ≥ 20 & SPY < 50MA rule already captures what it knows, and the post-spike backwardation weeks are
where the premium is richest.
