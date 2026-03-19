#!/usr/bin/env python3
"""
TLT Multi-Strategy Regime Study

Evaluates five strategies on every Friday entry date (2018–2026, ~20 DTE):
  1. bear_call_spread  — short 0.35Δ call / long 0.25Δ call  (credit)
  2. bull_put_spread   — short 0.35Δ put  / long 0.25Δ put   (credit)
  3. iron_condor       — put spread + call spread combined    (credit)
  4. short_straddle    — short 0.50Δ call + short 0.50Δ put  (credit)
  5. long_straddle     — long  0.50Δ call + long  0.50Δ put  (debit)

Regime signals per entry date:
  - trend_bullish:  TLT close > 50-day MA
  - roc20:          20-day price return (%)
  - vix:            VIX close
  - rv20:           20-day annualized realized vol of TLT

Exit rules:
  - Credit strategies (1–4): profit take 50%, stop at 2× credit
  - Long straddle (5):       profit take at +50%, stop at -40%

Regimes (4 buckets):
  Bearish_HighIV:  below 50MA + VIX ≥ 20
  Bearish_LowIV:   below 50MA + VIX <  20
  Bullish_HighIV:  above 50MA + VIX ≥ 20
  Bullish_LowIV:   above 50MA + VIX <  20

Usage:
  PYTHONPATH=src python run_tlt_strategy_study.py [--ticker TMF]

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
CALL_SHORT_DELTA = 0.35
CALL_LONG_DELTA  = 0.25
PUT_SHORT_DELTA  = 0.35
PUT_LONG_DELTA   = 0.25
STRADDLE_DELTA   = 0.50

DTE_TARGET    = 20
DTE_TOL       = 5
MAX_DELTA_ERR = 0.08

PROFIT_TAKE_PCT = 0.50   # credit strategies: close when value drops to entry × (1 - this)
STOP_MULT       = 2.0    # credit strategies: stop when value ≥ entry × this
LONG_TAKE_PCT   = 0.50   # long straddle: take at +50%
LONG_STOP_PCT   = 0.40   # long straddle: stop at -40%

MA_WINDOW = 50
RV_WINDOW = 20
VIX_HIGH  = 20           # threshold for High vs Low IV regime

START_DATE = date(2018, 1, 1)
END_DATE   = date(2026, 3, 14)


# ── Data loading ──────────────────────────────────────────────────────────────

def load_options(ticker: str) -> pd.DataFrame:
    all_deltas = [CALL_SHORT_DELTA, CALL_LONG_DELTA, PUT_SHORT_DELTA, PUT_LONG_DELTA, STRADDLE_DELTA]
    dte_min    = max(0, DTE_TARGET - DTE_TOL - 5)
    dte_max    = DTE_TARGET + DTE_TOL + 5
    delta_min  = min(all_deltas) - MAX_DELTA_ERR
    delta_max  = max(all_deltas) + MAX_DELTA_ERR
    sql = f"""
        SELECT trade_date, expiry, strike, mid, delta, cp,
               DATEDIFF(expiry, trade_date) AS dte
        FROM options_cache
        WHERE ticker = '{ticker}'
          AND trade_date >= '{START_DATE}'
          AND trade_date <= '{END_DATE}'
          AND mid > 0
          AND delta <> 0
          AND ABS(delta) BETWEEN {delta_min} AND {delta_max}
          AND DATEDIFF(expiry, trade_date) BETWEEN {dte_min} AND {dte_max}
        ORDER BY trade_date, expiry, strike
    """
    df = pd.read_sql(sql, _get_engine())
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    df["strike"]     = df["strike"].astype(float)
    df["mid"]        = df["mid"].astype(float)
    df["delta"]      = df["delta"].abs().astype(float)
    df["dte"]        = df["dte"].astype(int)
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
    df  = pd.read_parquet(path)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    col = "close" if "close" in df.columns else df.columns[-1]
    return dict(zip(df["trade_date"], df[col].astype(float)))


# ── Regime computation ────────────────────────────────────────────────────────

def build_regime_map(stock_df: pd.DataFrame, vix_map: dict[date, float]) -> dict[date, dict]:
    closes = stock_df["close"].astype(float).values
    dates  = stock_df["trade_date"].values

    regime: dict[date, dict] = {}
    for i, d in enumerate(dates):
        if i < RV_WINDOW:
            continue

        close = closes[i]
        ma50  = closes[max(0, i - MA_WINDOW + 1):i + 1].mean()

        roc20_base = closes[i - RV_WINDOW]
        roc20      = (close / roc20_base - 1) * 100 if roc20_base > 0 else 0.0

        log_rets = np.log(
            closes[i - RV_WINDOW + 1:i + 1] /
            closes[i - RV_WINDOW:i]
        )
        rv20 = float(np.std(log_rets) * math.sqrt(252) * 100)

        vix = vix_map.get(d, float("nan"))

        regime[d] = dict(
            close         = close,
            ma50          = ma50,
            trend_bullish = bool(close > ma50),
            roc20         = roc20,
            rv20          = rv20,
            vix           = vix,
        )
    return regime


def classify_regime(r: dict) -> str:
    direction = "Bullish" if r["trend_bullish"] else "Bearish"
    vix = r.get("vix", float("nan"))
    iv_label = "HighIV" if (not math.isnan(vix) and vix >= VIX_HIGH) else "LowIV"
    return f"{direction}_{iv_label}"


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

def sim_spread(
    entry_date:      date,
    expiry:          date,
    short_strike:    float,
    long_strike:     float,
    cp:              str,
    entry_credit:    float,
    daily_map:       dict,
    stock_map:       dict[date, float],
) -> dict:
    """Simulate one credit spread (call or put)."""
    take_target = entry_credit * (1.0 - PROFIT_TAKE_PCT)
    stop_level  = entry_credit * STOP_MULT

    cur = entry_date + timedelta(days=1)
    while cur <= expiry:
        s_mid = daily_map.get((cur, expiry, short_strike))
        l_mid = daily_map.get((cur, expiry, long_strike))

        if s_mid is not None and l_mid is not None:
            val = s_mid - l_mid
            if val <= take_target:
                return dict(pnl=entry_credit - val, exit="profit_take",
                            days=(cur - entry_date).days, exit_date=cur)
            if val >= stop_level:
                return dict(pnl=entry_credit - val, exit="stop_loss",
                            days=(cur - entry_date).days, exit_date=cur)

        if cur >= expiry:
            spot = stock_map.get(expiry) or stock_map.get(cur, short_strike)
            if cp == "C":
                s_intr = max(0.0, spot - short_strike)
                l_intr = max(0.0, spot - long_strike)
            else:
                s_intr = max(0.0, short_strike - spot)
                l_intr = max(0.0, long_strike - spot)
            close_val = s_intr - l_intr
            pnl = entry_credit - close_val
            etype = "expiry_win" if pnl >= 0 else "expiry_loss"
            return dict(pnl=pnl, exit=etype,
                        days=(expiry - entry_date).days, exit_date=expiry)

        cur += timedelta(days=1)

    # fallback — no data
    spot = stock_map.get(expiry, short_strike)
    if cp == "C":
        s_intr = max(0.0, spot - short_strike)
        l_intr = max(0.0, spot - long_strike)
    else:
        s_intr = max(0.0, short_strike - spot)
        l_intr = max(0.0, long_strike - spot)
    pnl = entry_credit - (s_intr - l_intr)
    return dict(pnl=pnl, exit="expiry_win" if pnl >= 0 else "expiry_loss",
                days=(expiry - entry_date).days, exit_date=expiry)


def sim_straddle(
    entry_date:  date,
    expiry:      date,
    call_strike: float,
    put_strike:  float,
    entry_value: float,
    is_short:    bool,
    daily_map_c: dict,
    daily_map_p: dict,
    stock_map:   dict[date, float],
) -> dict:
    """Simulate short or long straddle."""
    if is_short:
        take_target = entry_value * (1.0 - PROFIT_TAKE_PCT)
        stop_level  = entry_value * STOP_MULT
    else:
        take_target = entry_value * (1.0 + LONG_TAKE_PCT)
        stop_level  = entry_value * (1.0 - LONG_STOP_PCT)

    cur = entry_date + timedelta(days=1)
    while cur <= expiry:
        c_mid = daily_map_c.get((cur, expiry, call_strike))
        p_mid = daily_map_p.get((cur, expiry, put_strike))

        if c_mid is not None and p_mid is not None:
            val = c_mid + p_mid
            if is_short:
                if val <= take_target:
                    return dict(pnl=entry_value - val, exit="profit_take",
                                days=(cur - entry_date).days, exit_date=cur)
                if val >= stop_level:
                    return dict(pnl=entry_value - val, exit="stop_loss",
                                days=(cur - entry_date).days, exit_date=cur)
            else:
                if val >= take_target:
                    return dict(pnl=val - entry_value, exit="profit_take",
                                days=(cur - entry_date).days, exit_date=cur)
                if val <= stop_level:
                    return dict(pnl=val - entry_value, exit="stop_loss",
                                days=(cur - entry_date).days, exit_date=cur)

        if cur >= expiry:
            spot = stock_map.get(expiry) or stock_map.get(cur, call_strike)
            c_intr = max(0.0, spot - call_strike)
            p_intr = max(0.0, put_strike - spot)
            expire_val = c_intr + p_intr
            pnl = (entry_value - expire_val) if is_short else (expire_val - entry_value)
            etype = "expiry_win" if pnl >= 0 else "expiry_loss"
            return dict(pnl=pnl, exit=etype,
                        days=(expiry - entry_date).days, exit_date=expiry)

        cur += timedelta(days=1)

    spot = stock_map.get(expiry, call_strike)
    c_intr    = max(0.0, spot - call_strike)
    p_intr    = max(0.0, put_strike - spot)
    expire_val = c_intr + p_intr
    pnl = (entry_value - expire_val) if is_short else (expire_val - entry_value)
    return dict(pnl=pnl, exit="expiry_win" if pnl >= 0 else "expiry_loss",
                days=(expiry - entry_date).days, exit_date=expiry)


# ── Report helper ─────────────────────────────────────────────────────────────

STRATEGIES = [
    "bear_call_spread",
    "bull_put_spread",
    "iron_condor",
    "short_straddle",
    "long_straddle",
]

HDR = (f"  {'Strategy':<22}  {'N':>4}  {'Win%':>6}  {'AvgEntry':>9}  "
       f"{'AvgPnL':>7}  {'ROC%':>6}  {'MaxLoss':>8}  {'SumPnL':>8}  {'Stops%':>6}")
SEP = "  " + "─" * 88


def print_section(df_sub: pd.DataFrame, label: str) -> None:
    print(f"\n── {label} " + "─" * max(0, 70 - len(label)))
    print(HDR)
    print(SEP)
    best_roc = -9999.0
    best_strat = ""
    for strat in STRATEGIES:
        sub = df_sub[df_sub["strategy"] == strat]
        if sub.empty:
            continue
        n        = len(sub)
        wins     = (sub["pnl"] > 0).sum()
        avg_cr   = sub["entry_val"].mean()
        avg_pnl  = sub["pnl"].mean()
        avg_roc  = (sub["pnl"] / sub["entry_val"]).mean() * 100
        max_loss = sub["pnl"].min()
        sum_pnl  = sub["pnl"].sum()
        stops    = (sub["exit"] == "stop_loss").sum()
        marker   = " ◀" if avg_roc > 0 and avg_roc == max(
            (df_sub[df_sub["strategy"] == s]["pnl"] / df_sub[df_sub["strategy"] == s]["entry_val"]).mean() * 100
            for s in STRATEGIES if not df_sub[df_sub["strategy"] == s].empty
        ) else ""
        print(f"  {strat:<22}  {n:>4}  {wins/n*100:>5.1f}%  "
              f"${avg_cr:>8.3f}  ${avg_pnl:>6.3f}  {avg_roc:>5.1f}%  "
              f"${max_loss:>7.3f}  ${sum_pnl:>7.3f}  {stops/n*100:>5.1f}%{marker}")
        if avg_roc > best_roc:
            best_roc   = avg_roc
            best_strat = strat
    if best_roc > 0:
        print(f"  → Best ROC: {best_strat}  ({best_roc:+.1f}%)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="TLT", help="Ticker symbol (default: TLT)")
    args = parser.parse_args()
    ticker = args.ticker.upper()

    print(f"Loading {ticker} option data...")
    opts = load_options(ticker)
    print(f"  {len(opts):,} rows  ({opts['trade_date'].min()} → {opts['trade_date'].max()})")

    stock_df   = load_stock(ticker)
    stock_map  = dict(zip(stock_df["trade_date"], stock_df["close"].astype(float)))
    vix_map    = load_vix()
    regime_map = build_regime_map(stock_df, vix_map)

    print("Building daily option lookup maps...")
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

    print(f"Simulating {len(entry_dates)} entry dates × 5 strategies...")
    results = []
    for edate in entry_dates:
        reg = regime_map.get(edate)
        if reg is None:
            continue
        day_opts = opts_by_date.get(edate)
        if day_opts is None:
            continue

        regime_label = classify_regime(reg)

        # Initialize all leg vars
        cs_short = cs_long = ps_short = ps_long = atm_call = atm_put = None

        # ── 1. Bear call spread ───────────────────────────────────────────
        cs_short = find_option(day_opts, "C", CALL_SHORT_DELTA)
        if cs_short is not None:
            cs_long = find_option(day_opts, "C", CALL_LONG_DELTA, expiry=cs_short["expiry"])
            if cs_long is not None and cs_long["strike"] > cs_short["strike"]:
                credit = cs_short["mid"] - cs_long["mid"]
                if credit > 0:
                    sim = sim_spread(edate, cs_short["expiry"],
                                     cs_short["strike"], cs_long["strike"],
                                     "C", credit, daily_map_c, stock_map)
                    results.append({"strategy": "bear_call_spread", "edate": edate,
                                    "regime": regime_label, "entry_val": credit, **sim, **reg})

        # ── 2. Bull put spread ────────────────────────────────────────────
        ps_short = find_option(day_opts, "P", PUT_SHORT_DELTA)
        if ps_short is not None:
            ps_long = find_option(day_opts, "P", PUT_LONG_DELTA, expiry=ps_short["expiry"])
            if ps_long is not None and ps_long["strike"] < ps_short["strike"]:
                credit = ps_short["mid"] - ps_long["mid"]
                if credit > 0:
                    sim = sim_spread(edate, ps_short["expiry"],
                                     ps_short["strike"], ps_long["strike"],
                                     "P", credit, daily_map_p, stock_map)
                    results.append({"strategy": "bull_put_spread", "edate": edate,
                                    "regime": regime_label, "entry_val": credit, **sim, **reg})

        # ── 3. Iron condor (both sides, same expiry) ──────────────────────
        if (cs_short is not None and cs_long is not None and
                ps_short is not None and ps_long is not None and
                cs_short["expiry"] == ps_short["expiry"]):
            call_credit = cs_short["mid"] - cs_long["mid"]
            put_credit  = ps_short["mid"] - ps_long["mid"]
            if call_credit > 0 and put_credit > 0:
                call_sim = sim_spread(edate, cs_short["expiry"],
                                      cs_short["strike"], cs_long["strike"],
                                      "C", call_credit, daily_map_c, stock_map)
                put_sim  = sim_spread(edate, ps_short["expiry"],
                                      ps_short["strike"], ps_long["strike"],
                                      "P", put_credit, daily_map_p, stock_map)
                ic_pnl    = call_sim["pnl"] + put_sim["pnl"]
                ic_credit = call_credit + put_credit
                exits = {call_sim["exit"], put_sim["exit"]}
                if "stop_loss" in exits:
                    ic_exit = "stop_loss"
                elif "expiry_loss" in exits:
                    ic_exit = "expiry_loss"
                elif "expiry_win" in exits:
                    ic_exit = "expiry_win"
                else:
                    ic_exit = "profit_take"
                results.append({"strategy": "iron_condor", "edate": edate,
                                "regime": regime_label, "entry_val": ic_credit,
                                "pnl": ic_pnl, "exit": ic_exit,
                                "days": max(call_sim["days"], put_sim["days"]),
                                "exit_date": max(call_sim["exit_date"], put_sim["exit_date"]),
                                **reg})

        # ── 4 & 5. Short + Long straddle (ATM) ───────────────────────────
        atm_call = find_option(day_opts, "C", STRADDLE_DELTA)
        atm_put  = find_option(day_opts, "P", STRADDLE_DELTA)
        if (atm_call is not None and atm_put is not None and
                atm_call["expiry"] == atm_put["expiry"]):
            entry_val = atm_call["mid"] + atm_put["mid"]
            for is_short, label in [(True, "short_straddle"), (False, "long_straddle")]:
                sim = sim_straddle(edate, atm_call["expiry"],
                                   atm_call["strike"], atm_put["strike"],
                                   entry_val, is_short,
                                   daily_map_c, daily_map_p, stock_map)
                results.append({"strategy": label, "edate": edate,
                                "regime": regime_label, "entry_val": entry_val,
                                **sim, **reg})

    df = pd.DataFrame(results)
    df["year"] = pd.to_datetime(df["edate"]).dt.year

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "═" * 92)
    print(f"  {ticker} MULTI-STRATEGY REGIME STUDY  ·  2018–2026  ·  ~20 DTE")
    print("  Credit strategies: 50% profit take / 2× stop   |   Long straddle: +50% take / -40% stop")
    print("═" * 92)

    print_section(df, "OVERALL — all regimes combined")

    all_regimes = ["Bearish_HighIV", "Bearish_LowIV", "Bullish_HighIV", "Bullish_LowIV"]
    for regime in all_regimes:
        rdf = df[df["regime"] == regime]
        if rdf.empty:
            continue
        n_weeks = rdf["edate"].nunique()
        print_section(rdf, f"REGIME: {regime}  ({n_weeks} Fridays)")

    # ── Per-year for top 4 credit strategies ─────────────────────────────────
    print("\n\n" + "═" * 92)
    print("  PER-YEAR BREAKDOWN  ·  All regimes combined")
    print("═" * 92)
    for strat in ["bear_call_spread", "bull_put_spread", "iron_condor", "short_straddle"]:
        sub = df[df["strategy"] == strat]
        if sub.empty:
            continue
        print(f"\n  {strat.upper()}")
        print(f"  {'Year':>6}  {'N':>4}  {'Win%':>6}  {'AvgEntry':>9}  "
              f"{'AvgPnL':>7}  {'ROC%':>6}  {'SumPnL':>8}")
        print("  " + "─" * 58)
        for yr, grp in sub.groupby("year"):
            avg_roc = (grp["pnl"] / grp["entry_val"]).mean() * 100
            print(f"  {yr:>6}  {len(grp):>4}  {(grp['pnl']>0).mean()*100:>5.1f}%  "
                  f"${grp['entry_val'].mean():>8.3f}  ${grp['pnl'].mean():>6.3f}  "
                  f"{avg_roc:>5.1f}%  ${grp['pnl'].sum():>7.3f}")
        avg_roc_tot = (sub["pnl"] / sub["entry_val"]).mean() * 100
        print(f"  {'TOTAL':>6}  {len(sub):>4}  {(sub['pnl']>0).mean()*100:>5.1f}%  "
              f"${sub['entry_val'].mean():>8.3f}  ${sub['pnl'].mean():>6.3f}  "
              f"{avg_roc_tot:>5.1f}%  ${sub['pnl'].sum():>7.3f}")

    # ── Regime distribution ───────────────────────────────────────────────────
    print("\n\n" + "═" * 92)
    print("  REGIME DISTRIBUTION  ·  weeks per regime per year")
    print("═" * 92)
    regime_df = df[df["strategy"] == "bear_call_spread"][["edate", "regime", "year"]].drop_duplicates("edate")
    pivot = regime_df.groupby(["year", "regime"]).size().unstack(fill_value=0)
    print(f"\n  {pivot.to_string()}")
    total_by_regime = regime_df["regime"].value_counts().sort_index()
    print(f"\n  Total weeks: {total_by_regime.to_dict()}")


if __name__ == "__main__":
    main()
