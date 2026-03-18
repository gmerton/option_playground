#!/usr/bin/env python3
"""
TLT Short Strangle Study — Bearish_LowIV regime
(and optionally other regimes for comparison)

Sweeps call_delta × put_delta to find the optimal asymmetric strangle.
0.50/0.50 = symmetric ATM straddle (baseline).

Exit rules: 50% profit take, 2× stop loss.

Usage:
  PYTHONPATH=src python run_tlt_strangle_study.py [--regime LABEL]

  LABEL: Bearish_LowIV (default), Bearish_HighIV, Bullish_HighIV, Bullish_LowIV, ALL

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

_CACHE_DIR = pathlib.Path(__file__).parent / "data" / "cache"

# ── Config ────────────────────────────────────────────────────────────────────
CALL_DELTAS   = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
PUT_DELTAS    = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

DTE_TARGET    = 20
DTE_TOL       = 5
MAX_DELTA_ERR = 0.08
PROFIT_TAKE   = 0.50
STOP_MULT     = 2.0
MA_WINDOW     = 50
RV_WINDOW     = 20
VIX_HIGH      = 20

START_DATE    = date(2018, 1, 1)
END_DATE      = date(2026, 3, 14)


# ── Data loading ──────────────────────────────────────────────────────────────

def load_tlt_options() -> pd.DataFrame:
    sql = f"""
        SELECT trade_date, expiry, strike, mid, delta, cp
        FROM options_cache
        WHERE ticker = 'TLT'
          AND trade_date >= '{START_DATE}'
          AND trade_date <= '{END_DATE}'
          AND mid > 0
          AND delta <> 0
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


def load_stock() -> pd.DataFrame:
    path = _CACHE_DIR / "TLT_stock.parquet"
    df   = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    return df.sort_values("trade_date").reset_index(drop=True)


def load_vix() -> dict[date, float]:
    path = _CACHE_DIR / "vix_daily.parquet"
    if not path.exists():
        return {}
    df  = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    col = "vix_close" if "vix_close" in df.columns else (
          "close"     if "close"     in df.columns else df.columns[-1])
    return dict(zip(df["trade_date"], df[col].astype(float)))


# ── Regime ────────────────────────────────────────────────────────────────────

def build_regime_map(stock_df: pd.DataFrame, vix_map: dict[date, float]) -> dict[date, dict]:
    closes = stock_df["close"].astype(float).values
    dates  = stock_df["trade_date"].values
    regime: dict[date, dict] = {}
    for i, d in enumerate(dates):
        if i < RV_WINDOW:
            continue
        close = closes[i]
        ma50  = closes[max(0, i - MA_WINDOW + 1):i + 1].mean()
        roc20 = (close / closes[i - RV_WINDOW] - 1) * 100
        log_r = np.log(closes[i - RV_WINDOW + 1:i + 1] / closes[i - RV_WINDOW:i])
        rv20  = float(np.std(log_r) * math.sqrt(252) * 100)
        vix   = vix_map.get(d, float("nan"))
        direction = "Bullish" if close > ma50 else "Bearish"
        iv_label  = "HighIV" if (not math.isnan(vix) and vix >= VIX_HIGH) else "LowIV"
        regime[d] = dict(regime=f"{direction}_{iv_label}", vix=vix, roc20=roc20, rv20=rv20)
    return regime


# ── Entry selection ───────────────────────────────────────────────────────────

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
        best_exp = (
            window.iloc[(window["dte"] - DTE_TARGET).abs().argsort()[:1]]
            ["expiry"].iloc[0]
        )
        subset = subset[subset["expiry"] == best_exp]

    subset = subset.copy()
    subset["_derr"] = (subset["delta"] - target_delta).abs()
    subset = subset[subset["_derr"] <= MAX_DELTA_ERR]
    if subset.empty:
        return None
    return subset.loc[subset["_derr"].idxmin()]


# ── Simulation ────────────────────────────────────────────────────────────────

def sim_strangle(
    entry_date:   date,
    expiry:       date,
    call_strike:  float,
    put_strike:   float,
    entry_credit: float,
    daily_map_c:  dict,
    daily_map_p:  dict,
    stock_map:    dict[date, float],
) -> dict:
    take_target = entry_credit * (1.0 - PROFIT_TAKE)
    stop_level  = entry_credit * STOP_MULT

    cur = entry_date + timedelta(days=1)
    while cur <= expiry:
        c_mid = daily_map_c.get((cur, expiry, call_strike))
        p_mid = daily_map_p.get((cur, expiry, put_strike))

        if c_mid is not None and p_mid is not None:
            val = c_mid + p_mid
            if val <= take_target:
                return dict(pnl=entry_credit - val, exit="profit_take",
                            days=(cur - entry_date).days, exit_date=cur)
            if val >= stop_level:
                return dict(pnl=entry_credit - val, exit="stop_loss",
                            days=(cur - entry_date).days, exit_date=cur)

        if cur >= expiry:
            spot  = stock_map.get(expiry) or stock_map.get(cur, call_strike)
            c_int = max(0.0, spot - call_strike)
            p_int = max(0.0, put_strike - spot)
            pnl   = entry_credit - (c_int + p_int)
            etype = "expiry_win" if pnl >= 0 else "expiry_loss"
            return dict(pnl=pnl, exit=etype,
                        days=(expiry - entry_date).days, exit_date=expiry)

        cur += timedelta(days=1)

    spot  = stock_map.get(expiry, call_strike)
    c_int = max(0.0, spot - call_strike)
    p_int = max(0.0, put_strike - spot)
    pnl   = entry_credit - (c_int + p_int)
    return dict(pnl=pnl, exit="expiry_win" if pnl >= 0 else "expiry_loss",
                days=(expiry - entry_date).days, exit_date=expiry)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regime", default="Bearish_LowIV",
                        help="Regime filter (or ALL)")
    args = parser.parse_args()

    print("Loading TLT option data...")
    opts = load_tlt_options()
    print(f"  {len(opts):,} rows")

    stock_df  = load_stock()
    stock_map = dict(zip(stock_df["trade_date"], stock_df["close"].astype(float)))
    vix_map   = load_vix()
    regime_map = build_regime_map(stock_df, vix_map)

    calls = opts[opts["cp"] == "C"]
    puts  = opts[opts["cp"] == "P"]
    daily_map_c = {(r.trade_date, r.expiry, r.strike): r.mid for r in calls.itertuples(index=False)}
    daily_map_p = {(r.trade_date, r.expiry, r.strike): r.mid for r in puts.itertuples(index=False)}
    opts_by_date = {d: g for d, g in opts.groupby("trade_date")}

    entry_dates = [
        START_DATE + timedelta(days=i)
        for i in range((END_DATE - START_DATE).days + 1)
        if (START_DATE + timedelta(days=i)).weekday() == 4
    ]

    regime_filter = args.regime  # "ALL" = no filter

    results = []
    for edate in entry_dates:
        reg = regime_map.get(edate)
        if reg is None:
            continue
        if regime_filter != "ALL" and reg["regime"] != regime_filter:
            continue

        day_opts = opts_by_date.get(edate)
        if day_opts is None:
            continue

        for cd in CALL_DELTAS:
            call_row = find_option(day_opts, "C", cd)
            if call_row is None:
                continue

            for pd_ in PUT_DELTAS:
                put_row = find_option(day_opts, "P", pd_, expiry=call_row["expiry"])
                if put_row is None:
                    continue

                # For a strangle, put strike must be ≤ call strike
                # (if cd=pd_=0.50 they may be equal — that's the straddle)
                if put_row["strike"] > call_row["strike"]:
                    continue

                credit = call_row["mid"] + put_row["mid"]
                if credit <= 0:
                    continue

                sim = sim_strangle(
                    edate, call_row["expiry"],
                    call_row["strike"], put_row["strike"],
                    credit, daily_map_c, daily_map_p, stock_map,
                )
                results.append({
                    "call_delta": cd,
                    "put_delta":  pd_,
                    "edate":      edate,
                    "year":       edate.year,
                    "credit":     credit,
                    "call_strike": call_row["strike"],
                    "put_strike":  put_row["strike"],
                    **sim,
                    **reg,
                })

    df = pd.DataFrame(results)

    regime_lbl = regime_filter if regime_filter != "ALL" else "All regimes"
    print(f"\n{'═'*88}")
    print(f"  TLT SHORT STRANGLE SWEEP  ·  {regime_lbl}  ·  ~20 DTE  ·  50% take / 2× stop")
    print(f"  Rows: {len(df):,}   Entry dates: {df['edate'].nunique()}")
    print(f"{'═'*88}")

    # ── ROC matrix ───────────────────────────────────────────────────────────
    print("\n  AVG ROC% MATRIX  (rows = call_delta, cols = put_delta)\n")
    matrix_roc = (
        df.groupby(["call_delta", "put_delta"])
        .apply(lambda g: (g["pnl"] / g["credit"]).mean() * 100, include_groups=False)
        .unstack("put_delta")
    )
    header = "  CallΔ\\PutΔ" + "".join(f"   {c:.2f}" for c in matrix_roc.columns)
    print(header)
    print("  " + "─" * (len(header) - 2))
    for cd, row in matrix_roc.iterrows():
        vals = "".join(
            f" {'▶' if v == row.max() else ' '}{v:+5.1f}%" for v in row.values
        )
        print(f"    {cd:.2f}    {vals}")

    # ── SumPnL matrix ─────────────────────────────────────────────────────────
    print("\n  SUM PnL MATRIX  (rows = call_delta, cols = put_delta)\n")
    matrix_sum = (
        df.groupby(["call_delta", "put_delta"])["pnl"]
        .sum()
        .unstack("put_delta")
    )
    print(header)
    print("  " + "─" * (len(header) - 2))
    for cd, row in matrix_sum.iterrows():
        vals = "".join(
            f" {'▶' if v == row.max() else ' '}{v:+7.2f}" for v in row.values
        )
        print(f"    {cd:.2f}    {vals}")

    # ── Win% matrix ───────────────────────────────────────────────────────────
    print("\n  WIN% MATRIX  (rows = call_delta, cols = put_delta)\n")
    matrix_win = (
        df.groupby(["call_delta", "put_delta"])
        .apply(lambda g: (g["pnl"] > 0).mean() * 100, include_groups=False)
        .unstack("put_delta")
    )
    print(header)
    print("  " + "─" * (len(header) - 2))
    for cd, row in matrix_win.iterrows():
        vals = "".join(
            f" {'▶' if v == row.max() else ' '}{v:+5.1f}%" for v in row.values
        )
        print(f"    {cd:.2f}    {vals}")

    # ── Detailed table: top combos by avg ROC ────────────────────────────────
    print(f"\n  TOP 15 COMBINATIONS BY AVG ROC%\n")
    print(f"  {'CallΔ':>6}  {'PutΔ':>5}  {'N':>4}  {'Win%':>6}  {'AvgCr':>7}  "
          f"{'AvgPnL':>7}  {'ROC%':>6}  {'MaxLoss':>8}  {'SumPnL':>8}  {'Stops%':>6}")
    print("  " + "─" * 76)

    summary = (
        df.groupby(["call_delta", "put_delta"])
        .apply(lambda g: pd.Series({
            "n":        len(g),
            "win_pct":  (g["pnl"] > 0).mean() * 100,
            "avg_cr":   g["credit"].mean(),
            "avg_pnl":  g["pnl"].mean(),
            "avg_roc":  (g["pnl"] / g["credit"]).mean() * 100,
            "max_loss": g["pnl"].min(),
            "sum_pnl":  g["pnl"].sum(),
            "stop_pct": (g["exit"] == "stop_loss").mean() * 100,
        }), include_groups=False)
        .sort_values("avg_roc", ascending=False)
        .head(15)
    )
    for (cd, pd_), row in summary.iterrows():
        marker = " ◀ STRADDLE" if cd == 0.50 and pd_ == 0.50 else ""
        print(f"  {cd:>6.2f}  {pd_:>5.2f}  {row['n']:>4.0f}  {row['win_pct']:>5.1f}%  "
              f"${row['avg_cr']:>6.3f}  ${row['avg_pnl']:>6.3f}  {row['avg_roc']:>5.1f}%  "
              f"${row['max_loss']:>7.3f}  ${row['sum_pnl']:>7.3f}  {row['stop_pct']:>5.1f}%{marker}")

    # ── Per-year breakdown for top 3 + straddle baseline ─────────────────────
    # find top 3 by avg_roc that aren't the straddle
    top_combos = (
        df.groupby(["call_delta", "put_delta"])
        .apply(lambda g: (g["pnl"] / g["credit"]).mean() * 100, include_groups=False)
        .sort_values(ascending=False)
    )
    # always include straddle + top 3 non-straddle
    to_show = []
    for (cd, pd_) in top_combos.index:
        if (cd, pd_) not in to_show:
            to_show.append((cd, pd_))
        if len(to_show) >= 3:
            break
    if (0.50, 0.50) not in to_show:
        to_show.append((0.50, 0.50))

    print(f"\n{'═'*88}")
    print(f"  PER-YEAR BREAKDOWN  ·  Top combos + straddle baseline")
    print(f"{'═'*88}")

    for (cd, pd_) in to_show:
        sub = df[(df["call_delta"] == cd) & (df["put_delta"] == pd_)]
        label = f"CallΔ={cd:.2f} / PutΔ={pd_:.2f}" + (" (straddle)" if cd == 0.50 and pd_ == 0.50 else "")
        print(f"\n  {label}")
        print(f"  {'Year':>6}  {'N':>4}  {'Win%':>6}  {'AvgCr':>7}  {'AvgPnL':>7}  "
              f"{'ROC%':>6}  {'MaxLoss':>8}  {'SumPnL':>8}  {'Stops':>5}")
        print("  " + "─" * 66)
        for yr, grp in sub.groupby("year"):
            n   = len(grp)
            roc = (grp["pnl"] / grp["credit"]).mean() * 100
            print(f"  {yr:>6}  {n:>4}  {(grp['pnl']>0).mean()*100:>5.1f}%  "
                  f"${grp['credit'].mean():>6.3f}  ${grp['pnl'].mean():>6.3f}  "
                  f"{roc:>5.1f}%  ${grp['pnl'].min():>7.3f}  "
                  f"${grp['pnl'].sum():>7.3f}  {(grp['exit']=='stop_loss').sum():>5}")
        tot_roc = (sub["pnl"] / sub["credit"]).mean() * 100
        print(f"  {'TOTAL':>6}  {len(sub):>4}  {(sub['pnl']>0).mean()*100:>5.1f}%  "
              f"${sub['credit'].mean():>6.3f}  ${sub['pnl'].mean():>6.3f}  "
              f"{tot_roc:>5.1f}%  ${sub['pnl'].min():>7.3f}  "
              f"${sub['pnl'].sum():>7.3f}  {(sub['exit']=='stop_loss').sum():>5}")


if __name__ == "__main__":
    main()
