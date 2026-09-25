#!/usr/bin/env python3
"""Probe Athena options coverage for the sleeping-giants LEAP backtest.
Checks: (1) XOM trade_date range + row count, (2) long-dated LEAP coverage with
delta/bid/ask/OI as-of a historical date."""
import sys
sys.path.insert(0, '/Users/gmerton/v2/options_playground/src')
from lib.athena_lib import athena
from lib.constants import DB, TABLE, S3TABLES_CATALOG

T = f'"{S3TABLES_CATALOG}"."{DB}"."{TABLE}"'

print("=== (1) XOM date range + row count ===")
df = athena(f"""
  SELECT MIN(trade_date) AS min_dt, MAX(trade_date) AS max_dt, COUNT(*) AS rows
  FROM {T} WHERE ticker = 'XOM'
""")
print(df.to_string(index=False))

print("\n=== (2) XOM long-dated calls as-of 2021-06-30 (DTE 250-400) near 0.40 delta ===")
df2 = athena(f"""
  SELECT trade_date, expiry,
         date_diff('day', trade_date, expiry) AS dte,
         strike, delta, bid, ask, open_interest,
         ROUND((bid+ask)/2, 2) AS mid
  FROM {T}
  WHERE ticker = 'XOM' AND cp = 'C'
    AND trade_date = TIMESTAMP '2021-06-30 00:00:00'
    AND date_diff('day', trade_date, expiry) BETWEEN 250 AND 400
    AND delta BETWEEN 0.30 AND 0.50
    AND bid > 0 AND ask > 0
  ORDER BY ABS(delta - 0.40), dte
  LIMIT 15
""")
print(df2.to_string(index=False) if not df2.empty else "  (no rows — LEAP coverage gap at this date)")

print("\n=== (3) How many distinct long-dated expiries exist per year for XOM calls? ===")
df3 = athena(f"""
  SELECT year(trade_date) AS yr,
         COUNT(DISTINCT expiry) AS distinct_long_expiries,
         COUNT(*) AS leap_call_rows
  FROM {T}
  WHERE ticker = 'XOM' AND cp = 'C'
    AND date_diff('day', trade_date, expiry) BETWEEN 250 AND 400
    AND bid > 0 AND ask > 0
  GROUP BY year(trade_date)
  ORDER BY yr
""")
print(df3.to_string(index=False) if not df3.empty else "  (none)")
