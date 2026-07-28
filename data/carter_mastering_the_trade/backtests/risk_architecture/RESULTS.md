# Risk-Architecture Test — RESULTS

**Run:** 2026-07-26 · `run_arch_test.py` → `run_portfolio.py`
**Universe:** 299 most-liquid names as of today, 2006–2026 (`../squeeze/longhistory.parquet`)
**Signals:** 22,774 · **Grid:** 10 stops × 6 exits = 60 architectures, all trading the *same* trade list

## The hypothesis

> A breakout setup's job is not to forecast — it's to locate a tight, logical invalidation level.
> Tight stop → small risk per share → large position at fixed fractional risk → a mediocre entry
> becomes a convex payoff. Therefore expectancy should be positive at tight stops with a trailing
> exit, and flat-to-negative at wide stops with a fixed target.

**Verdict: refuted, decisively, in both its naive and its structural form.**

---

## 1. Tight stops on a weak entry are not convex — they are ruinous

Portfolio CAGR, mean across the six exits:

| stop | mean CAGR % |
|---|---:|
| 3.0% | **+3.72** |
| 2.0 ATR | +3.25 |
| 20-EMA | +3.15 |
| 5.0% | +3.15 |
| 10d low | +2.57 |
| 1.0 ATR | +2.33 |
| 20d low | +1.90 |
| bar low | −0.20 |
| 1.5% | −1.27 |
| **1.0%** | **−7.91** |

Monotone in the wrong direction over the tight end. The worst cell in the grid is 1.0% stop +
2R target: **−15.3% CAGR, −96.2% max drawdown**.

**The capital-recycling argument dies on its own terms.** That same worst cell took **7,956
trades — the most of any of the 60 cells** (34.9% of signals got a slot, versus 4–17% elsewhere).
It had maximum turnover, maximum opportunity to compound, and it lost 96% of the account. Faster
recycling of a worse per-trade outcome is just a faster way to lose.

Mechanism, no mystery: at a 1% stop the dumb entry is **stopped out on 76–87% of trades**, median
hold 2 days. And because position size = 0.3% risk ÷ 1% stop = 30% of equity, the no-leverage cap
allows only ~3 concurrent positions. Maximum concentration paired with a near-certain stop-out.

## 2. A *structural* stop is no better than an arbitrary one of the same width

This was the version of the hypothesis worth testing — Luk doesn't say "use a 1% stop," he says
place it at a level that proves the trade wrong. Matched-width comparison:

**bar low** (mean width 2.25%, structural) vs **1.0 ATR** (mean width 2.30%, arbitrary):

| exit | 1.0 ATR | bar low | structural − arbitrary |
|---|---:|---:|---:|
| close<10EMA | −2.48 | −6.94 | **−4.47** |
| close<20EMA | +3.71 | −2.33 | **−6.04** |
| close<50EMA | +5.39 | +5.28 | −0.11 |
| hold 20d | +2.84 | +0.88 | −1.96 |
| target 2R | +2.38 | −0.44 | −2.82 |
| target 4R | +2.15 | +2.38 | +0.23 |

Structural is worse in four of six, tied in one, better in one. **At equal width, placing the stop
at a "logical level" bought nothing.** Same story for the wider structural stops (10d low, 20d low,
20-EMA) — they land mid-table, indistinguishable from arbitrary stops of comparable width.

⚠ This result is bounded by data resolution — see Limitations §5.

## 3. Once the stop is survivable, the EXIT is the variable that matters

Mean CAGR by exit, across all ten stops:

| exit | mean CAGR % |
|---|---:|
| close<50EMA | **+3.71** |
| target 4R | +2.37 |
| hold 20d | +2.21 |
| target 2R | +0.98 |
| close<20EMA | +0.39 |
| close<10EMA | **−3.23** |

- Spread across exits: **6.94 pp**
- Spread across stops: 11.63 pp — but that is entirely the 1.0% catastrophe
- Spread across stops **excluding the two unsurvivable rows: 3.92 pp**

So: avoid a stop too tight for your entry, and after that the exit rule moves the outcome roughly
**twice as much** as the stop does. **`close<10EMA` is negative in all ten stop rows** — the most
consistent single effect in the grid. Cutting winners fast is the reliable way to lose.

## 4. ⚠ Nothing in the grid beat buying the index

| | CAGR | max DD | avg exposure |
|---|---:|---:|---:|
| Best cell (3.0% stop, close<50EMA) | **6.46%** | −27.4% | 85.6% |
| 2nd (3.0%, target 4R) | 6.45% | −29.2% | 88.2% |
| **SPY buy & hold, same window** | **~10.7%** (8.83% price + ~1.9% div) | −56.5% | 100% |

All 60 architectures underperform SPY. The best one was **86% invested on average** — this is not a
low-exposure strategy earning a respectable risk-adjusted return; it was almost always fully in the
market and still lost to the index by ~4 pp/yr. It does show a better max drawdown (−27% vs −56%),
but the sim marks equity only on realized exits, which understates drawdown — so even that edge is
soft.

**With a dumb entry, no risk architecture produced a strategy worth trading.**

---

## What this actually means

The risk architecture is **not a return generator**. It cannot manufacture edge from a weak signal —
it is a *survival constraint* that bounds damage. Which forces the conclusion the other way round:

> **The edge has to be in the selection. The tight stop is a consequence of high-conviction entry
> location, not a substitute for it.**

Luk can run a 1–1.5% stop because his entries sit at points where 1–1.5% of adverse movement is
genuinely informative. On a random 20-day closing high it is noise, and the data says so: 76–87%
stop-out. Tight stops and entry precision are **complements, not substitutes** — which is exactly
his own stated rule, *"always hunt for the entry tactic that tightens the stop,"* read in the
correct direction. The entry tactic comes first.

This *confirms* the repo's standing note that conviction selection IS the strategy, and supplies
the first direct evidence for it rather than an assertion.

## 5. Limitations — read before citing any of this

1. **Survivorship, and it is not neutral.** The universe is the 299 most liquid names *today*; all
   survived. The inflation grows with holding period, so it pushes directly toward "slow exits and
   wide stops win" — i.e. finding §3 is partly manufactured and its magnitude should be discounted.
   Findings §1 and §2 are driven by stop-out rates and are not affected by it.
2. **Wrong universe for the style.** These are mega-caps. Luk and Qullamaggie trade high-ADR
   small/mid caps, where both the breakout behaviour and the shakeout frequency differ. A proper
   test needs a broader, delisting-inclusive universe.
3. **Drawdowns understated.** Equity is marked only on realized exits; open losers are invisible.
   This flatters the wide-stop/slow-exit cells — again the ones that won.
4. **Sell-into-strength untested.** Every exit here is weakness-based (trail) or a fixed target.
   Luk's most-repeated exit rule — scale out into strength — is not in the grid.
5. **EOD resolution is the real boundary on §2.** A 1.5% stop below a *precise intraday pivot
   entry* is a different object from 1.5% below the next day's open. This test cannot distinguish
   them, so it refutes "tight stops create convexity mechanically" but leaves open "tight stops
   work when the entry is intraday-precise." That question needs 1-minute data.

## Files

- `run_arch_test.py` — signal generation + 60-cell trade simulation → `arch_trades.parquet` (1.36M rows)
- `run_portfolio.py` — capital-constrained portfolio sim → `portfolio_results.csv`
