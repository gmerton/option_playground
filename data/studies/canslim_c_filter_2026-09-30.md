# [BB-2] CAN SLIM "C" (quarterly EPS growth) as a universe filter (2026-09-30)

**Verdict: NULL · UNDERPOWERED primary.** Source: Ross Haber CAN SLIM review (TraderLion afkUTFNVpso), queued by Gabe
2026-09-23. Pre-registration: `run_canslim_c_filter.py` docstring (committed before the run). Log:
`logs/canslim_c_filter.log`; cells `logs/canslim_c_filter_cells.csv`.

C = the last three reported quarters each ≥ +25% EPS YoY (yfinance `eps_act`, positive base, point-in-time at the
reaction session, membership as of the prior close). `liquid_panel_2009`, 2010-01 → 2026-09, ADR-matched forward
excess, paired per non-overlapping date, halves split 2018-01-01.

| cell | dates | median names | Δ (pp) | t | halves |
|---|---|---|---|---|---|
| **PRIMARY INT∧C vs INT, 20d** | 88 / 210 | 2 vs 10 | **−0.43** | **−0.85** | −0.32 / −0.47 |
| (a) C vs eligible panel, 20d | 210 | 37 | +0.20 | 1.36 | −0.00 / +0.38 |
| (a′) C vs EPS-covered panel [info] | 210 | 37 | +0.19 | 1.34 | −0.01 / +0.38 |
| (b) INT∧C∧accelerating vs INT | 10 | 0 | — | — | too thin |
| (c) INT∧EPS ≥ +100% vs INT | 79 | 1 | −0.13 | −0.23 | +1.87 / −0.35 |
| (d) INT∧C vs INT, 63d | 23 / 66 | 1 | +0.86 | 0.40 | −1.90 / +1.44 |
| (e) primary, ex 10 sessions post-report | 76 | 1.5 | −0.39 | −0.65 | −0.13 / −0.47 |

- The primary has the **wrong sign** and is thin. On this panel INT is only ~10 names a day (the $200M ADDV floor
  is nominal, so the early 2010s are sparse), and INT∧C is 2 a day, so only 88 of 210 dates qualify. Per year: 7 up,
  8 down.
- **The powered cell is (a)**, C across the whole eligible panel with 37 names a day on every date: +0.20pp at 20d,
  t 1.36, and the pre-2018 half is exactly zero. Whatever EPS growth carries is small and recent (2023–26
  +0.3 to +1.4pp a year). That points to the current AI-earnings tape, not a durable selection lever.
- The false-negative check (did a thin sample hide a positive?) comes back no. Cell (a) has full power and still
  does not clear 2.57, and its first half is flat.
- Caveats as pre-declared: survivorship (today's liquid names), adjusted rather than GAAP EPS, 451 of 592 eligible
  names/day covered.

**Consequence:** no change to the INT universe. The sales-confirmation arm (EDGAR revenue) was gated on the EPS arm
clearing or nearly clearing. It did neither, so it is not queued.
