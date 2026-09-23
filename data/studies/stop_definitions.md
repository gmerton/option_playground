# Stops — the canonical definitions (2026-09-23)

**This file is the single source of truth for stop terminology.** It exists because the terms got muddled
in conversation on 2026-09-23: "disaster stop", "hard stop", "close stop" and "emergency stop" were used
as if they were four names for one thing. They are not. Two are real and live, one is a retrospective
grading criterion, and one does not exist in this repo at all.

⚠ If another doc disagrees with this one, this one is right and the other should be fixed.

---

## There are TWO live stops, and they execute DIFFERENTLY

| | **Disaster stop** | **Tight stop** |
|---|---|---|
| width | **1.0 ADR** below the current close | the **ENTRY BAR's low**, fixed at entry — typically 0.4–0.8 ADR |
| execution | ⭐ **RESTING, EXECUTED INTRADAY** | ⭐ **JUDGED ON THE CLOSE** |
| what it is for | the crash | ordinary trade management |
| how often it fires | **4–6% of days** | often |
| recomputed | daily, off the current close; never stored | per trade, from the entry bar |

**The single most important line:** the wide stop is the intraday one; the tight stop is the close-judged
one. Getting this backwards is the specific error made on 2026-09-23 — the close-judged rule was quoted
against the 1-ADR level, which is exactly the stop that IS supposed to rest with the broker.

Source: `entry_study_2026-09-17.md`. Its wording: the wide stop "almost never fires (4–6% of days at
1 ADR) — **its job is the crash, not the noise**", and it "is the best **intraday-executed** variant on
both universes"; whereas *"cut losses early" survives at the daily level (stop at the session low, judged
on the close) — what does not survive is executing that stop on 1-minute bars.*

### Why executing the TIGHT stop intraday hurts — the worked case

**DINO, 2026-09-22** (broker records, Flex query 1415008, order 5649590827): bought 20 @ 109.745 at 11:55,
resting stop ≈ 106.22 = **0.75 ADR — the width was correct**, only $0.39 tighter than the day-low stop of
105.83. It filled at **106.17 at 15:51, the exact post-entry low**, nine minutes before a close of
**106.69** that would have kept the position alive. Cost ≈ **$11.56 plus the position**.

The width was never the problem. Resting it was.

---

## ⛔ THE TIGHT STOP IS NOT A TRAILING LEVEL — READ THIS BEFORE QUOTING ONE

The tight stop is the **entry bar's low, fixed when the trade is opened.** It is NOT today's session low,
and for a position held more than a day or two it is usually stale and far away. Its real job is
**retrospective**: it is how the reviewer grades whether an entry was well-constructed.

⚠ **Harm actually caused, 2026-09-23.** A "tight stop" table was produced for 17 open positions using
**today's rolling session low**. That number is self-referential — the level IS the low, so it can only be
touched by the stock making a new low, at which point the level moves. It printed at 0.01–0.02 ADR on
several names and **drove three unnecessary exits, two of them winners** (NBIS +1.13 ADR above basis,
SNDK +0.87 ADR). Twelve of the seventeen rows were flagged "TOO TIGHT" in the same table and that did not
prevent the harm, because a column of levels invites action whatever the footnote says.

**The rule, with no ambiguity: for an OPEN position there is exactly ONE stop to quote — the 1-ADR
disaster stop, resting with the broker.** Do not produce a per-position "tight stop" column for open
positions at all. Quote the entry-bar low only when (a) grading a completed trade, or (b) sizing a NEW
entry on its entry day.

---

## WIDTH — quote `stop/ADR`, and under ~0.5 ADR widen and cut size

**ZETA, 2026-09-22**: entered on the close at 30.13 with a day-low stop of 29.53 = 2.0% on a 4.4% ADR name
= **0.45 ADR**. Too tight; it is inside the name's ordinary daily movement.

Give both numbers when recommending an entry:
`1-ADR stop ≈ entry × (1 − ADR%)` and `shares × (day-low stop% ÷ ADR%)` to hold dollar risk constant.

⚠ **A weak close is a SIZING problem, never a SELECTION problem.** Close-in-range does not forecast the
move (`close_strength_2026-09-22.md`: Spearman −0.80/−0.90, the strongest closes are the *worst* 60d cell)
— but it *is* the stop distance: `stop/ADR` runs **0.12** at cir ≤ 0.2 up to **1.03** at cir ≥ 0.8. Under
a day-low stop the weak-close cell looks 0.43R worse; **under a fixed 1-ADR stop the gap reverses.**

⚠ **Do not overclaim the 1-ADR stop.** That cell is ≈ **+0.03R and does not beat its control.** Widening
removes a self-inflicted penalty; it does not manufacture edge. And no stop variant beats simply **buying
the close** (+5.94%).

---

## Terms that are NOT live stops

**"Hard stop"** — `src/lib/trade_reviewer/principles.py:63`. The O'Neill/Luk/Qullamaggie **entry-time**
rule: the tighter of (a) the breakout-candle low, (b) 7–8% below entry, (c) no wider than 50% of ADR. It
exists so the **trade reviewer can grade a past trade** — *was the stop placed correctly at entry?* It is
a scoring criterion, not a level the desk maintains on an open position.

⚠ Note the apparent contradiction and its resolution: Luk says the stop must be **no wider** than 0.5 ADR,
while the house finding says anything **under** ~0.5 ADR is inside the noise. Together they mean
**~0.5 ADR is the target**, and when the candle low implies something wider you **cut size**, never tighten
the stop.

**"Emergency stop"** — ⛔ **not a term in this repo.** The only `emergency` in the codebase is a VIX-based
portfolio exit in `run_portfolio_backtest.py`, unrelated to equity stops. If it is used in conversation,
ask which of the two live stops is meant.

**"End-of-day stop"** — not a third stop. It describes the *execution* half of the tight stop. The
disaster stop is **not** end-of-day; it rests intraday.

**Per-alert entry stops** (`daily_routine.md`) — each intraday alert defines its own initial stop:
UR → session low · ORB9 → opening-range/bar low · LVL → level − 0.5 ADR · BIR/FBO → above the failed high.
A 0.60 ADR floor is adopted **for ORB9 only**; UR and FBO still emit sub-0.5-ADR stops (0.35 and 0.48 on
2026-09-22, both losses) and the floor study is queued for those types.

---

## How to answer "what is my stop?"

**For an OPEN position — give ONE number, the disaster stop, and nothing else:**

> **TXG disaster stop 70.74** — rest this with the broker. It fires ~5% of days; its job is the crash.

Do **not** add a tight-stop column. See the ⛔ section above: doing exactly that on 2026-09-23 caused
three unnecessary exits.

**For a NEW entry being sized, on its entry day** — then the entry-bar low is live and both numbers apply:

> Entry 30.13, entry-bar low **29.53 = 0.45 ADR — too tight.** Widen to the 1-ADR stop at **28.80** and
> cut size to `shares × (0.45 ÷ 1.0)` to hold dollar risk constant.

**For a COMPLETED trade being graded** — the entry-bar low is the benchmark: was it ≤ 0.5 ADR, was it
rested intraday when it should have been judged on the close, did it fill at the post-entry low?
