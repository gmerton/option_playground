# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas pyarrow awswrangler boto3 sqlparse aiohttp polygon-api-client requests pandas-ta
```

AWS authentication is required. Set your profile:
```bash
aws configure list-profiles
export AWS_PROFILE=clarinut-gmerton
```

The Tradier API key must be set as an environment variable:
```bash
export TRADIER_API_KEY=<your key>
```

## Running Scripts

All scripts are run from the repo root with `PYTHONPATH=src`:
```bash
PYTHONPATH=src python -m lib.commons.credit_spread_finder
PYTHONPATH=src python -m lib.leaps.leap_finder
PYTHONPATH=src python -m lib.fly.fly_finder
PYTHONPATH=src python -m lib.interface.sepa
PYTHONPATH=src python -m lib.forward.ff
```

## Architecture

The codebase is an options strategy research and screening tool with two data paths:

### 1. Live Market Data (Tradier API)
- **`src/lib/tradier/tradier_client_wrapper.py`** — async HTTP client (`TradierClient`) used as an async context manager. Always use `async with TradierClient(api_key=...) as client:` to share a single session.
- **`src/lib/commons/`** — shared async helper functions that wrap Tradier API calls:
  - `list_expirations.py` — fetch available expiration dates
  - `list_contracts.py` — fetch option chains for a given expiry
  - `get_underlying_price.py` — fetch spot price
  - `get_daily_history.py` / `tradier/get_daily_history.py` — OHLCV history for technical indicators
  - `moving_averages.py`, `high_low.py`, `pivot_detector.py`, `vol_compression.py`, `volume_breakout.py` — technical screening indicators

### 2. Historical Data (AWS Athena / S3 Tables)
- **`src/lib/athena_lib.py`** — core `athena(sql)` function using `awswrangler`. The main table is `silver.options_daily_v2` in the S3 Tables catalog (`awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket`). `ctas_approach=False` is required because `data_source` is not `AwsDataCatalog`.
- **`src/lib/constants.py`** — all Athena/S3 connection constants (`CATALOG`, `DB`, `TABLE`, `WORKGROUP`, `S3_OUTPUT`, etc.).
- Athena queries join against temporary Glue tables (written to S3 via `wr.s3.to_parquet`) for batch lookups. Both catalogs must be fully-qualified in cross-catalog JOINs: `"<S3TABLES_CATALOG>"."silver"."options_daily_v2"` vs `"AwsDataCatalog"."silver"."<tmp_table>"`.

### Strategy Modules
- **`src/lib/data/Leg.py`** — core data model. `Leg` is an immutable dataclass representing one side of a trade (direction, option type, delta target, DTE). `Strategy` wraps a list of `Leg`s. Legs are specified in "trader language" (delta + DTE) and resolved to concrete contracts later.
- **`src/lib/commons/credit_spread_finder.py`** — screens stocks for put/call credit spread, iron condor, and iron butterfly setups using live Tradier data. Computes RV20, IV30, VRP, ADX, and 25-delta skew.
- **`src/lib/fly/fly_finder.py`** — finds ATM butterfly setups (short 2x ATM, long wings) using near-term expirations.
- **`src/lib/leaps/leap_finder.py`** — finds LEAP collar plays (long stock + protective ATM put + covered call) on low-priced stocks (<$30), screening expirations ≥5 months out.
- **`src/lib/double_calendar/double_calendar.py`** — double calendar spread analysis (near 10–15 DTE front leg, 7–14 DTE further back leg).
- **`src/lib/interface/sepa.py`** — SEPA (Stan Weinstein / Mark Minervini) momentum screening (MA rules, 52-week range, pivot signals) using Tradier daily history.
- **`src/lib/forward/ff.py`** — forward volatility ("vol of vol") calculation between two expiries.

### Lambda Deployment
`buildspec.yml` packages `src/` into `function.zip` and deploys to the `options_toolkit_prod` Lambda function via AWS CodeBuild.

## Key Patterns

- All live data helpers are `async` and accept a `TradierClient` instance. Older modules sometimes use bare `aiohttp` sessions directly — prefer the `TradierClient` wrapper for new code.
- `RuntimeError` is used as the standard exception for non-fatal screening failures (e.g., missing data, insufficient liquidity). Callers typically swallow these to skip symbols.
- Ticker lists (NYSE, NASDAQ, curated watchlists) live in `src/lib/commons/nyse_arca_list.py`.
- The `src/lib/earnings/` module handles earnings-specific option queries and caching against Athena.
