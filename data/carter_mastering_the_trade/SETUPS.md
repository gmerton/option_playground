# Mastering the Trade — Setup Index

Skeptic-default leaderboard of setups from John F. Carter's *Mastering the Trade*.
Conviction 0–5 (independently-earned confidence, LOW until tested) · Risk 1–10 · Tested? no/partial/yes.
See each `setups/<slug>.md` for the full write-up. Convention and the regime-decay mandate: [README.md](README.md).

**Edition being read: 3rd (2019).**

| Setup | Type | Instrument | Conviction | Risk | Tested? | One-line verdict |
|-------|------|-----------|:---------:|:----:|:------:|------------------|
| [The Squeeze (TTM)](setups/squeeze.md) | swing/intraday | Equities, indices, futures | 1/5 | 4/10 | **yes** | **🔬 Backtested 3 ways, all closed — the observation holds, the trade doesn't.** Compression→expansion is real over 20y and *strongest in 2022-26* (no decay), but (1) the direction rule has NEGATIVE excess return in all 4 eras (−0.23%/−0.29% at 5/10d, t≈−2.6); (2) "longer squeeze = bigger move" is contradicted **monotonically** (1.003→0.906, t=−4.2), and bars still INSIDE the squeeze predict expansion better (t=+67) than the fire does (t=+12) — the edge is generic vol mean-reversion, not the trigger; (3) **the expansion is FULLY PRICED** — IV is cheaper (−0.91 vol pts) but realized comes in even lower (−1.03), so RV/IV = 0.980 vs 0.982 baseline (t=0.10, 9,143 fires w/ IV); in-squeeze premium is significantly *expensive* (VRP −0.59, t=−2.64). No directional and no long-premium edge. |
| [The Opening Gap (fade)](setups/opening-gap-fade.md) | intraday | ES/NQ/YM/TF (tested on SPY/QQQ/IWM/DIA) | 1/5 | 7/10 | **yes** | **🔬 Backtested — the headline statistic is a composition artifact.** The ~70% fill rate is carried by the 53% of days whose gap is <0.25 ATR (28 bp, untradeable); fill collapses monotonically with gap size to **35% at 0.5–1.0 ATR and 27% post-2022** — the gaps worth fading are the ones that don't fill. Fill% and expectancy move in *opposite* directions (beyond-range gaps: 52.7% fill but the better edge). No-stop edge is +2.6 bp/t=3.5 on SPY but **negative on DIA**, and every stopped variant brackets zero (path-order unresolvable on daily bars). What's real: it's a **high-VIX** trade (+6.9 bp t=3.7 vs −0.8 in low VIX), and Carter's "don't fade after a big trend day" veto is **backwards** (+11.9 bp, t=6.5). ~5.7% of days carry half the 33-year P&L. |

---

## Reading checklist

⚠ **Seeded from general knowledge of the book, NOT from your copy — confirm, correct, and delete
what isn't there.** I have not read your edition, and chapter organization varies between editions.
Treat this as a prompt to tick off, not a table of contents.

Setups I'm reasonably confident appear in the book:

- [ ] **The Squeeze** (Bollinger Bands inside Keltner Channels) — his signature indicator, later
      productized as the TTM Squeeze. **Highest-priority write-up:** fully mechanical, EOD-testable
      on the existing cache with zero new data.
- [x] **Opening gap fades** (ch. 7) — ✅ written up + backtested 2026-07-26. Still open: the book's
      own quoted fill percentages and point thresholds need to be read out of the user's copy and
      dropped into §2 of the write-up.
- [ ] **Pivot points** — floor-trader pivots as intraday S/R.
- [ ] **TICK extremes / fading the TICK** — market-internals reversal. ⚠ Highest decay risk in the
      book; the NYSE TICK's distribution has shifted substantially with ETF/basket flow.
- [ ] **3 Little Indians** — three-drives exhaustion pattern.
- [ ] **Hold and hedge** — options overlay to protect a position rather than sell it.
- [ ] **Scalps / market-internals intraday trades**

Add the rest as you hit them. Anything you find that isn't listed here is more trustworthy than
anything that is, since it came from the actual text.

## Priority order for write-ups

1. **Anything EOD-testable** (Squeeze first) — you can settle these against your own data.
2. **Anything with a stated statistic** (gap-fill rates, win rates) — cheapest possible falsification.
3. **Intraday/discretionary setups** — write up for completeness, but park the evaluation; they
   need 1-min data you don't currently have wired up.
