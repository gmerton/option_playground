"""
Iron Butterfly study — short ATM straddle + long OTM strangle wings.

Structure (from the seller's perspective):
  Short 1x ATM call  (~50Δ)
  Short 1x ATM put   (~50Δ)   ← same strike
  Long  1x OTM call  (~wing_delta)
  Long  1x OTM put   (~wing_delta)   ← same expiry

P&L at expiry:
  net_credit = straddle_premium - call_wing_mid - put_wing_mid
  payout     = call_last + put_last - call_wing_last - put_wing_last
  profit     = net_credit - payout
  max_loss   = wing_width - net_credit
               where wing_width = MAX(call_wing_strike - atm_strike,
                                       atm_strike - put_wing_strike)

ROC (return on capital, max-loss basis):
  roc = profit / max_loss

Cache-based assembly:
  Uses silver.option_legs_settled (pre-computed Friday ~10 DTE legs with settlement
  prices) to assemble any wing delta variant as a local pandas join — no Athena
  round-trips per variant.

Usage:
  from lib.studies.iron_butterfly_study import load_legs_from_cache, assemble_iron_fly, compute_roc
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import awswrangler as wr

# ── Config ────────────────────────────────────────────────────────────────────

BODY_DELTA  = 0.50
BODY_TOL    = 0.08    # |delta ∓ 0.50| ≤ 0.08
WING_SEARCH = 0.15    # search window around wing_delta (± this)
MIN_CREDIT  = 0.05    # minimum net credit to include the trade

_LEGS_DB     = "silver"
_LEGS_TABLE  = "option_legs_settled"
_WORKGROUP   = "dev-v3"
_S3_OUTPUT   = "s3://athena-919061006621/"


# ── Cache loader ──────────────────────────────────────────────────────────────

def load_legs_from_cache(
    tickers: list[str],
    start: date,
    end: date,
) -> pd.DataFrame:
    """
    Load pre-built option legs from silver.option_legs_settled.

    Returns columns:
      ticker, entry_date, expiry, dte, cp, strike, delta, mid_entry, last_expiry
    """
    if not tickers:
        return pd.DataFrame()

    tickers_sql = ", ".join(f"'{t}'" for t in tickers)
    years_sql   = ", ".join(str(y) for y in range(start.year, end.year + 1))

    df = wr.athena.read_sql_query(
        sql=f"""
        SELECT ticker, entry_date, expiry, dte, cp, strike, delta, mid_entry, last_expiry
        FROM "{_LEGS_DB}"."{_LEGS_TABLE}"
        WHERE ticker IN ({tickers_sql})
          AND year   IN ({years_sql})
          AND entry_date >= DATE '{start.isoformat()}'
          AND entry_date <= DATE '{end.isoformat()}'
        """,
        database=_LEGS_DB,
        workgroup=_WORKGROUP,
        s3_output=_S3_OUTPUT,
    )
    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
        df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    return df


# ── Pandas assembly ───────────────────────────────────────────────────────────

def assemble_iron_fly(
    legs: pd.DataFrame,
    wing_delta: float,
    body_delta: float = BODY_DELTA,
    body_tol: float   = BODY_TOL,
    wing_search: float = WING_SEARCH,
    min_credit: float  = MIN_CREDIT,
) -> pd.DataFrame:
    """
    Assemble iron butterfly trades from pre-loaded leg cache.

    For each (ticker, entry_date, expiry):
      1. Best ATM call  : delta closest to +body_delta  (within ±body_tol)
      2. Matching put   : same strike, delta closest to -body_delta
      3. Best call wing : delta closest to +wing_delta, strike > atm_strike
      4. Best put wing  : delta closest to -wing_delta, strike < atm_strike

    Returns DataFrame with entry metrics and expiry settlement ready for compute_roc().
    """
    if legs.empty:
        return pd.DataFrame()

    KEY = ["ticker", "entry_date", "expiry"]

    calls = legs[legs["cp"] == "C"].copy()
    puts  = legs[legs["cp"] == "P"].copy()

    # ── Step 1: best ATM call per (ticker, entry_date, expiry) ────────────────
    atm_c = calls[
        (calls["delta"] >= body_delta - body_tol) &
        (calls["delta"] <= body_delta + body_tol)
    ].copy()
    atm_c["_err"] = (atm_c["delta"] - body_delta).abs()
    atm_c = (
        atm_c.sort_values("_err")
        .groupby(KEY, sort=False)
        .first()
        .reset_index()
        .rename(columns={"strike": "atm_strike", "delta": "call_delta",
                         "mid_entry": "call_mid", "last_expiry": "call_last_exp"})
        [KEY + ["atm_strike", "dte", "call_delta", "call_mid", "call_last_exp"]]
    )

    # ── Step 2: matching ATM put at same strike ───────────────────────────────
    atm_p = puts[
        (puts["delta"] >= -(body_delta + body_tol)) &
        (puts["delta"] <= -(body_delta - body_tol))
    ].copy()
    atm_p["_err"] = (atm_p["delta"] + body_delta).abs()
    # best put per (ticker, entry_date, expiry, strike)
    atm_p = (
        atm_p.sort_values("_err")
        .groupby(KEY + ["strike"], sort=False)
        .first()
        .reset_index()
        .rename(columns={"delta": "put_delta", "mid_entry": "put_mid",
                         "last_expiry": "put_last_exp"})
        [KEY + ["strike", "put_delta", "put_mid", "put_last_exp"]]
    )

    # Body: join on same strike
    body = atm_c.merge(
        atm_p.rename(columns={"strike": "atm_strike"}),
        on=KEY + ["atm_strike"],
        how="inner",
    )
    body["straddle_premium"] = body["call_mid"] + body["put_mid"]
    body = body[body["straddle_premium"] > 0]

    if body.empty:
        return pd.DataFrame()

    # ── Step 3: best OTM call wing ────────────────────────────────────────────
    wing_lo = max(0.01, wing_delta - wing_search)
    wing_hi = wing_delta + wing_search

    cw = calls[
        (calls["delta"] >= wing_lo) &
        (calls["delta"] <= wing_hi)
    ].copy()
    # join to get atm_strike, then filter OTM
    cw = cw.merge(body[KEY + ["atm_strike"]], on=KEY, how="inner")
    cw = cw[cw["strike"] > cw["atm_strike"]].copy()
    cw["_err"] = (cw["delta"] - wing_delta).abs()
    cw = (
        cw.sort_values("_err")
        .groupby(KEY, sort=False)
        .first()
        .reset_index()
        .rename(columns={"strike": "call_wing_strike", "delta": "call_wing_delta",
                         "mid_entry": "call_wing_mid", "last_expiry": "call_wing_last_exp"})
        [KEY + ["call_wing_strike", "call_wing_delta", "call_wing_mid", "call_wing_last_exp"]]
    )

    # ── Step 4: best OTM put wing ─────────────────────────────────────────────
    pw = puts[
        (puts["delta"] >= -wing_hi) &
        (puts["delta"] <= -wing_lo)
    ].copy()
    pw = pw.merge(body[KEY + ["atm_strike"]], on=KEY, how="inner")
    pw = pw[pw["strike"] < pw["atm_strike"]].copy()
    pw["_err"] = (-pw["delta"] - wing_delta).abs()
    pw = (
        pw.sort_values("_err")
        .groupby(KEY, sort=False)
        .first()
        .reset_index()
        .rename(columns={"strike": "put_wing_strike", "delta": "put_wing_delta",
                         "mid_entry": "put_wing_mid", "last_expiry": "put_wing_last_exp"})
        [KEY + ["put_wing_strike", "put_wing_delta", "put_wing_mid", "put_wing_last_exp"]]
    )

    # ── Step 5: combine all four legs ─────────────────────────────────────────
    out = (
        body
        .merge(cw, on=KEY, how="inner")
        .merge(pw, on=KEY, how="inner")
    )

    out["net_credit"]     = out["straddle_premium"] - out["call_wing_mid"] - out["put_wing_mid"]
    out["call_wing_width"] = out["call_wing_strike"] - out["atm_strike"]
    out["put_wing_width"]  = out["atm_strike"]       - out["put_wing_strike"]
    out["wing_width"]      = out[["call_wing_width", "put_wing_width"]].max(axis=1)

    # Payout: straddle assignment minus wing protection
    out["payout"] = (
        out["call_last_exp"] + out["put_last_exp"]
        - out["call_wing_last_exp"] - out["put_wing_last_exp"]
    )

    out = out[out["net_credit"] >= min_credit]
    return out.reset_index(drop=True)


# ── P&L ───────────────────────────────────────────────────────────────────────

def compute_roc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute profit, max_loss, and ROC for each iron butterfly trade.

    ROC = profit / max_loss  (positive = seller profit, expressed as %)
    win  = profit > 0

    Returns df with added columns: profit, max_loss, roc, win
    """
    if df.empty:
        return df

    out = df.copy()
    out = out.dropna(subset=["payout", "net_credit", "wing_width"])
    out = out[out["net_credit"] > 0]
    out = out[out["wing_width"] > out["net_credit"]]  # max_loss must be positive

    out["profit"]   = out["net_credit"] - out["payout"]
    out["max_loss"] = out["wing_width"] - out["net_credit"]

    # Clamp to theoretical bounds (stale last prices can occasionally violate)
    out["profit"] = out["profit"].clip(lower=-out["max_loss"], upper=out["net_credit"])

    out["roc"] = out["profit"] / out["max_loss"] * 100   # as percentage
    out["win"] = (out["profit"] > 0).astype(int)

    return out.reset_index(drop=True)
