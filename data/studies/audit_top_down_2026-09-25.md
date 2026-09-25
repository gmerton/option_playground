# Top-down audit — 2026-09-25

Three read-only passes (certified strategies → the operations that feed them → the discards), every number verified at the
primary study doc, not the TEST_INDEX row. Load-bearing claims were re-checked a second time by hand before this was
written. Nothing was changed in code or in the ledger by this audit; the "action" lists are proposals.

---

## Part 1 — The certified book

| strategy | summary-layer claim | what the primary doc supports | verdict |
|---|---|---|---|
| **Index stress bucket** (SPY bull put 0.25/0.15, 20 DTE, 50% take, no stop; SPX condor; regime = below 50MA & VIX ≥ 20) | SPY t 6.1, SPX 5.2, "one bucket" | SPY 75 trades / 37 months, +6.76% net, t_month 6.07, 8/9 years; SPX 71 / 36, +9.82%, t 5.21. **But the independent unit is ~11 stress episodes**, one of them (2021-09→2023-03) carries 43% of trades; SPX ex-2020 & 2022 is **t 2.75**; SPY/SPX monthly correlation only 0.11. No delta-matched long-SPY control at the same entry dates exists. SPX sample silently starts 2018 (the VIX cache used begins 2018-01-08), so the 2016-Q1 stress episode is untested. | **HOLDS, scope weakened.** Still the strongest claim in the book. Settling test: episode-clustered t with a delta-matched long-index control on the same Fridays, 2016 included via `vix_daily_long`. |
| **House breakout** (precision tier, close entry, day-low stop on the close, 20-EMA exit) | MARGINAL-PASS +0.4R, t 3.3 | The only cell over the bar (vs a random other name, +0.44R t 3.52) measures breakout-vs-random-survivor on a 2026-survivor panel. Every angle that removes one confound is null: timing vs the same name later +0.28R t 2.89 with the first half −0.01; month-weighted t **−0.04**; out-of-sample refit NULL; 0/9 gates earn their place; 2024–26 = 54% of trades and ≈87% of R. | **DOWNGRADE to "uncertified selection, regime-dependent".** Keep trading it small; stop calling it certified. Settling test: point-in-time universe (chain_spot incl. delisted), control = same-date NON-tier breakouts, per-year paired edge. |
| **7-DTE long straddle** (Friday, FVR ≥ 1.20, IV pct ≤ 30, RSI < 70) | IN BOOK as half of the pair; MTC "CONFIRMED t 3.7" | The 3.7 is per-trade over overlapping Friday entries. At the honest unit: **monthly t 1.8, date-clustered 0.83** (335 dates). Top 1% of trades = 91% of the return (100% in the DTE re-run); ex-top-1% ≈ 0. The +6.73% headline has no t and carries +1.3pp of stale-print settlement. The pair that justified IN BOOK lost its put leg on 9/24. FVR and IV thresholds are in-sample; only RSI was walk-forwarded. Friday-only was the original 2026-03 rule (not post-hoc). | **DOWNGRADE to PARKED / UNDERPOWERED, token size.** Today's 9 straddles are fine at their size; do not scale. Settling test: date-clustered gated-minus-unconditional same-Friday pool, parity-settled, per-year. |
| **GEX regime** (negative dealer gamma → +8% realised vol) | PASS t 7.7 | Verified: NW t 7.71, both halves t 4.6 / 6.0, holds inside every VIX tercile, no look-ahead (OI is prior-close). Note: the *registered* pin test was INVERTED (t −4.2); "no pin" is the post-hoc diagnostic. | **HOLDS.** |
| **GEX SPY 1-day fly** (2× wings, positive-gamma days) | PASS t 3.4, paper trading | Verified n 928, +5.8%, t 3.4 (month-clustered 3.56), 14/17 years. **Weekday-only entries are +4.9% t 2.46**; the pass needs the 211 Fri→Mon entries (+8.9%). "Max loss ≈ $290" is the median; worst −$709. Charged k = 2 for ≥ 7 dependent cells on the same days. The underlying finding is the short straddle (+13.7% t 5.6); the fly is its defined-risk wrapper. | **WEAKENED.** Keep the paper trade, report weekday and Fri→Mon separately, do not size. |
| **VRP panel** (iv − realised, 10d) | t 8.93, 17/17 years | Verified, but it is **vol points, gross, no costs, a mechanism** — 10/17 years clear individually; the tradeable stage-two (10-DTE single names) is net-negative. | **HOLDS as mechanism only**; must not sit beside tradeable "confirmed" rows. |
| **Paid-to-wait put spread, IV ≥ 60th pct gate** | +5.7% net, "the tested gate" | Gated cell n 129, **t 1.53**; gated − ungated +16pp t 2.29 on 37 months; NOT CERTIFIED at k 6. Ex-2025 (n 81) the gated cell is **−0.26%**. The up/B+ exclusion is post-hoc. The live scan (`run_putspread_scan.py`) is **not** the tested rule (leaders not SETUP, an extra untested IV/RV ≥ 1 filter, mid credit, hard-coded expiry). A live DINO spread opened 9/16 sits in this family. | **DOWNGRADE to UNDERPOWERED / paper only.** CLAUDE.md and OPERATIONS.md call this "the tested gate"; it is neither certified nor what the script runs. |

**Cross-cutting.** (a) "One bucket" is a regime statement, not a P&L one (SPY/SPX corr 0.11). QQQ's stress cell (t 3.53, same month-weighted return as SPY) fails only the k = 54 charge; it is the same bet, so nothing to revive — but the Friday screener sizes it as "S" while the ledger says NOT CERTIFIED. (b) Nothing certified depends on the ETF-roster put leg; what depended on it was the straddle's IN-BOOK status and the "pair" rows, which are now stale. (c) The book's honest state: **one certified strategy (the index stress sale), one certified mechanism (GEX regime), everything else uncertified or parked.**

---

## Part 2 — Operations that feed those strategies

Severity: HIGH = a live signal is wrong or missing; MED = wasted quota / misleading output; LOW = cosmetic.

| sev | where | finding |
|---|---|---|
| HIGH | `run_friday_screener.py` | **No emitter for the SPX condor** — half the certified bucket is never screened live. **XLE still carries tier "A"** (ledger: blocked / not reproducible) and emits ENTER. Tier S/U is a label only: uncertified cells (SPY bullish-high-IV, QQQ bullish-low-IV t −0.87, …) still print ENTER + sizing. QQQ Bearish_HighIV tagged "S". |
| HIGH | `src/lib/interface/breakout_lambda.py` → `premarket_watchlist.run_eod_scan` | The cloud EOD breakout scan **does not implement the house spec**: Stage-2 MAs, EMA 9>21>50, optional ADR ≥ 3.5, tight-base pivot, vol ≥ 1.5× on the 46-name INT list. None of ADR 4–7 / 15% off high / 10-20-50 stack 5–40 / RVOL 1.1. daily_routine step 3 tells you to act on its POTENT rows. |
| HIGH | `run_adhikary_scan.py:65-84` | RVOL pro-rating is linear (`mins/390`) while volume is U-shaped: at 15:30–15:40 ET RVOL is understated ~10%, so the desk's own A block misses 1.1–1.2× breakouts. Today's 4 → 0 between 13:54 and 15:28 was this artefact. Fix: `volprofile.vol_frac(mins)`. |
| HIGH | `run_build_liquid_panel.py` + `daily_desk.sh` | The panel drops today's bar when built before 16:30 ET; the desk builds it at ~15:40, so **the panel is always one session short** and the scan stamps the live row after a D−2 bar (chg%, pivot, SMA stack, avg volume all miss D−1). Same lag hits `run_putspread_scan.py`, `run_scan_clusters.py`, `run_trailing_retro.py`. |
| HIGH | `run_straddle_screen.py` IV gate | Live gate = IBKR 30-day composite vs its own history; the study gated ~10-DTE ATM put IV. The Athena fallback ranks today's iv30 against a stale `iv_put_10` history that ended 2026-02 — cross-tenor and 7 months old — and it kicks in silently per name (today: 101/331 names). |
| HIGH | `src/lib/alerts/grading.py`, `run_journal_grades.py` | Entry grades reward a 09:41–12:00 window and "alert-following" speed; the ledger's best entry is the close, and intraday triggers are null. A close-of-day buy grades C. |
| MED | `run_putspread_scan.py` | Universe = leaders (study: SETUP names); extra IV/RV ≥ 1.0 filter from one observation; expiry hard-coded 2026-10-16; credit at mid; earnings flag claimed in the docstring but absent. |
| MED | `run_straddle_screen.py` | No Friday guard (`STRADDLE=1` archived a Thursday run as a Friday record); partial runs print QUALIFIERS with no banner and the desk's `sed` hides the error count. |
| MED | `start_alerts.sh` / `lib.alerts.universe` | Reads the local `preferred_tickers.txt`, not S3 → stale whenever the desk did not run; `levels.csv` still arms a 9/09 OKTA hand level; `universe_short.txt` is from 9/13. |
| MED | `daily_desk.sh` | Every step's stderr → /dev/null (a traceback reads as "no signals"). The alert scorecard runs at 15:40, so `close` = the 15:40 bar and the all-days file holds partial-session results. The 19:15 Lambda branch is never taken (desk runs first), so step 3 rescans on a partial bar with no pro-rating. |
| MED | dead weight | The intraday detector suite (UR/ORB9/LVL/BIR) runs all day though every one is null or inverted vs a random minute; its only live value is the scorecard sample and the grader's alert matching. Premarket gaps/industries: unvalidated vetoes, context only. Adhikary B/C blocks: no edge (B rows still stream into tomorrow's universe). |
| OK | cloud | Local code = deployed code (clean diff vs origin/main); Adhikary precision flag matches the study definition; the GEX paper trade matches its spec. |

---

## Part 3 — Discards: were we too hasty?

The 9/24 slippage re-check was done at the right bound (0.20 of the spread, arrival-based). **No discard is a cost false negative**; scaling the Tier-U set to 0.13 lifts nothing to t 3 (GEV would, but its problem is beta, not costs). The near-misses are **power and holdout** cases, and most now have free data.

### List A — worth re-examining (ranked; p = honest chance of passing |t| ≥ 3 both halves)

| # | row | original | named defect | corrected test | data / cost | p |
|---|---|---|---|---|---|---|
| 1 | QQQ noise-band momentum, negative-gamma days | t 2.92, halves +1.2 / +6.3 | one cell, own-GEX gate when the confirmed mechanism is SPY GEX; queued dose-response never ran | GEX-quintile dose-response + VIX control; SPY-underlying replication | local, < 1 h each | 0.25 |
| 2 | Four near-bar equity rows on the unused 2010–19 holdout: earnings drift good+muted (**t 3.17, 8/8 yrs** vs xname), breakout in HYB-A (t 4.15 vs post, back-loaded), HYB-B universe (t 2.6), breakout-activity gate (t 2.59) | parked for a 2027 lockbox | `liquid_panel_2009` is an out-of-time holdout nobody has used for these | pre-registered 2010-01→2019-09, xname AND post, per-year | local, ~1 h each | 0.30 / 0.25 / 0.25 / 0.15 |
| 3 | Event convexity (calls before FOMC / elections) | 2019→ only, Welch t 1.96 on 53 dates | v3 covers 2010→: ~80 more FOMC decisions, 5 more elections | 2010–19 holdout, 0.25Δ only (0.12Δ was a mid artefact), real fills | **Athena ~40 min + 1 h → ask** | 0.30 |
| 4 | QQQ 1-day 2× fly | t 2.55, first half −5.05% | the failing half is the pre-2016 era when QQQ barely had daily expiries; 2016+ +8.1% (n 599), 2018–26 t 3.5 | re-cut at 2016 on BOTH tickers, halves at 2021, charged as a second look; certify via the paper trade | local, < 1 h | 0.45 (to "supported", not certified) |
| 5 | Paid-to-wait IV ≥ 60 gate | n 129 because IV was known for 18% of events | `options_iv_daily` now covers all 1,548 spreads; events extend to 2010; no delta-matched control ever run | gated − ungated AND vs delta-matched stock, SETUP universe, per-year | local ~1–2 h | 0.20 |
| 6 | Sector-momentum 12-1 as the bear leg | hedge survives de-meaning; fails "Sharpe must not fall"; only 4 bear episodes, 2000–02 fails | the bar is unmeetable for a zero-mean hedge; episode count is the real limit | Ken French industry returns 1926→ (~10 bear episodes); bar = positive in ≥ 7/10 with the DD cut | local 1–2 h | 0.40 for the hedge property; ≈ 0 for return |
| 7 | P2 "buy the dip in an uptrend" | t 4–5 on survivors; −0.88 t −3.8 close-only | definition fragility, unresolved | run close-only defs on the survivor panel's own adjusted closes to isolate price-source vs definition; only then ALL/NONSURV on chain_spot | local, minutes | 0.15 |
| 8 | 30/15Δ call debit spread vs delta-matched stock | +$97 t 2.29; down months t 2.45; SPY < 200 SMA cell t 1.25 on 18 names 2019→ | sample; v3 has 2010→ (3× the down-market months) | same test 2010→ | Athena ~20 min + 1 h → ask | 0.20 |
| 9 | Single-name short family on the survivorship-free series | offering short −0.67pp/60d t −1.85; CRASH-H t −1.28 | delisted names are absent and are a short's best outcome | ALL vs NONSURV on `chain_spot_daily` (closes only) | local ~2 h | 0.15 |
| 10 | Sleeping Giants | arm B t 2.76 n 81, hand-picked universe, 13 exits tried in-sample, IV gate never built | universe and gate | point-in-time S&P 500 universe, `options_iv_daily` gate, top-5 share | Athena ~1–2 h → ask | 0.15 |

Also noted, low rank: post-FTD names as an exposure state (n 8 episodes → ~20 on the 2009 panel, p 0.15); earnings vol premium killed at 0.5 of the spread (interpolates to ≈ +0.5% t 1.4 at 0.20 — the limit is 2019→ only; p 0.10); GEV bull put (t 3.55 at 0.20 but 2024+ only, 60-cell sweep; the honest test is vs delta-matched GEV stock, p 0.10).

### List B — confirmed dead, do not revisit
ETF roster bull put leg (gross reproduces; net ≈ 0 even at 0.13; the edge was long beta) · calendar family (erratum correct; clean re-run t 0.5 ETFs, −8…−18% stocks) · retrace entry (t 0.48 on ~1,700 dates; three later tests agree) · ADX ≤ 12 (holdout done correctly, t 1.49) · RV spread (INT-driven, empties in crashes, not a hedge) · 21-DTE management (risk reducer only, t −2.4) · Stage A / intraday suite (control is fair — random LATER minute holds the name fixed and is handicapped by drift, and the triggers still lose; ORB9 t −8.5) · UR band sweep (84% of entries outcome-selected) · EMA pullbacks (t ≤ 1.4; the intraday version is the queued 620 test) · Tito spike exit (every arm loses; risk lever on a losing vehicle) · Kell wedge pop · VCP damped sine · CW put-call IV spread (−0.4pp, halves disagree, no forward window) · sector momentum as a return · Tier-U spreads other than GEV · 10-DTE single-name selling · spin-offs (adding the missing 228 lowers the mean) · theme co-breakout, buyback, gap share, PEAD tape (all ≤ t 2.3 and confounded) · weak-tape leaders, beaten-down beats, insider clusters, tax-loss, deletions (fail even on a survivor panel) · post-shock vol, FOMC daily, index-add, FTD index, distribution days, TOM, UUP/UVXY/UVIX, 1-DTE straddle, PMCC · HTF / Mari / dilution fade (still blocked: no small-cap OHLCV).

---

## Summary-layer corrections (docs only; none applied yet)
- `TEST_INDEX.md` §0 rows 1–2: the pair / Tier A-B rows are stale (5 of 7 cells NOT CERTIFIED 9/22; the put leg net-negative 9/24). Row 17: "both halves positive" is wrong for the breakout's timing cell. Row 36: paid-to-wait lacks NOT CERTIFIED. Row 61: "$290 max loss" is the median; weekday-only t 2.46 omitted. Row 388: paper trade started 9/24, not 9/22.
- `CLAUDE.md` / `OPERATIONS.md`: "run_putspread_scan.py carries the tested IV ≥ 60 gate" — the gate is uncertified and the script does not implement it.
- `capital_allocation_framework.md`: Tier A/B labels still shown under the banner.
- `spx_strangle_playbook.md:98`: "2016–2025, 10 years" → the sample is 2018–25.
- `paid_to_wait_study.md:5,18`: window ends 2026-02, not 2026-05.
- memory `reference_strategy_data.md`: straddle IV-pct gate is ≤ 30, not ≤ 20.
- `run_friday_screener.py:248`: QQQ Bearish_HighIV "S" → U (same bet, but the label is wrong).

## Proposed order of work (for Gabe to confirm)
1. **Operations, HIGH rows** (an afternoon): SPX condor emitter or an explicit "SPY-only" note; XLE tier → blocked; U tier suppresses ENTER; `vol_frac` in the scan; build the panel after 16:30 or top up D−1 before stamping the live row; Friday guard + error banner on the straddle screen; fix or disable the Athena IV fallback; grader stops rewarding the 09:41–12:00 window and alert-following speed.
2. **Ledger honesty** (an hour): apply the corrections above; relabel the breakout, straddle and paid-to-wait rows.
3. **Cheap re-tests, local** (List A #1, #2, #4, #7, #5, #6): ~6 h of laptop time total, pre-registered one at a time.
4. **Athena re-tests** (#3, #8, #10): ~1–3 h of Athena — ask before running.
5. **Settling tests for the two certified claims**: episode-clustered stress bucket with a delta-matched control (local, the trade files exist); breakout on a point-in-time universe (needs chain_spot masks).
