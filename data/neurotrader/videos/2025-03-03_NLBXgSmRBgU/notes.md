# neurotrader: "How I Develop Trading Strategies | Permutation Tests and Trading Strategy Development with Python" (2025-03-03, 22 min)

_Reviewed 2026-09-23. A method video: solo screen share with code (github.com/neurotrader888/mcpt). Worked example is a
Donchian breakout with an optimised lookback on hourly BTC 2016–2019, plus a deliberately overfit decision tree.
Source: Timothy Masters, *Permutation and Randomization Tests for Trading System Development*. Transcript
(`en-orig` auto-captions) in this folder._

## Verdict: 3.5 / 5 (as METHOD). No strategy claim to test.

He sells no strategy, and he rejects his own example on camera: walk-forward p = 22%, "I would not trade it". What he
teaches is a correct and useful idea we have **only partly adopted**: **the null must include the optimiser.** When you
pick the best of k parameter settings, the null distribution is "the best of k on noise", not "one run on noise". He
builds that null by re-running the *whole* search on each permuted price series. We charge for search with Šidák
arithmetic (`multiple_testing_correction_2026-09-22.md`, `k` estimated "from the row text"). His approach measures the
search's own data-mining power instead of guessing `k`, and correlated parameter cells are handled automatically.

Points off:
- His null (shuffle bar returns) is **the wrong null for most of our questions.** It tests "is there any structure the
  optimiser can exploit". Ours are "does this beat a same-name later entry / another name on the same day". See Critique.
- No costs appear anywhere.
- The "quasi p-value" is read as P(result is due to data-mining bias), which it is not.
- n = one market, one strategy family.

YIELD: **METHOD.**

## The method as he describes it

| step | what | his statistic / numbers |
|---|---|---|
| 1. In-sample excellence | Optimise on the development window (grid over lookback, pick max profit factor). Ask "is it excellent?" and "is it obviously overfit?" (100% win rate → leak or overfit) | Donchian best lookback 19, PF 1.08 on BTC 1h 2016–19 |
| 2. In-sample Monte Carlo permutation test (IS-MCPT) | Permute the bars, **re-optimise on each permutation**, and count permutations whose *optimised* PF ≥ the real optimised PF | 1,000 perms (hard floor 100); p = (count ≥ real)/N = **0.3%** → pass; his bar is p < 1%. The overfit tree fails (perms do as well) |
| 3. Walk-forward | Re-optimise on a trailing 4-yr window every 30 days, trade the next slice | 2020 PF 1.04 |
| 4. Walk-forward MCPT | Permute **only the bars after the first training fold** (`start_index`), re-run the whole walk-forward, compare PF | 200 perms; **p = 22%** → fail. Tolerates p ≈ 5% on one year of OOS, requires < 1% on ≥ 2 years |

**Permutation algorithm (07:00–09:20).** Work in log prices. Break each bar into its intrabar shape (H, L, C relative to
its own open) and its gap (open minus previous close). Shuffle the two sets **independently**, then chain them back into
a path. The first open and last close are unchanged, so net drift is preserved. So is the marginal distribution of
returns: mean, sd, skew and kurtosis are all "nearly identical". For several markets, one shared index shuffle keeps the
cross-correlation. ⚠ **He says himself (09:47)** that this destroys volatility clustering and long memory, so the test is
"optimistically biased" for strategies that rely on those properties.

**Objective at bar granularity (01:04–01:30).** Position vector × next-bar log return gives a return on every bar, and PF
or Sharpe is computed on those instead of on per-trade returns. Masters's argument: more observations make the statistic
more stable.

**Why not just use OOS (13:57–15:35).** Every look at the holdout adds selection bias across ideas ("strategy B beat A on
2020" is contaminated). The IS-MCPT kills bad ideas *before* they spend the holdout.

**Closing heuristic (20:20).** Optimised lookbacks rarely generalise. Find a lookback where "a large variety of lookbacks
have decent performance", fix it, and move on. That is the parameter-plateau rule.

## Claim by claim against our practice

Harness facts below are checked in `src/lib/studies/pattern_test.py` (read 2026-09-23), not taken from memory.

| @ | Claim | How we compare |
|---|---|---|
| 01:04 | Compute the objective on per-bar strategy returns, not per trade | **Different unit, and ours is the right one for us.** `_stats()` averages R **per signal date** and takes t over dates (`d = s.groupby(date).mean()`), because our signals cluster by date. Per-bar returns would inflate n exactly the way our effective-n rule forbids (3,377 spreads = 53 dates). Per-bar returns suit one always-in-market series, not event entries across 1,700 names |
| 02:05 | Grid-search the lookback, keep the best PF | **We do this too, and charge for it only loosely.** `_report()` picks `best = tab.edge.idxmax()` across 5 daily arms (6 intraday) and then applies the unadjusted \|t\| ≥ 3. That is best-of-5 with no in-harness charge. The ledger-wide pass charges k by Šidák, with k judged from prose. `ledger=False` "for parameter sweeps" keeps the ledger count honest but records nothing about the size of the sweep |
| 04:30 | Null hypothesis = "the strategy is garbage". Optimised real ≫ optimised-on-noise → reject | ✅ **Right concept, not implemented here.** None of our controls re-runs a selection step. `control="post"` / `"xname"` / intraday random-minute are **one draw of the unoptimised rule** (3 controls per signal, `RNG` seeded 20260918). Closest prior art: `run_stack_slack_walkforward.py` (500-draw placebo that permutes run-length *within month*) and `run_rsi_straddle_walkforward.py` (5,000 within-week RSI permutations). ⚠ **Both permute at the already-chosen cutoff**, so neither is optimisation-aware |
| 05:17 | A bar permutation removes "any legitimate patterns" but keeps the statistical properties | **Only the marginal properties.** He concedes vol clustering and long memory are lost (09:47). For us that is not a minor footnote. The straddle/VRP book, the GEX regime result (+8% RV beyond VIX, t 7.7) and every ADR-scaled stop *are* volatility-clustering effects. See Critique §1 |
| 07:40 | Shuffle intrabar and gap components separately; gaps matter on daily stocks | **Correct detail, and relevant to us.** The DR-EP / catalyst work shows gaps carry our strongest single-day information (catalyst-day buy t −4.70). A shuffle that decouples gaps from the next bar's range is a strong null there. Fine for crypto, deliberate for stocks |
| 09:05 | First open and last close are preserved, so the trend is preserved | **This is the control that matters, and it is weaker than ours.** Preserving drift means a long-biased rule is not rewarded for beta. But it matches only *total* drift over the window, not the timing of drift. Our `post` control holds the name and the next 20 sessions fixed. `xname` holds the date fixed. Both are tighter than "same endpoints" |
| 11:07 | Quasi-p = share of perms ≥ real. "Roughly the probability the result was found mainly from data-mining bias" | ⚠ **Misstated.** It is P(stat ≥ observed \| null of no exploitable structure, *given this optimiser*). It is not P(null \| data). Also use (count+1)/(N+1): with 1,000 perms and 0 exceedances, p < 0.001, not p = 0 |
| 11:50 | Bar: p < 1% in-sample. Walk-forward: ≤ 5% on 1 year, < 1% on ≥ 2 years | **Comparable to ours in-sample** (\|t\| ≥ 3 ≈ p 0.0027 two-sided). But his is a *single* test with no family charge across ideas. Our BH/Šidák over M = 125–400 is stricter. His "p < 1% each, both tests" rule ≈ our "\|t\| ≥ 3 + both halves", in spirit |
| 13:02 | ≥ 1,000 permutations, 100 as a hard floor | **Right order of magnitude.** The resolution needed to certify p ≈ 0.0027 (our \|t\| 3 bar) needs ~2,000+ perms for a stable tail; at M = 125 BH the rank-1 line is 0.0004 → **≥ 5,000**. Cost is the issue (see effort) |
| 13:37 | "A measure that becomes a target is no longer a good measure": fiddle enough and anything passes | ✅ **Agrees** with our pre-registration rule and the ledger multiple-testing header. The permutation p inherits the garden of forking paths between runs. Only the ledger counts those |
| 14:05 | Once OOS is looked at, it becomes validation data. Selection across strategies inflates the winner | ✅ **Agrees exactly** with the forward-lockbox item (method queue #5) and the AI Pathways "OOS used for selection so nothing is sealed" critique. Our chronological split (`split="2023-01-01"` daily, `"2026-06-01"` intraday) is **reused on every pattern**, so by his definition our back half is validation data, not OOS. The halves rule is a consistency check, not an OOS test, and we should say so |
| 15:45 | Walk-forward re-optimisation every 30 days on a trailing 4-yr window | **We rarely re-optimise.** Most rules are fixed parameters with a single split. The RSI straddle gate and MA-stack slack use one train/test split, not a rolling one. For fixed-parameter pattern tests, walk-forward adds nothing. It matters only for rules we tuned (HYB-B ADR/ADDV cutoffs, IV-pctile gate, slack) |
| 17:25 | Walk-forward MCPT: permute only post-training bars and re-run the WF | **A clean test we have no equivalent of.** It answers "could a worthless rule, re-tuned the same way, make this OOS number". Relevant only to tuned rules (above) |
| 20:20 | Optimised lookbacks rarely generalise. Pick one inside a broad region where many values work, then stop tuning | ✅ **This is method-queue #2 (parameter-neighbourhood robustness) in his words.** We have one done instance: the straddle IV gate plateau (≤10…≤60 → +8.9…+5.8, clean dose-response), and cw_play's top-9…50% plateau |

## Critique: where his scheme is wrong or insufficient for us

1. **Bar-return permutation destroys volatility clustering, so it is the wrong null for anything vol-scaled.** He admits
   the test is "optimistically biased" for vol-dependent strategies and waves it off ("if it can't pass even so, it's
   overfit"). That covers only one direction. In our book **the bias also runs against true positives.** Our stops and
   targets are in ADR units and our R is stop-relative. Shuffling bars puts a calm bar after a wide one, so R
   distributions on permuted data get *fatter tails in both directions*. The null's max-over-k widens, and a real
   modest edge is harder to see. Either way, the null's shape is set by what the permutation broke, not by what we want
   to exclude. **Fix: a block (stationary) bootstrap of bars or returns with block ≈ 10–20 sessions.** It keeps vol
   clustering and most short-range autocorrelation. `vrp_stats.block_bootstrap_ci` already implements the
   moving-block bootstrap for means.
2. **Single-series only. Our strategies are cross-sectional.** A daily pattern in `pattern_test` fires across ~1,700
   names on shared dates. Permuting each name independently destroys **cross-sectional correlation**, which is the
   thing that makes 3,377 trades = 53 dates. The permuted null would then have too-small variance and be
   anti-conservative. His multi-market option (one shared index shuffle) fixes it only if every name is permuted with
   the **same date permutation**. That preserves the cross-section but breaks each name's calendar alignment with
   earnings and news, which is fine for a null.
3. **It tests "any structure", not "beats the control".** A rule can clear his null by harvesting momentum, drift
   timing, or vol clustering (on his block-less version, clustering is absent from the null so *any* vol-timing rule
   passes). Our standing lesson is that the question is always relative. The UR band sweep (t 27.8) and ORB9
   (+0.352% gross, but −0.425pp vs a random minute, t −8.50) are the kind of result **a bar-permutation null would
   likely pass (untested here)**: ORB9's +0.352% is real structure (intraday drift/momentum), just not the trigger;
   UR's sample was outcome-selected. **Controls answer the question. Permutation
   answers "how much of the best-of-k is search luck".** We need both, and the permutation should be applied to the
   **edge (signal − control)**, not to the raw stat.
4. **No costs.** PF on gross log returns. Our cost model is the thing that killed nine "good at mid" strategies. A
   permutation p on gross returns certifies nothing tradeable. Permute on net R (the harness already applies 10 bps
   slip per side; option engines use `costs.py`).
5. **Outcome-conditioned samples are immune to it.** If the signal set was selected by an outcome (the UR reclaim
   "guaranteed to succeed"), the look-ahead survives any permutation of the *other* bars. Permutation does not replace
   the "clean result is a bug" check.
6. **Walk-forward MCPT permutes only the future, but the rule's *design* came from looking at the whole sample.** Its
   p is valid only for the tuning the code performs, not for the human search before it. Same limitation as ours; the
   ledger count is the only guard.
7. **Minor.** Profit factor is a ratio with an unstable denominator, which is his own instability complaint. We should
   stay on mean net R and date-clustered t. A studentised statistic (t, not mean) makes permutation p's better behaved
   across arms of different variance.

## Design proposal: a permutation / Monte-Carlo null in `pattern_test.py` (proposal only, no code changed)

**Principle.** Keep the controls as the *question* (post = timing, xname = selection, random minute = trigger). Add a
permutation layer whose only job is to price **the search**: best-of-arms now, best-of-grid later. The statistic is
always the **date-clustered t of per-date edge** (signal R minus the matched control R on that date). ⚠ Today's `_stats`
t is on raw meanR vs zero, and `edge > 0` is a point-estimate check. That gap is worth fixing on its own (item A).

**A. Paired edge t (prerequisite, ~2 h).** Pair each signal with the mean of its own controls (they are already drawn
per signal), and compute t on the per-date mean of `R_signal − R_ctrl`. Pass = this t ≥ 3, not `t(meanR)` plus
`edge > 0`. This makes "beats the control" a significance statement. Re-run the ledger's closest rows (earnings drift
t 2.65, HYB-B) because the labels may move.

**B. Label permutation null for "best of arms" (daily, ~½ day).** Within each signal's **matched stratum** (same name,
the signal session plus its 20 `post` candidates; or the same date for `xname`), randomly swap which session is labelled
"signal" and which is "control". Recompute the edge-t for **every arm** and keep the max. Repeat N = 2,000.
- p_search = (#{max-arm t\* ≥ observed max-arm t} + 1)/(N + 1).
- This is an **exact conditional null** (same machinery as the stack-slack within-month placebo), and it holds the
  cross-section, vol regime and name fixed by construction. **This fixes Critique 1–3 without any price simulation.**
- Cost: the arms for all candidate sessions can be computed once and cached, since the post window already has them.
  Each permutation is then an index shuffle plus a groupby. 2,000 perms ≈ minutes, not hours.
- Intraday: the same, with the random-minute pool of the same name-day. `run_intraday` already iterates that pool.

**C. Block-bootstrap null for "any structure" (optional, ~1 day).** For pattern families where the controls cannot
express the null (always-in-market rules, index timing), do a stationary bootstrap of daily bars with mean block 10–20
sessions. Use **one shared date-index draw across all names** to keep the cross-section. Chain intrabar and gap
components as he does. Re-run `pattern(P)` on the synthetic panel. Use it as a secondary sanity check only; report it,
don't gate on it.

**D. Optimisation-aware permutation = method-queue #2 (~1–1.5 days on top of B).** A new
`run_grid(name, pattern_factory, grid, …)`:
1. Pre-register the grid in the docstring. For HYB-B: ADR 3.5/4/4.5 × ADDV $75/100/150M = 9 cells × 5 arms = 45.
2. Run every cell on real data with `ledger=False` and record the full surface of edge-t by cell and by half.
3. **Plateau metric** (his 20:20 rule, made numeric): the share of cells with edge-t ≥ 2 and both halves positive, and
   the ratio of the median-cell t to the best-cell t. A spike shows as best ≫ median.
4. **Optimisation-aware null:** on each of N label permutations (B's stratum swap, applied jointly to all cells so the
   cells stay correlated as they really are), re-run the *whole* grid and keep the max edge-t. p_opt = share ≥ the
   real max. This replaces the prose-estimated Šidák `k` with the grid's **effective** k, which is smaller than 45
   because neighbouring cells are nearly the same trades. So it is *less* punitive than naive Šidák when cells are
   correlated, and exact rather than guessed.
5. Write **one** ledger row per grid: best cell, median cell, plateau share, p_opt, and n cells.

**Interaction with the bar.** None of this replaces |t| ≥ 3 + halves + ledger BH/Šidák. It sits in between:
- **Within-row search** (arms, grid): charged by permutation (p_search / p_opt) instead of Šidák with a guessed k. The
  row's p entering the ledger-wide BH is p_opt, and `multiple_testing_correction` stops multiplying k for harness rows.
- **Across rows:** BH over M = 125/400 still governs. Permutation does nothing about ideas tried in separate runs.
- **|t| ≥ 3 stays** as the harness's printed bar, but on the paired edge-t (A). A row passes when it has paired edge-t
  ≥ 3, both halves' edge > 0, per-year sign check, **p_opt < 0.003**, and it survives the ledger BH.
- **Halves ≠ OOS** (his 14:05 point). Label the reused 2023 split a consistency check. True OOS is the forward lockbox
  (queue #5) from 2026-09-22.
- **N:** 2,000 for a harness run. Use ≥ 5,000 only when a row is near the BH line (resolution to ~0.0005).

**Effort.** A 2 h + B ½ day + D 1–1.5 days = **~2–2.5 days**, plus re-running the smoke test (gap-down reclaim ≈ −0.07R
should get a large p_search) and a synthetic check: plant a +0.3R effect in one grid cell and confirm p_opt finds it.
Also plant it in *all* cells and confirm the plateau metric reads "plateau". C is optional (+1 day). First use:
HYB-B's pre-registered 9-cell grid, which is method-queue #2 anyway.

## What I would take

1. **The optimiser belongs inside the null.** This is the one genuinely new idea for us. It turns the queued
   "neighbourhood robustness" item from a visual plateau check into a p-value that prices the search.
2. **Permute labels within our matched strata, not price bars.** Same logic, far better null for a cross-sectional,
   vol-scaled book, and cheap because the control candidates already exist.
3. **Fix the harness t to test the edge, not the mean** (item A). Independent of the video and arguably overdue.
4. **Call our reused split what it is**: validation data, not OOS.

## Not taken

- Bar permutation as the primary null (Critique 1–3). Profit factor as the objective. Per-bar returns as the unit.
- His p thresholds as standalone bars. Ours are ledger-corrected.
