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
import numpy as np
import pandas as pd
from polygon import RESTClient
from py_vollib_vectorized import (
    vectorized_implied_volatility,
    vectorized_delta,
    vectorized_gamma,
    vectorized_theta,
    vectorized_vega,
)

# Risk-free rate proxy for IV solve. ~1Y Treasury yield. Refine later if needed.
RISK_FREE_RATE = 0.045

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
    """Return the most recent market date in US/Eastern time.

    The scheduled job runs at 10 PM ET, well after market close, so
    'today' is always the correct trade date.  But if someone triggers
    a manual run after midnight ET (e.g. from Pacific time), the clock
    has already rolled to tomorrow — roll back to the previous weekday
    so we never tag data with a future date.
    """
    try:
        import zoneinfo
        et = zoneinfo.ZoneInfo("America/New_York")
    except ImportError:
        et = timezone(timedelta(hours=-5))

    now_et = datetime.now(tz=et)
    d = now_et.date()

    # Before 8 AM ET the market hasn't opened — use the previous weekday
    if now_et.hour < 8:
        d -= timedelta(days=1)
        while d.weekday() >= 5:   # roll back over Saturday / Sunday
            d -= timedelta(days=1)

    return d


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
    """Convert Polygon option snapshot objects to v3 schema rows.

    The current Polygon plan returns last_quote, greeks, and implied_volatility
    as None for option contracts. So we read price from the day's OHLC
    (close → vwap fallback) and leave Greeks/IV blank — they are computed
    later by compute_iv_and_greeks() once we have the underlying spot price.
    """
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

            day = snap.day
            day_close  = getattr(day, "close",  None) if day else None
            day_vwap   = getattr(day, "vwap",   None) if day else None
            day_volume = getattr(day, "volume", None) if day else None

            if bid is not None and ask is not None and bid > 0 and ask > 0:
                last = (bid + ask) / 2
            elif day_close is not None and day_close > 0:
                last = day_close
            elif day_vwap is not None and day_vwap > 0:
                last = day_vwap
            else:
                last = None

            oi = getattr(snap, "open_interest", None)

            rows.append({
                "trade_date":    trade_date,
                "ticker":        ticker,
                "cp":            cp,
                "strike":        float(strike),
                "expiry":        expiry,
                "bid":           float(bid)  if bid  is not None else None,
                "ask":           float(ask)  if ask  is not None else None,
                "last":          float(last) if last is not None else None,
                "bid_iv":        None,
                "ask_iv":        None,
                "open_interest": int(oi)         if oi         is not None else None,
                "volume":        int(day_volume) if day_volume is not None else None,
                "delta":         None,
                "gamma":         None,
                "theta":         None,
                "vega":          None,
                "rho":           0.0,
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


def fetch_underlying_closes(
    client: RESTClient,
    trade_date: date,
    tickers: list[str] | None = None,
) -> dict[str, float]:
    """Fetch dict {ticker: close_price} for trade_date.

    Strategy: grouped daily aggregates first (one API call for ~12k tickers).
    On the day-of-run, Polygon's grouped endpoint can return NOT_AUTHORIZED
    ("before end of day") even after market close — when that happens we
    fall back to per-ticker get_aggs (parallelized) for whichever tickers
    in the universe are still missing. Per-ticker bars are available faster
    after close than the grouped aggregate.
    """
    print(f"Fetching underlying closes for {trade_date} ...")
    result: dict[str, float] = {}

    try:
        for agg in client.get_grouped_daily_aggs(
            date=str(trade_date), adjusted=True, locale="us", market_type="stocks"
        ):
            tk = getattr(agg, "ticker", None)
            cl = getattr(agg, "close", None)
            if tk and cl is not None and cl > 0:
                result[tk] = float(cl)
        print(f"  grouped: {len(result):,} closes")
    except Exception as e:
        print(f"  [WARN] grouped daily aggs failed: {e}")

    if tickers:
        missing = [t for t in tickers if t not in result]
        if missing:
            print(f"  fallback: per-ticker fetch for {len(missing):,} missing tickers ...")
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _fetch_one(t: str) -> tuple[str, float | None]:
                try:
                    bars = list(client.get_aggs(
                        ticker=t, multiplier=1, timespan="day",
                        from_=str(trade_date), to=str(trade_date),
                        adjusted=True, limit=1,
                    ))
                    if bars and bars[0].close is not None and bars[0].close > 0:
                        return t, float(bars[0].close)
                except Exception:
                    pass
                return t, None

            recovered = 0
            with ThreadPoolExecutor(max_workers=8) as ex:
                for fut in as_completed([ex.submit(_fetch_one, t) for t in missing]):
                    t, c = fut.result()
                    if c is not None:
                        result[t] = c
                        recovered += 1
            print(f"  fallback recovered {recovered:,} additional closes")

    print(f"  total: {len(result):,} underlying close prices loaded")
    return result


def compute_iv_and_greeks(
    df: pd.DataFrame,
    underlying_closes: dict[str, float],
    trade_date: date,
    risk_free_rate: float = RISK_FREE_RATE,
) -> pd.DataFrame:
    """Solve for IV from `last`, then compute delta/gamma/theta/vega.

    Mutates `df` in place and returns it. Rows missing a usable price or
    underlying spot are left with NaN for IV/Greeks.
    """
    if df.empty:
        return df

    S = df["ticker"].map(underlying_closes).astype("float64")
    T = df["expiry"].apply(
        lambda e: max((e - trade_date).days / 365.0, 1.0 / 365.0)
    ).astype("float64")
    flag = df["cp"].str.lower().values  # 'c' or 'p'

    last = pd.to_numeric(df["last"], errors="coerce")
    eligible = last.notna() & (last > 0) & S.notna() & (T > 0)
    if not eligible.any():
        return df

    idx = df.index[eligible]
    price = last.loc[idx].values
    s_vec = S.loc[idx].values
    k_vec = df.loc[idx, "strike"].astype("float64").values
    t_vec = T.loc[idx].values
    f_vec = pd.Series(flag).loc[idx].values

    try:
        iv = vectorized_implied_volatility(
            price=price, S=s_vec, K=k_vec, t=t_vec,
            r=risk_free_rate, flag=f_vec, return_as="numpy",
        )
    except Exception as e:
        print(f"  [WARN] IV solve failed: {e}")
        return df

    iv = np.where(np.isfinite(iv) & (iv > 0.001) & (iv < 5.0), iv, np.nan)
    valid = ~np.isnan(iv)
    if not valid.any():
        return df

    v_idx = idx[valid]
    kw = dict(
        S=s_vec[valid], K=k_vec[valid], t=t_vec[valid],
        r=risk_free_rate, sigma=iv[valid], flag=f_vec[valid], return_as="numpy",
    )
    try:
        d_arr  = vectorized_delta(**kw)
        g_arr  = vectorized_gamma(**kw)
        th_arr = vectorized_theta(**kw)
        ve_arr = vectorized_vega(**kw)
    except Exception as e:
        print(f"  [WARN] Greeks computation failed: {e}")
        return df

    df.loc[v_idx, "bid_iv"] = iv[valid]
    df.loc[v_idx, "ask_iv"] = iv[valid]
    df.loc[v_idx, "delta"]  = d_arr
    df.loc[v_idx, "gamma"]  = g_arr
    df.loc[v_idx, "theta"]  = th_arr
    df.loc[v_idx, "vega"]   = ve_arr

    return df


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

    # ── Underlying spot prices (grouped first, per-ticker fallback) ──────────
    underlying_closes = fetch_underlying_closes(client, trade_date, tickers)

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
            combined = compute_iv_and_greeks(combined, underlying_closes, trade_date)
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
        combined = compute_iv_and_greeks(combined, underlying_closes, trade_date)
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
