# Double Calendar (Range Tent, no transform) — Ravish

Source: `2025-06-15_olVPaP7OSOM` — "How This Trader Makes 100%+ Returns with Double Calendar
Spreads (Full Strategy)" ([watch](https://www.youtube.com/watch?v=olVPaP7OSOM)). Guest: **Ravish**
(first name only on the audio; promotes a new channel **"Options with Ravish"** `@29:00`),
ex‑product‑manager at a fintech, ~7 yrs trading options, went full‑time in 2021. Host: John.

**Identity / relation note — same structure, opposite playbook to Steve Bernich.** This is the
**second double-calendar episode** in the KB. The *entry* is essentially identical to Bernich's
`strategies/dc_time_machine.md` — a **put calendar below + call calendar above** on SPX. The
**difference is everything that happens next**: Bernich's whole edge is **transforming** the winning
double calendar into an all-front-month "risk-free" iron condor; **Ravish does NOT transform at all.**
He simply holds the double calendar as a **long-vega / long-theta tent** and **scales out at 15–30% of
debit a few days before expiry**, before the center "sag" develops. So: same skeleton, no transformer,
no "risk-free" claim, much wider/further-OTM strikes (expected-move placement vs Bernich's tight
30–40Δ), and a **discretionary VIX-direction call** in place of Bernich's paywalled "Flux" IV tool.
Treat them as the same family, different management. The closest "pure calendar" cousin is Simon
Black's Time Flies (`strategies/time_flies.md`), but that uses a put *diagonal* + call *BWB*, not two
calendars.

## Verdict

> **Conviction: 1.5 / 5 · Risk: 5 / 10 (defined per trade, but campaign-layered vol risk) · Tested: PARTIAL (skeleton only)**
>
> **Backtest update (2026-06-25, `backtests/dc_time_machine/`):** the Ravish parameterization (tight +3
> gap, 0.25Δ, 15–30% PT) was **net-negative after costs** on SPY 2018–2026 (−5% CW ROC, −$15 sumPnL) and
> only ~breakeven (−0.4%) even in the favorable 2022+ window — worse than the user's existing SPY dcal
> (+2% to +4.5%). The thin 15–30% target on a ~$0.80 Fri/Mon debit is **eaten by the multi-leg fills he
> himself admits are hard**. The cleanly-testable skeleton confirms the suspicion in this write-up: with
> the discretionary VIX-timing removed, it's a generic long-vega tent that rode the 2022–2025 vol regime
> and loses to a plain wider-gap calendar after costs.
> A textbook double calendar with no novel mechanics and — unlike Bernich — **no separable track
> record at all**. The evidence is purely account-level ("$400k → $2M in 3 years trading only this"
> `@23:43`): no trade count, no per-trade log, no win/loss series, nothing falsifiable, and it
> **contradicts his own 80/20 framing** (he says elsewhere only 20% of capital is in this strategy).
> To his credit he is **honest about the dominant failure mode** — a **vol crush turns the middle of
> the tent into "a sea of red"** `@11:59` and a COVID-style gap "could wipe you out" `@25:34` — which
> keeps it above a "risk-free" oversell. But the headline depends on a skill he admits is "easier said
> than done" (forecasting VIX direction `@15:06`), the touted **"negative-vega trick" is hand-waved**
> ("it will do the trick" with no mechanism `@21:08`), and the demoed P&L is **winners-only OptionStrat
> theory**. It ranks **below Bernich (2)** despite the cleaner/more-standard structure, purely because
> the evidence is weaker (account anecdote vs 3 months of trade stats). The vanilla skeleton is the
> most cleanly testable of the calendar trio — that's its one real advantage.

## Mechanics

- **Underlying:** SPX preferred; also SPY, **QQQ** ("Triple Q"), or large caps (Apple, Microsoft).
  **Avoids small caps** (too volatile). Prefers cash-settled indexes. `@10:34`, `@10:50`
- **Structure — double calendar:** a **put calendar below** + a **call calendar above** the current
  price. Each calendar = **same strike, two expirations**: **sell the front (near) expiry, buy the
  back (further) expiry**, net **debit**. Example given: 5900 put calendar + 6100 call calendar with
  SPX ~6000 (strikes ~100 pts ≈ **~1.6%** either side). `@07:42`, `@08:10`, `@08:27`
- **A single calendar** here is the long-vol cousin of a butterfly: same tent shape, but it **profits
  when VIX rises** (a butterfly profits when VIX falls). `@03:38`, `@03:52` That long-vega property is
  the strategy's whole personality.
- **Strike placement (discretionary):** based on the **implied / expected move** — "not completely to
  the tea," with discretion for where he thinks the market is going. Further OTM = higher max profit %
  but lower probability the price reaches it. `@08:27`, `@11:16`
- **DTE:** time horizon **10–15 days**. **Short leg on a Friday expiry**; **long leg is either the
  next-week Friday or the Monday immediately after** the short Friday (a **2-day** calendar gap).
  He adds "a few extra days" to the horizon so the tent doesn't get too narrow. `@06:46`, `@17:54`,
  `@18:07`
- **Entry timing:** typically **Tuesday/Wednesday** for the following Friday (~10-day). **Enter when
  VIX is low, take profit when VIX is high** ("rule of thumb"); **won't enter if VIX > 20**, lower the
  better. **Avoids entering before known events** (e.g. FOMC); exits existing trades before such events.
  `@10:50`, `@13:00`, `@16:00`, `@18:21`
- **VIX/vega is the master variable, not price:** if VIX **rises**, the profit range expands hugely —
  can profit even past the strikes, and a spike can pay "**well over 100%**" vs a ~50% peak `@14:26`.
  If VIX **falls**, the middle of the range becomes a loss and POP collapses to **~30%** `@11:59`.
- **The "negative-vega trick" (high-VIX entry):** to enter when VIX is already high, pick the **short
  leg on a Wednesday** and the **long leg the next Friday**; he claims this "**does the trick**" and
  profits even if VIX falls — while admitting the platform "still says the trade is long vega."
  Mechanism **not explained**. `@20:47`, `@21:01`, `@21:08`
- **Profit target:** **start scaling out at 15–20%** of debit, **goal > 30%**; sells in pieces (he runs
  many contracts). **Hard deadline: completely out 2–3 days before expiry**, before the center sags.
  `@17:15`, `@18:48`, `@19:02`
- **Loss management:** **max loss = debit paid.** If underwater, can hold to the time-horizon **as long
  as price is near one of the strikes**; **exits if price reaches either strike** (regardless of P&L);
  in a vol-crush, max loss is "usually 20–30%" and he'll hold inside the range hoping for a VIX spike to
  revive it. **No hard stop articulated.** `@19:02`, `@19:16`, `@20:09`
- **Cadence:** a **"campaign"** — layer a couple of trades every week, open new as old close.
  Marketed as **"passive / set-and-forget,"** little chart-watching. `@22:05`, `@22:18`
- **Self-rated risk:** **3** on the option-strategy curve (notes every option trade is riskier than
  owning stock). `@23:11`

## Claimed edge & returns

All **account-level, self-reported, no trade-level data**:

- **"$400,000 → over $2 million in 3 years trading only this strategy."** `@23:43`, `@23:51`
- **">85% win rate"** on double calendars. `@02:18`
- **"20–30% monthly on the invested capital"**; **"well over 100% annually"** if traded alone in an
  account. `@24:33`, `@24:47`
- **"No single losing year"** trading double calendar. `@25:04`
- **80/20 capital framing:** 80% in low-risk "passive" strategies (LEAP covered calls, collars, a
  "hybrid collar" he claims can be **"zero risk … won't lose a single dollar even if the stock drops
  50%"** `@27:47`), 20% in double calendars → overall portfolio "well over 50%." `@23:58`, `@27:02`
- **Per-trade illustrations (OptionStrat theory, not fills):** a single bullish calendar showing
  "**180% on max risk in ~10 days**" `@04:49`; a double calendar with "**71% chance of profit**" and a
  ±2.4% break-even range `@08:46`.

## Objective assessment (where to be skeptical)

1. **No separable track record — the central problem.** Unlike Bernich's 3 months of monthly trade
   stats, Ravish gives **zero** trade-level evidence: no trade count, no P&L series, no losing trade
   walked to the end. Just an **account-growth anecdote** ($400k→$2M) that is **un-auditable** and
   **internally inconsistent** — he says it was "trading **only** this strategy" `@23:51`, yet the
   whole 80/20 pitch says double calendar is only **20%** of capital `@24:06`. Both can't be true; the
   headline is doing promotional work. New channel + (discontinued) mentorship = soft sales frame
   `@28:55`.
2. **The edge is an admitted-hard discretionary vol forecast.** The trade lives or dies on **VIX
   direction during the hold**, and he says plainly "**the trick is to know when volatility will go up,
   which is easier said than done**" `@15:06`. So the win-rate claim is inseparable from an unspecified
   "I've done this so long I can tell" skill `@19:46` — not a rule, not reproducible.
3. **Vol crush is a common (not tail) failure mode.** A modest VIX drop turns the middle of the tent
   into "**a sea of red**," POP → ~30% `@11:59`–`@12:24`. Because he runs a **layered weekly campaign**,
   **all open tents are long-vega and crush together** on a single vol collapse. He's honest about this,
   but it means "passive/set-and-forget" `@22:05` undersells a position that needs an active vol view.
4. **Tail/gap risk is real and he says so.** Range-based; a COVID-style 5–10% gap "**could get wiped
   out**," "most likely the trades I'm holding lose" `@25:34`–`@25:54`. With **no hard stop** and
   overnight exposure, the defined per-trade debit can still mean **multiple simultaneous max-losses**.
   The 80/20 sizing is his mitigation — i.e. he concedes this sleeve can be largely lost.
5. **The "negative-vega trick" is hand-waved.** Switching the short leg to Wednesday so a long-vega
   structure "does the trick" and profits on a vol drop — **while the platform still shows it long
   vega** `@21:08` — is asserted with **no mechanism**. Calendar vega is dominated by the **back (long)
   leg's** expiry, so a near Wed/next-Fri pair narrows the gap and changes the vega/theta mix, but
   "even if VIX is 50 I make a lot of profit" `@16:24` is an extraordinary claim shown with **no
   example**. Treat as unverified.
6. **Winners-only, theoretical P&L.** Every curve is an **OptionStrat model** (180% / 71% POP / 100%+
   on a spike) — favorable snapshots, no real fills, no losing example carried through. OptionStrat
   greeks/marks are estimates, especially across split expiries.
7. **Costs hand-waved.** He concedes **fills are hard** — 4 legs across different expiries, large orders
   must be split `@22:30`. On a **15–30% target**, SPX multi-leg commissions + the bid/ask he's
   "working around" are material and unaccounted for.
8. **Adjacent "zero risk" claim is a red flag.** The "hybrid collar … won't lose a single dollar even
   if the stock drops 50%" `@27:47` is the classic can't-lose overstatement (a real collar caps but
   does not eliminate downside without giving up essentially all upside) — not this strategy, but it
   calibrates the presenter's tendency to round risk down to zero.

## What's genuinely sound (the diamond)

- **It's a clean, standard, well-understood structure.** A double calendar is textbook; the **vega
  design is internally coherent** — long-vega tent that *wants* a vol expansion, paired with the
  empirical "VIX spikes on shocks" behavior. No proprietary black box on the structure itself.
- **Defined risk per position** (max loss = debit, cash-settled index, no assignment) and a **sensible
  exit discipline** — scale out at 15–30%, **always out 2–3 days before expiry** to dodge the center
  sag and pin/gamma. That timing rule is correct and important for calendars.
- **Unusually candid about the real risks:** names the vol-crush "sea of red," the black-swan wipeout,
  and that he **sizes small (20%) precisely because this sleeve can be lost.** That risk honesty is a
  notch better than the channel's "can't lose" norm (Burrito), even if the returns are un-evidenced.
- **The mechanical skeleton is the most faithfully backtestable of the three calendars** (no
  intraday transform like Bernich, no per-week "artistic" curve like Time Flies).

## Backtestability

- **Testable mechanical skeleton:** SPX double calendar, put calendar below + call calendar above at
  **~expected-move strikes** (≈1.5–2.5% OTM, or a fixed delta proxy), **short leg 10-DTE Friday**,
  **long leg +2 to +7 days** (next Mon or next Fri), enter for a debit on Tue/Wed, **only when VIX <
  20**; exit at **+15–30% of debit** or **2–3 days before the short expiry**, whichever first; secondary
  exit if price touches either strike. Measure win rate, avg P&L (% of debit), max loss, and **EV after
  multi-leg SPX commissions + slippage** (fills are the soft spot). Compare against the **null**: a
  plain weekly iron condor at matched strikes/exits — does the *calendar* (long-vega) construction beat
  a short-vega condor over the same window, and in which vol regime?
- **Testable secondary question (the actual claimed edge):** does **entering only when VIX is low and a
  rise is "likely"** add measurable EV vs random entry? Use an EOD proxy (e.g. VIX percentile +
  term-structure) since his discretionary "I can tell" can't be replayed. The headline depends on this;
  if the EOD proxy has no edge, the strategy is a generic long-vega tent riding the 2022–2025 vol-spike
  regime.
- **✅ Data (SPX confirmed):** Athena `silver.options_daily_v3` has **SPX (46M rows, 2010 → 2026-02-20,
  full greeks + bid/ask)** and **XSP**, with short-DTE expirations present → the calendars are
  constructible at EOD. **QQQ/SPY/large caps would need confirming** if testing his non-SPX universe.
- **⚠ EOD-only caveat:** "daily" resolution **fits his once-a-day, multi-day-hold style well** (unlike
  Bernich's intraday transform) — entry on the Tue/Wed close and exit on a target/deadline close are
  faithful. But the **discretionary VIX-direction call and intraday scale-outs can't be replicated**;
  the test is the rules-based floor and should **underperform** any genuine vol-timing skill he has.
- **Not faithfully testable:** the "negative-vega Wednesday trick" (assert-only, no rule), the VIX
  forecast, and discretionary strike-nudging.

## Open questions / next step

- Does the rules-based skeleton have **positive EV after fills/commissions**, given the thin 15–30%
  target and admitted fill difficulty? Calendars are notoriously slippage-sensitive.
- **Regime split:** how does it do isolated to **vol-crush stretches** (e.g. post-spike VIX mean
  reversion) vs the **vol-spike** windows (2022, Aug-2024, Apr-2025) the pitch leans on? The headline
  ("Trump tweets → VIX spikes → 100%+") is a **regime tailwind**, not a structural edge.
- **Does VIX-low entry timing beat random entry** on EOD data — i.e. is the claimed edge real or is it a
  generic long-vega bet that happened to coincide with a high-vol era?
- **Head-to-head with Bernich:** same entry, so test **"hold the calendar and exit at 15–30%"
  (Ravish) vs "transform to a credit IC" (Bernich)** on one SPX engine — which management wins, and in
  which regime? This is the natural shared backtest (`backtests/dc_time_machine/` would cover both).
- Report results as **% of capital / max-loss**, never the un-auditable account-growth dollar figure.
- **Next step (on command only):** backtest the skeleton under `backtests/double_calendar_ravish/`,
  ideally sharing the SPX calendar engine with `backtests/dc_time_machine/`.
