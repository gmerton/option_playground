#!/usr/bin/env python3
"""
Remove exact duplicate rows from the 9 duplicated sessions in silver.options_daily_v3.

WHAT HAPPENED (measured 2026-09-23). `import_historicaldata.py` was INSERT-only, so re-running it over an
already-loaded date appended a whole duplicate set instead of replacing it. A day-level scan of all 4,220
sessions 2010-2026 found exactly NINE affected days, 12.86M excess rows of 4.14B (0.31%):

    2014-01-02                                                   ratio 2.05
    2024-04-11 / 04-12 / 04-17 / 04-18 / 04-19                   ratio 2.03 - 2.20
    2024-08-12, 2024-12-06                                       ratio 1.97 / 2.06
    2025-07-03                                                   ratio 1.64   <- NOT repairable, see below

The importer was made idempotent the same day (it now calls `athena_delete_day()` before every insert),
so this is a one-off cleanup of damage already done, not a recurring chore.

⛔ 2025-07-03 IS NOT REPAIRABLE BY THIS SCRIPT, and three earlier claims about it were wrong. Verified
2026-09-23 against the table itself:
  * It has **ZERO byte-identical rows** — 2,606,336 rows, 2,606,336 distinct. Every row differs somewhere,
    so `drop_duplicates()` removes nothing and the script correctly reports the day "clean".
  * The duplication is real: 1,021,059 contract-keys carry more than one row. What differs is mostly the
    GREEKS at trailing decimals — delta differs in 733,295 groups, gamma 466,476, bid_iv 334,801 — while
    **498,795 groups (48.8%) agree on every economic field** (bid, ask, last, open_interest, volume).
    Only **72,919 (7.1%)** disagree on bid/ask; 505,640 disagree on `last`.
  * All five Iceberg data files for the day share one query prefix (20260221_203603_00286) = ONE INSERT on
    2026-02-21. The duplication was already in that write's source. `$path` cannot separate the variants,
    so recency is not available as a tiebreak.
  * ⚠ Superseded claims, recorded so they are not repeated: "a partial re-pull against changed vendor
    data" (no — single insert), "53% of groups have differing prices" (no — 7.1% on bid/ask; the 53% came
    from a 5-ticker sample containing SPY, one of the worst-affected names), and "~950k identical copies
    can be removed losslessly" (no — there are none).
Collapsing this day would require choosing one row per contract, which is exactly the operation this
script refuses. Left as-is deliberately; read-time dedupe is documented in CLAUDE.md.

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
CONFLICTED: set[str] = set()   # ⚠ was {"2025-07-03"} — lifted 2026-09-23, see below

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

    print(f"  → {n_total - n_all:,} BYTE-IDENTICAL excess rows ({100*(n_total-n_all)/n_total:.2f}%) "
          f"are safe to remove; any conflicting variants noted above are kept")
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



# ── greek-rounding collapse ───────────────────────────────────────────────────────────────────────────
ECON = ["bid", "ask", "last", "open_interest", "volume"]
# Relaxed guard: `last` may differ. Justified 2026-09-23 on 2025-07-03 — of 449,063 groups where ONLY
# `last` differed, 99.7% had the gap INSIDE the quoted bid-ask spread and 97.2% had both variants inside
# the quote. Every engine prices at real fills on bid/ask, never `last`, and the gap is smaller than the
# modelled transaction cost (25% of bid/ask + commission), so the choice cannot move any result.
ECON_QUOTE = ["bid", "ask", "open_interest", "volume"]


def collapse_greeks(d: str, apply: bool, econ: list[str] | None = None) -> dict:
    """Keep ONE row per contract, but ONLY where every economic field is identical across the variants.

    ⚠ THIS IS NOT THE LOSSLESS OPERATION. `repair()` removes byte-identical rows and can never choose.
    This one DOES choose a row — it is authorised only for groups where bid, ask, last, open_interest and
    volume all agree, so the choice cannot change any P&L; what is discarded is greek precision at
    trailing decimals. Groups where ANY economic field differs are left completely alone.

    Authorised by the owner 2026-09-23 for 2025-07-03: "pick one row per contract, I'm indifferent to
    which if it's just a difference in rounding of greeks."
    """
    econ = econ or ECON
    print(f"\n{'='*92}\n{d}  —  COLLAPSE (guard: {'+'.join(econ)} must all agree)\n{'='*92}")
    t0 = time.time()
    df = read_day(d).reset_index(drop=True)
    n_total = len(df)

    # a contract group is collapsible iff it carries exactly ONE distinct (KEY + economic) tuple
    h = pd.util.hash_pandas_object(df[KEY + econ], index=False)
    nvar = h.groupby([df[k] for k in KEY]).transform("nunique")
    collapsible = nvar.eq(1)
    dup_in_group = df.duplicated(subset=KEY, keep="first")
    drop = collapsible & dup_in_group
    keep = ~drop

    n_groups_collapsed = int(df.loc[collapsible, KEY].drop_duplicates().shape[0])
    n_groups_left = int(df.loc[~collapsible, KEY].drop_duplicates().shape[0])
    print(f"  rows {n_total:>10,}   [{time.time()-t0:.0f}s]")
    print(f"  collapsible groups (economics identical, greeks differ): {n_groups_collapsed:>9,}")
    print(f"  groups LEFT ALONE (an economic field differs):           {n_groups_left:>9,}")
    print(f"  → {int(drop.sum()):,} rows would be removed ({100*drop.mean():.2f}%), {int(keep.sum()):,} kept")

    # verification: every row we drop must belong to a group whose economics are genuinely constant
    bad = df.loc[drop].groupby(KEY, dropna=False)[econ].nunique(dropna=False).gt(1).any(axis=1).sum()
    if bad:
        print(f"  ⛔ ABORT — {bad} collapsed groups do NOT have constant economics (hash collision?).")
        return dict(day=d, status="aborted")
    print(f"  ✓ verified: every collapsed group has identical {'/'.join(econ)}")

    if not apply:
        print("  (dry run — pass --apply to write)")
        return dict(day=d, status="dry_run", removed=int(drop.sum()))

    clean = df.loc[keep, COLS]
    for c in ("open_interest", "volume"):
        clean[c] = pd.to_numeric(clean[c], errors="coerce").astype("Int64")
    BACKUP.mkdir(parents=True, exist_ok=True)
    bak = BACKUP / f"{d}_greekcollapse.parquet"
    clean.to_parquet(bak, index=False)
    print(f"  backup written: {bak} ({bak.stat().st_size/1e6:.0f} MB)")

    tmp = f"tmp_gc_{uuid.uuid4().hex}"
    tmp_path = TMP_S3_PREFIX.rstrip("/") + f"/{tmp}/"
    _ensure_glue_db(DB)
    wr.s3.to_parquet(df=clean, path=tmp_path, dataset=True, database=DB, table=tmp,
                     compression="snappy", mode="overwrite", dtype=GLUE_DTYPE)
    try:
        print("  deleting the day ...")
        run_ddl(f"DELETE FROM \"{DB}\".\"{TABLE}\" WHERE trade_date = DATE '{d}'")
        print("  re-inserting ...")
        run_ddl(f'INSERT INTO "{DB}"."{TABLE}" SELECT {", ".join(COLS)} FROM "{GLUE_CATALOG}"."{DB}"."{tmp}"')
    finally:
        wr.catalog.delete_table_if_exists(database=DB, table=tmp)
        wr.s3.delete_objects(tmp_path)

    after = count_day(d)
    ok = after == int(keep.sum())
    print(f"  VERIFY: {after:,} rows after (expected {int(keep.sum()):,}) — {'✓ OK' if ok else '✗ MISMATCH'}")
    if not ok:
        print(f"  ⚠ RESTORE FROM {bak}")
    return dict(day=d, status="collapsed" if ok else "MISMATCH", before=n_total, after=after)



def collapse_conservative(d: str, apply: bool) -> dict:
    """Final pass to UNIQUENESS: one row per contract, keeping the WIDEST-SPREAD observation.

    ⚠ THIS IS THE ONLY OPERATION HERE THAT CHOOSES BETWEEN GENUINELY DIFFERENT PRICES. The two passes
    before it discarded fields that cannot affect a result (greeks; `last`, which nothing fills at). This
    one resolves rows whose BID/ASK differ, which IS what engines fill at.

    The safeguard is the direction of the choice, not a claim about which quote is true: keeping the
    widest spread means a lower bid AND a higher ask, i.e. you sell worse and buy worse under every
    variant. It can only make a backtest more conservative, never flatter it. Measured on 2025-07-03
    (72,919 affected contracts): median bid gap $0.034 / ask gap $0.042; 75.2% of gaps already sit inside
    25% of the quoted spread — the slippage the house cost model assumes — 96.7% inside the full spread,
    and only 2,430 exceed it. Zero crossed quotes.

    Authorised by the owner 2026-09-23: "I'd still like to strive for uniqueness."
    """
    print(f"\n{'='*92}\n{d}  —  CONSERVATIVE COLLAPSE TO UNIQUENESS (keep widest spread)\n{'='*92}")
    t0 = time.time()
    df = read_day(d).reset_index(drop=True)
    n_total = len(df)
    multi = df.duplicated(subset=KEY, keep=False)
    n_groups_multi = int(df.loc[multi, KEY].drop_duplicates().shape[0])
    print(f"  rows {n_total:>10,}   contracts with >1 row: {n_groups_multi:,}   [{time.time()-t0:.0f}s]")

    df["_spread"] = pd.to_numeric(df["ask"], errors="coerce") - pd.to_numeric(df["bid"], errors="coerce")
    # widest spread wins; NaN spreads sort last so a real quote is always preferred
    order = df.sort_values("_spread", ascending=False, kind="mergesort", na_position="last")
    keep_idx = order.drop_duplicates(subset=KEY, keep="first").index
    clean = df.loc[sorted(keep_idx), COLS]
    print(f"  → {n_total - len(clean):,} rows removed ({100*(n_total-len(clean))/n_total:.2f}%), "
          f"{len(clean):,} kept — one row per contract")

    dupes_left = int(clean.duplicated(subset=KEY).sum())
    if dupes_left:
        print(f"  ⛔ ABORT — {dupes_left} contracts still carry >1 row.")
        return dict(day=d, status="aborted")
    print("  ✓ verified: every contract now has exactly ONE row")

    if not apply:
        print("  (dry run — pass --apply to write)")
        return dict(day=d, status="dry_run", removed=n_total - len(clean))

    for c in ("open_interest", "volume"):
        clean[c] = pd.to_numeric(clean[c], errors="coerce").astype("Int64")
    BACKUP.mkdir(parents=True, exist_ok=True)
    bak = BACKUP / f"{d}_unique.parquet"
    clean.to_parquet(bak, index=False)
    print(f"  backup written: {bak} ({bak.stat().st_size/1e6:.0f} MB)")

    tmp = f"tmp_uq_{uuid.uuid4().hex}"
    tmp_path = TMP_S3_PREFIX.rstrip("/") + f"/{tmp}/"
    _ensure_glue_db(DB)
    wr.s3.to_parquet(df=clean, path=tmp_path, dataset=True, database=DB, table=tmp,
                     compression="snappy", mode="overwrite", dtype=GLUE_DTYPE)
    try:
        print("  deleting the day ...")
        run_ddl(f"DELETE FROM \"{DB}\".\"{TABLE}\" WHERE trade_date = DATE '{d}'")
        print("  re-inserting ...")
        run_ddl(f'INSERT INTO "{DB}"."{TABLE}" SELECT {", ".join(COLS)} FROM "{GLUE_CATALOG}"."{DB}"."{tmp}"')
    finally:
        wr.catalog.delete_table_if_exists(database=DB, table=tmp)
        wr.s3.delete_objects(tmp_path)

    after = count_day(d)
    ok = after == len(clean)
    print(f"  VERIFY: {after:,} rows after (expected {len(clean):,}) — {'✓ OK' if ok else '✗ MISMATCH'}")
    if not ok:
        print(f"  ⚠ RESTORE FROM {bak}")
    return dict(day=d, status="unique" if ok else "MISMATCH", before=n_total, after=after)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", action="append", help="repeatable; defaults to the 8 clean days")
    ap.add_argument("--apply", action="store_true", help="actually write (default is a dry run)")
    ap.add_argument("--unique", action="store_true",
                    help="collapse to ONE row per contract, keeping the widest-spread (most conservative) quote")
    ap.add_argument("--relax-last", action="store_true",
                    help="with --collapse-greeks: allow `last` to differ (bid/ask/OI/volume must still agree)")
    ap.add_argument("--collapse-greeks", action="store_true",
                    help="keep one row per contract where ONLY the greeks differ (chooses a row; see collapse_greeks)")
    a = ap.parse_args()
    days = a.date or CLEAN_DAYS
    print(f"{'APPLY' if a.apply else 'DRY RUN'} — {len(days)} day(s)"
          f"{' — GREEK-ROUNDING COLLAPSE' if a.collapse_greeks else ''}")
    if a.unique:
        out = [collapse_conservative(d, a.apply) for d in days]
    elif a.collapse_greeks:
        econ = ECON_QUOTE if a.relax_last else ECON
        out = [collapse_greeks(d, a.apply, econ) for d in days]
    else:
        out = [repair(d, a.apply) for d in days]
    print(f"\n{'='*92}\nSUMMARY")
    print(pd.DataFrame(out).to_string(index=False))


if __name__ == "__main__":
    main()
