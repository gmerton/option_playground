#!/usr/bin/env python3
"""
Deduplicate options_daily_v3 for Sep 2025 onwards.

For each month, keeps the best row per (ticker, trade_date, cp, strike, expiry)
ranked by highest open_interest (bid as tiebreaker), deletes all other copies.

Process per month:
  1. CTAS  — write dedup'd month to a Glue temp table (stays on S3, no Python memory)
  2. DELETE — remove that month from v3
  3. INSERT — copy dedup'd rows from Glue temp back to v3
  4. VERIFY — row counts match
  5. CLEANUP — drop Glue temp table + S3 objects

Usage:
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python dedup_v3.py
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python dedup_v3.py --dry-run
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src python dedup_v3.py --from-month 2025-11
"""

import argparse
import sys
import time
import uuid

import awswrangler as wr

from lib.constants import (
    CATALOG, DB, GLUE_CATALOG, S3_OUTPUT,
    S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX, WORKGROUP,
)

# Months to process: Sep 2025 → Feb 2026
MONTHS = [
    ("2025-09-01", "2025-10-01"),
    ("2025-10-01", "2025-11-01"),
    ("2025-11-01", "2025-12-01"),
    ("2025-12-01", "2026-01-01"),
    ("2026-01-01", "2026-02-01"),
    ("2026-02-01", "2026-03-01"),
]

V3_COLS = (
    "trade_date, strike, expiry, cp, last, bid, ask, "
    "bid_iv, ask_iv, open_interest, volume, delta, gamma, "
    "vega, theta, rho, resolution, ticker"
)


def _run_dml(sql: str) -> None:
    """Execute a DML/DDL statement (INSERT, DELETE, CTAS) and wait."""
    qid = wr.athena.start_query_execution(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        data_source=CATALOG,
        s3_output=S3_OUTPUT,
    )
    wr.athena.wait_query(query_execution_id=qid)


def _count(month_start: str, month_end: str) -> int:
    sql = f"""
    SELECT COUNT(*) AS n
    FROM "{DB}"."{TABLE}"
    WHERE trade_date >= DATE '{month_start}'
      AND trade_date <  DATE '{month_end}'
    """
    df = wr.athena.read_sql_query(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        data_source=CATALOG,
        s3_output=S3_OUTPUT,
        ctas_approach=False,
    )
    return int(df["n"].iloc[0])


def _count_dup_keys(month_start: str, month_end: str) -> int:
    sql = f"""
    SELECT COUNT(*) AS n
    FROM (
      SELECT ticker, trade_date, cp, strike, expiry
      FROM "{DB}"."{TABLE}"
      WHERE trade_date >= DATE '{month_start}'
        AND trade_date <  DATE '{month_end}'
      GROUP BY ticker, trade_date, cp, strike, expiry
      HAVING COUNT(*) > 1
    ) t
    """
    df = wr.athena.read_sql_query(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        data_source=CATALOG,
        s3_output=S3_OUTPUT,
        ctas_approach=False,
    )
    return int(df["n"].iloc[0])


def dedup_month(month_start: str, month_end: str, dry_run: bool) -> None:
    label = f"{month_start[:7]}"
    print(f"\n{'='*60}")
    print(f"  {label}  ({month_start} → {month_end})")
    print(f"{'='*60}")

    t0 = time.perf_counter()

    n_before = _count(month_start, month_end)
    print(f"  Rows in v3      : {n_before:,}")

    n_dup_keys = _count_dup_keys(month_start, month_end)
    print(f"  Duplicate keys  : {n_dup_keys:,}  (~{n_dup_keys:,} extra rows to remove)")

    if n_dup_keys == 0:
        print("  No duplicates — skipping.")
        return

    if dry_run:
        print(f"  [DRY RUN] Would remove ~{n_dup_keys:,} rows.")
        return

    tmp_table = f"tmp_dedup_{uuid.uuid4().hex}"
    tmp_path  = TMP_S3_PREFIX.rstrip("/") + f"/{tmp_table}/"

    try:
        # ── Step 1: CTAS ─────────────────────────────────────────────────────
        # No external_location: workgroup enforces centralized output bucket.
        # Athena writes parquet to its own prefix; we retrieve the location
        # from the Glue catalog after creation for cleanup.
        print(f"  Step 1/4: CTAS dedup → Glue temp table ...", end=" ", flush=True)
        t1 = time.perf_counter()
        ctas_sql = f"""
        CREATE TABLE "{GLUE_CATALOG}"."{DB}"."{tmp_table}"
        WITH (
          format = 'PARQUET',
          write_compression = 'SNAPPY'
        )
        AS
        SELECT {V3_COLS}
        FROM (
          SELECT *,
            ROW_NUMBER() OVER (
              PARTITION BY ticker, trade_date, cp, strike, expiry
              ORDER BY open_interest DESC NULLS LAST, bid DESC
            ) AS rn
          FROM "{DB}"."{TABLE}"
          WHERE trade_date >= DATE '{month_start}'
            AND trade_date <  DATE '{month_end}'
        ) t
        WHERE rn = 1
        """
        _run_dml(ctas_sql)
        print(f"done ({time.perf_counter()-t1:.0f}s)")

        # Retrieve actual S3 location Athena chose, so we can clean it up later
        tmp_path = wr.catalog.get_table_location(database=DB, table=tmp_table)

        # Count what was written
        n_dedup = int(wr.athena.read_sql_query(
            sql=f'SELECT COUNT(*) AS n FROM "{GLUE_CATALOG}"."{DB}"."{tmp_table}"',
            database=DB,
            workgroup=WORKGROUP,
            s3_output=S3_OUTPUT,
            ctas_approach=False,
        )["n"].iloc[0])
        print(f"  Dedup rows      : {n_dedup:,}  (removing {n_before - n_dedup:,} duplicates)")

        if n_dedup == 0:
            raise RuntimeError("CTAS produced 0 rows — aborting before delete.")

        # ── Step 2: DELETE month from v3 ─────────────────────────────────────
        print(f"  Step 2/4: Deleting {label} from v3 ...", end=" ", flush=True)
        t2 = time.perf_counter()
        _run_dml(f"""
        DELETE FROM "{DB}"."{TABLE}"
        WHERE trade_date >= DATE '{month_start}'
          AND trade_date <  DATE '{month_end}'
        """)
        print(f"done ({time.perf_counter()-t2:.0f}s)")

        # ── Step 3: INSERT dedup rows back ────────────────────────────────────
        print(f"  Step 3/4: Inserting {n_dedup:,} dedup rows back to v3 ...", end=" ", flush=True)
        t3 = time.perf_counter()
        _run_dml(f"""
        INSERT INTO "{DB}"."{TABLE}"
        SELECT {V3_COLS}
        FROM "{GLUE_CATALOG}"."{DB}"."{tmp_table}"
        """)
        print(f"done ({time.perf_counter()-t3:.0f}s)")

        # ── Step 4: Verify ────────────────────────────────────────────────────
        print(f"  Step 4/4: Verifying ...", end=" ", flush=True)
        n_after = _count(month_start, month_end)
        if n_after == n_dedup:
            print(f"✓  {n_after:,} rows  (removed {n_before - n_after:,} duplicates)")
        else:
            print(f"\n  ✗ MISMATCH: expected {n_dedup:,}, got {n_after:,}")
            sys.exit(1)

    finally:
        # ── Step 5: Cleanup ───────────────────────────────────────────────────
        wr.catalog.delete_table_if_exists(database=DB, table=tmp_table)
        wr.s3.delete_objects(tmp_path)

    elapsed = time.perf_counter() - t0
    print(f"  Month complete in {elapsed:.0f}s")


def main():
    parser = argparse.ArgumentParser(description="Deduplicate options_daily_v3 Sep 2025+")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report duplicate counts only; no writes")
    parser.add_argument("--from-month", default=None, metavar="YYYY-MM",
                        help="Resume from this month, e.g. 2025-11")
    args = parser.parse_args()

    skip_before = args.from_month  # e.g. "2025-11"

    t_total = time.perf_counter()
    for month_start, month_end in MONTHS:
        if skip_before and month_start[:7] < skip_before:
            print(f"  Skipping {month_start[:7]} (before --from-month {skip_before})")
            continue
        dedup_month(month_start, month_end, dry_run=args.dry_run)

    elapsed = time.perf_counter() - t_total
    print(f"\n{'='*60}")
    print(f"  All months complete in {elapsed/60:.1f}m")
    if args.dry_run:
        print("  [DRY RUN — no writes performed]")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
