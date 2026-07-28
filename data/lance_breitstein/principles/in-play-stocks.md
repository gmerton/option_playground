# "In-play" stocks — the universe gate

> **Verdict:** ⭐ The strongest independent corroboration yet of this repo's standing conclusion
> that **selection is the strategy** — stated from inside multiple prop firms with a hard number.
> Also supplies a concrete, testable **upgrade to the ADR gate**: relative range expansion rather
> than an absolute threshold.
> **Type:** universe gate · **Conviction:** 3/5 · **Testability:** EOD ⭐⭐ · **Tested?** no
> **Source:** `7FbTZZNljSo` — "I Only Trade Stocks That Meet This Criteria" (2025-12-13)

---

## 1. The claim

> "Most traders only have maybe **25 stocks on any given day** that actually offer positive
> expected value. And out of those, often **fewer than five** tend to move your P&L in a real way.
> I've worked at many elite trading firms, I've managed a whole office, and month after month the
> pattern is the same: **five to ten stocks make up 90% of the firm's profits.**"

> "**Stock selection is the number one foundational skill** to making money as a trader… Even the
> best traders in the world would lose money if you force them to trade the other 99% of stocks.
> There is no edge there."

Framing: the market is a casino with ~5,000 games, almost all of which have negative edge; in-play
stocks are the "broken slot machines."

⚠ This is an *observation about where P&L concentrates*, from someone who ran an office and saw
the firm-wide distribution — not a backtest. But it is multi-firm, multi-month, and it is the same
shape as [[feedback-conviction-selection-is-the-strategy]] and the measured Luk selection alpha
(+4.84% at 20d over the screen-matched pool). Three independent lines now point the same way.

## 2. What makes a stock in-play — three categories

1. **News catalyst** — earnings, buyouts, regulatory decisions, contract wins, drug-trial results.
   ⚠ Gated on reaction, not on the event: "if a company reports news but the stock barely moves,
   no volume, no volatility, **that is not in-play**."
2. **Technical catalyst** — breakouts, breakdowns, multi-day squeezes, parabolic extensions. "A
   stock breaking a huge multi-month level with real velocity and volume."
3. **⭐ Volatility / range** — "in-play stocks move **multiple average trading ranges relative to
   their normal behavior**. If a stock normally trades in a 50-cent range but today it's moving
   four or five dollars in either direction **with clean levels**, that is in-play." Excludes moves
   that are "choppy, illiquid, and random."

Discovery tools: price scanners, news aggregators, unusual-volume tools, and social (Reddit,
StockTwits, X) — with an explicit warning about small-cap bias in the social sources.

## 3. ⭐ The testable upgrade to the repo's own gate

The repo's `GATES` tier uses **ADR(20) ≥ 3.5% — an absolute threshold**. His criterion #3 is a
**ratio**: today's range ÷ the stock's own normal range. These are materially different filters:

- Absolute ADR selects a *class* of permanently volatile names.
- Relative range expansion selects a *moment* — a normally quiet stock waking up.

The repo has already established that ADR is the single most valuable gate it has (`REQ-only`
+1.23%/trade → `GATES` +2.92% on adding ADR alone, the largest jump in the ladder). If a *relative*
version does better, that is a direct improvement to production code with no new data required —
both range and a trailing average of range are already computed in `arch_lib.prep`.

**Proposed test:** replace `adr20 >= 3.5` with `range_today / ADR(20) >= k` for k ∈ {1.5, 2, 3},
and run it through the existing tier ladder. Also test the two in combination, since they are not
mutually exclusive.

Secondary: his volume emphasis is stronger than the repo's `vol_ratio >= 1.5` (the CONFIRMED
tier), and he treats volume as **necessary** for a catalyst to count at all — worth testing as a
required gate rather than a tier refinement.

## 4. Objective assessment

- **This is the least hype-driven video of the batch.** The claim is structural ("most tickers
  have no edge"), the mechanism is stated (volume, price discovery, clean levels), and the advice
  is a filter rather than a trade.
- **Red flags:** three examples (CRCL, IonQ, QCOM), all winners, all after the fact. Course/stream
  plug. "$100M verified profits" opener again.
- ⚠ **"Clean levels" and "choppy vs clean" are the discretionary joint** — and they are doing real
  work in the definition. A mechanical version will capture the range expansion but not the
  cleanliness, so expect the tested version to underperform his description.
- ⚠ **Selection bias in the claim itself.** "5–10 stocks make up 90% of profits" is measured
  *ex post* on firms whose traders were already good at finding them. It does not establish that
  the in-play criteria identify those names *in advance* — which is exactly what a test would
  need to show.

## 5. Overlap with the rest of the repo

- **Corroborates** [[feedback-conviction-selection-is-the-strategy]] from an independent source
  and a different vantage (firm-wide P&L distribution rather than one trader's log).
- **Directly upgradeable into** `lib/interface/premarket_watchlist.py` — the ADR gate is already
  there and already flagged as mis-tiered (see [[feedback-breakout-scorecard]]: ADR is marked
  "optional" but does nearly all the work). This proposes changing its *form*, not just its tier.
- **Connects to the young-stock blind spot** — he names fresh IPOs as an in-play category, and
  every backtest in the repo excludes them via SMA200 + 400-bar minimums.
