# Put spread vs the house stock trade on precision-tier breakouts (2026-09-24)

**Question (Gabe):** "put spread vs delta-matched stock is apples and oranges — our stock strategy gets stopped out
often, whereas put spreads are held to expiry." So compare each vehicle **under its own management**, on the **same
signal**, at **equal risk**.

**Script:** `run_breakout_putspread_vs_stock.py` (pre-registration in the docstring). Log
`data/studies/logs/breakout_putspread_vs_stock.log`, trades `..._trades.parquet`, v3 cache `data/cache/breakout_putspread_v3/`.

**Setup.** Precision-tier house breakouts, liquid panel, 2019-10 → 2026-02 (1,512 signals, 434 names).
- **S (stock):** the house process — buy the close, day-low stop judged on the close, exit on a close under the 20 EMA,
  cap 60, ±10 bps. Unit **R**.
- **P (spread):** same close, sell ~0.30Δ / buy ~0.15Δ put at the expiry nearest 30 DTE (the live scan's legs), **hold
  to expiry**, house fills (25% of each leg's bid-ask + commission), settled at intrinsic vs the chain's raw spot. Unit
  **ROC on max loss**. Both are return per $ of risk budget.
- Tradeability gate (the live scan's): short-leg bid-ask ≤ 25% of mid. **959 of 1,512 signals (63%) qualify.**

## Result

| arm (959 paired signals) | mean / $ risk | t | median | win % | days | p95 | worst |
|---|---|---|---|---|---|---|---|
| **S** stock, house process | **+0.327R** | 1.70 | −1.11 | 28 | 20 | +6.22 | −6.8 |
| **P** 0.30/0.15 spread, net | **−0.008** | −0.44 | +0.24 | 75 | 31 | +0.36 | −1.0 |
| P gross (mid) | +0.027 | 1.42 | | | | | |
| P2 0.45/0.30 spread, net (n 1,106) | −0.052 | −1.94 | +0.39 | 59 | 32 | | −1.0 |

**PRIMARY (P − S, paired): −0.336 per $ of risk, t −1.77**, halves +0.05 / −0.63 → **FAIL (NULL, leans stock).**
Per year the spread wins the weak breakout years (2019 +0.59, 2021 +0.43, 2022 +0.19, 2023 +0.24) and loses the strong
ones (2024 −1.29, 2025 −0.81). P2 − S −0.314, t −1.79.

## Gabe's mechanism is real — and it is not where the money is

| | n | stock | spread |
|---|---|---|---|
| stock stopped / lost (R ≤ −0.5) | 630 (66%) | **−1.51R** | **−0.12** |
| stock held / won (R > −0.5) | 329 (34%) | **+3.50R** | **+0.23** |

The spread survives the stop-outs almost untouched — exactly the point. But the stock's entire edge is its right tail
(p95 +6.2R vs the spread's +0.36 cap), and the spread sells that tail for a 75% win rate. On the same risk budget the
two roughly trade one for the other, with the stock ahead in trend years.

## Two findings that change how to read it

1. **The spread only fits the weaker signals.** The 37% of signals with no tradeable spread carry most of the stock
   edge: stock R **+1.39 excluded vs +0.21 included**; robust to outliers — capped at 10R **+0.63 vs −0.08**, win 36%
   vs 28% (the largest excluded contributor, SNDK +337R, is removed by the cap). Illiquid-option names are where the
   breakout pays, and they cannot be expressed as a spread at the live scan's liquidity gate.
2. **The breakout signal adds nothing to the spread.** The pre-registered control (0.30/0.15 on a random non-signal
   session, same name and month) read P − CTL **−0.108, t −5.94** — ⚠ **that is an artefact of my control design**:
   control days BEFORE the signal are selected on the known subsequent rise (ctl +0.185, diff −0.148, t −6.93); control
   days AFTER the signal give **+0.008, t 0.09**. Same defect as the retracted VCP same-name ±60 control. Honest reading:
   a put spread on a breakout day ≈ a put spread on a random later day in the same name.

**Capital-time (descriptive):** stock +12.5%/yr per $ of capital while deployed (sized to risk, it ties up ~23× the
risk unit) vs the spread +3.0%/yr (capital = max loss). The spread's capital efficiency does not survive its ~zero mean.

## Verdicts

- **Put spread vs the house stock trade, same signal, equal risk: NULL, leans stock** (−0.34 per $ risk, t −1.77).
  YIELD MECHANISM: the spread converts stop-outs (66% of signals, −1.51R → −0.12) into small wins by selling the right
  tail (+3.50R → +0.23), which is where the breakout's edge lives.
- **The spread has no edge on breakouts** (−0.008 net, t −0.44; vs a random later session +0.008, t 0.09).
- **METHOD:** a same-name-same-month control that can fall before the signal is outcome-selected — use post-signal
  control days only (pattern_test's `post`).
- Caveats: house cost model (25% of bid-ask) governs the spread arm; earnings inside the 30-day window not excluded
  (the live scan flags them); stock R uncapped (capped variants in §"two findings").
