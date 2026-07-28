# Triple Calendar Spread — Vipul

Source: `2026-05-03_6d0tVjJnzvQ` — "How I Doubled My Money With Triple Calendar Spreads (Full
Breakdown)" ([watch](https://www.youtube.com/watch?v=6d0tVjJnzvQ)). Guest: **Vipul** (first name
only; started options 2019 in the US, now in NCR/Delhi, India; runs a YouTube channel + Discord
where he posts his trades `@29:10`). Host: John. Mid-video sponsor plug for the paid "Earnings
Watcher" tool with a community discount `@07:26` — soft sales frame, plus his own channel/Discord
funnel.

**Identity / relation note — this is the THIRD calendar episode in the KB, and the most
"vanilla-plus-one" of the trio.** A triple calendar is just Ravish's **double calendar**
(`strategies/double_calendar_ravish.md`: put calendar below + call calendar above) **with a third
ATM calendar added in the middle** `@03:12`. So: same long-vega tent family as Ravish and Steve
Bernich (`strategies/dc_time_machine.md`), and a cousin of Simon Black's Time Flies
(`strategies/time_flies.md`, which uses a put *diagonal* + call *BWB* instead of three calendars).
Notably, Vipul's parameterization is **closer to the user's own working SPY dcal than the other two
TP calendars**: he uses a **7-day calendar gap (sell 21 DTE / buy 28 DTE)** and **expected-move
strike placement** — i.e. the wider +7 gap that the user's memory notes is the *net-positive* config,
not the tight +2/+3 Fri-Mon gap that made Bernich/Ravish net-negative after fills. He does NOT
transform (Bernich) and does NOT hold to the last week (unlike Ravish's 2–3-days-to-expiry hold) —
he hard-exits at **7 DTE**. That combination makes his skeleton the most promising of the three to
test, even though the evidence is still one year.

## Verdict

> **Conviction: 2 / 5 · Risk: 4 / 10 (defined-risk debit, but long-vega campaign + adjustment-stacking) · Tested: NO**
> A disciplined, defined-risk long-vega tent with the **most sensible calendar rule-set of the three
> TP calendar episodes** — a firm 10%-of-debit profit target, a hard 7-DTE time exit (dodging the
> center-sag / pin week), an event rule (keep CPI/FOMC *between* the legs, never sell a leg after an
> event), and VIX-based sizing. Unlike Ravish, he actually **shows a per-trade log** (2025: 17
> trades, 82% win, +6.33% avg, 11-day hold) — real, if thin, evidence rather than an account-growth
> anecdote. The single best thing is that discipline + the user-friendly +7 gap; the single worst is
> that the "**doubled my money every year**" headline is (a) just the *sum* of ~17 tiny %-of-debit
> trades in **one** year, (b) unverified for the prior years, and (c) internally inconsistent — he
> only adopted the 21-DTE triple version "since 2025" `@18:09`, so there is no multi-year record of
> *this* strategy at all. The third (middle ATM) calendar adds cost and vol-crush exposure over a
> plain double for unclear benefit. Rated **2/5** — a notch above Ravish (1.5) for showing an actual
> trade log, at Bernich's level (2); it does not clear the bar for higher because the sample is one
> year, screenshotted-not-audited, with a sponsor/channel sales motive.

## Mechanics

- **Underlying:** index preferred — SPX, SPY, or **QQQ (his favorite, "always aligned to QQQ")**;
  optionally stocks near earnings if you want more juice. Cash-settled index for safety. `@08:36`,
  `@09:10`
- **Structure — triple calendar (6 legs, 2 expiries):** three same-strike calendars, each = **sell
  the near expiry, buy the far expiry** (net debit): a **middle ATM calendar**, an **upper (call)
  calendar**, and a **lower (put) calendar**. `@03:12`, `@04:44` Example (QQQ ~638): **635 middle,
  605 lower, 665 upper**, debit ~$426–434. `@04:44`, `@14:35`
- **DTE / calendar gap:** **sell leg 21 DTE, buy leg 28 DTE** — a **7-day (one-week) gap**, both
  **Friday** expiries. If entering mid-week he stretches to ~23 days to keep the sell leg on a
  Friday. `@09:22`, `@09:44`
- **Strike selection (semi-mechanical):** middle = ATM rounded to a **multiple of 5** (avoids
  thin-volume odd strikes). Outer strikes = ATM **± the expected move**, computed from the **ATM
  straddle price** of the 21-DTE expiry, **plus ~5 points of margin** (e.g. 25.8-pt expected move →
  round to 30). `@11:26`, `@12:15` Then **discretionary ±5-pt nudges** for support/resistance or a
  strong recent trend. `@13:17`
- **Entry timing / event rule:** enter roughly weekly. **Never let the sell (near) leg sit after a
  known event** (CPI, FOMC) — ideally keep the **event between the two legs** (buy leg after, sell
  leg before). `@09:57`, `@23:54`
- **Volatility gate:** works "most of the time"; if **VIX ≤ ~12–13**, profits shrink (10% → ~5%), so
  he **reduces size or skips** those days. `@10:40`
- **Profit target:** **+10% of the debit paid**, taken whenever hit — first day or fifth. `@06:13`,
  `@15:13` Typically reached in **2–10 days**. `@16:30`
- **Stop / hard time exit:** **no price stop.** Hard rule: **close at 7 DTE of the sell leg (one week
  left), whatever the P&L** — never carry into the final week (center sag / pin / gamma). `@15:26`,
  `@16:17`
- **Adjustments (discretionary):** if price **breaches an outer calendar**, add a **4th calendar**
  (same expiry, strike just ahead in the direction of the move); keeps existing calendars open
  ("closing them doesn't help — they're peanuts by then"). In a big move (Oct 2022 drop) he added a
  **5th** calendar. Usually stops at four. `@18:23`, `@19:00`, `@19:19`
- **Sizing:** deploys a **large capital amount** and "sleeps peacefully"; reduces size in low VIX.
  `@10:40`, `@24:39`
- **Self-rated risk:** **2–3 / 10.** Reasons: max loss is bounded by the debit, and "a calendar can't
  go to zero" because the near/far premium difference can't collapse to nothing. `@24:27`, `@25:10`

## Claimed edge & returns

All **self-reported**; the only artifact shown is an on-screen **2025 spreadsheet** (not audited):

- **"Roughly 100% — double my money — every year."** `@00:12`, `@01:05` (unverified; see #1 below).
- **Target 10% per trade, win ratio "above 80%."** `@02:28`, `@07:16`
- **2025 (the shown log):** **17 trades, 3 losses → 82.35% win, +6.33% avg return, ~11-day avg hold**
  (incl. weekends). One example: 17-Apr entry, closed 28-Apr, **+11.12%**. `@26:20`, `@26:39`
- **All returns are "% of the debit you paid"** (max risk), not account. `@27:15`
- **Losses:** ~20% of trades; usually **< 10%**, but **once 30–35% in 2022**. `@16:55`, `@17:08`
- **2026 YTD:** **4 trades, 3 winners, 1 loss of −8.6%** (a QQQ up-move requiring two adjustments).
  `@27:23`
- **Track-record caveat he states himself:** he only switched to the **21-DTE triple** version
  **"since 2025"** — earlier years used a **14-DTE** parameterization. `@17:44`, `@18:09`

## Objective assessment (where to be skeptical)

1. **"Doubled my money every year" ≠ an account return.** The 2025 log is **17 trades × ~6.33% of
   debit ≈ 107% summed** — a *sum of small per-trade percentages on the at-risk debit*, un-compounded,
   and only "double the money" if 100% of allocated capital is continuously in debits (it isn't — he
   sizes down in low VIX and sits between trades). It is the standard calendar framing, not an audited
   NAV double, and the headline is doing promotional work. Report on a common capital / max-loss basis
   before ranking.
2. **The multi-year headline is unverified and inconsistent with his own timeline.** He's traded
   *this* (21-DTE triple) version for **one year** `@18:09`; the "every year" claim spans a
   14-DTE-and-earlier era he says he "changed a lot." So there is **no separable multi-year record of
   the strategy being pitched** — just a single 2025 spreadsheet screenshot plus a 4-trade 2026 stub.
3. **One-year, screenshot-only sample.** 17 + 4 = **21 trades** of the actual strategy, self-tabulated,
   no broker statements, no third-party audit. Better than Ravish's account-growth anecdote (Vipul at
   least gives trade count / win rate / avg return), but far short of a falsifiable multi-year series.
4. **The win rate is P(hit a tiny 10% target), and the EV hinges on the losers.** 82% win at +10% vs
   18% losers "up to 30%" ≈ 0.82·(+10) − 0.18·(≈15) ≈ **+5–7%** — consistent with his +6.33% avg, but
   the whole edge lives in keeping the loss tail near his claimed size. One 30–35% loss (2022) already
   equals ~5 winners; a cluster of vol-crush losers on a layered book would flip the year.
5. **Thin target on a small debit → fills are the enemy.** 6 legs across 2 expiries, target = **10% of
   a ~$426 debit = ~$42**. QQQ multi-leg commissions + bid/ask across split expiries eat exactly this
   kind of thin edge — the same cost problem that made Bernich's and Ravish's *tight-gap* skeletons
   net-negative in the backtest. He even concedes OptionStrat "**will not calculate the exact
   numbers**" for calendars `@29:45`, i.e. the demoed P&L is model theory, not fills.
6. **Long-vega campaign = correlated vol-crush risk.** Every open tent (and especially the added
   **middle ATM** calendar) is long vega; a single VIX collapse sags them **together**. He's honest
   about it ("VIX falling is the one you usually see," profits then need more days `@22:35`, `@23:42`),
   but "sleep peacefully with big capital" undersells a book that needs vol to hold up.
7. **Adjustments are the real tail, and they compound cost.** The losing scenarios (2022 −35%, 2026
   −8.6%) are exactly the ones where he **stacks a 4th/5th calendar** into the move `@19:00` — more
   debit, more legs, more long-vega, into the trade that's already wrong. These add-ons are
   discretionary and unlogged; the clean per-trade stats don't capture the campaign-level risk of a
   trending market that keeps breaching the outer strike.
8. **"A calendar can't go to zero" ≠ low risk.** True that full loss is near-impossible, but his own
   realized **−30–35%** is a large drawdown, and self-rating the strategy **2–3/10** rounds that down.
   Defined-risk, yes; low-risk, only if the vol regime cooperates.
9. **What does the *third* (ATM) calendar buy you?** A triple = a double + an ATM calendar that sits
   right where the center sag and vol-crush hurt most. It adds 2 legs of cost and the most
   vol-sensitive piece for a fuller tent middle — an open question whether it beats the cheaper double
   at the same +7 gap.

## What's genuinely sound (the diamond)

- **The rule-set is the best-disciplined of the three TP calendars.** A firm **+10% target**, a
  **hard 7-DTE time exit** (correctly avoiding the center-sag/pin week — the thing Ravish flirts with),
  the **event-between-the-legs** rule, and **VIX-based sizing** are all correct, mechanical, and
  reproducible.
- **He actually shows a per-trade log** (count, win rate, avg return, avg hold) — thin (one year) but
  materially more evidence than Ravish's un-auditable "$400k→$2M," and honest that returns are % of
  debit, that 2022 gave a 30–35% loss, and that 2026 already has a loser.
- **The parameterization is user-relevant.** The **+7-day calendar gap** and **expected-move strike
  placement** match the *net-positive* config in the user's own SPY dcal work (memory: tight +2/+3
  gaps lose to fills; the +7 gap is the one that survives). This is the closest any TP calendar comes
  to the user's validated setup.
- **Defined risk, cash-settled index, no assignment, bounded per-trade loss** — no naked short vol,
  no blow-up beyond the debit (plus discretionary adjustment cost).

## Backtestability

- **Testable mechanical skeleton (the most faithful of the calendar trio):** QQQ/SPY/SPX triple
  calendar — ATM middle + upper/lower at **ATM ± ATM-straddle expected move + ~5 pts**, all at rounded
  strikes; **sell 21-DTE Friday, buy 28-DTE Friday (+7 gap)**; enter weekly, **skip when VIX ≤ 13**,
  **never let the sell leg sit after CPI/FOMC**; exit at **+10% of debit** or **hard-close at 7 DTE**,
  whichever first. Measure win rate, avg %-of-debit, max loss, and **EV after QQQ multi-leg
  commissions + slippage** (the soft spot). Natural **null**: (a) the same tent as a **double** (drop
  the ATM calendar) — does the third calendar earn its cost? and (b) a plain weekly **iron condor** at
  matched strikes — does the long-vega construction beat short-vega in this regime?
- **Directly comparable to prior work:** shares an engine with `backtests/dc_time_machine/` and the
  user's own `double_calendar_study.py`. Because Vipul uses the **+7 gap** (not the tight gap that
  tested net-negative), this is the calendar most likely to survive costs — worth running against the
  user's existing SPY dcal result as the benchmark.
- **⚠ EOD-only caveat (`silver.options_daily_v3`, daily resolution):** his once-a-day, multi-day-hold
  style fits EOD *well* (entry/exit at the close are faithful; no intraday transform like Bernich). But
  the **discretionary ±5-pt strike nudges** and the **4th/5th-calendar adjustments** can't be
  replicated — the test is the rules-based floor and should **underperform** any real management skill.
  Data: **SPX confirmed** (46M rows, greeks + bid/ask); **QQQ/SPY coverage + short-DTE expirations need
  confirming** for his preferred underlying.
- **Not faithfully testable:** the discretionary strike nudges, the adjustment stacking, and the
  "double my money" account-level claim.

## Open questions / next step

- Does the **third (ATM) calendar** add EV over a plain double at the **same +7 gap**, net of the two
  extra legs' cost? This is the central novel question of the episode.
- Does the **+7-gap triple** beat the user's **existing SPY dcal** (the +7 benchmark that already
  tested net-positive), or is it just a fuller-tent variant of the same edge?
- How does it hold up **isolated to vol-crush stretches** (VIX mean-reversion) vs the vol-spike windows?
  The long-vega campaign wants rising vol; a benign 2025 flatters it.
- Does the **VIX ≤ 13 skip** and the **event-between-the-legs** rule add measurable EV on an EOD proxy,
  or are they hygiene with no edge?
- **Cross-reference:** host explicitly ties this to **Ravish Ahuja's double calendar** (the channel's
  most-viewed video) `@30:13`; treat Bernich/Ravish/Vipul as one family, three managements
  (transform / hold-to-near-expiry / +7-gap-with-7-DTE-time-exit).
- **Next step (on command only):** backtest the skeleton under `backtests/triple_calendar/`, sharing
  the SPX/QQQ calendar engine with `backtests/dc_time_machine/`, and A/B it against both a double and
  the user's own +7-gap SPY dcal.
