# Sinclair: PEAD option vehicles (2026-09-28)

Source: Euan Sinclair, *Positional Option Trading* (2020), as typed by Gabe: after a positive surprise buy a short-dated 40/10 call spread; after a negative one a 50/20 put spread ("also selling one of the most expensive parts of the implied vol curve"); or sell a covered call / put ("guaranteed to profit if any drift occurs"). Script `run_pead_option_vehicles.py` (pre-registered in the docstring, committed before the pull; chunking fix only). Events from yfinance EPS actual vs estimate; entry at the reaction-day close; expiry nearest 30 DTE; held to expiry; house fills. Control = same name, same structure, ≥ 25 sessions later with no earnings before expiry.

```
trades priced: 45,402 (23,001 event, 22,401 control), 1092 names, 2010-02-16 -> 2025-12-22
A = 40/10 call spread (beats), B = 50/20 put spread (misses): % of debit. C = covered call (beats): % of net cost. D = covered put (misses): % of spot.

## PRIMARY / SECONDARY (surprise >= 10%)
  A beat >= 10%: n  7841 (paired 6511) | ABS net  -3.64% t -0.79 halves  -9.65/ +3.60 | gross +15.84% t +2.09 | control  +1.42% t +0.28 | EVENT - CONTROL  -2.61pp t -0.35 halves  -9.27/ +6.21 yrs+ 10/16  *PRIMARY*
  B miss >= 10%: n  2743 (paired 2211) | ABS net -10.87% t -2.13 halves  -9.87/-12.88 | gross  -1.04% t -0.18 | control -16.90% t -3.29 | EVENT - CONTROL  +1.37pp t +0.19 halves  -1.34/ -2.50 yrs+ 7/16  *PRIMARY*
  C beat >= 10%: n  8366 (paired 7048) | ABS net  +0.49% t +1.36 halves  +0.20/ +0.51 | gross  +0.84% t +2.33 | control  +0.73% t +1.80 | EVENT - CONTROL  -0.04pp t -0.08 halves  -0.79/ +0.27 yrs+ 8/16
  D miss >= 10%: n  2841 (paired 2327) | ABS net  -1.06% t -2.35 halves  -1.00/ -0.61 | gross  -0.66% t -1.46 | control  -0.81% t -2.20 | EVENT - CONTROL  -0.49pp t -0.85 halves  +0.19/ -0.04 yrs+ 8/16

## EXPLORATORY thresholds
  A beat >= 0.001%: n 15872 (paired 13237) | ABS net  +1.58% t +0.35 halves  -1.35/ +4.36 | gross +19.68% t +3.02 | control  +3.46% t +0.73 | EVENT - CONTROL  -1.07pp t -0.16 halves  -2.61/ +9.58 yrs+ 10/16
  B miss >= 0.001%: n  5698 (paired 4654) | ABS net -12.65% t -2.83 halves  -9.21/-11.50 | gross  -3.65% t -0.74 | control -15.66% t -3.29 | EVENT - CONTROL  +1.71pp t +0.26 halves  -0.27/ -2.71 yrs+ 6/16
  C beat >= 0.001%: n 17047 (paired 14460) | ABS net  +0.54% t +1.77 halves  +0.31/ +0.42 | gross  +0.86% t +2.84 | control  +0.61% t +2.00 | EVENT - CONTROL  -0.01pp t -0.02 halves  -0.38/ +0.40 yrs+ 8/16
  D miss >= 0.001%: n  5893 (paired 4852) | ABS net  -0.89% t -2.75 halves  -0.77/ -1.15 | gross  -0.53% t -1.62 | control  -0.96% t -3.03 | EVENT - CONTROL  -0.03pp t -0.06 halves  -0.09/ +0.01 yrs+ 9/16
  A beat >= 20%: n  4583 (paired 3795) | ABS net  -5.62% t -1.06 halves -13.05/ +5.29 | gross +18.49% t +1.76 | control  +4.51% t +0.74 | EVENT - CONTROL  -5.60pp t -0.61 halves -11.91/ +7.17 yrs+ 8/16
  B miss >= 20%: n  1862 (paired 1498) | ABS net -12.17% t -2.30 halves  -9.80/-13.89 | gross  -3.06% t -0.52 | control -16.21% t -2.87 | EVENT - CONTROL  -0.69pp t -0.09 halves  -1.95/ -8.20 yrs+ 8/16
  C beat >= 20%: n  4873 (paired 4076) | ABS net  +0.51% t +1.26 halves  +0.20/ +0.79 | gross  +0.88% t +2.16 | control  +1.26% t +2.29 | EVENT - CONTROL  -0.47pp t -0.67 halves  -0.94/ +0.26 yrs+ 8/16
  D miss >= 20%: n  1924 (paired 1577) | ABS net  -1.47% t -2.79 halves  -1.16/ -0.93 | gross  -1.07% t -2.03 | control  -0.96% t -2.16 | EVENT - CONTROL  -0.74pp t -1.08 halves  +0.40/ -0.87 yrs+ 8/16

'guaranteed if any drift': covered-call beats with S_T > S_0: 4396 of 8366 (53%), profitable 100%; with S_T <= S_0: mean -6.82%

absolute net by year (%): 
trade_date  2010  2011  2012  2013  2014  2015  2016  2017  2018  2019  2020  2021  2022  2023  2024  2025
A          -38.6 -48.6 -37.9  40.2   8.0 -24.7  15.4  -5.6  -5.3  -4.5  28.0   9.7 -28.4  12.6  18.4   4.1
B          -25.4  29.5   2.4 -15.5 -31.7  12.7 -40.6  -3.0   0.7  -3.7 -28.5 -14.4  -8.5  15.9 -30.1 -27.6
C           -1.5  -4.1  -1.3   2.2   1.0  -0.5   2.5   1.1  -0.0  -0.3   1.0   1.0  -0.5   0.6   1.6   0.6
D           -2.2   2.9  -1.5  -0.4  -2.4   1.4  -4.4  -0.5  -1.2  -2.6  -5.2   0.9   1.8   0.2  -1.4  -0.4

BAR (event - control, t >= 3, both halves > 0, majority of years):
  A: NOT MET (-2.61pp t -0.35); absolute -3.64% t -0.79
  B: NOT MET (+1.37pp t +0.19); absolute -10.87% t -2.13
```

## Reading

- **PRIMARY, both NOT MET.** The surprise adds nothing to either spread. Call spread after a ≥ 10% beat: event −
  control **−2.61pp, t −0.35**. Put spread after a ≥ 10% miss: **+1.37pp, t 0.19**. The same holds at every
  threshold (any sign, ≥ 20%). This independently re-confirms the stock PEAD null through a different instrument.
- **The call spread's leverage is eaten by the spread.** It earns **+15.8% of debit gross (t 2.09)** but **−3.6%
  net**: crossing two legs' quotes costs ~19% of a cheap debit. The gross is no better than its own no-event control
  (+1.4% net), so it's the structure and the tape, not the surprise.
- **The 50/20 put spread loses in absolute terms:** −10.9% net (t −2.13) on events and −16.9% on controls, and it
  is ≈ 0 gross. Selling the "expensive" 20Δ wing does not fund a long 50Δ put on single names after costs.
- **Covered call/put ≈ the stock ± noise:** C +0.49% (control +0.73%), D −1.06% (control −0.81%). The "guarantee"
  is definitional: 100% of beats with S_T > S_0 profit, but 47% of beats drifted DOWN, averaging −6.8%.

**Verdict: NULL (both primaries) · MECHANISM.** Changing the vehicle does not create the drift the stock test could
not find. The call spread's gross is ordinary upside, not PEAD, and costs take it. The put spread's "sell the rich
wing" leg does not pay for its long leg on single names.
