#!/usr/bin/env python3
"""
Build silver.options_iv_daily -- per-(ticker, trade_date) implied-volatility SHAPE from options_daily_v3, for the
option-implied short-signal test (run_iv_skew_short.py, 2026-09-25). Glue catalog, Parquet, partitioned by year,
built inside Athena exactly like run_build_options_flow_daily.py (CTAS first year, one INSERT per year, idempotent).

Contract filter: DTE 10-60, bid > 0 and ask > 0, bid_iv > 0 and ask_iv > 0; iv = (bid_iv + ask_iv) / 2.
Delta-based selection, so no spot price is needed (v3 strikes are RAW; delta is scale-free).
Columns:
  skew         Xing-Zhang-Zhao (2010) smirk: IV of the put nearest -0.25 delta minus IV of the call nearest
               0.50 delta, both from the ONE expiry nearest 30 DTE that has both (put delta in [-0.40, -0.10],
               call delta in [0.35, 0.65])
  put25_iv / call50_iv / skew_dte    its components and the expiry used
  cw           Cremers-Weinbaum (2010) spread: OI-weighted mean of (call IV - put IV) over every same-strike,
               same-expiry pair with both legs quoted and OI > 0, call delta in [0.10, 0.90]. LOW (negative) =
               puts rich relative to parity.
  cw_pairs     number of pairs behind cw
⚠ Coverage: bid/ask ends ~Mar 2026 and stored IV ~mid-May 2026 -> build 2010-2026, use through 2026-03.

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_options_iv_daily.py --years 2010-2026
"""
from __future__ import annotations

import argparse
import time

import awswrangler as wr

from lib.constants import S3_OUTPUT, WORKGROUP

GLUE = "AwsDataCatalog"
DBN, TBL = "silver", "options_iv_daily"
SRC = '"awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"'

SELECT = """
WITH b AS (
  SELECT ticker, trade_date, expiry, strike, upper(substr(cp, 1, 1)) AS cp,
         date_diff('day', trade_date, expiry) AS dte,
         (CAST(bid_iv AS DOUBLE) + CAST(ask_iv AS DOUBLE)) / 2 AS iv,
         CAST(delta AS DOUBLE) AS delta, CAST(open_interest AS DOUBLE) AS oi
  FROM {src}
  WHERE trade_date BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
    AND bid > 0 AND ask > 0 AND bid_iv > 0 AND ask_iv > 0
    AND date_diff('day', trade_date, expiry) BETWEEN 10 AND 60
),
ex AS (
  SELECT ticker, trade_date, expiry, max(dte) AS dte,
         min_by(CASE WHEN cp = 'P' AND delta BETWEEN -0.40 AND -0.10 THEN iv END,
                CASE WHEN cp = 'P' AND delta BETWEEN -0.40 AND -0.10 THEN abs(delta + 0.25) END) AS put25_iv,
         min_by(CASE WHEN cp = 'C' AND delta BETWEEN 0.35 AND 0.65 THEN iv END,
                CASE WHEN cp = 'C' AND delta BETWEEN 0.35 AND 0.65 THEN abs(delta - 0.50) END) AS call50_iv
  FROM b GROUP BY ticker, trade_date, expiry
),
sk AS (
  SELECT ticker, trade_date,
         min_by(put25_iv - call50_iv, abs(dte - 30)) AS skew,
         min_by(put25_iv, abs(dte - 30)) AS put25_iv,
         min_by(call50_iv, abs(dte - 30)) AS call50_iv,
         min_by(dte, abs(dte - 30)) AS skew_dte
  FROM ex WHERE put25_iv IS NOT NULL AND call50_iv IS NOT NULL
  GROUP BY ticker, trade_date
),
cw AS (
  SELECT c.ticker, c.trade_date,
         sum((c.oi + p.oi) / 2 * (c.iv - p.iv)) / sum((c.oi + p.oi) / 2) AS cw,
         count(*) AS cw_pairs
  FROM b c JOIN b p
    ON c.ticker = p.ticker AND c.trade_date = p.trade_date AND c.expiry = p.expiry AND c.strike = p.strike
   AND c.cp = 'C' AND p.cp = 'P'
  WHERE c.oi > 0 AND p.oi > 0 AND c.delta BETWEEN 0.10 AND 0.90
  GROUP BY c.ticker, c.trade_date
)
SELECT coalesce(sk.ticker, cw.ticker) AS ticker, coalesce(sk.trade_date, cw.trade_date) AS trade_date,
       sk.skew, sk.put25_iv, sk.call50_iv, sk.skew_dte, cw.cw, cw.cw_pairs, {y} AS year
FROM sk FULL OUTER JOIN cw ON sk.ticker = cw.ticker AND sk.trade_date = cw.trade_date
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
