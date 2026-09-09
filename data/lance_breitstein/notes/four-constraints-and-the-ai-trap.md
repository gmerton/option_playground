# The four constraints (edge → execution → opportunity → risk), and the AI trap

> **Verdict:** The most useful diagnostic frame in the KB, and it lands uncomfortably on this repo's own September work.
> **Type:** review-process / psychology (unfalsifiable as stated; the diagnosis it produces is checkable against the journal)
> **Sources:** `3sug7e1AYk8` — You're Solving the Wrong Trading Problems (2026-07-18) · `Z9THivbJ2mI` — The Claude Trading Trap Killing Your PnL (2026-08-26)

---

## The frame [3sug7e1AYk8 00:55–08:38]

Four constraints, in a strict hierarchy; the bottleneck moves as you improve, and advice only works when it matches the constraint you actually have.

| Constraint | You are here if... | The fix |
|---|---|---|
| **Edge** | inconsistent, negative P&L over weeks, strategy-hopping; you cannot say with data why the setup works, where it fails, which conditions favour it | research: one setup, a playbook, screenshots, statistics |
| **Execution** | the playbook is profitable but your results are not; best trades look like the playbook, worst trades are outside it; "I knew what I should have done" | process: defined entries/exits, checklists, routines that make discipline easy, sleep, the daily report card; automate if you cannot |
| **Opportunity** | edge + discipline, but you wait more than you trade; growth plateaued for lack of setups | expansion: scanners, alerts, more markets/products/timeframes, adjacent playbooks — "10x the opportunities beats a 5% better setup" |
| **Risk** | huge swings and give-backs ("if I had sized smaller I'd still be fine"), or flat for years with no best day in ages | **pre-assign risk levels by trade quality, then grade yourself daily on whether you risked accordingly** |

The one question he asks every mentee: *if we could fix only one thing in the next six months, what would create the biggest improvement?*

## The AI corollary [Z9THivbJ2mI]

- AI helps only if it works on your current constraint [02:11–02:26]. Tangible output (code, reports, agents) feels like progress; "markets have never paid anyone for a cool workflow" [12:16].
- The example that maps onto this repo [04:24–04:50]: *a trader makes $20k on his best strategy and loses $12k on everything else — I'm not interested in giving him another strategy; I'm interested in why he needs all those other trades.*
- Where he says AI does earn its keep [06:35–06:58, 08:50–10:47]: classify a large trade database, build a test for a setup hypothesis, automate nightly repetitive work, **and diagnose from the P&L first** — compare exits to subsequent price action, cut by setup and environment, check whether size changes behaviour, then build the guard (e.g. "an automated program that detects and blocks you from trying to play back").
- His own case [04:50–05:42]: the right-side-of-the-V concept came from diagnosing his own reversal losses; AI "could have easily distracted me from finding my true limitation."

## ⚠ What the frame says about this repo, honestly

The September 2026 journal evidence (9/8–9/9: same-day exits on working plan entries, stops inside noise on correct short theses, four unplanned scalps a day, two mega-cap dip buys below VWAP, vehicle doubling) is **execution-constrained** trading on Breitstein's definitions — the best trades look like the plan, the worst are outside it. Meanwhile the week's tooling (universe alert monitor, short detectors, website feed) is **opportunity** work. By his hierarchy that is a rung too high: more alerts do not fix an execution constraint, and the 9/9 scorecard (19 alerts, the one that worked was missed, the losses came from trades no alert suggested) is consistent with that.

The parts of the week that do sit on the right rung, by his own list: the journal's per-trade verdicts, the same-day-exit tally, the stop-in-ADR tag, the CRCL higher-low rule, and the "pre-assign risk by quality and grade yourself daily" idea, which is the A–D grading video still pending ingest (`ubofAZwgd4w`).

**Standing caveats:** course pitch in both videos ([09:46], [05:59–06:35]); the constraint labels are his, not a validated taxonomy; the AI video's skepticism is also positioning against a competitor for the same audience.
