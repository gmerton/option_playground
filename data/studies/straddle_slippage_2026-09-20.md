# Long straddle entry slippage — measured, not guessed (2026-09-20)

**VERDICT: ADOPTED (confirmed) · MECHANISM.** The strategy survives realistic fills. This replaces
the playbook's parameterised guess with a measurement on real quotes, and the guess turns out to
have been close.

**Why it mattered.** Every number in `long_straddle_playbook.md` prices at mid with zero slippage,
and the doc says so: *"Entry costs are not modelled anywhere in this document. Sensitivity: −0.95pp
per 1% paid over mid."* The queue called this **the single largest remaining unknown in the book's
best strategy**, and today's event-spread study showed exactly this failure mode elsewhere — a
0.12Δ-over-0.25Δ preference worth +19.5pp at mid collapsed to +1.9pp at realistic fills.

**Method.** `run_straddle_slippage.py`. Real `bid`/`ask` for **both legs of all 41,757 gated entries**
pulled from `options_daily_v3` via the temp-Glue-table join. **Both legs quoted on 41,746 — 100.0%
coverage**, so there is no survivorship from missing quotes. Gates and folds are *imported* from
`run_straddle_rebuild_wf` so they cannot drift. Cost is **one-sided**: the position settles at expiry,
so you only cross on the way in. Fill `f`: entry = mid + f × (ask − mid).

## The measured spread

**Median 6.5% of mid, mean 8.4%, p90 17.6%.** That is what a 7-DTE straddle actually costs to cross.

## Arm 4 (full pool + both gates), folds 2021–25, 4,573 trades

| f | % over mid | mean (no stop) | **mean (−50% stop)** | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| 0.00 | 0.0 | +8.77 | **+15.46** | 14.97 | 18.02 | 15.25 | 13.19 | 18.88 |
| 0.25 | 1.1 | +7.74 | +14.50 | 13.92 | 16.85 | 14.49 | 12.27 | 17.67 |
| **0.50** | **2.2** | **+6.73** | **+13.57** | 12.91 | 15.72 | 13.76 | 11.39 | 16.50 |
| 1.00 | 4.4 | +4.79 | +11.78 | 10.98 | 13.60 | 12.34 | 9.69 | 14.28 |

**Measured sensitivity: −0.86pp of ROC per 1% paid over mid**, against the playbook's guessed −0.95.
The guess was good; it is now a measurement.

**The strategy survives.** At a realistic half-spread fill (f=0.5, 2.2% over mid) arm 4 is **+13.57%**,
a **−1.90pp** haircut. Even paying the **full ask** it is +11.78%. **Every fold is positive at every
fill level** — the worst cell in the table is 2024 at the full ask, +9.69%.

**Assumption-free floor: +6.73%** (f=0.5, no stop clip). The −50% stop remains an assumption rather
than a path simulation — it is still the other, larger half of the uncertainty, and it is still
un-measured.

## ⚠ The playbook's numbers do not reproduce

`long_straddle_playbook.md` states arm 4 = **+12.61%** (stop) / **+5.76%** (no stop). Neither figure
comes back from the current code and data on any natural population:

| population | stop −50% | no stop |
|---|---|---|
| all years pooled | +14.80% | +8.06% |
| folds 2021–25 pooled | +15.46% | +8.77% |
| folds 2021–25 fold-mean | **+16.06%** | — |

My f=0 row reproduces `run_straddle_rebuild_wf`'s arm 4 **exactly** (14.97 / 18.02 / 15.25 / 13.19 /
18.88 → +16.06), so the pipeline is faithful; it is the **document** that is out of step with the code.
Most likely it predates the August data refresh. **The doc's figures should not be quoted until
reconciled.** The slippage sensitivity is baseline-independent, so the −0.86pp/1% result stands either
way — apply it to whichever baseline survives the reconciliation.

## What changes

- The straddle stays in the book, and the pair stays the unit. The mid-pricing caveat that has sat on
  every straddle number since August is **discharged**.
- Budget **−1 to −2pp** for entry costs at a realistic fill, not the previously-guessed 1–3pp.
- Two open items, in order: **reconcile the playbook doc against the code**, then **the −50% stop**,
  which is now the largest remaining assumption in the strategy and needs daily contract marks.
