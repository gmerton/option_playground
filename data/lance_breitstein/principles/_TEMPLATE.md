# <Principle / Technique Name>

> **Verdict:** <one line>
> **Type:** entry-location | sizing | exit | regime | review-process | psychology
> **Conviction:** _/5 · **Testability:** EOD | intraday-needed | process/unfalsifiable · **Tested?** no | partial | yes
> **Source:** `<videoId>`@<mm:ss> — <video title>

---

## 1. Mechanics

Precise enough to test, or precise enough to admit it can't be. If neither, it stays in `notes/`.

- **Instrument / universe:**
- **Session / timeframe:**
- **Setup condition:**
- **Trigger:**
- **Entry — exactly where, relative to what reference:**
- **Stop — exactly where, and how far from entry in %:**
- **Implied position size** at a 0.3% risk budget (= 0.3 ÷ stop%):
- **Exit:**
- **Vetoes / conditions:**

## 2. ⚠ The sizing-lever question

The repo's open question. Fill this in for every entry-location principle:

- **Stop distance as % of entry:** ____
- **Position that buys at 0.3% risk:** ____  (vs 3.3% for the 9.2% ATR stop used in the sims)
- **Does he state or imply a stop-out / "gets me out wrong" rate?** ____
  (Daily-bar baseline to beat: **91% stop-out at a 1.5% stop**, 39% at 9.2%. If his method
  genuinely runs a ~1.5% stop without a ~90% stop-out rate, that IS the mechanism.)
- **What would settle it:** ____ (1-min bars? tape? his own trade data?)

## 3. Claimed edge & evidence

His numbers, quoted, with timestamps. Note whether it's a track record, an illustration, or
nothing at all. **Flag if the claim also functions as course marketing.**

## 4. ⚠ Prop-infrastructure dependency

Does this need locates, borrow, fee/rebate structure, routing, capital, or firm risk oversight?
Anything that does is **not transferable** to a retail account regardless of whether it works.

- **Depends on:**
- **Retail-viable as stated?** yes / no / partly —

## 5. Decay risk

Attention/flow niches decay fastest of anything in this repo. Date the claim; say what market
condition it assumes; state whether that condition still holds in 2026.

## 6. Objective assessment

Red flags, oversell, discretionary joints, what's unverifiable.

## 7. What's genuinely sound

The legitimate core, if any — stated separately from the packaging.

## 8. Overlap / conflict with the rest of the repo

Especially [[martin_luk]] (the swing-side counterpart — convergence between the two is the
strongest cross-source evidence available) and
`carter_mastering_the_trade/backtests/risk_architecture/`. Name conflicts; don't silently merge.
