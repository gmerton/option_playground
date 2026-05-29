#!/usr/bin/env python3
"""
SPX Short Strangle Study — DTE sweep, 2016–2026

Queries Athena directly (SPX is too large for MySQL options_cache).
Caches results to data/cache/SPX_options_dteXX.parquet to avoid re-querying.

Exit rules: 50% profit take, 2× stop loss.

Usage:
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \\
    .venv/bin/python3 run_spx_strangle.py [--dte 20] [--refresh] [--vix-min 20]

  --dte       Target DTE: 7, 20 (default), or 45
  --refresh   Force re-query from Athena even if cache exists
  --regime    Bearish_LowIV | Bearish_HighIV | Bullish_HighIV | Bullish_LowIV | ALL (default)
  --vix-min   Only enter on days where VIX >= this threshold
  --vix-max   Only enter on days where VIX < this threshold
"""
from __future__ import annotations

import argparse
import math
import pathlib
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

_CACHE_DIR = pathlib.Path(__file__).parent / "data" / "cache"
_VIX_CACHE  = _CACHE_DIR / "vix_daily.parquet"

# ── Config ────────────────────────────────────────────────────────────────────
_ALL_DELTAS   = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
CALL_DELTAS   = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
PUT_DELTAS    = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

# DTE-specific settings: (dte_tol, dte_max_load)
_DTE_SETTINGS: dict[int, tuple[int, int]] = {
    7:  (2,  15),   # entry window 5–9, load up to 15 DTE
    10: (3,  15),   # entry window 7–13, load up to 15 DTE
    20: (5,  30),   # entry window 15–25, load up to 30 DTE
    45: (10, 60),   # entry window 35–55, load up to 60 DTE
}

DELTA_MIN     = 0.07     # load wider than sweep to give find_option some slack
DELTA_MAX     = 0.58
MAX_DELTA_ERR = 0.08     # max error when matching target delta at entry

PROFIT_TAKE   = 0.50
STOP_MULT     = 2.0      # default; overridden by --stop-mult (0 = no stop)
MA_WINDOW     = 50
MA_WINDOW_200 = 200
RV_WINDOW     = 20
VIX_HIGH      = 20

START_DATE    = date(2016, 1, 1)
END_DATE      = date(2026, 3, 21)


# ── Athena data pull ──────────────────────────────────────────────────────────

def pull_from_athena(dte_max_load: int) -> pd.DataFrame:
    """Query Athena for SPX options within the DTE/delta window."""
    from lib.athena_lib import athena

    print(f"Querying Athena for SPX options (DTE 0–{dte_max_load}, |delta| {DELTA_MIN}–{DELTA_MAX}) ...")
    sql = f"""
    SELECT
        trade_date,
        expiry,
        strike,
        CAST((bid + ask) / 2.0 AS DOUBLE) AS mid,
        CAST(delta AS DOUBLE)              AS delta,
        cp,
        date_diff('day', trade_date, expiry) AS dte
    FROM "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"
    WHERE ticker = 'SPX'
      AND trade_date >= TIMESTAMP '{START_DATE} 00:00:00'
      AND trade_date <= TIMESTAMP '{END_DATE} 23:59:59'
      AND bid > 0
      AND delta IS NOT NULL
      AND ABS(delta) BETWEEN {DELTA_MIN} AND {DELTA_MAX}
      AND date_diff('day', trade_date, expiry) BETWEEN 0 AND {dte_max_load}
    ORDER BY trade_date, expiry, cp, strike
    """
    df = athena(sql)
    print(f"  Athena returned {len(df):,} rows")
    return df


def load_options(dte_target: int, refresh: bool = False) -> pd.DataFrame:
    _, dte_max_load = _DTE_SETTINGS[dte_target]
    cache_file = _CACHE_DIR / f"SPX_options_dte{dte_max_load}.parquet"

    if not refresh and cache_file.exists():
        print(f"Loading SPX options from cache: {cache_file}")
        df = pd.read_parquet(cache_file)
        print(f"  {len(df):,} rows")
    else:
        df = pull_from_athena(dte_max_load)
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_file, index=False)
        print(f"  Cached to {cache_file}")

    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    df["strike"]     = df["strike"].astype(float)
    df["mid"]        = df["mid"].astype(float)
    df["delta"]      = df["delta"].abs().astype(float)
    df["dte"]        = df["dte"].astype(int)
    return df


# ── Spot price for SPX (yfinance) ─────────────────────────────────────────────

def load_spot() -> dict[date, float]:
    """Load SPX daily closes via yfinance (^GSPC)."""
    import yfinance as yf
    print("Downloading SPX spot prices from yfinance ...")
    raw = yf.download("^GSPC", start=str(START_DATE), end=str(END_DATE + timedelta(days=5)),
                      progress=False, auto_adjust=True)
    raw.index = pd.to_datetime(raw.index).date
    closes = raw["Close"].squeeze()
    print(f"  {len(closes)} trading days")
    return dict(zip(closes.index, closes.values.astype(float)))


# ── VIX ───────────────────────────────────────────────────────────────────────

def load_vix() -> dict[date, float]:
    if _VIX_CACHE.exists():
        df = pd.read_parquet(_VIX_CACHE)
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
        col = "vix_close" if "vix_close" in df.columns else (
              "close"     if "close"     in df.columns else df.columns[-1])
        return dict(zip(df["trade_date"], df[col].astype(float)))
    # fallback: yfinance
    import yfinance as yf
    print("Downloading VIX from yfinance ...")
    raw = yf.download("^VIX", start=str(START_DATE), end=str(END_DATE + timedelta(days=5)),
                      progress=False, auto_adjust=True)
    raw.index = pd.to_datetime(raw.index).date
    closes = raw["Close"].squeeze()
    return dict(zip(closes.index, closes.values.astype(float)))


# ── Regime ────────────────────────────────────────────────────────────────────

def build_regime_map(spot_map: dict[date, float],
                     vix_map:  dict[date, float]) -> dict[date, dict]:
    dates  = sorted(spot_map.keys())
    closes = [spot_map[d] for d in dates]
    arr    = np.array(closes, dtype=float)
    regime: dict[date, dict] = {}
    for i, d in enumerate(dates):
        if i < RV_WINDOW:
            continue
        close  = arr[i]
        ma50   = arr[max(0, i - MA_WINDOW + 1):i + 1].mean()
        ma200  = arr[max(0, i - MA_WINDOW_200 + 1):i + 1].mean()
        log_r  = np.log(arr[i - RV_WINDOW + 1:i + 1] / arr[i - RV_WINDOW:i])
        rv20   = float(np.std(log_r) * math.sqrt(252) * 100)
        vix    = vix_map.get(d, float("nan"))
        direction = "Bullish" if close > ma50 else "Bearish"
        iv_label  = "HighIV" if (not math.isnan(vix) and vix >= VIX_HIGH) else "LowIV"
        above_200 = close > ma200
        regime[d] = dict(regime=f"{direction}_{iv_label}", vix=vix, rv20=rv20,
                         above_200ma=above_200)
    return regime


# ── Entry selection ───────────────────────────────────────────────────────────

def find_option(
    opts: pd.DataFrame,
    cp: str,
    target_delta: float,
    dte_target: int,
    dte_tol: int,
    expiry: Optional[date] = None,
) -> Optional[pd.Series]:
    subset = opts[opts["cp"] == cp]
    if expiry is not None:
        subset = subset[subset["expiry"] == expiry]
    else:
        window = subset[
            (subset["dte"] >= dte_target - dte_tol) &
            (subset["dte"] <= dte_target + dte_tol)
        ]
        if window.empty:
            return None
        best_exp = (
            window.iloc[(window["dte"] - dte_target).abs().argsort()[:1]]
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
    entry_date:       date,
    expiry:           date,
    call_strike:      float,
    put_strike:       float,
    entry_credit:     float,
    daily_map_c:      dict,
    daily_map_p:      dict,
    spot_map:         dict[date, float],
    stop_mult:        float = STOP_MULT,
    call_wing_strike: Optional[float] = None,
    put_wing_strike:  Optional[float] = None,
) -> dict:
    take_target = entry_credit * (1.0 - PROFIT_TAKE)
    stop_level  = entry_credit * stop_mult if stop_mult > 0 else float("inf")

    cur = entry_date + timedelta(days=1)
    while cur <= expiry:
        c_mid = daily_map_c.get((cur, expiry, call_strike))
        p_mid = daily_map_p.get((cur, expiry, put_strike))

        if c_mid is not None and p_mid is not None:
            net_val = c_mid + p_mid
            if call_wing_strike is not None:
                cw = daily_map_c.get((cur, expiry, call_wing_strike), 0.0)
                pw = daily_map_p.get((cur, expiry, put_wing_strike), 0.0)
                net_val -= (cw + pw)
            if net_val <= take_target:
                return dict(pnl=entry_credit - net_val, exit="profit_take",
                            days=(cur - entry_date).days, exit_date=cur)
            if net_val >= stop_level:
                return dict(pnl=entry_credit - net_val, exit="stop_loss",
                            days=(cur - entry_date).days, exit_date=cur)

        if cur >= expiry:
            spot  = spot_map.get(expiry) or spot_map.get(cur, call_strike)
            c_int = max(0.0, spot - call_strike)
            p_int = max(0.0, put_strike - spot)
            if call_wing_strike is not None:
                c_int = min(c_int, call_wing_strike - call_strike)
                p_int = min(p_int, put_strike - put_wing_strike)
            pnl   = entry_credit - (c_int + p_int)
            etype = "expiry_win" if pnl >= 0 else "expiry_loss"
            return dict(pnl=pnl, exit=etype,
                        days=(expiry - entry_date).days, exit_date=expiry)

        cur += timedelta(days=1)

    spot  = spot_map.get(expiry, call_strike)
    c_int = max(0.0, spot - call_strike)
    p_int = max(0.0, put_strike - spot)
    if call_wing_strike is not None:
        c_int = min(c_int, call_wing_strike - call_strike)
        p_int = min(p_int, put_strike - put_wing_strike)
    pnl   = entry_credit - (c_int + p_int)
    return dict(pnl=pnl, exit="expiry_win" if pnl >= 0 else "expiry_loss",
                days=(expiry - entry_date).days, exit_date=expiry)


# ── Reporting ─────────────────────────────────────────────────────────────────

def print_matrix(df: pd.DataFrame, metric_col: str, title: str, fmt: str,
                 suffix: str = "") -> None:
    matrix = (
        df.groupby(["call_delta", "put_delta"])
        .apply(
            lambda g: (g["pnl"] / g["max_loss"]).mean() * 100
            if metric_col == "roc"
            else (g["pnl"] > 0).mean() * 100
            if metric_col == "win"
            else g["pnl"].sum(),
            include_groups=False,
        )
        .unstack("put_delta")
    )
    print(f"\n  {title}\n")
    header = "  CallΔ\\PutΔ" + "".join(f"   {c:.2f}" for c in matrix.columns)
    print(header)
    print("  " + "─" * (len(header) - 2))
    for cd, row in matrix.iterrows():
        vals = "".join(
            f" {'▶' if v == row.max() else ' '}{v:{fmt}}{suffix}" for v in row.values
        )
        print(f"    {cd:.2f}    {vals}")


def print_results(df: pd.DataFrame, ticker: str, regime_lbl: str) -> None:
    sep = "═" * 92
    print(f"\n{sep}")
    print(f"  {ticker} SHORT STRANGLE SWEEP  ·  {regime_lbl}")
    print(f"  Rows: {len(df):,}   Entry dates: {df['edate'].nunique()}")
    print(sep)

    print_matrix(df, "roc",   "AVG ROC% MATRIX  (rows=CallΔ, cols=PutΔ)", "+5.1f", "%")
    print_matrix(df, "win",   "WIN% MATRIX",                               "+5.1f", "%")
    print_matrix(df, "sumpnl","SUM PnL MATRIX ($/share)",                  "+7.2f")

    # ── Top 15 by avg ROC ─────────────────────────────────────────────────────
    print(f"\n  TOP 15 COMBINATIONS BY AVG ROC%\n")
    print(f"  {'CallΔ':>6}  {'PutΔ':>5}  {'N':>4}  {'Win%':>6}  {'AvgCr':>7}  "
          f"{'AvgPnL':>8}  {'ROC%':>6}  {'AnnROC%':>8}  {'AvgDays':>8}  {'Stops%':>6}")
    print("  " + "─" * 84)

    summary = (
        df.groupby(["call_delta", "put_delta"])
        .apply(lambda g: pd.Series({
            "n":        len(g),
            "win_pct":  (g["pnl"] > 0).mean() * 100,
            "avg_cr":   g["credit"].mean(),
            "avg_pnl":  g["pnl"].mean(),
            "avg_roc":  (g["pnl"] / g["max_loss"]).mean() * 100,
            "ann_roc":  ((g["pnl"] / g["max_loss"]) * (365 / g["days"])).mean() * 100,
            "avg_days": g["days"].mean(),
            "stop_pct": (g["exit"] == "stop_loss").mean() * 100,
        }), include_groups=False)
        .sort_values("avg_roc", ascending=False)
        .head(15)
    )
    for (cd, pd_), row in summary.iterrows():
        marker = " ◀ STRADDLE" if cd == 0.50 and pd_ == 0.50 else ""
        print(f"  {cd:>6.2f}  {pd_:>5.2f}  {row['n']:>4.0f}  {row['win_pct']:>5.1f}%  "
              f"${row['avg_cr']:>6.2f}  ${row['avg_pnl']:>7.2f}  {row['avg_roc']:>5.1f}%  "
              f"{row['ann_roc']:>7.1f}%  {row['avg_days']:>7.1f}d  "
              f"{row['stop_pct']:>5.1f}%{marker}")

    # ── Per-year breakdown for top 3 + straddle ───────────────────────────────
    top_combos = (
        df.groupby(["call_delta", "put_delta"])
        .apply(lambda g: (g["pnl"] / g["max_loss"]).mean() * 100, include_groups=False)
        .sort_values(ascending=False)
    )
    to_show: list[tuple] = []
    for combo in top_combos.index:
        if combo not in to_show:
            to_show.append(combo)
        if len(to_show) >= 3:
            break
    if (0.50, 0.50) not in to_show:
        to_show.append((0.50, 0.50))

    print(f"\n{sep}")
    print(f"  PER-YEAR BREAKDOWN  ·  Top combos + straddle baseline")
    print(sep)

    for (cd, pd_) in to_show:
        sub = df[(df["call_delta"] == cd) & (df["put_delta"] == pd_)]
        label = (f"CallΔ={cd:.2f} / PutΔ={pd_:.2f}" +
                 (" (straddle)" if cd == 0.50 and pd_ == 0.50 else ""))
        print(f"\n  {label}")
        print(f"  {'Year':>6}  {'N':>4}  {'Win%':>6}  {'AvgCr':>7}  {'AvgPnL':>8}  "
              f"{'ROC%':>6}  {'AnnROC%':>8}  {'AvgDays':>8}  {'Stops':>5}")
        print("  " + "─" * 78)
        for yr, grp in sub.groupby("year"):
            roc     = (grp["pnl"] / grp["max_loss"]).mean() * 100
            ann_roc = ((grp["pnl"] / grp["max_loss"]) * (365 / grp["days"])).mean() * 100
            print(f"  {yr:>6}  {len(grp):>4}  {(grp['pnl']>0).mean()*100:>5.1f}%  "
                  f"${grp['credit'].mean():>6.2f}  ${grp['pnl'].mean():>7.2f}  "
                  f"{roc:>5.1f}%  {ann_roc:>7.1f}%  {grp['days'].mean():>7.1f}d  "
                  f"{(grp['exit']=='stop_loss').sum():>5}")
        tot_roc     = (sub["pnl"] / sub["max_loss"]).mean() * 100
        tot_ann_roc = ((sub["pnl"] / sub["max_loss"]) * (365 / sub["days"])).mean() * 100
        print(f"  {'TOTAL':>6}  {len(sub):>4}  {(sub['pnl']>0).mean()*100:>5.1f}%  "
              f"${sub['credit'].mean():>6.2f}  ${sub['pnl'].mean():>7.2f}  "
              f"{tot_roc:>5.1f}%  {tot_ann_roc:>7.1f}%  {sub['days'].mean():>7.1f}d  "
              f"{(sub['exit']=='stop_loss').sum():>5}")

    # ── VIX breakdown for the best non-straddle combo ────────────────────────
    best_cd, best_pd = to_show[0]
    best_sub = df[(df["call_delta"] == best_cd) & (df["put_delta"] == best_pd)].copy()
    best_sub["vix"] = best_sub["vix"].astype(float)

    print(f"\n{sep}")
    print(f"  VIX SUBSETS  ·  Best combo: CallΔ={best_cd:.2f} / PutΔ={best_pd:.2f}")
    print(sep)
    print(f"\n  {'VIX Filter':>15}  {'N':>4}  {'Win%':>6}  {'AvgCr':>7}  "
          f"{'AvgPnL':>8}  {'ROC%':>6}  {'Stops%':>6}")
    print("  " + "─" * 60)

    vix_cuts = [("All VIX", None), ("VIX < 30", 30), ("VIX < 25", 25), ("VIX < 20", 20)]
    for lbl, cutoff in vix_cuts:
        sub = best_sub if cutoff is None else best_sub[best_sub["vix"] < cutoff]
        if sub.empty:
            continue
        roc = (sub["pnl"] / sub["max_loss"]).mean() * 100
        print(f"  {lbl:>15}  {len(sub):>4}  {(sub['pnl']>0).mean()*100:>5.1f}%  "
              f"${sub['credit'].mean():>6.2f}  ${sub['pnl'].mean():>7.2f}  "
              f"{roc:>5.1f}%  {(sub['exit']=='stop_loss').mean()*100:>5.1f}%")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dte", type=int, default=20, choices=[7, 10, 20, 45],
                        help="Target DTE (default: 20)")
    parser.add_argument("--refresh", action="store_true",
                        help="Force re-query from Athena even if cache exists")
    parser.add_argument("--regime", default="ALL",
                        help="Regime filter (or ALL)")
    parser.add_argument("--vix-min", type=float, default=None,
                        help="Only enter on days where VIX >= this threshold")
    parser.add_argument("--vix-max", type=float, default=None,
                        help="Only enter on days where VIX < this threshold")
    parser.add_argument("--stop-mult", type=float, default=STOP_MULT,
                        help="Stop-loss multiplier on entry credit (0 = no stop, default: 2.0)")
    parser.add_argument("--require-200ma", action="store_true",
                        help="For Bullish_HighIV entries, also require SPX > 200-day MA")
    parser.add_argument("--wing-delta", type=float, default=None,
                        help="Add protective wings at this delta, converting strangle to IC "
                             "(ROC denominator becomes wing_width - net_credit, matching spread framework)")
    parser.add_argument("--delta-min", type=float, default=0.20,
                        help="Minimum delta included in the sweep (default: 0.20; use 0.10 to include 0.10/0.15)")
    args = parser.parse_args()

    stop_mult     = args.stop_mult
    require_200ma = args.require_200ma
    wing_delta    = args.wing_delta
    active_deltas = [d for d in _ALL_DELTAS if d >= args.delta_min]
    CALL_DELTAS[:] = active_deltas
    PUT_DELTAS[:]  = active_deltas
    dte_target, dte_tol = args.dte, _DTE_SETTINGS[args.dte][0]
    opts = load_options(dte_target=dte_target, refresh=args.refresh)
    spot_map  = load_spot()
    vix_map   = load_vix()
    regime_map = build_regime_map(spot_map, vix_map)

    calls = opts[opts["cp"] == "C"]
    puts  = opts[opts["cp"] == "P"]
    daily_map_c = {(r.trade_date, r.expiry, r.strike): r.mid
                   for r in calls.itertuples(index=False)}
    daily_map_p = {(r.trade_date, r.expiry, r.strike): r.mid
                   for r in puts.itertuples(index=False)}
    opts_by_date = {d: g for d, g in opts.groupby("trade_date")}

    # Entry dates: every Friday in range
    entry_dates = [
        START_DATE + timedelta(days=i)
        for i in range((END_DATE - START_DATE).days + 1)
        if (START_DATE + timedelta(days=i)).weekday() == 4
    ]

    regime_filter = args.regime
    vix_min = args.vix_min
    vix_max = args.vix_max

    print(f"\nSimulating {len(entry_dates)} potential entry Fridays ...")
    results = []
    skipped = 0
    for edate in entry_dates:
        reg = regime_map.get(edate)
        if reg is None:
            skipped += 1
            continue
        if regime_filter != "ALL" and reg["regime"] != regime_filter:
            continue
        vix = reg.get("vix", float("nan"))
        if vix_min is not None and (math.isnan(vix) or vix < vix_min):
            continue
        if vix_max is not None and (math.isnan(vix) or vix >= vix_max):
            continue
        if require_200ma and reg["regime"] == "Bullish_HighIV" and not reg.get("above_200ma", True):
            continue

        day_opts = opts_by_date.get(edate)
        if day_opts is None:
            skipped += 1
            continue

        for cd in CALL_DELTAS:
            call_row = find_option(day_opts, "C", cd, dte_target, dte_tol)
            if call_row is None:
                continue

            for pd_ in PUT_DELTAS:
                put_row = find_option(day_opts, "P", pd_, dte_target, dte_tol,
                                      expiry=call_row["expiry"])
                if put_row is None:
                    continue

                # put strike must be ≤ call strike (strangle rule)
                if put_row["strike"] > call_row["strike"]:
                    continue

                gross_credit = call_row["mid"] + put_row["mid"]
                if gross_credit <= 0:
                    continue

                # ── Optional wings (IC mode) ───────────────────────────────
                call_wing_strike = None
                put_wing_strike  = None
                net_credit       = gross_credit
                max_loss         = gross_credit  # strangle: max managed loss = credit at 2× stop

                if wing_delta is not None:
                    cw_row = find_option(day_opts, "C", wing_delta, dte_target, dte_tol,
                                         expiry=call_row["expiry"])
                    pw_row = find_option(day_opts, "P", wing_delta, dte_target, dte_tol,
                                         expiry=put_row["expiry"])
                    if cw_row is None or pw_row is None:
                        continue
                    if cw_row["strike"] <= call_row["strike"]:
                        continue
                    if pw_row["strike"] >= put_row["strike"]:
                        continue
                    wing_cost  = cw_row["mid"] + pw_row["mid"]
                    net_credit = gross_credit - wing_cost
                    if net_credit <= 0:
                        continue
                    call_wing_width = cw_row["strike"] - call_row["strike"]
                    put_wing_width  = put_row["strike"] - pw_row["strike"]
                    max_loss = max(call_wing_width, put_wing_width) - net_credit
                    if max_loss <= 0:
                        continue
                    call_wing_strike = cw_row["strike"]
                    put_wing_strike  = pw_row["strike"]

                sim = sim_strangle(
                    edate, call_row["expiry"],
                    call_row["strike"], put_row["strike"],
                    net_credit, daily_map_c, daily_map_p, spot_map,
                    stop_mult=stop_mult,
                    call_wing_strike=call_wing_strike,
                    put_wing_strike=put_wing_strike,
                )
                results.append({
                    "call_delta":  cd,
                    "put_delta":   pd_,
                    "edate":       edate,
                    "year":        edate.year,
                    "credit":      net_credit,
                    "max_loss":    max_loss,
                    "call_strike": call_row["strike"],
                    "put_strike":  put_row["strike"],
                    "expiry":      call_row["expiry"],
                    **sim,
                    **reg,
                })

    if skipped:
        print(f"  Skipped {skipped} dates (no regime data or no options data)")

    df = pd.DataFrame(results)
    if df.empty:
        print("No results — check regime filter or date range.")
        return

    stop_lbl   = f"no stop" if stop_mult == 0 else f"{stop_mult}× stop"
    regime_name = regime_filter if regime_filter != "ALL" else "All regimes"
    if require_200ma and regime_filter == "Bullish_HighIV":
        regime_name += " + above 200MA"
    struct_lbl = f"IC (wing {wing_delta:.2f}Δ)" if wing_delta is not None else "strangle"
    regime_lbl = f"~{dte_target} DTE  ·  {regime_name}  ·  {struct_lbl}  ·  50% PT / {stop_lbl}"
    if vix_min is not None and vix_max is not None:
        regime_lbl += f"  ·  {vix_min} ≤ VIX < {vix_max}"
    elif vix_min is not None:
        regime_lbl += f"  ·  VIX ≥ {vix_min}"
    elif vix_max is not None:
        regime_lbl += f"  ·  VIX < {vix_max}"
    print_results(df, "SPX", regime_lbl)


if __name__ == "__main__":
    main()
