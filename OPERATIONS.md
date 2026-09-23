# OPERATIONS — what to run, when

*Map of the 9 shell orchestrators + the handful of scripts you drive by hand. Written 2026-09-22.*
*Rule: **if an orchestrator calls it, you never call it yourself.** Sub-bullets are steps, not commands.*

**Every command below assumes:** repo root, `.venv/bin/python3` (system python3 lacks packages), `PYTHONPATH=src`.
**Secrets live in `~/.trading_env`** — `source ~/.trading_env` first, or use a shell whose profile did.
`daily_desk.sh` / `journal_day.sh` do *not* source it; `start_alerts.sh` and `morning_journal.sh` do.

---

## Daily, pre-market (your morning, PT)

**1. `morning_journal.sh` — AUTOMATED, 08:00 local daily. You read it, you don't run it.**
```bash
./morning_journal.sh                 # manual re-run only (--no-deploy, --charts)
```
- Scheduled by launchd: `~/Library/LaunchAgents/com.gmerton.morning-journal.plist` (confirmed running — logs in `data/journal/logs/morning_<date>.log`, 9/18–9/22 present; weekend guard exits early).
- Produces: yesterday's journal + the published site → `data/journal/<date>.md`, `data/journal/days/`, `data/studies/journal_process_grades.md`, and https://d1z4hclel0mtsn.cloudfront.net/
- Steps: `run_daily_journal.py` (Flex pull, retries 6×10min while IBKR's statement isn't ready) → `run_build_reviews.py` → `run_journal_grades.py` → `run_trade_review_pages.py --no-charts` → `deploy_trade_journal.sh`
- Env: `IBKR_FLEX_TOKEN`, `MYSQL_PASSWORD`, `TRADIER_API_KEY`, `AWS_PROFILE=clarinut-gmerton` (all from `~/.trading_env`)
- **Skip it:** no process grade, no updated site, and the review rows for that session never get built — the day silently drops out of the journal.

**2. `market_conditions.py` — optional regime read before the bell**
```bash
TRADIER_API_KEY=... PYTHONPATH=src .venv/bin/python3 market_conditions.py
```
- Produces: printed regime / index scoreboard / sector + industry RS / position radar. Terminal only.
- **Skip it:** nothing breaks; `daily_desk.sh` step 1 covers the regime state each evening.

---

## Daily, during session

**3. `start_alerts.sh` — launch ~06:25 PT / 09:25 ET, leave running until the close**
```bash
./start_alerts.sh                # focus universe (data/watchlist/universe_focus.txt + today's plan)
./start_alerts.sh --full         # preferred-list union
./start_alerts.sh AMD LITE       # explicit symbols
```
- Produces: graded intraday alerts in the terminal (with chime) → `data/watchlist/logs/universe_alerts_<date>.log` and `data/journal/alerts/<date>.json`, published to `alerts.html` on the site.
- Steps (all auto, in this one terminal): loud env preflight → `run_premarket_gaps.py` + `run_premarket_industries.py` (only if before 09:30 ET) → `run_pnl_alarm.py` in background (`PNL_ALARM=0` to skip; needs TWS open) → `run_gex_fly_paper.py --open` at 09:45 ET → `run_universe_monitor.py --sound`
- Env: **`TRADIER_API_KEY` required** (hard fail). `AWS_PROFILE` optional — without it the monitor auto-adds `--no-publish` and alerts stay terminal-only.
- **Skip it:** no intraday triggers, and `data/journal/alerts/<date>.json` is missing, so this evening's `run_alert_scorecard.py` has nothing to score — that day is a permanent hole in the alert sample.

---

## Daily, post-close (evening)

**4. `daily_desk.sh` — run ~15:45 ET for the live read, or any time after the close**
```bash
source ~/.trading_env && AWS_PROFILE=clarinut-gmerton ./daily_desk.sh
STRADDLE=1 ./daily_desk.sh        # force the Friday-only straddle screen
```
- Produces: the whole evening desk → `data/watchlist/` (`regime_<date>.txt`, `positions_<date>.txt`, `adhikary_<date>.txt`, `clusters_<date>.txt`, `straddle_screen_<date>.txt`, `alerts_latest.csv`).
- Steps: pulls `minervini_matrix.parquet` + `preferred_tickers.txt` from S3 first (both were found badly stale in Sept — do not bypass) → `run_gex_fly_paper.py --close` → `run_trailing_retro.py` (regime) → `run_position_monitor.py --live` (open book) → `run_adhikary_scan.py` → `run_build_liquid_panel.py` + `run_scan_clusters.py` → `run_preferred_breakouts.py` → `run_straddle_screen.py` *(Fridays only)* → pending-notes list → `run_journal_grades.py` → `run_alert_scorecard.py` (+ `--oop`) → `lib.alerts.universe` (tomorrow's focus list)
- Env: `AWS_PROFILE`, `TRADIER_API_KEY`, `MYSQL_PASSWORD`. TWS/Gateway open on Fridays for the straddle IV-percentile gate (`IB_PORT=7496` live / `4002` paper).
- **Skip it:** no `universe_focus.txt` for tomorrow (so `start_alerts.sh` watches a stale universe), expiring positions go unreviewed, and the GEX fly paper trade misses a settle.

---

## Weekly / periodic

**5. `run_friday_screener.py` — Fridays, the ETF credit-spread roster**
```bash
TRADIER_API_KEY=... PYTHONPATH=src .venv/bin/python3 run_friday_screener.py
```
- Produces: per-strategy ENTER/SKIP verdict, terminal only. Actively maintained (7 spreads retired 2026-09-22).
- **Skip it:** nothing breaks. ⚠ Per memory, **all 13 remaining entries are Tier U** — token size only.

**6. Thursday bull-put screens — two scripts, one job**
```bash
IB_PORT=7496 IB_ALLOW_LIVE=1 TRADIER_API_KEY=... PYTHONPATH=src:. .venv/bin/python3 run_putspread_scan.py
```
- **`run_putspread_scan.py` is current** (2026-09-18, carries the tested IV≥60th-pctile gate). Produces a single-name bull-put candidate list, terminal + `data/watchlist/`.
- **`run_thursday_screener.py` is superseded** by it — same trade, no IV gate, and ungated is −3.3% net.
- **Skip it:** no bull-put candidates; the straddle/bull-put pair goes one-legged.

**7. Monthly — long-history re-validation**
```bash
PYTHONPATH=src .venv/bin/python3 run_regime_validation.py
PYTHONPATH=src .venv/bin/python3 run_adhikary_validation.py
PYTHONPATH=src .venv/bin/python3 run_trade_lens.py --start <d> --end <d> --out <f>
```
- Produce: refreshed conditional tables in `data/studies/`, and the month scored against the Luk/Tito rules.
- Note: `run_build_liquid_panel.py` used to be the manual monthly prerequisite — **`daily_desk.sh` now refreshes that panel every evening**, so don't run it by hand.
- **Skip it:** the conditional expectancy tables you read each night drift out of date.

---

## On demand

**8. Trade reviewer** — `ANTHROPIC_API_KEY`, `TRADIER_API_KEY`, `MYSQL_PASSWORD`
```bash
PYTHONPATH=src .venv/bin/python3 -m lib.trade_reviewer.cli        # menu of recent buys
PYTHONPATH=src .venv/bin/python3 -m lib.trade_reviewer.cli -p PHIN # prospective, market hours
```
Produces: an O'Neill/CANSLIM review in the terminal. Skipping breaks nothing.

**9. `journal_day.sh` — the manual twin of `morning_journal.sh`. Use it ONLY to backfill.**
```bash
./journal_day.sh --date 20260918 --force    # --force loses hand-written notes
./journal_day.sh --no-deploy
```
Same five steps as the automated morning chain. **Do not run it for today's session — launchd already did.**
⚠ Never re-run the review builder over a range of past dates; it creates duplicate reviews.

**10. Straddle pool eligibility** — `check_straddle_ticker.py KNSA WDC CF` (or `--file`). Structural gate only.
**11. Pullback shorts** — `run_pullback_shorts.py`. ⚠ raw arrival signal is negative EV; screen, not a signal.
**12. `run_straddle_iv_gate.py`** — manual cross-check of straddle gates 3+5; `daily_desk.sh` already applies both.
**13. `run_news_pull.py --plan`** — prints the TradingView MCP calls for Claude to make; not self-executing.

---

## Deploy / maintenance

| command | produces / where | if skipped |
|---|---|---|
| `AWS_PROFILE=clarinut-gmerton ./deploy_trade_journal.sh` | syncs `data/journal/` → `s3://gmerton-trade-journal` + CloudFront invalidation (`E2VZA7AMN3NFDL`). Runs `run_journal_home.py` first. | Nothing — both journal orchestrators already call it. Standalone only after a manual page rebuild. |
| `AWS_PROFILE=clarinut-gmerton ./deploy_breakout_lambda.sh` | redeploys the `preferred-breakout-scan` Lambda + `preferred-breakout-eod` rule (`cron(15 23 ? * MON-FRI)`, **verified ENABLED**). Needs `TRADIER_API_KEY`. | EOD scan keeps running old code. ⚠ Historically this deploy overwrote the S3 preferred list — fixed 2026-09-21, verify after any run. |
| `AWS_PROFILE=clarinut-gmerton ./deploy_refresh_lambda.sh` | redeploys `preferred-list-refresh` + `preferred-list-refresh-nightly` (`cron(30 7 ? * TUE-SAT)`, **verified ENABLED**). Needs `POLYGON_API_KEY`. Pandas layer is **pinned to v24** — v29 segfaults. | The nightly preferred list stops refreshing; every scan runs a frozen universe. |
| `AWS_PROFILE=clarinut-gmerton ./sync_journal_cache.sh push` (or `pull`) | backs up `data/cache/journal_{daily,intraday}/` ↔ `s3://gmerton-trade-journal-cache`. The parquet cache is git-ignored — **this bucket is its only copy.** | A lost/rebuilt checkout means a cold-cache rebuild. Run occasionally. |
| CodeBuild `buildspec.yml` | zips `src/` → `options_toolkit_prod` Lambda (deployed, no schedule). | — |

**`run_eod_scan.sh` — SUPERSEDED, do not use.** It is a cron entrypoint for `run_preferred_breakouts.py`, but `crontab -l` shows **no crontab installed**, so it has never fired on a schedule. The same scan now runs in the cloud as the `preferred-breakout-eod` Lambda, and `daily_desk.sh` step 3 runs it interactively. Per the house rule, check `s3://gmerton-stock-data/breakouts/eod_latest.txt` before scanning locally at all.

---

## Not operational — study scripts

**The rule:** of the 234 root `run_*.py`, **18 are invoked by an orchestrator** (listed above as sub-bullets) and about **10 more are the on-demand / weekly tools above**. Of the remaining 216, **109 write a one-time document into `data/studies/`** and are never re-run — they exist so a result can be reproduced, and their conclusions live in `data/studies/TEST_INDEX.md`, not in the script. Most of the rest print to stdout or only touch `data/cache/`; they are the same thing without a saved doc.

**Do not read the scripts to find out what's true — read `data/studies/TEST_INDEX.md`.** That index carries one line + verdict + link for every test ever run.

Exceptions worth knowing:

- **Periodically re-run despite looking one-off:** `run_regime_validation.py`, `run_adhikary_validation.py`, `run_trade_lens.py` (monthly — item 7). `run_build_liquid_panel.py` looks monthly but is now nightly inside `daily_desk.sh`.
- **Looks operational, is dead:** `run_stock_dcal_screener.py` — a Friday screener, **RETIRED 2026-09-16**; the study behind it had a path-truncation bug and no calendar/diagonal/condor has an edge. Do not act on its output.
- **Looks operational, superseded by the cloud:** `run_minervini_scan.py` and `run_refresh_preferred.py`. The `preferred-list-refresh` Lambda is canonical and owns the S3 list; running these locally risks pushing a stale list over it.
- **Looks operational, superseded by a gated version:** `run_thursday_screener.py` → use `run_putspread_scan.py`.
- **Stale hardcoded state (root, non-`run_`):** `premarket_check.py` and `premarket_defense.py` carry ticker rosters and a `HOLDINGS` dict hand-edited 2026-06-15 — they will report on positions you no longer hold. `start_alerts.sh` → `run_premarket_gaps.py` replaced both.
- **Untracked / in-flight:** `run_etf_putspread_roster.py`, `run_etf_putspread_roster_athena.py` are not in git.
- **One-offs by their own docstring:** `upsert_put_spread_from_csv.py`, `migrate_to_v3.py`, `dedup_v3.py`, `import_historicaldata.py`, plus the 14 `scratch_*.py`.

### Archive candidates (proposed only — nothing has been moved)

A `scripts/archive/` directory would absorb, with zero effect on any orchestrator:
- **62** `run_*.py` last committed before 2026-08 and not invoked by any orchestrator,
- the **14** `scratch_*.py`,
- the 4 migration/import one-offs, `premarket_check.py`, `premarket_defense.py`, `run_stock_dcal_screener.py`, `run_thursday_screener.py`, `option_chart_app.py` (GOOG-only, paused Aug-2026 data pull),
- `run_eod_scan.sh`.

Verify each still isn't imported (`grep -rl "<name>" *.sh *.py src/`) before moving — several study scripts import helpers from each other.

---

## Reconciliation with the older docs

- **`data/studies/daily_routine.md`** — a *what to act on* doc (which signals to trust), not an ops map; it defers to this file for what runs. Reconciled 2026-09-23 (liquid-panel refresh moved to nightly, step 0 GEX settle added).
- **`CLAUDE.md` (repo root)** — rewritten 2026-09-22 around the three orchestrators; it now points here for the full map and lists the March-era `lib.*` finders as ad-hoc entry points, not the routine. Consistent with this file.
- **`/Users/gmerton/CLAUDE.md`** (workspace level) has nothing on this repo beyond pointing at it. Nothing to reconcile.
