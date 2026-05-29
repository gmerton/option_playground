#!/usr/bin/env python3
"""
One-off backfill of options_daily_v3 from Polygon's per-contract historical
aggregates, for the active strategy universe (Friday screener tickers +
long-straddle walk-forward set, ~220 tickers).

The nightly daily_updater handles new days going forward; this script fills
the gap from when the snapshot-based ingestion stopped writing prices
(2026-02-21) up through `--end`.

Bid/ask remain NULL (no NBBO on this Polygon plan). open_interest is also
NULL for backfilled rows (aggs endpoint doesn't return it). last comes from
agg.close (or vwap fallback) and IV/Greeks are computed via py_vollib.

Usage:
    AWS_PROFILE=clarinut-gmerton POLYGON_API_KEY=<key> \\
        PYTHONPATH=src .venv/bin/python3 run_backfill_options_v3.py \\
            --start 2026-02-21 --end 2026-04-30

    # Smoke-test single ticker:
    ... run_backfill_options_v3.py --start 2026-04-15 --end 2026-04-30 \\
            --tickers INTC --dry-run
"""

import argparse
import concurrent.futures
import os
import sys
import time
import uuid
from datetime import date, datetime

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

# ── Athena / S3 Tables config (must match daily_updater) ──────────────────
CATALOG       = "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"
WORKGROUP     = "dev-v3"
S3_OUTPUT     = "s3://athena-919061006621/"
DB            = "silver"
TABLE         = "options_daily_v3"
TMP_S3_PREFIX = "s3://athena-919061006621/tmp_targets/"
GLUE_CATALOG  = "AwsDataCatalog"
RISK_FREE_RATE = 0.045

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

# Tickers that appear in the Friday screener (hardcoded — extracted from
# run_friday_screener.py). VIX is the index, not optionable, so excluded.
SCREENER_TICKERS = {
    "ASHR", "BJ", "CLS", "GEV", "GLD", "INDA", "QQQ", "SOXX", "SPY",
    "SQQQ", "TLT", "TMF", "USO", "UUP", "UVIX", "UVXY",
    "XLE", "XLF", "XLP", "XLU", "XLV", "XOP",
}


def get_universe(straddle_csv: str = "straddle_walkforward_ticker_persistence.csv") -> list[str]:
    """Union of screener tickers + straddle walk-forward universe."""
    straddle = set()
    try:
        df = pd.read_csv(straddle_csv)
        straddle = set(df["ticker"].astype(str).str.upper())
    except FileNotFoundError:
        print(f"[WARN] {straddle_csv} not found — using screener tickers only")
    universe = SCREENER_TICKERS | straddle
    return sorted(universe)


def fetch_underlying_history(client: RESTClient, ticker: str,
                             start: date, end: date) -> dict[date, float]:
    """Daily close for ticker between start and end (one API call)."""
    out: dict[date, float] = {}
    try:
        bars = client.get_aggs(
            ticker=ticker, multiplier=1, timespan="day",
            from_=str(start), to=str(end), adjusted=True, limit=50000,
        )
        for bar in bars:
            d = datetime.fromtimestamp(bar.timestamp / 1000).date()
            if bar.close is not None and bar.close > 0:
                out[d] = float(bar.close)
    except Exception as e:
        print(f"  [WARN] underlying history failed for {ticker}: {e}")
    return out


def list_contracts(client: RESTClient, ticker: str, start: date) -> list:
    """All contracts (active + expired-after-start) for a ticker, deduped."""
    contracts = []
    try:
        for c in client.list_options_contracts(
            underlying_ticker=ticker, expired=False, limit=1000,
        ):
            contracts.append(c)
        for c in client.list_options_contracts(
            underlying_ticker=ticker, expired=True,
            expiration_date_gte=str(start), limit=1000,
        ):
            contracts.append(c)
    except Exception as e:
        print(f"  [WARN] list_contracts failed for {ticker}: {e}")
        return []
    seen = set()
    out = []
    for c in contracts:
        if c.ticker not in seen:
            seen.add(c.ticker)
            out.append(c)
    return out


def fetch_contract_bars(client: RESTClient, contract_ticker: str,
                        start: date, end: date) -> list:
    """OHLC bars for one option contract over date range."""
    try:
        return list(client.get_aggs(
            ticker=contract_ticker, multiplier=1, timespan="day",
            from_=str(start), to=str(end), limit=50000,
        ))
    except Exception:
        return []


def process_ticker(client: RESTClient, ticker: str,
                   start: date, end: date) -> pd.DataFrame:
    """Fetch all option data for one ticker over [start, end]."""
    underlying = fetch_underlying_history(client, ticker, start, end)
    if not underlying:
        return pd.DataFrame()

    contracts = list_contracts(client, ticker, start)
    if not contracts:
        return pd.DataFrame()

    rows = []
    for c in contracts:
        cp_raw = getattr(c, "contract_type", None)
        if cp_raw not in ("call", "put"):
            continue
        cp = "C" if cp_raw == "call" else "P"

        try:
            exp = c.expiration_date
            expiry = date.fromisoformat(exp) if isinstance(exp, str) else exp
        except Exception:
            continue

        bars = fetch_contract_bars(client, c.ticker, start, end)
        if not bars:
            continue

        strike = float(c.strike_price)
        for bar in bars:
            d = datetime.fromtimestamp(bar.timestamp / 1000).date()
            if d not in underlying:
                continue
            close = bar.close if bar.close and bar.close > 0 else (
                bar.vwap if getattr(bar, "vwap", None) else None
            )
            if not close:
                continue
            rows.append({
                "trade_date":    d,
                "ticker":        ticker,
                "cp":            cp,
                "strike":        strike,
                "expiry":        expiry,
                "bid":           None,
                "ask":           None,
                "last":          float(close),
                "bid_iv":        None,
                "ask_iv":        None,
                "open_interest": None,
                "volume":        int(bar.volume) if bar.volume else None,
                "delta":         None,
                "gamma":         None,
                "theta":         None,
                "vega":          None,
                "rho":           0.0,
                "resolution":    "daily",
                "S":             underlying[d],
            })

    return pd.DataFrame(rows)


def compute_iv_greeks_backfill(df: pd.DataFrame,
                               risk_free_rate: float = RISK_FREE_RATE) -> pd.DataFrame:
    """Vectorized IV solve + Greeks. Spot is per-row in the 'S' column."""
    if df.empty:
        return df

    T = (pd.to_datetime(df["expiry"]) - pd.to_datetime(df["trade_date"])).dt.days / 365.0
    T = T.clip(lower=1.0 / 365.0).astype("float64")

    last = pd.to_numeric(df["last"], errors="coerce")
    eligible = last.notna() & (last > 0) & df["S"].notna() & (T > 0)
    if not eligible.any():
        return df

    idx = df.index[eligible]
    flag = df.loc[idx, "cp"].str.lower().values
    s_vec = df.loc[idx, "S"].astype("float64").values
    k_vec = df.loc[idx, "strike"].astype("float64").values
    t_vec = T.loc[idx].values
    p_vec = last.loc[idx].astype("float64").values

    try:
        iv = vectorized_implied_volatility(
            price=p_vec, S=s_vec, K=k_vec, t=t_vec,
            r=risk_free_rate, flag=flag, return_as="numpy",
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
        r=risk_free_rate, sigma=iv[valid], flag=flag[valid], return_as="numpy",
    )
    try:
        df.loc[v_idx, "delta"] = vectorized_delta(**kw)
        df.loc[v_idx, "gamma"] = vectorized_gamma(**kw)
        df.loc[v_idx, "theta"] = vectorized_theta(**kw)
        df.loc[v_idx, "vega"]  = vectorized_vega(**kw)
        df.loc[v_idx, "bid_iv"] = iv[valid]
        df.loc[v_idx, "ask_iv"] = iv[valid]
    except Exception as e:
        print(f"  [WARN] Greeks failed: {e}")

    return df


def delete_existing(tickers: list[str], start: date, end: date) -> None:
    chunks = [tickers[i:i + 200] for i in range(0, len(tickers), 200)]
    print(f"Deleting existing rows for {len(tickers)} tickers in [{start}, {end}] "
          f"({len(chunks)} delete batches) ...")
    for i, chunk in enumerate(chunks, 1):
        tickers_sql = ", ".join(f"'{t}'" for t in chunk)
        sql = f"""
        DELETE FROM "{DB}"."{TABLE}"
        WHERE ticker IN ({tickers_sql})
          AND trade_date BETWEEN DATE '{start}' AND DATE '{end}'
        """
        qid = wr.athena.start_query_execution(
            sql=sql, database=DB, workgroup=WORKGROUP,
            data_source=CATALOG, s3_output=S3_OUTPUT,
        )
        wr.athena.wait_query(query_execution_id=qid)
        print(f"  delete batch {i}/{len(chunks)} done")
    print("Delete complete.")


def athena_insert(tmp_table: str) -> None:
    sql = f"""
    INSERT INTO "{DB}"."{TABLE}"
    SELECT trade_date, strike, expiry, cp, last, bid, ask,
           bid_iv, ask_iv, open_interest, volume, delta, gamma,
           vega, theta, rho, resolution, ticker
    FROM "{GLUE_CATALOG}"."{DB}"."{tmp_table}"
    """
    qid = wr.athena.start_query_execution(
        sql=sql, database=DB, workgroup=WORKGROUP,
        data_source=CATALOG, s3_output=S3_OUTPUT,
    )
    wr.athena.wait_query(query_execution_id=qid)


def flush_batch(df: pd.DataFrame, dry_run: bool) -> int:
    if df.empty:
        return 0
    df = df[V3_COLS].copy()
    df["open_interest"] = df["open_interest"].astype("Int64")
    df["volume"]        = df["volume"].astype("Int64")
    n = len(df)
    if dry_run:
        print(f"    [dry-run] would insert {n:,} rows")
        return n

    tmp_table = f"tmp_backfill_{uuid.uuid4().hex}"
    tmp_path  = TMP_S3_PREFIX.rstrip("/") + f"/{tmp_table}/"
    wr.s3.to_parquet(
        df=df, path=tmp_path, dataset=True, database=DB, table=tmp_table,
        compression="snappy", mode="overwrite", dtype=GLUE_DTYPE,
    )
    try:
        athena_insert(tmp_table)
    finally:
        wr.catalog.delete_table_if_exists(database=DB, table=tmp_table)
        wr.s3.delete_objects(tmp_path)
    return n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end",   required=True, help="YYYY-MM-DD")
    parser.add_argument("--tickers", default=None,
                        help="Comma-separated override (default: screener+straddle universe)")
    parser.add_argument("--workers", type=int, default=8,
                        help="Concurrent ticker workers (default 8)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-delete", action="store_true",
                        help="Skip delete-existing-rows step")
    parser.add_argument("--batch-tickers", type=int, default=5,
                        help="Tickers per Athena flush (default 5)")
    args = parser.parse_args()

    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        print("ERROR: POLYGON_API_KEY not set"); sys.exit(1)

    start = date.fromisoformat(args.start)
    end   = date.fromisoformat(args.end)

    if args.tickers:
        tickers = sorted({t.strip().upper() for t in args.tickers.split(",")})
    else:
        tickers = get_universe()
    print(f"Backfill: {start} → {end}  |  {len(tickers)} tickers  |  "
          f"workers={args.workers}  |  batch={args.batch_tickers}")

    if not args.dry_run and not args.no_delete:
        delete_existing(tickers, start, end)

    client = RESTClient(api_key)
    rows_total    = 0
    tickers_done  = 0
    tickers_empty = 0
    tickers_err   = 0
    batch         = []
    t_run         = time.perf_counter()

    def _process(ticker):
        try:
            return ticker, process_ticker(client, ticker, start, end), None
        except Exception as e:
            return ticker, pd.DataFrame(), str(e)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(_process, t): t for t in tickers}
        for fut in concurrent.futures.as_completed(futures):
            ticker, df, err = fut.result()
            tickers_done += 1
            if err:
                tickers_err += 1
                print(f"  [{tickers_done}/{len(tickers)}] {ticker}: ERROR {err}")
                continue
            if df.empty:
                tickers_empty += 1
                print(f"  [{tickers_done}/{len(tickers)}] {ticker}: empty")
                continue
            batch.append(df)
            print(f"  [{tickers_done}/{len(tickers)}] {ticker}: {len(df):,} rows")

            if len(batch) >= args.batch_tickers:
                combined = pd.concat(batch, ignore_index=True)
                combined = compute_iv_greeks_backfill(combined)
                combined = combined.drop(columns=["S"])
                t0 = time.perf_counter()
                n = flush_batch(combined, args.dry_run)
                rows_total += n
                print(f"    >> Flushed {n:,} rows in {time.perf_counter()-t0:.1f}s "
                      f"(total {rows_total:,})")
                batch = []

    if batch:
        combined = pd.concat(batch, ignore_index=True)
        combined = compute_iv_greeks_backfill(combined)
        combined = combined.drop(columns=["S"])
        t0 = time.perf_counter()
        n = flush_batch(combined, args.dry_run)
        rows_total += n
        print(f"    >> Final flush {n:,} rows in {time.perf_counter()-t0:.1f}s")

    elapsed = (time.perf_counter() - t_run) / 60
    print(f"\n{'='*60}")
    print(f"  Backfill complete  —  [{start}, {end}]")
    print(f"{'='*60}")
    print(f"  Tickers processed : {tickers_done}")
    print(f"  Tickers with data : {tickers_done - tickers_empty - tickers_err}")
    print(f"  Tickers empty     : {tickers_empty}")
    print(f"  Tickers errored   : {tickers_err}")
    print(f"  Rows inserted     : {rows_total:,}")
    print(f"  Total time        : {elapsed:.1f}m")
    if args.dry_run:
        print(f"  [DRY RUN — no Athena writes performed]")


if __name__ == "__main__":
    main()
