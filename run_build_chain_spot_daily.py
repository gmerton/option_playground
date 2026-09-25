#!/usr/bin/env python3
"""
Build silver.chain_spot_daily -- a RAW daily underlying price for EVERY optionable ticker (incl. delisted), recovered
from options_daily_v3 by put-call parity (2026-09-25; the survivorship check for the pullback-dip finding needs prices
for names our survivor panels do not hold).

Per (ticker, trade_date): expiry nearest 30 DTE within 7-60 DTE having >= 1 strike quoted on BOTH sides (bid > 0,
ask > 0); per strike parity spot = K + Cmid - Pmid (r = q = 0; the residual is carry + dividends, small at ~30 DTE);
spot = median over the 3 strikes with the smallest |Cmid - Pmid| (nearest the money). Also opt_vol = total contract
volume that day (all expiries), a liquidity proxy (no stock volume in v3).
⚠ RAW prices (never split-adjusted): adjust with data/cache/pit/splits.parquet before computing returns.
⚠ Bid/ask ends ~2026-03 -> use through 2026-02.  Idempotent per year, like the other builders.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_chain_spot_daily.py --years 2010-2026
"""
from __future__ import annotations

import argparse
import time

import awswrangler as wr

from lib.constants import S3_OUTPUT, WORKGROUP

GLUE = "AwsDataCatalog"
DBN, TBL = "silver", "chain_spot_daily"
SRC = '"awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"'

SELECT = """
WITH b AS (
  SELECT ticker, trade_date, expiry, strike, upper(substr(cp, 1, 1)) AS cp,
         date_diff('day', trade_date, expiry) AS dte,
         (CAST(bid AS DOUBLE) + CAST(ask AS DOUBLE)) / 2 AS mid, CAST(volume AS DOUBLE) AS volume,
         bid, ask
  FROM {src}
  WHERE trade_date BETWEEN DATE '{y}-01-01' AND DATE '{y}-12-31'
),
vol AS (SELECT ticker, trade_date, sum(volume) AS opt_vol FROM b GROUP BY ticker, trade_date),
q AS (SELECT * FROM b WHERE bid > 0 AND ask > 0 AND dte BETWEEN 7 AND 60),
pairs AS (
  SELECT c.ticker, c.trade_date, c.expiry, c.dte, CAST(c.strike AS DOUBLE) AS k, c.mid AS cm, p.mid AS pm
  FROM q c JOIN q p ON c.ticker = p.ticker AND c.trade_date = p.trade_date AND c.expiry = p.expiry
                   AND c.strike = p.strike AND c.cp = 'C' AND p.cp = 'P'
),
ex AS (
  SELECT ticker, trade_date, min_by(expiry, abs(dte - 30)) AS expiry FROM pairs GROUP BY ticker, trade_date
),
r AS (
  SELECT pr.ticker, pr.trade_date, pr.k + pr.cm - pr.pm AS s,
         row_number() OVER (PARTITION BY pr.ticker, pr.trade_date ORDER BY abs(pr.cm - pr.pm)) AS rn
  FROM pairs pr JOIN ex ON pr.ticker = ex.ticker AND pr.trade_date = ex.trade_date AND pr.expiry = ex.expiry
)
SELECT r.ticker, r.trade_date, approx_percentile(r.s, 0.5) AS spot, count(*) AS n_strikes,
       max(vol.opt_vol) AS opt_vol, {y} AS year
FROM r JOIN vol ON r.ticker = vol.ticker AND r.trade_date = vol.trade_date
WHERE r.rn <= 3
GROUP BY r.ticker, r.trade_date
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
