#!/usr/bin/env python3
"""
TLT 2:1 Call Ratio Spread backtest.

Structure:
  - Sell 2 calls at short_delta_target  (closer OTM)
  - Buy  1 call at long_delta_target    (further OTM, same expiry)
  - Net credit = 2 × short_mid − long_mid

Exit rules:
  (a) Profit take: daily spread value ≤ entry_credit × (1 − profit_take_pct)
  (b) Stop loss:   daily spread value ≥ entry_credit × stop_mult  (default 2×)
  (c) Expiry:      settle at intrinsic — 2×short_intrinsic − long_intrinsic

P&L at expiry:
  S < short_strike          → keep full credit
  short < S < long_strike   → credit − 2×(S−short)  [losses mount, no hedge yet]
  S > long_strike           → credit − 2×(S−short) + (S−long)  [1 naked short remains]

Sweep: short_delta × long_delta × profit_take × vix_filter

Requires: MYSQL_PASSWORD
"""
from __future__ import annotations

import pathlib
from datetime import date, timedelta

import pandas as pd

from lib.mysql_lib import _get_engine

_CACHE_DIR = pathlib.Path(__file__).parent / "data" / "cache"

# ── Config ────────────────────────────────────────────────────────────────────
SHORT_DELTAS  = [0.25, 0.30, 0.35]
LONG_DELTAS   = [0.10, 0.15, 0.20]   # must be < short delta (further OTM)
PROFIT_TAKES  = [0.50, 0.70]
VIX_MINS      = [None, 20]
STOP_MULT     = 2.0                   # close if spread value ≥ entry_credit × STOP_MULT
DTE_TARGET    = 20
DTE_TOL       = 5
MAX_DELTA_ERR = 0.08
START_DATE    = date(2018, 1, 1)
END_DATE      = date(2026, 3, 14)


# ── Data loading ──────────────────────────────────────────────────────────────

def load_tlt_calls() -> pd.DataFrame:
    sql = f"""
        SELECT trade_date, expiry, strike, mid, delta
        FROM options_cache
        WHERE ticker = 'TLT'
          AND cp     = 'C'
          AND trade_date >= '{START_DATE}'
          AND trade_date <= '{END_DATE}'
          AND mid > 0
          AND delta > 0
        ORDER BY trade_date, expiry, strike
    """
    df = pd.read_sql(sql, _get_engine())
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    df["strike"]     = df["strike"].astype(float)
    df["mid"]        = df["mid"].astype(float)
    df["delta"]      = df["delta"].astype(float)
    df["dte"]        = (df["expiry"] - df["trade_date"]).apply(lambda d: d.days)
    return df


def load_stock() -> dict[date, float]:
    path = _CACHE_DIR / "TLT_stock.parquet"
    df = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    return dict(zip(df["trade_date"], df["close"].astype(float)))


def load_vix() -> dict[date, float]:
    path = _CACHE_DIR / "vix_daily.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    col = "close" if "close" in df.columns else df.columns[-1]
    return dict(zip(df["trade_date"], df[col].astype(float)))


# ── Entry selection ───────────────────────────────────────────────────────────

def find_entry(calls_on_date: pd.DataFrame, target_delta: float) -> pd.Series | None:
    window = calls_on_date[
        (calls_on_date["dte"] >= DTE_TARGET - DTE_TOL) &
        (calls_on_date["dte"] <= DTE_TARGET + DTE_TOL)
    ]
    if window.empty:
        return None
    best_exp = window.iloc[(window["dte"] - DTE_TARGET).abs().argsort()[:1]]["expiry"].iloc[0]
    candidates = window[window["expiry"] == best_exp].copy()
    candidates["_derr"] = (candidates["delta"] - target_delta).abs()
    candidates = candidates[candidates["_derr"] <= MAX_DELTA_ERR]
    if candidates.empty:
        return None
    return candidates.loc[candidates["_derr"].idxmin()]


# ── Simulation ────────────────────────────────────────────────────────────────

def simulate(
    entry_date:      date,
    expiry:          date,
    short_strike:    float,
    long_strike:     float,
    entry_credit:    float,
    profit_take_pct: float,
    daily_map:       dict,
    stock_map:       dict[date, float],
) -> dict:
    """Simulate one 2:1 ratio spread position."""
    take_target = entry_credit * (1.0 - profit_take_pct)
    stop_level  = entry_credit * STOP_MULT          # stop if spread widens this much

    current_date = entry_date + timedelta(days=1)
    while current_date <= expiry:
        short_mid = daily_map.get((current_date, expiry, short_strike))
        long_mid  = daily_map.get((current_date, expiry, long_strike))

        if short_mid is not None and long_mid is not None:
            spread_val = 2.0 * short_mid - long_mid   # cost to close

            # Profit take
            if spread_val <= take_target:
                return dict(pnl=entry_credit - spread_val,
                            exit_type="profit_take",
                            days_held=(current_date - entry_date).days,
                            exit_date=current_date)

            # Stop loss
            if spread_val >= stop_level:
                return dict(pnl=entry_credit - spread_val,
                            exit_type="stop_loss",
                            days_held=(current_date - entry_date).days,
                            exit_date=current_date)

        # Expiry settlement
        if current_date >= expiry:
            spot = stock_map.get(expiry) or stock_map.get(current_date, short_strike)
            short_intr = max(0.0, spot - short_strike)
            long_intr  = max(0.0, spot - long_strike)
            close_val  = 2.0 * short_intr - long_intr
            pnl        = entry_credit - close_val
            etype      = "expiry_win" if pnl >= 0 else "expiry_loss"
            return dict(pnl=pnl, exit_type=etype,
                        days_held=(expiry - entry_date).days,
                        exit_date=expiry)

        current_date += timedelta(days=1)

    # Fallback
    spot = stock_map.get(expiry, short_strike)
    short_intr = max(0.0, spot - short_strike)
    long_intr  = max(0.0, spot - long_strike)
    pnl = entry_credit - (2.0 * short_intr - long_intr)
    return dict(pnl=pnl, exit_type="expiry_win" if pnl >= 0 else "expiry_loss",
                days_held=(expiry - entry_date).days, exit_date=expiry)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading TLT call data...")
    calls     = load_tlt_calls()
    stock_map = load_stock()
    vix_map   = load_vix()

    daily_map = {
        (r.trade_date, r.expiry, r.strike): r.mid
        for r in calls.itertuples(index=False)
    }
    calls_by_date = {d: g for d, g in calls.groupby("trade_date")}

    entry_dates = [
        START_DATE + timedelta(days=i)
        for i in range((END_DATE - START_DATE).days + 1)
        if (START_DATE + timedelta(days=i)).weekday() == 4
    ]

    results = []
    for short_delta in SHORT_DELTAS:
        for long_delta in LONG_DELTAS:
            if long_delta >= short_delta:
                continue                          # long must be further OTM
            for profit_take in PROFIT_TAKES:
                for vix_min in VIX_MINS:
                    for edate in entry_dates:
                        vix = vix_map.get(edate)
                        if vix_min is not None and (vix is None or vix < vix_min):
                            continue

                        day_calls = calls_by_date.get(edate)
                        if day_calls is None:
                            continue

                        short_row = find_entry(day_calls, short_delta)
                        if short_row is None:
                            continue

                        # Long must use SAME expiry as short
                        same_exp = day_calls[day_calls["expiry"] == short_row["expiry"]]
                        same_exp = same_exp.copy()
                        same_exp["_derr"] = (same_exp["delta"] - long_delta).abs()
                        same_exp = same_exp[same_exp["_derr"] <= MAX_DELTA_ERR]
                        if same_exp.empty:
                            continue
                        long_row = same_exp.loc[same_exp["_derr"].idxmin()]

                        if long_row["strike"] <= short_row["strike"]:
                            continue              # long must be at higher strike

                        net_credit = 2.0 * short_row["mid"] - long_row["mid"]
                        if net_credit <= 0:
                            continue              # skip if not a credit

                        sim = simulate(
                            entry_date      = edate,
                            expiry          = short_row["expiry"],
                            short_strike    = short_row["strike"],
                            long_strike     = long_row["strike"],
                            entry_credit    = net_credit,
                            profit_take_pct = profit_take,
                            daily_map       = daily_map,
                            stock_map       = stock_map,
                        )

                        results.append({
                            "short_delta":  short_delta,
                            "long_delta":   long_delta,
                            "profit_take":  profit_take,
                            "vix_min":      vix_min or 0,
                            "entry_date":   edate,
                            "short_strike": short_row["strike"],
                            "long_strike":  long_row["strike"],
                            "entry_credit": net_credit,
                            "vix":          vix,
                            **sim,
                        })

    df = pd.DataFrame(results)
    df["year"] = pd.to_datetime(df["entry_date"]).dt.year

    # ── Summary table ─────────────────────────────────────────────────────────
    print("\n" + "═" * 90)
    print(f"  TLT 2:1 CALL RATIO SPREAD  ·  2018–2026  ·  ~20 DTE  ·  Stop={int(STOP_MULT)}× credit")
    print("═" * 90)

    for profit_take in PROFIT_TAKES:
        print(f"\n  Profit Take: {int(profit_take*100)}%")
        print(f"  {'ShortΔ':>7}  {'LongΔ':>6}  {'VIX≥':>5}  {'N':>4}  {'Win%':>6}  "
              f"{'AvgCr':>7}  {'AvgPnL':>7}  {'AvgROC%':>8}  {'MaxLoss':>8}  "
              f"{'Stops':>6}  {'SumPnL':>8}")
        print("  " + "─" * 84)

        for vix_min in [0, 20]:
            for short_delta in SHORT_DELTAS:
                for long_delta in LONG_DELTAS:
                    if long_delta >= short_delta:
                        continue
                    sub = df[
                        (df["short_delta"] == short_delta) &
                        (df["long_delta"]  == long_delta) &
                        (df["profit_take"] == profit_take) &
                        (df["vix_min"]     == vix_min)
                    ]
                    if sub.empty:
                        continue
                    n        = len(sub)
                    wins     = (sub["pnl"] > 0).sum()
                    stops    = (sub["exit_type"] == "stop_loss").sum()
                    avg_cr   = sub["entry_credit"].mean()
                    avg_pnl  = sub["pnl"].mean()
                    avg_roc  = (sub["pnl"] / sub["entry_credit"]).mean() * 100
                    max_loss = sub["pnl"].min()
                    sum_pnl  = sub["pnl"].sum()
                    vix_lbl  = str(vix_min) if vix_min else "All"
                    print(f"  {short_delta:>7.2f}  {long_delta:>6.2f}  {vix_lbl:>5}  {n:>4}  "
                          f"{wins/n*100:>5.1f}%  ${avg_cr:>6.3f}  ${avg_pnl:>6.3f}  "
                          f"{avg_roc:>7.1f}%  ${max_loss:>7.3f}  {stops:>6}  ${sum_pnl:>7.3f}")
            print()

    # ── Per-year breakdown: best combos ───────────────────────────────────────
    print("\n" + "═" * 90)
    print("  PER-YEAR  ·  0.35Δ short / 0.15Δ long  ·  70% take  ·  All VIX vs VIX≥20")
    print("═" * 90)

    for vix_min, lbl in [(0, "All VIX"), (20, "VIX≥20")]:
        sub = df[
            (df["short_delta"] == 0.35) &
            (df["long_delta"]  == 0.15) &
            (df["profit_take"] == 0.70) &
            (df["vix_min"]     == vix_min)
        ]
        if sub.empty:
            continue
        print(f"\n  {lbl}")
        print(f"  {'Year':>6}  {'N':>4}  {'Win%':>6}  {'AvgCr':>7}  {'AvgPnL':>7}  "
              f"{'Stops':>6}  {'SumPnL':>8}")
        print("  " + "─" * 56)
        for yr, grp in sub.groupby("year"):
            print(f"  {yr:>6}  {len(grp):>4}  {(grp['pnl']>0).mean()*100:>5.1f}%  "
                  f"${grp['entry_credit'].mean():>6.3f}  ${grp['pnl'].mean():>6.3f}  "
                  f"{(grp['exit_type']=='stop_loss').sum():>6}  ${grp['pnl'].sum():>7.3f}")
        print(f"  {'TOTAL':>6}  {len(sub):>4}  {(sub['pnl']>0).mean()*100:>5.1f}%  "
              f"${sub['entry_credit'].mean():>6.3f}  ${sub['pnl'].mean():>6.3f}  "
              f"{(sub['exit_type']=='stop_loss').sum():>6}  ${sub['pnl'].sum():>7.3f}")

    # ── Comparison vs naked and spread ────────────────────────────────────────
    print("\n" + "═" * 90)
    print("  STRUCTURE COMPARISON  ·  0.35Δ short  ·  70% take  ·  VIX≥20")
    print("  (ratio = short 0.35Δ × 2 / long varies; spread = short 0.35Δ / long 0.25Δ)")
    print("═" * 90)
    print(f"  {'Structure':<30}  {'N':>4}  {'Win%':>6}  {'AvgCr':>7}  "
          f"{'AvgPnL':>7}  {'MaxLoss':>8}  {'SumPnL':>8}")
    print("  " + "─" * 78)
    for long_delta in LONG_DELTAS:
        sub = df[
            (df["short_delta"] == 0.35) &
            (df["long_delta"]  == long_delta) &
            (df["profit_take"] == 0.70) &
            (df["vix_min"]     == 20)
        ]
        if sub.empty:
            continue
        lbl = f"Ratio: -2×0.35Δ / +1×{long_delta:.2f}Δ"
        print(f"  {lbl:<30}  {len(sub):>4}  {(sub['pnl']>0).mean()*100:>5.1f}%  "
              f"${sub['entry_credit'].mean():>6.3f}  ${sub['pnl'].mean():>6.3f}  "
              f"${sub['pnl'].min():>7.3f}  ${sub['pnl'].sum():>7.3f}")


if __name__ == "__main__":
    main()
