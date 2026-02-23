#!/usr/bin/env python3
"""
Nightly Polygon.io → options_daily_v3 updater.

Fetches end-of-day option snapshots for every ticker in the combined
NYSE/NASDAQ/NYSE-Arca universe (≈10,000 symbols) and inserts them into
silver.options_daily_v3 via Glue temp table + Athena INSERT.

Usage (local):
    AWS_PROFILE=clarinut-gmerton POLYGON_API_KEY=<key> python daily_updater.py
    AWS_PROFILE=clarinut-gmerton POLYGON_API_KEY=<key> python daily_updater.py --dry-run
    AWS_PROFILE=clarinut-gmerton POLYGON_API_KEY=<key> python daily_updater.py --tickers AAPL,IBIT,SPY

Build & run with Docker:
    docker build -t options-daily-updater .
    docker run --rm \
        -e POLYGON_API_KEY=<key> \
        -e AWS_DEFAULT_REGION=us-west-2 \
        options-daily-updater
"""

import argparse
import os
import sys
import time
import uuid
from datetime import date, datetime, timedelta, timezone

import awswrangler as wr
import pandas as pd
from polygon import RESTClient

# ── Athena / S3 Tables configuration ────────────────────────────────────────
CATALOG       = "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"
WORKGROUP     = "dev-v3"
S3_OUTPUT     = "s3://athena-919061006621/"
DB            = "silver"
TABLE         = "options_daily_v3"
TMP_S3_PREFIX = "s3://athena-919061006621/tmp_targets/"
GLUE_CATALOG  = "AwsDataCatalog"

# ── Column ordering must match options_daily_v3 schema ──────────────────────
V3_COLS = [
    "trade_date", "strike", "expiry", "cp", "last", "bid", "ask",
    "bid_iv", "ask_iv", "open_interest", "volume", "delta", "gamma",
    "vega", "theta", "rho", "resolution", "ticker",
]

GLUE_DTYPE = {
    "trade_date":    "date",
    "expiry":        "date",
    "ticker":        "string",
    "cp":            "string",
    "resolution":    "string",
    "strike":        "double",
    "last":          "double",
    "bid":           "double",
    "ask":           "double",
    "bid_iv":        "double",
    "ask_iv":        "double",
    "open_interest": "bigint",
    "volume":        "bigint",
    "delta":         "double",
    "gamma":         "double",
    "vega":          "double",
    "theta":         "double",
    "rho":           "double",
}

# Batch size: flush to Athena after this many tickers to keep memory bounded.
# At ~300 contracts/ticker average, 500 tickers ≈ 150k rows ≈ a few MB.
BATCH_SIZE = 500

# Options Starter is unlimited (no per-minute cap); no sleep needed.

# Retry config for 429 / transient errors
MAX_RETRIES = 3
RETRY_BACKOFF = [5, 15, 30]  # seconds


def _ensure_glue_db(database: str) -> None:
    """Ensure a Glue database exists (creates it if missing)."""
    try:
        if hasattr(wr.catalog, "does_database_exist"):
            if not wr.catalog.does_database_exist(name=database):
                wr.catalog.create_database(name=database)
            return
        # Fallback for older awswrangler
        dbs = wr.catalog.get_databases()
        names = {d.get("Name") or d.get("name") for d in dbs if isinstance(d, dict)}
        if database not in names:
            wr.catalog.create_database(name=database)
    except Exception as e:
        raise RuntimeError(f"Failed to ensure Glue database '{database}': {e}") from e


def get_tickers(client: RESTClient, override: list[str] | None = None) -> list[str]:
    """
    Return sorted, deduped list of tickers to process.
    If override is given, use that. Otherwise fetch all active tickers from
    NYSE, NASDAQ, and NYSE Arca (excludes OTC/pink sheets).
    """
    if override:
        return sorted(set(t.upper() for t in override))

    print("Fetching ticker universe from Polygon...")
    tickers = set()
    for exchange in ("XNYS", "XNAS", "ARCX"):
        for t in client.list_tickers(market="stocks", exchange=exchange, active=True, limit=1000):
            tickers.add(t.ticker)
    result = sorted(tickers)
    print(f"  {len(result):,} active tickers fetched (NYSE + NASDAQ + NYSE Arca)")
    return result


def today_et() -> date:
    """Return today's date in US/Eastern time (DST-aware)."""
    try:
        import zoneinfo
        et = zoneinfo.ZoneInfo("America/New_York")
        return datetime.now(tz=et).date()
    except ImportError:
        # Fallback: UTC-5 (EST); close enough for a nightly job
        return datetime.now(tz=timezone(timedelta(hours=-5))).date()


def check_already_loaded(trade_date: date) -> bool:
    """Return True if options_daily_v3 already has rows for trade_date."""
    sql = f"""
    SELECT COUNT(*) AS n
    FROM "{DB}"."{TABLE}"
    WHERE trade_date = DATE '{trade_date}'
    """
    df = wr.athena.read_sql_query(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        data_source=CATALOG,
        s3_output=S3_OUTPUT,
        ctas_approach=False,
    )
    return int(df["n"].iloc[0]) > 0


def delete_existing(trade_date: date) -> None:
    """Delete all rows for trade_date (allows idempotent re-run)."""
    print(f"  Deleting existing rows for {trade_date} ...")
    sql = f"""
    DELETE FROM "{DB}"."{TABLE}"
    WHERE trade_date = DATE '{trade_date}'
    """
    qid = wr.athena.start_query_execution(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        data_source=CATALOG,
        s3_output=S3_OUTPUT,
    )
    wr.athena.wait_query(query_execution_id=qid)
    print("  Delete complete.")


def fetch_polygon_snapshot(client: RESTClient, ticker: str) -> list:
    """
    Fetch all option contracts for ticker from Polygon snapshot endpoint.
    Returns list of raw snapshot objects.
    Raises RuntimeError on persistent failure.
    """
    for attempt in range(MAX_RETRIES):
        try:
            results = []
            for snap in client.list_snapshot_options_chain(ticker):
                results.append(snap)
            return results
        except Exception as e:
            msg = str(e)
            if "429" in msg or "Too Many Requests" in msg:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"    [429] rate limited, waiting {wait}s ...")
                time.sleep(wait)
            else:
                raise RuntimeError(f"Polygon error for {ticker}: {e}") from e
    raise RuntimeError(f"Polygon max retries exceeded for {ticker}")


def transform_snapshot(snapshots: list, ticker: str, trade_date: date) -> pd.DataFrame:
    """Convert Polygon option snapshot objects to v3 schema rows."""
    rows = []
    for snap in snapshots:
        try:
            details = snap.details
            if details is None:
                continue

            cp_raw = getattr(details, "contract_type", None)
            if cp_raw not in ("call", "put"):
                continue
            cp = "C" if cp_raw == "call" else "P"

            strike = getattr(details, "strike_price", None)
            expiry_raw = getattr(details, "expiration_date", None)
            if strike is None or expiry_raw is None:
                continue
            expiry = date.fromisoformat(expiry_raw) if isinstance(expiry_raw, str) else expiry_raw

            quote = snap.last_quote
            bid = getattr(quote, "bid", None) if quote else None
            ask = getattr(quote, "ask", None) if quote else None
            midpoint = getattr(quote, "midpoint", None) if quote else None

            if bid is not None and ask is not None:
                last = (bid + ask) / 2
            elif midpoint is not None:
                last = midpoint
            else:
                last = None

            iv = getattr(snap, "implied_volatility", None)

            day = snap.day
            volume = getattr(day, "volume", None) if day else None
            oi = getattr(snap, "open_interest", None)

            greeks = snap.greeks
            delta = getattr(greeks, "delta", None) if greeks else None
            gamma = getattr(greeks, "gamma", None) if greeks else None
            theta = getattr(greeks, "theta", None) if greeks else None
            vega  = getattr(greeks, "vega",  None) if greeks else None
            rho   = getattr(greeks, "rho",   None) if greeks else 0.0

            rows.append({
                "trade_date":    trade_date,
                "ticker":        ticker,
                "cp":            cp,
                "strike":        float(strike),
                "expiry":        expiry,
                "bid":           float(bid)    if bid    is not None else None,
                "ask":           float(ask)    if ask    is not None else None,
                "last":          float(last)   if last   is not None else None,
                "bid_iv":        float(iv)     if iv     is not None else None,
                "ask_iv":        float(iv)     if iv     is not None else None,
                "open_interest": int(oi)       if oi     is not None else None,
                "volume":        int(volume)   if volume is not None else None,
                "delta":         float(delta)  if delta  is not None else None,
                "gamma":         float(gamma)  if gamma  is not None else None,
                "theta":         float(theta)  if theta  is not None else None,
                "vega":          float(vega)   if vega   is not None else None,
                "rho":           float(rho)    if rho    is not None else 0.0,
                "resolution":    "daily",
            })
        except Exception:
            continue

    if not rows:
        return pd.DataFrame(columns=V3_COLS)

    df = pd.DataFrame(rows)
    df["open_interest"] = df["open_interest"].astype("Int64")
    df["volume"]        = df["volume"].astype("Int64")
    return df[V3_COLS]


def athena_insert(tmp_table: str) -> None:
    """INSERT rows from Glue temp table into options_daily_v3."""
    sql = f"""
    INSERT INTO "{DB}"."{TABLE}"
    SELECT trade_date, strike, expiry, cp, last, bid, ask,
           bid_iv, ask_iv, open_interest, volume, delta, gamma,
           vega, theta, rho, resolution, ticker
    FROM "{GLUE_CATALOG}"."{DB}"."{tmp_table}"
    """
    qid = wr.athena.start_query_execution(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        data_source=CATALOG,
        s3_output=S3_OUTPUT,
    )
    wr.athena.wait_query(query_execution_id=qid)


def flush_batch(batch_df: pd.DataFrame, dry_run: bool) -> int:
    """Write batch_df to Glue + Athena INSERT. Returns row count."""
    n_rows = len(batch_df)
    if n_rows == 0:
        return 0
    if dry_run:
        print(f"    [dry-run] would insert {n_rows:,} rows")
        return n_rows

    tmp_table = f"tmp_daily_{uuid.uuid4().hex}"
    tmp_path  = TMP_S3_PREFIX.rstrip("/") + f"/{tmp_table}/"

    _ensure_glue_db(DB)
    wr.s3.to_parquet(
        df=batch_df,
        path=tmp_path,
        dataset=True,
        database=DB,
        table=tmp_table,
        compression="snappy",
        mode="overwrite",
        dtype=GLUE_DTYPE,
    )
    try:
        athena_insert(tmp_table)
    finally:
        wr.catalog.delete_table_if_exists(database=DB, table=tmp_table)
        wr.s3.delete_objects(tmp_path)

    return n_rows


def main():
    parser = argparse.ArgumentParser(description="Nightly Polygon → options_daily_v3 updater")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch and transform only; skip all Athena writes")
    parser.add_argument("--tickers", default=None,
                        help="Comma-separated ticker override, e.g. AAPL,IBIT,SPY")
    parser.add_argument("--date", default=None,
                        help="Trade date override YYYY-MM-DD (default: today ET)")
    parser.add_argument("--force", action="store_true",
                        help="Re-run even if today already has data (delete first)")
    args = parser.parse_args()

    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        print("ERROR: POLYGON_API_KEY environment variable not set.")
        sys.exit(1)

    trade_date = date.fromisoformat(args.date) if args.date else today_et()
    print(f"Trade date: {trade_date}")

    client = RESTClient(api_key)

    ticker_override = [t.strip() for t in args.tickers.split(",")] if args.tickers else None
    tickers = get_tickers(client, ticker_override)
    print(f"Tickers to process: {len(tickers):,}")

    # ── Idempotency guard ────────────────────────────────────────────────────
    if not args.dry_run:
        already = check_already_loaded(trade_date)
        if already:
            if args.force:
                delete_existing(trade_date)
            else:
                print(f"Data for {trade_date} already exists in {TABLE}. "
                      "Use --force to re-run (will delete existing rows first).")
                sys.exit(0)

    # ── Main loop ─────────────────────────────────────────────────────────────
    t_total       = time.perf_counter()
    rows_inserted = 0
    tickers_ok    = 0
    tickers_empty = 0
    tickers_err   = 0
    errors        = []

    batch_frames: list[pd.DataFrame] = []
    batch_tickers = 0

    for i, ticker in enumerate(tickers):
        try:
            snapshots = fetch_polygon_snapshot(client, ticker)
            df = transform_snapshot(snapshots, ticker, trade_date)

            if df.empty:
                tickers_empty += 1
            else:
                batch_frames.append(df)
                tickers_ok += 1

        except Exception as e:
            tickers_err += 1
            errors.append((ticker, str(e)))
            if len(errors) <= 20:
                print(f"  [ERROR] {ticker}: {e}")

        if (i + 1) % 100 == 0:
            elapsed = time.perf_counter() - t_total
            print(f"  {i+1}/{len(tickers)} tickers  "
                  f"ok={tickers_ok} empty={tickers_empty} err={tickers_err}  "
                  f"[{elapsed/60:.1f}m]")

        batch_tickers += 1
        if batch_tickers >= BATCH_SIZE and batch_frames:
            combined = pd.concat(batch_frames, ignore_index=True)
            t0 = time.perf_counter()
            n = flush_batch(combined, args.dry_run)
            rows_inserted += n
            print(f"  >> Flushed batch: {n:,} rows in {time.perf_counter()-t0:.1f}s "
                  f"(total inserted: {rows_inserted:,})")
            batch_frames = []
            batch_tickers = 0

    # Flush remainder
    if batch_frames:
        combined = pd.concat(batch_frames, ignore_index=True)
        t0 = time.perf_counter()
        n = flush_batch(combined, args.dry_run)
        rows_inserted += n
        print(f"  >> Final flush: {n:,} rows in {time.perf_counter()-t0:.1f}s")

    # ── Summary ──────────────────────────────────────────────────────────────
    elapsed_total = time.perf_counter() - t_total
    print(f"\n{'='*60}")
    print(f"  Daily updater complete — {trade_date}")
    print(f"{'='*60}")
    print(f"  Tickers processed : {len(tickers):,}")
    print(f"  Tickers with data : {tickers_ok:,}")
    print(f"  Tickers empty     : {tickers_empty:,}")
    print(f"  Tickers errored   : {tickers_err:,}")
    print(f"  Rows inserted     : {rows_inserted:,}")
    print(f"  Total time        : {elapsed_total/60:.1f}m")
    if args.dry_run:
        print(f"  [DRY RUN — no Athena writes performed]")
    if errors:
        print(f"\nFirst {min(len(errors), 20)} errors:")
        for t, e in errors[:20]:
            print(f"  {t}: {e}")

    if tickers_err > 0 and len(tickers) > 0:
        error_rate = tickers_err / len(tickers)
        if error_rate > 0.20:
            print(f"\nERROR: Error rate {error_rate:.1%} exceeds 20% threshold.")
            sys.exit(1)


if __name__ == "__main__":
    main()
