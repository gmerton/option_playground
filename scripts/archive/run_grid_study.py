#!/usr/bin/env python3
"""
Grid Structure Study
====================
For every (ticker, Friday) in the ETF universe, simulate ALL valid
(call_Δ, put_Δ, DTE_target) combinations of a short strangle / straddle.
Produces a training dataset suitable for a conditional structure optimizer:

    f(market_features, call_Δ, put_Δ, DTE) → E[ROC]

Cache files written:
  data/cache/grid_options_etf.parquet   — wide options pull (delta 0.08-0.62, DTE 0-52)
  data/cache/grid_features_etf.parquet  — per-(ticker, date) market features
  data/cache/grid_training_etf.parquet  — final training dataset

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src \\
    .venv/bin/python3 run_grid_study.py [--refresh] [--refresh-opts] [--refresh-features]

Flags:
  --refresh          Rebuild everything from Athena
  --refresh-opts     Rebuild only the options cache (re-query Athena)
  --refresh-features Rebuild only the features cache
"""
from __future__ import annotations

import argparse
import math
import pathlib
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

_REPO_ROOT    = pathlib.Path(__file__).parent
_CACHE_DIR    = _REPO_ROOT / "data" / "cache"
_FVR_CACHE    = _CACHE_DIR / "fvr_daily.parquet"

_GRID_OPTS_CACHE     = _CACHE_DIR / "grid_options_etf.parquet"
_GRID_FEATURES_CACHE = _CACHE_DIR / "grid_features_etf.parquet"
_GRID_TRAINING_CACHE = _CACHE_DIR / "grid_training_etf.parquet"

# ── Date range ─────────────────────────────────────────────────────────────────
START_DATE = date(2018, 1, 1)
END_DATE   = date(2026, 3, 21)

# ── Options pull config ─────────────────────────────────────────────────────────
DELTA_PULL_MIN = 0.08   # pull slightly wider than the grid for matching slack
DELTA_PULL_MAX = 0.62
DTE_PULL_MIN   = 0      # include expiry-day marks for settlement
DTE_PULL_MAX   = 52

# ── Structure grid ──────────────────────────────────────────────────────────────
CALL_DELTA_TARGETS = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
PUT_DELTA_TARGETS  = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
DTE_TARGETS        = [15, 20, 30, 45]
DELTA_TOL          = 0.07   # max delta error for leg matching

# ── Exit rules ─────────────────────────────────────────────────────────────────
PROFIT_TAKE = 0.50   # exit when premium decays to 50%
STOP_MULT   = 2.0    # exit when premium doubles

# ── Universe (same as run_iv_condor_study.py after coverage filter) ─────────────
ETF_UNIVERSE = sorted([
    "SPY", "QQQ", "IWM", "DIA",
    "XLF", "XLE", "XLI", "XLB", "XLU", "XLP",
    "XBI", "XRT", "XOP",
    "GDX", "SLV", "GLD",
    "USO", "UNG",
    "TQQQ", "UPRO", "TNA",
    "EEM", "EFA", "EWZ", "EWY", "FXI", "FEZ",
    "TLT", "IEF", "LQD",
    "IYR", "JETS", "FEZ",
])
# deduplicate
ETF_UNIVERSE = sorted(set(ETF_UNIVERSE))

VOL_INDEX_PROXY: dict[str, str] = {
    "SPY":  "^VIX",
    "QQQ":  "^VXN",
    "IWM":  "^RVX",
    "TQQQ": "^VXN",
    "UPRO": "^VIX",
    "DIA":  "^VIX",
}

IVP_LOOKBACK    = 252
IVP_MIN_PERIODS = 60

MIN_COVERAGE = 0.70   # min fraction of Fridays with options data to keep ticker


# ═══════════════════════════════════════════════════════════════════════════════
# 1. OPTIONS DATA
# ═══════════════════════════════════════════════════════════════════════════════

def pull_wide_options(tickers: list[str]) -> pd.DataFrame:
    """Query Athena for wide options universe: all delta/DTE combos needed for grid."""
    from lib.athena_lib import athena
    ticker_list = ", ".join(f"'{t}'" for t in tickers)
    print(f"Querying Athena: {len(tickers)} tickers, "
          f"delta {DELTA_PULL_MIN}–{DELTA_PULL_MAX}, DTE {DTE_PULL_MIN}–{DTE_PULL_MAX} ...")
    sql = f"""
    SELECT
        ticker,
        trade_date,
        expiry,
        strike,
        CAST((bid + ask) / 2.0 AS DOUBLE) AS mid,
        CAST(delta AS DOUBLE)              AS delta,
        cp,
        date_diff('day', trade_date, expiry) AS dte
    FROM "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"
    WHERE ticker IN ({ticker_list})
      AND trade_date >= TIMESTAMP '{START_DATE} 00:00:00'
      AND trade_date <= TIMESTAMP '{END_DATE} 23:59:59'
      AND bid > 0
      AND delta IS NOT NULL
      AND ABS(delta) BETWEEN {DELTA_PULL_MIN} AND {DELTA_PULL_MAX}
      AND date_diff('day', trade_date, expiry) BETWEEN {DTE_PULL_MIN} AND {DTE_PULL_MAX}
    ORDER BY ticker, trade_date, expiry, cp, strike
    """
    df = athena(sql)
    print(f"  Athena returned {len(df):,} rows")
    return df


def load_options(tickers: list[str], refresh: bool = False) -> pd.DataFrame:
    if not refresh and _GRID_OPTS_CACHE.exists():
        print(f"Loading grid options from cache: {_GRID_OPTS_CACHE}")
        df = pd.read_parquet(_GRID_OPTS_CACHE)
        print(f"  {len(df):,} rows, {df['ticker'].nunique()} tickers")
    else:
        df = pull_wide_options(tickers)
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(_GRID_OPTS_CACHE, index=False)
        print(f"  Saved → {_GRID_OPTS_CACHE}")

    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    df["strike"]     = df["strike"].astype(float)
    df["mid"]        = df["mid"].astype(float)
    df["delta"]      = df["delta"].abs().astype(float)
    df["dte"]        = df["dte"].astype(int)
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 2. FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

def _rolling_ivp(iv_series: pd.Series) -> pd.Series:
    iv_arr = iv_series.values.astype(float)
    out    = np.full(len(iv_arr), np.nan)
    for i in range(IVP_MIN_PERIODS, len(iv_arr)):
        cur = iv_arr[i]
        if math.isnan(cur):
            continue
        hist = iv_arr[max(0, i - IVP_LOOKBACK):i]
        hist = hist[~np.isnan(hist)]
        if len(hist) == 0:
            continue
        out[i] = (hist < cur).sum() / len(hist) * 100.0
    return pd.Series(out, index=iv_series.index)


def build_features(
    tickers: list[str],
    opts_df: pd.DataFrame,
    spot_maps: dict[str, dict[date, float]],
    refresh: bool = False,
) -> pd.DataFrame:
    """Build per-(ticker, date) feature DataFrame.

    Features:
      ivp         — 252d IV percentile (options-derived credit/spot proxy)
      vix         — ^VIX level
      vix_ivp     — 252d percentile of VIX
      rv20        — 20-day realized vol (annualised)
      iv_rv_ratio — ATM straddle credit / (spot * rv20 / sqrt(252)) crude IV/RV
      spot_50ma   — spot / 50-day SMA ratio
      spot_200ma  — spot / 200-day SMA ratio
      skew_25d    — (0.25Δ put mid − 0.25Δ call mid) / spot at nearest 20-DTE expiry
      term_slope  — ATM credit 20-DTE / ATM credit 45-DTE (front/back)
      fvr_30_90   — forward vol ratio from FVR cache (NaN if unavailable)
    """
    if not refresh and _GRID_FEATURES_CACHE.exists():
        print(f"Loading features from cache: {_GRID_FEATURES_CACHE}")
        feat = pd.read_parquet(_GRID_FEATURES_CACHE)
        feat["trade_date"] = pd.to_datetime(feat["trade_date"]).dt.date
        print(f"  {len(feat):,} rows")
        return feat

    print("Building features ...")
    import yfinance as yf

    # ── Spot-derived features: rv20, 50MA, 200MA ─────────────────────────────
    print("  Computing RV20, moving averages ...")
    spot_feat_rows = []
    for ticker, sm in spot_maps.items():
        if not sm:
            continue
        prices = pd.Series(sm).sort_index()
        log_ret = np.log(prices / prices.shift(1))
        rv20    = log_ret.rolling(20).std() * np.sqrt(252)
        ma50    = prices.rolling(50).mean()
        ma200   = prices.rolling(200).mean()
        for d in prices.index:
            spot_feat_rows.append({
                "ticker":     ticker,
                "trade_date": d,
                "spot":       prices[d],
                "rv20":       rv20.get(d, np.nan),
                "spot_50ma":  prices[d] / ma50[d] if not math.isnan(float(ma50.get(d, np.nan) or np.nan)) and ma50.get(d) else np.nan,
                "spot_200ma": prices[d] / ma200[d] if not math.isnan(float(ma200.get(d, np.nan) or np.nan)) and ma200.get(d) else np.nan,
            })
    spot_feat = pd.DataFrame(spot_feat_rows)

    # ── VIX + VIX_IVP ─────────────────────────────────────────────────────────
    print("  Downloading VIX ...")
    vix_raw = yf.download("^VIX",
                          start=str(START_DATE),
                          end=str(END_DATE + timedelta(days=5)),
                          progress=False, auto_adjust=True)
    vix_raw.index = pd.to_datetime(vix_raw.index).date
    if isinstance(vix_raw.columns, pd.MultiIndex):
        vix_s = vix_raw["Close"]["^VIX"].dropna()
    else:
        vix_s = vix_raw["Close"].dropna()
    vix_ivp_s = _rolling_ivp(vix_s)
    vix_df = pd.DataFrame({
        "trade_date": vix_s.index,
        "vix":        vix_s.values.astype(float),
        "vix_ivp":    vix_ivp_s.values,
    })

    # ── Options-derived features: IVP, skew, term structure ──────────────────
    print("  Computing per-ticker options features ...")
    opts_by_ticker_date = opts_df.groupby(["ticker", "trade_date"])

    ivp_rows     = []
    skew_rows    = []
    term_rows    = []
    iv_rv_rows   = []

    def _find_opt(day_df, cp, target_delta, dte_lo, dte_hi):
        sub = day_df[(day_df["cp"] == cp) &
                     (day_df["dte"] >= dte_lo) &
                     (day_df["dte"] <= dte_hi)].copy()
        if sub.empty:
            return None
        # pick expiry closest to midpoint of DTE range
        target_dte = (dte_lo + dte_hi) / 2
        best_exp = sub.iloc[(sub["dte"] - target_dte).abs().argsort()[:1]]["expiry"].iloc[0]
        sub = sub[sub["expiry"] == best_exp].copy()
        sub["_derr"] = (sub["delta"] - target_delta).abs()
        sub = sub[sub["_derr"] <= DELTA_TOL]
        if sub.empty:
            return None
        return sub.loc[sub["_derr"].idxmin()]

    daily_iv_by_ticker: dict[str, dict[date, float]] = {t: {} for t in tickers}

    for (ticker, trade_date), day_df in opts_by_ticker_date:
        spot = spot_maps.get(ticker, {}).get(trade_date)
        if not spot or spot <= 0:
            continue

        # IVP proxy: ATM straddle credit / spot at ~20 DTE
        c20 = _find_opt(day_df, "C", 0.50, 15, 25)
        if c20 is not None:
            # find matching put at same expiry/strike
            p_same = day_df[
                (day_df["cp"] == "P") &
                (day_df["expiry"] == c20["expiry"]) &
                (day_df["strike"] == c20["strike"])
            ]
            if not p_same.empty:
                credit_atm = c20["mid"] + p_same.iloc[0]["mid"]
                iv_proxy   = credit_atm / spot
                if iv_proxy > 0:
                    daily_iv_by_ticker[ticker][trade_date] = iv_proxy

        # Skew: (0.25Δ put mid − 0.25Δ call mid) / spot at ~20 DTE
        c_25 = _find_opt(day_df, "C", 0.25, 15, 25)
        p_25 = _find_opt(day_df, "P", 0.25, 15, 25)
        if c_25 is not None and p_25 is not None:
            skew = (p_25["mid"] - c_25["mid"]) / spot
            skew_rows.append({"ticker": ticker, "trade_date": trade_date, "skew_25d": skew})

        # Term structure: ATM credit at ~20 DTE vs ~45 DTE
        c20_atm = _find_opt(day_df, "C", 0.50, 15, 25)
        c45_atm = _find_opt(day_df, "C", 0.50, 38, 52)
        if c20_atm is not None and c45_atm is not None:
            p20_same = day_df[
                (day_df["cp"] == "P") &
                (day_df["expiry"] == c20_atm["expiry"]) &
                (day_df["strike"] == c20_atm["strike"])
            ]
            p45_same = day_df[
                (day_df["cp"] == "P") &
                (day_df["expiry"] == c45_atm["expiry"]) &
                (day_df["strike"] == c45_atm["strike"])
            ]
            if not p20_same.empty and not p45_same.empty:
                cr20 = c20_atm["mid"] + p20_same.iloc[0]["mid"]
                cr45 = c45_atm["mid"] + p45_same.iloc[0]["mid"]
                if cr45 > 0:
                    term_rows.append({
                        "ticker": ticker, "trade_date": trade_date,
                        "term_slope": cr20 / cr45,
                    })

    # Build IVP per ticker
    for ticker, daily_iv in daily_iv_by_ticker.items():
        if len(daily_iv) < IVP_MIN_PERIODS:
            continue
        iv_s   = pd.Series(daily_iv).sort_index()
        ivp_s  = _rolling_ivp(iv_s)
        for d, v in ivp_s.items():
            if not math.isnan(v):
                ivp_rows.append({"ticker": ticker, "trade_date": d, "ivp": v})

    ivp_df  = pd.DataFrame(ivp_rows)  if ivp_rows  else pd.DataFrame(columns=["ticker","trade_date","ivp"])
    skew_df = pd.DataFrame(skew_rows) if skew_rows else pd.DataFrame(columns=["ticker","trade_date","skew_25d"])
    term_df = pd.DataFrame(term_rows) if term_rows else pd.DataFrame(columns=["ticker","trade_date","term_slope"])

    # ── FVR cache ──────────────────────────────────────────────────────────────
    print("  Loading FVR cache ...")
    fvr_rows = []
    if _FVR_CACHE.exists():
        fvr = pd.read_parquet(_FVR_CACHE)
        fvr["entry_date"] = pd.to_datetime(fvr["entry_date"]).dt.date
        fvr = fvr[fvr["ticker"].isin(tickers)][["ticker", "entry_date", "fvr_put_30_90"]].copy()
        fvr.columns = ["ticker", "trade_date", "fvr_30_90"]
        fvr_df = fvr
    else:
        fvr_df = pd.DataFrame(columns=["ticker", "trade_date", "fvr_30_90"])

    # ── Merge all features ─────────────────────────────────────────────────────
    print("  Merging features ...")
    feat = spot_feat.merge(vix_df,  on="trade_date", how="left")
    feat = feat.merge(ivp_df,  on=["ticker", "trade_date"], how="left")
    feat = feat.merge(skew_df, on=["ticker", "trade_date"], how="left")
    feat = feat.merge(term_df, on=["ticker", "trade_date"], how="left")
    feat = feat.merge(fvr_df,  on=["ticker", "trade_date"], how="left")

    # iv_rv_ratio: ivp proxy already divides by spot; just use rv20 for IV/RV
    # Proxy: (daily_iv_proxy × sqrt(252)) / rv20 — ratio of implied to realised annual vol
    iv_proxy_df = ivp_df.rename(columns={"ivp": "_ivp_pct"})  # IVP is percentile, not raw IV
    # Recompute raw IV proxy for iv_rv_ratio
    iv_raw_rows = [
        {"ticker": t, "trade_date": d, "_iv_raw": v}
        for t, daily_iv in daily_iv_by_ticker.items()
        for d, v in daily_iv.items()
    ]
    if iv_raw_rows:
        iv_raw_df = pd.DataFrame(iv_raw_rows)
        feat = feat.merge(iv_raw_df, on=["ticker", "trade_date"], how="left")
        feat["iv_rv_ratio"] = (feat["_iv_raw"] * np.sqrt(252)) / feat["rv20"].replace(0, np.nan)
        feat.drop(columns=["_iv_raw"], inplace=True)
    else:
        feat["iv_rv_ratio"] = np.nan

    feat.drop(columns=["spot"], inplace=True)

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    feat.to_parquet(_GRID_FEATURES_CACHE, index=False)
    print(f"  Saved → {_GRID_FEATURES_CACHE}  ({len(feat):,} rows)")
    return feat


# ═══════════════════════════════════════════════════════════════════════════════
# 3. OPTION MATCHING
# ═══════════════════════════════════════════════════════════════════════════════

def find_option_at(
    day_opts: pd.DataFrame,
    cp:           str,
    target_delta: float,
    dte_target:   int,
    expiry:       Optional[date] = None,
) -> Optional[pd.Series]:
    """Find best option matching (cp, target_delta, dte_target).

    If expiry is supplied, restrict to that expiry (used for put leg matching
    after call leg has been selected).
    """
    dte_lo = dte_target - 3
    dte_hi = dte_target + 3

    sub = day_opts[day_opts["cp"] == cp].copy()

    if expiry is not None:
        sub = sub[sub["expiry"] == expiry]
    else:
        window = sub[(sub["dte"] >= dte_lo) & (sub["dte"] <= dte_hi)]
        if window.empty:
            return None
        best_exp = window.iloc[(window["dte"] - dte_target).abs().argsort()[:1]]["expiry"].iloc[0]
        sub = sub[sub["expiry"] == best_exp]

    sub = sub.copy()
    sub["_derr"] = (sub["delta"] - target_delta).abs()
    sub = sub[sub["_derr"] <= DELTA_TOL]
    if sub.empty:
        return None
    return sub.loc[sub["_derr"].idxmin()]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SETTLEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def settle_at_expiry(
    credit:      float,
    call_strike: float,
    put_strike:  float,
    expiry:      date,
    dm_c:        dict,
    dm_p:        dict,
    spot_map:    dict,
) -> float:
    """Settle at expiry using Athena option marks where possible.

    For a strangle/straddle at most ONE leg is ITM at expiry:
    - Found mark → that leg has value; missing leg is OTM (worth $0)
    - Neither found → both expired worthless → full profit (credit)
    - Fallback to yfinance spot only if that implies plausible intrinsic.
    """
    c_exp = dm_c.get((expiry, expiry, call_strike))
    p_exp = dm_p.get((expiry, expiry, put_strike))

    if c_exp is not None or p_exp is not None:
        return credit - ((c_exp or 0.0) + (p_exp or 0.0))

    # Neither mark: check yfinance spot as fallback
    spot = (spot_map.get(expiry) or
            spot_map.get(expiry - timedelta(days=1)) or
            spot_map.get(expiry - timedelta(days=2)))
    if spot is None:
        return credit   # no data — assume worthless (conservative win)

    c_int    = max(0.0, spot - call_strike)
    p_int    = max(0.0, put_strike - spot)
    intrinsic = c_int + p_int

    # Guard against split-adjustment artifacts (intrinsic > 3× credit is impossible)
    if intrinsic > credit * 3:
        return credit

    return credit - intrinsic


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

def simulate_one(
    entry_date:  date,
    expiry:      date,
    call_strike: float,
    put_strike:  float,
    credit:      float,
    dm_c:        dict,
    dm_p:        dict,
    spot_map:    dict,
) -> dict:
    """Simulate one short strangle/straddle trade."""
    take_target = credit * (1.0 - PROFIT_TAKE)
    stop_level  = credit * STOP_MULT
    mark_days = 0
    total_days = 0

    cur = entry_date + timedelta(days=1)
    while cur <= expiry:
        total_days += 1
        c_mid = dm_c.get((cur, expiry, call_strike))
        p_mid = dm_p.get((cur, expiry, put_strike))

        if c_mid is not None and p_mid is not None:
            mark_days += 1
            net_val = c_mid + p_mid
            if net_val <= take_target:
                return dict(pnl=credit - net_val, exit="profit_take",
                            days=(cur - entry_date).days,
                            mark_cov=mark_days / total_days)
            if net_val >= stop_level:
                return dict(pnl=credit - net_val, exit="stop_loss",
                            days=(cur - entry_date).days,
                            mark_cov=mark_days / total_days)

        if cur >= expiry:
            pnl = settle_at_expiry(credit, call_strike, put_strike, expiry,
                                   dm_c, dm_p, spot_map)
            cov = mark_days / total_days if total_days else 0.0
            return dict(pnl=pnl,
                        exit="expiry_win" if pnl >= 0 else "expiry_loss",
                        days=(expiry - entry_date).days,
                        mark_cov=cov)

        cur += timedelta(days=1)

    # Fallback
    pnl = settle_at_expiry(credit, call_strike, put_strike, expiry,
                           dm_c, dm_p, spot_map)
    cov = mark_days / total_days if total_days else 0.0
    return dict(pnl=pnl,
                exit="expiry_win" if pnl >= 0 else "expiry_loss",
                days=(expiry - entry_date).days,
                mark_cov=cov)


def _simulate_ticker(
    ticker:    str,
    ticker_df: pd.DataFrame,
    ivp_map:   dict,
    spot_map:  dict,
    feat_index,
    feat_cols: list[str],
    fridays:   list,
) -> list[dict]:
    """Simulate all grid combos for a single ticker. Returns a list of row dicts."""
    calls = ticker_df[ticker_df["cp"] == "C"]
    puts  = ticker_df[ticker_df["cp"] == "P"]
    dm_c  = {(r.trade_date, r.expiry, r.strike): r.mid
              for r in calls.itertuples(index=False)}
    dm_p  = {(r.trade_date, r.expiry, r.strike): r.mid
              for r in puts.itertuples(index=False)}
    opts_by_date = {d: g for d, g in ticker_df.groupby("trade_date")}

    rows = []
    for edate in fridays:
        ivp = ivp_map.get((ticker, edate))
        if ivp is None:
            continue
        day_opts = opts_by_date.get(edate)
        if day_opts is None:
            continue
        try:
            feat_row  = feat_index.loc[(ticker, edate)]
            feat_vals = {c: feat_row[c] for c in feat_cols}
        except KeyError:
            feat_vals = {c: np.nan for c in feat_cols}

        for dte_tgt in DTE_TARGETS:
            call_cache: dict[float, Optional[pd.Series]] = {}
            for c_delta in CALL_DELTA_TARGETS:
                if c_delta not in call_cache:
                    call_cache[c_delta] = find_option_at(day_opts, "C", c_delta, dte_tgt)
                call_row = call_cache[c_delta]
                if call_row is None:
                    continue

                for p_delta in PUT_DELTA_TARGETS:
                    put_row = find_option_at(
                        day_opts, "P", p_delta, dte_tgt, expiry=call_row["expiry"]
                    )
                    if put_row is None:
                        continue
                    if put_row["strike"] > call_row["strike"]:
                        continue
                    credit = call_row["mid"] + put_row["mid"]
                    if credit <= 0:
                        continue

                    sim = simulate_one(
                        edate, call_row["expiry"],
                        call_row["strike"], put_row["strike"],
                        credit, dm_c, dm_p, spot_map,
                    )
                    rows.append({
                        "ticker":      ticker,
                        "edate":       edate,
                        "year":        edate.year,
                        "c_delta_tgt": c_delta,
                        "p_delta_tgt": p_delta,
                        "dte_tgt":     dte_tgt,
                        "expiry":      call_row["expiry"],
                        "call_strike": call_row["strike"],
                        "put_strike":  put_row["strike"],
                        "c_delta_act": call_row["delta"],
                        "p_delta_act": put_row["delta"],
                        "actual_dte":  call_row["dte"],
                        "credit":      credit,
                        "ivp":         ivp,
                        **feat_vals,
                        **sim,
                    })
    return rows


def run_grid_simulation(
    tickers:    list[str],
    opts_df:    pd.DataFrame,
    ivp_map:    dict,
    spot_maps:  dict,
    feat_df:    pd.DataFrame,
    out_path:   pathlib.Path = _GRID_TRAINING_CACHE,
) -> pd.DataFrame:
    """
    For every (ticker, Friday, call_Δ_target, put_Δ_target, DTE_target),
    simulate and record outcome + features.

    Processes one ticker at a time and writes results incrementally to avoid
    accumulating the full dataset in RAM.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    feat_df = feat_df.copy()
    feat_df["trade_date"] = pd.to_datetime(feat_df["trade_date"]).dt.date
    feat_index = feat_df.set_index(["ticker", "trade_date"])
    feat_cols  = [c for c in feat_df.columns if c not in ("ticker", "trade_date")]

    fridays = [
        START_DATE + timedelta(days=i)
        for i in range((END_DATE - START_DATE).days + 1)
        if (START_DATE + timedelta(days=i)).weekday() == 4
    ]

    print(f"\nRunning grid: {len(fridays)} Fridays × {len(tickers)} tickers × "
          f"{len(CALL_DELTA_TARGETS)}×{len(PUT_DELTA_TARGETS)}×{len(DTE_TARGETS)} combos")
    print("  (writing incrementally — one ticker at a time)")

    writer    = None
    schema    = None
    total_sim = 0
    ticker_groups = {ticker: grp for ticker, grp in opts_df.groupby("ticker")}

    for i, ticker in enumerate(tickers):
        ticker_df = ticker_groups.get(ticker)
        if ticker_df is None:
            print(f"  [{i+1}/{len(tickers)}] {ticker}: no options data, skipping")
            continue

        rows = _simulate_ticker(
            ticker, ticker_df, ivp_map,
            spot_maps.get(ticker, {}),
            feat_index, feat_cols, fridays,
        )
        if not rows:
            print(f"  [{i+1}/{len(tickers)}] {ticker}: 0 trades")
            continue

        chunk = pd.DataFrame(rows)
        chunk["roc"] = chunk["pnl"] / chunk["credit"]
        chunk["win"] = (chunk["pnl"] > 0).astype(int)
        total_sim   += len(chunk)

        tbl = pa.Table.from_pandas(chunk, preserve_index=False)
        if writer is None:
            schema = tbl.schema
            writer = pq.ParquetWriter(out_path, schema)
        writer.write_table(tbl)

        print(f"  [{i+1}/{len(tickers)}] {ticker}: {len(chunk):,} trades  "
              f"(cumulative: {total_sim:,})")

        # Free this ticker's memory before moving on
        del ticker_df, rows, chunk, tbl
        ticker_groups[ticker] = None   # release the reference

    if writer is not None:
        writer.close()

    print(f"\n  Total simulated: {total_sim:,} trades")

    if total_sim == 0:
        return pd.DataFrame()

    df = pd.read_parquet(out_path)
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 6. IVP
# ═══════════════════════════════════════════════════════════════════════════════

def load_ivp(tickers: list[str], opts_df: pd.DataFrame,
             spot_maps: dict) -> dict[tuple, float]:
    """Compute IVP from vol-index proxies, FVR cache, then options data."""
    import yfinance as yf

    ivp_map: dict[tuple, float] = {}

    # Vol-index proxies
    proxy_tickers = [t for t in tickers if t in VOL_INDEX_PROXY]
    if proxy_tickers:
        proxy_syms = sorted(set(VOL_INDEX_PROXY[t] for t in proxy_tickers))
        print(f"Downloading vol-index proxies: {proxy_syms} ...")
        raw = yf.download(proxy_syms,
                          start=str(START_DATE),
                          end=str(END_DATE + timedelta(days=5)),
                          progress=False, auto_adjust=True)
        if isinstance(raw.columns, pd.MultiIndex):
            closes = raw["Close"]
        else:
            closes = raw[["Close"]].rename(columns={"Close": proxy_syms[0]})
        closes.index = pd.to_datetime(closes.index).date
        sym_ivp: dict[str, pd.Series] = {}
        for sym in proxy_syms:
            if sym not in closes.columns:
                continue
            iv_s = closes[sym].dropna() / 100.0
            sym_ivp[sym] = _rolling_ivp(iv_s)
        for tkr in proxy_tickers:
            sym = VOL_INDEX_PROXY[tkr]
            if sym not in sym_ivp:
                continue
            for d, v in sym_ivp[sym].items():
                if not math.isnan(v):
                    ivp_map[(tkr, d)] = v

    # FVR cache
    fvr_tickers = [t for t in tickers if t not in VOL_INDEX_PROXY]
    if fvr_tickers and _FVR_CACHE.exists():
        fvr = pd.read_parquet(_FVR_CACHE)
        fvr = fvr[fvr["ticker"].isin(fvr_tickers)].copy()
        fvr["entry_date"] = pd.to_datetime(fvr["entry_date"]).dt.date
        fvr = fvr.sort_values(["ticker", "entry_date"])
        for ticker, grp in fvr.groupby("ticker"):
            iv_s  = grp.set_index("entry_date")["iv_put_30"]
            ivp_s = _rolling_ivp(iv_s)
            for d, v in ivp_s.items():
                if not math.isnan(v):
                    ivp_map[(ticker, d)] = v

    # Options-derived IVP for remaining tickers
    covered = {k[0] for k in ivp_map}
    missing = [t for t in tickers if t not in covered]
    if missing:
        print(f"Computing options-derived IVP for {len(missing)} tickers ...")
        sub = opts_df[opts_df["ticker"].isin(missing)]
        for ticker, grp in sub.groupby("ticker"):
            sm = spot_maps.get(ticker, {})
            daily_iv: dict[date, float] = {}
            for td, day in grp.groupby("trade_date"):
                spot = sm.get(td)
                if not spot or spot <= 0:
                    continue
                c = find_option_at(day, "C", 0.50, 20)
                if c is None:
                    continue
                p_same = day[(day["cp"] == "P") &
                             (day["expiry"] == c["expiry"]) &
                             (day["strike"] == c["strike"])]
                if p_same.empty:
                    continue
                cr = c["mid"] + p_same.iloc[0]["mid"]
                if cr > 0:
                    daily_iv[td] = cr / spot
            if len(daily_iv) < IVP_MIN_PERIODS:
                continue
            iv_s  = pd.Series(daily_iv).sort_index()
            ivp_s = _rolling_ivp(iv_s)
            for d, v in ivp_s.items():
                if not math.isnan(v):
                    ivp_map[(ticker, d)] = v

    covered_total = len({k[0] for k in ivp_map})
    print(f"  IVP: {len(ivp_map):,} (ticker, date) pairs, {covered_total} tickers")
    return ivp_map


# ═══════════════════════════════════════════════════════════════════════════════
# 7. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh",          action="store_true",
                        help="Rebuild everything from Athena")
    parser.add_argument("--refresh-opts",     action="store_true",
                        help="Rebuild only the options cache")
    parser.add_argument("--refresh-features", action="store_true",
                        help="Rebuild only the features cache")
    args = parser.parse_args()

    refresh_opts  = args.refresh or args.refresh_opts
    refresh_feats = args.refresh or args.refresh_features
    refresh_train = args.refresh

    tickers = ETF_UNIVERSE
    print(f"Universe: {len(tickers)} tickers")

    # ── Options ───────────────────────────────────────────────────────────────
    opts_df = load_options(tickers, refresh=refresh_opts)

    # ── Chain coverage filter ─────────────────────────────────────────────────
    fridays = [
        START_DATE + timedelta(days=i)
        for i in range((END_DATE - START_DATE).days + 1)
        if (START_DATE + timedelta(days=i)).weekday() == 4
    ]
    opts_fridays = opts_df[opts_df["trade_date"].apply(lambda d: d.weekday() == 4)]
    cov_counts   = opts_fridays.groupby("ticker")["trade_date"].nunique()
    n_fridays    = len(fridays)
    tickers = [t for t in tickers
               if cov_counts.get(t, 0) / n_fridays >= MIN_COVERAGE]
    print(f"After coverage filter: {len(tickers)} tickers")
    opts_df = opts_df[opts_df["ticker"].isin(tickers)]

    # ── Spot prices ───────────────────────────────────────────────────────────
    print("Downloading spot prices ...")
    import yfinance as yf
    raw = yf.download(tickers,
                      start=str(START_DATE),
                      end=str(END_DATE + timedelta(days=5)),
                      progress=False, auto_adjust=False)
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]].rename(columns={"Close": tickers[0]})
    close.index = pd.to_datetime(close.index).date
    spot_maps: dict[str, dict[date, float]] = {}
    for t in tickers:
        if t in close.columns:
            s = close[t].dropna()
            spot_maps[t] = {d: float(v) for d, v in zip(s.index, s.values)}
    print(f"  Spot loaded for {len(spot_maps)}/{len(tickers)} tickers")

    # ── IVP ───────────────────────────────────────────────────────────────────
    ivp_map = load_ivp(tickers, opts_df, spot_maps)

    # ── Features ──────────────────────────────────────────────────────────────
    feat_df = build_features(tickers, opts_df, spot_maps, refresh=refresh_feats)

    # ── Grid simulation ───────────────────────────────────────────────────────
    if not refresh_train and _GRID_TRAINING_CACHE.exists():
        print(f"\nLoading training data from cache: {_GRID_TRAINING_CACHE}")
        df = pd.read_parquet(_GRID_TRAINING_CACHE)
        print(f"  {len(df):,} rows")
    else:
        df = run_grid_simulation(tickers, opts_df, ivp_map, spot_maps, feat_df,
                                 out_path=_GRID_TRAINING_CACHE)
        if df.empty:
            print("No simulation results.")
            return
        print(f"\nTraining data saved → {_GRID_TRAINING_CACHE}  ({len(df):,} rows)")

    # ── Quick sanity summary ──────────────────────────────────────────────────
    print(f"\n{'═'*70}")
    print(f"  GRID TRAINING DATASET SUMMARY")
    print(f"{'═'*70}")
    print(f"  Rows:     {len(df):,}")
    print(f"  Tickers:  {df['ticker'].nunique()}")
    print(f"  Dates:    {df['edate'].min()} – {df['edate'].max()}")
    print(f"  Win rate: {df['win'].mean()*100:.1f}%")
    print(f"  Avg ROC:  {df['roc'].mean()*100:.2f}%")
    print(f"\n  Structure breakdown (avg ROC% by structure):")
    pivot = (
        df.groupby(["c_delta_tgt", "p_delta_tgt"])["roc"]
        .mean()
        .mul(100)
        .unstack("p_delta_tgt")
        .round(1)
    )
    print(pivot.to_string())
    print(f"\n  ROC% by DTE target:")
    for dte, g in df.groupby("dte_tgt"):
        print(f"    DTE {dte:>2}: N={len(g):>7,}  Win={g['win'].mean()*100:.1f}%  "
              f"AvgROC={g['roc'].mean()*100:.2f}%")


if __name__ == "__main__":
    main()
