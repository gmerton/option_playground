"""
Append daily stock bars to the silver.equity_daily Iceberg table (S3 Tables).

Pattern per lib.athena_lib: stage the rows as a temp Glue-catalog parquet table,
then cross-catalog INSERT INTO the S3 Tables Iceberg table with fully-qualified
names. Idempotent: the target's rows for the incoming trade_dates are DELETEd
first, so re-running a night (or overlapping backfills) never double-writes.

Created 2026-07-24. Table schema (created via `aws s3tables create-table` —
Athena DDL does NOT work on S3 Tables):
  trade_date date, ticker string, open double, high double, low double,
  close double, volume long, vwap double, dollar_volume double
Backfilled rows sourced from the wide matrix have open/volume/vwap NULL
(the matrix stores only c/h/l/dollar_volume); rows written live by the nightly
refresh carry all fields.
"""
from __future__ import annotations

import uuid

import awswrangler as wr
import pandas as pd

from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, S3_OUTPUT, TMP_S3_PREFIX, WORKGROUP

EQUITY_TABLE = "equity_daily"

_DTYPE = {
    "trade_date": "date",
    "ticker": "string",
    "open": "double",
    "high": "double",
    "low": "double",
    "close": "double",
    "volume": "bigint",
    "vwap": "double",
    "dollar_volume": "double",
}
COLS = list(_DTYPE)


def _run_dml(sql: str) -> None:
    qid = wr.athena.start_query_execution(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        data_source=S3TABLES_CATALOG,
        s3_output=S3_OUTPUT,
    )
    res = wr.athena.wait_query(query_execution_id=qid)
    state = res["Status"]["State"]
    if state != "SUCCEEDED":
        reason = res["Status"].get("StateChangeReason", "")
        raise RuntimeError(f"Athena DML {state}: {reason}\nSQL: {sql[:300]}")


def append_rows(df: pd.DataFrame, log=print) -> int:
    """Idempotently upsert long-format rows (COLS schema) into equity_daily."""
    if df is None or df.empty:
        log("equity_daily: no rows to append")
        return 0

    d = df.copy()
    d["trade_date"] = pd.to_datetime(d["trade_date"]).dt.date
    d["ticker"] = d["ticker"].astype(str)
    # Polygon reports some volumes as floats (incl. fractional-share tapes) —
    # round before the nullable-int cast or it raises "cannot safely cast".
    d["volume"] = pd.to_numeric(d["volume"], errors="coerce").round().astype("Int64")
    for c in ("open", "high", "low", "close", "vwap", "dollar_volume"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[COLS]

    stage = f"equity_daily_stage_{uuid.uuid4().hex[:12]}"
    path = TMP_S3_PREFIX.rstrip("/") + f"/{stage}/"
    wr.s3.to_parquet(df=d, path=path, dataset=True, database=DB, table=stage,
                     compression="snappy", mode="overwrite", dtype=_DTYPE)
    try:
        dates = sorted({dt.isoformat() for dt in d["trade_date"].unique()})
        date_list = ", ".join(f"DATE '{x}'" for x in dates)
        fq_target = f'"{S3TABLES_CATALOG}"."{DB}"."{EQUITY_TABLE}"'
        fq_stage = f'"{GLUE_CATALOG}"."{DB}"."{stage}"'

        log(f"equity_daily: replacing {len(dates)} trade_date(s), inserting {len(d)} rows...")
        _run_dml(f"DELETE FROM {fq_target} WHERE trade_date IN ({date_list})")
        _run_dml(f"INSERT INTO {fq_target} ({', '.join(COLS)}) "
                 f"SELECT {', '.join(COLS)} FROM {fq_stage}")
    finally:
        try:
            wr.catalog.delete_table_if_exists(database=DB, table=stage)
        except Exception:
            pass
        try:
            wr.s3.delete_objects(path)
        except Exception:
            pass
    return len(d)


def frames_to_long(frames, dates=None) -> pd.DataFrame:
    """
    Long-format rows from the wide matrix (open/volume/vwap NULL — backfill use).
    `dates`: optional iterable of date-likes to restrict to.
    """
    close, high, low, dolvol = frames
    if dates is not None:
        idx = close.index.intersection(pd.to_datetime(list(dates)))
        close, high, low, dolvol = (x.loc[idx] for x in (close, high, low, dolvol))
    parts = {"close": close.stack(), "high": high.stack(),
             "low": low.stack(), "dollar_volume": dolvol.stack()}
    out = pd.DataFrame(parts).reset_index()
    out.columns = ["trade_date", "ticker", "close", "high", "low", "dollar_volume"]
    out["open"] = None
    out["volume"] = pd.array([None] * len(out), dtype="Int64")
    out["vwap"] = None
    return out[COLS]
