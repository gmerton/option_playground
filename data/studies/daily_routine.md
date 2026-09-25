# Daily routine — what to run, what to act on

*2026-09-08. Turns the September studies into a fixed sequence. `daily_desk.sh` runs steps 0–5 (incl. 1b open book) and writes to `data/watchlist/`. Every number a scanner prints is descriptive of the current tape; the validations say which parts carry expectancy.*

## Evening (15:45 ET for a live read, or after the close)

| step | command | act on | ignore |
|---|---|---|---|
| 0 GEX fly paper trade | `run_gex_fly_paper.py --close` (from 15:30 ET; idempotent) → `data/paper/gex_fly_signals.csv`, `gex_fly_trades.csv` | nothing tonight — it settles due flies and logs a paper fly when SPY gamma is positive; the forward sample is reviewed after ~6 months / ~100 flies ([gex_spy_ironfly_2026-09-21.md](gex_spy_ironfly_2026-09-21.md)). A skipped evening is a hole in that sample | the day's single fly result |
| 1 Regime | `run_trailing_retro.py` | the state line (SPY trend × breadth) — it selects which row of each study's conditional table applies today | the trailing style spread and "what worked last 30 days" as forecasts (no persistence, `trailing_regime_validation.md`) |
| **1b Open book** | `run_position_monitor.py --live` → `data/watchlist/positions_<date>.txt` | **anything tagged `<<< EXPIRES` (≤2 DTE)** — decide close/roll/let-expire tonight, not at the bell. The 7-DTE straddles and the bull put block are the evidenced pair: check both are still on and roughly balanced. `EXPIRED, reconcile` = a leg past expiry still showing open | the net P&L line as a performance read — it is a mark, not a decision, and the stock legs dominate it. ⚠ one (underlying, expiry) cell can merge two unrelated positions into one odd-looking row |
| 2 Adhikary scan | `run_adhikary_scan.py` → `alerts_latest.csv` | **SETUP rows with `precision=YES`**: set a buy-stop at the pivot. A-block rows with `precision=YES` that broke today on a close in the upper half | B catalysts (no validated edge); the C block (daily bar is a continuation signal, never short it) |
| 2b Live alert monitor (market hours) | `./start_alerts.sh` (wraps `run_universe_monitor.py`) on the auto universe (`lib.alerts.universe`: preferred list + holdings + evening scans + fresh plan/creator lists; the hand-edited `universe_focus.txt` was retired 2026-09-24) → terminal/dialog + `data/watchlist/logs/universe_alerts_<date>.log` | **UR** = flush (≥0.25 ADR from max(open, prev close)) that undercuts the prior-day low or tags/opens below the 9/21 EMA, then a 1-min close back above VWAP → stop = session low. **ORB9** = opened and held the daily 9 EMA + VWAP, 5-min close above the 15-min opening-range high before noon → stop = OR low / bar low. **Pre-market hot industries** (2026-09-14): `run_premarket_industries.py` (run by start_alerts.sh before the bell) ranks every sector/industry ETF and the universe's groups by the pre-market move in ADR units with member breadth and the ETF's daily state; HOT = ≥1.5 ADR or ≥2/3 of members ≥0.5 ADR the same way. Context, not a gate: a leading group un-gates ORB9 on its names, names gapping ≥1 ADR get re-classified at the first bar, and on a gapped-down group the reclaim that pays is after 09:40. **Mid-session restarts** (2026-09-14): the monitor seeds every book from today's 1-min bars before streaming, so VWAP / opening range / session range / the gap re-classification use the true open (before the fix a restart rebuilt them from the restart minute). **GAP re-classification** (2026-09-14): at the first bar, an open ≥1 ADR from the prior close re-runs the daily in-play state with the open as a provisional close (`GAP` lines in the log; a gap-down on a day-SHORT name is left alone, that is the crack) — TER/MRVL/LITE/DRAM/SNDK 9/14 went LONG → SHORT at 09:30 and their reclaims were saved, not shown. **LVL** = first 1-min close through the 15-session pivot (or a hand level from `data/watchlist/levels.csv` / the Adhikary scan's buy-stop rows) above VWAP on ≥1.1× volume pace, 09:45–15:30, not once price is >0.5 ADR past the level → stop = level − 0.5 ADR; tagged PRECISION for the validated Adhikary cohort (ADR 4–7%, within 15% of the 52wk high, SMA stack 5–40d) and CATALYST-SIZE (gap ≥5% / day ≥8% = B archetype, no edge). A day-OUT "no room" name counts as LONG for LVL (the break resolves it). **BIR** (short) = name below its 9/21 EMA bounces ≥0.4 ADR into a level above (9/21/50 EMA, 50/200 SMA, PDH), first 5-min close below the prior 5-min low → stop above the bounce high. **FBO** (short, every name) = a 5-min close above the prior-day high or 15-min OR high, then a 5-min close back below it and VWAP within 90 min of the high → stop above the failed high; on a long-universe name it is also the exit tell. Short universe = `universe_short.txt` + long-list names below their 9/21 EMA. Read the tags before acting: `still below 9 EMA`, `light vol`, `GAP ≥1 ADR`, `stop in noise` (<0.4 ADR), `SPY vs VWAP` and the ADR-vs-21-EMA number are the lens gates; `--index-gate` mutes longs under / shorts over the index VWAP | Alerts are pattern hits, not entries: on 9/8 the same UR fired on SPCX/TXG/TGTX (worked) and OKTA/RVMD/ILMN/MSFT (failed). Replay any day with `--replay YYYY-MM-DD SYMS` |
| 5b Process report card | `run_journal_grades.py` → `data/studies/journal_process_grades.md` (+ csv) | Read the GRADE, not the P&L: entry quality (share of discretionary entries reviewed good), stock same-day round trips, fills, too-soon exits, vehicle doubling. A = the rules held; D = they did not. First thing on the desk next morning | Aug-Sep 2026: 20 of 26 sessions graded D; the score has ~zero correlation with day P&L (P&L is the option book + beta), which is the point: the grade is the signal, the P&L is noise |
| 3 Preferred-list breakout scan (CONTEXT, not the house spec) | `run_preferred_breakouts.py` / the `preferred-breakout-eod` Lambda | nothing on its own. It is a Luk/Qullamaggie-style screen (Stage-2 MAs, EMA 9>21>50, tight-base pivot, 1.5× volume on the INT list), **not** the precision-tier breakout; relabelled 2026-09-25 (top-down audit). The house signal is step 2's `precision=YES` rows | its POTENT / "confirmed" rows as buy signals, and the old band rule (≤1 ADR over the 21 EMA), which the 9/25 band test did not support |
| 4 Straddles (Fri) | `run_straddle_screen.py` (rev 2026-09-16: Tradier data, IBKR for the IV percentile, so open TWS first; `--data-source ibkr` if the Tradier quota is out) → `data/watchlist/straddle_screen_<date>.txt` + dated CSV archive. `run_straddle_iv_gate.py` stays as a manual cross-check of gates 3+5 from option prints | names passing FVR ≥1.20 **and** IV percentile ≤30 **and** RSI(14) <70 (`passes_all`, added 2026-09-16) **and** worst bid-ask ≤25% / OI ≥50 | full-size FVR ≥1.40 prints on thin chains (AMLP/ANVS-type artifacts); RSI ≥70 qualifiers — extended names lose on the put leg (`rsi_conditioning_study_2026-09-16.md`) |
| 5 Journal | pending notes list | add same-day notes for every trade (`add_pending_note`) so the morning chain can grade them | — |
| **Morning 8:00 PT (launchd `com.gmerton.morning-journal`)** | `morning_journal.sh`: Flex pull (retries while IBKR's statement is not ready) → `run_build_reviews.py` (review rows from the rubric + exit classifier, attaches staged notes) → `run_journal_grades.py` → `run_trade_review_pages.py --no-charts` → `deploy_trade_journal.sh` (S3 + CloudFront) | read the process GRADE and the hosted journal; `./morning_journal.sh --no-deploy` for a manual re-run; logs in `data/journal/logs/` | — |

## Entry rules for every long — with their evidence (relabelled 2026-09-25)

> ⚠ Most of these came from the **August 2026 journal lens**, i.e. Gabe's own trades, which are **not admissible for
> setup selection** (CLAUDE.md working rules). Each rule now carries its provenance. **UNVALIDATED** = journal only:
> follow it as a habit if you like, but do not treat it as an edge, and do not build on it. **CONTRADICTED** = the
> panel says otherwise.

1. ⛔ **NOT SUPPORTED (tested 2026-09-25) — Location band** (within 1 ADR of the 21 EMA). *Source was the August journal
   only.* Panel test `band_runaway_entry_2026-09-25.md` (2,862 mornings, 2010→2026): closes bought 1–2+ ADR over the
   21 EMA returned +1.34%/20d vs +1.44% in-band; open vs close vs house rule all within 0.3pp (t ≤ 1.1). Don't skip a
   precision-tier close for being extended, and don't rush in at the open either. The close stays the default for its
   stop (the day's low), not for extra return.
2. ⚠ **UNVALIDATED — No gap-up buys** (≥3% gap, first hour). *Source: August journal.* The panel shows catalyst gaps have
   no edge (Adhikary B, DR-EP), but has never tested the veto itself.
   **PARTLY SUPPORTED — No buying below falling EMAs.** *Journal (laggard bounce −$3.8k) plus panel:* crash-leader veto
   (never buy deep drawdowns in a healthy tape) and the Trend Template ablation (close > 150/200 SMA carry the weight).
3. ⛔ **CONTRADICTED — "Trigger, not anticipation": a reclaim with the reclaim bar's low as the stop.** The panel says
   **buy the close**: entry study 2026-09-17, reclaim + re-entry −2.28pp vs the close (t −3.4); Stage A: intraday
   triggers ≈ a random later minute. Alerts are information, not triggers.
4. **RISK POLICY, not an edge — Stop ≤2% or size down to it.** Size = risk ÷ stop distance; never widen. *Journal
   ($13k past 2%).* The stop-distance cell failed as a grade on the panel (size-lever study); keep it as sizing hygiene.
5. ✅ **SUPPORTED — No same-day exits unless the stop is hit.** Panel **and** journal: exit-timing study, scalp −0.13R vs
   trail +0.89R; 278 same-day cycles −$8.3k at 19% win. Execution behaviour, which the journal *is* valid evidence for.
6. **WEAK — Vehicle follows entry quality:** clean pullback + IV <60% → stock (or ITM 45+ DTE call); extended or
   IV >60% → 30/15-delta put spread; never a 9%-OTM 3-week call held a day. *August descriptive + panel:* breakout put
   spread vs house stock NULL, leaning stock (t −1.77).
7. **PARTLY SUPPORTED — Exits:** grind → first daily close below the 20 EMA. Spike (option 3× in days) → sell into
   strength: **NULL as a return lever** on real call prints (t +0.18); it only trims the tail, so it is a risk choice.

## Monthly

- `run_trade_lens.py --start --end --out …` — score the month against the Luk/Tito rules; compare to August (`august_2026_luk_tito_lens.md`).
- Re-run `run_regime_validation.py` and `run_adhikary_validation.py` so the conditional tables include the newest regime. (The long-history panel they read, `run_build_liquid_panel.py`, is refreshed nightly by `daily_desk.sh` step 2c — do not run it by hand.)
- Re-read the conditional row for today's state before trusting any pooled number (feedback: weight current conditions).

## Open builds, in priority order

1. Intraday 620 / VWAP-reclaim logging in `ibkr_bot/fade_watch.py` (Ariel's trigger; the only untested entry layer).
2. Intraday C-archetype (0DTE fade) test — needs minute data; the daily proxy is refuted.
3. Options-vehicle overlay on the precision tier (his 0.2–0.35Δ ≥15 DTE rule) with sell-the-spike, on real prints.
4. Score Ariel's nightly calls (`data/ariel_hernandez/analysis/`) — hit rate accrues per video.


### Friday: stock double calendars / diagonals -- ⚠ ON HOLD 2026-09-16
The study behind `run_stock_dcal_screener.py` had a path-truncation bug (see `calendar_path_study.md` erratum); on the clean ETF re-run no calendar / diagonal / condor has an edge. The clean stock run (2026-09-16) shows every structure losing 5–18% per trade on single names; the screener is RETIRED. Do not act on its output. The IWM / QQQ / SPY double-calendar entries were removed from the Friday screener the same day.
