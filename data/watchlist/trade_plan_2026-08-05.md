# Trade Plan — RVMD earnings EP (print 2026-08-05)

> Built 2026-07-23 from the scenario walk-through (scorecard + Minervini scan + Luk KB read).
> Grammar: Qullamaggie/Adhikary EP — no pre-earnings entry; buy the *reaction*, not the prediction.
> ⚠ Verify report timing (BMO vs AMC). If AMC, the EP session is **Aug 6**, not Aug 5.

---

## Why this name (state as of 7/23)

- Cleanest long candidate in the universe: **every gate passes, no `!` tags** — Stage 2 (50/150/200 =
  167/127/111, price 188.75), ADR 4.11% (stock is the right vehicle), $363M/day, **RS 99** (7/22
  Minervini scan), Potent, coiled **2.6% under pivot 193.82**.
- Sector: XBI top-3 industry RS (+9.4%), "lower-risk leader"; XLV #2 sector. Passes Luk's bull-trap
  test — based *at highs* through the correction (leadership), not a laggard bounce (LITE/OPEN pattern).
- Blockers today: no trigger (RVOL 0.8x) + tape (SPY/QQQ 8 distribution days SERIOUS; Luk flipped
  bearish 7/22, corroborating). The earnings EP dissolves both **if** the reaction qualifies.

---

## PRIMARY: earnings EP (day of reaction)

**Qualify the event first — ALL required:**
1. Gap **≥ +8%** in premarket (≈ ≥ $204 from a ~189 base; recheck vs actual prior close).
2. Gap carries price **through the pivot 193.82** (a +8% gap from anywhere near current levels does).
3. **Huge premarket volume** — target ≥ 1M shares premarket / on pace for ≥ 3× the 3.0M 50d avg.
4. **Market gate:** SPY/QQQ not down >0.2% on rising volume at trigger time (forming distribution
   day = stand down; regime is already SERIOUS — this is the one Luk-checklist item we can demand
   intraday).

**Entry mechanics (opening-range breakout):**
- Let the 9:30:00–9:31:00 candle complete. Buy-stop just above its high.
- Filled → **stop = low of day**, daily-close basis thereafter.
- Not filled / fades from open → NO entry. One re-entry attempt allowed on the **5-minute** ORH if
  the first trigger stops out but price holds above the gap midpoint (Luk's BMNR sequence). Two
  stops = done for the day; reassess as Archetype-B gap-and-hold next day.
- Gap opens **>~+15–18%** (super-extended): skip the 1-min entry; only the 15/60-min ORH with the
  same LOD stop, half size — extension eats the R:R.

**Size:** risk 0.3–0.5% of account on the LOD stop distance (tape is SERIOUS → stay at the low end;
half normal EP size unless the market gate is unambiguously green).

**Vehicle: STOCK.** ADR 4.1% earns its stop; EP entries need instant fills — no options at the open.
(Optional post-hold kicker only after the daily close confirms: check chain vs ≤25% BA / OI gates
before any call structure; do NOT assume the chain is tradeable.)

**Exits:** SPIKE day (+20%+ fast) → sell partials into strength, don't trail. Otherwise trail the
9/20-EMA on daily closes per the standard grammar. Failed EP = daily close back below the pivot →
out, no averaging.

---

## SECONDARY: Archetype-B day-after (if no clean ORH fill)

Beat/raise + **gap-and-hold above 193.82 on the cash session** closing near highs on ≥2× volume →
valid entry the day after the reaction. Don't buy the premarket pop (APP/PLTR rule). A pop that
stalls *under* the pivot = no trade.

## TERTIARY: post-EP first pullback (days 3–10)

First orderly pullback to the rising daily 9/21 — best if it *gaps down into* that support on a red
XBI open (Luk 7/22 principle). Stop under the pullback low. Only if the EP held its gap.

---

## PRE-EARNINGS CONTINGENCY (window closes ~Jul 29)

- **Case-1 breakout before the print:** close ≥ 193.82 on ≥1.5× 50d volume with the market gate green.
  Intraday monitor is already armed (RVMD coiled, 20d-high trigger, `monitor_latest.json`).
- **Earnings gate (5-session rule): no new entry after ~Jul 29.** An entry Jul 24–29 has ≤8 sessions
  of runway → pre-commit the de-risk date: **flatten or reduce to a cushioned core by Aug 4 close**
  unless sitting on ~8%+ cushion. Light-volume poke through the pivot = monitor only, never chase.

## NO-TRADE cases (write them down now so they're boring later)

- Gap up <8%, or gap that opens *below* the pivot → not an EP; falls back to the ordinary
  breakout/pullback playbook.
- Gap-and-crap: trades below the 1-min low / gap midpoint early and closes mid-range or lower →
  nothing. A failed earnings gap on a leader is information (Luk: leaders failing = market tell) —
  log it, don't fight it.
- Market gate red at trigger time → skip regardless of how good the tape looks. 8 distribution days
  means the burden of proof is on the market, not the stock.
- Sector check the morning of: XBI gapping hard down / biotech risk-off → EP quality downgrade,
  halve size or skip.

---

## Correlation with ILMN (see `trade_plan_2026-07-30.md`)

- ILMN (also XBI) reports **Jul 30** — its EP is the SCOUT for this one. Combined biotech-EP risk cap
  ~0.75%: ILMN holds its gap → full planned size here (within the cap); ILMN gaps-and-craps → halve
  this EP or demand the slower 15/60-min ORH. If still holding ILMN from its EP, RVMD gets the
  remainder of the cap only.

## Reminders

- Recompute the scorecard the evening before the print (`run_breakout_scorecard.py RVMD`) — pivot may
  migrate if it breaks out or builds more base before Aug 5.
- Single-name biotech: the print can include pipeline/clinical updates → gaps can exceed ±15%. The
  ORB structure is the risk control; no overnight anticipation positions, no short puts into the print.
- Cross-check morning-of premarket via `premarket_watchlist.py --mode premarket` (EP category fires
  at ≥8% gap automatically).
