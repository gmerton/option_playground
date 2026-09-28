# Stress bucket head-to-head — 20-DTE 0.25/0.15 spread vs 45-DTE 12Δ naked put (2026-09-28)

Script: `run_stress_bucket_h2h.py` (pre-registered in the docstring, committed before the run). Per-trade: `stress_bucket_h2h_2026-09-28.csv`.

```
paired regime entries: 113 of 122 (56 months), 2010-01-29 -> 2025-11-21; A median width $9, credit $1.32, exits {'take': 103, 'expiry': 10}
  A 20-DTE 0.25/0.15 spread    ROC +8.15%/trade (median +15.19, t +3.93) win 93% | worst -100.0% of capital ($-1258/contract) | CVaR5 -100.0% | median capital $768/contract | mean $ P&L +61
  B 45-DTE 12Δ naked (Reg-T)   ROC +3.15%/trade (median +3.58, t +11.08) win 93% | worst -26.7% of capital ($-1564/contract) | CVaR5 -11.5% | median capital $3,128/contract | mean $ P&L +83
  (B on a SPAN-like capital ≈ Reg-T/5: ROC +15.76%/trade — sensitivity only)

PRIMARY paired ROC_A - ROC_B: +5.94pp  t +2.73  halves +6.95 / +4.05
  A annualised ROC per capital-day +330%/yr (mean hold 14 d); B held ≤ 24 d by rule
  episode-level (33 episodes): A +10.25% vs B +3.47% -> +6.78pp t +3.59; A positive in 30/33, B in 33/33
  2020-02/03 n  7: A +2.78% (worst -100.0) | B +3.70% (worst -26.7)
  2022       n 33: A +5.69% (worst -100.0) | B +2.86% (worst -6.6)
  2018-Q4    n  7: A -6.40% (worst -100.0) | B +1.38% (worst -7.9)

per year ROC %/trade:
trade_date   2010  2011   2012   2014   2015   2016  2018   2019  2020   2021  2022   2023   2024  2025
roc_A       13.46 -2.63  13.01  12.43  13.74  13.55 -1.22  14.59  7.46  14.23  5.69  16.08  13.84  6.33
roc_B        5.33  4.20   3.41   3.27   3.41   3.48  2.13   2.52  4.12   3.64  2.86   2.66   3.02  1.16

VERDICT: EQUIVALENT on return (choose on tail / capital)
```

## Reading

- **PRIMARY not met**: spread − naked = **+5.94pp ROC/trade, t 2.73** (halves +6.95 / +4.05). Episode-level t 3.59 is
  secondary. Verdict per the pre-registration: **EQUIVALENT on return; choose on tail and capital.**
- The spread earns more per dollar of **Reg-T** capital (+8.15% vs +3.15%) because its capital is only the width. It
  also has **6 full losses (−100% of capital)** in 113 trades: 2011-07, 2018-12, 2020-03-06, and three in Apr–Jun 2022.
  The naked put's worst was −26.7% of Reg-T margin (2020-03-06) and it was positive in 33/33 episodes against the spread's 30/33.
- **In dollars per contract the naked put makes more (+$83 vs +$61) and has the bigger single loss (−$1,564 on
  2025-03-28 vs −$1,258).** Which one "wins" depends on what capital actually binds:
  - Reg-T / cash-style account: the spread. It earns more per dollar, and its tail is capped at the width.
  - Portfolio margin or /ES SPAN (≈1/5 of Reg-T): the naked put, at +15.8%/trade (a sensitivity only, not tested). Its
    tail is uncapped, though, so size on the Reg-T number, not on SPAN.
- 2018-Q4 was the only window where the structures diverged in sign: spread −6.4%, naked +1.4%. The spread's
  near-the-money short leg is what gets hit in a grind lower.

## Decision

Nothing changes in the book. The certified spread stays the traded structure, and the ledger does not prefer
either one on return. Anyone wanting the naked put for margin efficiency is making a risk choice, not an edge choice.
