# I Fixed the Darvas Box: 74.2% Win Rate Over 33 Years

**Video:** `b8Usenu2QIY` · **Channel:** Quantified Strategies · **Watched:** 2026-09-30 · **Published:** 2026-09-28 · 4:00

> **2.5/5 · tested same day: NULL · YIELD METHOD.** The numbers are honest: our replication gives 282 trades, 74.8%
> winners, +0.343% per trade, PF 2.94 against his 279 / 74.2% / +0.34% / 3.08. But the entry signal adds nothing.
> With the same exit, buying SPY on ANY day wins 69.5% of the time and averages +0.283% per trade; signal days
> average +0.289% (diff +0.006pp, **t 0.09**). The win rate is the exit, and the "Darvas box" is decoration.

## Rules [01:03-01:38]
- Box top: highest high of the previous 12 trading days.
- Entry: SPY closes above the box top, but no more than 0.75% above it; volume above its 15-day average. Buy the
  next open.
- Exit (the same "QS exit" as the RSI video): SPY closes above the previous day's high, sell the next open.
- No stop. Average hold about three trading days.

## Claimed results [01:38-03:08]
SPY 1993-2026, TradeStation: 279 trades, 74.2% winners, +0.34% average trade, profit factor 3.08. PF by era 2.70
(1993-2004), 2.78 (2005-15), 3.94 (2016-26). "Cherry-picking test": lookbacks 11 / 13 / 16 / 18 / 20 days give PF
2.75 / 2.97 / 2.84 / 2.71 / 2.80. No costs, no benchmark, no return or drawdown figure. "Historical tendency, not a
forecast."

## Critique
- **No control.** The exit sells only after a strong close and there is no stop, so losers are held until they
  recover or the next up day arrives. That manufactures a high win rate for any entry in a rising index.
- **The robustness test varies the wrong knob.** The lookback (11-20 days) barely changes which days qualify; the
  0.75% cap and the volume filter, which do the selecting, get no neighbourhood.
- **Profit factor without exposure or return.** PF 3.08 sounds large; the strategy is long 10% of days and compounds
  at 2.6%/yr.
- **"Fixed Darvas" is a stretch**, which he half concedes [03:08]: Darvas traded growth stocks with a trailing box
  stop for weeks to months. This is a 3-day index trade with a sell-into-strength exit.

## Our test (2026-09-30, `run_darvas_spy.py`, pre-registered and committed before the run)
Log: `data/studies/logs/darvas_spy.log`. SPY 1993-01-29 -> 2026-09-18, 8,467 days, 351 signal days. Signals on raw
OHLC, returns on dividend-adjusted opens, costs 1 bp + $0.005/share per side.

| | n | win | mean trade | PF |
|---|---|---|---|---|
| claim | 279 | 74.2% | +0.34% | 3.08 |
| replication, gross (signal while long ignored) | 282 | 74.8% | +0.343% | 2.94 |
| replication, net | 282 | 72.7% | +0.315% | 2.71 |

Eras replicate less well (PF 1.90 / 4.01 / 4.43 vs his 2.70 / 2.78 / 3.94); PF is fragile to vendor differences.
Lookbacks 11-20: PF 2.82-3.05, as flat as he says.

- **PRIMARY (same instrument, same exit, vary only the entry day): NULL.** Signal days +0.289% (n 351, 72.6% win)
  vs every other day +0.283% (n 8,114, 69.4% win): **diff +0.006pp, HAC t +0.09**; halves +0.004 / +0.008pp; years
  positive 15/34.
- **S1 exposure-matched:** long days +11.3 bp vs flat days +4.0 bp, t 2.98. This looked like a near-pass, so a
  random-entry null was added AFTER the first run (labelled post hoc in the docstring): 351 random signal days, same
  book, same exit, 2,000 draws give a median 8.6 bp per long day (5-95%: 3.8-13.6), and 18% of random draws beat the
  strategy. Most of the 11.3 bp is the exit's arithmetic (every trade ends on a guaranteed strong day), not the entry.
  Only the win rate stands out against random entries (74.8% vs 69.5% median, 1.4% of draws higher); the mean trade
  does not (23% of draws higher).
- **S2 other indexes:** QQQ 199 trades, +0.079%, PF 1.16; signal vs other days **-0.237pp, t -2.06**. IWM 163 trades,
  +0.137%, PF 1.31; -0.151pp, t -1.24. The parameters do not transfer.
- Exploratory: strategy net CAGR 2.64%, max drawdown -6.8%, long 10.2% of days; buy-and-hold 10.83%, -55.4%.
- Exploratory ablation: a plain 12-day breakout day is WORSE than other days under this exit (-0.180pp, t -3.60, 6/34
  years positive), still worse with the 0.75% cap (-0.156pp, t -3.08); the volume filter only brings it back to
  average. That is index short-term reversal: buying SPY right after strength pays less than buying it after weakness.

## Against the ledger
- Same exit as the RSI video (`2026-09-26_tjL4wcI403E`). There the exit could not be tested (no survivorship-free
  OHLC for single names); on SPY it can, and it is the whole result: 69.5% winners on any entry day.
- Index-level mean reversion is the one family the ledger supports (bearish-high-IV put sale, AI Pathways row); a
  breakout entry on the index runs against it, and the ablation shows that.
- The house breakout is a single-name, multi-week trade and is not addressed by this test.

## Method yield
For any strategy with a sell-into-strength exit and no stop, run the any-day-entry control before reading the win
rate. And when a per-day comparison disagrees with a per-trade one, check it against random entries with the same
exit, because holding time differs.
