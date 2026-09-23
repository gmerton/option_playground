# Review: "Part 2: The Best Options Strategies for a $10K Account" (Nick Galarnyk, 2026-06-16, ZetDnCq7EhI) — 3/5

Reviewed 2026-09-23. 55:44, public, 831 views, 10,145-word transcript. Live Zoom session with Q&A, screen
sharing IBKR; part 2 of a series (part 1 — "foundation and mindset" — not captured here). Funnels to
one-on-one coaching (~25 hours, his figure).

Transcript: `videos/education/2026-06-16_ZetDnCq7EhI/`.

## What it says

**Framing:** a $10K account cannot buy 100 shares of NVDA/TSLA/MU, so options are the only access to
those names. The goal is consistency, not home runs.

**The ladder of structures, in his order of preference:**

1. **Long single calls/puts** — introduced, then explicitly rejected as a primary vehicle: too much
   percentage risk per trade.
2. **Vertical spreads — his core recommendation.** Defined risk, low capital. He walks in-the-money,
   at-the-money and out-of-the-money variants on NVDA and shows the risk/reward shifting with strike
   choice (risking ~6 to make ~14; or ~2 to make ~8 further OTM).
3. **Butterflies** — "a compromise on taking a directional bias", and he stresses you are a **net seller**.
   Explicitly says do *not* target max profit (that requires pinning the body); take it when it doubles.
4. **Poor man's covered call** — long-dated ITM call, sell shorter-dated calls against it, grinding the
   cost basis down each cycle.
5. **Cash-secured puts** — "not wrong, just a very slow way" for a small account; better once large.
6. **Covered strangle** — better for larger portfolios.

**Method worth noting:** his first step on any name is to read the **straddle price** to get the market's
expected move, then draw that range on the chart and structure the trade inside it.

**Liquidity:** mega-caps only. Avoid anything where the bid-ask exceeds **10% of the contract's cost**;
target 10–20 cent spreads. Underlying average daily volume correlates with option-chain volume.

**Expirations:** 0DTE — "be ready to say goodbye to it." Longer-dated contracts cost less per day.

**Management:** mechanical stop at **50% of max loss**; de-risk by selling one of two contracts to create
a free position; close butterflies before expiry (a long Q&A segment on assignment mechanics — if you let
a call fly expire above the body you can end up short 100 shares the following Monday).

**Risk and psychology** — roughly a third of the runtime, and the strongest material. The goal of trading
is *minimising emotional attachment to each decision*, not maximising profit. A long anecdote about a
student who made ~$5M in 2020–22, averaged down into the 2023 tech drawdown, and gave back ~$3.6M. ⭐
"I put little credence into anyone that shows me one good trade" — it is what you do repeatedly that
matters.

## ⭐ Where it agrees with our evidence — and the liquidity match is precise

**Liquidity discipline.** Our own finding: short-dated single-name premium selling is **net negative
because costs run 136% of gross**, and *"liquidity is the gate, tradeable set = SPY + NVDA/AMZN/AAPL/V."*
His rule — mega-caps only, reject anything wider than 10% of contract cost — lands on essentially the same
universe from first principles, and it is **operational**, which most creator advice is not. Our own cost
model charges 25% of the quoted bid-ask, so a 10% gate is the right order of magnitude.

**Straddle price as the expected move.** This is the `vrp_panel` idea in miniature — read what the market
has priced rather than forecasting, then position inside it. Sound.

**0DTE scepticism.** Matches `one_day_straddle_study` (no edge; every exit ≈ −30% of premium).

**"One good trade is not evidence."** That is our standing rule on the journal, stated by a creator
against his own marketing interest.

**Defined risk over naked.** Agrees, and for the right reason (he never claims it improves expectancy).

## ⚠ Where it conflicts, or is simply unevidenced

1. ⛔ **The poor man's covered call is contradicted.** A PMCC is a diagonal. Our path study: after the
   truncation erratum, the clean re-run found **no edge in single/double calendars, diagonals or condors
   on ETFs, and stocks lose 8–18%**. He presents it as a solid small-account grinder with a worked
   31% return in 31 days, from one favourable NVDA path. This is his weakest recommendation.
2. ⚠ **Butterflies: right structure, wrong conditioner.** Flies *do* work in our book — the SPY 1-day
   2× iron fly on **positive dealer-gamma days** passed pre-registration (+5.8% on max risk), replicated
   on QQQ and extended to mega-caps. But that edge is conditioned on a **gamma regime**, not on a
   directional target. His fly is a directional bet dressed as a premium sale. Same structure, different
   trade.
3. ⚠ **The mechanical 50%-of-max-loss stop is unsupported.** Our stop work is a graveyard: 0 of 20 stop
   variants beat no-stop on the straddle, and a real −50% stop on the daily close scored **+3.89% vs
   +4.14% for holding**. Profit-locks and trims all cost. He states it as settled practice.
4. ⚠ **No evidence of any kind.** No backtest, no track record, no equity curve, no win rate. Every
   number is a hypothetical constructed live on an NVDA chain. He is explicit that one trade proves
   nothing — and then offers only hypothetical single trades.
5. ⭐⭐ **The load-bearing input is never sourced.** Every example begins "let's say you think NVDA goes to
   230 by July 17th." The entire video is *structure selection conditional on a directional view*, and
   where that view comes from is never addressed. **That is the actual hard problem** — and it is the one
   our own book says is unsolved: six independent angles now say mechanical selection cannot be improved,
   and our one certified bucket (index premium in stress, SPY t 6.07 / SPX t 5.21) is explicitly *not*
   a directional bet.
6. ⚠ **The stated expectation is more aggressive than it sounds.** "$5K on $10K over 6–7 months, which
   doesn't sound very sexy" is ~50% in half a year, presented as the modest outcome.

## Testable claim extracted

**Does a poor man's covered call beat simply holding the long-dated call, on mega-caps?** Directly
runnable against the existing diagonal machinery and `options_daily_v3`: long ~90 DTE ITM call, roll a
~30 DTE short call against it each cycle, versus the naked long call, priced at real fills. Prior: the
short call is a drag once costs are charged, consistent with the path study's finding that diagonals on
stocks lose 8–18%. ⚠ Pre-register that the PMCC caps the right tail while the long call keeps it — so
report the tail percentiles, not just the mean, or it will look like a risk win the way the 21-DTE and
spike-branch results did.

## Score rationale — 3/5

The **risk, psychology and liquidity thirds are genuinely good** and align with things we measured the
hard way: the round-trip leak, the cost gate, the worthlessness of single-trade evidence. His liquidity
rule is the most directly adoptable thing any creator in these KBs has offered.

It does not score higher because the **strategy content is unevidenced and one recommendation is
contradicted outright**, and because the whole framework sits downstream of a directional view he never
justifies. It is a competent teaching video about *structure*, presented as a video about *how to grow an
account* — and those are different claims.
