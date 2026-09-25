# OPERATIONS — what to run, when

*Map of the shell orchestrators, the cloud jobs, and the handful of scripts you drive by hand. Written 2026-09-22; housekeeping pass 2026-09-24 (cloud jobs + CI documented, 73 dead scripts archived to `scripts/archive/`).*
*Rule: **if an orchestrator calls it, you never call it yourself.** Sub-bullets are steps, not commands.*

**Every command below assumes:** repo root, `.venv/bin/python3` (system python3 lacks packages), `PYTHONPATH=src`.
**Secrets live in `~/.trading_env`** (`TRADIER_API_KEY`, `MYSQL_PASSWORD`, `IBKR_FLEX_TOKEN`, `ANTHROPIC_API_KEY`, `POLYGON_API_KEY`).
Since 2026-09-24 **every orchestrator sources it itself** (`start_alerts.sh`, `morning_journal.sh`, `daily_desk.sh`, `journal_day.sh`), and so do the two Lambda deploy scripts.

---

## Daily, pre-market (your morning, PT)

**1. `morning_journal.sh` — AUTOMATED, 08:00 local daily. You read it, you don't run it.**
```bash
./morning_journal.sh                 # manual re-run only (--no-deploy, --charts)
```
- Scheduled by launchd: `~/Library/LaunchAgents/com.gmerton.morning-journal.plist` (confirmed running — logs in `data/journal/logs/morning_<date>.log`, 9/18–9/22 present; weekend guard exits early).
- Produces: yesterday's journal + the published site → `data/journal/<date>.md`, `data/journal/days/`, `data/studies/journal_process_grades.md`, and https://d1z4hclel0mtsn.cloudfront.net/
- Steps: `run_daily_journal.py` (Flex pull, retries 6×10min while IBKR's statement isn't ready) → `run_build_reviews.py` → `run_journal_grades.py` → `run_trade_review_pages.py --no-charts` → `deploy_trade_journal.sh` → `sync_journal_cache.sh push` (backup of the git-ignored journal cache; non-fatal; added 2026-09-24 after the last manual push turned out to be 2026-09-02)
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
- Env: sourced from `~/.trading_env` by the script (since 2026-09-24); `AWS_PROFILE` for the S3 pulls. The panel builder's gap fill needs `POLYGON_API_KEY`. TWS/Gateway open on Fridays for the straddle IV-percentile gate (`IB_PORT=7496` live / `4002` paper).
- **Skip it:** no `universe_focus.txt` for tomorrow (so `start_alerts.sh` watches a stale universe), expiring positions go unreviewed, and the GEX fly paper trade misses a settle.

---

## Cloud jobs (scheduled) — verified 2026-09-24

| job | schedule | what it does | health (7 days to 2026-09-24) |
|---|---|---|---|
| **`preferred-list-refresh`** Lambda, rule `preferred-list-refresh-nightly` | `cron(30 7 ? * TUE-SAT)` UTC (03:30 ET) | Minervini day-matrix + preferred list → `s3://gmerton-stock-data/breakouts/` (`minervini_matrix.parquet`, `preferred_tickers.txt`, `refresh_latest.txt`) | 7 runs, 0 errors |
| **`preferred-breakout-scan`** Lambda, rule `preferred-breakout-eod` | `cron(15 23 ? * MON-FRI)` UTC (19:15 ET) | the house EOD breakout scan → `eod_<date>.txt`, `eod_latest.{txt,json}`, `monitor_latest.json` in the same prefix | 5 runs, 0 errors |
| ⭐ **`options-daily-updater`** — ECS Fargate task on `options-cluster`, EventBridge **Scheduler** (not a rule) | `cron(0 22 ? * MON-FRI)` America/New_York, ~4.5 h | **the feed for `silver.options_daily_v3`**: nightly Polygon EOD option snapshots for ~11k tickers, Glue temp table → Athena INSERT; deletes the day first, so re-runs are idempotent. Source: `services/daily-updater/` (Docker). Logs: CloudWatch `/ecs/options-daily-updater` | 2026-09-23 complete (11,273 tickers, 5,444 with data, 1.77M rows, 0 errors); 09-24 running. **Previously undocumented** — check it first when v3 looks stale |

**CI (CodePipeline, all on push to `main` via the GitHub connection):**

| pipeline | builds | trigger | note |
|---|---|---|---|
| `journal-site` | `buildspec_journal_site.yml` → the journal site's page generator | path-filtered | two failures on 2026-09-23, succeeded since |
| `preferred-breakout-scan` | `buildspec_breakout.yml` → the breakout Lambda | path-filtered (`src/lib/interface/breakout_*.py`, tradier, …) | ⚠ a SECOND deploy path besides `deploy_breakout_lambda.sh` — open decision: which is canonical |
| `preferred-list-refresh` | `buildspec_refresh.yml` → the refresh Lambda | path-filtered | same second-deploy-path question as above; three failures on 2026-09-22 |
| `options_toolkit` | `buildspec.yml` → `options_toolkit_prod` | **every push** | fails every run; retirement pending (see the deploy table) |

Other Lambdas / ECS resources in the account (`AGAWorkshop*`, `ninja-*`, `my-math-fucntion`, `sftp-endpoint-*`, `cloudwatch_catalog_3`, the `sftp-ecs-04` cluster, the CodeGuru rule) date from 2021 and are **not this repo**.

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
Same five steps as the automated morning chain (it now sources `~/.trading_env` too). **Do not run it for today's session — launchd already did.**
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
| `AWS_PROFILE=clarinut-gmerton ./sync_journal_cache.sh push` (or `pull`) | backs up `data/cache/journal_{daily,intraday}/` ↔ `s3://gmerton-trade-journal-cache`. The parquet cache is git-ignored — **this bucket is its only copy.** **Automated since 2026-09-24** as the last step of `morning_journal.sh`; run `pull` on a fresh checkout. | A lost/rebuilt checkout means a cold-cache rebuild. |
| `PYTHONPATH=src .venv/bin/python3 scripts/cache_sync.py` | mirrors the *other* irreplaceable artifacts (IBKR intraday bars in `ibkr_bot/data/`, orphaned files with no producer) to `s3://gmerton-stock-data/cache`. **Not scheduled.** | IBKR bars that IBKR no longer serves are lost for good with the laptop. Run after any new bar pull. |
| CodeBuild `buildspec.yml` | zips `src/` → `options_toolkit_prod` Lambda (deployed, no schedule). **⚠ RETIREMENT PENDING:** zero invocations, 3 s / 128 MB, and its `options_toolkit` CodePipeline fails on every push to `main`. Needs Gabe's OK to delete (Lambda + pipeline + CodeBuild project). | Nothing. |

**`run_index_audit.py` — run after any study lands.** Checks TEST_INDEX against the study docs on disk:
orphans (a doc with no row) and broken links (a row pointing at a missing file). Exit code 1 on either, so
it can gate a commit. Added 2026-09-23 after three same-day instances: the Davis XSP condor was fully
backtested with no row, §286 carried another study's `n`, and that afternoon's own alert study shipped
unindexed. Docs closed by a status banner (SUPERSEDED/RETIRED/WITHDRAWN) count as a terminal state, not
an orphan.

**`run_eod_scan.sh` — ARCHIVED 2026-09-24** (`scripts/archive/`). It was a cron entrypoint that never had a crontab. The same scan runs in the cloud as the `preferred-breakout-eod` Lambda (19:15 ET), and `daily_desk.sh` step 3 still runs it locally for the pre-19:15 read — ⚠ **open decision:** after 19:15 ET the desk could read `s3://gmerton-stock-data/breakouts/eod_latest.txt` instead of rescanning (house rule: check S3 before scanning locally).

---

## Not operational — study scripts

**The rule:** of the 234 root `run_*.py`, **18 are invoked by an orchestrator** (listed above as sub-bullets) and about **10 more are the on-demand / weekly tools above**. Of the remaining 216, **109 write a one-time document into `data/studies/`** and are never re-run — they exist so a result can be reproduced, and their conclusions live in `data/studies/TEST_INDEX.md`, not in the script. Most of the rest print to stdout or only touch `data/cache/`; they are the same thing without a saved doc.

**Do not read the scripts to find out what's true — read `data/studies/TEST_INDEX.md`.** That index carries one line + verdict + link for every test ever run.

Exceptions worth knowing:

- **Periodically re-run despite looking one-off:** `run_regime_validation.py`, `run_adhikary_validation.py`, `run_trade_lens.py` (monthly — item 7). `run_build_liquid_panel.py` looks monthly but is now nightly inside `daily_desk.sh`.
- **Looks operational, is dead (archived 2026-09-24):** `run_stock_dcal_screener.py` — a Friday screener, **RETIRED 2026-09-16**; the study behind it had a path-truncation bug and no calendar/diagonal/condor has an edge. Do not act on its output.
- **Looks operational, superseded by the cloud:** `run_minervini_scan.py` (archived 2026-09-24) and `run_refresh_preferred.py` (still at the root because `deploy_breakout_lambda.sh` calls it). The `preferred-list-refresh` Lambda is canonical and owns the S3 list; running either locally risks pushing a stale list over it.
- **Looks operational, superseded by a gated version (archived 2026-09-24):** `run_thursday_screener.py` → use `run_putspread_scan.py`.
- **Stale hardcoded state (archived 2026-09-24):** `premarket_check.py` and `premarket_defense.py` carry ticker rosters and a `HOLDINGS` dict hand-edited 2026-06-15 — they will report on positions you no longer hold. `start_alerts.sh` → `run_premarket_gaps.py` replaced both.
- **Untracked / in-flight:** `run_etf_putspread_roster.py`, `run_etf_putspread_roster_athena.py` are not in git.
- **One-offs by their own docstring:** `upsert_put_spread_from_csv.py`, `migrate_to_v3.py`, `dedup_v3.py` and the 17 `scratch_*.py` are archived; `import_historicaldata.py` stays at the root (made idempotent 2026-09-23, still the v3 repair path).

### Archive — DONE 2026-09-24

**73 scripts moved to `scripts/archive/`** with `git mv` (history kept); `scripts/archive/README.md` lists each
with its last commit and one-line purpose, and says how to re-run one. Moved: study/backtest `run_*.py` last
committed before 2026-08, the 17 `scratch_*.py` probes, the migration one-offs (`migrate_to_v3.py`, `dedup_v3.py`,
`upsert_put_spread_from_csv.py`), and the retired/superseded look-alikes: `premarket_check.py`,
`premarket_defense.py`, `run_stock_dcal_screener.py`, `run_thursday_screener.py`, `run_minervini_scan.py`,
`option_chart_app.py`, `run_eod_scan.sh`. Every file was checked for imports and shell/CI references first; the
index audit is clean after the move.

**Kept at the root on purpose:** `run_build_fwd_vol.py`, `run_build_option_legs.py` (Glue table builders),
`run_backfill_options_v3.py`, `run_reversal_monitor.py`, `run_sleeping_giants.py`, `run_breakout_scorecard.py`,
and six scripts other scripts import — notably **`run_refresh_preferred.py`, which `deploy_breakout_lambda.sh`
still calls** (the historical route by which a deploy overwrote the S3 preferred list; do not run it by hand).

**Generated watchlist outputs are now git-ignored** (`.gitignore`, 2026-09-24): `*_latest.*`, dated
`adhikary_*`, `alerts_*`, `clusters_*`, `eod_*`, `positions_*`, `regime_*`, `straddle_screen_*.txt`,
`putspread_scan*`, `premarket_industries_*`. Hand-edited files in `data/watchlist/` stay tracked.

---

## Reconciliation with the older docs

- **`data/studies/daily_routine.md`** — a *what to act on* doc (which signals to trust), not an ops map; it defers to this file for what runs. Reconciled 2026-09-23 (liquid-panel refresh moved to nightly, step 0 GEX settle added).
- **`CLAUDE.md` (repo root)** — rewritten 2026-09-22 around the three orchestrators; it now points here for the full map and lists the March-era `lib.*` finders as ad-hoc entry points, not the routine. Consistent with this file.
- **`/Users/gmerton/CLAUDE.md`** (workspace level) has nothing on this repo beyond pointing at it. Nothing to reconcile.
