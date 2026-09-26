# Self-Exciting Behavior and Detecting the End of Price Trends (Hawkes-process exit)

**Video:** `wdsiZBIhAFw` · **Watched:** 2026-09-26 · **Published:** 2023-04-18 · 8:20

> **3/5 · ⭐ one NEW test queued (not run).** A volatility-decay exit: trends end when the volatility burst that
> came with them decays. Every exit we've tested is price-based (trails, partials, profit locks, Qullamaggie's
> relay) and all were NULL or INVERTED; this one uses a different input. His evidence is weak (BTC hourly, no
> costs, no benchmark, and the exit is never isolated from the entry), but the axis is new.

## Raw notes
- [00:49] Normalised range = (log high − log low) / ATR(336) on log prices (hourly BTC, 2-week ATR).
- [01:36] Volatility clusters (self-excitation); after the March 2020 crash it decays as the trend fizzles.
- [02:24] Hawkes process (as he codes it): `out_t = out_{t−1} · e^{−κ} + x_t`, then × κ to normalise. Smaller
  κ = slower decay. Credit: blogger "Trader with an 8" (signed-volume Hawkes indicator).
- [03:12–04:48] Rules: rolling 1-week 5th and 95th percentiles of the Hawkes series. When it crosses ABOVE the
  95th, take the sign of the price change since it was last below the 5th (long if up, short if down). **Exit when
  it crosses BELOW the 5th.**
- [05:36–06:23] κ 0.1, lookback 168: PF 1.07; longs 58% win, avg +2.9%; shorts 49%, +1.1%; in the market 50% of
  the time. **No fees.**
- [06:23–07:12] 5 κ × 5 lookbacks = 25 versions, **all PF > 1** — the neighbourhood-robustness check.
- [07:12] "Its main power is the exit. I use this exact exit on many of my momentum-based strategies."

## Critique
- PF 1.07 gross on hourly BTC, where turnover costs would matter a lot.
- The long side dominates in a BTC bull sample → at least partly beta. No buy-and-hold benchmark.
- The headline claim ("the power is the exit") is never tested: entry and exit are one rule, and there's no
  comparison of the exit against another exit on the same entries.

## For this book → queued test (TEST_INDEX §10)
**Vol-decay exit vs the house 20-EMA close trail on precision-tier breakouts.** Same entries (the profit-lock pool,
`data/studies/profit_lock/profit_lock_trades_2026-09-20.parquet`), paired per trade, scored in % return (not R).
Daily bars: normalised range = (H−L)/ATR, Hawkes κ, rolling percentile threshold; exit on the first close after the
Hawkes series drops below its rolling low percentile, with the house disaster stop kept. Charge the κ × lookback grid
with p_opt (the harness already has it). Also report the tail: the book's edge lives in the few big winners, and an
exit that fires when volatility calms could cut them in a quiet grind (Tito's "grind" archetype). Local, ~½ day.
