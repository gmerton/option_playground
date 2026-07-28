# Trade Automation ("Bots") — Scott Clark (Trade Steward)

Source: `2025-04-27_gGMc1Y3tWbY` — "How to Automate Options Trading Like a Pro in 2025"
([watch](https://www.youtube.com/watch?v=gGMc1Y3tWbY)). Guest: Scott Clark, representing
**Trade Steward**, a paid retail order-automation ("bot") platform; host: John. Scott is a
**vendor spokesperson** for the product. This is the least strategy-bearing entry in the KB: it
is effectively a **product infomercial for automation-as-a-category**, with essentially no
tradeable content.

## Verdict

> **Conviction: 1 / 5 · Risk: n/a (no strategy disclosed) · Tested: NO**
> A **tool advertisement, not a strategy.** Scott confirms the one useful cross-cutting truth —
> automation is *execution infrastructure* that lets you run a plan across many entries/accounts;
> it is **"not a get-rich thing… simply another tool to enable the trades you've already thought
> of"** (`@13:30`). Beyond that, the interview contains **no strategy, no parameters, no numbers,
> and no track record** — his own trading returns are never mentioned. It leans on an unfalsifiable
> hype anecdote ("people made more money that week than the previous two years"), a competing-vendor
> landscape plug, and repeated "join our Discord / start a trial" funnels. Rated 1/5 because there
> is nothing to independently confirm; it earns its spot in the KB only as the *category* reference
> alongside Kyle Lisman's more substantive TAT review.

## What it actually covers (tooling, not a trade)

- **What a "bot" is:** a template where you input delta/width/entry-time/profit-target/stop-loss and
  the platform deploys and manages it automatically, including **across multiple accounts at once**
  (his repeated selling point — "one trade across four accounts"). `@02:34`, `@01:21`
- **Platform landscape (competitors he names):** Trade Steward, Options Alpha, Option Omega (adding
  automation), Trade Automation Toolbox (Kyle Lisman's). Differentiator he claims for Trade Steward:
  **customer support**, not performance. `@04:47`, `@03:53`
- **Strategy-agnostic:** "can't think of a strategy you can't trade on it" — butterflies, ICs, iron
  flies; the platform's founder trades **0DTE**, which was its genesis. `@11:47`, `@12:01`
- **"Not fully auto":** explicitly *not* set-and-forget — likens it to **supervised Tesla
  self-driving**: you must still monitor. `@07:41`, `@07:50`
- **Onboarding advice:** 7-day trial → configure **one bot** → verify strikes/targets/stops match
  expectation for a week → scale slowly. Note: **major brokers lack paper-account API access**, so
  you can't paper-trade a bot end-to-end; Trade Steward offers a "test run" that only shows *which
  strikes* you'd have gotten. `@12:38`, `@13:41`

## Claimed edge & returns

- **None.** No personal P&L, no win rate, no strategy parameters, no separable record of any kind.
- The one performance claim is second-hand and unfalsifiable: during the April 2025 vol spike, "I've
  seen people make **more money in that week than the previous two years**… automation really
  enabled that." A survivorship anecdote about unnamed people in a private group. `@10:14`

## Objective assessment (where to be skeptical)

1. **This is a sponsored-style product pitch.** The guest is a vendor rep; the video's function is
   subscriptions/trials. Treat all claims as marketing.
2. **No strategy = nothing to evaluate or test.** Unlike Kyle Lisman (who at least names the
   underlying IC + trend book), Scott discloses zero trade mechanics. There is no hypothesis here.
3. **The hero anecdote survives selection bias, not analysis.** "Made more in a week than two
   years" during a huge vol event is exactly what you'd hear from the *winners* of a fat-tailed
   week; the equal-and-opposite blow-ups (see the KB's 1-1-2 file) don't get interviewed.
   Automation "enabling" larger/faster deployment cuts **both** ways — it scales losers as
   efficiently as winners.
4. **"Automation reduces execution risk" is true but narrow.** It removes fat-finger and
   slow-manual-exit errors; it **adds** software/data-feed/connectivity risk (he concedes bad-tick
   and data-blip incidents "a few times in three years") and, crucially, does **nothing** for
   *strategy* risk — a negative-EV plan automated is a negative-EV plan run faster and across more
   accounts.
5. **Paper-testing gap is a real caveat.** No broker paper-API means you cannot fully dry-run a bot
   before risking live money — the "test run" only previews strikes, not fills/management. That's a
   material limitation he states plainly (credit) but which undercuts "start risk-free."

## What's genuinely sound (the small diamond)

- **The category truth is correct and consistent with Kyle Lisman's:** automation is a **tool to
  execute a plan you already validated**, not a source of edge — and it materially helps
  *discipline* (removing the fear/greed that makes traders abandon a good plan). This matches the
  user's own thesis (`memory/feedback_conviction_selection_is_the_strategy.md`).
- **Honest disclaimers:** "not set and forget," "supervised self-driving," "understand volatility
  and leverage — spreads hide leverage," "start with one bot." Standard, sensible, correct.
- **Useful multi-account point:** for anyone running the *same* validated strategy across several
  accounts, automation is the only sane way to deploy it — a legitimate operational use case.

## Backtestability

- **Nothing to backtest.** No strategy is specified. The automation layer is orthogonal to edge and
  irrelevant to our research stack.
- **Relevance to us:** purely as a **vendor-comparison data point** if the user ever automates his
  own validated strategies — Trade Steward vs Trade Automation Toolbox (Kyle) vs Option Omega /
  Options Alpha. Evaluate on Kyle's engineering checklist (broker-resident stops, failure
  redundancy, alerting), not on either salesman's word.

## Open questions / next step

- **No trade to pursue.** File as the automation-*category* reference; the substantive automation
  review is `automation_tat_kyle_lisman.md`.
- If/when automation of the user's own strategies becomes a real project, revisit this only to
  shortlist vendors — and demand a live paper/parallel-run proof before trusting any of them with
  size, given the no-paper-API limitation Scott concedes.
