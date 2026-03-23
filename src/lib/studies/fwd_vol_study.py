"""
Forward volatility ratio study — ATM put method.

For each (ticker, trade_date), computes:

  iv_put_10     : annualized BS IV of the ATM put nearest to 10 DTE  (optional leg)
  iv_put_30     : annualized BS IV of the ATM put nearest to 30 DTE
  iv_put_90     : annualized BS IV of the ATM put nearest to 90 DTE
  fvr_put_10_30 : forward vol ratio = σ_fwd(10→30) / iv_put_10  (NULL if no 10-DTE data)
  fvr_put_30_90 : forward vol ratio = σ_fwd(30→90) / iv_put_30

  where σ_fwd(T1,T2) = sqrt(max(0, iv_T2²×T2 - iv_T1²×T1) / (T2 - T1))
  with T in years.  Ratio > 1 = contango; ratio < 1 = backwardation.

Naming convention (extensible to other methods):
  iv_{method}_{dte}             e.g. iv_put_30, iv_put_90
  fvr_{method}_{near}_{far}     e.g. fvr_put_30_90, fvr_put_10_30
  Future: iv_straddle_30, iv_vix_30, fvr_straddle_30_90, etc.

Implementation notes:
  - IV is computed with S ≈ K (valid for near-ATM puts where |delta + 0.50| ≤ 0.15)
  - r = 0, q = 0 (small-T ATM: rate terms are second-order on the ratio)
  - 30 and 90 DTE legs are required; 10 DTE is LEFT-JOINed (NULL for monthly-only chains)
  - All three legs are sourced from options_daily_v3 via Athena
"""

from __future__ import annotations

import math
import pathlib
from datetime import date
from typing import Optional

import pandas as pd
import awswrangler as wr

from lib.athena_lib import athena
from lib.constants import DB, TABLE
from lib.commons.bs import implied_vol

# ── S3 / Glue constants ────────────────────────────────────────────────────────

FWD_VOL_DB    = "silver"
FWD_VOL_TABLE = "fwd_vol_daily"
_S3_FWD_VOL   = "s3://athena-919061006621/datasets/fwd_vol_daily/"

# ── DTE window parameters ─────────────────────────────────────────────────────

_EXTRA_DTE  = 10   # extra (shortest) leg — LEFT-JOINed; NULL for monthly-only chains
_NEAR_DTE   = 30
_FAR_DTE    = 90
_EXTRA_TOL  = 5    # accept dte in [5,  15]
_NEAR_TOL   = 7    # accept dte in [23, 37]
_FAR_TOL    = 14   # accept dte in [76, 104]
_DELTA_TOL  = 0.15  # |delta − (−0.50)| ≤ 0.15


# ── Athena query ──────────────────────────────────────────────────────────────

def fetch_atm_puts_all(
    tickers: list[str],
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """
    Fetch nearest-ATM puts at ~10 DTE (optional), ~30 DTE, and ~90 DTE for
    each (ticker, trade_date).

    The 30 and 90 DTE legs are INNER-JOINed (required).
    The 10 DTE leg is LEFT-JOINed — NULL for tickers with monthly-only chains.

    Returns columns:
      ticker, trade_date,
      strike_10, mid_10, delta_10, dte_10,   ← NULL when no weekly options
      strike_30, mid_30, delta_30, dte_30,
      strike_90, mid_90, delta_90, dte_90
    """
    if not tickers:
        return pd.DataFrame()

    tickers_sql = ", ".join(f"'{t}'" for t in tickers)
    extra_lo = _EXTRA_DTE - _EXTRA_TOL   # 5
    extra_hi = _EXTRA_DTE + _EXTRA_TOL   # 15
    near_lo  = _NEAR_DTE  - _NEAR_TOL    # 23
    near_hi  = _NEAR_DTE  + _NEAR_TOL    # 37
    far_lo   = _FAR_DTE   - _FAR_TOL     # 76
    far_hi   = _FAR_DTE   + _FAR_TOL     # 104

    sql = f"""
    WITH
    leg10 AS (
      SELECT
        ticker, trade_date, strike,
        (bid + ask) / 2.0 AS mid,
        delta,
        date_diff('day', trade_date, expiry) AS dte_val,
        ROW_NUMBER() OVER (
          PARTITION BY ticker, trade_date
          ORDER BY
            ABS(date_diff('day', trade_date, expiry) - {_EXTRA_DTE}),
            ABS(delta + 0.50)
        ) AS rn
      FROM "{DB}"."{TABLE}"
      WHERE ticker IN ({tickers_sql})
        AND cp = 'P'
        AND trade_date >= TIMESTAMP '{start_date.isoformat()} 00:00:00'
        AND trade_date <= TIMESTAMP '{end_date.isoformat()} 00:00:00'
        AND bid > 0 AND ask > 0 AND delta IS NOT NULL
        AND date_diff('day', trade_date, expiry) BETWEEN {extra_lo} AND {extra_hi}
        AND ABS(delta + 0.50) <= {_DELTA_TOL}
    ),
    leg30 AS (
      SELECT
        ticker, trade_date, strike,
        (bid + ask) / 2.0 AS mid,
        delta,
        date_diff('day', trade_date, expiry) AS dte_val,
        ROW_NUMBER() OVER (
          PARTITION BY ticker, trade_date
          ORDER BY
            ABS(date_diff('day', trade_date, expiry) - {_NEAR_DTE}),
            ABS(delta + 0.50)
        ) AS rn
      FROM "{DB}"."{TABLE}"
      WHERE ticker IN ({tickers_sql})
        AND cp = 'P'
        AND trade_date >= TIMESTAMP '{start_date.isoformat()} 00:00:00'
        AND trade_date <= TIMESTAMP '{end_date.isoformat()} 00:00:00'
        AND bid > 0 AND ask > 0 AND delta IS NOT NULL
        AND date_diff('day', trade_date, expiry) BETWEEN {near_lo} AND {near_hi}
        AND ABS(delta + 0.50) <= {_DELTA_TOL}
    ),
    leg90 AS (
      SELECT
        ticker, trade_date, strike,
        (bid + ask) / 2.0 AS mid,
        delta,
        date_diff('day', trade_date, expiry) AS dte_val,
        ROW_NUMBER() OVER (
          PARTITION BY ticker, trade_date
          ORDER BY
            ABS(date_diff('day', trade_date, expiry) - {_FAR_DTE}),
            ABS(delta + 0.50)
        ) AS rn
      FROM "{DB}"."{TABLE}"
      WHERE ticker IN ({tickers_sql})
        AND cp = 'P'
        AND trade_date >= TIMESTAMP '{start_date.isoformat()} 00:00:00'
        AND trade_date <= TIMESTAMP '{end_date.isoformat()} 00:00:00'
        AND bid > 0 AND ask > 0 AND delta IS NOT NULL
        AND date_diff('day', trade_date, expiry) BETWEEN {far_lo} AND {far_hi}
        AND ABS(delta + 0.50) <= {_DELTA_TOL}
    )
    SELECT
      n30.ticker,
      n30.trade_date,
      n10.strike   AS strike_10,
      n10.mid      AS mid_10,
      n10.delta    AS delta_10,
      n10.dte_val  AS dte_10,
      n30.strike   AS strike_30,
      n30.mid      AS mid_30,
      n30.delta    AS delta_30,
      n30.dte_val  AS dte_30,
      n90.strike   AS strike_90,
      n90.mid      AS mid_90,
      n90.delta    AS delta_90,
      n90.dte_val  AS dte_90
    FROM leg30 n30
    JOIN leg90 n90
      ON n30.ticker = n90.ticker AND n30.trade_date = n90.trade_date
      AND n90.rn = 1
    LEFT JOIN leg10 n10
      ON n30.ticker = n10.ticker AND n30.trade_date = n10.trade_date
      AND n10.rn = 1
    WHERE n30.rn = 1
    ORDER BY n30.ticker, n30.trade_date
    """

    df = athena(sql)
    if not df.empty:
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    return df


# Alias for backward compatibility
fetch_atm_puts = fetch_atm_puts_all


# ── IV / FVR computation ─────────────────────────────────────────────────────

def _safe_iv(mid: float, K: float, T: float) -> Optional[float]:
    """
    Compute ATM put IV with S ≈ K (valid when |delta + 0.50| ≤ 0.15).
    Returns None on failure.
    """
    if mid <= 0 or T <= 0 or K <= 0:
        return None
    return implied_vol(price=mid, S=K, K=K, T=T, r=0.0, q=0.0, opt_type="put")


def _fvr(iv_near: float, T_near: float, iv_far: float, T_far: float) -> float:
    """Forward vol ratio σ_fwd(T_near→T_far) / iv_near.  Returns 0.0 on extreme backwardation."""
    var_fwd = iv_far**2 * T_far - iv_near**2 * T_near
    if var_fwd <= 0:
        return 0.0
    return math.sqrt(var_fwd / (T_far - T_near)) / iv_near


def compute_all_fvr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given raw ATM put data from fetch_atm_puts_all, compute IV and forward vol ratios.

    Returns DataFrame with columns:
      ticker, trade_date, year,
      iv_put_10, iv_put_30, iv_put_90,
      fvr_put_10_30, fvr_put_30_90

    iv_put_10 and fvr_put_10_30 are NaN when no 10-DTE data exists (monthly-only chains).
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "ticker", "trade_date", "year",
            "iv_put_10", "iv_put_30", "iv_put_90",
            "fvr_put_10_30", "fvr_put_30_90",
        ])

    records = []
    for row in df.itertuples(index=False):
        T_near = row.dte_30 / 365.0
        T_far  = row.dte_90 / 365.0

        iv_near = _safe_iv(row.mid_30, row.strike_30, T_near)
        iv_far  = _safe_iv(row.mid_90, row.strike_90, T_far)

        if iv_near is None or iv_far is None or iv_near <= 0 or iv_far <= 0:
            continue

        fvr_30_90 = _fvr(iv_near, T_near, iv_far, T_far)

        td = row.trade_date
        yr = td.year if hasattr(td, "year") else pd.to_datetime(td).year

        rec: dict = {
            "ticker":        row.ticker,
            "trade_date":    td,
            "year":          yr,
            "iv_put_30":     round(iv_near,    6),
            "iv_put_90":     round(iv_far,     6),
            "fvr_put_30_90": round(fvr_30_90,  6),
            "iv_put_10":     None,
            "fvr_put_10_30": None,
        }

        # 10-DTE leg is optional (LEFT JOIN — may be pd.NA/None/NaN)
        dte_10    = getattr(row, "dte_10",    None)
        mid_10    = getattr(row, "mid_10",    None)
        strike_10 = getattr(row, "strike_10", None)
        if dte_10 is not None and not pd.isna(dte_10):
            T_extra = float(dte_10) / 365.0
            iv_extra = _safe_iv(float(mid_10), float(strike_10), T_extra)
            if iv_extra is not None and iv_extra > 0:
                rec["iv_put_10"]     = round(iv_extra, 6)
                rec["fvr_put_10_30"] = round(_fvr(iv_extra, T_extra, iv_near, T_near), 6)

        records.append(rec)

    return pd.DataFrame(records)


# Alias for backward compatibility
compute_fvr = compute_all_fvr


# ── S3 / Glue write ──────────────────────────────────────────────────────────

def write_fwd_vol(df: pd.DataFrame, mode: str = "append") -> None:
    """
    Write computed rows to S3 parquet and register/update the Glue table.

    mode:
      'append'              — add new partitions (safe for incremental updates)
      'overwrite_partitions' — replace only the year/ticker partitions in df
      'overwrite'           — full replace (use only for complete re-runs)
    """
    if df.empty:
        return

    out = df.copy()
    out["trade_date"] = pd.to_datetime(out["trade_date"])
    out["year"] = out["year"].astype(int)
    out["ticker"] = out["ticker"].astype(str)

    wr.s3.to_parquet(
        df=out,
        path=_S3_FWD_VOL,
        dataset=True,
        database=FWD_VOL_DB,
        table=FWD_VOL_TABLE,
        partition_cols=["year", "ticker"],
        compression="snappy",
        mode=mode,
        dtype={
            "trade_date":    "date",
            "iv_put_10":     "double",
            "iv_put_30":     "double",
            "iv_put_90":     "double",
            "fvr_put_10_30": "double",
            "fvr_put_30_90": "double",
            "year":          "int",
            "ticker":        "string",
        },
    )
    print(f"  [fwd_vol] wrote {len(out):,} rows → {FWD_VOL_DB}.{FWD_VOL_TABLE}")
