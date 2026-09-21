# Test index — every strategy and claim tested, one line each

_Started 2026-09-19. One row per test: what was asked, the verdict, and where the detail lives. Newest work
is at the top of each section. Verdict vocabulary: **IN BOOK** (traded, survives costs and audits) ·
**MARGINAL** (positive but below the bar or thin) · **FAIL** (tested, no edge) · **INVERTED** (the opposite
of the claim holds) · **INVALIDATED / WITHDRAWN** (an earlier positive result was an artefact) ·
**DESCRIPTIVE** (measured, not a tradeable claim). Pattern-harness rows also live in
[pattern_ledger.md](pattern_ledger.md) (bar: beats the same-name random control, both halves positive, |t| ≥ 3)._

## 0. What survives (the book as of 2026-09-20)

| what | verdict | detail |
|---|---|---|
| **7-DTE long straddle + bull put spread as a PAIR** — the two surviving option strategies, corr −0.25; the blend clears t 2.5 where neither leg does alone (1.8 / 1.2) | **IN BOOK** — the pair is the unit, size small | [audit_review_2026-09-16.md](audit_review_2026-09-16.md) §4, [long_straddle_playbook.md](long_straddle_playbook.md) | <br>⭐ **2026-09-20: the straddle is now fully measured** — real entry quotes (median spread 6.5% of mid) and a path-simulated exit, no modelled assumption left. **The −50% stop is REMOVED** (worth nothing at mid, −3.84pp once the exit crossing counts; 0 of 20 depth×timing variants beat no stop). **Honest arm-4 expectation +6.73%/trade unstopped at a realistic fill.** [straddle_slippage](straddle_slippage_2026-09-20.md), [stop_path](straddle_stop_path_2026-09-20.md), [stop_sweep](straddle_stop_sweep_2026-09-20.md)
| **SPX condors (bullish-high-IV + 200MA; bearish-high-IV) and QQQ / SPY bull puts by regime**, after the cost model | **IN BOOK** — Tier A/B (+9.4 to +22.5% net) | [playbook_review_2026-09.md](playbook_review_2026-09.md), [capital_allocation_framework.md](capital_allocation_framework.md) |
| **Equity swing: buy the daily close of a precision-tier breakout** (ADR 4–7, <15% off high, EMA stack 5–40d, RVOL ≥ 1.8), stop = day's low on the close, exit on a close under the 20 EMA | **IN BOOK, MARGINAL-PASS (2026-09-19)** — honest expectation **+0.4R** (cap 20, stops ≥ 2%), not +0.79R; 30% win, median −1.08R; beats a random name +0.4–0.6R (selection) and a random later day +0.1–0.3R (timing, 2023+ only) | [breitstein_tests/precision_tier_control_2026-09-19.md](breitstein_tests/precision_tier_control_2026-09-19.md), [exit_timing_study_2026-09-18.md](exit_timing_study_2026-09-18.md), [daily_routine.md](daily_routine.md) | <br>⚠ **2026-09-20 qualifiers** (measured on the BROADER house 20d-breakout mask, ADR≥3 — *not* the precision tier, so these bound the family rather than overturn this row): the population is **bimodal** — 23.6% never return to the level (**+1.27R**), 76.4% do (**−0.37R**); **the split is not callable at entry** (best gate = distance to 21 EMA, +0.057R of a 1.647R spread); and entry **location** is worth ~2.6 ADR of price vs a later entry. Deferring entry to a retrace beats the breakout in all 6 cells but **fails the t bar (0.48)** — parked, not adopted. [entry_vs_stop_2026-09-20.md](entry_vs_stop_2026-09-20.md), [breakout_hold_predictors_2026-09-20.md](breakout_hold_predictors_2026-09-20.md)
| **Size lever = exclusion** (trade A+B grades only, +0.29R OOS) rather than scaling risk by grade (+0.08R, more drawdown) | **IN BOOK** | [size_lever_2026-09-18.md](size_lever_2026-09-18.md) |

## 1. Option premium selling

| test | verdict | detail |
|---|---|---|
| ETF playbooks re-scored with the cost model (commission + 25% of bid/ask): XLU/XLV/XLP put calendars, TLT, XLF | **INVALIDATED** — negative after costs (calendars −54 to −129% net) | [playbook_review_2026-09.md](playbook_review_2026-09.md) |
| SOXX always-on bull put; GLD bull put VIX<25 | **MARGINAL** — 4 of 8 years negative / positive only 2024–26 | same |
| ETF bull put spreads: is the exit rule the edge? (50% take, no stop, hold to expiry) | **DESCRIPTIVE** — the exit rule carries the put-spread result; it is mostly directional beta | [etf_put_spread_exit_rule_2026-09-16.md](etf_put_spread_exit_rule_2026-09-16.md), [etf_put_spread_study.md](etf_put_spread_study.md) |
| Does the put-spread exit rule generalise to bear calls / condors on ETFs? | **FAIL** — nothing on the call side; ETF condor +0.36%/trade, t 0.6 | [etf_condor_call_side_2026-09-16.md](etf_condor_call_side_2026-09-16.md) |
| Own-IV-percentile gate on QQQ / IWM bull puts | **FAIL** — high own-IV is a mild VETO on the index, not an edge (≥80th pct = veto) | [qqq_iv_gate_study.md](qqq_iv_gate_study.md), [iwm_iv_gate_study.md](iwm_iv_gate_study.md) |
| Paid-to-wait single-name put spreads (7-yr real quotes) | **MARGINAL** — generic rule −3.3% net; IV ≥ 60th pct gate +5.7% net / 78% win; never close on the break; 2021–22 negative | [paid_to_wait_study.md](paid_to_wait_study.md) |
| "More like CF + XLE" profile (3 wins) — does it carry an edge? | **FAIL** — three wins at an 80% base rate is the base rate; breach odds depend only on cushion in ADR (2 ADR ≈ 21%, 3 ≈ 13%) | [ema_strike_breach_study_2026-09-17.md](ema_strike_breach_study_2026-09-17.md) |
| Short-dated (10-DTE) premium selling on single names | **FAIL** — net negative (costs = 136% of gross); liquidity is the gate, tradeable set = SPY + NVDA/AMZN/AAPL/V | [vrp_shortdte_names_study.md](vrp_shortdte_names_study.md) |
| Variance risk premium panel (measure IV − realised directly) | **DESCRIPTIVE / real** — 10d premium +1.75vp t 8.9, 17/17 years; 30d/90d/term-structure absent; FVR doesn't sort | [vrp_panel_study.md](vrp_panel_study.md), [vrp_straddle_reconcile.md](vrp_straddle_reconcile.md) |
| FVR (10/30d ratio) → short straddle P&L regression | **FAIL** — zero predictive power | [fvr_straddle_regression_playbook.md](fvr_straddle_regression_playbook.md) |
| QQQ VRP regression (oquants-style single-ticker model) | **DESCRIPTIVE** — at the breakevens; not a verdict on flies | [qqq_vrp_regression.md](qqq_vrp_regression.md) |
| BCI cash-secured puts / covered calls vs holding stock at the same delta (326 names, 8 yrs) | **FAIL** — stock-at-same-delta minus costs; filters add nothing; selling through earnings earned MORE | [bci_csp_study_2026-09-17.md](bci_csp_study_2026-09-17.md) |
| CSP expansion (breakout-screen rejects as the CSP universe) | **DESCRIPTIVE** — gate stack + candidate list only; superseded by the BCI result | [csp_expansion_playbook.md](csp_expansion_playbook.md) |
| UVXY: reverse wheel; short put / short call sweeps; combined bear call + short put | reverse wheel **FAIL** (max DD > total profit in every variant); combined strategy **Tier C, no stop by design** | [uvxy_reverse_wheel.md](uvxy_reverse_wheel.md), [uvxy_strategy_playbook.md](uvxy_strategy_playbook.md), [uvxy_combined_strategy.md](uvxy_combined_strategy.md) |
| SPX short strangle by regime | **IN BOOK (Tier B)** — as the condor above | [spx_strangle_playbook.md](spx_strangle_playbook.md) |

## 2. Long volatility

| test | verdict | detail |
|---|---|---|
| 7-DTE long ATM straddle, pool of ~323 names, FVR + IV-percentile gate | **IN BOOK (as the pair)** — honest expectation ~+4%/trade after costs; ⚠ P&L is 99.9% from the top 0.1% of trades | [long_straddle_playbook.md](long_straddle_playbook.md), [vrp_straddle_reconcile.md](vrp_straddle_reconcile.md) |
| Straddle re-centering / flat-take / −50% stop | **FAIL** — re-center −3 to −7pp; the stop clip is an artefact; 14-DTE no edge | [straddle_recenter_study.md](straddle_recenter_study.md) |
| Straddle → call / put / straddle by trend | **FAIL / not adopted** — gain is bull-market beta that always-call already has | [straddle_directional_legs_2026-09-16.md](straddle_directional_legs_2026-09-16.md) |
| RSI(14) as a gate: put spreads, straddle, Ryan's RSI+BB swing | put spreads: RSI = VIX proxy (**FAIL**); **straddle: skip RSI ≥ 70 — walk-forward PASSED, adopted as gate 5**; Ryan swing 1.5/5 | [rsi_conditioning_study_2026-09-16.md](rsi_conditioning_study_2026-09-16.md) |
| 1-DTE long ATM straddle at the close before expiry (COHR generalised, 153k trades) | **FAIL** — every exit ≈ −30% of premium; premise false (open > close only 25–29% of days); bid/ask is the whole P&L | [one_day_straddle_study.md](one_day_straddle_study.md) |
| Long-call strategy (step 1: does the straddle's IV-pct gate transfer?) | **FAIL (step 1)** — gate kills weekly t and 2022; benchmark is always-call +9.5%; call prefers high IV pct + mild uptrend | [call_strategy_project.md](call_strategy_project.md) |
| "Buy a QQQ LEAP every ≥ 1% down day" | **FAIL** — no edge vs any day (12mo −5.8pp, t −0.7) | [qqq_dip_leap_study_2026-09-17.md](qqq_dip_leap_study_2026-09-17.md) |
| Event convexity: 0.12Δ / 0.25Δ calls bought the session before FOMC / elections | **MARGINAL / real tail** — beats random dates on every exit (sell-5d +30.7% vs −3.6%); lottery sizing, sell within 5 sessions | [event_convexity_2026-09-18.md](event_convexity_2026-09-18.md) | <br>⚠ **2026-09-20:** the 0.12Δ-over-0.25Δ preference is a **mid-price artefact** — +19.5pp (t 2.73) at mid but **+1.9pp (t 0.29) at realistic fills**; do not treat 0.12Δ as the established strike. Expressing it as a debit spread FAILS on friction, not capping. [ftd_names / event_spread_2026-09-20.md](event_spread_2026-09-20.md)
| Momentum-skew verticals (oquants #3) on real quotes | **FAIL as a strategy** — the skewness premium is measurable (~15pp/unit move) but the realised P&L does not pay | [momentum_skew_vertical_study.md](momentum_skew_vertical_study.md) |
| Sleeping Giants: cheap LEAP on a multi-year base (Tito note 2) | **MARGINAL** — convex edge holds OOS; exit lever unbuilt; IV-rank gate TODO | `Adhikary/sleeping_giants_*.csv`, `src/lib/sleeping_giants/` |

## 3. Calendars and diagonals

| test | verdict | detail |
|---|---|---|
| Single / double put calendars, diagonals, condors on ETFs and stocks (path study) | **INVALIDATED then FAIL** — steps 4–12 of the original were a path-truncation artefact; clean re-run: no edge on ETFs, stocks lose 8–18%; playbook and screener entries withdrawn | [calendar_path_study.md](calendar_path_study.md), [double_calendar_playbook.md](double_calendar_playbook.md), [audit_review_2026-09-16.md](audit_review_2026-09-16.md) §1 |
| XLU / XLV / XLP / GLD put calendars (FVF ≤ 0.90, iv_ratio) | **INVALIDATED** — negative after costs on real bid/ask; retired 2026-09-15 | [playbook_review_2026-09.md](playbook_review_2026-09.md), the four `*_calendar_playbook.md` files |
| SPY double calendar 0.35Δ; IWM put calendar (hold to short expiry) | SPY **Tier B** (own cost model, gains concentrated 2021/24/25); IWM **Tier B** | [spy_double_calendar_playbook.md](spy_double_calendar_playbook.md), [iwm_calendar_playbook.md](iwm_calendar_playbook.md) |
| oquants forward-factor calendars | **FAIL** — the signal does not replicate on index ETFs | [oquants_forward_factor_replication.md](oquants_forward_factor_replication.md) |
| Earnings placement for double calendars (tastylive segment) | ⚠ **RETRACTED 2026-09-20 — contaminated by the path-truncation bug.** It was the `calendar_path_study.md` "earnings position" cut, and steps 4–12 of that study were invalidated 2026-09-16. The erratum states **87% of paths with a >3% move were truncated before the loss finished** — and an earnings move IS a >3% move, so this is the **worst-affected slice**, not a survivor. The +10–15% / 66%-win figure and the playbook rule 3 change it drove are both withdrawn. Re-answer by measuring implied vs realised directly, not by re-running a path sim | [calendar_path_study.md](calendar_path_study.md) erratum |

## 4. Equity swing — entries, exits, stops, size

| test | verdict | detail |
|---|---|---|
| **Pattern-ledger re-run with honest controls** (19 daily patterns × `post` timing + `xname` selection; the original same-month control had look-ahead) | **still 0 for 19** — the month control was inflated +0.14…+0.21R for continuation patterns and deflated −0.48…−0.86R for reversal patterns, so every old `edge` was mostly the control; honest edges −0.09…+0.26R, none |t| ≥ 3. Closest: earnings drift good+MUTED +0.27R, beats both controls by +0.25, t 2.65 | [ledger_rerun/ledger_rerun_2026-09-19.md](ledger_rerun/ledger_rerun_2026-09-19.md) |
| Entry timing on layer-2 name-days: close vs ORB / intraday low / pivot buy-stop, with intraday stop execution | **FAIL for intraday entries** — the CLOSE beats every intraday entry (t to −3.4); tightness comes from day structure, not entry timing | [entry_study_2026-09-17.md](entry_study_2026-09-17.md) |
| Profit-lock exits on the house breakout (1,968 trades): breakeven after +1R/+2R, lock +1R, tighten when ≥2 ADR extended, 10-EMA trail, trim half at +2R / 2–3 ADR | **FAIL / INVERTED** — only BE-after-+2R is harmless (+0.01R, t 1.3 = NULL, allowed as comfort rule); BE +1R −0.08R and raises give-back 39→46%; "extended → tighten" INVERTED (−0.19R t −2.8, 10-EMA −0.47R t −4.8); trims −0.25…−0.33R for −25…−40% drawdown = worse per unit DD than half size; cap-10 "trim pass" is the clip | [profit_lock/profit_lock_2026-09-20.md](profit_lock/profit_lock_2026-09-20.md) |
| Exit timing: same-day exits vs holding, our pool and Gabe's own book | **DESCRIPTIVE / decisive** — same-day exits are the negative bucket in both books (scalp −0.13R vs trail +0.89R; 278 same-day cycles −$8.3k, 19% win) | [exit_timing_study_2026-09-18.md](exit_timing_study_2026-09-18.md) |
| Where tight stops come from + can regime be fed back (breakout pool, 3,539 events) | **DESCRIPTIVE** — entries 0–1.5% above the low stop out 76%; the paying months cannot be forecast (47% positive, top decile = 68% of R) → fixed small size, no switch | [breakout_regime_and_stop_distance_2026-09-17.md](breakout_regime_and_stop_distance_2026-09-17.md) |
| Precision-tier breakout vs three random controls (same-month / later-day / other-name), R-cap and stop-floor sensitivity | **MARGINAL-PASS** — +0.63R uncapped, +0.39R cap 20, +0.15R cap 10 (t 3.9 / 3.3 / 1.5); the +0.79R headline was tiny-stop trades; **found look-ahead in the harness's same-month control** | [breitstein_tests/precision_tier_control_2026-09-19.md](breitstein_tests/precision_tier_control_2026-09-19.md) |
| Adhikary breakout initial-stop rules (entry low / ADR / EMA) | **DESCRIPTIVE** — no stop rule turns the generic breakout positive; precision cohort is the lever | [adhikary_stop_study.md](adhikary_stop_study.md) |
| Adhikary archetype detectors A/B/C validated 2019–26 | **MARGINAL** — recipe ≈ flat; precision tier (ADR 4–7, <15% off high, stack 5–40d) +0.67R; B no edge; C daily bar INVERTED | [adhikary_detector_validation.md](adhikary_detector_validation.md), [tito_selection_playbook.md](tito_selection_playbook.md) |
| Pullback entries on leaders (Luk / Ariel EMA pullbacks) on daily bars | **FAIL vs the breakout** — +1.2–2.4%/trade (t ≤ 1.4) below the breakout entry; Luk's ≤3%-above-low version NEGATIVE | [pullback_entry_study_2026-09-17.md](pullback_entry_study_2026-09-17.md) |
| Size lever: scale risk by grade vs flat vs exclusion | **PASS for exclusion only** — A+B only +0.29R OOS; 10× spread +0.08R; ⚠ stop-distance cell fails as a grade | [size_lever_2026-09-18.md](size_lever_2026-09-18.md) |
| Vehicle choice for August 2026 entries (stock / calls / short puts / put spreads) | **DESCRIPTIVE** — no vehicle fixes entries; calls worst; put spread cuts loss 60–70% but forfeits the +5% winners | [august_2026_vehicle_study.md](august_2026_vehicle_study.md) |
| August 2026 trades through the Luk / Tito lens | **DESCRIPTIVE** — leak = entries 1–2 ADR over the 21 EMA + same-day round trips (−$7.9k) + stops blown past 2% | [august_2026_luk_tito_lens.md](august_2026_luk_tito_lens.md), [august_2026_retrospective.md](august_2026_retrospective.md) |
| Alert grading rubric (one rubric for alerts + journal) | **DESCRIPTIVE / adopted** — `src/lib/alerts/grading.py`; A/B good, C gray, F bad | [alert_filter_study_2026-09.md](alert_filter_study_2026-09.md), [journal_process_grades.md](journal_process_grades.md) |

## 5. Intraday triggers and alerts

| test | verdict | detail |
|---|---|---|
| **Stage A + bouncy ball intraday re-scored with honest controls** (random LATER minute / random other watchlist name at the same minute) | **FAIL, unchanged** — every intraday arm within ±0.03R of both controls; swing-arm gap flips sign with the control (noise); bouncy short −0.41…−0.67R on signal AND both controls | [ledger_rerun/ledger_rerun_2026-09-19.md](ledger_rerun/ledger_rerun_2026-09-19.md) |
| Stage A: UR / ORB9 / LVL intraday long triggers (11,227 fires) | **FAIL** — every arm −0.10 to −0.13R; a RANDOM entry in the same name-day beats the trigger on every arm | [stage_a_intraday_2026-09-18.md](stage_a_intraday_2026-09-18.md) |
| Alert funnel: do intraday alerts add anything once a name passed layer 2? | **FAIL** — alert day +3.85% = no-alert day +4.14%; alert-price entry + session-low stop is worse than the close entry (t −3.2) | [alert_funnel_test_2026-09-17.md](alert_funnel_test_2026-09-17.md) |
| Alert detectors replayed over 20 sessions (1,073 alerts) | **DESCRIPTIVE** — which detectors survive at the R level; feeds the rubric | [alert_filter_study_2026-09.md](alert_filter_study_2026-09.md) |
| QQQ intraday noise-band momentum (Zarattini–Aziz–Barbon replication) at $10k fixed | **MARGINAL** — engine replicates the paper; in Gabe's game 2.5%/yr, Sharpe 0.28, dead 2009–17 | [qqq_noise_band_replication_2026-09-17.md](qqq_noise_band_replication_2026-09-17.md) |
| TQQQ / SQQQ rule lab (17 years) | **FAIL for "consistent"** — every gated rule has 3–5 losing years vs QQQ's 2; one reasonable config (long-only, 200-day gate, 50% TQQQ, no SQQQ) | [tqqq_lab/RESULTS.md](tqqq_lab/RESULTS.md) |

## 6. Reversion, counter-trend and capitulation

| test | verdict | detail |
|---|---|---|
| Buying the crash (anti-Minervini): deep drawdowns from a 252d high | **REGIME BET, not selection** — pays only in a broken tape; **veto: never in a healthy tape** (median −20%/252d) | [crash_leader_reversion_study.md](crash_leader_reversion_study.md) |
| Breitstein "boring stock, violent move" (drop ≥ k× own ADR, low prior ADR) | **INVERTED** — normalising and the boring gate SHRINK the reversion (60d +3.2% vs raw ≥15% drop +23.3%); the raw cell's reversion is entirely weak-tape; below SPY in a healthy tape | [breitstein_tests/boring_violent_2026-09-19.md](breitstein_tests/boring_violent_2026-09-19.md) |
| Breitstein counter-trend long (≥3 ADR below the 20 EMA + prior-bar-high break), A/B vs the bare trigger | **FAIL** — every arm negative (−0.15R slow / −0.33R t1R); bare trigger ≈ control; deeper extension and the volume flush are worse | [breitstein_tests/counter_trend_long_2026-09-19.md](breitstein_tests/counter_trend_long_2026-09-19.md) |
| Breitstein "bouncy ball" short (daily and intraday) | **FAIL** — daily −0.34R vs control +0.34/+0.48; intraday −0.41 to −0.67R, 18% win | [bouncy_ball_2026-09-18.md](bouncy_ball_2026-09-18.md) |
| Pullback-short screen (arrival signal) | **FAIL** — raw signal −1.5%/10d, worse in a weak tape → rejection-watch list only | `run_pullback_shorts.py`, memory `project_pullback_short_screen` |

## 7. Regimes, catalysts and rotation

| test | verdict | detail |
|---|---|---|
| Breitstein high-vol regime gate: split the 20d breakout by cross-sectional realised vol, watch which exit wins | **FAIL / no switch** — fast exit worst in BOTH halves, H−L ±0.02R, 12/12 cells; p90 cell lifts every arm = beta | [breitstein_tests/hivol_gate_split_2026-09-19.md](breitstein_tests/hivol_gate_split_2026-09-19.md) |
| Trailing-30-day regime rules from August 2026 (breadth, own results, stop-out share) validated 2019–26 | **FAIL** — none survives; weak breadth is a mild BUY; the August pattern was real but not forecastable | [trailing_regime_validation.md](trailing_regime_validation.md), [august_2026_retrospective.md](august_2026_retrospective.md) |
| Industry rotation detection (the 2026 insurance rally, forensically) | **FAIL to front-run** — leading-group filtering INVERTED (bottom-3 sectors beat top-3, t 2.6); by-products: RVOL gate 1.2 → 1.8, vetoes below 200sma / 6mo < −10% | [industry_rotation_detection_study.md](industry_rotation_detection_study.md) |
| Catching multi-month group moves early (31 ETFs, 2006–26) | **DESCRIPTIVE** — 12 legs/yr of ≥ +20pp; joining after the first +5pp relative signal is measured, not an edge claim | [group_move_study_2026-09-17.md](group_move_study_2026-09-17.md) |
| FOMC as a catalyst (buy high-beta before the decision) | **FAIL** — pre-FOMC drift visible but t < 2 and sign flips across entry day | [fomc_event_study_2026-09-18.md](fomc_event_study_2026-09-18.md) |
| Earnings proximity / "good earnings, delayed bump" (Tito) | **RETRACTED / FAIL** — proximity finding was bucket mix; delayed bump loses to the same-name control (−0.19 to −0.36R) | [delayed_earnings_2026-09-18.md](delayed_earnings_2026-09-18.md) |
| What moved after each election (5 elections) | **DESCRIPTIVE** — not a sample | [election_cycles_2026-09-18.md](election_cycles_2026-09-18.md) |
| Index-add rebalance auction: does the run-up into the effective date reverse? (173 S&P 500 / NDX adds, 2019–26) | **FAIL** — pre-registered T+5 vs xname t −0.83 (bar 3); every arm \|t\| < 1.4 vs post / xname / extension-matched controls; direction is −1pp at T+5 and 40% win but inside the noise; no gradient in extension; MDE 1.84pp | [index_add_study_2026-09-20.md](index_add_study_2026-09-20.md) |
| Oil transmission map (USO / XOP / XLE capture, lag, continuation) | **DESCRIPTIVE** — no lag, no continuation edge; the trade dies once the equity has run >10% | [oil_spike_short_playbook_2026-09.md](oil_spike_short_playbook_2026-09.md) |
| Cameron / Breitstein "80% chance of doubling the loss after breaching max loss" on Gabe's journal | **QUEUED** (Breitstein test 1) | memory `project_breitstein_test_queue` |
| Margin expansion in the cost model for short premium in high-IV regimes | **QUEUED** (Breitstein test 5, design note first) | same |

## 8. Ticker playbooks (single-ticker option systems, mostly 2026-03 → 05)

Status after the September 2026 cost re-score. Playbook files are in this directory as `<ticker>_*_playbook.md`.

| ticker / system | status |
|---|---|
| SPX condors (2 regimes), QQQ bull puts (3 regimes), SPY bearish-high-IV bull put | **survive** — Tier A/B |
| SPY double calendar, IWM put calendar, SPY bullish-low-IV bull put, SOXX, GLD | **marginal / Tier B–C** |
| XLE bull put (bearish-high-IV) | **blocked** — not reproducible from the split-adjusted cache; episodic only |
| XLU / XLV / XLP put calendars, TLT regime switch, XLF regime switch | **dead after costs** |
| INDA, UUP, BJ, USO, SQQQ, UVXY, UVIX, ASHR, TMF, CLS, GEV, XOP | **Tier C fillers / provisional** — liquidity re-check before any entry; ≤ 2 years of data for the provisional set |
| YINN, FXI, EEM | **removed / discarded** (do not re-analyse YINN) |

## 9. Creator knowledge bases (claims tested, not just reviewed)

Each KB folder under `data/<creator>/` carries a skeptic-default leaderboard; only claims that reached a test are listed here.

| creator / claim | verdict | detail |
|---|---|---|
| Lance Breitstein — bouncy ball, boring/violent, counter-trend long, high-vol gate (4 tests) | **4 FAIL** (one inverted) | `data/lance_breitstein/PRINCIPLES.md`, §6–7 above |
| Tito Adhikary — 4 archetypes, delayed bump, sleeping giants, event convexity | precision tier + convexity **MARGINAL**; rest **FAIL** | `data/studies/Adhikary/`, §2, §4, §7 |
| Martin Luk / Ariel Hernandez — EMA pullback entries, tight-stop version | **FAIL on daily bars** (intraday version untested) | §4 |
| BCI (TraderLion) — covered calls / CSPs | **FAIL** | §1 |
| oquants — forward-factor calendars, momentum-skew verticals, VRP ETF | **FAIL / mechanism only** | §1, §3 |
| Options With Ravish — double calendar management (early TP, re-center, low-VIX entry) | **INVERTED** by the path study; his double DIAGONAL idea was the better cell before the study was invalidated | `data/options_with_ravish/`, §3 |
| tastylive — double calendar vs condor, earnings placement | **INVERTED** (earnings between the expiries is the best cell) | §3 |
| Options With Ryan — RSI+BB swing on SPY/QQQ | **FAIL** (1.5/5) | §2 |
| Theta Profits — 0DTE long strangle and 30 others | **FAIL** (all ≤ 2.5/5; EOD floor −26%/trade) | `data/theta_profits/` |
| **Stop level × timing sweep** (20 cells: exit at −50/−65/−75/−85/−90%, × DTE gate any/≤3/≤2/≤1) | **NULL across the family · MECHANISM.** **0 of 20 beat no stop.** Both intuitions are directionally right — deeper is better at every timing, later at every depth (best: −90% @ ≤1 DTE, only −0.71pp) — but the gradient's limit is *don't stop*. ⭐ Why: **bid/ask on a near-worthless straddle is 16% of mid (mean 27%) vs ~8% normally** — the cost of cutting peaks exactly when you want to cut. ⚠ the playbook's −50%/any-DTE is the **worst cell in the grid** | [straddle_stop_sweep_2026-09-20.md](straddle_stop_sweep_2026-09-20.md) |
| **The straddle's −50% stop, path-simulated** (4,573 arm-4 trades, 43,203 leg-days of real marks) | ⭐ **INVERTED · MECHANISM — the stop is a COST, not a rescue. DROP IT.** (⚠ **confirms**, not discovers: the playbook's 2026-09-10 revision already called the clip an artefact — this reproduces it on arm 4 and **adds the exit-crossing cost**.) You exit at median **−59.7%/mean −64.3%**, not −50%; at mid a path stop is worth **nothing** (+8.86% vs +8.77% unstopped) and the clip's whole +6.69pp was the −50%-exactly assumption. Stopping costs **−9.51pp on the stopped cohort**; **69.8% would have done better held, 7.6% would have finished positive**. Honest arm 4 at a real fill: **+6.73% unstopped vs +2.89% stopped** | [straddle_stop_path_2026-09-20.md](straddle_stop_path_2026-09-20.md) |
| **Pre-earnings vol RAMP** (`src/lib/earnings/earnings.py` modernised: buy ATM straddle −3/−5/−10 bd, sell on the pre-print session; 1,762–2,572 events) | ⭐ **NULL · MECHANISM.** The ramp is REAL and huge — ATM IV **+40 to +57 vol points** into the print — and the front-expiry straddle **loses even at MID** (−3.4 / −6.9 / −14.3%), |t| 23–37, **8/8 years negative** at every entry. **Theta > vega**: σ doubles while √T falls to ~0.4 on the tenor that carries the ramp. ⭐ Liquidity halves the round-trip spread (16→8% of cost) and is STILL negative at mid — the loss is time decay, not friction. Longer tenor untested | [earnings_ramp_2026-09-20.md](earnings_ramp_2026-09-20.md) |
| **Earnings calendar, further-out back leg** (+30d and +45d vs next-expiry; liquidity-gated; 1,786–2,604 events) | ⭐ **NULL at every distance · MECHANISM.** Mid premium GROWS with the back leg (double +0.33→+0.47→+0.56%) but the debit nearly triples ($1.07→$2.95) and friction scales with it: real −1.53→−2.36→−2.42%, **8/8 years negative at every distance**. ⭐ **The liquidity gate does NOT rescue it** (unlike the straddle): top-40%-volume at a generous limit fill is −0.34 / −0.67 / −0.54%, |t| 3.3–5.8, 7–8/8 neg years. Straddle crosses the spread once; the calendar crosses it 3× incl. the back leg the print just blew out. `ts_slope` still doesn't sort at its own geometry | [earnings_calendar_backleg_2026-09-20.md](earnings_calendar_backleg_2026-09-20.md) |
| **Earnings CALENDAR** — short front / long back at the ATM strike, real exit marks, intrinsic floor (3,118 events) | ⭐ **NULL after costs · MECHANISM.** MID roughly flat (+0.09 to +0.33%); **paying the spread: call −0.777%, put −0.767%, DOUBLE −1.530%, all 8/8 years negative**, win collapses ~50%→~25%. **The double loses exactly 2× the single** → friction scales with legs. ⭐ **`ts_slope` does NOT sort its own vehicle**: flat at mid, and at real prices the MOST backwardated quintile is the WORST (−1.801) — the gate passes 90% of prints. The straddle-based null was right, now measured on the right instrument | [earnings_calendar_2026-09-20.md](earnings_calendar_2026-09-20.md) |
| **calculator.py pre-earnings vol gates** (iv30/rv30, term-structure slope, volume; 3,163 events) + regression | ⭐ **NULL for both VOL gates · MECHANISM · METHOD.** `iv30_rv30 ≥ 1.25` is **harmful** (−0.253pp at the bid) and its quintiles **invert** (cheapest IV/RV is best); `ts_slope` passes **90%** of prints so it barely filters (⚠ tested here on a STRADDLE, the wrong vehicle — re-tested on the CALENDAR, same null); **only `avg_volume` helps (+0.228pp)** — and it predicts the **spread**, not the premium (monotonic at BID, flat at MID). Regression: `iv30_rv30` **t 0.07**, `implied_pct` drives gross (t 8.43) AND spread (t 11.23) so they cancel. ⭐⭐ **the SPREAD is R² 0.153 vs the premium's 0.027 gross / 0.005 net — cost is 5–30× more predictable than profit** | [earnings_gates_2026-09-20.md](earnings_gates_2026-09-20.md) |
| **Earnings vol premium — is the event overpriced?** (oquants claim; 4,477 events, 392 names, ATM straddle measured not simulated) | ⭐ **NULL after costs unconditionally · PARKED on liquid names · MECHANISM.** Premium is REAL at mid (**+0.601%**) and dies on the spread unconditionally — but **survives on the top ~40% by volume: +0.284% at the BID, 7/8 years positive, t 1.1** (≥5M: +0.281%, +0.438% at a limit fill). Below the t bar: at the bid **−0.428%**, 7 of 8 years negative. **Crossing costs 171% of gross** (straddle spread median 10.5% of mid). ⭐ **The selectivity lever INVERTS** — at mid the premium sorts monotonically on implied move (q5 +1.70) but at the bid q5 is the WORST (−0.718): rich events have wide spreads. ⚠ **a split/dividend-adjustment trap first gave +6.37% / 74% win** — fixed by delta-selected ATM + parity spot | [earnings_vol_premium_2026-09-20.md](earnings_vol_premium_2026-09-20.md) |
| **PEAD on the ACTUAL EPS surprise** (12,232 events, 456 names, known AMC/BMO timing) | **NULL for the surprise · PARKED for the tape signal on the STRADDLE POOL · METHOD.** ⚠ same-day correction: the original 241 names were 100% the straddle pool; split by pool on the independent yfinance events the tape signal **reproduces on the pool** (edge **+0.244R** vs original +0.246, t 1.89, both halves +) and weakens off it (+0.073R). Universe-specific, not spurious. No surprise bucket passes; `corr(surprise, reaction)` = 0.203. Ledger: 0/50 passes, **one PARKED near-miss standing** | [pead_2026-09-20.md](pead_2026-09-20.md) |
| **Long straddle entry slippage** — real bid/ask for both legs of all 41,757 gated entries (100% quote coverage) | ⭐ **ADOPTED (confirmed) · MECHANISM.** Measured spread **median 6.5% of mid**; **sensitivity −0.86pp per 1% over mid** (playbook guessed −0.95). Arm 4 +15.46% → **+13.57% at a realistic fill (−1.90pp)**, +11.78% at the FULL ASK, **every fold positive at every fill**. Assumption-free floor +6.73%. ✅ **doc discrepancy TRACED + FIXED**: the "arm 4" block was full-pool **FVR-gate-only** (no IV gate), mislabelled since 2026-09-02 — it understated the honest config by ~2.9pp. Stop clip is **43% of the headline, not 55%** | [straddle_slippage_2026-09-20.md](straddle_slippage_2026-09-20.md) |
| **Debit call spread as a vehicle** (long 30Δ / short 15Δ added to the August vehicle study; matched 93 trades where all 5 vehicles exist) | **NULL** (+METHOD) — no change to the ranking. Risk-equalized it is the WORST option vehicle (−2,605 vs put spread −199, short put −57) and has the lowest win rate of the five (17%). A directional vehicle on flat-to-down entries: loses like the call, then caps the rare winner. ⚠ friction invisible (v3 = prints only) and skew ignored — both flatter it, and it still finishes last | [vehicle_callspread_2026-09-20.md](vehicle_callspread_2026-09-20.md) |
| **Can the breakout hold/fail split be called at entry?** (9 book features vs the bimodal target, 43,970 breakouts) | **NULL · METHOD · REFRAME** — settled at this power. Spread available **1.647R**; best single gate (dist to 21 EMA) **+0.057R over baseline, t ~2**; best combo +0.112R on n=696, t 1.39, and gates do NOT stack. ⭐ **The best CLASSIFIER is the worst GATE** — extension has a 28.7pp held% spread but 0.036 meanR spread (mechanical, near-tautological). `sma_stacked` INVERTS. → the +1.27R cohort is unknowable at entry | [breakout_hold_predictors_2026-09-20.md](breakout_hold_predictors_2026-09-20.md) |
| **Retrace entry** — house breakout, entry deferred until price returns to the breakout level (6 cells) | **PARKED · REFRAME** — 2 of 3 bar criteria (beats control, both halves positive; **t 0.48**). B beats A in all 6 cells and the edge flips −0.101 → **+0.065**, both halves positive, B−C = +0.53R confirms entry timing — but **t 0.48** vs the |t|≥3 bar, so not adoptable. ⭐ **Bigger finding: the breakout book is BIMODAL — 23.6% never return = +1.27R, 76.4% return = −0.37R** (survivorship, not a rule). The lever is predicting that split, not the entry price | [retrace_entry_2026-09-20.md](retrace_entry_2026-09-20.md) |
| **Is the breakout's negative R an entry or a stop problem?** (44,062 house breakouts vs same-name later controls, with and without stops) | ⭐ **MECHANISM** (verdict: the ENTRY, not the stop). Raw gap negative at every horizon with NO stop (−0.41pp at 5d), and stop-out rates identical (48.4% vs 48.0%) so the stop cannot be the cause. Mechanism measured: breakout entry sits **+0.52 ADR above the prior 20d high vs −2.09 ADR for the control — 2.6 ADR of price paid**. Panel-scale version of the August 1-ADR location rule | [entry_vs_stop_2026-09-20.md](entry_vs_stop_2026-09-20.md) |
| **FTD → do SINGLE NAMES work better?** (the actual Ariel claim; house breakout split by post-FTD window, honest `post` controls) | **UNDERPOWERED · MECHANISM** — eff. n **8 FTD episodes**, not 900+ trades; settles only by extending the panel pre-2019. Post-FTD breakouts are WORSE (5d −0.196R vs −0.072R) and miss their own control by more. But the post-FTD **controls** are +0.045–0.080R vs +0.000–0.028R elsewhere → the names are better, the **breakout entry** is the wrong way in. ⚠ effective n = **8 FTD episodes**, not 900+ trades | [ftd_names_2026-09-20.md](ftd_names_2026-09-20.md) |
| **O'Neil Follow-Through Day** as a regime-entry switch (SPY 1993–2026, QQQ, IWM; 4 param cells; bootstrap null) | **NULL** (+METHOD: naive-arm control) — eff. n 16–37 signals, ~144 tests run. No edge vs other correction days at +5/+10/+21d; **IWM negative in 10 of 12 cells** (p to .97); the up-%/volume gates barely beat a naive 'wait 4 days into the rally attempt' arm (−0.9 to +0.7pp at 10–21d). Only +63d SPY/QQQ survives, which is 'drawdowns recover over a quarter', not timing. 3rd failure of trailing-regime timing | [ftd_2026-09-20.md](ftd_2026-09-20.md) |
| **Event convexity expressed as a debit spread** (long 0.25Δ / short 0.12Δ, 3,377 spreads, 53 event dates) | **NULL as a vehicle · MECHANISM · METHOD** — eff. n **53 event dates** (not 3,377 spreads). The queued hypothesis was WRONG: The cap binds on 1.7% of trades and costs −2.0pp (t −0.45) at mid; the second leg's FRICTION costs −27.1pp (t −5.51). Event premium survives capping (+20pp gap). ⚠ Bonus: 0.12Δ beats 0.25Δ by +19.5pp at mid (t 2.73) but +1.9pp (t 0.29) at real fills — the far-OTM preference is a mid-price artefact | [event_spread_2026-09-20.md](event_spread_2026-09-20.md) |
| Options With Ravish — super bull call spread (OTM debit spread) | **not tested** (2.5/5 on review 2026-09-20; mechanics correct, no selection rule; 3:1 payoff = the market's price for ~25% odds, not an edge; 2 vehicle tests queued §10) | `data/options_with_ravish/super_bull_call_spread_2026-09_review.md` |
| Paycheck To Portfolio — leveraged income system | **not tested** (1.5/5 on review; 2022 stress test queued) | `data/paycheck2portfolio/` |

## 10. Queued and discussed, not yet run

Everything that has a spec or a decision behind it but no result. **Status:** QUEUED (specced, run on
command) · PARKED (discussed, no spec or deliberately shelved) · SUPERSEDED (the question was answered
elsewhere or the strategy it served is dead). Rough cost in the last column.

### Queued — specced, ready

| test | what it would settle | status / where | cost |
|---|---|---|---|
| **Cheap-convexity overlay (the book's missing bear leg)** — buy SPY / QQQ puts 5–10% OTM, 60–90 DTE, ONLY when protection is cheap (VIX < 20 or low IV pct), roll; variant = put debit spread. Scored on the BOOK (straddle + bull put pair + breakout book), not standalone: blended t, max DD, worst month, cumulative carry. Real SPY/QQQ bid/ask from `options_daily_v3` (quotes end Jul 2026). **Must-pass: 2022** (slow bear with VIX already high = the gate may never fire). Rationale: sell premium when IV is high, buy it when low — the VIX<20 SPY-selling cell is negative, so that is when the hedge is cheapest (Burry lesson: buy protection when nobody wants it, survive being early) | whether a gated index-put overlay cuts the book's drawdown by more than it costs — the one bearish exposure that does not need us to pick shorts (single-name shorts and ETF bear calls both FAIL) | QUEUED 2026-09-20 | 1 day |
| **Stocks that hold up in a weak tape** — names within ~10% of their 52wk high while breadth is washed out (< 35% of the liquid universe above the 50 SMA), then forward return after breadth recovers vs the field; entry at the close / pullback, NOT the breakout. Pattern harness, `post` + `xname` controls | whether stock-level relative strength *conditioned on breadth* selects (O'Neil); distinct from the INVERTED group-level RS filter. FTD study hint: post-FTD names beat the field (+0.05–0.08R) but the breakout entry lost (−0.20R) → test the state, not the moment | QUEUED 2026-09-20 | ½ day |
| **Pre-earnings ramp on a 30–45 DTE tenor** — same trade as `run_earnings_ramp_test.py` but the back tenor instead of the front expiry | whether less theta beats a smaller ramp (term structure); the front-expiry version lost −3 to −14% at mid with theta > vega. The ramp analogue of the calendar back-leg test | QUEUED 2026-09-20, declined for now; one Athena pull, `earnings_ramp_2026-09-20.md` | 1 hr |
| **Cameron's "80% chance of doubling the loss after breaching max loss"** on Gabe's journal: for sessions whose intraday P&L first crosses a fixed limit (−$500 / −$1,000 / 1% NAV), what share closes at ≤ 2× the breach, vs sessions that touch half the limit and recover | whether a hard-coded daily loss limit belongs in the desk routine | QUEUED (Breitstein test 1), memory `project_breitstein_test_queue` | ½ day |
| **Margin expansion in the cost model** for short premium in high-IV regimes (`costs.py` has commission + 25% of bid/ask only) | whether the surviving put spreads / condors carry a hidden regime cost | QUEUED (Breitstein test 5), design note first | design note |
| **Roster friction audit** — every confirmed strategy at 25% and 50% of bid/ask crossed, ranked by edge that survives (each leg ≈ −1.5pp) | which Tier A/B rows are mid-price mirages | deferred by Gabe 2026-08-08, [RESEARCH_QUEUE.md](RESEARCH_QUEUE.md) | ½ day |
| **Delta-matched beta check on 30-DTE single-name selling** (positive, but no 30d premium exists in the VRP panel → likely direction) | whether the one positive short-dated cell is premium or beta | QUEUED, memory `project_vrp_shortdte_names` | ½ day |
| **VIX ≥ 25 equity-ETF put-spread exits** on the pooled panel (+4.5% train, +10.1% with uptrend; 2022 negative) | an exit rule for the high-VIX cell | QUEUED, research queue #3 | ½ day |
| **Long-dated double calendars / diagonals** (front ~49 DTE, back ~76, ~0.22Δ, mega-caps; My Trading Journey) — needs a 45–85 DTE pull, the cache caps at 40 | whether the calendar structure lives at a horizon the path study never covered | QUEUED, research queue #2 | pull + 1 day |
| **Anchored-VWAP trailing exit** as a seventh exit rule in the risk-architecture harness (anchor = highest-volume session of the trailing N days; exit on first close below); null = a fixed-lookback trend filter does the same | whether the volume weighting adds anything over `close < 50 EMA` | QUEUED, `data/lance_breitstein/PRINCIPLES.md` "Extracted test" | ½ day |
| **Right side of the V** — A/B the unconditional gap fade (left side) against the same fade after a turn trigger (break of prior bar high / trendline / MA) | his unifying concept; retro-explains the gap study | QUEUED, `principles/right-side-of-the-v.md` | ½ day |
| **In-play gate as range expansion RELATIVE to the name's own normal** (vs the absolute ADR ≥ 3.5% gate) | a cheap upgrade to the universe gate, no new data | QUEUED, `principles/in-play-stocks.md` | ½ day |
| **Capitulation blowoff short**: bar range ≥ 2× prior day AND volume ≥ 2× prior day after an accelerating run | the one mechanical rule in the capitulation write-ups | QUEUED, `principles/capitulation-and-trade-writeups.md`; ⚠ prior poor after tests 2–3 | ½ day |
| **FBO short lower-high gate** (MULN anatomy: drive above the level, fail, lower high, break VWAP) on the existing FBO detector | whether the lower-high condition sharpens the detector | QUEUED, `principles/muln-layup-anatomy.md` | ½ day intraday |
| **Qullamaggie partial-then-trail exit** (sell ⅓–½ on day 3–5, stop to breakeven, trail 10/20-day) vs our full 20 EMA exit — the earlier "fast trails lose" result tested a full exit, not his | a fair exit comparison on the precision tier | QUEUED, `principles/qullamaggie-system-relayed.md` | ½ day |
| **Sleeping Giants exit lever + IV-rank gate** (win 47%, median −9%, mean +59%: the exit is a second alpha) | whether the convex LEAP idea is tradeable at the median | QUEUED, memory `project_sleeping_giants` | 1 day |
| **Options-vehicle overlay on the precision tier** (Tito's 0.2–0.35Δ ≥ 15 DTE calls with sell-the-spike) on real prints | whether the vehicle study's "no vehicle fixes entries" holds for good entries | QUEUED, [daily_routine.md](daily_routine.md) open builds #3 | 1 day |
| **Paycheck To Portfolio 2022 proxy stress test** (high-beta leveraged-income book through 2022) | whether the system survives a bear year it has never seen | QUEUED on command, `data/paycheck2portfolio/` | ½ day |
| **Grader improvements** (not tests): zero-trade-day rows, time-block subscores 09:30–11 / 11–12 / 12–14 / 14–16, "easiest layup not taken" from the layer-2 day state | the report card Breitstein describes | QUEUED, do when touching `run_journal_grades.py` | ½ day |

### Parked — discussed, shelved or waiting on data

| test | why parked | where |
|---|---|---|
| **Intraday versions of the daily nulls**: Luk/Ariel EMA-pullback entry on 5/15-min bars, the 620 setup (6/20 EMA cross after a morning wash + VWAP reclaim), Adhikary archetype C (0DTE fade), counter-trend VWAP-veto arm | need minute data beyond the ~1-month 1-min cache; Stage A already priced the intraday trigger family at −0.10 to −0.13R; **don't fund Polygon history for these** | [daily_routine.md](daily_routine.md) #1–2, [pullback_entry_study_2026-09-17.md](pullback_entry_study_2026-09-17.md), `principles/trend-definition-and-counter-trend-entry.md` |
| **Tito precision-tier true OOS** (run the detector on 2023 + 2025, pull bars, re-test; current n = 17, selection-biased) | data pull | memory `project_tito_playbook` |
| **QQQ intraday project #2–6**: TQQQ rebalance flow, trend-day classifier by 10:00 (the one supervised-ML fit), and three more | Gabe: "make notes, we might come back" | [qqq_noise_band_replication_2026-09-17.md](qqq_noise_band_replication_2026-09-17.md), memory `project_qqq_intraday_ml` |
| **IBKR minute option bid/ask dataset** (4 GOOG expiries pulled) | paused 2026-08-21 by Gabe before scaling up | memory `project_intraday_option_quotes` |
| **Long-call strategy steps 3+** (step 2 found the gate horizon-specific, not pooled) | next step undefined | [call_strategy_project.md](call_strategy_project.md) |
| **Calendar path study open items**: stock sym35 double screener, rolling the short legs (campaign), Bull-HiVIX SPY dcal cell (+18%, unstable halves) | the structure has no edge on the clean run; only the SPY/IWM Tier B cells remain | [calendar_path_study.md](calendar_path_study.md) |
| **Steenbarger: "the index is very probably higher a month after a panic"** (index-level, distinct from the single-name crash veto) | low value; likely beta | memory `project_breitstein_test_queue` parked list |
| **"99.9% of charts are D"** vs the funnel's layer-2 pass rate | descriptive; measures our D-line looseness, not an edge | same |
| **No-news veto on fades** (4 independent statements: Breitstein ×2, Carter, tastylive) | needs a news/catalyst field; earnings proxy gave no support in test 2 | same, [breitstein_tests/boring_violent_2026-09-19.md](breitstein_tests/boring_violent_2026-09-19.md) |
| **Float as a universe variable** (Cameron: < 100M shares) | never tested; needs shares outstanding in the Polygon cache | `principles/ross-cameron-system-relayed.md` |
| **IPO lockup expiry (90–180d) event study**; overnight-momentum IPO strategy | structural blind spot (SMA200 + 400-bar minimums exclude every IPO); clean mechanical event, not yet built | `principles/ipo-strategies.md` |
| **Theta Profits next-best skeletons** (SPY dcal variants, ATM SPX put spreads) | none beat Gabe's own SPY dcal on the skeleton; low priority | `data/theta_profits/` |
| **Ariel Hernandez nightly-call scoring** (hit rate accrues per video) | bookkeeping, not a test | [daily_routine.md](daily_routine.md) #4 |

### Superseded — the question was answered or the strategy died

| item | why |
|---|---|
| Extend the put-calendar franchise to XLI / XLK / XLB / XLY / XLC / XLRE (Track 1, 2026-08-08) | the parent calendars are negative after costs and the calendar structure has no edge on the clean path study |
| oquants forward-factor calendar replication (research queue #1) | closed by the VRP panel: the 30→90 forward premium it reaches for is absent (t 1.45) |
| "More like CF + XLE" chain pull (research queue #4) | three wins at an 80% base rate; breach odds depend only on cushion in ADR |
| Tier-weighted risk (10× by grade) before buying minute bars | done as the size-lever study: exclusion wins, the spread does not |

## Verdict scheme (adopted 2026-09-20)

"Pass / fail" was losing information. A test has **two independent outcomes**: what it says about the
*idea*, and what it gave *us*. Rows carry one **VERDICT** and, where it applies, one or more **YIELD**
tags.

### VERDICT — what the evidence says about the idea

| verdict | meaning | what to do with it |
|---|---|---|
| **ADOPTED** | clears the bar (beats its honest control, both halves positive, \|t\| ≥ 3) and is live | it is in §0 and on the desk |
| **PARKED** | right direction, consistent across cells, **below the bar** | a live candidate; re-test when data or power improves — do not re-derive from scratch |
| **NULL** | tested at adequate power, no effect | settled. Do not re-run without a new angle |
| **INVERTED** | significant in the **opposite** direction | ⭐ actionable as a **veto**, not a null — the strongest kind of negative |
| **UNDERPOWERED** | direction unresolved and the sample cannot resolve it | **not settled.** Says what data would settle it |
| **RETRACTED** | previously reported, later found wrong | the old number is poison; say what was wrong |

### YIELD — what the test gave us regardless of its verdict

- **MECHANISM** — explains *why* something works or fails (friction not capping; 2.6 ADR of entry location)
- **METHOD** — a durable lesson about how to test (the best classifier is the worst gate; honest controls)
- **REFRAME** — changed the question itself (the breakout book is bimodal)

A NULL with a MECHANISM or METHOD tag was a **good test**. A row with no yield tag and a NULL verdict
was a dead end, and that is worth knowing too.

### Effective n, always

Report the **clustering unit**, not the trade count — they diverge by orders of magnitude and the trade
count is what fools you. 3,377 event spreads were **53 event dates**; 900 post-FTD breakouts were
**8 FTD episodes**; 27,523 retrace entries still only reached t 0.48. Where they differ, the row states
effective n and the verdict is set from it.

## Standing rules this index enforces

- A pattern test goes through `lib.studies.pattern_test` and lands in [pattern_ledger.md](pattern_ledger.md) with its random controls (`post` for timing, `xname` for selection; the pre-2026-09-19 `month` control has look-ahead). All 25 pre-2026-09-19 rows were re-scored against both honest controls the same day ([ledger_rerun](ledger_rerun/ledger_rerun_2026-09-19.md)): still 0 passes; quote the RERUN rows' `ctrl`/`edge`, never the `month` rows'. `post` is now the harness default.
- Path simulations settle at intrinsic and are checked on crash weeks before any number is reported (the calendar study's +20–40% was a truncation artefact).
- Gabe's own trades are conformance and cost evidence only, never setup evidence.
- New tests append a row here in the same session they land, with a VERDICT from the scheme above and effective n where it differs from the trade count.
- Rows predating 2026-09-20 keep their original wording until they are next touched; re-label on contact, not in a sweep (a bulk re-read would mislabel work whose context is not in front of us).
