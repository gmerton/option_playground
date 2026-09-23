# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

An options + equity-swing trading research desk: it screens live setups, runs historical studies against
Athena/S3 Tables, and keeps a graded trade journal. It is a research repo first — most of the 230+ root
scripts are one-time studies, not tools.

## ⚠ Read these first

| file | what it answers |
|---|---|
| **`HANDOFF.md`** | **Picking this up cold?** Start here. The *why* and the *right now*: what changed recently and is not obvious from the code, what is in flight, what is knowingly broken. Dated — trust the files below it where they disagree. |
| **`OPERATIONS.md`** | **What do I actually RUN, and when.** The whole repo reduces to ~13 top-level commands; everything else is orchestrator-invoked or a dead study script. Start here. |
| `data/studies/TEST_INDEX.md` | What has already been tested, with the verdict — one line per test, plus §10 for what's queued. **Check before proposing any study; most ideas here have been run.** |
| `data/studies/daily_routine.md` | What to *act on* vs ignore each day (which signals carry expectancy). Different question from OPERATIONS.md. |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas pyarrow awswrangler boto3 sqlparse aiohttp polygon-api-client requests pandas-ta anthropic yfinance scipy statsmodels
```

**Always use `.venv/bin/python3`** — the system `python3` lacks these packages. Run everything from the repo
root with `PYTHONPATH=src`.

Secrets live in **`~/.trading_env`** (sourced by the shell profiles and by `start_alerts.sh` /
`morning_journal.sh`; `daily_desk.sh` and `journal_day.sh` do *not* source it). Keys used:
`AWS_PROFILE=clarinut-gmerton`, `TRADIER_API_KEY`, `MYSQL_PASSWORD`, `IBKR_FLEX_TOKEN`, `ANTHROPIC_API_KEY`.

Canonical invocation:
```bash
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 <script>.py
```

## Running things

**See `OPERATIONS.md` for the full map.** The short version — the desk is three shell orchestrators, and
**if an orchestrator calls a script, never call that script yourself**:

- **`morning_journal.sh`** — *automated*, 08:00 daily via launchd (`com.gmerton.morning-journal.plist`).
  Builds yesterday's journal, grades it, deploys the site. You read the output; you don't run it.
- **`start_alerts.sh`** — launch ~09:25 ET, leave running to the close. Intraday alerts + the pre-market gap
  and industry pulls. Writes `data/journal/alerts/<date>.json`, which the evening scorecard needs.
- **`daily_desk.sh`** — the evening desk: regime, open book, scans, clusters, grades, and tomorrow's focus
  universe. Pulls the Minervini matrix and preferred list from S3 first — do not bypass that.

Periodic: `run_friday_screener.py` (Fri), `run_putspread_scan.py` (Thu — carries the tested IV≥60th-pctile
gate; **`run_thursday_screener.py` is superseded and ungated**), and a monthly re-validation trio.

On demand: `./journal_day.sh --date <YYYYMMDD>` is **backfill only** now that launchd runs the same chain
daily; the trade reviewer (`python -m lib.trade_reviewer.cli [-p TICKER]`, needs `ANTHROPIC_API_KEY`); and
`run_pullback_shorts.py`, `run_straddle_iv_gate.py`, `run_news_pull.py`.

⚠ **Scripts that look operational but are traps** (details in `OPERATIONS.md`): `premarket_check.py` /
`premarket_defense.py` (hand-edited `HOLDINGS` frozen 2026-06-15), `run_thursday_screener.py` (no IV gate),
`run_stock_dcal_screener.py` (retired strategy), `run_minervini_scan.py` / `run_refresh_preferred.py`
(the Lambda owns the S3 list — running these locally re-creates a stale-list overwrite), `run_eod_scan.sh`
(prescribes crontab lines that were never installed; the `preferred-breakout-eod` Lambda does this now).

Cloud jobs (EventBridge, both enabled): `preferred-breakout-eod` weeknights 23:15 UTC,
`preferred-list-refresh-nightly` Tue–Sat 07:30 UTC.

## Architecture

### 1. Live market data (Tradier)
- **`src/lib/tradier/tradier_client_wrapper.py`** — async client (`TradierClient`), an async context manager.
  Always `async with TradierClient(api_key=...) as client:` so one session is shared.
- **`src/lib/commons/`** — async wrappers: `list_expirations.py`, `list_contracts.py`,
  `get_underlying_price.py`, `get_daily_history.py`, plus indicator helpers (`moving_averages.py`,
  `high_low.py`, `pivot_detector.py`, `vol_compression.py`, `volume_breakout.py`).

### 2. Historical data (Athena / S3 Tables)
- **`src/lib/athena_lib.py`** — `athena(sql)` via `awswrangler`. `ctas_approach=False` is required because
  `data_source` is not `AwsDataCatalog`.
- **The table is `silver.options_daily_v3`**, not `_v2` (see `src/lib/constants.py`; this doc said `_v2` for
  months). ~4.07B rows, 2010→2026, 11.5k tickers, partitioned `bucket[5](ticker) + year(trade_date)` — chunk
  queries by ticker-year (~6s each) rather than pre-narrowing.
- ⚠ **v3 strikes and greeks are RAW** (never split-adjusted) while every price panel we keep is adjusted —
  median 3.1% mismatch, and a full split factor for a name that split in-sample. Recover spot from the chain
  itself (`src/lib/studies/chain_spot.py`) for any settlement or moneyness calculation.
- ⚠ Coverage cliffs: bid/ask ends ~Mar 2026, stored IV ends ~mid-May 2026, later rows are prints-only.
- Cross-catalog JOINs need both sides fully qualified. Athena DDL does **not** work on S3 Tables (use
  `aws s3tables` / boto3), and `writeOrder` causes `HIVE_WRITER_DATA_ERROR`.
- **`stocks.options_cache` (MySQL)** is a synced *subset* of v3 (DTE 0–65, deduped). Its sync filters
  `bid > 0 AND ask > 0 AND delta IS NOT NULL`, exempting expiry-day rows — so **every zero-bid quote is
  missing except at expiry**. That silently breaks exit scans on winning spreads; pull from v3 when
  completeness matters.

### Strategy and study modules
- **`src/lib/data/Leg.py`** — `Leg` (immutable: direction, option type, delta target, DTE) and `Strategy`.
  Legs are written in trader language and resolved to contracts later.
- **`src/lib/studies/`** — the backtest engines: `put_spread_study.py`, `call_spread_study.py`,
  `straddle_study.py`, `calendar_study.py`, `iron_butterfly_study.py`, `vrp_panel.py`, `ticker_config.py`.
- **`src/lib/studies/pattern_test.py`** — the equity pattern harness. A new pattern is ~20 lines; the harness
  owns fills, arms, same-name and cross-name controls, sample splits and t-stats, and it writes into
  `data/studies/pattern_ledger.md`. **Use it for any new equity setup test.**
- **`src/lib/studies/costs.py`** — the house cost model ($0.65/contract/leg/side + 25% of the quoted
  bid-ask). Every engine applies it; `--no-costs` reproduces the old pre-cost tables.
- Screeners/finders under `src/lib/commons/credit_spread_finder.py`, `lib/fly/`, `lib/leaps/`,
  `lib/double_calendar/`, `lib/interface/sepa.py`, `lib/forward/ff.py` are importable modules and ad-hoc
  entry points, **not** part of the daily routine. `premarket_watchlist.py` is historical (last touched
  2026-03); the live equivalent runs inside `daily_desk.sh` / `start_alerts.sh`.

### Lambda deployment
`buildspec.yml` packages `src/` into `function.zip` → the `options_toolkit_prod` Lambda via CodeBuild.
`deploy_breakout_lambda.sh` / `deploy_refresh_lambda.sh` deploy the two scheduled scan Lambdas;
`deploy_trade_journal.sh` pushes the journal site to S3/CloudFront.

## Research conventions

These are hard-won; violating them has produced wrong results more than once.

- **Price at real fills, never mid.** A mid-priced backtest is how this book fools itself — a 2026-09-22 cost
  sweep killed nine strategies that looked good at mid. Report gross and after-cost side by side.
- **Pre-register the test** in the script's docstring before running it: universe, arms, control, the bar, and
  the multiple-testing charge. State the primary cell in advance; everything else is exploratory.
- **The bar is |t| ≥ 3 with both halves of the sample the same sign** — and when you test many cells, the
  Šidák/BH-corrected threshold governs instead, not the raw 3.
- **Always have a control**, and prefer one that holds the confound fixed (same name later, same day other
  name, exposure-matched buy-and-hold). A result with no benchmark cannot be distinguished from beta.
- **Chronological halves do not catch a regime in the back half** — check per-year too.
- Verdicts use the scheme in TEST_INDEX: ADOPTED / PARKED / NULL / INVERTED / UNDERPOWERED / RETRACTED, plus
  a YIELD tag (MECHANISM / METHOD / REFRAME) for what a null still taught us.
- **The trade journal is not evidence for setup selection** — it is admissible only for conformance,
  execution quality and cost realism. It is also structurally underpowered for certifying an edge.
- Quiet mode: verbose output goes to a log file under `data/studies/`; surface a short summary plus the path.
- **Review the negatives for false negatives.** After a run of nulls, re-check each: did "wider data" actually
  change the universe? Is a "cost proxy" cell really a positive after-cost strategy?
- **Pull all results — never truncate data the owner will act on.**
- **Creator patterns have no fixed timeframe.** Bars may be 1-minute or daily; normalise to ATR/scale-free
  before testing. A daily-bar null does **not** refute an intraday pattern.
- **Be pragmatic about data unevenness** — note the caveat and continue; don't halt on it.

## Working rules

How the owner wants the work done. These are his standing instructions, not inferences — follow them
unless he says otherwise in the moment.

- **Commit directly to `main`.** Personal repo; no feature-branch-by-default. Commit and push straight to
  `main` unless told otherwise.
- **His trades are not evidence.** Assume he is a bad trader. His log is admissible for conformance,
  execution and cost realism **only** — never for setup selection, and never as a benchmark. This is the
  rule most likely to be got wrong by someone new, and it is expensive: treating the journal as evidence
  for selection will manufacture confident, wrong conclusions.
- **Flag same-day round trips every time** the day's fills are pulled, unprompted — he asked for the
  reminder explicitly ("it's how I learn"). It is the largest measured leak in the book: August, 132 round
  trips, −$7,884; across his log, 278 same-day cycles, −$8.3k at a 19% win rate. Report the count and the
  dollar total even on a good day; one session is noise, the running tally is the point.
- **Precision over recall** — rather miss winners than admit losers.
- **Conviction selection IS the strategy.** The intraday machinery is execution insurance on discretionary
  picks, not a source of return.
- **Don't grade planned vs unplanned.** He doesn't report every plan, so absence from the sheet means
  nothing. Grade the trade's characteristics.
- **Incremental delivery**: plumbing first, defer strategy decisions.
- **Weight current market conditions** — report setup expectancy *conditioned* on today's regime (SPY trend
  × breadth) and mark today's row, rather than quoting an unconditional average.
- **Quote every stop two ways** — width and execution — and name **which of the two live stops** you mean.
  ⚠ **They execute differently and getting this backwards is a known error (2026-09-23):**
  - **Disaster stop = 1.0 ADR below the current close → RESTS WITH THE BROKER, executes INTRADAY.** Its
    job is the crash, not the noise; it fires 4–6% of days.
  - **Tight stop = the session low (0.4–0.8 ADR) → JUDGED ON THE CLOSE.** Resting *this* one intraday is
    what the research rejects (DINO 2026-09-22: correct 0.75-ADR width, filled at the post-entry low
    15:51, closed above the day-low stop nine minutes later; cost ~$11.56 plus the position).
  Always give `stop/ADR` for the tight one; under ~0.5 ADR, widen it and cut size (a weak close is a
  *sizing* problem, never a selection one). ⚠ Don't overclaim: the 1-ADR cell is ≈+0.03R and does not beat
  its control, and no stop variant beats buying the close. **"Hard stop"** is the trade reviewer's
  retrospective entry-quality criterion, not a live level; **"emergency stop" does not exist here** — ask
  which live stop is meant. **Canonical definitions: `data/studies/stop_definitions.md`.**
- **No background polling.** When data isn't ready (Flex, a scheduled job), report status and expected
  timing, then stop. He will ask again.
- **ASCII filenames only** — git escapes non-ASCII in `--name-only`, so grep-based audits silently miss
  those files.

⚠ **This section exists because memory does not travel.** The `~/.claude/projects/.../memory/` store is
account- and machine-local and is not in git, so these rules would otherwise be lost when switching Claude
accounts or machines. Keep durable behavioural rules here; leave situational project state in memory,
where going stale is harmless.

## Gotchas that cost an hour

Discovered the expensive way. Each one looks like a different problem than it is.

- **IB Gateway/TWS binds IPv6.** Do NOT probe its port with a `/dev/tcp` IPv4 loopback test — it reports
  closed on a port that is listening. Use `lsof -nP -iTCP -sTCP:LISTEN | grep 7496`. Live TWS is **7496**,
  paper Gateway **4002**.
- **API handshake times out although the port is open** → a stale clientId. Retry with a **fresh clientId**,
  then restart the Gateway if it persists. Use `reqAllOpenOrders()` to audit every stop, not just your own
  session's.
- **Cancel TWS orders via clientId 0 only**, and never stack stops on one position — audit before placing.
  Live account **U21036520**.
- **The real open book is the `journal_open_positions` Flex snapshot** (broker basis + mark), not a
  reconstruction from fills. ⚠ It lands **one session late**; for today's positions query IBKR live.
  Flex **trade confirms (query 1415008) land same-day**; the **NAV/Activity query (1605053) is a session
  behind** — a distinction that matters constantly.
- **TradingView MCP OAuth dies with a CloudFront 403** if you authenticate while signed out. **Sign in to
  tradingview.com first**, then authenticate.
- **`run_trade_review_pages.py` is a pure renderer** (zero DB writes) and is safe to re-run. **`run_build_reviews.py`
  is NOT** — re-running it over past dates re-creates existing reviews under new labels (425 duplicates on
  2026-09-21). Never rebuild reviews for a date that already has them.
- **`options_daily_v3` duplicate episode — FIXED AND VERIFIED 2026-09-23.** `import_historicaldata.py` was
  INSERT-only, so re-running it over an already-loaded date appended a whole duplicate set. **It is now
  idempotent** (deletes the day before inserting). A scan of all 4,220 sessions found exactly **9** damaged
  days; all are repaired. **12,441,196 rows removed, 4,142,170,035 -> 4,129,729,... ; an exact per-year
  check over a 5-ticker sample now returns ZERO duplicate groups in every year 2010-2026**, i.e. the table
  is unique on `(ticker, expiry, strike, cp, trade_date)`. The blanket "always dedupe when reading v3"
  workaround is **no longer required** — but it is cheap insurance, and re-verify if ingestion changes.
  ⚠ **2025-07-03 needed a different, weaker operation and this matters when reading that date.** It had
  **zero** byte-identical rows (every row differed in greeks at trailing decimals), so it was collapsed on
  the contract key in three authorised stages, each gated on the discarded field being unable to change a
  result: greeks only, then `last` (99.7% of gaps sat inside the quoted spread; nothing fills at `last`),
  then finally **73,317 contracts whose BID/ASK genuinely differed** — resolved by keeping the
  **widest-spread** row. That is the only place in the table where a price was chosen; the choice is
  deliberately pessimistic (lower bid, higher ask), so results on that date can only be conservative.
  Tooling: `repair_v3_duplicate_days.py` (`--collapse-greeks` / `--relax-last` / `--unique`).
- **MySQL is bound to `127.0.0.1`.** Nothing in the cloud can reach it, which is why the journal site's
  presentation had to be split from its data before CI could deploy it.

## Key patterns

- Live data helpers are `async` and take a `TradierClient`. Older modules use bare `aiohttp` — prefer the
  wrapper in new code.
- `RuntimeError` is the standard non-fatal screening failure (missing data, thin liquidity); callers swallow
  it to skip a symbol.
- Ticker lists live in `src/lib/commons/nyse_arca_list.py`; the generated preferred list is S3-owned.
- `src/lib/earnings/` handles earnings-specific option queries and Athena caching.
- ASCII filenames only — git escapes non-ASCII in `--name-only`, so grep-based audits silently miss them.
