# Thesis log — macro/narrative calls, written BEFORE the outcome

Why this file: some catalysts are foreseeable by reasoning about consequences (war → crude → energy
equities; an election outcome → the names that benefit), not by any pattern a backtest can find. That kind
of edge cannot be measured backwards — "it was obvious in retrospect" is what hindsight bias feels like from
the inside. **So we write the call down first and score it later.** After ~20 entries the hit rate says
whether the soft thinking is an edge or a story.

**How to use:** add a row when a view forms, not when it pays. Every field before "Outcome" is filled at
entry. Leave Outcome/Scored blank until the invalidator or the horizon hits, then fill both honestly —
including the ones that were right for the wrong reason.

**Vehicle guidance:** the transmission map (`data/studies/oil_transmission_2026-09-18.md`) is the template —
know the capture ratio and check what is already priced before choosing the expression. A correct thesis
entered after the vehicle has run is worth roughly nothing (XLE: +3.8% forward if it has not moved, −1.5% if
it is already up 10%).

**Express it convexly when the thesis is binary and dated** (an election, an OPEC meeting, a ruling): a wrong
call should cost a premium, not a position. Size as a lottery ticket.

---

## Template

```
### <date> — <one-line thesis>
- **Reasoning:** the causal chain, in one or two sentences
- **Expected consequence:** what should happen, to what, over what horizon
- **Vehicle:** instrument + why (capture ratio / convexity / liquidity)
- **Already priced?** what the vehicle has already done vs the driver
- **Invalidator:** the observation that would make this wrong
- **Size:** risk in % of account
- **Outcome:** (filled later) what happened
- **Scored:** (filled later) right / wrong / right-for-wrong-reason; was the vehicle the best expression?
```

---

## Open

### 2026-09-20 — SNDK: index-rebalance flow, and it is NOT the Nasdaq-100 add
- **Correction to the premise.** SNDK joined the **Nasdaq-100 on 2026-04-20** (replacing TEAM) and the
  **S&P 500 on 2025-11-28** (replacing IPG) — both verified against the index change histories. The 9/18
  event is the **S&P 100 add effective Monday 9/21** (with DELL, PANW, ANET, replacing NKE, HONA, SPG, CL),
  landing on the September quarterly rebalance / triple witching. The Nasdaq-100 inclusion is five months old
  and is not the catalyst.
- **Reasoning:** Gabe is long 4 SNDK from 1,698.90 (9/18, ORB9 alert at 10:09). The tape shows the rebalance
  trade: SNDK +3.25% between 15:30 and the close on 1.98M shares in the last ten minutes (11% of the day's
  volume) while QQQ +0.31%, SPY +0.10%, MU +0.79%, WDC +0.65%, STX +0.27%. That is a closing-auction print,
  not a trend close.
- **Mechanism, partly inferred.** S&P 100 tracking AUM is small and cannot on its own absorb ~$3.5B at the
  close. The rest is most likely the quarterly re-weighting SNDK earns in indices it is ALREADY in (NDX
  quarterly reconstitution + S&P float/share-count updates, all effective 9/21) after its market cap ran.
  Not verified to the dollar; the decomposition does not change the conclusion.
- **Expected consequence:** ~~the pop gives it back~~ **TESTED 2026-09-20 AND NOT SUPPORTED.** 173 S&P 500 /
  NDX adds 2019-26: holding from the auction close returns -1.00% at T+5 (40% win vs ~51% for every control),
  but the pre-registered test came in at t -0.83 against a bar of 3, and no arm reaches |t| 1.4 against post /
  xname / extension-matched controls. A give-back is the way to bet if forced; it is not a tradeable claim,
  and extension does not sort it. **Do not sell on flow logic.** See index_add_study_2026-09-20.md.
  What survives is mechanical, not statistical: the auction close is not a trend close, so read the day off
  1,740, not 1,791.82.
- **Vehicle:** already on: 4 shares, $7,167 = 8.8% of NAV. No add.
- **Already priced?** Yes, by construction — +17.9% in two sessions off the 9/16 close, +26% off the 20-day
  low, +2.11 ADR over the 21 EMA at Friday's close.
- **Invalidator:** SNDK holds and extends on real (non-auction) volume in the first 2-3 sessions after the
  effective date — then the move is the memory cycle, not the rebalance. The other side: a close back under
  1,686.50 says the auction pop was the whole trade.
- **Tested:** `data/studies/index_add_study_2026-09-20.md` (173 events, 2019-2026) — FAIL, no index-add
  reversal. The question is closed; "index add" is not a reason to buy, hold, fade or size differently.
- **Size:** open risk to the close-judged stop (1,686.50) = $50 = 0.06% of NAV; to the 1,595 resting stop
  = $416 = 0.51% of NAV.
- **Outcome:**
- **Scored:**

### 2026-09-18 — energy equities have not priced the crude move (SEED ENTRY, Gabe to confirm or delete)
- **Reasoning:** crude is +8.7% over 20 sessions on supply/geopolitical risk; energy equities normally capture
  roughly half of a crude move within the same window, and they have not.
- **Expected consequence:** either the equities catch up over the next 4-8 weeks, or crude round-trips. The
  historical base rate favours the equity side when it has lagged: XLE forward 20 sessions is +1.9% from an
  0-5% prior move vs −1.5% when it has already run 10%+.
- **Vehicle:** XOP or USO (capture 0.67 / 0.94) rather than XLE (0.47). Refiners are already up 11.2% — late.
- **Already priced?** No, and that is the point: XLE +1.1%, XOP +2.7%, OIH −3.7%, XES −4.1% over 20 sessions.
- **Invalidator:** crude closes back below its 20-session start (the driver is gone), or XOP runs >10% before
  entry (then it is priced).
- **Size:** unset — this is a seed entry to show the format, not a recommendation.
- **Outcome:**
- **Scored:**

## Closed

_(none yet)_
