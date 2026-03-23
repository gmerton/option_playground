"""
Option legs settled cache — per-leg entry and settlement prices for near-ATM options.

For each (ticker, trade_date) where trade_date is a Friday with expiry ~10 DTE,
fetches all liquid near-ATM options (|delta| 0.02–0.55) and their settlement price
at expiry. This cache enables strategy assembly (iron condors, butterflies, spreads,
straddles) as local pandas joins rather than repeated Athena queries.

Schema (Glue table: silver.option_legs_settled)
------------------------------------------------
  ticker        string   } partition cols
  year          int      }
  entry_date    date       (Friday, ~10 DTE before expiry)
  expiry        date
  dte           int        (actual DTE at entry)
  cp            string     ('C' or 'P')
  strike        double
  delta         double     (actual delta at entry)
  mid_entry     double     (entry mid price)
  last_expiry   double     (settlement price; 0 if OTM/not traded)

Coverage
--------
  DTE range  : 5–15 (target 10)
  Delta range: 0.02–0.55 (both calls and puts, by absolute value)
  Liquidity  : bid > 0, ask > 0, open_interest > 0; bid-ask ≤ 35% of mid
  Entry day  : Fridays only (day_of_week = 5 in Trino/Athena)
  Best row per (ticker, trade_date, cp, strike): highest open_interest → highest bid

Usage
-----
  from lib.studies.option_legs_study import fetch_option_legs_batch, write_option_legs
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import awswrangler as wr

from lib.athena_lib import athena
from lib.constants import DB, TABLE

# ── S3 / Glue constants ────────────────────────────────────────────────────────

LEGS_DB    = "silver"
LEGS_TABLE = "option_legs_settled"
_S3_LEGS   = "s3://athena-919061006621/datasets/option_legs_settled/"

# ── Query parameters ──────────────────────────────────────────────────────────

_DTE_TARGET  = 10
_DTE_LO      = 5
_DTE_HI      = 15
_DELTA_LO    = 0.02   # absolute delta lower bound (strips deep OTM)
_DELTA_HI    = 0.55   # absolute delta upper bound (strips deep ITM)
_BA_MAX      = 0.35   # max (ask-bid)/mid


# ── SQL ───────────────────────────────────────────────────────────────────────

def _legs_sql(tickers: list[str], start: date, end: date) -> str:
    tickers_sql = ", ".join(f"'{t}'" for t in tickers)
    return f"""
    WITH
    -- Step 1: deduplicate entry rows — keep highest open_interest, break ties by bid
    entry_dedup AS (
      SELECT
        ticker, trade_date, expiry, cp, strike,
        delta,
        (bid + ask) / 2.0                        AS mid_entry,
        date_diff('day', trade_date, expiry)      AS dte
      FROM (
        SELECT *,
          ROW_NUMBER() OVER (
            PARTITION BY ticker, trade_date, cp, strike, expiry
            ORDER BY open_interest DESC NULLS LAST, bid DESC
          ) AS rn
        FROM "{DB}"."{TABLE}"
        WHERE ticker IN ({tickers_sql})
          AND trade_date >= TIMESTAMP '{start.isoformat()} 00:00:00'
          AND trade_date <= TIMESTAMP '{end.isoformat()} 00:00:00'
          AND day_of_week(trade_date) = 5
          AND bid > 0 AND ask > 0 AND open_interest > 0
          AND delta IS NOT NULL
          AND ABS(delta) BETWEEN {_DELTA_LO} AND {_DELTA_HI}
          AND (ask - bid) / ((ask + bid) / 2.0) <= {_BA_MAX}
          AND date_diff('day', trade_date, expiry) BETWEEN {_DTE_LO} AND {_DTE_HI}
      ) deduped
      WHERE rn = 1
    ),
    -- Step 2: settlement price at expiry (last traded price on expiry date)
    -- For calls: delta > 0; for puts: delta < 0
    settlement AS (
      SELECT
        o.ticker, o.expiry, o.cp, o.strike,
        MAX(COALESCE(o.last, 0)) AS last_expiry
      FROM "{DB}"."{TABLE}" o
      JOIN entry_dedup e
        ON o.ticker = e.ticker
       AND o.expiry = e.expiry
       AND o.cp     = e.cp
       AND o.strike = e.strike
      WHERE o.trade_date = o.expiry
      GROUP BY o.ticker, o.expiry, o.cp, o.strike
    )
    SELECT
      e.ticker,
      e.trade_date                          AS entry_date,
      e.expiry,
      e.dte,
      e.cp,
      e.strike,
      e.delta,
      e.mid_entry,
      COALESCE(s.last_expiry, 0)            AS last_expiry,
      YEAR(e.trade_date)                    AS year
    FROM entry_dedup e
    LEFT JOIN settlement s
      ON e.ticker = s.ticker
     AND e.expiry = s.expiry
     AND e.cp     = s.cp
     AND e.strike = s.strike
    ORDER BY e.ticker, e.trade_date, e.cp, e.strike
    """


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_option_legs_batch(
    tickers: list[str],
    start: date,
    end: date,
) -> pd.DataFrame:
    """
    Fetch all near-ATM option legs with settlement prices for a batch of tickers.

    Returns columns:
      ticker, entry_date, expiry, dte, cp, strike, delta, mid_entry, last_expiry, year
    """
    df = athena(_legs_sql(tickers, start, end))
    if df.empty:
        return df
    df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    df["year"]       = df["year"].astype(int)
    return df


# ── S3 / Glue write ───────────────────────────────────────────────────────────

def write_option_legs(df: pd.DataFrame, mode: str = "append") -> None:
    """
    Write computed rows to S3 parquet and register/update the Glue table.

    mode:
      'append'               — add new partitions (safe for incremental updates)
      'overwrite_partitions' — replace only the year/ticker partitions in df
      'overwrite'            — full replace (use only for complete re-runs)
    """
    if df.empty:
        return

    out = df.copy()
    out["entry_date"] = pd.to_datetime(out["entry_date"])
    out["expiry"]     = pd.to_datetime(out["expiry"])
    out["year"]       = out["year"].astype(int)
    out["ticker"]     = out["ticker"].astype(str)

    wr.s3.to_parquet(
        df=out,
        path=_S3_LEGS,
        dataset=True,
        database=LEGS_DB,
        table=LEGS_TABLE,
        partition_cols=["year", "ticker"],
        compression="snappy",
        mode=mode,
        dtype={
            "entry_date":   "date",
            "expiry":       "date",
            "dte":          "int",
            "cp":           "string",
            "strike":       "double",
            "delta":        "double",
            "mid_entry":    "double",
            "last_expiry":  "double",
            "year":         "int",
            "ticker":       "string",
        },
    )
    print(f"  [option_legs] wrote {len(out):,} rows → {LEGS_DB}.{LEGS_TABLE}")
