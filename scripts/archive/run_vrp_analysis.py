#!/usr/bin/env python3
"""
VRP (Volatility Risk Premium) predictiveness analysis.

For each strategy entry in the backtest, computes VRP = IV30 - RV20 at entry and
correlates it with trade outcome (ROC, win/loss).

IV30  = implied vol of the ATM ~20-DTE option on the entry date (annualized, from BS)
RV20  = realized vol over the prior 20 trading days (annualized)
VRP   = IV30 - RV20  (positive = market paying excess premium → favours credit sellers)

Usage:
    PYTHONPATH=src python run_vrp_analysis.py --ticker TLT
    PYTHONPATH=src python run_vrp_analysis.py --ticker TLT --regime Bearish_HighIV
    PYTHONPATH=src python run_vrp_analysis.py --all

Requires: MYSQL_PASSWORD
"""
from __future__ import annotations

import argparse
import math
import pathlib
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from lib.mysql_lib import _get_engine
from lib.commons.bs import implied_vol as bs_iv

_CACHE_DIR = pathlib.Path(__file__).parent / "data" / "cache"

# ── Constants ─────────────────────────────────────────────────────────────────
PROFIT_TAKE   = 0.50
STOP_MULT     = 2.0
DTE_TARGET    = 20
DTE_TOL       = 5
MAX_DELTA_ERR = 0.08
MA_WINDOW     = 50
RV_WINDOW     = 20
VIX_HIGH      = 20.0
START_DATE    = date(2018, 1, 1)
END_DATE      = date(2026, 3, 14)

# ── Strategy registry ─────────────────────────────────────────────────────────
#
# Each entry:  name, ticker, dte, regimes dict
#   regimes key "*"            → applies to all regimes (no regime gate)
#   regimes key "Bearish_HighIV" etc → applies only in that regime
#
# Strategy tuple: (structure, cp, short_delta, long_delta)
#   structure: "bear_call_spread" | "bull_put_spread" | None (skip)
#   cp:        "C" | "P" | None  (None = skip / strangle handled separately)
#
STRATEGIES_CONFIG: list[dict] = [
    # ── Regime-switching ──────────────────────────────────────────────────────
    {
        "name": "TLT Bear Call", "ticker": "TLT", "dte": 20,
        "regimes": {
            "Bearish_HighIV": ("bear_call_spread", "C", 0.35, 0.25),
            "Bearish_LowIV":  (None, None, None, None),
            "Bullish_HighIV": (None, None, None, None),
            "Bullish_LowIV":  (None, None, None, None),
        },
    },
    {
        "name": "XLF Regime", "ticker": "XLF", "dte": 20,
        "regimes": {
            "Bearish_HighIV": ("bull_put_spread",  "P", 0.35, 0.25),
            "Bearish_LowIV":  (None, None, None, None),   # strangle — skip for now
            "Bullish_HighIV": (None, None, None, None),   # strangle — skip for now
            "Bullish_LowIV":  ("bear_call_spread", "C", 0.35, 0.25),
        },
    },
    {
        "name": "XLE Bull Put", "ticker": "XLE", "dte": 20,
        "regimes": {
            "Bearish_HighIV": ("bull_put_spread", "P", 0.35, 0.25),
            "Bearish_LowIV":  (None, None, None, None),
            "Bullish_HighIV": (None, None, None, None),
            "Bullish_LowIV":  (None, None, None, None),
        },
    },
    # ── All-regime credit spreads ─────────────────────────────────────────────
    {"name": "UVXY Bear Call", "ticker": "UVXY", "dte": 20,
     "regimes": {"*": ("bear_call_spread", "C", 0.50, 0.40)}},
    {"name": "TMF Bear Call",  "ticker": "TMF",  "dte": 20,
     "regimes": {"*": ("bear_call_spread", "C", 0.35, 0.25)}},
    {"name": "GLD Bull Put",   "ticker": "GLD",  "dte": 20,
     "regimes": {"*": ("bull_put_spread",  "P", 0.30, 0.20)}},
    {"name": "SOXX Bull Put",  "ticker": "SOXX", "dte": 20,
     "regimes": {"*": ("bull_put_spread",  "P", 0.35, 0.25)}},
    {"name": "SQQQ Bear Call", "ticker": "SQQQ", "dte": 20,
     "regimes": {"*": ("bear_call_spread", "C", 0.50, 0.40)}},
    {"name": "ASHR Bull Put",  "ticker": "ASHR", "dte": 20,
     "regimes": {"*": ("bull_put_spread",  "P", 0.25, 0.15)}},
    {"name": "ASHR Bear Call", "ticker": "ASHR", "dte": 20,
     "regimes": {"*": ("bear_call_spread", "C", 0.20, 0.10)}},
    {"name": "INDA Bull Put",  "ticker": "INDA", "dte": 20,
     "regimes": {"*": ("bull_put_spread",  "P", 0.25, 0.15)}},
    {"name": "USO Bull Put",   "ticker": "USO",  "dte": 30,
     "regimes": {"*": ("bull_put_spread",  "P", 0.25, 0.15)}},
    {"name": "BJ Bull Put",    "ticker": "BJ",   "dte": 45,
     "regimes": {"*": ("bull_put_spread",  "P", 0.20, 0.10)}},
    {"name": "GEV Bull Put",   "ticker": "GEV",  "dte": 20,
     "regimes": {"*": ("bull_put_spread",  "P", 0.25, 0.15)}},
    {"name": "CLS Bull Put",   "ticker": "CLS",  "dte": 20,
     "regimes": {"*": ("bull_put_spread",  "P", 0.25, 0.15)}},
]

STRATEGY_MAP: dict[str, dict] = {s["name"]: s for s in STRATEGIES_CONFIG}

# ── Data loading ──────────────────────────────────────────────────────────────

def load_options(ticker: str) -> pd.DataFrame:
    sql = f"""
        SELECT trade_date, expiry, cp, strike, bid, ask, mid, delta
        FROM options_cache
        WHERE ticker = '{ticker}'
          AND trade_date >= '{START_DATE}'
          AND trade_date <= '{END_DATE}'
          AND mid > 0 AND delta <> 0
        ORDER BY trade_date, expiry, strike
    """
    df = pd.read_sql(sql, _get_engine())
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    df["strike"]     = df["strike"].astype(float)
    df["mid"]        = df["mid"].astype(float)
    df["delta"]      = df["delta"].abs().astype(float)
    df["dte"]        = (df["expiry"] - df["trade_date"]).apply(lambda d: d.days)
    return df


def load_stock(ticker: str) -> pd.DataFrame:
    path = _CACHE_DIR / f"{ticker}_stock.parquet"
    df   = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    return df.sort_values("trade_date").reset_index(drop=True)


def load_vix() -> dict[date, float]:
    path = _CACHE_DIR / "vix_daily.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    col = "vix_close" if "vix_close" in df.columns else "close"
    return dict(zip(df["trade_date"], df[col].astype(float)))


# ── Regime + RV20 ─────────────────────────────────────────────────────────────

def build_regime_map(
    stock_df: pd.DataFrame,
    vix_map:  dict[date, float],
) -> dict[date, dict]:
    closes = stock_df["close"].astype(float).values
    dates  = stock_df["trade_date"].values
    result: dict[date, dict] = {}
    for i, d in enumerate(dates):
        if i < RV_WINDOW:
            continue
        close = closes[i]
        ma50  = closes[max(0, i - MA_WINDOW + 1):i + 1].mean()
        vix   = vix_map.get(d, float("nan"))

        window_closes = closes[i - RV_WINDOW:i + 1]
        log_rets = np.diff(np.log(window_closes))
        rv20 = float(np.std(log_rets, ddof=1) * math.sqrt(252))

        direction = "Bullish" if close > ma50 else "Bearish"
        iv_label  = "HighIV"  if (not math.isnan(vix) and vix >= VIX_HIGH) else "LowIV"
        result[d] = dict(
            regime = f"{direction}_{iv_label}",
            vix    = vix,
            rv20   = rv20,
            close  = close,
            ma50   = ma50,
        )
    return result


# ── IV computation ────────────────────────────────────────────────────────────

def compute_atm_iv(
    opts:     pd.DataFrame,
    spot:     float,
    cp:       str = "C",
    dte_tgt:  int = DTE_TARGET,
) -> Optional[float]:
    window = opts[
        (opts["cp"] == cp) &
        (opts["dte"] >= dte_tgt - DTE_TOL) &
        (opts["dte"] <= dte_tgt + DTE_TOL)
    ]
    if window.empty:
        alt = "P" if cp == "C" else "C"
        window = opts[
            (opts["cp"] == alt) &
            (opts["dte"] >= dte_tgt - DTE_TOL) &
            (opts["dte"] <= dte_tgt + DTE_TOL)
        ]
        if window.empty:
            return None

    best_exp = window.iloc[(window["dte"] - dte_tgt).abs().argsort()].iloc[0]["expiry"]
    atm_opts = window[window["expiry"] == best_exp].copy()
    atm_opts["_ddist"] = (atm_opts["delta"] - 0.50).abs()
    best = atm_opts.loc[atm_opts["_ddist"].idxmin()]

    mid = float(best["mid"])
    K   = float(best["strike"])
    T   = float(best["dte"]) / 365.0
    if mid <= 0 or T <= 0:
        return None

    opt_type = "call" if best["cp"] == "C" else "put"
    try:
        iv = bs_iv(price=mid, S=spot, K=K, T=T, r=0.04, q=0.0, opt_type=opt_type)
        return iv
    except Exception:
        return None


# ── Simulation helpers ────────────────────────────────────────────────────────

def find_option(
    opts: pd.DataFrame,
    cp: str,
    target_delta: float,
    expiry: Optional[date] = None,
    dte_tgt: int = DTE_TARGET,
) -> Optional[pd.Series]:
    subset = opts[opts["cp"] == cp]
    if expiry is not None:
        subset = subset[subset["expiry"] == expiry]
    else:
        window = subset[
            (subset["dte"] >= dte_tgt - DTE_TOL) &
            (subset["dte"] <= dte_tgt + DTE_TOL)
        ]
        if window.empty:
            return None
        best_exp = window.iloc[(window["dte"] - dte_tgt).abs().argsort()[:1]]["expiry"].iloc[0]
        subset = subset[subset["expiry"] == best_exp]
    subset = subset.copy()
    subset["_derr"] = (subset["delta"] - target_delta).abs()
    subset = subset[subset["_derr"] <= MAX_DELTA_ERR]
    if subset.empty:
        return None
    return subset.loc[subset["_derr"].idxmin()]


def sim_credit_spread(
    entry_date:   date,
    expiry:       date,
    short_strike: float,
    long_strike:  float,
    cp:           str,
    credit:       float,
    daily_map:    dict,
    stock_map:    dict[date, float],
) -> dict:
    take = credit * (1.0 - PROFIT_TAKE)
    stop = credit * STOP_MULT
    cur  = entry_date + timedelta(days=1)
    while cur <= expiry:
        s = daily_map.get((cur, expiry, short_strike))
        l = daily_map.get((cur, expiry, long_strike))
        if s is not None and l is not None:
            val = s - l
            if val <= take:
                return dict(pnl=credit - val, exit="profit_take",
                            days=(cur - entry_date).days, exit_date=cur)
            if val >= stop:
                return dict(pnl=credit - val, exit="stop_loss",
                            days=(cur - entry_date).days, exit_date=cur)
        if cur >= expiry:
            spot = stock_map.get(expiry) or stock_map.get(cur, short_strike)
            si = max(0.0, spot - short_strike) if cp == "C" else max(0.0, short_strike - spot)
            li = max(0.0, spot - long_strike)  if cp == "C" else max(0.0, long_strike - spot)
            pnl = credit - (si - li)
            return dict(pnl=pnl, exit="expiry_win" if pnl >= 0 else "expiry_loss",
                        days=(expiry - entry_date).days, exit_date=expiry)
        cur += timedelta(days=1)
    spot = stock_map.get(expiry, short_strike)
    si = max(0.0, spot - short_strike) if cp == "C" else max(0.0, short_strike - spot)
    li = max(0.0, spot - long_strike)  if cp == "C" else max(0.0, long_strike - spot)
    pnl = credit - (si - li)
    return dict(pnl=pnl, exit="expiry_win" if pnl >= 0 else "expiry_loss",
                days=(expiry - entry_date).days, exit_date=expiry)


# ── Record builder (shared between single and --all modes) ────────────────────

def build_records(
    cfg:         dict,
    opts_df:     pd.DataFrame,
    regime_map:  dict[date, dict],
    stock_map:   dict[date, float],
    filter_regime: Optional[str] = None,
) -> list[dict]:
    dte_tgt     = cfg.get("dte", DTE_TARGET)
    regime_strats = cfg["regimes"]
    cp_map      = {"C": "C", "P": "P"}

    daily_map_c = {
        (r.trade_date, r.expiry, r.strike): r.mid
        for r in opts_df[opts_df["cp"] == "C"].itertuples(index=False)
    }
    daily_map_p = {
        (r.trade_date, r.expiry, r.strike): r.mid
        for r in opts_df[opts_df["cp"] == "P"].itertuples(index=False)
    }

    records = []
    fridays = sorted(
        d for d in regime_map
        if date.fromisoformat(str(d)).weekday() == 4
        and START_DATE <= date.fromisoformat(str(d)) <= END_DATE
    )

    for edate in fridays:
        info   = regime_map[edate]
        regime = info["regime"]

        if filter_regime and regime != filter_regime:
            continue

        # Resolve strategy config: specific regime or "*" wildcard
        strat_cfg = regime_strats.get(regime) or regime_strats.get("*")
        if strat_cfg is None:
            continue
        structure, cp, short_d, long_d = strat_cfg
        if structure is None or cp is None:
            continue
        if structure not in ("bear_call_spread", "bull_put_spread"):
            continue

        day_opts = opts_df[opts_df["trade_date"] == edate]
        if day_opts.empty:
            continue

        spot = stock_map.get(edate)
        if spot is None:
            continue

        atm_iv = compute_atm_iv(day_opts, spot, cp=cp, dte_tgt=dte_tgt)
        rv20   = info["rv20"]
        if atm_iv is None or rv20 <= 0:
            continue

        vrp_diff  = (atm_iv - rv20) * 100
        vrp_ratio = atm_iv / rv20
        vrp_log   = math.log(atm_iv / rv20) * 100

        short_row = find_option(day_opts, cp, short_d, dte_tgt=dte_tgt)
        if short_row is None:
            continue
        long_row = find_option(day_opts, cp, long_d, expiry=short_row["expiry"], dte_tgt=dte_tgt)
        if long_row is None:
            continue
        if cp == "C" and long_row["strike"] <= short_row["strike"]:
            continue
        if cp == "P" and long_row["strike"] >= short_row["strike"]:
            continue

        credit = short_row["mid"] - long_row["mid"]
        if credit <= 0:
            continue

        daily_map = daily_map_c if cp == "C" else daily_map_p
        sim = sim_credit_spread(
            edate, short_row["expiry"],
            short_row["strike"], long_row["strike"],
            cp, credit, daily_map, stock_map,
        )

        spread_w = abs(long_row["strike"] - short_row["strike"])
        max_loss = spread_w - credit
        roc      = sim["pnl"] / max_loss if max_loss > 0 else float("nan")

        records.append(dict(
            edate     = edate,
            year      = edate.year,
            regime    = regime,
            vix       = info["vix"],
            iv30      = atm_iv,
            rv20      = rv20,
            vrp_diff  = vrp_diff,
            vrp_ratio = vrp_ratio,
            vrp_log   = vrp_log,
            credit    = credit,
            spread_w  = spread_w,
            pnl       = sim["pnl"],
            roc       = roc,
            roc_pct   = roc * 100,
            is_win    = sim["pnl"] > 0,
            exit_type = sim["exit"],
            days      = sim["days"],
        ))

    return records


# ── Summary stats for --all mode ──────────────────────────────────────────────

def summarize(records: list[dict]) -> Optional[dict]:
    if not records:
        return None
    df = pd.DataFrame(records)
    n  = len(df)
    r_diff  = df["vrp_diff"].corr(df["roc_pct"])
    r_ratio = df["vrp_ratio"].corr(df["roc_pct"])
    r_log   = df["vrp_log"].corr(df["roc_pct"])
    try:
        df["_q"] = pd.qcut(df["vrp_diff"], q=4, labels=["Q1","Q2","Q3","Q4"])
        q1_win = df[df["_q"]=="Q1"]["is_win"].mean() * 100
        q1_roc = df[df["_q"]=="Q1"]["roc_pct"].mean()
        q4_win = df[df["_q"]=="Q4"]["is_win"].mean() * 100
        q4_roc = df[df["_q"]=="Q4"]["roc_pct"].mean()
        q1_cutoff = df[df["_q"]=="Q1"]["vrp_diff"].max()
    except Exception:
        q1_win = q1_roc = q4_win = q4_roc = q1_cutoff = float("nan")
    return dict(
        n        = n,
        win_pct  = df["is_win"].mean() * 100,
        avg_roc  = df["roc_pct"].mean(),
        r_diff   = r_diff,
        r_ratio  = r_ratio,
        r_log    = r_log,
        q1_win   = q1_win,
        q1_roc   = q1_roc,
        q4_win   = q4_win,
        q4_roc   = q4_roc,
        q1_cutoff= q1_cutoff,
        q4_q1_roc_spread = q4_roc - q1_roc,
    )


# ── Single-ticker detail output ───────────────────────────────────────────────

def print_detail(cfg: dict, records: list[dict], filter_regime: Optional[str]) -> None:
    W   = 80
    BAR = "═" * W

    print(f"\n{BAR}")
    print(f"  VRP PREDICTIVENESS ANALYSIS  ·  {cfg['name']}")
    if filter_regime:
        print(f"  Regime filter: {filter_regime}")
    print(BAR)

    if not records:
        print("\n  No trades found for the specified filters.\n")
        return

    df = pd.DataFrame(records)
    n  = len(df)

    print(f"\n{'─'*W}")
    print(f"  OVERALL  ·  {n} trades  ·  regimes: {', '.join(sorted(df['regime'].unique()))}")
    print(f"{'─'*W}")
    print(f"  Win rate:     {df['is_win'].mean()*100:.1f}%")
    print(f"  Avg ROC:      {df['roc_pct'].mean():+.1f}%")
    print(f"  Avg IV30:     {df['iv30'].mean()*100:.1f}%")
    print(f"  Avg RV20:     {df['rv20'].mean()*100:.1f}%")
    print(f"  Avg VRP diff: {df['vrp_diff'].mean():+.2f} pp")
    print(f"  Avg VRP ratio:{df['vrp_ratio'].mean():+.4f}")

    # Metric comparison
    METRICS = [
        ("vrp_diff",  "IV−RV (pp)"),
        ("vrp_ratio", "IV/RV (ratio)"),
        ("vrp_log",   "ln(IV/RV)×100"),
    ]
    print(f"\n{'─'*W}")
    print(f"  METRIC COMPARISON  ·  Pearson r with ROC + quartile stats")
    print(f"{'─'*W}")
    print(f"  {'Metric':<18}  {'r→ROC':>7}  {'r→win':>7}  "
          f"{'Q1 win%':>8}  {'Q1 ROC':>8}  {'Q4 win%':>8}  {'Q4 ROC':>8}  {'Best?':>6}")
    print(f"  {'─'*17}  {'─'*7}  {'─'*7}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*6}")

    best_col = max(METRICS, key=lambda m: abs(df[m[0]].corr(df["roc_pct"])))[0]
    for col, label in METRICS:
        r_roc = df[col].corr(df["roc_pct"])
        r_win = df[col].corr(df["is_win"].astype(float))
        try:
            df[f"_q_{col}"] = pd.qcut(df[col], q=4, labels=["Q1","Q2","Q3","Q4"])
            q1 = df[df[f"_q_{col}"] == "Q1"]
            q4 = df[df[f"_q_{col}"] == "Q4"]
            q1_win = q1["is_win"].mean() * 100
            q1_roc = q1["roc_pct"].mean()
            q4_win = q4["is_win"].mean() * 100
            q4_roc = q4["roc_pct"].mean()
        except Exception:
            q1_win = q1_roc = q4_win = q4_roc = float("nan")
        star = "★" if col == best_col else ""
        print(f"  {label:<18}  {r_roc:>+7.3f}  {r_win:>+7.3f}  "
              f"{q1_win:>7.1f}%  {q1_roc:>+7.1f}%  "
              f"{q4_win:>7.1f}%  {q4_roc:>+7.1f}%  {star:>6}")

    print(f"  {'─'*17}  {'─'*7}")
    for col, label in [("iv30","IV30 alone"),("rv20","RV20 alone"),("vix","VIX alone")]:
        print(f"  {label:<18}  {df[col].corr(df['roc_pct']):>+7.3f}  (reference)")

    # Per-metric detail (quartile + threshold scan) using vrp_diff
    col = "vrp_diff"
    q_col = f"_q_{col}"
    print(f"\n{'─'*W}")
    print(f"  IV−RV QUARTILE DETAIL")
    print(f"{'─'*W}")
    try:
        print(f"  {'Quartile':<10}  {'N':>4}  {'VRP range':>22}  {'Win%':>7}  {'Avg ROC':>9}")
        for q_label, q_key in [("Q1 (low)","Q1"),("Q2","Q2"),("Q3","Q3"),("Q4 (high)","Q4")]:
            grp = df[df[q_col] == q_key]
            if grp.empty:
                continue
            lo, hi = grp[col].min(), grp[col].max()
            print(f"  {q_label:<10}  {len(grp):>4}  [{lo:+7.2f} to {hi:+7.2f}] pp  "
                  f"{grp['is_win'].mean()*100:>6.1f}%  {grp['roc_pct'].mean():>+8.1f}%")
    except Exception as e:
        print(f"  (Quartile failed: {e})")

    # Threshold scan
    sorted_vals = sorted(df[col].dropna())
    thresholds = sorted(set(
        round(sorted_vals[int(len(sorted_vals) * p)], 2)
        for p in [0.10, 0.25, 0.33, 0.50, 0.67]
    ))
    base_roc = df["roc_pct"].mean()
    print(f"\n  Threshold scan (enter only when IV−RV > cutoff):")
    print(f"  {'Cutoff':>8}  {'Kept':>5}  {'% kept':>7}  {'Win%':>7}  {'Avg ROC':>9}  {'vs all':>8}")
    for thr in thresholds:
        sub = df[df[col] > thr]
        if len(sub) < 5:
            continue
        print(f"  {thr:>+8.2f}  {len(sub):>5}  {len(sub)/n*100:>6.0f}%  "
              f"{sub['is_win'].mean()*100:>6.1f}%  {sub['roc_pct'].mean():>+8.1f}%  "
              f"{sub['roc_pct'].mean()-base_roc:>+7.1f}%")

    # Per-year
    print(f"\n{'─'*W}")
    print(f"  PER-YEAR BREAKDOWN")
    print(f"{'─'*W}")
    print(f"  {'Year':>4}  {'N':>4}  {'Avg IV-RV':>10}  {'Win%':>7}  {'Avg ROC':>9}  {'r→ROC':>7}")
    print(f"  {'─'*4}  {'─'*4}  {'─'*10}  {'─'*7}  {'─'*9}  {'─'*7}")
    for yr, grp in df.groupby("year"):
        yr_r = grp["vrp_diff"].corr(grp["roc_pct"]) if len(grp) >= 3 else float("nan")
        print(f"  {yr:>4}  {len(grp):>4}  "
              f"{grp['vrp_diff'].mean():>+9.2f}pp  "
              f"{grp['is_win'].mean()*100:>6.1f}%  "
              f"{grp['roc_pct'].mean():>+8.1f}%  "
              f"{yr_r:>+7.3f}")

    print(f"\n{BAR}\n")


# ── --all summary mode ────────────────────────────────────────────────────────

def run_all(vix_map: dict[date, float]) -> None:
    W   = 110
    BAR = "═" * W
    print(f"\n{BAR}")
    print(f"  VRP ANALYSIS  ·  ALL STRATEGIES  ·  IV−RV (pp)")
    print(BAR)
    print(f"\n  Loading data for each ticker...")

    # Cache loaded data per ticker to avoid re-fetching ASHR twice etc.
    opts_cache:     dict[str, pd.DataFrame] = {}
    stock_cache:    dict[str, pd.DataFrame] = {}
    regime_cache:   dict[str, dict]         = {}
    failed_tickers: set[str]                = set()

    rows = []
    for cfg in STRATEGIES_CONFIG:
        ticker = cfg["ticker"]
        name   = cfg["name"]
        print(f"    {name:<22} ({ticker})", end="", flush=True)

        if ticker in failed_tickers:
            print(f"  → SKIP (no data)")
            rows.append({"name": name, "ticker": ticker, "error": "no data"})
            continue

        try:
            if ticker not in opts_cache:
                opts_cache[ticker]   = load_options(ticker)
                stock_cache[ticker]  = load_stock(ticker)
                regime_cache[ticker] = build_regime_map(stock_cache[ticker], vix_map)
        except Exception as e:
            print(f"  → SKIP (data error: {e})")
            rows.append({"name": name, "ticker": ticker, "error": str(e)})
            failed_tickers.add(ticker)
            continue

        stock_map = dict(zip(
            stock_cache[ticker]["trade_date"],
            stock_cache[ticker]["close"].astype(float)
        ))
        records = build_records(cfg, opts_cache[ticker], regime_cache[ticker], stock_map)
        if not records:
            print(f"  → SKIP (no trades)")
            rows.append({"name": name, "ticker": ticker, "error": "no trades"})
            continue

        s = summarize(records)
        print(f"  → {s['n']} trades  r={s['r_diff']:+.3f}")
        rows.append({"name": name, "ticker": ticker, **s, "error": None})

    # Summary table
    ok = [r for r in rows if r.get("error") is None]
    if not ok:
        print("\n  No results to display.")
        return

    # Sort by abs(r_diff) descending — most predictive first
    ok.sort(key=lambda r: abs(r["r_diff"]), reverse=True)

    print(f"\n{BAR}")
    print(f"  SUMMARY TABLE  ·  sorted by |r(IV−RV → ROC)|")
    print(BAR)
    print(
        f"  {'Strategy':<22}  {'N':>4}  {'Win%':>6}  {'ROC%':>6}  "
        f"{'r(diff)':>8}  {'r(ratio)':>9}  {'r(log)':>7}  "
        f"{'Q1 ROC':>7}  {'Q4 ROC':>7}  {'Spread':>7}  {'Q1 cut':>7}  {'Signal?':>8}"
    )
    print(f"  {'─'*22}  {'─'*4}  {'─'*6}  {'─'*6}  "
          f"{'─'*8}  {'─'*9}  {'─'*7}  "
          f"{'─'*7}  {'─'*7}  {'─'*7}  {'─'*7}  {'─'*8}")

    for r in ok:
        signal = "★ YES" if abs(r["r_diff"]) >= 0.15 else "no"
        print(
            f"  {r['name']:<22}  {r['n']:>4}  {r['win_pct']:>5.1f}%  {r['avg_roc']:>+5.1f}%  "
            f"  {r['r_diff']:>+7.3f}  {r['r_ratio']:>+8.3f}  {r['r_log']:>+6.3f}  "
            f"  {r['q1_roc']:>+6.1f}%  {r['q4_roc']:>+6.1f}%  "
            f"{r['q4_q1_roc_spread']:>+6.1f}pp  {r['q1_cutoff']:>+7.2f}  {signal:>8}"
        )

    skipped = [r for r in rows if r.get("error")]
    if skipped:
        print(f"\n  Skipped: {', '.join(r['name'] for r in skipped)}")

    print(f"\n{BAR}")
    print(f"  Signal = |r| ≥ 0.15.  Q1 cut = upper bound of lowest VRP quartile.")
    print(f"  For strategies with a signal, consider adding a VRP ≥ Q1_cut filter.")
    print(f"{BAR}\n")


# ── Entry points ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="VRP predictiveness analysis for credit spread strategies",
    )
    parser.add_argument("--ticker",  default=None, help="Ticker or strategy name (e.g. TLT, 'SOXX Bull Put')")
    parser.add_argument("--regime",  default=None, help="Filter to a single regime (optional)")
    parser.add_argument("--all",     action="store_true", help="Run summary for all strategies")
    args = parser.parse_args()

    vix_map = load_vix()

    if args.all:
        run_all(vix_map)
        return

    # Single-strategy mode
    ticker_or_name = args.ticker or "TLT"

    # Match by name first, then by ticker (first match)
    cfg = STRATEGY_MAP.get(ticker_or_name)
    if cfg is None:
        cfg = next((s for s in STRATEGIES_CONFIG if s["ticker"] == ticker_or_name), None)
    if cfg is None:
        print(f"ERROR: no strategy found for '{ticker_or_name}'")
        print(f"Available: {[s['name'] for s in STRATEGIES_CONFIG]}")
        return

    ticker = cfg["ticker"]
    try:
        opts_df  = load_options(ticker)
        stock_df = load_stock(ticker)
    except Exception as e:
        print(f"ERROR loading data for {ticker}: {e}")
        return

    print(f"\nLoading data...")
    print(f"  Options rows: {len(opts_df):,}  |  Stock rows: {len(stock_df):,}")

    regime_map = build_regime_map(stock_df, vix_map)
    stock_map  = dict(zip(stock_df["trade_date"], stock_df["close"].astype(float)))

    records = build_records(cfg, opts_df, regime_map, stock_map, filter_regime=args.regime)
    print_detail(cfg, records, args.regime)


if __name__ == "__main__":
    main()
