# Luk and Ariel long entries vs the house breakout (2026-10-03 15:04)

Descriptive, no outcomes. House rule = run_precision_tier_control.build() on liquid_panel_2019 (2026 survivors).

## Ariel

Entries 314 (282 long, 31 short, set aside). Long entries in the panel: 244 (38 not in it: small/illiquid names, ETFs, or dates outside it). Fill dates 2025-04-15 -> 2026-09-30.

- house breakout that day: **1%** (3); precision tier that day: **0%** (1)
- within 3 sessions either side: breakout 9%, precision 4%

First gate the entry fails (one bucket each, in rule order):

- closed below the 15-day pivot (inside the base / pullback): 188 (77%)
- not in liquid universe / ADR < 3 / 52wk range < 17%: 29 (12%)
- volume < 1.1x 50-day: 13 (5%)
- EMA stack < 5 days (not yet trending): 4 (2%)
- chase: gap >= 5% or day change >= 8%: 4 (2%)
- closed in the bottom half of the day's range: 3 (1%)
- breakout, but outside precision (ADR 4-7, <15% off high, stack <= 40): 2 (1%)
- PRECISION BREAKOUT: 1 (0%)

Share failing each gate (not exclusive):

- not in liquid universe / ADR < 3 / 52wk range < 17%: 12%
- closed below the 15-day pivot (inside the base / pullback): 86%
- already above the pivot the day before (not fresh): 0%
- volume < 1.1x 50-day: 74%
- closed in the bottom half of the day's range: 45%
- EMA stack < 5 days (not yet trending): 33%
- chase: gap >= 5% or day change >= 8%: 9%

| feature (median) | his/her long entries | same-period precision tier |
|---|---|---|
| ADR % | +5.71 | +4.80 |
| % off 52-week high | -13.78 | +1.09 |
| close vs 20 EMA, ADR | +0.74 | +2.82 |
| close vs 15-day pivot, ADR | -1.10 | +0.39 |
| EMA stack days | +10.00 | +16.00 |
| volume / 50-day | +0.90 | +1.43 |
| gap % | +0.58 | +0.63 |

## Luk

Entries 144 (102 long, 42 short, set aside). Long entries in the panel: 91 (11 not in it: small/illiquid names, ETFs, or dates outside it). Fill dates 2025-11-26 -> 2026-09-18.

- house breakout that day: **0%** (0); precision tier that day: **0%** (0)
- within 3 sessions either side: breakout 2%, precision 1%

First gate the entry fails (one bucket each, in rule order):

- closed below the 15-day pivot (inside the base / pullback): 79 (87%)
- not in liquid universe / ADR < 3 / 52wk range < 17%: 5 (5%)
- chase: gap >= 5% or day change >= 8%: 3 (3%)
- EMA stack < 5 days (not yet trending): 2 (2%)
- volume < 1.1x 50-day: 1 (1%)
- closed in the bottom half of the day's range: 1 (1%)

Share failing each gate (not exclusive):

- not in liquid universe / ADR < 3 / 52wk range < 17%: 5%
- closed below the 15-day pivot (inside the base / pullback): 91%
- already above the pivot the day before (not fresh): 0%
- volume < 1.1x 50-day: 73%
- closed in the bottom half of the day's range: 42%
- EMA stack < 5 days (not yet trending): 44%
- chase: gap >= 5% or day change >= 8%: 21%

| feature (median) | his/her long entries | same-period precision tier |
|---|---|---|
| ADR % | +6.68 | +4.80 |
| % off 52-week high | -17.53 | +1.09 |
| close vs 20 EMA, ADR | +0.81 | +2.82 |
| close vs 15-day pivot, ADR | -1.19 | +0.39 |
| EMA stack days | +7.00 | +16.00 |
| volume / 50-day | +0.89 | +1.43 |
| gap % | +0.76 | +0.63 |

