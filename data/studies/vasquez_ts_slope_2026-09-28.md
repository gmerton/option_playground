# Vasquez (JFQA 2017): IV term-structure slope sort on single-stock straddles (2026-09-28)

Cited in Sinclair, *Positional Option Trading*. Script `run_vasquez_ts_slope.py` (pre-registered in the docstring, committed before the pull). Paper spec seen as abstract only; tenors are ours (IV ~91 DTE − IV ~30 DTE). Universe, straddles and P&L are reused unchanged from the Goyal–Saretto run (2026-09-26).

```
straddles with a long-tenor IV: 45,402 (167 months); median long DTE 81; slope median +0.006, share inverted 43%; median cost 1.8% of mid per side

## PRIMARY slope = IV91 - IV30: 167 months, ~28 names per decile
  UNHEDGED NET D10 long + D1 short -1.79%/mo t_NW -0.92 halves +3.41 / -5.73 yrs+ 5/16 | GROSS +1.94%/mo t +0.99 | legs net: long -0.22% short -1.57%  *PRIMARY*
           gross LONG by decile: D1:-0.2 D2:-0.7 D3:+2.4 D4:+0.3 D5:-0.8 D6:+1.7 D7:+1.9 D8:+2.2 D9:+0.1 D10:+1.7
           net by year: 2011:-7.3 2012:+6.6 2013:+12.2 2014:+14.8 2015:+10.4 2016:-5.8 2017:-6.4 2018:-3.0 2019:-9.8 2020:-12.9 2021:-0.5 2022:-5.3 2023:+1.6 2024:-7.7 2025:-9.5 2026:-0.7
  HEDGED   NET D10 long + D1 short -4.33%/mo t_NW -5.13 halves -4.28 / -4.36 yrs+ 1/16 | GROSS +1.09%/mo t +1.28 | legs net: long -3.52% short -0.81%
           gross LONG by decile: D1:-1.7 D2:-0.6 D3:-1.0 D4:-2.3 D5:-2.4 D6:-2.1 D7:-1.2 D8:-0.9 D9:-0.5 D10:-0.6

## EXPLORATORY ratio IV91 / IV30: 167 months, ~28 names per decile
  UNHEDGED NET D10 long + D1 short -2.69%/mo t_NW -1.46 halves +1.62 / -5.96 yrs+ 4/16 | GROSS +1.00%/mo t +0.54 | legs net: long -0.54% short -2.16%
           gross LONG by decile: D1:+0.4 D2:+0.1 D3:+2.4 D4:-0.0 D5:-0.1 D6:+1.4 D7:+1.5 D8:+1.3 D9:-0.0 D10:+1.4
  HEDGED   NET D10 long + D1 short -4.44%/mo t_NW -5.23 halves -3.59 / -5.09 yrs+ 3/16 | GROSS +1.40%/mo t +1.62 | legs net: long -2.90% short -1.55%
           gross LONG by decile: D1:-1.0 D2:-1.0 D3:-1.2 D4:-2.1 D5:-2.7 D6:-1.4 D7:-1.6 D8:-1.6 D9:-1.3 D10:+0.4

## EXPLORATORY slope inside the top HV-IV tercile: 167 months, ~9 names per decile
  UNHEDGED NET D10 long + D1 short -3.66%/mo t_NW -1.16 halves -4.69 / -2.87 yrs+ 8/16 | GROSS +0.14%/mo t +0.04 | legs net: long -0.34% short -3.32%
           gross LONG by decile: D1:+1.4 D2:+3.7 D3:+3.9 D4:+1.5 D5:+0.2 D6:+4.9 D7:+1.8 D8:+0.1 D9:+3.0 D10:+1.6
  HEDGED   NET D10 long + D1 short -3.50%/mo t_NW -2.61 halves -4.27 / -2.92 yrs+ 5/16 | GROSS +2.05%/mo t +1.52 | legs net: long -3.28% short -0.22%
           gross LONG by decile: D1:-2.5 D2:-1.7 D3:-1.5 D4:-1.9 D5:-1.6 D6:-0.9 D7:+0.6 D8:-0.9 D9:-0.6 D10:-0.5

VERDICT (PRIMARY unhedged net): NOT MET (-1.79%/mo, t -0.92)
```

## Reading

- **PRIMARY NOT MET.** The unhedged net spread is **−1.79%/mo, t −0.92**, and the halves flip sign: +3.41 in
  2011–17, −5.73 in 2018–26 (the 2012–15 run carries all of it). The gross spread is +1.94%/mo (t 0.99), far below
  the ~3.6%/mo round-trip friction of a long-plus-short straddle pair (1.8% of mid per side, per leg).
- **Hedged: FAIL at the bar in the wrong direction**, −4.33%/mo, t −5.13, 1/16 years positive. That is the same
  cost wall as Goyal–Saretto (−4.73%, t −4.99).
- **The gradient is weak and non-monotone.** Gross unhedged long returns run D1 −0.2 … D10 +1.7 with noise
  throughout. The sign leans the paper's way, but it is not an edge at our costs on liquid names 2011–26.
- The ratio form and the within-cheap-IV-tercile version change nothing.

**Verdict: NULL (primary) · MECHANISM:** the second cross-sectional single-stock vol sort to die on friction. The
priors on the Cao–Han and HAR siblings fall further, since they need a gross spread of ≳4–5%/mo.
