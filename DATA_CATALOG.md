# DATA_CATALOG.md — what data we have, where, and what it cannot answer

Inventoried 2026-09-25 from the live systems (Athena/Glue listings, MySQL `information_schema`, `data/cache/`,
S3), not from memory. **Read §0 and §7 before designing a study.** Row counts and ranges drift, so re-verify any
number a study will depend on.

## 0. Pre-study checklist
1. **Is the data in §1–§5 already?** Prefer a derived table (§2) or a local cache (§4) over a fresh v3 pull.
2. **Does the universe answer the question?** Every equity panel here is **survivorship-biased** (liquid *as of
   2026*). Reversal, value and "beaten-down" tests are flattered by it (§7).
3. **Price adjustment:** v3 strikes and greeks are **RAW**, while every price panel is **split-adjusted**. Recover spot
   from the chain (`src/lib/studies/chain_spot.py`), or select by delta.
4. **Coverage cliffs:** v3 bid/ask ends ~**2026-03**, stored IV ~**mid-May 2026**, and later rows are prints only.
   End option studies at 2026-02/03.
5. **Cost:** a v3 pull is ~6 s per ticker-year. Build per-day aggregates inside Athena (§2 pattern), not locally.

## 1. Athena / S3 Tables — primary historical stores
Catalog `s3tablescatalog/gm-equity-tbl-bucket`, namespace `silver`. Query through `lib.athena_lib.athena(sql)`
(`ctas_approach=False`). Athena DDL does **not** work here.

| table | what | range / size | notes |
|---|---|---|---|
| **`options_daily_v3`** | EOD option chains: bid/ask/last, bid_iv/ask_iv, greeks, OI, volume | 2010→2026, ~4.13B rows, ~11.5k tickers | THE options table. Unique on (ticker, expiry, strike, cp, trade_date) since the 9/23 repair; **2025-07-03** kept the widest-spread row. Nightly feed = ECS `options-daily-updater` (22:00 ET). Partitioned bucket(ticker) + year: chunk by ticker-year |
| `equity_daily` | daily OHLCV + vwap + dollar_volume, all listed names | 2025-05-19→present, 5,302 tickers | short history; the source for `minervini_matrix` |
| `options_daily` | legacy (v1/v2) | — | ⛔ **broken**: `ICEBERG_INVALID_METADATA`. Do not use |
| `temp2`, `tmp1` | scratch | — | ignore |

## 2. Glue catalog (`AwsDataCatalog`, db `silver`) — derived per-day tables built in Athena
Query with `data_source="AwsDataCatalog"`. Build pattern: CTAS for the first year, then one INSERT per year,
idempotent per year (see either builder).

| table | built by | contents | range |
|---|---|---|---|
| **`options_flow_daily`** | `run_build_options_flow_daily.py` | per (ticker, day): call/put volume and OI (all, ≤30 DTE), OTM ≤30 DTE volume by delta band, $ premium, delta-weighted share volume | 2010→2026, 19.2M rows. ⚠ after ~Apr 2026 deltas are NULL and volume drops ~60% |
| **`options_iv_daily`** | `run_build_options_iv_daily.py` | per (ticker, day): `skew` (25Δ put − 50Δ call IV, nearest 30 DTE), `put25_iv`, `call50_iv`, `cw` (call−put IV at the same strike, OI-weighted) | 2010→2026, 13.0M rows. Use through 2026-03 |
| **`chain_spot_daily`** | `run_build_chain_spot_daily.py` | per (ticker, day): RAW spot from put-call parity (3 nearest-ATM strikes, ~30 DTE), `n_strikes`, `opt_vol`. **Includes delisted names**, so it is the only survivorship-free price series we have (optionable names, closes only). Adjust splits with `pit/splits.parquet` | 2010→2026, 16.3M rows, 10.8k tickers; ~0.4% from real closes; use through 2026-02 |
| `fwd_vol_daily`, `option_legs_settled` | older studies (2026-03) | forward vol; settled legs | legacy, unverified |
| `gm_equity.*` (`options_1min_parquet`, `stock_5min`, `options_daily_parquet`, …) | 2025 Polygon experiments | 1-min options (year=2021→2025 prefixes), 5-min stock | legacy; extent not verified. Check before relying on it |

## 3. MySQL `stocks` (127.0.0.1 only; nothing in the cloud can reach it)

| table | what | notes |
|---|---|---|
| **`journal_trades`** | every IBKR fill (Flex confirms, query 1415008, same day) | 1.6k rows; admissible for conformance, execution and costs **only** |
| **`journal_open_positions`** | Flex position snapshot with mark and basis | **the** open book; lands one session late |
| `journal_campaigns` / `journal_campaign_trades` | fills grouped into campaigns | the key for trade reviews |
| `journal_trade_reviews`, `journal_review_tags`, `journal_entry_grades`, `journal_pending_notes` | reviewer and grader output | ⚠ never re-run `run_build_reviews.py` over past dates |
| `journal_nav` | NAV (Flex query 1605053) | one session late |
| **`options_cache`** | synced **subset** of v3: DTE 0–65 | 67M rows, 5.1 GB. ⚠ drops every zero-bid quote except at expiry, which breaks exit scans on winners. Use v3 when completeness matters |
| `earnings_report`, `income_statement`, `financial_metrics`, `key_metrics`, `m_and_a`, `stocks` | older fundamentals pulls | undated vintage; ~10–15k rows each; not point-in-time |
| `study_detail` / `study_summary` / `strangle_study_det` / `studies` / `trades` | legacy study outputs (2026-H1) | superseded by `data/studies/` |

## 4. Local caches (`data/cache/`, 6.1 GB, not in git)

### 4a. Equity price panels
| file | what | range | notes |
|---|---|---|---|
| **`liquid_panel_2009.parquet`** | yfinance **adjusted** daily OHLCV + dolvol | 2009-01→2026-09-23, 1,728 names | the long panel for pattern tests; ⚠ survivorship: liquid as of 2026 |
| **`liquid_panel_2019.parquet`** | same | 2019-01→2026-09-23, 1,719 names | refreshed nightly by `daily_desk.sh` (`run_build_liquid_panel.py`); default for `pattern_test` |
| `minervini_matrix.parquet` | close/high/low/dolvol, all listed names | 2025-07→present, 5,302 names | pulled from S3 (Lambda-owned); do not rebuild locally |
| `price_features.parquet` | above_50ma, rv20, momentum_21 | 2016-12→2026-03, 986 names | iron-fly features |
| `<TICKER>_stock.parquet`, `group_etf_closes`, `rsi_closes`, `index_daily_ftd` | single-name / ETF / index closes | varies | study-specific |
| `pit/tickers.parquet`, `pit/splits.parquet` | Polygon ticker master **incl. delisted** (10,984) + 17.7k splits | — | stages 1–2 of the survivorship-free panel; ⛔ stage 3 (prices) is BLOCKED on a free-tier key |

### 4b. Option extracts (pulled from v3 for specific studies)
| file | contents | range |
|---|---|---|
| `options_flow_liquid.parquet` | `options_flow_daily` restricted to the liquid panel | 2010→2026-09, 1,713 names |
| `options_iv_liquid.parquet` | `options_iv_daily` restricted to the liquid panel | 2010→2026-02, 1,685 names |
| `SPY_puts_v3_2018_2026*.parquet` | SPY puts with bid/ask/delta | 2018→2026-04 |
| `QQQ_options`, `TLT_options`, `XLF_options`, `TMF_options`, `KWEB_options`, `uup_chain` | full chains, bid/ask/delta/OI | QQQ/TLT 2018→2026-02 |
| `SPX_options*.parquet` (dte15/30/60) | SPX mid/delta | 2016→2025-09 |
| `spy_skew_25d.parquet` | SPY 25Δ IV by expiry | 2010→2026-02 |
| `fvr_daily.parquet` | per-name put IV30 and the 30/90 forward-vol ratio | 987 names |
| `gex/` | SPY/QQQ GEX by strike + 20-day quotes | GEX studies |
| `vrp_panel/`, `bci_csp/`, `straddle_dte/`, `iv_*`, `grid_*`, `earnings_*_chains`, `vehicle_chains`, `*_recon` | study-specific chain pulls | see the owning study |
| `fill_quotes_ibkr_1min.parquet` | IBKR 1-min bid/ask at Gabe's option fill minutes | 403 fills, the slippage calibration |

### 4c. Intraday
| path | what | range |
|---|---|---|
| **`intraday_hist/{SPY,QQQ,TQQQ,SQQQ}_1min.parquet`** | IBKR 1-min bars (ts, OHLCV, average, barCount) | **2007-01→2026-09-17** (TQQQ/SQQQ from 2010) |
| **`intraday_1min/<SYM>_<date>.parquet`** | per-name-day 1-min bars (Tradier; Polygon backfill) for the watchlist | 24,755 files, 2026-02→2026-09. ⚠ `vwap` is **per-bar**; session VWAP = `lib.journal.exit_kind.session_vwap` |
| **`s3://gmerton-stock-data/backfill/intraday_1min/bars/<SYM>/`** (cloud) | Polygon 1-min bars, 1,715 liquid names (precision-tier names first), **2024-10 → 2026-09**, one parquet per name × 70-day chunk, same schema as `intraday_1min/` | ⏳ filling from 2026-09-25 (ECS `polygon-1min-backfill`, ~3 days; `services/polygon-1min-backfill/`). Free-tier key: nothing earlier than ~2y is available |
| `alert_ctx_v*_<date>.parquet` | alert-replay context snapshots | 2026-02→09 |
| `journal_intraday/`, `journal_daily/` | bars behind journal entries | 2026 |
| `GOOG_*_1min_bidask.parquet` | intraday option quotes, 4 GOOG expiries | ⏸ paused 2026-08 |

### 4d. Events, fundamentals, flows
| file | what | range | source |
|---|---|---|---|
| `earnings_yf.parquet` | earnings dates, EPS estimate/actual, surprise %, session | 89k events, 1,336 names | yfinance (`run_earnings_calendar_pull.py`) |
| `insider_purchases.parquet` (+ `sec_form345/`) | SEC Form 4 open-market purchases, point-in-time | 2010→2026-03, 506k lines | SEC bulk (`run_sec_insider_pull.py`) |
| `sec_companyfacts.parquet` | XBRL fundamentals (tag, val, period, filed) | 1,692 names | SEC companyfacts (`run_sec_companyfacts_pull.py`) |
| `short_interest.parquet` (+ parts) | FINRA bi-monthly SI, avg volume, days to cover | 2017-12→2026-08, 44.9k tickers | Polygon (`run_short_interest_pull.py`) |
| `edgar_form10_12b.csv` | spin-off registrations | 2009→2026 | SEC EDGAR |
| `sp500_changes_wikipedia.csv`, `data/sp500_constituents.txt` | S&P 500 adds/deletes | — | Wikipedia |
| `splits_yfinance.parquet` | splits | 857 names | yfinance |
| `vix_daily_long.parquet` / `vix_daily.parquet` | VIX close | 2008-06→2026-08 / 2018→2026-09 | — |
| `economic_calendar.json`, `data/fomc_dates.json`, `data/bls_cpi_schedule.json` | macro event dates | — | — |
| `data/ticker_industry_map.csv` | ticker → industry | — | used by scans and the regime report |

### 4e. Study result caches
`pattern_*.parquet`, `stage_a_*`, `precision_*`, `bouncy_ball_*`, `size_lever_trades`, … are **outputs** of earlier
tests (`pattern_test` writes them). They are reusable for re-scoring. They are not source data.

## 5. S3 (`s3://gmerton-stock-data/`)
| prefix | what | owner |
|---|---|---|
| `breakouts/` | `preferred_tickers.txt`, `refresh_latest.txt`, `monitor_latest.json`, `eod_<date>.txt`, `minervini_matrix.parquet` | the two Lambdas; ⚠ **S3 is authoritative**, so never overwrite from local |
| `cache/` (`data/`, `ibkr_bot/`, `intraday_1min/`) | cloud copies of caches | Lambdas / bot |
| `lambda/` | Lambda zips + layer | deploy scripts |
| `AAPL/`, `TSCO/` | 2025 XBRL experiments | legacy |

## 6. Live and external sources (pull on demand)
| source | gives | limits |
|---|---|---|
| **Tradier** (`TradierClient`) | quotes, chains with ORATS greeks, daily history, ~20 sessions of 1-min | rate quota; history ≈ unadjusted |
| **IBKR** (TWS 7496 live / Gateway 4002 paper; `ibkr_bot/conn.py`) | live positions, fills (`reqExecutions`), open orders, 1-min history incl. BID_ASK | read-only for research (`readonly=True`); no expired-option history |
| **IBKR Flex** | trade confirms (1415008, same day), NAV/Activity (1605053, one session late) | via `morning_journal.sh` |
| **Polygon** | tickers incl. delisted, splits, short interest, minute aggregates | ⚠ **free tier**: 5 calls/min, ~2y history, so no bulk price history |
| **yfinance** | adjusted daily OHLCV, earnings calendar, mutual funds (long-history proxies: VFINX, VUSTX, …) | fine for backtests; prefer Tradier for live |
| **SEC EDGAR** | Forms 3/4/5, 10-12B, companyfacts, filing index | free, rate-limited |
| **TradingView MCP** | news, screener, fundamentals, calendars | sign in to tradingview.com first; `run_news_pull.py` merges it |
| **Anthropic API** | trade reviewer | `ANTHROPIC_API_KEY` |

## 7. What we do NOT have: the blind spots
- **No survivorship-free OHLCV panel.** Delisted and failed names are missing from every panel. Partial fix: `chain_spot_daily` (closes only, optionable names, incl. delisted). Blocked on paid data
  (paid Polygon, or Sharadar SEP+SF1).
- **No small-cap / micro-cap history** (ADDV < $30–50M). Blocks dilution fades, "first green day" and IPO/lockup work.
- **No borrow-cost or locate data.** Short studies assume a flat borrow (0.25–1%/yr).
- **No signed option volume** (open-buy vs open-sell). Flow studies see volume only, which is where the
  Pan–Poteshman effect lives.
- **No historical news or headline archive**, **no analyst estimate revisions / ratings history**, **no guidance data.**
- **No point-in-time fundamentals** beyond SEC companyfacts' `filed` date (the MySQL fundamentals have no vintage).
- **Option quotes end ~2026-03** (bid/ask) and IV ~2026-05. Forward option tests need Tradier/IBKR capture going
  forward.
- **Intraday single-name history is short** (2026-02 onward); only SPY/QQQ/TQQQ/SQQQ have long 1-min history.

## 8. Cache retention (value review 2026-09-25)
- **Tier A: cannot be re-pulled.** `intraday_1min/` (Tradier keeps ~20 sessions), `fill_quotes_ibkr_1min`
  (IBKR has no expired-option history), `alert_ctx_*`, `journal_intraday/`, `journal_daily/`, `gex/`, the GOOG bid/ask
  files. Backed up nightly.
- **Tier B: broad reuse, slow to rebuild.** Price panels, `intraday_hist/`, the flow and IV extracts, short interest,
  SEC pulls, QQQ/TLT/SPY chains, `vrp_panel/`, `pattern_*` (harness outputs, reused by rescoring). Kept locally and
  backed up nightly.
- **Backup:** `daily_desk.sh` ends with a detached `aws s3 sync data/{cache,backups} s3://gmerton-stock-data/backup/`
  (no `--delete`). Log: `data/studies/logs/cache_backup.log`. Restore with `aws s3 sync s3://gmerton-stock-data/backup/cache data/cache`.
- **Tier C: ARCHIVED and removed locally.** 92 single-study pulls from closed verdicts (calendar_path*, call_grid,
  tenor_window, skew_vertical, event_convexity, straddle_recenter, the July ML grid, IV-condor, SPX extracts, stage_a_*,
  …; ~4.0 GB) are in **`s3://gmerton-stock-data/archive/cache_2026-09-25/`**, S3 **Glacier Deep Archive**.
  Restoring takes **12–48 h** (`aws s3api restore-object … --restore-request Days=7`), then a copy. For most of them,
  re-pulling from v3 is faster.
- **Rule going forward:** a new study pull goes in its own `data/cache/<study>/` directory. When the study's verdict is
  final, archive that directory the same way.
