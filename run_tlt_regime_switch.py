#!/usr/bin/env python3
"""
TLT Regime-Switching Strategy Backtest

Each Friday, classify the regime and deploy the optimal structure:
  Bearish_HighIV  → Bear call spread:        short 0.35Δ call / long 0.25Δ call
  Bearish_LowIV   → Short strangle (sym):     short 0.25Δ call / short 0.25Δ put
  Bullish_HighIV  → Short strangle (skewed):  short 0.45Δ call / short 0.25Δ put
  Bullish_LowIV   → Long straddle:            long  0.50Δ call / long  0.50Δ put

Exit rules:
  Credit strategies: 50% profit take, 2× stop loss
  Long straddle:     +50% take, −40% stop

Comparison baselines:
  (A) Always-on bear call spread (0.35Δ / 0.25Δ, no filter)
  (B) Always-on bear call spread with VIX ≥ 20 filter

Usage:
  PYTHONPATH=src python run_tlt_regime_switch.py

Requires: MYSQL_PASSWORD
"""
from __future__ import annotations

import math
import pathlib
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from lib.mysql_lib import _get_engine

_CACHE_DIR = pathlib.Path(__file__).parent / "data" / "cache"

# ── Strategy parameters ───────────────────────────────────────────────────────
REGIME_STRATEGIES = {
    "Bearish_HighIV": ("bear_call_spread",     0.35, 0.25, None,  None ),
    "Bearish_LowIV":  ("short_strangle_sym",   0.25, 0.25, None,  None ),
    "Bullish_HighIV": ("short_strangle_skew",  0.45, 0.25, None,  None ),
    "Bullish_LowIV":  ("long_straddle",        0.50, 0.50, None,  None ),
}
# (strategy_name, call_delta, put_delta, ...)

PROFIT_TAKE   = 0.50
STOP_MULT     = 2.0
LONG_TAKE_PCT = 0.50
LONG_STOP_PCT = 0.40

DTE_TARGET    = 20
DTE_TOL       = 5
MAX_DELTA_ERR = 0.08
MA_WINDOW     = 50
RV_WINDOW     = 20
VIX_HIGH      = 20

START_DATE = date(2018, 1, 1)
END_DATE   = date(2026, 3, 14)


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
        vix   = vix_map.get(d, float("nan"))
        direction = "Bullish" if close > ma50 else "Bearish"
        iv_label  = "HighIV"  if (not math.isnan(vix) and vix >= VIX_HIGH) else "LowIV"
        regime[d] = dict(
            regime    = f"{direction}_{iv_label}",
            vix       = vix,
            roc20     = (close / closes[i - RV_WINDOW] - 1) * 100,
            above_ma  = close > ma50,
        )
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

    cur = entry_date + timedelta(days=1)
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


def sim_strangle(
    entry_date:   date,
    expiry:       date,
    call_strike:  float,
    put_strike:   float,
    credit:       float,
    is_short:     bool,
    daily_map_c:  dict,
    daily_map_p:  dict,
    stock_map:    dict[date, float],
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
                                days=(cur - entry_date).days, exit_date=cur)
                if val >= stop:
                    return dict(pnl=credit - val, exit="stop_loss",
                                days=(cur - entry_date).days, exit_date=cur)
            else:
                if val >= take:
                    return dict(pnl=val - credit, exit="profit_take",
                                days=(cur - entry_date).days, exit_date=cur)
                if val <= stop:
                    return dict(pnl=val - credit, exit="stop_loss",
                                days=(cur - entry_date).days, exit_date=cur)
        if cur >= expiry:
            spot   = stock_map.get(expiry) or stock_map.get(cur, call_strike)
            ci     = max(0.0, spot - call_strike)
            pi     = max(0.0, put_strike - spot)
            expire = ci + pi
            pnl    = (credit - expire) if is_short else (expire - credit)
            return dict(pnl=pnl, exit="expiry_win" if pnl >= 0 else "expiry_loss",
                        days=(expiry - entry_date).days, exit_date=expiry)
        cur += timedelta(days=1)

    spot = stock_map.get(expiry, call_strike)
    ci   = max(0.0, spot - call_strike)
    pi   = max(0.0, put_strike - spot)
    pnl  = (credit - ci - pi) if is_short else (ci + pi - credit)
    return dict(pnl=pnl, exit="expiry_win" if pnl >= 0 else "expiry_loss",
                days=(expiry - entry_date).days, exit_date=expiry)


# ── Trade entry for each strategy ────────────────────────────────────────────

def enter_trade(
    regime:      str,
    edate:       date,
    day_opts:    pd.DataFrame,
    daily_map_c: dict,
    daily_map_p: dict,
    stock_map:   dict[date, float],
) -> Optional[dict]:
    strategy, cd, pd_, _, _ = REGIME_STRATEGIES[regime]

    if strategy == "bear_call_spread":
        short_row = find_option(day_opts, "C", cd)
        if short_row is None:
            return None
        long_row = find_option(day_opts, "C", pd_, expiry=short_row["expiry"])
        if long_row is None or long_row["strike"] <= short_row["strike"]:
            return None
        credit = short_row["mid"] - long_row["mid"]
        if credit <= 0:
            return None
        sim = sim_credit_spread(edate, short_row["expiry"],
                                short_row["strike"], long_row["strike"],
                                "C", credit, daily_map_c, stock_map)
        return dict(strategy=strategy, entry_val=credit, **sim)

    elif strategy in ("short_strangle_sym", "short_strangle_skew"):
        call_row = find_option(day_opts, "C", cd)
        if call_row is None:
            return None
        put_row = find_option(day_opts, "P", pd_, expiry=call_row["expiry"])
        if put_row is None or put_row["strike"] > call_row["strike"]:
            return None
        credit = call_row["mid"] + put_row["mid"]
        if credit <= 0:
            return None
        sim = sim_strangle(edate, call_row["expiry"],
                           call_row["strike"], put_row["strike"],
                           credit, True, daily_map_c, daily_map_p, stock_map)
        return dict(strategy=strategy, entry_val=credit, **sim)

    elif strategy == "long_straddle":
        call_row = find_option(day_opts, "C", cd)
        if call_row is None:
            return None
        put_row = find_option(day_opts, "P", pd_, expiry=call_row["expiry"])
        if put_row is None:
            return None
        cost = call_row["mid"] + put_row["mid"]
        if cost <= 0:
            return None
        sim = sim_strangle(edate, call_row["expiry"],
                           call_row["strike"], put_row["strike"],
                           cost, False, daily_map_c, daily_map_p, stock_map)
        return dict(strategy=strategy, entry_val=cost, **sim)

    return None


def enter_bear_call_spread(
    edate:       date,
    day_opts:    pd.DataFrame,
    daily_map_c: dict,
    stock_map:   dict[date, float],
    vix:         float,
    vix_filter:  Optional[float] = None,
) -> Optional[dict]:
    if vix_filter is not None and (math.isnan(vix) or vix < vix_filter):
        return None
    short_row = find_option(day_opts, "C", 0.35)
    if short_row is None:
        return None
    long_row = find_option(day_opts, "C", 0.25, expiry=short_row["expiry"])
    if long_row is None or long_row["strike"] <= short_row["strike"]:
        return None
    credit = short_row["mid"] - long_row["mid"]
    if credit <= 0:
        return None
    sim = sim_credit_spread(edate, short_row["expiry"],
                            short_row["strike"], long_row["strike"],
                            "C", credit, daily_map_c, stock_map)
    return dict(strategy="bear_call_spread", entry_val=credit, **sim)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading TLT option data...")
    opts = load_tlt_options()
    print(f"  {len(opts):,} rows")

    stock_df   = load_stock()
    stock_map  = dict(zip(stock_df["trade_date"], stock_df["close"].astype(float)))
    vix_map    = load_vix()
    regime_map = build_regime_map(stock_df, vix_map)

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

    switch_rows = []
    baseline_rows = []   # always-on, no filter
    vix20_rows    = []   # always-on, VIX ≥ 20

    for edate in entry_dates:
        reg = regime_map.get(edate)
        if reg is None:
            continue
        day_opts = opts_by_date.get(edate)
        if day_opts is None:
            continue

        regime = reg["regime"]
        vix    = reg["vix"]

        # Switching strategy
        trade = enter_trade(regime, edate, day_opts, daily_map_c, daily_map_p, stock_map)
        if trade:
            switch_rows.append(dict(edate=edate, year=edate.year, regime=regime,
                                    vix=vix, **trade))

        # Baseline A: always-on call spread
        b = enter_bear_call_spread(edate, day_opts, daily_map_c, stock_map, vix)
        if b:
            baseline_rows.append(dict(edate=edate, year=edate.year, regime=regime,
                                      vix=vix, **b))

        # Baseline B: call spread, VIX ≥ 20 only
        b2 = enter_bear_call_spread(edate, day_opts, daily_map_c, stock_map, vix,
                                    vix_filter=20.0)
        if b2:
            vix20_rows.append(dict(edate=edate, year=edate.year, regime=regime,
                                   vix=vix, **b2))

    sw  = pd.DataFrame(switch_rows)
    bl  = pd.DataFrame(baseline_rows)
    v20 = pd.DataFrame(vix20_rows)

    # ── Helper ────────────────────────────────────────────────────────────────
    def stats(df: pd.DataFrame) -> dict:
        if df.empty:
            return {}
        n      = len(df)
        wins   = (df["pnl"] > 0).sum()
        avg_cr = df["entry_val"].mean()
        avg_p  = df["pnl"].mean()
        roc    = (df["pnl"] / df["entry_val"]).mean() * 100
        maxl   = df["pnl"].min()
        sump   = df["pnl"].sum()
        stops  = (df["exit"] == "stop_loss").sum()
        return dict(n=n, win_pct=wins/n*100, avg_cr=avg_cr, avg_pnl=avg_p,
                    roc=roc, max_loss=maxl, sum_pnl=sump, stop_pct=stops/n*100)

    def print_stats_row(label: str, s: dict, width: int = 30) -> None:
        if not s:
            return
        print(f"  {label:<{width}}  {s['n']:>4}  {s['win_pct']:>5.1f}%  "
              f"${s['avg_cr']:>7.3f}  ${s['avg_pnl']:>6.3f}  {s['roc']:>6.1f}%  "
              f"${s['max_loss']:>7.3f}  ${s['sum_pnl']:>8.3f}  {s['stop_pct']:>5.1f}%")

    HDR = (f"  {'Strategy':<30}  {'N':>4}  {'Win%':>6}  {'AvgCr':>8}  "
           f"{'AvgPnL':>7}  {'ROC%':>7}  {'MaxLoss':>8}  {'SumPnL':>9}  {'Stops%':>6}")

    # ── Overall comparison ────────────────────────────────────────────────────
    print("\n" + "═" * 96)
    print("  TLT REGIME-SWITCHING STRATEGY  ·  2018–2026  ·  ~20 DTE")
    print("  50% profit take / 2× stop  (long straddle: +50% take / −40% stop)")
    print("═" * 96)
    print("\n  OVERALL COMPARISON\n")
    print(HDR)
    print("  " + "─" * 92)
    print_stats_row("Regime-switching",        stats(sw))
    print_stats_row("Always-on call spread",   stats(bl))
    print_stats_row("Call spread VIX≥20 only", stats(v20))

    # ── Per-year comparison ───────────────────────────────────────────────────
    print("\n\n" + "═" * 96)
    print("  PER-YEAR  ·  Regime-switching vs Baselines")
    print("═" * 96)
    print(f"\n  {'Year':>6}  {'Regime-Switch':>14}  "
          f"{'Always-On':>10}  {'VIX≥20 Only':>12}  "
          f"{'Regime counts (BearHI / BearLO / BullHI / BullLO)':>50}")
    print("  " + "─" * 92)

    all_years = sorted(sw["year"].unique())
    for yr in all_years:
        sw_yr  = sw[sw["year"] == yr]
        bl_yr  = bl[bl["year"] == yr]
        v2_yr  = v20[v20["year"] == yr]

        sw_roc = (sw_yr["pnl"] / sw_yr["entry_val"]).mean() * 100 if len(sw_yr) else 0.0
        bl_roc = (bl_yr["pnl"] / bl_yr["entry_val"]).mean() * 100 if len(bl_yr) else 0.0
        v2_roc = (v2_yr["pnl"] / v2_yr["entry_val"]).mean() * 100 if len(v2_yr) else 0.0

        sw_sum = sw_yr["pnl"].sum()
        bl_sum = bl_yr["pnl"].sum()
        v2_sum = v2_yr["pnl"].sum()

        # regime counts from switching df
        rc = sw_yr["regime"].value_counts()
        bhi = rc.get("Bearish_HighIV", 0)
        blo = rc.get("Bearish_LowIV",  0)
        uhi = rc.get("Bullish_HighIV", 0)
        ulo = rc.get("Bullish_LowIV",  0)

        sw_tag  = f"{sw_roc:+5.1f}% ${sw_sum:+7.2f}"
        bl_tag  = f"{bl_roc:+5.1f}% ${bl_sum:+7.2f}"
        v2_tag  = f"{v2_roc:+5.1f}% ${v2_sum:+7.2f}" if len(v2_yr) else "    (skipped)  "
        print(f"  {yr:>6}  {sw_tag:>14}   {bl_tag:>14}  {v2_tag:>14}   "
              f"BHI={bhi:>2}  BLO={blo:>2}  UHI={uhi:>2}  ULO={ulo:>2}")

    # totals
    sw_tot  = (sw["pnl"] / sw["entry_val"]).mean() * 100
    bl_tot  = (bl["pnl"] / bl["entry_val"]).mean() * 100
    v2_tot  = (v20["pnl"] / v20["entry_val"]).mean() * 100
    print(f"\n  {'TOTAL':>6}  {sw_tot:+5.1f}% ${sw['pnl'].sum():+7.2f}   "
          f"{bl_tot:+5.1f}% ${bl['pnl'].sum():+7.2f}  "
          f"{v2_tot:+5.1f}% ${v20['pnl'].sum():+7.2f}")

    # ── Switching strategy detail by regime ──────────────────────────────────
    print("\n\n" + "═" * 96)
    print("  SWITCHING STRATEGY  ·  per-regime contribution")
    print("═" * 96)
    print("\n" + HDR)
    print("  " + "─" * 92)
    for regime, (strat, cd, pd_, _, _) in REGIME_STRATEGIES.items():
        sub = sw[sw["regime"] == regime]
        label = f"{regime}  →  {strat}  ({cd:.2f}Δ/{pd_:.2f}Δ)"
        print_stats_row(label, stats(sub), width=50)

    # ── Win/loss streaks in switching strategy ────────────────────────────────
    print("\n\n" + "═" * 96)
    print("  DRAWDOWN ANALYSIS  ·  Regime-switching vs Always-on call spread")
    print("═" * 96)

    for label, df_ in [("Regime-switching", sw), ("Always-on call spread", bl)]:
        cumulative = df_["pnl"].cumsum().values
        running_max = np.maximum.accumulate(cumulative)
        drawdown    = cumulative - running_max
        max_dd      = drawdown.min()
        # longest losing streak
        wins_  = (df_["pnl"] > 0).astype(int).values
        max_streak = cur_streak = 0
        for w in wins_:
            if w == 0:
                cur_streak += 1
                max_streak = max(max_streak, cur_streak)
            else:
                cur_streak = 0
        print(f"\n  {label}")
        print(f"    Cumulative P&L:    ${cumulative[-1]:+.3f}")
        print(f"    Max drawdown:      ${max_dd:+.3f}")
        print(f"    Max losing streak: {max_streak} weeks")

    # ── Regime transition table ───────────────────────────────────────────────
    print("\n\n" + "═" * 96)
    print("  REGIME DISTRIBUTION  ·  weeks per year")
    print("═" * 96)
    pivot = (sw.groupby(["year", "regime"]).size().unstack(fill_value=0))
    cols  = ["Bearish_HighIV", "Bearish_LowIV", "Bullish_HighIV", "Bullish_LowIV"]
    pivot = pivot.reindex(columns=[c for c in cols if c in pivot.columns], fill_value=0)
    pivot.columns = ["BearHI", "BearLO", "BullHI", "BullLO"]
    pivot["Total"] = pivot.sum(axis=1)
    print(f"\n{pivot.to_string()}")
    print(f"\n  Column totals: {pivot.sum().to_dict()}")


if __name__ == "__main__":
    main()
