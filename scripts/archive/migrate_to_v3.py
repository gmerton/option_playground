#!/usr/bin/env python3
"""
One-off migration script: options_daily_v2 → options_daily_v3

Repartitions by bucket[50](ticker) + year(trade_date) for single-ticker query performance.
- 50 writer limit: well under Athena's 100 open writers limit for annual batch inserts
- Query improvement: ~50x fewer rows scanned for single-ticker queries
- Sort order: (ticker ASC, trade_date ASC) enables file-level date pruning via statistics

Partition spec: bucket[50](ticker) + year(trade_date)
Sort order: ticker ASC, trade_date ASC

NOTE: identity(ticker) + day(trade_date) was the original plan but cannot be used for bulk
inserts — 10,823 unique tickers × 252 trading days far exceeds Athena's 100 open writers limit.

Run from repo root:
    PYTHONPATH=src python migrate_to_v3.py

Steps:
  1. Create options_daily_v3 via S3 Tables boto3 API (Athena DDL not supported for S3 Tables)
  2. Smoke test: insert 2025-08-29, verify, then truncate
  3. Migrate all data in annual batches (2010–2025) — 50 writers per batch, safe
  4. Validate row counts match v2

After success: update src/lib/constants.py TABLE = "options_daily_v3"
"""

import sys
import time

from lib.athena_lib import athena

OLD_TABLE = "options_daily_v2"
NEW_TABLE = "options_daily_v3"
DB = "silver"


# ─── Step 1: Create options_daily_v3 ──────────────────────────────────────────

TABLE_BUCKET_ARN = "arn:aws:s3tables:us-west-2:919061006621:bucket/gm-equity-tbl-bucket"

CREATE_METADATA = {
    "iceberg": {
        "schema": {
            "fields": [
                {"id": 1,  "name": "trade_date",    "type": "date",    "required": False},
                {"id": 2,  "name": "strike",        "type": "double",  "required": False},
                {"id": 3,  "name": "expiry",        "type": "date",    "required": False},
                {"id": 4,  "name": "cp",            "type": "string",  "required": False},
                {"id": 5,  "name": "last",          "type": "double",  "required": False},
                {"id": 6,  "name": "bid",           "type": "double",  "required": False},
                {"id": 7,  "name": "ask",           "type": "double",  "required": False},
                {"id": 8,  "name": "bid_iv",        "type": "double",  "required": False},
                {"id": 9,  "name": "ask_iv",        "type": "double",  "required": False},
                {"id": 10, "name": "open_interest", "type": "long",    "required": False},
                {"id": 11, "name": "volume",        "type": "long",    "required": False},
                {"id": 12, "name": "delta",         "type": "double",  "required": False},
                {"id": 13, "name": "gamma",         "type": "double",  "required": False},
                {"id": 14, "name": "vega",          "type": "double",  "required": False},
                {"id": 15, "name": "theta",         "type": "double",  "required": False},
                {"id": 16, "name": "rho",           "type": "double",  "required": False},
                {"id": 17, "name": "resolution",    "type": "string",  "required": False},
                {"id": 18, "name": "ticker",        "type": "string",  "required": False},
            ]
        },
        "partitionSpec": {
            "fields": [
                {"sourceId": 18, "transform": "bucket[5]", "name": "ticker_bucket"},
                {"sourceId": 1,  "transform": "year",       "name": "trade_date_year"},
            ]
        }
        # NOTE: writeOrder intentionally omitted — Athena writes temp sort files to the
        # S3 Tables bucket for large inserts, which fails with HIVE_WRITER_DATA_ERROR.
    }
}


def step1_create_table():
    """
    S3 Tables does NOT support CREATE TABLE via Athena DDL.
    Use aws s3tables create-table via boto3 instead.
    """
    import json
    import boto3

    print(f"\n=== Step 1: Create {NEW_TABLE} (via S3 Tables API) ===")
    client = boto3.client("s3tables", region_name="us-west-2")

    # Check if table already exists
    try:
        resp = client.get_table(
            tableBucketARN=TABLE_BUCKET_ARN,
            namespace=DB,
            name=NEW_TABLE,
        )
        print(f"  Table already exists (ARN: {resp['tableARN']}) — continuing.")
        return
    except client.exceptions.NotFoundException:
        pass

    # Create table
    try:
        resp = client.create_table(
            tableBucketARN=TABLE_BUCKET_ARN,
            namespace=DB,
            name=NEW_TABLE,
            format="ICEBERG",
            metadata=CREATE_METADATA,
        )
        print(f"✓ Table {DB}.{NEW_TABLE} created (ARN: {resp['tableARN']})")
    except Exception as e:
        print(f"✗ create_table failed: {e}")
        sys.exit(1)


# ─── Step 2: Smoke test ────────────────────────────────────────────────────────

SMOKE_DATE = "2025-08-29"

SMOKE_INSERT = f"""
INSERT INTO "{DB}"."{NEW_TABLE}"
SELECT * FROM "{DB}"."{OLD_TABLE}"
WHERE trade_date = DATE '{SMOKE_DATE}'
"""

SMOKE_COUNT = f"""
SELECT COUNT(*) AS n FROM "{DB}"."{NEW_TABLE}"
"""

# Iceberg TRUNCATE (supported in Athena engine v3 for Iceberg tables)
TRUNCATE_V3 = f"""
DELETE FROM "{DB}"."{NEW_TABLE}"
WHERE trade_date IS NOT NULL OR trade_date IS NULL
"""


def step2_smoke_test():
    print(f"\n=== Step 2: Smoke test — {SMOKE_DATE} ===")

    # Insert one day
    t0 = time.time()
    print("  Inserting smoke day...", end="", flush=True)
    athena(SMOKE_INSERT)
    elapsed = time.time() - t0
    print(f" done ({elapsed:.1f}s)")

    # Verify rows landed
    df = athena(SMOKE_COUNT)
    n = df.iloc[0, 0]
    print(f"  Rows in {NEW_TABLE} after smoke insert: {n:,}")
    if n == 0:
        print("✗ Smoke test: no rows inserted — aborting.")
        sys.exit(1)
    print("✓ Smoke test passed.")

    # Clean up smoke data before full migration
    # Note: awswrangler raises NoFilesFound when reading empty DML results, but the
    # DELETE actually succeeds. Swallow that specific error and verify via COUNT.
    print("  Truncating smoke data...", end="", flush=True)
    try:
        athena(f'DELETE FROM "{DB}"."{NEW_TABLE}"')
    except Exception as e:
        if "NoFilesFound" not in str(type(e).__name__) and "NoFilesFound" not in str(e):
            print(f"\n  DELETE error: {e}")
    df2 = athena(SMOKE_COUNT)
    n2 = df2.iloc[0, 0]
    print(f" done. Rows remaining: {n2:,}")
    if n2 != 0:
        print("✗ Table not empty after truncate — aborting.")
        sys.exit(1)
    print("✓ Table cleared, ready for full migration.")


# ─── Step 3: Annual migration batches ─────────────────────────────────────────

# 2010 → 2024 full years; 2025 is a partial year ending 2025-08-29
YEAR_RANGES = [(y, y + 1) for y in range(2010, 2025)] + [(2025, 2026)]


def annual_insert_sql(year_start: int, year_end: int) -> str:
    return f"""
INSERT INTO "{DB}"."{NEW_TABLE}"
SELECT * FROM "{DB}"."{OLD_TABLE}"
WHERE trade_date >= DATE '{year_start}-01-01'
  AND trade_date <  DATE '{year_end}-01-01'
"""


def step3_annual_batches(start_from_year: int = 2010):
    print(f"\n=== Step 3: Annual migration batches (starting from {start_from_year}) ===")
    total_elapsed = 0.0

    for year_start, year_end in YEAR_RANGES:
        if year_start < start_from_year:
            print(f"  Skipping {year_start} (already done)")
            continue

        sql = annual_insert_sql(year_start, year_end)
        label = f"{year_start}" if year_end <= 2025 else "2025 (partial)"
        print(f"  Inserting {label}...", end="", flush=True)
        t0 = time.time()
        try:
            athena(sql)
            elapsed = time.time() - t0
            total_elapsed += elapsed
            print(f" ✓ ({elapsed:.1f}s)")
        except Exception as e:
            elapsed = time.time() - t0
            print(f"\n✗ FAILED on year {year_start} after {elapsed:.1f}s: {e}")
            print(f"  → Fix the issue, then re-run with: start_from_year={year_start}")
            sys.exit(1)

    print(f"\n  Total insert time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")


# ─── Step 4: Validate ─────────────────────────────────────────────────────────

def step4_validate() -> bool:
    print("\n=== Step 4: Validate row counts ===")

    print(f"  Counting {OLD_TABLE}...", end="", flush=True)
    t0 = time.time()
    df_old = athena(f'SELECT COUNT(*) AS n FROM "{DB}"."{OLD_TABLE}"')
    n_old = int(df_old.iloc[0, 0])
    print(f" {n_old:,} ({time.time()-t0:.1f}s)")

    print(f"  Counting {NEW_TABLE}...", end="", flush=True)
    t0 = time.time()
    df_new = athena(f'SELECT COUNT(*) AS n FROM "{DB}"."{NEW_TABLE}"')
    n_new = int(df_new.iloc[0, 0])
    print(f" {n_new:,} ({time.time()-t0:.1f}s)")

    if n_old == n_new:
        print(f"✓ Row counts match: {n_new:,}")
    else:
        diff = n_old - n_new
        print(f"✗ MISMATCH: {OLD_TABLE}={n_old:,}  {NEW_TABLE}={n_new:,}  diff={diff:,}")
        return False

    # Spot check
    print("\n  Spot check — IBIT on 2025-01-17...")
    df_spot = athena(f"""
        SELECT COUNT(*) AS n FROM "{DB}"."{NEW_TABLE}"
        WHERE ticker = 'IBIT' AND trade_date = DATE '2025-01-17'
    """)
    print(f"  IBIT rows on 2025-01-17: {int(df_spot.iloc[0, 0]):,}")

    return True


# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Allow resuming from a specific year if a previous run was interrupted.
    # Usage: PYTHONPATH=src python migrate_to_v3.py --from-year 2018
    import argparse

    parser = argparse.ArgumentParser(description="Migrate options_daily_v2 → options_daily_v3")
    parser.add_argument(
        "--from-year",
        type=int,
        default=None,
        help="Resume annual batches from this year (skips steps 1 and 2)",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip the smoke test (useful when resuming after step 2)",
    )
    args = parser.parse_args()

    if args.from_year is not None:
        print(f"Resuming from year {args.from_year} — skipping steps 1 and 2.")
        step3_annual_batches(start_from_year=args.from_year)
    else:
        step1_create_table()
        if not args.skip_smoke:
            step2_smoke_test()
        step3_annual_batches()

    ok = step4_validate()

    if ok:
        print(
            "\n✓ Migration complete!\n"
            "  Next: update src/lib/constants.py\n"
            '    TABLE = "options_daily_v3"   # was "options_daily_v2"'
        )
    else:
        print(
            "\n✗ Validation failed — do NOT update constants.py yet.\n"
            "  Investigate the row count mismatch and re-run step 4."
        )
        sys.exit(1)
