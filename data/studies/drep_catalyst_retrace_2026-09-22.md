# DR-EP: does a catalyst gate improve the retrace entry? — 2026-09-22

**Verdict: NULL. The catalyst gate adds nothing — it makes the retrace entry slightly WORSE.**
Pre-registered in the docstring of `run_drep_catalyst_retrace.py` before the run. This answers the
post-catalyst-entry half of catalyst-queue #1.

## The setup

Two results pointed at the same design from opposite directions:
- `retrace_entry_2026-09-20`: deferring entry until price retraces beat the breakout close in **all 6
  cells** (edge −0.101 → +0.065, both halves positive) but landed at **t 0.48 → PARKED**. It had **no
  catalyst gate**.
- Bonde's "delayed reaction EP" ([[project_traderlion_kb]], reviewed today): after a catalyst he refuses
  to chase, waits for an orderly pullback, and enters on the resumption within ~25 sessions.

So the **catalyst gate is the new variable** — exactly what catalyst-queue #1 specifies.

**Catalyst day (mechanical proxy):** gap ≥ 3% AND RVOL ≥ 1.8 AND ADR ≥ 3 AND eligible.
**DR-EP entry:** after the catalyst day, require (i) at least one close *below* the catalyst close, then
(ii) the first close *above* the highest high since the catalyst day, within 25 sessions. If it never
gives back there is no entry — faithful to Bonde ("sometimes it just goes straight and never gives you a
DR entry"). Entry at that close, stop = that day's low. Liquid panel, 2019-10 → 2026-09, house fills.

7,149 catalyst days → **only 38.4% ever gave back and then resumed** within 25 sessions.

## Results (ema20 arm, the house trail; day-clustered t)

| arm | n | meanR | t | half1 | half2 | vs `post` | vs `xname` |
|---|---|---|---|---|---|---|---|
| **A** catalyst-day close ("buy the event") | 6,815 | **−0.173** | −4.70 | −0.350 | −0.070 | −0.047 | −0.075 |
| **B** DR-EP (catalyst + retrace) | 2,702 | **−0.067** | 0.21 | **−0.193** | +0.012 | **−0.061** | −0.009 |
| **D** retrace, **no** catalyst gate | 16,887 | **−0.057** | −1.01 | −0.277 | +0.095 | −0.048 | +0.050 |
| B + Bonde's 9M absolute-volume floor | 1,459 | −0.025 | −0.01 | −0.185 | +0.064 | −0.015 | — |

**Primary (B vs its `post` control): FAIL.** Edge −0.061, |t| 0.21, first half negative. Three of the
four pass conditions missed.

## What it establishes

1. **Buying the catalyst day is decisively bad** — arm A is −0.173R at t −4.70, negative in both halves,
   and loses to *both* controls. This independently reproduces the PEAD null and the "buying the event
   fails" line in [[project_catalyst_studies]] — and **Bonde agrees with it himself** ("I don't chase
   gaps now… I'm done chasing that").
2. **Deferring the entry genuinely helps: A → B is +0.106R.** The direction of the PARKED retrace result
   replicates, now on a catalyst-selected pool. But it only rescues a bad entry to a **less bad** one; it
   never reaches positive, and it still loses to a random later day in the same name.
3. ⭐ **The catalyst gate contributes nothing. B (−0.067) is slightly WORSE than D (−0.057)** — the same
   retrace rule with no catalyst requirement at all, on 6× the sample. The new variable failed.
4. **Bonde's 9M absolute-volume floor adds nothing**, exactly as pre-registered — our diagnostic had
   already shown 59.2% of its firings come from names whose median volume already exceeds 9M.

## Why — the same structure as before

Only **38.4%** of catalyst days ever give back and resume. By construction the retrace rule buys the
cohort that *faltered*; the ones that run away and never come back are unbuyable by this rule. That is
[[project_entry_extension_finding]]'s bimodality verbatim — *"the retrace rule only rescues the failing
76% to ~flat; it never touches the +1.27R cohort because those never come back to be bought."* Adding a
catalyst filter does not change which cohort the rule can reach.

⚠ **Fair limit on the claim.** Bonde's DR-EP is *discretionary*: he researches whether the catalyst is
genuinely game-changing, classifies turnarounds, and watches 3–4 names for a sub-1% stop. Our proxy
(gap ≥ 3% + RVOL ≥ 1.8) cannot express "is this a real catalyst." **This is a fair test of the
mechanisable version — the only version we could deploy — not a refutation of his practice.**
The untested residual is his *catalyst taxonomy* (genuine multi-quarter turnaround vs cyclical vs
one-quarter beat), which is the one part of the video we have no analogue for and which he insists is
the whole discrimination.

## How to apply

- **Close the post-catalyst-entry half of catalyst-queue #1.** Mechanical catalyst gating + retrace entry
  does not work. Do not build a DR-EP screener.
- Keep the standing conclusion: signals mark **states, not moments**, and the retrace family cannot reach
  the cohort that pays.
- The live residual worth pursuing is **catalyst classification**, not catalyst *timing*. The earnings
  ledger came back NULL treating every print alike; Bonde's taxonomy is the first concrete proposal for
  splitting them, and it is untested here.

Script `run_drep_catalyst_retrace.py`. Ledger rows: arms A, B, D (`post` controls).
Related: [[project_catalyst_queue]], [[project_catalyst_studies]], [[project_entry_extension_finding]],
[[project_earnings_2026_09_20]], [[project_traderlion_kb]].
