# Jade Lizard / Big Lizard — Ross Young

Source: `2025-06-29_h5JyUtuTN8I` — "Jade Lizard Options Strategy Explained: No Upside Risk!"
([watch](https://www.youtube.com/watch?v=h5JyUtuTN8I)). Guest: Ross Young, a self-described
diversified, "more cautious… getting a little older" retail options trader (a repeat guest — the
channel did a prior interview with him); host: John. **No sales motive** — Young sells nothing,
disclaims being a "professional options instructor," and repeatedly credits the originators
(Liz & Jenny / tastytrade) as "the masters… probably a lot smarter than me" `@01:23`, `@25:50`.
That candor is a genuine mark in his favor for this channel.

## Verdict

> **Conviction: 2/5 · Risk: 6/10 (naked short-put downside on volatile high-IV ETFs) · Tested: NO**
> A legitimate, well-known tastytrade structure — a short put financed by a short call spread sized
> so the **net credit ≥ the call-spread width**, which really does remove upside risk *at expiration*.
> The single best thing: the "no upside risk" claim is, unusually for this channel, **mechanically
> true, not rhetorical** — it's arithmetic, not a promise. The single worst thing: the title
> advertises the *safe* side and buries the *exposed* one — **all the risk is a naked short put on
> gap-prone gold-miner ETFs**, and the headline "close to 90% win" is self-reported, untracked, and
> **inflated by his own admission that he refuses to close losers and rolls them out indefinitely**
> (one GDXJ position he "wrestled" for 2+ years). Honest presenter, real structure, no sales motive
> → above the 1.5s; but no separable evidence and a can-kicking win rate → capped at 2.

## Mechanics

- **Underlying:** liquid, **cheaper, high-IV ETFs** so a $1-wide call spread fits and buying-power
  use stays low — his examples are **GDX / GDXJ (gold miners)**. Needs good liquidity (three legs)
  and available narrow ($1) strikes; $5/$10-wide-strike names are "tougher." `@02:06`, `@06:58`,
  `@13:13`
- **Structure (Jade Lizard):** short put **+ short call (vertical) spread** on top. Not delta-based —
  **credit-based**: start with the put targeting **~$0.70 credit**, then add a narrow (**$1-wide**)
  call spread. **Rule: total credit ≥ call-spread width → zero upside risk at expiry.** `@01:32`,
  `@02:19`, `@03:12`
- **Worked example (GDX, spot ~$53):** short put **strike 49 for $0.79**; $1-wide call spread
  (short ~$1.25 / long ~$1.03) ≈ **$0.25**. Total ≈ **$1.04 ≥ $1.00 width** → if it "goes to the
  moon" he keeps a small residual credit (~$0.50 in his illustration). `@02:31`, `@03:12`
- **DTE:** targets **45**, occasionally out to 60, "so theta comes in more quickly." `@07:42`
- **Profit target:** **50%** (Jade); take it earlier on a fast move. `@19:19`
- **Stop:** **3× the total credit** ("the standard thing I have in my head… when I've been mechanical
  with that I've probably been the most successful") — but admits he often overrides it emotionally.
  `@22:07`
- **Adjustments (the claimed engine):** roll the **call spread down** for small credits (never widen
  it — that would add upside risk); final roll matches call to the put strike. **Roll the whole trade
  out in time** for a credit while IV stays high, one leg at a time (can't roll 3→3). On a downside
  break: roll the put out, or **take assignment/shares** if it's a name he wants (now dividend
  payers). `@08:04`–`@11:20`
- **Big Lizard (variant):** start from a **short straddle (ATM put + ATM call)**, then buy a long call
  capping upside so credit ≥ width. Much **bigger credit, much closer (worse) break-even**; less to
  manage (no room to roll the call down). Sized as "one contract of downside risk instead of five"
  Jade lizards. PT **25–30%**. `@13:46`, `@14:35`, `@19:32`
- **Reverse lizard:** flips risk to the upside — he only likes it when he already **owns shares** so
  the short call is covered. `@24:52`
- **Self-rated risk:** if a naked short put = 5, **Jade ≈ 3, Big ≈ 4** ("less risky than short puts").
  `@23:17`

## Claimed edge & returns

- **"Close to 90% winners"** `@21:24` — immediately hedged to **"the 80s, I guess, if I had to nail
  it down, but I don't know"** `@21:35`, and preceded by **"I don't have a percentage on the winners
  and losers"** `@19:57`. So: **no tracked win rate, no ROC, no $ figures, no sample size, no years.**
- He explicitly attributes the high win rate to **rolling losers out rather than realizing them**:
  "the other thing that adds on the winning percentage is that I roll them out of time… I'll keep
  fighting the battle." `@20:10`
- One anecdote of a **GDXJ** position rolled for **2+ years** that "turned out pretty good in the end
  … but was sweating in between." `@11:10`, `@21:24` — a single winners-biased war story, not data.

## Objective assessment (where to be skeptical)

1. **The title inverts the risk.** "No Upside Risk!" is true *at expiration* by construction (net
   credit ≥ call width), and Young himself is clear the real risk is the downside — but the framing
   advertises the harmless side. The position **is a naked short put**: full exposure from the put
   strike down to zero, minus the credit. On **gold-miner ETFs (GDX/GDXJ)** — high-beta, gap-prone,
   commodity-driven — that downside is exactly where the pain lives. Risk 6/10, not the 3 he
   self-rates, once you weight the fat-tailed underlying rather than the structure in the abstract.
2. **The win rate is loss-deferral, not edge.** He says it plainly (`@20:10`): the ~90% comes partly
   from **never closing losers** — rolling out indefinitely converts a marked loss into a
   longer-dated open position that isn't counted as a loss *yet*. That is the classic
   short-premium can-kicking that reads as a high win rate right up until a name keeps falling and the
   accumulated, repeatedly-rolled position is realized (or assigned) at a large loss. A 2-year GDXJ
   roll is not "a win" — it's a loss he refused to book, tying up buying power the whole time.
3. **The win rate is also unverifiable.** "I don't have a percentage… I don't know… close to 90%…
   the 80s I guess." No log, no statements, no sample. It is a feeling, self-reported, on his own
   (loss-deferring) accounting.
4. **The edge is tiny; costs are not.** Total credit on the GDX example is ~$1.04 with the
   *residual* upside profit ~$0.50, on a **three-leg** structure (four when rolling). Bid/ask on GDX
   options + commissions on three legs, repeated across every roll, eat a large fraction of a
   sub-$1 credit. The reward for the naked-put risk is small in absolute terms — the payoff geometry
   is "collect a little, often; risk a lot, rarely," which lives or dies on avoiding the rare tail.
5. **Stop discipline is aspirational.** The 3× stop only holds "when I'm smart enough" `@22:07`; he
   admits letting emotions run ("it's come down, it's going to come back up") and even **adding a
   second Jade lizard below a loser** — "throw good money after bad" `@22:31`. So the risk control
   that would bound the downside is the first thing to fail in the scenario that matters.
6. **Benign-regime, self-selected anecdotes.** The only concrete stories (GDXJ, an XOM position
   "already profitable") are winners or works-in-progress. No losing trade is carried to a realized
   loss. Gold/miners had tailwinds over much of the period he's describing.

## What's genuinely sound (the diamond)

- **"No upside risk" is arithmetic, not marketing.** Net credit ≥ call-spread width genuinely caps
  the upside outcome at a small profit — a rare case on this channel where a "no risk" phrase is
  literally true (on one side, at expiry). Credit for a correctly-stated mechanic.
- **A real, documented, originator-credited structure.** The Jade/Big Lizard is a standard tastytrade
  construction; Young points viewers to Liz & Jenny rather than to a course of his own. **No sales
  motive** — no Discord, no software, no newsletter. That honesty is why this clears the 1.5 tier.
- **Sober self-assessment.** He rates his own trades 3–4/10, names the downside as the true risk,
  concedes he has no tracked stats, and warns that rolling "can add to a loss if you do it the wrong
  way" `@21:45`. Low oversell for the format.
- **Sensible plumbing:** defined upside, credit-based sizing to keep BP low, 45 DTE for theta,
  liquidity-first underlying selection, a nominal profit target and stop.

## Backtestability

- **Testable skeleton (the honest floor):** GDX/GDXJ (or any covered ETF), 45 DTE, credit-based
  strikes (put ≈ $0.70, $1-wide call spread sized so total credit ≥ width), **exit at 50% PT or 3×
  stop, no rolling.** That mechanical, no-roll version is exactly what strips out the discretionary
  loss-deferral — so it will surface the **true realized loss rate the rolling hides**, and is the
  single most informative test to run. Expect it to show a *lower* win rate and larger tail losses
  than his ~90% claim, by construction.
- **Not faithfully testable:** the roll-down / roll-out / take-shares management that he says *is* the
  edge — path-dependent, discretionary, and IV-conditional. Also the "add another lizard below" and
  emotional stop overrides. These are the alpha claim and they can't be specified as rules.
- **Data caveats on `silver.options_daily_v3` (EOD-only):** GDX/GDXJ are equity ETFs (in scope, not
  futures) — need to **confirm coverage + greeks + strike granularity** for these names, which are
  thinner than SPX. **45-DTE, three-leg, sub-$1-credit structures are precisely where modeled fills
  bite:** mark-at-mid entry vs intrinsic settle will over- or under-state a $0.25 call-spread credit
  badly, and the rolling multiplies leg count. Any result must be reported net of a conservative
  per-leg slippage assumption or it's meaningless.

## Open questions / next step

- What is the **realized** (no-roll) win rate and EV on GDX/GDXJ Jade lizards 45 DTE, and how far
  below "close to 90%" does it fall once losers are actually booked?
- How large is the **left tail** — worst realized outcome on a gold-miner gap-down / commodity shock
  when the naked put is breached? That, not the win rate, sizes the strategy.
- Does the **roll-out management** actually recover losers on EOD data, or just extend duration and
  buying-power drag (the GDXJ-2-year pattern)? Can't be tested faithfully, but a bounded proxy
  (roll once at test) could bracket it.
- **Next step (on command only):** backtest the no-roll skeleton under `backtests/jade_lizard/` on
  GDX/GDXJ (confirm Athena coverage first) — the point of the test is to measure how much of the
  90% win rate is real vs deferred.
