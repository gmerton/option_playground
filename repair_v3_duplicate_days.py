#!/usr/bin/env python3
"""
Remove exact duplicate rows from the 8 double-loaded sessions in silver.options_daily_v3.

WHAT HAPPENED (measured 2026-09-23). `import_historicaldata.py` was INSERT-only, so re-running it over an
already-loaded date appended a whole duplicate set instead of replacing it. A day-level scan of all 4,220
sessions 2010-2026 found exactly NINE affected days, 12.86M excess rows of 4.14B (0.31%):

    2014-01-02                                                   ratio 2.05
    2024-04-11 / 04-12 / 04-17 / 04-18 / 04-19                   ratio 2.03 - 2.20
    2024-08-12, 2024-12-06                                       ratio 1.97 / 2.06
    2025-07-03                                                   ratio 1.64   <- EXCLUDED, see below

The importer was made idempotent the same day (it now calls `athena_delete_day()` before every insert),
so this is a one-off cleanup of damage already done, not a recurring chore.

⛔ 2025-07-03 IS DELIBERATELY NOT IN THE DEFAULT LIST. It is a PARTIAL overlap (1.64x, not ~2x) and 53%
of its duplicate groups have DIFFERING bid/ask/last -- two different observations of the same contract-day,
consistent with a re-pull against changed vendor data. Deduping it means CHOOSING a price, and we do not
know which source is authoritative. A visible duplicate is better than an invisible wrong price. It needs
a decision first; the guard below would refuse it anyway.

THE SAFETY PROPERTY. The repair keeps `df.drop_duplicates()` over EVERY column and nothing else. That is
lossless by construction: it deletes only byte-identical copies, and where a contract holds two genuinely
different variants it KEEPS BOTH. It can never choose between two prices, because it never compares rows
on a key. The post-write verification asserts the day's row count equals the pre-computed distinct count.

⚠ An earlier version of this script ABORTED whenever any contract held conflicting variants. That was
wrong and would have blocked all 8 days over records it was never going to modify: 2014-01-02 carries 2
such contracts (both AVP 2014-01-18 $5, one variant an obvious placeholder) out of 627,166. Conflicting
variants are a PRE-EXISTING SOURCE defect -- loading one file twice reproduces identical rows and cannot
manufacture a disagreement -- so they are orthogonal to the double-load bug. They are reported, not acted
on. NEVER dedupe on (ticker, expiry, strike, cp); that is the operation that would silently pick a price.

⚠ DELETE and INSERT are not atomic here. The deduped day is written to a local parquet BEFORE the delete,
so a failure between the two is recoverable from disk rather than from the vendor.

Usage:
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 repair_v3_duplicate_days.py            # dry run, all 8
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 repair_v3_duplicate_days.py --date 2014-01-02 --apply
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import time
import uuid
from datetime import date

import awswrangler as wr
import pandas as pd

sys.path.insert(0, "src")

from lib.athena_lib import athena, _ensure_glue_db
from lib.constants import CATALOG, DB, GLUE_CATALOG, S3_OUTPUT, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX, WORKGROUP

CLEAN_DAYS = ["2014-01-02", "2024-04-11", "2024-04-12", "2024-04-17",
              "2024-04-18", "2024-04-19", "2024-08-12", "2024-12-06"]
CONFLICTED = {"2025-07-03"}          # never repaired by this script; needs a source decision

KEY = ["ticker", "expiry", "strike", "cp"]
COLS = ["trade_date", "strike", "expiry", "cp", "last", "bid", "ask", "bid_iv", "ask_iv",
        "open_interest", "volume", "delta", "gamma", "vega", "theta", "rho", "resolution", "ticker"]
GLUE_DTYPE = {
    "trade_date": "date", "expiry": "date", "ticker": "string", "cp": "string", "resolution": "string",
    "strike": "double", "last": "double", "bid": "double", "ask": "double", "bid_iv": "double",
    "ask_iv": "double", "open_interest": "bigint", "volume": "bigint", "delta": "double",
    "gamma": "double", "vega": "double", "theta": "double", "rho": "double",
}
BACKUP = pathlib.Path("data/backups/v3_repair")
FQ = f'"{S3TABLES_CATALOG}"."{DB}"."{TABLE}"'


def read_day(d: str) -> pd.DataFrame:
    return athena(f"SELECT {', '.join(COLS)} FROM {FQ} WHERE trade_date = DATE '{d}'")


def count_day(d: str) -> int:
    return int(athena(f"SELECT count(*) n FROM {FQ} WHERE trade_date = DATE '{d}'").n.iloc[0])


def run_ddl(sql: str) -> None:
    qid = wr.athena.start_query_execution(sql=sql, database=DB, workgroup=WORKGROUP,
                                          data_source=CATALOG, s3_output=S3_OUTPUT)
    wr.athena.wait_query(query_execution_id=qid)


def repair(d: str, apply: bool) -> dict:
    print(f"\n{'='*92}\n{d}\n{'='*92}")
    if d in CONFLICTED:
        print("  ⛔ REFUSED — this day has conflicting prices, not exact duplicates. Needs a source decision.")
        return dict(day=d, status="refused")

    t0 = time.time()
    df = read_day(d)
    n_total = len(df)
    n_all = len(df.drop_duplicates())
    n_key = len(df.drop_duplicates(subset=KEY))
    print(f"  rows {n_total:>10,}   distinct(all cols) {n_all:>10,}   distinct(contract) {n_key:>10,}   "
          f"[{time.time()-t0:.0f}s]")

    # ⚠ CONFLICTS DO NOT BLOCK THE REPAIR — an earlier version aborted on them, which was wrong.
    # Removing EXACT duplicates is lossless by construction: drop_duplicates() over every column deletes
    # only byte-identical copies and KEEPS BOTH variants of a conflicted contract. It never chooses a
    # price. Conflicts are a pre-existing SOURCE defect (loading one file twice cannot manufacture a
    # disagreement), so they are reported and left exactly as they are.
    # Measured on 2014-01-02: 2 conflicts, both AVP 2014-01-18 $5 — one variant is an obvious placeholder
    # (a $5 call marked 0.00 with AVP near $17). Worth fixing one day; not this script's job.
    if n_all != n_key:
        print(f"  ⓘ note: {n_all - n_key:,} contract(s) hold conflicting variants (pre-existing source "
              f"defect). BOTH variants are preserved — only byte-identical copies are removed.")
    if n_total == n_all:
        print("  ✓ already clean — nothing to remove.")
        return dict(day=d, status="clean")

    print(f"  → every duplicate group is byte-identical; {n_total - n_all:,} excess rows "
          f"({100*(n_total-n_all)/n_total:.2f}%) are safe to remove")
    if not apply:
        print("  (dry run — pass --apply to write)")
        return dict(day=d, status="dry_run", excess=n_total - n_all)

    clean = df.drop_duplicates()[COLS]
    for c in ("open_interest", "volume"):
        clean[c] = pd.to_numeric(clean[c], errors="coerce").astype("Int64")

    BACKUP.mkdir(parents=True, exist_ok=True)
    bak = BACKUP / f"{d}_deduped.parquet"
    clean.to_parquet(bak, index=False)
    print(f"  backup written: {bak} ({bak.stat().st_size/1e6:.0f} MB) — recoverable if the insert fails")

    tmp = f"tmp_fix_{uuid.uuid4().hex}"
    tmp_path = TMP_S3_PREFIX.rstrip("/") + f"/{tmp}/"
    _ensure_glue_db(DB)
    wr.s3.to_parquet(df=clean, path=tmp_path, dataset=True, database=DB, table=tmp,
                     compression="snappy", mode="overwrite", dtype=GLUE_DTYPE)
    try:
        print("  deleting the day ...")
        run_ddl(f"DELETE FROM \"{DB}\".\"{TABLE}\" WHERE trade_date = DATE '{d}'")
        print("  re-inserting deduped rows ...")
        run_ddl(f'INSERT INTO "{DB}"."{TABLE}" SELECT {", ".join(COLS)} '
                f'FROM "{GLUE_CATALOG}"."{DB}"."{tmp}"')
    finally:
        wr.catalog.delete_table_if_exists(database=DB, table=tmp)
        wr.s3.delete_objects(tmp_path)

    after = count_day(d)
    ok = after == n_all
    print(f"  VERIFY: {after:,} rows after (expected {n_all:,}) — {'✓ OK' if ok else '✗ MISMATCH'}")
    if not ok:
        print(f"  ⚠ RESTORE FROM {bak} BEFORE RUNNING ANYTHING ELSE")
    return dict(day=d, status="repaired" if ok else "MISMATCH", before=n_total, after=after)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", action="append", help="repeatable; defaults to the 8 clean days")
    ap.add_argument("--apply", action="store_true", help="actually write (default is a dry run)")
    a = ap.parse_args()
    days = a.date or CLEAN_DAYS
    print(f"{'APPLY' if a.apply else 'DRY RUN'} — {len(days)} day(s)")
    out = [repair(d, a.apply) for d in days]
    print(f"\n{'='*92}\nSUMMARY")
    print(pd.DataFrame(out).to_string(index=False))


if __name__ == "__main__":
    main()
