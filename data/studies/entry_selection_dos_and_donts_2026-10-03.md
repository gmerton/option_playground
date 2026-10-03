# Entry and selection: what not to do, what helps (2026-10-03)

**What this is.** A compilation of tests already run. No new test, query or data pull went into it. Scope is
equity entries (timing, trigger, price location) and selection (names, gates, filters, regimes, vetoes), long
and short. Option-structure, premium-selling, exit and sizing results are left out unless they reveal an
entry or selection fact.

**Method.** Every item was checked against its primary study doc (or log), not only against its
TEST_INDEX row. Where the two disagree, the primary doc is used and the discrepancy is listed in §5.

**Tiers.** SIGNIFICANT means |t| ≥ 3, or the item passes its own pre-registered corrected bar, with both
chronological halves the same sign. STRONG LEAN means 2 ≤ |t| < 3 with both halves the same sign. Weaker
results are not listed. Items with |t| ≥ 3 that fail a check (no halves reported, t not measured against a
control, sign flips out of time) are in §4 with the reason they were excluded.

**Standing caveats.**
- "Survivor" means the panel holds names that were liquid in 2026. That flatters long selection and hurts shorts.
- The point-in-time S&P test found that survivorship moves the precision tier by about 3.8pp per trade on large caps.
- Intraday results come from one 7-month tape (Feb–Sep 2026) on the curated watchlist, which was chosen with hindsight.

---

## 1. WHAT NOT TO DO

### SIGNIFICANT (8)

| # | rule (don't…) | effect vs CONTROL (what the control varies) | t | n | halves / years | sample, universe | primary doc | how to act |
|---|---|---|---|---|---|---|---|---|
| D1 | **…buy the intraday break of the opening-range high (ORB9).** | +0.351% vs +0.775% for a random minute in the same name-day, 09:45–12:00 window: **−0.425pp**. The control varies only the **entry minute**. Vs a random peer name the gap is −0.687pp (t −6.01). | **−8.50** | 1,411 | −0.440 / −0.407 | Feb–Sep 2026, 153 sessions, curated watchlist (hindsight) | `alert_triggers_2026-09-23.md` §3 | Never use an ORH break as the buy trigger on a name already chosen. ⚠ The random minute enters earlier on average. The doc treats that as the finding itself: waiting for the break costs money. |
| D2 | **…buy the day of a fresh stage-2 / 52-week-high break** (first close above the prior 252-day high after ≥126 sessions without one, SMA50 rising, 126-day return in the top 30%). | −0.48R vs random eligible names on the same date with the same stop %: **−0.489R**. The control varies the **name**. Waiting for the first 50-day touch recovers about 0.37R, which only gets back to roughly random. | **−6.29** | 1,804 | −0.49 / −0.49 | 2010–26, `liquid_panel_2009` (survivor) | `haber_launchpad_pullback_2026-09-29.md` | Don't buy the breakout day of a fresh 52-week high. ⚠ This cell was reported as a secondary and was **not pre-registered**. Results are in R, but the control uses the same stop %, so the denominators match. |
| D3 | **…buy the generic house breakout on large caps.** | −0.87pp per trade vs 3 random **same-date S&P members** (the control varies the name). | **−3.71** | 2,391 | both halves negative | 2010-01 → 2025-04, **point-in-time S&P 500** including removed names (survivorship-free) | `breakout_pit_certify_2026-09-30.md` | On large caps, a plain breakout does worse than a random member. Neither the tier (−0.73pp, t −1.20) nor the generic breakout beats random. Treat breakout membership as no reason to buy. |
| D4 | **…rank near-high names up because they "held up" on index down days** (down-day RS, dose ≥2 in the prior 20 sessions). | 63-day return +3.99% vs +7.50% for undosed breakouts that are also within 15% of the 52-week high, on the same date: **−3.51pp**. The control holds 52-week proximity fixed and varies only the down-day behaviour. Extension was identical (+2.69 vs +2.66 ADR). | **−3.33** | 2,796 vs 17,151 | −2.81 / −4.33 | 2019–26, 1,725 names (survivor) | `downday_rs_selection_2026-09-23.md` | Don't use "held up in the correction" as a positive filter. It clears Šidák-16 (2.96) in the negative direction, with a monotone dose-response (dose ≥1: −0.92pp). It is relative, not an absolute short. |
| D5 | **…short a fresh 15-close low in a downtrend** (SMA10<20<50, mirror of the house breakout; stop is the larger of the prior close or +2%, 20-EMA exit). | Absolute −1.90% per trade. Vs 3 random same-date, same-ADR-tercile shorts run with the **same exit**: **−0.71pp**. The control varies the name. | **−7.02** | 28,648 | −0.89 / −0.62; 1/16 yrs + | 2010-06 → 2025-11, chain_spot incl. delisted (survivorship-free) | `breakdown_survivorship_2026-09-29.md` | Don't short fresh lows. Fresh lows bounce more than random names. ⚠ The reversal-long follow-up attributes much of the t to the tight-stop exit, but the control used the same exit, so the rule as traded loses. |
| D6 | **…short the intraday failed-breakout (FBO) trigger.** | −0.156pp vs a random minute in the same name-day with the same stop width. The control varies the **minute**. Breitstein's literal "lower high + support break" sequence is −0.185pp (t −4.14). That cell was redefined after a disclosed n=0 bug and was not seen before the fix. | **−4.04** | 3,175 | −0.16 / −0.15 | Feb–Sep 2026, curated watchlist | `fbo_lower_high_gate_2026-09-30.md` | FBO stays retired as a short entry. The lower-high gate halves the damage but creates no edge (primary −0.082pp, t −2.25). |
| D7 | **…replace 12-1 momentum with 52-week-high proximity for selection.** | Top decile by proximity to the 52-week high vs the 12-1 decile: **−0.83pp/mo**. The control varies the **ranking rule**. Proximity alone vs EW is −0.16pp (t −0.82): the replication fails. | **−3.24** (NW) | ~180 months | −0.43 / −1.16; 2/16 yrs + | 2011–26, chain_spot incl. delisted | `momentum_52wk_sue_2026-10-02.md` | Rank on 12-1, not on closeness to the high. Names near the high are the calm ones (63-day vol 22% vs 41%). |
| D8 | **…buy an intraday pullback whose low sits on the AVWAP anchored at the 60-day swing high** (Luk-style tight-stop entries). | −0.48pp vs the trade's own exposure-matched beta × QQQ. The control varies the market exposure. | **−3.20** | 2,396 | −0.42 / −0.54; 2/8 quarters + | 2024-10 → 2026-08, 674 names (survivor) | `luk_avwap_confluence_2026-10-01.md` | Treat the AVWAP from the swing high as overhead supply, not support. It clears the 5-cell Šidák 2.57. ⚠ The primary (any anchor) was NULL (t −0.26), so this is a subgroup of a null population. The gap-day anchor leans the same way (t −2.40). |

### STRONG LEAN (4)

| # | rule (don't…) | effect vs CONTROL | t | n | halves / years | sample, universe | primary doc | how to act |
|---|---|---|---|---|---|---|---|---|
| D9 | **…buy a breakout while the stock is below its 200 SMA** (veto V1). | 20-day ADR-matched same-date excess −1.58pp on the 2010–19 holdout (PRIMARY) and −1.83pp on 2019–26 (t −2.76, halves −2.32/−1.18). About −3pp at 60 days in both periods. Has no effect on the panel as a whole; it applies to breakouts only. | **−2.23** | 8–9% of breakouts vetoed | −2.88 / −0.60; 7/10 yrs − | `liquid_panel_2009` (survivor, which flatters the vetoed side) | `veto_ttest_2026-09-28.md` | A hard veto at the screen. It is consistent in two independent periods. V2 (6-month return < −10%) is NULL out of time; drop it. |
| D10 | **…short a sector/industry ETF breakdown** (close below the prior 20-day low). | −0.156R vs random other ETFs on the same date with the same stop %. Absolute −0.473R. | **−2.64** | 807 | −0.11 / −0.19 | 31 ETFs, 2010–26 | `etf_breakouts_breakdowns_2026-09-29.md` | Breakdown shorts are 0 for 10 across stocks, dead names and ETFs. |
| D11 | **…dilute the 12-1 rank with earnings momentum (SUE) or 52-week proximity.** | Composite 12-1+SUE vs 12-1 on the same covered names: −0.48pp/mo (t −2.70, halves −0.27/−0.66, 5/16 yrs). Composite 12-1+PTH: −0.48pp (t −2.55, −0.20/−0.72). SUE alone: −0.73pp (t −2.58). | −2.55 to −2.70 | ~180 months | all halves − | 2011–26 chain_spot; SUE uses about 343 survivor names | `momentum_52wk_sue_2026-10-02.md` | Keep the screener on pure 12-1. A SUE-above-median filter is a wash (−0.05pp). |
| D12 | **…make new 12-1 names wait for a 20-EMA pullback** (cash otherwise). | E0.5 vs the certified rule (buy at the formation close): −0.11pp/mo. Deeper waits are worse (E0.0 −0.12pp). The control varies only entry timing. | **−2.01** | ~180 months | −0.07 / −0.14; 4/16 yrs + | 2011–26 chain_spot | `momentum_entry_refine_2026-10-02.md` | Buy the decile at formation. The roughly 10% of names that never pull back are the runners. ⚠ Below its own Šidák 2.57. Small effect. |

---

## 2. WHAT HELPS

### SIGNIFICANT (4)

| # | rule | effect vs CONTROL | t | n | halves / years | sample, universe | primary doc | how to act |
|---|---|---|---|---|---|---|---|---|
| H1 | **12-1 momentum:** buy the top decile of optionable names by close(t−21)/close(t−252), equal weight, monthly, 10 bp/side. | **+0.67pp/mo** over the equal-weight eligible universe. The control varies the name (everything vs the winners). Alpha on EW +0.56 (t 2.49), β 1.11. | **2.93** (NW) | 180 months | +0.38 / +0.92; 12/16 yrs | 2011 → 2026-01, chain_spot **incl. delisted** | `momentum_portfolio_2026-09-25.md` | **CERTIFIED (replication track):** t ≥ 2 and above its own Šidák(3) 2.39, pre-registered, post-publication. The top quintile is steadier (t 2.64, 14/16 yrs). Don't add an SPY > 200d filter (worse). Max drawdown 28%; crash months 2019-09 −12.2, 2023-01 −9.1. |
| H2 | **Require ≥ 2M shares/day** (Ariel criterion a3) inside the INT universe. | Dropping it costs **−0.49pp** of 20-day ADR-matched same-date excess. It excludes liquid high-priced names (median $319: URI, SPOT, MELI…) that lag in 6/7 years. 5-day: t −3.89. | **−4.24** (drop) | ~11 names/day excluded | −0.54 / −0.46 | 2020–26 liquid panel (survivor) | `ariel_ablation_2026-09-28.md` | Keep the share-volume floor. It clears Šidák-20 (3.02). The doc does not separate share count from nominal price. |
| H3 | **Short (open → cover close) a big gap-up (≥5% and ≥1.5 ADR) in a stock below a declining 50 SMA** (pre-registered with breadth falling). | **+0.54% per date** vs same-date eligible names with no gap. The control varies the name. One event per date: +0.81%, t 4.68. | **3.87** | 1,738 / 711 dates | +0.66 / +0.28; 12/17 yrs | 2010–26, `liquid_panel_2009` | `gap_fade_breadth_2026-09-26.md` | **PARKED, paper only.** The edge is the stock's own downtrend; breadth adds t 1.70 (not shown). ⚠ Cost-fragile: +10 bp/side → t 2.44, +20 bp → gone. It needs MOO/MOC auction fills. 2020: −2.1%. Top 20 trades = 49% of total. ⚠ The daily-panel opens may be vendor prints (cf. the yfinance-open caveat in `overnight_persistence_2026-09-24.md`), though 0/1,738 opens fell outside the day's range. |
| H4 | **(Index only.) Buy SPY on a close below its prior 5-day low;** sell after a close above the prior high or after 5 days. | **+0.468pp** vs any-day entry with the same exit (the control varies the entry day). QQQ: +0.584pp, t 4.43. | **3.72** (HAC) | 209 trades | +0.429 / +0.493; 13/14 yrs | SPY 2013–26, post-publication | `index_dip_family_2026-09-30.md` | Candidate, not adopted. About 6.8%/yr book: **off-goal** by Gabe's 9/30 rule. Listed for completeness. |

### STRONG LEAN (3)

| # | rule | effect vs CONTROL | t | n | halves / years | sample, universe | primary doc | how to act |
|---|---|---|---|---|---|---|---|---|
| H5 | **Require ≥ 70% above the 252-day low** (Ariel a1) inside INT. | Dropping it costs −0.62pp of 20-day ADR-matched excess. | **−2.74** (drop) | ~14 names/day | −0.93 / −0.41 | 2020–26 liquid panel (survivor) | `ariel_ablation_2026-09-28.md` | Keep it. Below Šidák-20 3.02. |
| H6 | **Pick from the INT or HYB-B momentum universe rather than the plain Trend Template** (HYB-B = TT at a $100M floor plus ADR ≥ 4). | 20-day excess vs ADR-matched same-date panel names: INT **+1.44pp** (t 2.47, halves +1.63/+1.31), HYB-B **+1.79pp** (t 2.60, +1.77/+1.80), TT +0.56 (t 1.30). | 2.47 / 2.60 | ~80 effective dates | both + | 2020–26 (survivor) | `universe_test_2026-09-21.md` | The universe carries the return, not the trigger. Breakouts inside any universe show edge vs a later day of ≈ 0. ⚠ The ADR-matched check was not pre-registered. HYB-B holdout 2010–19: +1.16%, t 1.35 on 28 dates (same sign, underpowered). |
| H7 | **Earnings "good + MUTED":** reaction day up, RVOL ≥ 1.5, close in the upper half, move ≤ 4%; enter at the next open. | +0.094R vs random **other names** on the same date (2010–19 holdout, arm fixed in advance). In-sample: t 3.17, 8/8 yrs. | **2.54** | 676 | +0.046 / +0.127 | holdout `liquid_panel_2009` (survivor) | `equity_holdout_2010_19_2026-09-29.md` | **Relative selection only, not a trade.** Vs a later day in the same name it is −0.008R (t −0.09), and raw R is −0.038 in the holdout. Use it as a tiebreak between candidates, not as a buy signal. |

---

## 3. The mechanism behind the entry leak: entry extension

Source: `entry_vs_stop_2026-09-20.md` (`run_entry_vs_stop.py`, `liquid_panel_2019`, survivor).

- **Sample.** 44,062 house breakouts vs 43,344 controls. Each control is a random later session in the same
  name, within the next 20 sessions (harness `post`). The control varies only the **entry day**; name, stop
  and exit are held fixed.
- **It is the entry, not the stop.** With no stop at all, the breakout underperforms the later entry at every
  horizon: **−0.411pp at 5d, −0.259pp at 10d, −0.074pp at 21d**. Stop-out rates are identical (48.4 vs 48.0%,
  62.4 vs 61.9%, 73.1 vs 73.2%), and the same holds at a 2-ADR stop.
- **Price paid.** The breakout enters **+0.52 ADR above** the prior 20-session high. The random later entry is
  **−2.09 ADR below** it. That is **≈ 2.6 ADR more paid for the same name**.
- ⚠ **No t-stat is reported** for the raw gap in the primary doc.
- **Ledger shape.** In 22 of 40 daily ledger patterns the later control beats the signal. On breakout variants
  the signal is −0.21 to −0.33R and the control is +0.13 to +0.21R (R with slippage and a t1R cap; this doc's
  no-cost R levels are milder).
- **Corroboration with t-stats:**
  - D1: ORB9, t −8.50, the intraday form.
  - D2: stage-2 breakout day, t −6.29.
  - D3: PIT breakout vs random member, t −3.71.
  - The pivot-break intraday entry sits +2.0 ADR over the 21 EMA and is the worst-timed of 13 levels
    (`level_trigger_test_2026-09-21.md`).
- **It is not fixable at entry.**
  - Deferring entry to a retrace beats the breakout in 6/6 cells but only at t 0.48 (`retrace_entry_2026-09-20.md`).
  - The book is bimodal. 23.6% of breakouts never return to the level and earn +1.27R; 76.4% return and earn −0.37R.
  - No feature calls the split at entry. The best is distance to the 21 EMA: +0.057R, t ≈ 2.
  - Within a good selection, entry timing is irrelevant or harmful:
    - band / open / close: 0/6 (`band_runaway_entry_2026-09-25.md`);
    - momentum EMA-wait: D12.
- **Practical reading.** Location discipline (within about 1 ADR of the 21 EMA) is directionally right. The
  winners that matter never come back, so fixed small size plus selection is the lever, not a cleverer trigger.

---

## 4. Excluded despite strong-looking numbers (and why)

| claim as often cited | why it is not on the lists |
|---|---|
| Close entry beats intraday ORB/reclaim entries (−1.22 / −2.28pp, t −3.4), `entry_study_2026-09-17.md` | No halves reported, one Feb–Sep 2026 regime (Mar–May carries it). The t is for intraday entry **+ intraday stop + re-entry** vs the close, so it is confounded with stop execution. Direction is consistent with D1. |
| Alert-price entry worse than the close (−1.53%, t −3.2), `alert_funnel_test_2026-09-17.md` | No halves reported. The stop differs (1.8% vs 5.7%). The curated hindsight list. |
| Leading-sector filter INVERTED: bottom-3 sectors beat top-3 (+5.60pp at 63d same-date, t 2.61), `industry_rotation_detection_study.md` | No halves reported, not pre-registered (2026-07), 299-name survivor set. The co-breakout test leans the other way (CONFIRMED − LONE +1.61pp, t 1.80). Read it as "don't veto a clean setup for a weak group", not as a positive filter. |
| "Buying the catalyst day −0.173R, t −4.70" (DR-EP arm A) | The t is **absolute**. Edge vs a later day is −0.047R and vs other names −0.075R, with no t reported (`drep_catalyst_retrace_2026-09-22.md`). |
| Pivot-break worst-timed (edge −0.093R); VWAP double-rejection short (edge −0.084R) | Only absolute t-stats are reported (−4.5, −6.2). The edge t vs a random minute is not reported. |
| Precision tier vs a random other name +0.44R, t 3.52 | Survivor panel. On the PIT S&P 500, TIER vs random is −0.73pp (t −1.20). The OOS refit is null. |
| Breakout inside HYB-A vs a later day, t 4.15 | Reverses on the 2010–19 holdout: −0.81R, t −4.44. RETRACTED. |
| "A hot streak precedes worse trades" (−3.71pp, t −2.17, holdout halves both −) | Same rule on 2019–26: +0.69pp (t 0.46). The sign flips across samples (`self_regime_holdout_2026-09-25.md`). |
| Next-open entry costs −0.32% (t −2.7 / −2.1) | That is deciles 9–10 only. All trades: −0.144%, t −1.34 (`logs/overnight_execution.log`). |
| Ariel's broker-logged shorts +7.66pp, t 3.39 | His picks, not a codable rule. His longs lean INVERTED (−2.23pp, t −2.15). |
| Insider clusters −1.68pp (t −2.23); buybacks +0.53pp (t 2.28) | Industry tilts: ≈ 0 / −0.38pp vs same-industry peers. Insider halves are not reported. |
| EP out of a base vs other names, t 2.94 | Best of several exit arms; fails its own p_search (0.0035 vs 0.003). |
| Reversal long on fresh lows +0.34pp, t 2.91 | Method check t −0.73. Top 1% of trades = 114% of the excess. |
| Spin-offs +10.45pp, t 2.06 | n 38, survivor-flattered (228 registrants dropped), +5.4pp (t 0.96) vs industry peers. |
| Small-cap precision breakout −0.50pp vs random small caps | t −1.99, below 2. |

## Notable nulls (commonly believed to help; tested ≈ 0)

1. **Intraday triggers ≈ a random later minute.** Stage A: 11,227 UR/ORB9/LVL alerts. UR vs a random minute
   is +0.033pp (t −0.31). Level triggers: 0/12 (`stage_a_intraday_2026-09-18.md`, `alert_triggers_2026-09-23.md`).
2. **Tight-stop intraday pullback entries (Luk-style).** TIGHT − BETA: +0.003pp, t 0.02, MDE 0.38pp (`luk_tight_stop_survival_2026-10-01.md`).
3. **Base quality.** VCP −0.37pp (t −0.70). RMV tightness −0.43pp (t −1.43). Base depth −0.02pp (t −0.13).
   Wedge Pop −0.38pp (t −0.28). The breakout payoff does not depend on the base.
4. **Market-state gates on breakouts.** QQQ 10/20 RED −0.86pp, t −1.68, halves flip. Distribution-day count has
   the wrong sign. The breakout-activity gate reversed out of time.
5. **Volume as a selector.** RVOL joint work is inconclusive. Dollar-volume rank on the holdout: t −0.97. Up/down
   volume ratio: t 0.39. High-volume premium: t −0.01.
6. **Catalyst / "in play" as selection.** +0.02pp, t 0.05 (`catalyst_selection_2026-09-28.md`). The long-base
   condition on earnings gaps adds nothing (−0.49pp, t −0.64).
7. **Precision-tier gates one by one.** 0 of 9 earn their place. Within 15% of the 52-week high: +0.12pp, t 0.14.
   `prev_green`: t −0.16.
8. **Pullback / retrace / confirmation entries vs the breakout.** Daily EMA pullbacks: t ≤ 1.4. Retrace: t 0.48.
   The confirmation ladder buys safety one-for-one in price.

---

## 5. Summary vs primary discrepancies found

1. **Qullamaggie review row (§9): "ORH entry vs the close −1.22pp, t −3.4".** The primary
   (`entry_study_2026-09-17.md`) measures ORB15 entry **with an intraday stop and re-entry** vs the close entry.
   The stop execution is part of the comparison. The ORB15 close-judged entry vs the close is not paired-tested,
   and no halves are given. The clean entry-only evidence is ORB9 vs a random minute (D1).
2. **DR-EP "−0.173R, t −4.70"** is quoted in several §9 creator rows (USIC, KINFO, Qullamaggie) as evidence
   against buying the catalyst day. It is an absolute t. The edges vs controls are small and untested.
3. **Alert-suite row (§5): "FBO −0.148%/trade (t −3.80), worse than control (−0.126pp)".** The t −3.80 is
   absolute. The control comparison with a t is the 9/30 doc: −0.156pp vs a random minute, t −4.04. Same
   conclusion, different statistic.
4. **Leading-group "INVERTED"** is cited throughout §9 as settled. The primary has no halves, a naive pooled t
   on the +9.12pp/t 4.57 baseline figure, and only the same-date pairing (t 2.61) as the clean cell.
5. **Overnight-execution row:** "buying at the next open costs −0.32% (t −2.7/−2.1)" is correct for deciles 9–10.
   The all-trades figure in the log (−0.144%, t −1.34) is not in the row, so "the close is right" is a lean.
6. **Entry-extension memory/notes** give the "2.6 ADR" correctly (+0.52 vs −2.09). The primary doc reports no
   t-stat for the raw-return gap.
7. **Haber stage-2 breakout day (t −6.29)** reads as a finding in the TEST_INDEX row. The primary labels it a
   reported secondary that was not pre-registered.
