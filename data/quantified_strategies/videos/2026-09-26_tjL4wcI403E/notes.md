# This RSI Strategy Won 68% of 1,321 Trades

**Video:** `tjL4wcI403E` · **Channel:** Quantified Strategies · **Watched:** 2026-09-26 · **Published:** 2026-09-26 · 4:48

> **2.5/5 · no new test.** Best-specified strategy video we've reviewed: every rule is stated, fills are next-open,
> and the data includes delisted stocks. But there are no costs, no benchmark or control, and the evidence is a
> win rate and an equity curve. The mechanism (short-term reversal inside an uptrend) is already in the ledger as
> real but PARKED on survivorship.

## Rules [01:03–02:06]
- Universe: Nasdaq-100 constituents (Norgate, "includes delisted stocks"). Max 5 positions open.
- Trend: close > 200-day SMA.
- Oversold: RSI(3) < 20.
- Weak close: IBS = (close − low) / (high − low) < 0.3.
- Exit ("QS exit", "used for about three decades"): close > yesterday's high.
- Entries and exits at the NEXT open, market order.

## Claimed results [02:06–03:10]
1,321 trades, win rate 68%, average +1.1% per trade, average winner ≈ average loser, 11% annual return while invested
~16% of the time, max drawdown 17% ("the NASDAQ index fell over 80% during the dot-com burst"). [04:11] "This is a
theoretical backtest... trading costs, slippage, liquidity and execution all matter."

## Critique
- **No costs.** At +1.1% gross per trade, 20 bp round trip leaves most of it; this probably survives costs in
  Nasdaq-100 names, but it isn't shown.
- **No control.** A 68% win rate over 2–5-day holds in a rising index isn't an edge by itself. The needed comparison
  is same-date uptrend names that did NOT dip (or the same name on a random day), which is exactly what our ladder
  test did.
- **The exposure argument is half right.** 11% at 16% exposure only beats buy-and-hold if the idle 84% earns
  something. It's a genuine portfolio-construction point (combine with other sleeves), not evidence of edge.
- **Max 5 positions** makes the path depend on which signals win the slot on crowded days; not described.
- Nasdaq-100 membership must be point-in-time for the delisted data to matter; not stated.

## Against the ledger
- ⭐ **Already measured:** the confirmation-ladder test (2026-09-25) found the bare dip in a broad uptrend beats
  same-date non-dipping uptrend names by **+0.7…+1.4pp over 20 days, t 2.5–5.5, 16/17 years**, i.e. short-term
  reversal inside uptrends. PARKED because the liquid panel is survivor-biased, which flatters exactly this trade.
- Pullback entries on leaders (Luk/Ariel EMA pullbacks): weaker than the breakout entry.
- RSI(14) as a gate: a VIX proxy on put spreads; Ryan's RSI + Bollinger swing 1.5/5.
- What's new here is only the exact trigger (RSI(3) + IBS) and the fast exit (close > prior high). Testing them adds
  nothing until the survivorship blocker is gone: chain_spot is survivorship-free but closes-only, so neither IBS nor
  the QS exit can be computed on it. The unblocker is the paid point-in-time OHLC panel (`run_build_pit_panel.py`).
