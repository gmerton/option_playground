# Sizing the 12-1 momentum sleeve: leverage x concentration (2026-10-02)

Script: `run_momentum_sizing.py` (pre-registered 4ab14a3, before the run; decision rule declared there). Log
`data/studies/logs/momentum_sizing.log`; full grid `momentum_sizing_2026-10-02.csv`. Books from `run_momentum_topn.run`
(chain_spot incl. delisted, 180 months 2011-02 → 2026-01, 10 bp/side). Leverage reset monthly, financed at the 3-month
T-bill + 1.5% (T-bill averaged 1.47%/yr). Forward = 10,000 block-bootstrapped 10-year paths. HAIRCUT = every book's
monthly return minus 0.33pp (half the certified excess), because an in-sample t 2.9 mean overstates the future.

## Verdict: leverage cannot get this sleeve near 100%/yr · the rule picks the decile at 1.0× · T30 at 1.0× is the practical upgrade

Selected cells (month-end drawdowns; intramonth is deeper):

| book × L | hist CAGR | hist maxDD | HAIRCUT CAGR | HAIRCUT boot P(DD > 50%) | HAIRCUT boot 5th-pct 10-yr CAGR |
|---|---|---|---|---|---|
| D1 (decile) 1.0× | 18.7% | 28% | 14.1% | 2.8% | +3.7% |
| D1 1.25× | 21.9% | 35% | 16.1% | 13.3% | +3.0% |
| D1 1.5× | 24.9% | 41% | 17.8% | 31.8% | +2.1% |
| D1 2.0× | 29.8% | 52% | 20.0% | 79.6% | −1.0% |
| **T30 1.0×** | **22.9%** | **30%** | **18.2%** | **9.5%** | **+4.4%** |
| T30 1.5× | 30.3% | 44% | 22.9% | 54.2% | +2.0% |
| T20 1.0× | 23.8% | 35% | 19.1% | 15.6% | +3.9% |
| T30 3.0× (best CAGR in the grid) | 36.7% | 77% | 21.2% | 99.9% | −17.6% |

- **The ceiling is ~35%/yr, not 100%.** Leverage multiplies volatility as fast as return, and volatility drag eats the
  rest: on history the growth-optimal (Kelly) leverage is 2.4–3.0× and tops out at 34–37% CAGR with a 70–80% drawdown.
  Under the haircut, Kelly falls to 2.0–2.4× and 3× is *worse* than 2× (T20 3×: 17.8% CAGR, 89% drawdown).
- **Decision rule (declared in advance):** the largest cell with haircut P(DD > 50%) ≤ 10% and a non-negative 5th-pct
  CAGR → **D1 at 1.0×**. Every levered cell fails on drawdown; even 1.25× on the decile has a 13% chance of a >50%
  drawdown in 10 years.
- **T30 at 1.0× also passes** (9.5%, just inside the limit) and earns ~4pp/yr more than the decile in both scenarios; the
  rule's tie-break chose the decile only because it is less concentrated. T30's extra mean partly comes from a few huge
  winners (the 20-name study's winsorised t fell to 1.47), so treat the +4pp as optimistic.
- **The worst months are the known momentum crashes:** 2020-03 for the decile (−19% unlevered, −38% at 2×), 2022-06
  for the concentrated books.

**Consequence.** Run the sleeve unlevered; T30 is a reasonable choice over the full decile if he accepts slightly more
concentration risk. The sleeve is a ~15–20%/yr base, not a route to triple digits; that has to come from elsewhere.
