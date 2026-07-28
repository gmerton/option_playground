# Mastering the Trade — John F. Carter

Notes and setup write-ups from *Mastering the Trade: Proven Techniques for Profiting from
Intraday and Swing Trading Setups* (John F. Carter).

Unlike the channel KBs (`data/theta_profits/`, `data/options_with_ryan/`), this is **one author
with a coherent system** — closer to `data/martin_luk/`. But like the channel KBs, the unit of
value is the **named setup**, so the deliverable is one objective write-up per setup.

**Edition: 3rd (2019).** Note this on every write-up — the setups and especially the
market-internals material differ meaningfully between the 1st (2005), 2nd (2012), and 3rd editions.

## Prime directive: skepticism, plus a regime clock

Standard house rule applies — **separate the mechanics from the marketing**, default conviction LOW
until independently tested. But this KB has a second, more important filter the channel KBs don't need:

> **Age is a real risk, but the 3rd edition narrows it.** A 2019 revision post-dates the changes
> that would have gutted the 1st edition — decimalization, the HFT takeover, ES/MES migration —
> and Carter had the chance to re-baseline his examples and statistics against a modern tape. Treat
> pre-2005 concerns as probably already handled.
>
> **What 2019 still does NOT cover — the live decay questions:**
> - **0DTE.** SPX/SPY daily expirations only completed in 2022. The intraday index setups
>   (gap fades, TICK extremes, opening-range work) were baselined on a tape without the dealer
>   gamma flows that now dominate the session. This is the single biggest open question in the book.
> - **The 2020 vol regime and the retail-flow shift** — post-COVID participation, meme-driven
>   single-name behavior, and a structurally different VIX complex.
> - **Cumulative TICK drift.** ETF/basket flow keeps reshaping the NYSE TICK's distribution;
>   any absolute threshold (±1000, etc.) is the most perishable kind of rule in the book.
>
> **A setup validated as of 2019 is a hypothesis in 2026, not a finding** — but the burden is now
> "has this survived 0DTE and 2020?" rather than "is this pre-modern?"

So every write-up must answer: *does this setup's edge depend on a market-structure fact that has
changed since 2019?* Flag it explicitly. Don't assume decay — but don't assume persistence either.
Any setup keyed to a hard-coded numeric threshold deserves extra suspicion: re-derive the threshold
from current data before testing the rule.

Red flags to call out when present (same checklist as the other KBs):
- Winners-only chart examples; no losing trade carried to the end.
- Discretionary filters ("only when it feels right," "in the right market") that make the rule
  unfalsifiable — these are where backtests and books diverge most.
- Costs hand-waved: for intraday scalps, commissions + slippage frequently exceed the whole edge.
- Track record that isn't separable from the author's other activity or products.
- Indicator sold as the edge when it's really a repackaged volatility/momentum transform.

## What's actually testable from here

Much of the book is intraday and needs 1-min data you don't have wired up. Sort setups into:

- **EOD-testable now** — daily-bar setups run against `data/cache/minervini_matrix.parquet`
  (~5,300 names, no API cost) or Athena `silver.options_daily_v2` for the options overlays.
- **Needs intraday data** — anything on TICK, opening range, pivots-intraday, scalps. Park these;
  note the data you'd need.
- **Discretionary / untestable** — say so plainly rather than backtesting a strawman version.

The **Squeeze** is the obvious first candidate: it's a fully mechanical daily-bar transform
(Bollinger Bands inside Keltner Channels) and can be tested on the existing cache with no new data.

## Layout

```
README.md                  This file — convention, skeptic mandate, regime clock.
SETUPS.md                  Index / leaderboard: setup · type · conviction · risk · tested? · verdict.
setups/<slug>.md           One objective write-up per setup (the deliverable).
setups/_TEMPLATE.md        Copy this to start a new setup.
notes/<chapter>.md         Raw reading notes, chapter by chapter (input, not deliverable).
notes/_TEMPLATE.md         Copy this to start a chapter note.
backtests/<slug>/          (created on demand) test script + results when a setup is evaluated.
```

**Workflow:** read a chapter → dump raw notes into `notes/` → when a *named setup* is fully
described, promote it to `setups/<slug>.md` using the template → add a row to `SETUPS.md` →
backtest if it's EOD-testable.

Keep `notes/` messy and `setups/` clean. Notes are for capture; setups are for decisions.

## Relationship to the rest of the repo

- Carter's swing material overlaps the existing momentum work ([`data/martin_luk/`](../martin_luk/),
  the Minervini scan). Where he contradicts them, note it — don't silently merge.
- His options chapters (hedging, income) overlap the strategy book in
  `data/studies/capital_allocation_framework.md`. Same rule.
- Anything that becomes an active strategy graduates to `data/studies/<ticker>_*_playbook.md` and
  the allocation framework. This directory is research, not the live book.
