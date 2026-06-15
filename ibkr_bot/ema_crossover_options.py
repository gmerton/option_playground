#!/usr/bin/env python3
"""Option-leverage P&L of the BEST crossover config, modeled with Black-Scholes.

Best config: close>VWAP + open-hour + 12/34 EMAs + RS>=+1 + RVOL>=1.5. Each trade
is an intraday long in the underlying (enter open-hour, exit on the 12/34
down-cross or EOD). Here we re-express every trade as a near-dated CALL bought at
entry and sold at exit, to see how the fat-tailed underlying edge transforms
under leverage.

Why MODELED (not real option bars): a true backtest needs ~242 pacing-limited
IBKR historical pulls and intraday option history that may not reach back to
April for every strike. BS with the ACTUAL entry/exit prices, holding time, and a
stated IV/DTE captures the dominant effects (delta amplification + theta over the
hold) and runs offline. Real-data spot-checks are the follow-up. Spreads are NOT
modeled here (gross, mid-to-mid) -- same basis as the underlying numbers; a
spread haircut is reported separately.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_options.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_options.py --iv 0.5 --dte 5
"""

from __future__ import annotations

import argparse
import glob
import math
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ema_crossover_backtest import backtest  # noqa: E402
from vcb import load_index  # noqa: E402

INDEX_SYMS = {"SPY", "QQQ"}
EARLY_CUTOFF = "09:45"
BEST = {"trend_vwap": True, "entry_before": "10:30", "fast_span": 12,
        "slow_span": 34, "rs_min": 1.0, "rvol_min": 1.5}
YEAR_MIN = 365 * 24 * 60  # calendar minutes per year (theta decays on calendar time)


def _ncdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call(S: float, K: float, T: float, sigma: float, r: float = 0.0) -> float:
    """Black-Scholes call price (r=0 default)."""
    if T <= 0 or sigma <= 0:
        return max(0.0, S - K)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * _ncdf(d1) - K * math.exp(-r * T) * _ncdf(d2)


def bs_delta(S: float, K: float, T: float, sigma: float, r: float = 0.0) -> float:
    if T <= 0 or sigma <= 0:
        return 1.0 if S > K else 0.0
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    return _ncdf(d1)


def strike_for_delta(S: float, T: float, sigma: float, target: float) -> float:
    """Bisect the call strike whose entry delta == target (delta falls as K rises)."""
    lo, hi = 0.2 * S, 3.0 * S
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if bs_delta(S, mid, T, sigma) > target:
            lo = mid          # delta too high -> need higher strike
        else:
            hi = mid
    return 0.5 * (lo + hi)


def mins(hhmm: str) -> int:
    return int(hhmm[:2]) * 60 + int(hhmm[3:])


def stats(rets):
    if not rets:
        return None
    wins = [r for r in rets if r > 0]
    gw = sum(r for r in rets if r > 0)
    gl = -sum(r for r in rets if r <= 0)
    return {
        "n": len(rets), "win": 100 * len(wins) / len(rets),
        "avg": sum(rets) / len(rets), "total": sum(rets),
        "best": max(rets), "worst": min(rets),
        "pf": (gw / gl) if gl else float("inf"),
    }


def opt_return(entry_px, exit_px, hold_min, dte, sigma, target_delta):
    """% return of a target-delta call, bought at entry, sold at exit."""
    T0 = dte / 365.0
    K = strike_for_delta(entry_px, T0, sigma, target_delta)
    prem_in = bs_call(entry_px, K, T0, sigma)
    T1 = max(1e-6, T0 - hold_min / YEAR_MIN)        # theta over the actual hold
    prem_out = bs_call(exit_px, K, T1, sigma)
    if prem_in <= 1e-6:
        return None
    return (prem_out / prem_in - 1) * 100


def collect_trades(glob_pat, min_bars, index):
    idx = load_index(index)
    idx_hhmm = {d: {ts.strftime("%H:%M"): v for ts, v in s.items()}
                for d, s in idx.items()}
    files = sorted(glob.glob(glob_pat))
    sess_by, early = {}, {}
    for f in files:
        sym = os.path.basename(f).split("_")[0]
        if sym in INDEX_SYMS:
            continue
        df = pd.read_csv(f, parse_dates=["time"])
        for day, g in df.groupby(df["time"].dt.date):
            if len(g) < min_bars or str(day) not in idx_hhmm:
                continue
            g = g.sort_values("time").reset_index(drop=True)
            hhmm = g["time"].dt.strftime("%H:%M")
            sess_by[(sym, str(day))] = g
            early.setdefault(sym, {})[str(day)] = g.loc[hhmm <= EARLY_CUTOFF, "volume"].sum()
    rvol = {}
    for sym, byday in early.items():
        for date, ev in byday.items():
            others = [v for d, v in byday.items() if d != date]
            typ = (sum(others) / len(others)) if others else ev
            rvol[(sym, date)] = (ev / typ) if typ > 0 else 1.0

    trades = []
    for (sym, date), g in sess_by.items():
        tr, _ = backtest(g, idx_by_hhmm=idx_hhmm[date],
                         session_rvol=rvol[(sym, date)], **BEST)
        for t in tr:
            trades.append({**t, "sym": sym, "date": date,
                           "hold_min": mins(t["exit_t"]) - mins(t["entry_t"])})
    return trades


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--index", default="SPY")
    ap.add_argument("--iv", type=float, default=0.60, help="annualized IV assumption")
    ap.add_argument("--dte", type=int, default=5, help="days to expiry of the call")
    ap.add_argument("--spread", type=float, default=0.0,
                    help="per-side option spread cost %% (e.g. 1.0 = buy +1%%, sell -1%%)")
    a = ap.parse_args()

    trades = collect_trades(
        a.glob if os.path.isabs(a.glob) else os.path.join(HERE, a.glob),
        a.min_bars, a.index)
    print(f"\nOPTION-LEVERAGE P&L -- best config (VWAP+openhr+12/34+RS>=+1+RVOL>=1.5)")
    print(f"{len(trades)} trades | model: BS call, IV={a.iv:.0%}, DTE={a.dte}, "
          f"r=0, spread={a.spread:.1f}%/side")
    avg_hold = sum(t["hold_min"] for t in trades) / len(trades)
    print(f"avg hold {avg_hold:.0f} min\n")

    und = [t["ret_pct"] for t in trades]
    print(f"  {'vehicle':<22}{'win%':>6}{'avg%':>8}{'total%':>9}"
          f"{'best%':>8}{'worst%':>8}{'PF':>6}{'lev':>6}")
    s = stats(und)
    print(f"  {'underlying (stock)':<22}{s['win']:>6.1f}{s['avg']:>+8.2f}"
          f"{s['total']:>+9.0f}{s['best']:>+8.1f}{s['worst']:>+8.1f}{s['pf']:>6.2f}{'1.0x':>6}")

    for label, td in [("call 0.35Δ (OTM)", 0.35), ("call 0.50Δ (ATM)", 0.50),
                      ("call 0.65Δ (ITM)", 0.65), ("call 0.80Δ (deep ITM)", 0.80)]:
        orets, levs = [], []
        for t in trades:
            o = opt_return(t["entry"], t["exit"], t["hold_min"], a.dte, a.iv, td)
            if o is None:
                continue
            if a.spread:                       # buy higher, sell lower
                o = ((1 + o / 100) * (1 - a.spread / 100) / (1 + a.spread / 100) - 1) * 100
            orets.append(o)
            if abs(t["ret_pct"]) > 1e-9:
                levs.append(o / t["ret_pct"])
        s = stats(orets)
        lev = sum(levs) / len(levs) if levs else 0.0
        print(f"  {label:<22}{s['win']:>6.1f}{s['avg']:>+8.2f}{s['total']:>+9.0f}"
              f"{s['best']:>+8.1f}{s['worst']:>+8.1f}{s['pf']:>6.2f}{lev:>5.1f}x")

    print("\n  lev = avg(option_ret / underlying_ret); worst%% bounded by premium "
          "loss (theta+delta).")
    print("  gross of costs unless --spread; cache = hand-picked movers (UPPER BOUND).\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
