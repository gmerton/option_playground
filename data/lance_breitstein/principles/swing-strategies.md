# The two swing strategies — mean reversion and continuation

> **Verdict:** ⭐ His most testable material, and it contains a **direct contradiction of Martin
> Luk** on stop width that reframes the repo's central open question. Both strategies are
> specified precisely enough to backtest on daily bars.
> **Type:** setup (swing) · **Conviction:** 2.5/5 · **Testability:** EOD ⭐⭐ · **Tested?** partial
> **Source:** `k-X0164r66U` — "The 2 Swing Trading Strategies That Made Me Millions" (2026-05-27)

---

## 1. Strategy A — mean reversion / "right side of the V"

- **Setup:** a sharp, extended move accelerating at an unsustainable rate of change, ending in
  **capitulation characteristics — massive volume**. "Reversals usually happen when the emotional
  intensity reaches maximum levels."
- **Trigger:** he does *not* buy oversold. He waits for **the trend to break** — buying "the right
  side of the V," i.e. after the reversal begins.
- **Stop:** initial stop at the lows.
- **Trail:** prior daily bar lows.
- **Provenance:** his best trade ever, ~$10M, was this — the Nikkei panic of August 2024.

## 2. Strategy B — continuation

- **Setup:** **major multi-month breakouts, ideally with a catalyst attached.** "I want a stock
  that institutions suddenly care about." In-play, hot theme, high attention/volume.
- **Trigger:** buy the breakout level.
- **Instrument:** stock **or short-term call options** (the only place he mentions options).
- **Stop:** break below the resistance level; "or if I want to be looser, I use the lows of the day."
- **Trail:** prior daily bar lows, **or** a looser MA — the 20-period on the daily.
- **Rationale:** institutional demand is slow. "When institutions need exposure to a theme, they
  don't buy for 20 minutes. They buy for weeks and sometimes months."

Both are recognisably the same family as [[martin_luk]] and Qullamaggie — Strategy B especially,
which he credits to Qullamaggie by name.

## 3. ⚠⚠ The passage that contradicts Luk — and my own thesis

> "One of the biggest mistakes I made early when transitioning into swing trading is that my
> entries and exits were still **too intraday focused**… let's say a stock has a beautiful weekly
> breakout setup with a **logical stop 8% lower** based on the daily chart. Old Intraday Lance
> would enter the trade and then stop himself out because the stock dipped a percent and a half
> intraday… **If you're trading based on the daily chart, your risk management needs to align with
> the daily chart.**" (06:50)

> "As an intraday trader, I was accustomed to very tight stops — sometimes my stop might only be
> $0.50 or $1 away — but **swing trading naturally requires wider stops** because higher-timeframe
> structure is wider. My problem was I initially kept sizing way too aggressively relative to
> those wider stops… **If your stop is three times wider, your size probably needs to be three
> times smaller.**" (07:41)

**This is the exact opposite of Luk**, who runs 1–1.5% stops on swing trades and says performance
"lifted off" as he tightened them from 5–8%. Two demonstrably successful traders, opposite advice,
on precisely the question `HOW_THEY_DO_IT.md` identified as the crux.

**It also independently supports this repo's own swing results.** `RESULTS.md` found tight stops
catastrophic on daily-bar swing entries (94% stop-out at 1.5%, −96% drawdowns) and wide ATR stops
best. Breitstein names that exact failure mode — tight intraday stop on a daily setup — as his own
costliest early mistake. The backtest and the practitioner agree.

⟹ **The 6× sizing lever appears to be an INTRADAY phenomenon, not a swing one.** My
`HOW_THEY_DO_IT.md` over-generalized it to the swing horizon I was actually simulating. See the
corrections section there.

## 4. His own admission on where the edge is

> "There is generally **less absolute edge in swing trading** compared to intraday trading.
> Intraday trading still has more inefficiencies because emotions, liquidity imbalances, and panic
> happen so quickly… Swing trading, at the expense of scalability, is often more efficient. As a
> result, your edge can feel thinner and variance much higher."

Worth taking seriously as a partial explanation for why every swing backtest in this repo lands
near or below SPY. It also sets up the trade-off he states plainly: **intraday has more edge but
is liquidity-constrained; swing has thinner edge but "almost infinite scalability."** That is the
same capacity ceiling Qullamaggie describes.

## 5. Testable extractions, ranked

1. ⭐⭐ **Strategy A, fully mechanical**: extended move + capitulation volume → enter on trend
   break → stop at lows → trail prior daily bar lows. EOD-testable, and gives the repo a
   **mean-reversion** setup where everything tested so far has been momentum continuation.
2. ⭐ **Trail on prior daily bar lows** — a trail type not in the six already tested
   (`close<10/20/50EMA`, hold-20d, target 2R/4R). Cheap to add.
3. **Strategy B vs the existing GATES entry** — his is "multi-month breakout + catalyst + hot
   theme"; the repo's is "20-day closing high + Stage 2 + ADR + dollar volume." The multi-month
   base length and theme membership are both testable additions.
4. **Short-dated calls as the vehicle** on continuation breakouts — the repo has the options data
   (`silver.options_daily_v3`) to price this, and it has never been tested.

## 6. Red flags

- Every example is a winner (Nikkei, IonQ, semis). No losing swing carried through.
- Two course/other-video plugs.
- "Best trade of my career made me over $10 million" — the opener. Unverifiable, and note this is
  a *single trade*, which tells you about tail size, not about a repeatable process.
- ⚠ **The strategies are described qualitatively.** "Capitulatory characteristics," "unsustainable
  rate of change," "chart screaming to me that it's ready to move," "hot theme" — all judgment.
  Any backtest is a strawman of the discretionary original, and should say so.
