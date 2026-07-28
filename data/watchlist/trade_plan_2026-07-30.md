# Trade Plan — ILMN earnings EP (print 2026-07-30)

> Built 2026-07-23. Companion to `trade_plan_2026-08-05.md` (RVMD) — same EP grammar; mechanics not
> repeated here, only the deltas. ⚠ Verify report timing — ILMN has historically reported AMC, which
> would make the EP session **Jul 31**.

---

## State as of 7/23

- **Potent AND Leader** (only dual-qualifier in the universe): 1M +19.4%, 3M +50.9%, RS 93 (7/22
  Minervini scan). Stage 2 (50/150/200 = 169/144/137, price 196.86), $262M/day, ADR 3.73%
  (**marginal** pass — thinner payoff-per-stop than RVMD's 4.1). XBI top-3 industry.
- **⚠ Currently poking THROUGH the pivot 196.66 (+0.1%) on 0.63x volume.** Light-volume pre-earnings
  drift = the pattern the framework distrusts (CVS/USB/AAPL cases). NOT a breakout signal — and
  irrelevant anyway because:
- **The 5-session earnings gate is ALREADY CLOSED** (print in ~5 sessions). No pre-earnings entry,
  full stop. There is no Case-1 contingency for ILMN. Anything it does before Jul 30 only moves the
  reference pivot for the EP.

## PRIMARY: earnings EP — same mechanics as RVMD plan, with these deltas

1. **Gap bar:** ≥ +8% from the pre-print close (≈ ≥ $213 from ~197; recompute). It already sits at
   the pivot, so "through the pivot" is trivially met — the qualification burden is entirely on
   **gap size + premarket volume** (≥ ~1M premarket / pace ≥ 3× the ~1.4M 50d avg).
2. **Extension check (extra for ILMN):** if it keeps drifting UP into the print (e.g. >$205 by
   Jul 29, >4% above pivot), the EP is launching from extension — downgrade: skip the 1-min entry,
   use only the 15/60-min ORH at half size. An extended-then-gapping leader is where gap-and-crap
   lives (Luk: extension into an event = the risk, and leaders failing = market tell).
3. **Market + sector gate:** identical (SPY/QQQ not printing a distribution day at trigger; XBI not
   risk-off). Regime is SERIOUS — default to the low end of 0.3–0.5% risk.
4. **Vehicle: stock.** ADR 3.73 is marginal but acceptable for an EP (the gap supplies the range).
   No options at the open; chain check only after a daily-close confirmation.

## SECONDARY / TERTIARY

Same as RVMD plan: Archetype-B gap-and-hold day-after (cash-session hold above the pivot, close near
highs, ≥2x volume; never buy the premarket pop), then the first pullback to the rising 9/21.

## Sequencing: ILMN is the SCOUT for RVMD (correlation rule)

- Both are XBI names with prints 4 sessions apart. **Treat the two EPs as one theme bet: combined
  risk cap ~0.75%** (mirror of the XLU/XLV/XLP same-gate correlation cap).
- ILMN EP fires and HOLDS its gap → confidence upgrade for the RVMD Aug 5 EP (full planned size
  within the cap). ILMN gaps-and-craps or fades below the gap midpoint → biotech-EP appetite is weak:
  halve RVMD's planned size or demand the slower ORH there too.
- If ILMN's EP filled and is still held on Aug 5, RVMD takes the *remainder* of the cap only.

## NO-TRADE cases

Same list as RVMD plan (sub-8% gap, gap-and-crap, red market gate, XBI risk-off) plus one:
- **Pre-print light-volume "breakout" extends >4-5% above the pivot and then earnings gap up:**
  that's a gap on top of an unconfirmed move — 15/60-min entry only, half size, or pass.

## Reminders

- Re-run `run_breakout_scorecard.py ILMN` the evening before the print (pivot will have migrated if
  the drift continues).
- Genomics single-name: guidance/consumables commentary can gap it ±15%; no short puts into the
  print, no anticipation positions (the 7/21 analysis already rejected selling puts through this
  print for exactly this reason).
- Morning-of: `premarket_watchlist.py --mode premarket` flags the ≥8% EP automatically.
