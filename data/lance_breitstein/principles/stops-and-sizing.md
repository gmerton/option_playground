# Stop placement and exponential bet sizing

> **Verdict:** Two videos, one coherent system: **the setup dictates the stop, the stop dictates
> the size, and the grade dictates how hard you push.** Contains the clearest available statement
> of the mechanism behind the sizing lever — and a **10× variable-risk model that directly
> contradicts Luk's near-constant 0.3%.**
> **Type:** stops / sizing · **Conviction:** 3/5 · **Testability:** partly EOD, partly untestable
> **Tested?** partial — one claim tested and NOT confirmed (§3)
> **Source:** `WgRQWJq54OY` "How to Stop Guessing with Your Stop Losses" (2025-12-11) ·
> `eDdpTNB04ws` "The Trade Sizing Strategy that Made Me Millions" (2025-10-25)

---

## 1. Stop placement — five steps

1. **Strategic sense.** "Your stop should be placed at the point where you perceive **expected
   value to be going negative**" — normally where the thesis is invalidated. Breakout → back below
   resistance. Trend → below the relative lows. Surfing an MA → close below the MA. Trendline →
   the break.
2. **Timeframe match.** "If I enter a trade due to an intraday setup, it will have an intraday
   stop. If I enter due to a daily setup, the trade will have a daily stop."
3. **⭐ Backtest the stop; don't guess.** "Pros do not guess. They do not rely on comfort. They
   study **thousands of samples** of their setups and identify the stop placement that maximizes
   expected value." He then describes exactly the procedure this repo runs — collect comparable
   charts, propose competing stop/exit hypotheses (prior bar lows vs close of 20-day MA vs a
   symmetric price target), test them, forward-test the survivors, and **don't cherry-pick:
   include every setup meeting the criteria.**
4. **Volatility → size, not stop.** Volatile markets need wider stops, so **size down** to hold
   risk constant. The failure mode he names: "Most traders will use the **same size** in volatile
   markets, then to keep risk equal they give a **tighter stop** than what their system dictates,
   which **ruins their trading system**."
5. **Discipline.** Hard stops, automation, daily loss limits, size down to defuse emotion.

He also dismisses the stop-hunting conspiracy with a decent argument: if stop runs were reliably
predictable you could simply trade the same side of them; if they aren't, your levels were
arbitrary and you are "fooled by randomness."

## 2. ⭐ The claim that answers the repo's open question

> "If our breakout system stop is to give to the lows of the daily bar, and **that low of the bar
> was really tight up against resistance level, we end up with a far tighter stop than if the bar
> had been much looser. That often is what gives a setup far better expected value versus
> otherwise.**" (06:12)

This is *not* "use a tight stop." It is **"select setups whose natural invalidation is close —
those are the better setups."** Tightness is a property of the setup, not a parameter you choose.
That is precisely the mechanism `HOW_THEY_DO_IT.md` hypothesized and could not specify.

## 3. ⚠ Tested — and NOT confirmed on daily bars

Run 2026-07-26 on `lift_trades.parquet` (299-name panel, stop = breakout bar low, exit
close<50EMA), splitting trades into quintiles by **natural stop width**:

| tier | Q1 tightest → Q5 loosest (account bp/trade) | Q1 − Q5 | t |
|---|---|---:|---:|
| DUMB | 6.9 / 6.4 / 5.4 / 7.8 / 7.8 | −0.9 | −0.26 |
| GATES | 9.9 / 12.5 / 10.9 / 9.7 / 7.1 | +2.8 | +0.30 |
| BREAKOUT | 14.4 / 2.3 / 7.5 / 1.2 / 10.4 | +4.1 | +0.40 |

Directionally positive for the screened tiers, **nowhere near significant**, and non-monotonic.

**But the result is probably not a refutation.** The tightest quintile stops out **88–90%** of the
time with a **1–2 day median hold** — the overnight-gap signature. In this implementation entry is
at the *next* day's open with the stop at the *prior* bar's low, so gap noise fires the stop before
the setup can work. Breitstein and Qullamaggie both enter **intraday on the breakout day itself**,
so the stop only goes live once that day's low is established. **The claim is untestable in this
implementation, not refuted** — and that gap is itself the finding.

## 4. Exponential bet sizing — and the conflict with Luk

Opening claim: **"For the best traders in the world, 80% of profits come from 5% of trades."**

Grading system, with risk scaled to grade:

| grade | frequency | risk |
|---|---|---|
| **A** | 1–2 per **month** — "memorable, standout" | ~$100k |
| **B** | dozens per month — best trade of the day | ~$10k |
| **C** | average, small edge, "more of a flyer" | small |
| **D** | 50/50, taken from boredom | shouldn't be taken |

**A gets 10× the risk of B.** Justified with a poker analogy — betting the same on 9-2 (38.9%
equity) and pocket aces (85.3%) is how you fail to profit; aces come once per 221 hands, so you
must recognise *and* capitalise.

> ⚠ **This directly contradicts [[martin_luk]]**, who says risk varies "only *slightly* with setup
> quality (0.2% B-setup vs 0.25% baseline) — **never half- or double-size on conviction alone.**"
> Luk: near-constant tiny risk, many attempts. Breitstein: 10× on rare A setups.

Both are demonstrably successful. Plausible reconciliations: Breitstein is intraday with immediate
feedback and no overnight gap risk on the sized-up bet, and far more reps per day to grade
against; Luk carries overnight gap risk where a 10×-sized position can gap through the stop. Note
Breitstein gates the whole idea hard — "**not for beginners**," requires being able to tell A from
B *in real time*, and requires that size not alter your entries/exits.

**Implication for every simulation in this repo: they all size equally across trades.** If 80% of
profit comes from 5% of trades and those are sized 10× larger, flat-sized backtests capture none
of that. It is another multiplier the harness structurally cannot see.

## 5. Testable extraction

⭐ **Tier-weighted sizing.** The scorecard tiers are a ready-made conviction proxy — size
BOTH/LEADER as "A", GATES as "B", DUMB as "C", and compare against flat sizing. ⚠ Prior is
**unfavourable**: on the broad panel the higher tiers were *worse* per trade (GATES +0.93% vs BOTH
+0.01%), so exponential sizing on them would amplify a negative. That is itself worth knowing — it
would show the scorecard's tiers are not a valid conviction ranking, which is a stronger statement
than "the tiers are weak."

## 6. Red flags

- No losing example in either video.
- Course plug in both; "$100M verified profits" opener in both.
- The sizing video answers "what percent should I risk?" with "I can't answer that" — honest, but
  it means the actionable core is a grading scheme with no calibration.
- ⚠ **Grade assessment is entirely discretionary and real-time.** The whole system rests on
  correctly identifying an A trade *as it happens*. That is unfalsifiable from outside and is
  exactly where survivorship among traders would hide.
