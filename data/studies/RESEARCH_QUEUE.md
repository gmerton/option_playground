# Research Queue

Scoped-but-not-yet-run work. Newest at top. Move to a playbook once complete.

---

## Long straddle — measure entry slippage (QUEUED 2026-08-08)

**Why:** every straddle number in `long_straddle_playbook.md` prices at **mid with zero
slippage**. Sensitivity is **−0.95pp of ROC per 1% paid over mid**, so at a realistic
1–3% the honest edge drops from ~+12.6% to ~+9.8–11.6%. This is the single largest
remaining unknown in the strategy.

**What to do:** add `call_bid/call_ask/put_bid/put_ask` to the entry leg selection in
`run_straddle_pool_pull.py` (the current pull returns mids only), then recompute arm 4
paying a realistic fraction of the spread. Cost is **one-sided** — expiry settles, so you
only cross on entry.

**Also worth doing in the same pass:** the −50% stop is modelled as a loss clip
(`max(roc, −50)`), which contributes **+6.85pp — 55% of the headline** by rescuing 29.6%
of trades. A path-dependent version needs daily marks on the specific contracts between
entry and expiry. Expensive, but it is the other half of the uncertainty.

---

## Track 1 — Extend the put-calendar franchise (QUEUED 2026-08-08)

**Why:** XLU (347), XLV (286) and XLP (239) are ranks 1–3 in the whole book, share an
identical spec, and are deployed on only three underlyings. Highest-expected-value
extension available — pure replication against a known-good playbook, no new method.

**Spec to replicate verbatim** (from `xlv_calendar_playbook.md`; XLU and XLP are identical):

- Short leg: ATM put (~0.50Δ), front monthly, ~20 DTE
- Long leg: ATM put, **same strike**, next monthly (25–50 day gap from short expiry)
- Gate: `fwd_vol_factor ≤ 0.90`, where
  `fwd_vol_factor = sqrt((long_iv²·T_long − short_iv²·T_short)/(T_long − T_short)) / short_iv`,
  BS IVs at r=0.04
- Max bid-ask 25% of mid on the short leg; both legs positive bid
- Net debit; max loss = debit

**Wave 1 — the six Select Sector SPDRs not yet traded:** XLI, XLK, XLB, XLY, XLC, XLRE
**Wave 2 (only if wave 1 produces candidates):** XBI, KRE, XOP, XME, XRT, XHB — run the
option-liquidity gate first; the industry SPDRs are much thinner and several will fail the
25% bid-ask rule.

**Tooling:** `run_calendar.py --ticker <X> --short-dte 20 --min-gap 25 --max-gap 50`
(engine: `src/lib/studies/calendar_study.py`). No new code expected.

**Report per name:** fire frequency (XLV fires ~8 Fridays/yr — that selectivity is *why* it
scores 347), ROC, win rate, priority score, and **overlap of firing weeks with XLU/XLV/XLP**.

⚠ **Overlap is a first-class output, not a footnote.** The 3% combined-calendar debit cap
already binds when all three current names fire together on FOMC weeks. A new name that fires
on the *same* weeks adds nothing tradeable; one that fires on different weeks is worth more
than its standalone score suggests.

**Prior:** the XLV rationale is explicitly sector-specific — low drift, mean-reverting, and
diversified earnings that cancel out. XLU and XLP share that profile. **XLK and XLY do not**
(high drift, momentum-driven), so expect them to fail — that outcome is informative, not
wasted. XLB and XLRE are the better bets on the same logic.

---

## Deferred — Roster friction audit

Recompute every confirmed strategy's ROC at 25% and 50% of bid-ask crossed, and rank by how
much edge survives. Motivated by the XSP work (2026-08-08): every configuration tested was
profitable at mid and almost none survived half-spread fills, and each additional leg costs
~1.5pp of per-trade return. The confirmed book's headline ROCs are mid-priced.
User deferred 2026-08-08 ("not right now").
