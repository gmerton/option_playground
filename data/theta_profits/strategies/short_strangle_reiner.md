# Short Strangle (Reiner) — Reiner Hoffmann

Source: `2026-06-21_mvwWve5xSz4` — "How Reiner Achieved a 100% Win Rate Selling Short
Strangles" ([watch](https://www.youtube.com/watch?v=mvwWve5xSz4)). Guest: Reiner Hoffmann,
62, Germany, mechanical engineer / ex-tech executive, full-time options trader for ~1 year,
coached ~3 years by a former CBOE market maker; host: John.

## Verdict

> **Conviction: 2 / 5 · Risk: 8 / 10 (UNDEFINED / naked tail risk) · Tested: NO**
> A genuinely disciplined, well-instrumented version of a fundamentally dangerous trade. Reiner
> is the rare guest who states the risk plainly ("two times unlimited risk," `@00:13`), gates
> entry on real volatility structure (IV percentile, contango term structure, RVX ceiling),
> takes profit mechanically at 50% to dodge gamma, sizes small, and hedges the tail with micro
> futures and long options. That earns conviction above the Burrito Butterfly. **But the
> headline "100% win rate" is statistically vacuous on a short strangle** — over ~75 trades in a
> benign ~3-year window, a 100% win rate on an undefined-risk premium-seller is the *expected*
> result, not evidence of edge. The entire risk lives in the rare loss that hasn't happened yet
> ("picking up pennies in front of a steamroller"), and his own near-miss (Liberation Day +10%
> RUT gap, survived by "luck" and the small range left in a delta-8 call, `@33:53`–`@34:48`)
> shows the steamroller is real. He also reframes roll losses as "not a loss… temporary"
> (`@36:06`) — exactly the mechanism that lets a short-strangle win rate stay at 100% while EV
> erodes. **Returns are modest (25%/yr on allocated capital, target 10%, `@36:39`) for a
> strategy that can lose multiples of a year's gains in one gap.** Not yet a diamond; the tail
> is untested.

## Mechanics

- **Underlying:** RUT (Russell 2000 cash-settled index) is his primary — "Russell… my underlying
  for a premium/income trade." Chosen *because it tends to range, not trend up* (a short strangle
  dies on a bullish blowout). Also runs it on liquid equity options and on IWM (the ETF), but
  notes IWM carries **assignment risk** and "hasn't the same success rate as the Russell."
  `@08:27`, `@29:44`–`@30:13`
- **Structure:** classic two-leg short strangle — sell 1 OTM put + sell 1 OTM call, no long
  protection. **One contract per side** (RUT is large). `@03:48`, `@17:48`
- **Strike selection:** **put at ~10 delta, call at ~8 delta** (slightly tighter call because RUT
  upside is the feared side). Can also set delta-neutral, strike-symmetric, or premium-symmetric;
  he uses the fixed 10Δ/8Δ for the income trade. `@04:52`, `@15:46`–`@15:57`
- **DTE:** **30 days** is the backtested sweet spot; average **~14 days in trade** (exits on the
  50% target about halfway). Variations 45 / 75 DTE "work very well" but yield fewer trades.
  `@08:51`, `@11:42`, `@12:03`
- **Entry gates (mechanical — the testable core):** `@09:20`–`@11:31`, `@15:04`–`@15:46`
  - **RVX (Russell vol index) < 40** — no entry when fear is "sky high."
  - **IV elevated vs. its own history:** IV Z-score ≥ ~0.5 SD above the 1-yr mean, *or* IV
    percentile ≥ ~50–70% (he gives both ~50% and ~70% in different passes). Floor condition: **IV
    > RV** (implied above realized).
  - **Term structure in CONTANGO** (front vol < later vol) — so vol "rolls down" as time passes,
    a carry tailwind. He stresses **backwardation is the trap** retail misread as "selling the
    peak." `@11:31`, `@12:51`–`@14:14`
  - **Price not "super bullish":** EMA(50)-aware, **RSI ~40–60** (range-bound, not trending).
  - **Liquid underlying** (tight bid/ask, so adjustments are fillable when vol spikes). `@16:09`
- **Variant — "vol-crush" trade (explicitly NOT for beginners):** enter at very high IV (1.5–2 SD
  over mean, IV percentile 90–100%), term structure may be in backwardation, and take profit
  *small* (10–20%, not 50%) to capture the IV crush rather than theta. `@16:46`–`@17:46`
- **Primary exit:** **take profit at 50% of credit** — chosen to sit in the fat part of the theta
  decay curve and **avoid holding into peak gamma near expiry**. Does NOT hold to worthless.
  `@09:06`, `@18:42`, `@19:19`
- **Secondary exit / adjustment trigger:** when **either short leg reaches ~35 delta**, act:
  inspect regime (trend change / stress?), then either (a) close the pressured leg and roll the
  other toward ATM for compensating credit, (b) a credit-only vertical/delta adjustment ("never
  for a debit"), or (c) roll the pressured side out one expiration. `@19:41`–`@22:24`
- **Hard stop:** **lose 20% of required margin → exit the pressured side.** On a ~$10K-margin RUT
  strangle that's a **−$2,000** line. `@22:25`, `@38:09`
- **Tail hedges (he insists naked is not acceptable):** `@26:11`–`@29:31`
  - **Micro Russell future (M2K, $5/pt):** pre-place a stop (sell-stop on downside / buy-stop on
    upside) at the strike where loss hits the 20%-margin line, to neutralize a leg through a gap.
    Linear payoff, so you must then close the pressured option side.
  - **Long strangle/straddle overlay** at ~half the DTE, cheaper than the credit collected →
    effectively converts the position into a **defined-risk iron condor** ("if you feel unsafe…
    turn it into an iron condor"). `@31:46`, `@32:08`
- **Sizing:** allocate **~10% of account as the max margin** for the strategy; the 20%-of-margin
  stop = ~2% of account at risk per trade nominal (pre-gap). `@37:30`–`@38:22`
- **Frequency / management load:** ~**25 trades/year** on RUT; only ~**5%** need active
  management on RUT (more on equities, ~⅓). `@12:03`, `@23:17`–`@23:28`
- **Self-rated risk:** **8–9/10 for a beginner; 6–7/10 for an experienced manager.** `@35:25`

## Claimed edge & returns

- **"100% win rate… since 3 years," ~25 trades/yr** on the RUT strangle = **~75 trades, zero
  losers.** `@00:00`, `@11:57`, `@23:55`–`@24:24`
- Other strategies: **90–95%** win rate. `@24:31`
- **~25% profit over 3 years on allocated capital** (the carved-out sleeve), drawdowns "0 to
  ~50%," **target only ~10%/yr** — explicitly conservative. `@36:39`–`@37:18`
- Collects **~$1,800–$2,000 premium** per RUT strangle, keeps 50%; **~$10K margin** typical.
  `@17:48`, `@18:30`
- Edge attribution, his words: **"the risk management… is where I gain most of the edge"**
  (`@00:00`, `@19:08`) and "two times theta + two times short Vega + management." `@39:34`

## Objective assessment (where to be skeptical)

1. **"100% win rate" is the reddest flag on this channel — and nearly content-free here.** Short
   strangles win the overwhelming majority of the time *by construction*; you collect small
   premium often and pay back large rarely. A 100% win rate over ~75 trades in a ~2023–2026 window
   (no sustained bear, no Volmageddon, no COVID-scale gap) is the **default outcome of an
   undefined-risk seller who hasn't yet met its tail.** It tells you almost nothing about
   expectancy — EV is dominated by the magnitude of the loss that hasn't occurred, not the
   frequency of wins.
2. **"Roll loss is not a loss… it's temporary" is the win-rate-laundering mechanism.** `@36:06`
   He carries a pressured leg by rolling it (out in time / toward ATM) and books the realized debit
   not as a loss but as a reduction of premium "on the other side." This is exactly how a short
   strangle book maintains a 100% closed-trade win rate while accumulating *un-booked* losses and
   *increased exposure*. Until we see a trade-by-trade ledger with rolls marked-to-realized, the
   win rate is not falsifiable.
3. **The tail is undefined, and he says so.** "Theoretically two times unlimited risk" (`@00:13`),
   "can blow out an account if the market makes a 50% jump" (`@32:20`–`@32:33`), margin also
   *expands* into the move. A 10% overnight gap "overruns" the delta-35 trigger entirely
   (`@31:21`) — the mechanical stop **does not protect against the one event that matters**; only
   the futures hedge or a pre-existing long overlay does, and both must already be on.
4. **His own near-miss undercuts the 100%.** Liberation Day: RUT +~10% in a day; he says he was
   **"luckily"** only in RUT and not equities, had to roll the call side, and "delta-8 has a little
   range… it worked. But if it would be 1000 points… you might have difficulties… you might not be
   able to roll… I would have just closed the call side" at a loss. `@33:53`–`@34:59`. That is a
   survived-by-luck-and-margin account of the exact scenario that ends short strangles — and it
   happened *inside* the 3-year "100%" window.
5. **Reward is small relative to the risk geometry.** ~10% target, ~25% realized/yr on the sleeve.
   A single un-hedged tail event can erase several years of this. Pennies vs. steamroller is not
   rhetorical here — it's the literal payoff shape.
6. **Self-reported, single-instrument, no separable audited record.** Tracking is a personal Excel
   sheet (`@36:06`); the equity-options variants are vaguer (90–95%, "be careful"). The clean 100%
   is one underlying (RUT) over one benign regime.
7. **Some entry gates are softly specified / restated inconsistently** (IV percentile quoted as
   ≥50% in one pass, ≥70% in another; Z-score ≥0.5; "RSI 40–60"; "EMA ≥50"). Backtestable, but the
   exact thresholds need pinning.
8. **Caveat in his favor:** he is currently *not* recommending short strangles ("in times like
   this I would avoid to sell short strangles," `@23:38`) — i.e. he treats the entry gate as a real
   off-switch, not an always-on machine.

## What's genuinely sound

- **He never claims it's risk-free.** Opposite of the Burrito pitch — he leads and closes on
  "two times unlimited risk" and rates it 8–9/10 for beginners. Honest framing.
- **The entry filters are real and mechanical:** IV > RV, IV percentile/Z-score elevated, term
  structure in contango, RVX ceiling, RSI/EMA "not bullish." Selling premium *only when paid for
  it* and *only with a vol-roll-down tailwind* is a legitimate, defensible edge thesis — and it's
  fully testable.
- **50% profit target to dodge end-of-life gamma** is textbook-correct risk management (the same
  reason tastytrade-style sellers don't hold to expiry).
- **Layered, pre-planned tail defense:** delta-35 watch trigger → 20%-of-margin hard stop → M2K
  micro-future stop at the loss strike → optional long-overlay that converts to a defined-risk
  iron condor. This is materially more robust than naked-and-hoping, and the future-hedge logic
  (24/7 liquidity to cover a gap the options can't be filled into) is sound.
- **Conservative sizing and instrument selection:** ~10% margin allocation, RUT chosen *because*
  it ranges rather than trends, explicit avoidance of bullish mega-cap tech (the classic short-call
  killer). `@33:06`–`@33:30`
- **Cash-settled index = no assignment / pin risk** (vs. the IWM variant he flags as inferior).
- **Contrast with the user's existing books:** the user already runs **defined-risk** index
  premium (SPX iron condor, VIX≥20 gate; UUP short straddle with 50% PT / 2× stop). Reiner's gates
  (IV percentile, contango, RVX) and his "turn it into an iron condor when scared" are the *same
  family* — the key difference is that the user's structures cap the tail by buying wings, whereas
  Reiner's base trade leaves the tail open and relies on discretionary/futures defense to close it.
  His own escape hatch (`@31:46`, "turn it into an iron condor… risk is pretty much defined")
  essentially concedes the defined-risk version is the safer trade.

## Backtestability

- **Highly testable core (more so than most KB strategies):** every entry gate is a computable
  daily signal and every exit is a rule. Construct: RUT 30-DTE, sell 10Δ put + 8Δ call, enter only
  when (IV percentile ≥ ~70 **and** IV>RV **and** term structure in contango **and** RVX<40 **and**
  RSI 40–60 / above EMA50); exit at 50% credit, else manage at 35Δ touch, hard stop at −20% of
  margin. Measure win rate, **mean P&L including the losers**, max single-trade loss, and EV after
  commissions + (wide, gap-sensitive) slippage.
- **The test MUST capture the tail or it will look falsely perfect.** A short-strangle backtest
  that omits the gap days is worthless. Include **2018 Volmageddon (Feb), 2020 COVID (Feb–Mar),
  2022 bear, Aug-2024 yen-carry unwind, and Apr-2025 "Liberation Day"** explicitly, and **model
  margin expansion and the overnight-gap fill problem** — the delta-35 trigger cannot be hit
  intraday in EOD data, so the test should assume the stop fails on gap days (worst-case) and only
  the futures hedge / long overlay caps the loss.
- **Data:** Athena `silver.options_daily_v3` has **SPX + XSP confirmed** (46M rows, 2010 →
  2026-02-20, full greeks + bid/ask). **RUT and IWM coverage must be confirmed** before this can be
  run on his actual underlying; XSP/SPX could serve as a liquid proxy but changes the
  vol/term-structure character. **EOD/daily resolution only** — so the 50%-PT exit and the 35Δ
  watch can only be checked once per day at the close, and **intraday management, the M2K stop, and
  same-day adjustments cannot be faithfully replayed.** Term structure (front vs. back IV) and an
  RVX/VIX-style series would need to be assembled.
- **Not faithfully testable:** the discretionary roll-vs-close-vs-hedge decision tree at the 35Δ
  trigger, the "regime read," and the vol-crush variant — all judgment-dependent.
- **Honest null comparison:** vs. (a) an *un-gated* RUT 10Δ/8Δ strangle (does the IV/contango gate
  actually add EV, or just reduce trade count?), and (b) the **defined-risk iron condor** at the
  same short strikes with bought wings — to quantify what the open tail buys you in EV per unit of
  tail risk.

## Open questions / next step

- **Where are the losers?** Request/reconstruct the trade ledger with **rolls marked to realized
  P&L** — the 100% claim cannot be assessed until roll losses are counted as losses.
- Does the gated entry produce **positive EV after the tail is included** (2018/2020/2022/2024/2025),
  or does one modeled gap erase the cumulative theta?
- **How much EV does the contango/IV-percentile gate add** over an always-on strangle, and over the
  defined-risk iron-condor version?
- Confirm **RUT/IWM** option coverage (greeks + bid/ask + short-DTE expirations) in
  `silver.options_daily_v3`; otherwise proxy with SPX/XSP and note the regime mismatch.
- **Next step (on command only):** backtest the gated mechanical core under
  `backtests/short_strangle_reiner/`, with the tail windows mandatory and margin/gap modeled —
  expect the open-tail version to show a high win rate and a fat-tailed loss distribution; the
  decision is whether the gate's EV survives the steamroller.
