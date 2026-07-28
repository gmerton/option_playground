# <Setup Name>

> **Verdict:** <one line>
> **Type:** intraday | swing | options overlay · **Instrument:** <ES/SPX/equities/…>
> **Conviction:** _/5 · **Risk:** _/10 · **Tested?** no | partial | yes
> **Source:** Ch. _, pp. _–_ (3rd ed., 2019)

---

## 1. Mechanics

Precise enough to backtest. If you can't write it this precisely, the setup isn't ready to
promote out of `notes/`.

- **Universe / instrument:**
- **Timeframe / session:**
- **Setup condition (the state that must exist):**
- **Trigger (the event that puts you in):**
- **Entry:**
- **Stop:**
- **Target / exit:**
- **Position sizing rule:**
- **Filters & vetoes:**

## 2. Claimed edge & returns

His numbers, quoted, with page refs. Note whether they're stated as a track record, an
illustration, or nothing at all (often the third).

## 3. Market-structure dependencies ⚠

The key question for this book. Baseline is **2019** — pre-HFT/decimalization concerns are likely
already handled by the revision. The live questions are what came *after*: 0DTE dealer-gamma flows
(SPX dailies completed 2022), the 2020 vol/retail-flow shift, and ongoing NYSE TICK distribution drift.

- **Depends on:**
- **Changed since 2019?** yes / no / unknown — evidence:
- **Hard-coded thresholds?** (TICK ±N, gap %, ATR multiples) — list them; re-derive from current
  data before testing. These are the most perishable rules in the book.
- **Verdict on decay risk:** low / medium / high

## 4. Objective assessment

Red flags, oversell, the real risks, what's unverifiable. Where the discretionary joints are.

## 5. What's genuinely sound

The legitimate core, if any — stated separately from the packaging.

## 6. Testability

- **Class:** EOD-testable now | needs intraday data | discretionary/untestable
- **Data needed:**
- **Testable skeleton:** the mechanical subset you'd actually run
- **What the skeleton can't capture:** (say this explicitly — it's how the other KB backtests
  avoided overclaiming)

## 7. Overlap / conflicts with the existing book

Does this duplicate, refine, or contradict something already in the repo (Minervini scan, Luk
principles, the allocation framework)? Name it.
