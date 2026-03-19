#!/usr/bin/env python3
"""
TLT Per-Regime Structure Sweep

For each of the four regimes, tests every combination of:
  structure  : bear_call_spread, bull_put_spread
  short_delta: 0.20 … 0.45 (step 0.05)
  wing       : 0.10 (long_delta = short_delta - 0.10)

Plus benchmark rows for the current strangle and long-straddle assignments.

ROC = pnl / capital-at-risk, where capital-at-risk uses:
  - Spreads:   spread_width - credit  (max loss)
  - Strangles: Reg T BPR  (CBOE uncovered formula, larger side)
  - Straddle:  debit paid

Loads from parquet cache (built by run_tlt_regime_switch.py).

Usage:
  PYTHONPATH=src python run_tlt_structure_sweep.py [--ticker TLT]
"""
from __future__ import annotations

import argparse
import math
import pathlib
from datetime import date, timedelta
from typing import Optional

import pandas as pd

_CACHE_DIR = pathlib.Path(__file__).parent / "data" / "cache"

# ── Constants ─────────────────────────────────────────────────────────────────
DTE_TARGET    = 20
DTE_TOL       = 5
MAX_DELTA_ERR = 0.08
MA_WINDOW     = 50
RV_WINDOW     = 20
VIX_HIGH      = 20.0
PROFIT_TAKE   = 0.50
STOP_MULT     = 2.0
LONG_TAKE_PCT = 0.50
LONG_STOP_PCT = 0.40

START_DATE = date(2018, 1, 1)
END_DATE   = date(2026, 3, 14)

SPREAD_SHORT_DELTAS = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45]
WING                = 0.10

REGIMES = ["Bearish_HighIV", "Bearish_LowIV", "Bullish_HighIV", "Bullish_LowIV"]


# ── Capital at risk (Reg T) ───────────────────────────────────────────────────

def reg_t_margin(
    structure:    str,
    underlying:   float,
    credit:       float,
    spread_width: float = 0.0,
    call_strike:  float = 0.0,
    put_strike:   float = 0.0,
    call_prem:    float = 0.0,
    put_prem:     float = 0.0,
) -> float:
    if structure in ("bear_call_spread", "bull_put_spread"):
        return max(spread_width - credit, 0.01)
    elif structure in ("short_strangle_sym", "short_strangle_skew"):
        otm_c  = max(0.0, call_strike - underlying)
        otm_p  = max(0.0, underlying  - put_strike)
        call_m = max(0.20 * underlying - otm_c + call_prem, 0.10 * underlying + call_prem)
        put_m  = max(0.20 * underlying - otm_p + put_prem,  0.10 * put_strike  + put_prem)
        return max(call_m, put_m)
    else:  # long_straddle
        return credit


# ── Data loading ──────────────────────────────────────────────────────────────

def load_options(ticker: str) -> pd.DataFrame:
    cache_path = _CACHE_DIR / f"{ticker}_options.parquet"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"No options parquet cache for {ticker}. "
            f"Run run_tlt_regime_switch.py --ticker {ticker} first."
        )
    df = pd.read_parquet(cache_path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    df["strike"]     = df["strike"].astype(float)
    df["mid"]        = df["mid"].astype(float)
    df["delta"]      = df["delta"].abs().astype(float)
    if "dte" not in df.columns:
        df["dte"] = (df["expiry"] - df["trade_date"]).apply(lambda d: d.days)
    return df


def load_stock(ticker: str) -> pd.DataFrame:
    path = _CACHE_DIR / f"{ticker}_stock.parquet"
    df   = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    return df.sort_values("trade_date").reset_index(drop=True)


def load_vix() -> dict[date, float]:
    path = _CACHE_DIR / "vix_daily.parquet"
    df   = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    col  = "vix_close" if "vix_close" in df.columns else df.columns[-1]
    return dict(zip(df["trade_date"], df[col].astype(float)))


# ── Regime ────────────────────────────────────────────────────────────────────

def build_regime_map(stock_df: pd.DataFrame, vix_map: dict) -> dict[date, str]:
    closes = stock_df["close"].astype(float).values
    dates  = stock_df["trade_date"].values
    regime: dict[date, str] = {}
    for i, d in enumerate(dates):
        if i < RV_WINDOW:
            continue
        close = closes[i]
        ma50  = closes[max(0, i - MA_WINDOW + 1):i + 1].mean()
        vix   = vix_map.get(d, float("nan"))
        direction = "Bullish" if close > ma50 else "Bearish"
        iv_label  = "HighIV"  if (not math.isnan(vix) and vix >= VIX_HIGH) else "LowIV"
        regime[d] = f"{direction}_{iv_label}"
    return regime


# ── Option lookup ─────────────────────────────────────────────────────────────

def find_option(
    opts: pd.DataFrame,
    cp: str,
    target_delta: float,
    expiry: Optional[date] = None,
) -> Optional[pd.Series]:
    subset = opts[opts["cp"] == cp]
    if expiry is not None:
        subset = subset[subset["expiry"] == expiry]
    else:
        window = subset[
            (subset["dte"] >= DTE_TARGET - DTE_TOL) &
            (subset["dte"] <= DTE_TARGET + DTE_TOL)
        ]
        if window.empty:
            return None
        best_exp = (window.iloc[(window["dte"] - DTE_TARGET).abs().argsort()[:1]]
                    ["expiry"].iloc[0])
        subset = subset[subset["expiry"] == best_exp]
    subset = subset.copy()
    subset["_derr"] = (subset["delta"] - target_delta).abs()
    subset = subset[subset["_derr"] <= MAX_DELTA_ERR]
    if subset.empty:
        return None
    return subset.loc[subset["_derr"].idxmin()]


# ── Simulation ────────────────────────────────────────────────────────────────

def sim_credit_spread(
    entry_date: date, expiry: date,
    short_strike: float, long_strike: float,
    cp: str, credit: float,
    daily_map: dict, stock_map: dict,
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
                            days=(cur - entry_date).days)
            if val >= stop:
                return dict(pnl=credit - val, exit="stop_loss",
                            days=(cur - entry_date).days)
        if cur >= expiry:
            spot = stock_map.get(expiry) or stock_map.get(cur, short_strike)
            si = max(0.0, spot - short_strike) if cp == "C" else max(0.0, short_strike - spot)
            li = max(0.0, spot - long_strike)  if cp == "C" else max(0.0, long_strike - spot)
            pnl = credit - (si - li)
            return dict(pnl=pnl, exit="expiry", days=(expiry - entry_date).days)
        cur += timedelta(days=1)
    spot = stock_map.get(expiry, short_strike)
    si = max(0.0, spot - short_strike) if cp == "C" else max(0.0, short_strike - spot)
    li = max(0.0, spot - long_strike)  if cp == "C" else max(0.0, long_strike - spot)
    return dict(pnl=credit - (si - li), exit="expiry", days=(expiry - entry_date).days)


def sim_strangle(
    entry_date: date, expiry: date,
    call_strike: float, put_strike: float,
    credit: float, is_short: bool,
    daily_map_c: dict, daily_map_p: dict, stock_map: dict,
) -> dict:
    if is_short:
        take = credit * (1.0 - PROFIT_TAKE)
        stop = credit * STOP_MULT
    else:
        take = credit * (1.0 + LONG_TAKE_PCT)
        stop = credit * (1.0 - LONG_STOP_PCT)
    cur = entry_date + timedelta(days=1)
    while cur <= expiry:
        c = daily_map_c.get((cur, expiry, call_strike))
        p = daily_map_p.get((cur, expiry, put_strike))
        if c is not None and p is not None:
            val = c + p
            if is_short:
                if val <= take:
                    return dict(pnl=credit - val, exit="profit_take",
                                days=(cur - entry_date).days)
                if val >= stop:
                    return dict(pnl=credit - val, exit="stop_loss",
                                days=(cur - entry_date).days)
            else:
                if val >= take:
                    return dict(pnl=val - credit, exit="profit_take",
                                days=(cur - entry_date).days)
                if val <= stop:
                    return dict(pnl=val - credit, exit="stop_loss",
                                days=(cur - entry_date).days)
        if cur >= expiry:
            spot   = stock_map.get(expiry) or stock_map.get(cur, call_strike)
            ci, pi = max(0.0, spot - call_strike), max(0.0, put_strike - spot)
            pnl    = (credit - ci - pi) if is_short else (ci + pi - credit)
            return dict(pnl=pnl, exit="expiry", days=(expiry - entry_date).days)
        cur += timedelta(days=1)
    spot   = stock_map.get(expiry, call_strike)
    ci, pi = max(0.0, spot - call_strike), max(0.0, put_strike - spot)
    return dict(pnl=(credit - ci - pi) if is_short else (ci + pi - credit),
                exit="expiry", days=(expiry - entry_date).days)


# ── Single-combo backtest ─────────────────────────────────────────────────────

def run_combo(
    structure: str,
    short_d:   float,
    long_d:    float,
    regime_dates: list[date],
    opts_by_date: dict,
    daily_map_c: dict,
    daily_map_p: dict,
    stock_map: dict,
) -> Optional[dict]:
    rows = []
    for edate in regime_dates:
        day_opts = opts_by_date.get(edate)
        if day_opts is None:
            continue
        underlying = stock_map.get(edate, 0.0)

        if structure == "bear_call_spread":
            sr = find_option(day_opts, "C", short_d)
            if sr is None:
                continue
            lr = find_option(day_opts, "C", long_d, expiry=sr["expiry"])
            if lr is None or lr["strike"] <= sr["strike"]:
                continue
            credit = sr["mid"] - lr["mid"]
            if credit <= 0:
                continue
            spread_width = lr["strike"] - sr["strike"]
            margin = reg_t_margin(structure, underlying, credit, spread_width=spread_width)
            sim = sim_credit_spread(edate, sr["expiry"], sr["strike"], lr["strike"],
                                    "C", credit, daily_map_c, stock_map)

        elif structure == "bull_put_spread":
            sr = find_option(day_opts, "P", short_d)
            if sr is None:
                continue
            lr = find_option(day_opts, "P", long_d, expiry=sr["expiry"])
            if lr is None or lr["strike"] >= sr["strike"]:
                continue
            credit = sr["mid"] - lr["mid"]
            if credit <= 0:
                continue
            spread_width = sr["strike"] - lr["strike"]
            margin = reg_t_margin(structure, underlying, credit, spread_width=spread_width)
            sim = sim_credit_spread(edate, sr["expiry"], sr["strike"], lr["strike"],
                                    "P", credit, daily_map_p, stock_map)

        elif structure in ("short_strangle_sym", "short_strangle_skew"):
            cr = find_option(day_opts, "C", short_d)
            if cr is None:
                continue
            pr = find_option(day_opts, "P", long_d, expiry=cr["expiry"])
            if pr is None or pr["strike"] > cr["strike"]:
                continue
            credit = cr["mid"] + pr["mid"]
            if credit <= 0:
                continue
            margin = reg_t_margin(structure, underlying, credit,
                                  call_strike=cr["strike"], put_strike=pr["strike"],
                                  call_prem=cr["mid"], put_prem=pr["mid"])
            sim = sim_strangle(edate, cr["expiry"], cr["strike"], pr["strike"],
                               credit, True, daily_map_c, daily_map_p, stock_map)

        elif structure == "long_straddle":
            cr = find_option(day_opts, "C", short_d)
            if cr is None:
                continue
            pr = find_option(day_opts, "P", long_d, expiry=cr["expiry"])
            if pr is None:
                continue
            cost   = cr["mid"] + pr["mid"]
            if cost <= 0:
                continue
            margin = reg_t_margin("long_straddle", underlying, cost)
            sim    = sim_strangle(edate, cr["expiry"], cr["strike"], pr["strike"],
                                  cost, False, daily_map_c, daily_map_p, stock_map)
            credit = cost
        else:
            continue

        rows.append(dict(pnl=sim["pnl"], margin=margin, credit=credit,
                         days=sim["days"], exit=sim["exit"]))

    if not rows:
        return None
    df    = pd.DataFrame(rows)
    n     = len(df)
    wins  = (df["pnl"] > 0).sum()
    avg_r = (df["pnl"] / df["margin"]).mean() * 100
    maxl  = df["pnl"].min()
    sump  = df["pnl"].sum()
    return dict(n=n, win_pct=wins/n*100, avg_roc=avg_r, max_loss=maxl, sum_pnl=sump)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="TLT")
    args   = parser.parse_args()
    ticker = args.ticker.upper()

    print(f"Loading {ticker} data from parquet cache...")
    opts     = load_options(ticker)
    stock_df = load_stock(ticker)
    vix_map  = load_vix()
    print(f"  {len(opts):,} option rows")

    stock_map   = dict(zip(stock_df["trade_date"], stock_df["close"].astype(float)))
    regime_map  = build_regime_map(stock_df, vix_map)

    calls = opts[opts["cp"] == "C"]
    puts  = opts[opts["cp"] == "P"]
    daily_map_c  = {(r.trade_date, r.expiry, r.strike): r.mid for r in calls.itertuples(index=False)}
    daily_map_p  = {(r.trade_date, r.expiry, r.strike): r.mid for r in puts.itertuples(index=False)}
    opts_by_date = {d: g for d, g in opts.groupby("trade_date")}

    entry_dates = [
        START_DATE + timedelta(days=i)
        for i in range((END_DATE - START_DATE).days + 1)
        if (START_DATE + timedelta(days=i)).weekday() == 4
    ]

    # Partition dates by regime
    regime_dates: dict[str, list[date]] = {r: [] for r in REGIMES}
    for edate in entry_dates:
        reg = regime_map.get(edate)
        if reg and reg in regime_dates:
            regime_dates[reg].append(edate)

    # Current strangle assignments (benchmark reference)
    CURRENT_STRANGLES = {
        "Bearish_LowIV":  ("short_strangle_sym",  0.25, 0.25),
        "Bullish_HighIV": ("short_strangle_skew",  0.45, 0.25),
    }
    CURRENT_SPREADS = {
        "Bearish_HighIV": ("bear_call_spread", 0.35, 0.25),
        "Bullish_LowIV":  ("long_straddle",    0.50, 0.50),
    }

    W = 44
    HDR = (f"  {'Structure':<22}  {'ShΔ':>5}  {'LgΔ':>5}  "
           f"{'N':>4}  {'Win%':>6}  {'ROC%':>7}  {'MaxLoss':>8}  {'SumPnL':>9}")

    for regime in REGIMES:
        rdates = regime_dates[regime]
        n_weeks = len(rdates)
        print(f"\n{'═'*W}")
        print(f"  {regime}  ·  {n_weeks} weeks")
        print(f"{'═'*W}")
        print(HDR)
        print(f"  {'─'*(W-2)}")

        results = []

        # Spread structures
        for structure in ("bear_call_spread", "bull_put_spread"):
            for sd in SPREAD_SHORT_DELTAS:
                ld = round(sd - WING, 2)
                if ld <= 0:
                    continue
                r = run_combo(structure, sd, ld, rdates, opts_by_date,
                              daily_map_c, daily_map_p, stock_map)
                if r:
                    results.append((structure, sd, ld, r))

        # Current strangle benchmark (if applicable)
        if regime in CURRENT_STRANGLES:
            st, sd, ld = CURRENT_STRANGLES[regime]
            r = run_combo(st, sd, ld, rdates, opts_by_date,
                          daily_map_c, daily_map_p, stock_map)
            if r:
                results.append((f"{st} ★current", sd, ld, r))

        # Current spread / straddle benchmark
        if regime in CURRENT_SPREADS:
            st, sd, ld = CURRENT_SPREADS[regime]
            r = run_combo(st, sd, ld, rdates, opts_by_date,
                          daily_map_c, daily_map_p, stock_map)
            if r:
                results.append((f"{st} ★current", sd, ld, r))

        # Sort by avg_roc descending
        results.sort(key=lambda x: x[3]["avg_roc"], reverse=True)

        for i, (structure, sd, ld, r) in enumerate(results):
            marker = " ◀ BEST" if i == 0 else ""
            name   = structure[:22]
            print(f"  {name:<22}  {sd:>5.2f}  {ld:>5.2f}  "
                  f"{r['n']:>4}  {r['win_pct']:>5.1f}%  {r['avg_roc']:>+7.2f}%  "
                  f"${r['max_loss']:>7.3f}  ${r['sum_pnl']:>8.3f}{marker}")

    print(f"\n{'═'*W}\n")


if __name__ == "__main__":
    main()
