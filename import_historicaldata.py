#!/usr/bin/env python3
"""
Import historicaldata.net monthly zip files into silver.options_daily_v3.

Usage:
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python3 import_historicaldata.py
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python3 import_historicaldata.py --dry-run
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python3 import_historicaldata.py --from-date 2025-11-01

Processes one trading day at a time to keep memory bounded (~1M rows per day).
Skips any dates already in v3 (i.e., <= 2025-08-29).
"""

import argparse
import os
import sys
import time
import uuid
import zipfile
from datetime import date

import awswrangler as wr
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lib.constants import (
    CATALOG, DB, GLUE_CATALOG, S3_OUTPUT,
    S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX, WORKGROUP,
)
from lib.athena_lib import _ensure_glue_db

DOWNLOADS = os.path.expanduser("~/Downloads")

ZIPS = [
    "2025-08.zip",   # mostly already in v3; rows <= CUTOFF are skipped
    "2025-09.zip",
    "2025-10.zip",
    "2025-11.zip",
    "2025-12.zip",
    "2026-01.zip",
    "2026-02.zip",
]

CUTOFF = date(2025, 8, 29)  # v3 already has data through this date

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


def transform(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Map historicaldata.net columns to the v3 schema."""
    d = pd.DataFrame()
    d["trade_date"]    = pd.to_datetime(df_raw["quote_date"], errors="coerce").dt.date
    d["ticker"]        = df_raw["underlying"].astype(str)
    d["cp"]            = df_raw["type"].map({"call": "C", "put": "P"})
    d["strike"]        = pd.to_numeric(df_raw["strike"], errors="coerce")
    d["expiry"]        = pd.to_datetime(df_raw["expiration"], errors="coerce").dt.date
    d["bid"]           = pd.to_numeric(df_raw["bid"], errors="coerce")
    d["ask"]           = pd.to_numeric(df_raw["ask"], errors="coerce")
    # last = mid; set to None when bid or ask is missing
    mid = (d["bid"].fillna(0) + d["ask"].fillna(0)) / 2
    d["last"]          = mid.where(d["bid"].notna() & d["ask"].notna(), other=None)
    d["bid_iv"]        = pd.to_numeric(df_raw["implied_volatility"], errors="coerce")
    d["ask_iv"]        = d["bid_iv"]
    d["open_interest"] = pd.to_numeric(df_raw["open_interest"], errors="coerce").astype("Int64")
    d["volume"]        = pd.to_numeric(df_raw["volume"], errors="coerce").astype("Int64")
    d["delta"]         = pd.to_numeric(df_raw["delta"], errors="coerce")
    d["gamma"]         = pd.to_numeric(df_raw["gamma"], errors="coerce")
    d["theta"]         = pd.to_numeric(df_raw["theta"], errors="coerce")
    d["vega"]          = pd.to_numeric(df_raw["vega"], errors="coerce")
    d["rho"]           = 0.0
    d["resolution"]    = "daily"
    # Drop rows where cp or key fields couldn't be mapped
    d = d.dropna(subset=["cp", "strike", "expiry", "trade_date"])
    # Deduplicate: historicaldata.net includes per-exchange quotes for the same contract.
    # Keep the row with the highest open_interest (most representative quote).
    d = (d.sort_values("open_interest", ascending=False, na_position="last")
          .drop_duplicates(subset=["ticker", "trade_date", "cp", "strike", "expiry"], keep="first"))
    return d[V3_COLS]


def _dates_already_in_v3(dates: list) -> set:
    """Return the subset of dates that already have rows in v3 (one Athena query)."""
    if not dates:
        return set()
    date_list = ", ".join(f"DATE '{d}'" for d in dates)
    sql = f'SELECT DISTINCT trade_date FROM "{DB}"."{TABLE}" WHERE trade_date IN ({date_list})'
    df = wr.athena.read_sql_query(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        data_source=CATALOG,
        s3_output=S3_OUTPUT,
        ctas_approach=False,
    )
    return set(pd.to_datetime(df["trade_date"]).dt.date)


def athena_insert(tmp_table: str) -> None:
    """INSERT rows from a Glue temp table into options_daily_v3."""
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


def process_day(trade_date: date, df_raw: pd.DataFrame, dry_run: bool) -> dict:
    t0 = time.perf_counter()
    df = transform(df_raw)
    n_rows = len(df)

    if dry_run or n_rows == 0:
        return {"rows": n_rows, "elapsed": time.perf_counter() - t0, "status": "dry_run" if dry_run else "empty"}

    tmp_table = f"tmp_hd_{uuid.uuid4().hex}"
    tmp_path  = TMP_S3_PREFIX.rstrip("/") + f"/{tmp_table}/"

    _ensure_glue_db(DB)
    wr.s3.to_parquet(
        df=df,
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

    return {"rows": n_rows, "elapsed": time.perf_counter() - t0, "status": "ok"}


def main():
    parser = argparse.ArgumentParser(description="Import historicaldata.net zips into options_daily_v3")
    parser.add_argument("--dry-run",   action="store_true", help="Transform only, skip Athena writes")
    parser.add_argument("--from-date", default=None,        help="Skip dates before YYYY-MM-DD (for resuming)")
    args = parser.parse_args()

    from_date = date.fromisoformat(args.from_date) if args.from_date else None

    t_total        = time.perf_counter()
    days_processed = 0
    rows_inserted  = 0
    errors         = []

    for zip_name in ZIPS:
        zip_path = os.path.join(DOWNLOADS, zip_name)
        if not os.path.exists(zip_path):
            print(f"[SKIP] {zip_name} not found")
            continue

        print(f"\n{'='*50}")
        print(f"  {zip_name}")
        print(f"{'='*50}")

        with zipfile.ZipFile(zip_path) as zf:
            day_files = sorted(n for n in zf.namelist() if n.endswith("options.csv"))

            # Batch idempotency check: one Athena query per ZIP file
            candidate_dates = [
                date.fromisoformat(f[:10]) for f in day_files
                if date.fromisoformat(f[:10]) > CUTOFF
                and (from_date is None or date.fromisoformat(f[:10]) >= from_date)
            ]
            already_loaded = _dates_already_in_v3(candidate_dates) if candidate_dates else set()

            for fname in day_files:
                trade_date = date.fromisoformat(fname[:10])

                if trade_date <= CUTOFF:
                    print(f"  {trade_date} — skipped (before cutoff)")
                    continue
                if from_date and trade_date < from_date:
                    print(f"  {trade_date} — skipped (before --from-date)")
                    continue
                if trade_date in already_loaded:
                    print(f"  {trade_date} — skipped (already in v3)")
                    continue

                print(f"  {trade_date} ...", end=" ", flush=True)
                try:
                    with zf.open(fname) as f:
                        df_raw = pd.read_csv(f, dtype=str, low_memory=False)

                    result = process_day(trade_date, df_raw, args.dry_run)
                    days_processed += 1
                    rows_inserted  += result["rows"]

                    elapsed_total = time.perf_counter() - t_total
                    eta_per_day   = elapsed_total / days_processed if days_processed else 0
                    print(f"{result['rows']:,} rows  [{result['elapsed']:.1f}s, running {elapsed_total/60:.1f}m]")

                except Exception as e:
                    print(f"ERROR: {e}")
                    errors.append((trade_date, str(e)))

    elapsed_total = time.perf_counter() - t_total
    print(f"\n{'='*50}")
    print(f"  Done")
    print(f"{'='*50}")
    print(f"  Days processed : {days_processed}")
    print(f"  Rows inserted  : {rows_inserted:,}")
    print(f"  Errors         : {len(errors)}")
    print(f"  Total time     : {elapsed_total/60:.1f}m")
    if errors:
        print("\nFailed dates:")
        for d, e in errors:
            print(f"  {d}: {e}")


if __name__ == "__main__":
    main()
