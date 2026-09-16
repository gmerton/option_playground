# oquants forward-factor calendars — partial replication (2026-09-16)

Research-queue item #1. **Their claim** (`project_oquants_kb`, flagship post): FF = (front IV − forward IV) / forward IV
computed on **ex-earnings** IV; **FF ≥ 0.20 → long ATM calendar** (or ±35Δ double), hold to the front expiry, close as a
spread, liquidity ≥ 10k contracts/day. They report 19 years, >300k costed spreads, 30/60 · 30/90 · 60/90 all flipping
positive above the cutoff, 60/90 best, ~27% CAGR / Sharpe ~2.4 at quarter Kelly.

FF maps cleanly to our term-structure measure: **FF = 1/fvr − 1**, so FF ≥ 0.20 ⇔ fvr ≤ 0.833 ⇔ **backwardation**
(front IV 20% above the forward). That is the opposite regime from our long-straddle gate (FVR ≥ 1.20).

## What was tested

Everything below uses the **clean** caches built after the path-truncation erratum (settlement at intrinsic on the
expiry close). Front and back ATM IV at entry come from the same chains that priced the trade; the forward is
variance-additive, σ_fwd² = (σ_b²T_b − σ_f²T_f)/(T_b − T_f).

| structure | front / back | cache | truncated | source |
|---|---|---|---|---|
| 12 / 19 d | 12 / 19 | `calendar_path_clean` (30% strike window) | 0.8% | trustworthy |
| 20 / 27 d | 20 / 27 | `calendar_path_clean` | 1.3% | trustworthy |
| 28 / 55 d | ≈ their 30/60 | `calendar_path_long` (12% window) | 9.8% | indicative only |
| 46 / 71 d | ≈ their 30/90 shape | `calendar_path_long` | 20.2% | indicative only |

## Result: the signal does not replicate on index ETFs

| structure | corr(FF, ROC) | FF ≥ 0.20: n | ROC at their gate | ROC below the gate |
|---|---|---|---|---|
| 12 / 19 d double calendar | +0.002 | 128 | **−1.8%** | +1.6% |
| 12 / 19 d single ATM calendar | −0.022 | 141 | **−19.9%** | −2.1% |
| 28 / 55 d calendar | −0.015 | 27 | **−13.3%** | −0.8% |
| 46 / 71 d calendar | −0.015 | 24 | **−2.7%** | +4.8% |

Their gate is negative at all four horizons and the correlation is indistinguishable from zero at every one. The
quintile pattern is non-monotone and **flips sign between adjacent horizons** — the 12/19 top quintile is +23.6% while
the 20/27 top quintile is −15.9% on the same signal and the same names, which is noise, not structure. Halves disagree
inside the gate cell as well (28/55: +8.1 first half, −49.6 second).

This also **retracts the step-7 term-structure finding** from the pre-erratum study, which claimed a flat-or-inverted
front predicted +26% vs +4%. That came from the truncated paths; on clean data the effect is zero.

## Why this is not yet a refutation of their claim

1. **Their population barely exists on ETFs.** FF ≥ 0.20 fires on only **3.5–6.0% of days** (SPY 3.5, QQQ 3.6, IWM 6.0)
   and is clustered in vol spikes — 29 of the 82 hits are in 2020, and 2019 and 2023 have **zero across all three
   names**. On index ETFs "FF ≥ 0.20" is a crash detector, so our n at the gate is 24–141 with few independent episodes.
2. **Their universe is broad liquid single names,** where backwardation is routine rather than exceptional.
3. **Their best structure (60/90) is untested** — our caches stop at 40 DTE (clean) and 85 DTE (12% window).
4. ⚠ **Their FF is computed on ex-earnings IV, and we have no ex-earnings IV construction.** On single names,
   backwardation is usually *caused* by a pending earnings print. A single-name FF test without stripping the earnings
   jump measures "is there an event soon", not their signal — it would be a strawman.

## Recommendation

**Stop here rather than build the rest.** Completing the replication needs (a) a ~95-DTE wide-window pull for a
single-name universe and (b) an ex-earnings IV term-structure model we have never built — not the "one evening" the
queue assumed. Against that cost: the signal is uncorrelated with calendar P&L at every horizon we can price cleanly,
their threshold is negative at all four, and the unconditional calendar family was just shown to have no edge
(`calendar_path_study.md`, clean re-runs). The claim is unrefuted in its own setting but has failed everywhere it
can be tested cheaply.

**If it is revisited,** the order that makes it worth doing is: build the ex-earnings IV model first (it is reusable —
the straddle and VRP work both want it), then pull 95-DTE chains for the 26-name roster, then test 30/60 and 60/90.
Do not test single-name FF without the earnings strip.

Data: `data/cache/calendar_path_long/ff_30_90.parquet` (daily FF on the three ETFs),
`data/cache/calendar_path_clean/ff_joined.parquet` (per-trade FF joined to clean returns),
`results_cal_longstruct_fixed.parquet` (28/55 and 46/71 calendars, corrected settlement).

---

# CLOSED — 2026-09-15

Queue item #1 is closed on Gabe's instruction. The deciding evidence is new and did not
exist when the "stop here" recommendation above was written: the stage-one variance-risk
premium screen (`run_vrp_panel.py`, `data/studies/vrp_panel_study.md`) measures the
**premium a calendar reaches for** directly, without pricing a single calendar.

## What the new measurement adds

Forward implied vol between day 30 and day 90, against the realized vol that then arrives
in exactly that window, on the same 10 ETFs, 2010 to 2026:

```
  fwd 30->90 premium    +1.01 vol points    t_NW 1.45    hurdle 3.29    ABSENT
```

Split by forward vol ratio quartile, which is the same axis as FF (FF = 1/fvr − 1):

| FVR quartile | premium | t_NW |
|--------------|---------|------|
| Q4 (steep)   | +0.99%  | 1.20 |
| Q3           | +0.98%  | 1.39 |
| Q2           | +0.97%  | 1.69 |
| Q1 (flat/inverted, = high FF) | +0.77% | 1.04 |

Flat. The high-FF quartile is the *lowest* of the four, by an amount that is noise.

**This answers the "n is too small" objection that kept the item open.** The tables above
rest on 24,038 ticker-days across 3,511 dates, testing the relationship across the entire
FVR distribution, instead of 24 to 141 trades clustered on a rare threshold. The earlier
work could only say the signal failed to predict calendar P&L where we could price it. This
says the underlying premium is not there and the ratio does not sort it, which is the
stronger and more general null.

## What is still NOT refuted

Caveats 2 and 4 from the recommendation above stand, and closing the item does not retire
them:

- The single-name version is untested. The VRP panel now covers 331 single names, but only
  at 10 and 30 days. A single-name 30→90 forward premium needs a 90-day tenor on that
  universe, which has not been pulled.
- Their FF is computed on **ex-earnings** IV, and we still have no ex-earnings IV
  construction. On single names, backwardation is usually caused by a pending print, so any
  single-name FF test without stripping the earnings jump measures "is there an event soon"
  and would be a strawman.

So the honest verdict is unchanged in kind and stronger in degree: **the claim is unrefuted
in its own setting and has now failed every cheap test we can put to it.** It is closed
because the expected value of continuing is low, not because it has been disproven.

**If it is ever revisited,** the order is still: build the ex-earnings IV model first (the
straddle and VRP work both want it and it is reusable), then add a 90-day tenor to the
single-name VRP panel — which is now a one-line change, `--tenors 10 30 90` on
`run_vrp_panel.py --ticker-file` — and check the premium before pulling a single chain.
That sequence costs an afternoon instead of the multi-day build this item originally carried.
