#!/usr/bin/env python3
"""
Build silver.options_flow_daily -- a per-(ticker, trade_date) options FLOW table derived from options_daily_v3,
stored in the GLUE catalog (not S3 Tables: Athena DDL/CTAS doesn't work there) as Parquet under the dev-v3
workgroup's managed output path (the workgroup forbids CTAS external_location), partitioned by year. Built inside Athena (CTAS for the first year, then one INSERT per year) -- nothing is downloaded. (2026-09-23,
for the A1 call-buying study; kept for any future options-flow / positioning work.)

Columns (all tickers in v3, one row per ticker-day with any contract row):
  call_vol / put_vol                 contracts traded, all expiries
  call_oi / put_oi                   open interest, all expiries
  call_vol_30 / put_vol_30           volume, DTE 0-30
  call_oi_30 / put_oi_30             OI, DTE 0-30
  call_vol_otm30 / put_vol_otm30     volume, DTE 0-30 and |delta| in [0.05, 0.45] (short-dated OTM -- the retail
                                     footprint; delta is NULL on prints-only rows after ~mid-2026, so these go to 0)
  call_prem / put_prem               $ premium traded = sum(volume x price x 100), price = mid when bid>0 & ask>0
                                     else last (bid/ask ends ~Mar 2026)
  call_delta_sh / put_delta_sh       delta-weighted share volume = sum(volume x delta x 100) -- the dealer-hedge
                                     proxy (put_delta_sh is negative)
  n_contracts / n_traded             contract rows / rows with volume > 0
  year                               partition
⚠ v3 strikes/greeks are RAW (never split-adjusted); these aggregates are share counts and $ at the time, so a split
  changes contract counts per share -- normalise by the name's own trailing average, never compare raw levels
  across a split.
⚠ IDEMPOTENT by design (the v3 duplicate-days lesson): a year already present is SKIPPED unless --replace, which
  deletes that year's S3 prefix and partition first. Never re-INSERT a loaded year.

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_options_flow_daily.py --years 2010
  ... --years 2011-2026          (appends each missing year)
  ... --years 2024 --replace     (rebuild one year)
"""
from __future__ import annotations

import argparse
import time

import awswrangler as wr

from lib.constants import S3_OUTPUT, WORKGROUP

GLUE = "AwsDataCatalog"
DBN, TBL = "silver", "options_flow_daily"
SRC = '"awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"'

SELECT = """
SELECT ticker, trade_date,
  SUM(CASE WHEN cp = 'C' THEN volume END) AS call_vol,
  SUM(CASE WHEN cp = 'P' THEN volume END) AS put_vol,
  SUM(CASE WHEN cp = 'C' THEN open_interest END) AS call_oi,
  SUM(CASE WHEN cp = 'P' THEN open_interest END) AS put_oi,
  SUM(CASE WHEN cp = 'C' AND dte <= 30 THEN volume END) AS call_vol_30,
  SUM(CASE WHEN cp = 'P' AND dte <= 30 THEN volume END) AS put_vol_30,
  SUM(CASE WHEN cp = 'C' AND dte <= 30 THEN open_interest END) AS call_oi_30,
  SUM(CASE WHEN cp = 'P' AND dte <= 30 THEN open_interest END) AS put_oi_30,
  SUM(CASE WHEN cp = 'C' AND dte <= 30 AND delta BETWEEN 0.05 AND 0.45 THEN volume END) AS call_vol_otm30,
  SUM(CASE WHEN cp = 'P' AND dte <= 30 AND delta BETWEEN -0.45 AND -0.05 THEN volume END) AS put_vol_otm30,
  SUM(CASE WHEN cp = 'C' THEN volume * px * 100 END) AS call_prem,
  SUM(CASE WHEN cp = 'P' THEN volume * px * 100 END) AS put_prem,
  SUM(CASE WHEN cp = 'C' THEN volume * delta * 100 END) AS call_delta_sh,
  SUM(CASE WHEN cp = 'P' THEN volume * delta * 100 END) AS put_delta_sh,
  COUNT(*) AS n_contracts,
  SUM(CASE WHEN volume > 0 THEN 1 ELSE 0 END) AS n_traded,
  year
FROM (
  SELECT ticker, trade_date, upper(substr(cp, 1, 1)) AS cp,
         CAST(volume AS DOUBLE) AS volume, CAST(open_interest AS DOUBLE) AS open_interest,
         CAST(delta AS DOUBLE) AS delta, date_diff('day', trade_date, expiry) AS dte,
         CASE WHEN bid > 0 AND ask > 0 THEN (CAST(bid AS DOUBLE) + CAST(ask AS DOUBLE)) / 2
              ELSE CAST("last" AS DOUBLE) END AS px,
         year(trade_date) AS year
  FROM {src}
  WHERE trade_date BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
)
GROUP BY ticker, trade_date, year
"""


def run(sql: str) -> dict:
    t0 = time.time()
    qid = wr.athena.start_query_execution(sql=sql, database=DBN, workgroup=WORKGROUP, data_source=GLUE,
                                          s3_output=S3_OUTPUT, wait=True)
    st = qid["Statistics"] if isinstance(qid, dict) else {}
    return dict(secs=round(time.time() - t0), scanned_gb=round(st.get("DataScannedInBytes", 0) / 1e9, 1),
                state=qid.get("Status", {}).get("State") if isinstance(qid, dict) else None)


def table_exists() -> bool:
    return wr.catalog.does_table_exist(database=DBN, table=TBL)


def loaded_years() -> set[int]:
    if not table_exists():
        return set()
    df = wr.athena.read_sql_query(f"SELECT DISTINCT year FROM {DBN}.{TBL}", database=DBN, workgroup=WORKGROUP,
                                  data_source=GLUE, s3_output=S3_OUTPUT, ctas_approach=False)
    return set(df.year.astype(int))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", required=True, help="e.g. 2010 or 2011-2026")
    ap.add_argument("--replace", action="store_true")
    a = ap.parse_args()
    lo, _, hi = a.years.partition("-")
    years = list(range(int(lo), int(hi or lo) + 1))
    have = loaded_years()
    for y in years:
        if y in have and not a.replace:
            print(f"{y}: already loaded -- skipped (use --replace to rebuild)", flush=True)
            continue
        if y in have and a.replace:
            loc = wr.catalog.get_table_location(database=DBN, table=TBL).rstrip("/") + "/"
            wr.s3.delete_objects(f"{loc}year={y}/")
            run(f"ALTER TABLE {DBN}.{TBL} DROP IF EXISTS PARTITION (year={y})")
            print(f"{y}: cleared for rebuild", flush=True)
        body = SELECT.format(src=SRC, y=y)
        if not table_exists():
            # the dev-v3 workgroup enforces a centralised output location, so CTAS may not set external_location;
            # the table lives under the workgroup's managed path (read it back from Glue when needed)
            sql = (f"CREATE TABLE {DBN}.{TBL} WITH (format = 'PARQUET', parquet_compression = 'SNAPPY', "
                   f"partitioned_by = ARRAY['year']) AS {body}")
        else:
            sql = f"INSERT INTO {DBN}.{TBL} {body}"
        r = run(sql)
        print(f"{y}: {r}", flush=True)
    n = wr.athena.read_sql_query(f"SELECT year, COUNT(*) n, COUNT(DISTINCT ticker) tickers FROM {DBN}.{TBL} GROUP BY year ORDER BY year",
                                 database=DBN, workgroup=WORKGROUP, data_source=GLUE, s3_output=S3_OUTPUT, ctas_approach=False)
    print(n.to_string(index=False))


if __name__ == "__main__":
    main()
