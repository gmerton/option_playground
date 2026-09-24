# Deepvue — "How I Find Early Breakouts - The RMV Indicator in Deepvue" (Richard, 2026-03-06, 18 min)

_Reviewed 2026-09-23. A solo platform tutorial: set up the proprietary RMV ("Relative Measured Volatility")
indicator, walk three winners (PL, GLW, BE), sort Deepvue's leader screen by RMV, then build a scan. Transcript
(`en-orig` auto-captions, "R&V"/"RMD" = RMV) in this folder._

⚠ **This is vendor content.** Deepvue sells the charting/screening platform, the description opens with an
80%-off referral code, and RMV is "proprietary to the DV platform" [00:10]. The video is a feature demo. No
performance figure of any kind is claimed, so there is no record to audit. The formula is not disclosed.

## Verdict: 2 / 5

Better than most in this genre, because it claims little and is candid about the limits:
- he says out loud that contraction does not predict direction [05:29–06:20];
- he says you still need a stop and position awareness;
- he offers the short-side mirror [06:30].

What's missing is evidence. Every example is a winner that is still on the chart: PL, GLW, BE and the scan list.
The one expansion that went the wrong way (PL, [05:40]) is shown as "then it closed strong". There's no
denominator, no hit rate and no comparison against untight breakouts. The **idea is testable, though, and
not already in our ledger** (see "Not tested, could be"): it's a fast, own-relative compression gate on the
breakout. That's a different object from the slow VCP geometry that tested NULL today.

## What RMV is — reverse-engineered from what the transcript allows

What the transcript pins down:

| @ | statement | implication for the formula |
|---|---|---|
| 02:13–02:27 | "oscillates between 100 and zero. Zero = very tight relative to recent price action, 100 = expansion" | bounded 0–100, own-relative |
| 02:36–02:44 | earnings gap day reads "right at 100, which means it's the **maximum expansion over the lookback period, which by default is 15 days**" | 100 = the lookback MAX of some volatility measure → a **min-max (stochastic) normalisation**, not a percentile or a z-score |
| 02:48–02:54 | the tight range just before went "right back down to zero" | 0 = the lookback MIN |
| 08:21–08:47 | after a gap-up "the extreme volatility is going to **skew** that reading for quite some time until it is no longer part of the lookback", so switch to **RMV5** | the gap bar sits in the normaliser's max. With min-max scaling, one huge bar crushes every later reading towards 0. A percentile rank would barely notice one bar. **Confirms min-max over percentile.** The lookback is a user parameter (RMV5 / RMV10 / RMV15) |
| 10:11–10:15 | "all of this is tight and all of this is RMV basically equals zero" (several consecutive days) | repeated zeros need the inner measure to keep making new 15-day lows, which is easiest if it's a **smoothed, multi-bar** range rather than a single bar's range |
| 01:32–02:02 | he highlights 0–10 (sometimes ≤15) as "very tight" | the working threshold is **RMV ≤ 10** |
| 16:23 | screen field is "relative measured volatility **15 days**" | default L = 15 |

**Codable reconstruction (the parts marked ? are my choice; the transcript doesn't disclose them):**

```
TR3_t   = max(H[t-2..t], C[t-3]) - min(L[t-2..t], C[t-3])      # ? 3-bar true range (gap-aware: the gap day reads 100)
v_t     = TR3_t / C_t                                           # scale-free
RMV_L,t = 100 * (v_t - min(v[t-L+1..t])) / (max(v[t-L+1..t]) - min(v[t-L+1..t]))   # L = 15 default, 5 after gaps
tight_t = RMV_L,t <= 10
```

The normalisation (min-max over L bars, 0–100) is well supported. The inner measure is a guess.
Plausible alternatives are the 1-bar true range, ATR(3)/C, or an average of 1-, 2- and 3-bar ranges.
Community clones of "RMV" on TradingView differ on exactly this point, and none is verified against Deepvue.
Any test has to pre-register one inner measure and show the others as a neighbourhood.

**What RMV is, in our vocabulary:** a continuous **NR-N / "tightest in 15 days"** flag. It's own-relative
over three weeks, so it's scale-free and ADR-neutral by construction.

## How it differs from what we already have

| | RMV | `src/lib/commons/vol_compression.py` | VCP damped sine (`vcp_damped_sine_2026-09-23.md`) |
|---|---|---|---|
| horizon | **5–15 bars** | 252-day ATR% percentile, ATR14 vs ATR50, 20d ATR trend, 5<20<60 range chain | swing geometry over ≤ 65 sessions |
| question asked | is the last few bars' range the smallest of the last 3 weeks? | is volatility low for the *year* and falling? | do successive swings shrink? |
| normalisation | min-max over L bars | percentile over 252 | none (depth ratios) |
| status | untested | **indicator with no study behind it** (TEST_INDEX §10 VCP row) | **NULL**: −0.37pp vs same-date other-name breakouts, t −0.70; held-the-level 13.7% vs 13.3% |

So RMV is a **different claim from the VCP null**. VCP asked whether the *base's shape* improves the breakout.
RMV asks whether *the last few bars before the trigger being unusually narrow* does. The first answer doesn't
settle the second. It does lower the prior, since both come from the same "contraction precedes expansion" family.

## Claim by claim against our ledger

| @ | claim | our evidence |
|---|---|---|
| 00:30 | "From contraction comes expansion" | **Plausible as a volatility statement, and not a direction claim.** Vol clustering is well established. Our GEX work finds realised vol is forecastable (negative gamma +8% RV beyond VIX, t 7.7). But what a breakout trader needs is *direction* after contraction, and he concedes RMV doesn't give it [05:29] |
| 00:43, 04:51–05:26 | Tight areas matter most "up the right side of a constructive base" or after an earnings gap, with confluence at the 10/21 EMA ("the best possible scenario") | **Mostly already tested, and against him.** Earnings-gap follow-through: PEAD **NULL**, catalyst-day buy −0.173R (t −4.70), DR-EP post-catalyst retrace −0.067R (t 0.21). EMA-proximity: pullback entries on leaders came in **below** the breakout (+1.2–2.4%, t ≤ 1.4); within-date composite "near 21 EMA + high rvol" **t −0.11**. Distance to the 21 EMA is the *best* hold predictor we found, and it's still worth only +0.057R of a 1.647R spread (TEST_INDEX §4, 2026-09-20 qualifier) |
| 03:50–04:28 | When RMV ≈ 0, draw the "RMV pivot" at the lined-up recent highs and buy the range breakout | **The trigger is the house breakout at a shorter lookback.** The house breakout (close > prior 20d high) is bimodal: 23.6% never retest (+1.27R), 76.4% do (−0.37R), and the split **is not callable at entry** with the 9 features tried. **Pre-breakout compression wasn't one of the 9** (`run_breakout_hold_predictors.py` feature list). That's the untested gap |
| 04:36–04:46 | Undercut-and-rally of the 10 EMA as an alternative entry | Qullamaggie himself couldn't define the undercut & rally (Qullamaggie KB, 2020-07-02). Intraday reclaim entries lose to the close (RECLAIM −2.28pp, t −3.4, entry study) |
| 05:29–06:20 | Contraction ≠ upside expansion; always have a stop; don't anticipate | ✅ **Correct and honest.** It's the most useful sentence in the video |
| 06:30–06:47 | Mirror: a tight range just below a declining 50 SMA is a short setup | **Low prior.** 0 for 10 on short universes. Pullback-short arrival signal is negative EV |
| 07:41–07:50 | A broken range "often flips to support" on a retest; buy the retest if you missed it | **PARKED.** Our retrace entry beats the breakout in all 6 cells but t 0.48 (retrace_entry_2026-09-20). OptionsPlay's add-on-retest variant is queued (§9). Note the survivorship: the retests he shows are the ones that held |
| 08:21–08:56 | Use RMV5 after gaps / IPOs because the gap skews RMV15 | **A real property of the formula** (see reconstruction). It's also a parameter the viewer picks per chart after seeing it, which is look-ahead if backtested that way. A test has to fix L in advance |
| 09:41–09:48 | "It's amazing how we see expansion after RMV5/10/15 goes to zero" | **Selection by example.** Three hand-picked winners. No base rate: how often does RMV ≤ 10 precede a *down* expansion, or no expansion? |
| 11:13–11:25 | Screen: momentum / AS rating > 90 and RMV < 10 | Momentum-universe selection is where our return actually lives (universe test: HYB-B +1.79, t 2.6 PARKED; TT weakest). RMV would be a gate *inside* that universe. It's testable |
| 13:05–13:09 | "Pair a strong stock with a strong setup, then look for an RMV-zero tight range" | Consistent with our "selection carries the return, the trigger adds ≈ 0" (universe test: edge vs same-name later day ≈ 0 in every universe) |
| 16:03–17:35 | Scan: RMV15 in 0–10, $ volume 20d > $40M, 3-month AS rating > 90; optionally within a few ADR of the 21 EMA | **Codable end to end** (spec below), except that "AS rating" is proprietary. Proxy: 63-day return percentile ≥ 90 in the liquid panel |

## What I would take

1. **The formula family and the threshold**: min-max over 15 bars, ≤ 10 = tight. It's cheap to compute, ADR-neutral
   by construction, and gives the scorecard a continuous "tightness" number where it currently has none.
2. **His caveat [05:29]:** contraction predicts *size* of move, not direction. Any use has to be as a *gate on a
   directional trigger we already have*, never a trigger itself.
3. Nothing to adopt yet.

## Not tested, could be

### ⭐ RMV as a compression gate on the house breakout (pre-registerable)

**Why it's worth one run despite the VCP null.** It's a different horizon (3–15 bars, not swing geometry).
It's a different normalisation (own-relative, ADR-neutral). And it's the one pre-trigger variable never put against
the bimodal hold/fail target. The prior is low-moderate: VCP NULL, 0 of 9 hold predictors callable, 71 of 72
within-date ranking cells null.

**Spec (write it into the script docstring before running):**
- **Panel / universe:** the VCP study's (`lib.studies.pattern_test.load_panel`, liquid-eligible), 2019-10 → 2026-09.
- **Trigger:** the house breakout (`run_vcp_damped_sine.house_breakout`: close > prior 20d high, ADR20 ≥ 3%,
  eligible), entered at the close.
- **RMV:** the reconstruction above. Inner measure = 3-bar true range / close, **L = 15** (fixed, no per-chart
  switching), computed on bars strictly before the trigger day.
- **Gate (PRIMARY):** `min(RMV15[t-3..t-1]) ≤ 10`, i.e. tight in at least one of the 3 sessions before the breakout.
  The breakout day itself is expansion by construction and is excluded.
- **Exit (identical for both arms):** stop = the breakout day's low **judged on the close** (the house tight stop),
  then the 20-EMA close trail, max 60 sessions, 0.10% slippage per side. **Metric = % return per trade**, not R,
  because tight-range breakouts will have systematically narrower stops and R would flatter them (the ORB9 lesson).
  R is reported second, with the 2% stop floor and cap 20.
- **Control (PRIMARY): date-matched cross-name.** On each date that has ≥ 1 gated and ≥ 1 ungated house breakout:
  diff_d = mean(gated %) − mean(ungated %), where the ungated breakouts are **other names on the same date**.
  t is clustered by date. ⚠ Not a same-name ±N window: that control retracted the VCP pass.
  Secondary controls: the same, ADR-tercile-matched within the date; `pattern_test` `xname` and `post` rows for the ledger.
- **Must also show:** a higher **held-the-level share** (low never touches the breakout level within 20 sessions)
  than same-date ungated breakouts, i.e. it has to make the good cohort of the bimodal book callable.
- **Confound check (pre-declared):** report the gated-minus-ungated gap in `ext_above_level_ADR` and stop/ADR.
  If the gate only selects less-extended entries, the finding is the entry-extension result again, not RMV.
  Re-run the primary within extension terciles.
- **Bar:** |t| ≥ 3 on the primary diff, both halves (split 2023-01-01) the same sign, per-year table
  (a 2023+ regime can hide inside the halves; see the precision-tier freeze-forward).
- **Multiple testing:** the primary is the one registered look. Exploratory cells are RMV5; thresholds ≤ 5 / ≤ 15;
  the inner-measure variants (1-bar TR, ATR3); Brandt's ADX(14) ≤ 12 (Chat With Traders review, same day); and
  `vol_compression.is_compressing` on the same trigger. Those ~8 cells are judged at Šidák k = 8 (|t| ≈ 2.9)
  and carry no verdict of their own.
- **Effort: ~2–3 hours.** RMV is ~10 vectorised lines. Panel, breakout mask, `pct_trade`, `tstat` and the
  date-matched pairing are already in `run_vcp_damped_sine.py` / `_diag.py`. It's quiet mode: log to
  `data/studies/logs/rmv_gate.log`.
- **⭐ The "clean result is a bug" check to run first if it passes:** make sure the gate uses no bar ≥ t (the
  min-max window must end at t−1). Then check that the gated arm isn't just lower-ADR-in-the-moment names with
  tighter stops (the % metric guards this, and the ADR-matched secondary checks it).
