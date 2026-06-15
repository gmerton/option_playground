#!/usr/bin/env python3
"""Multi-day backtest of PHB vs MFR over the cached 1-min files.

Reads the multi-day CSVs in data/ (each may hold several sessions), splits by
trading date, and runs both strategies on every (symbol, day):

  PHB  -- power_hour_trigger.find_trigger (scan 14:30-15:30, >=1.0% above VWAP),
          exited two ways for comparison: VWAP/flat-by-close and 9/21 EMA cross.
  MFR  -- morning flush (low <= MORNING_END, >= MIN_DROP from open, RSI oversold)
          then VWAP reclaim; exit at close unless a close undercuts the flush low.

The MFR finder mirrors the live detect_mfr (low-so-far prefix logic) so a fire
here equals a live alert. Prints per-day breakdown + per-strategy totals.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/mday_backtest.py [--glob 'data/*_1min.csv']
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from characterize import add_indicators                       # noqa: E402
import power_hour_trigger as pht                               # noqa: E402
import signal_monitor as sm                                   # noqa: E402

# PHB live params
pht.SCAN_START, pht.SCAN_END, pht.MIN_VWAP_DIST = "14:30", "15:30", 1.0


def phb_trade(sess: pd.DataFrame, stop: str):
    trig = pht.find_trigger(sess)
    if not trig:
        return None
    _, xpx, _ = pht.simulate_exit(sess, trig["i"], stop)
    return (xpx / trig["px"] - 1) * 100


def mfr_trade(sess: pd.DataFrame):
    """First morning-flush VWAP reclaim (faithful to live detect_mfr), then
    exit at close unless a later close undercuts the flush low."""
    hhmm = sess["time"].dt.strftime("%H:%M")
    o = sess["open"].iloc[0]
    low = sess["low"].values
    close = sess["close"].values
    vwap = sess["vwap"].values
    rsi = sess["rsi"].values
    cur_min, cur_min_i = float("inf"), 0
    for i in range(len(sess)):
        if low[i] < cur_min:
            cur_min, cur_min_i = low[i], i
        if i < 2 or i <= cur_min_i:
            continue
        if hhmm.iloc[cur_min_i] > sm.MFR_MORNING_END:        # flush must be morning
            continue
        drop = (low[cur_min_i] / o - 1) * 100
        if not (drop <= sm.MFR_MIN_DROP and rsi[cur_min_i] <= sm.MFR_MAX_RSI):
            continue
        if close[i - 1] <= vwap[i - 1] and close[i] > vwap[i]:   # VWAP reclaim
            flush_low = low[cur_min_i]
            entry = close[i]
            exit_px = close[-1]
            for j in range(i + 1, len(sess)):
                if close[j] < flush_low:                      # invalidation
                    exit_px = close[j]
                    break
            return (exit_px / entry - 1) * 100
    return None


def stats(pnls: list[float]) -> str:
    if not pnls:
        return "no trades"
    wins = [p for p in pnls if p > 0]
    gw = sum(wins); gl = -sum(p for p in pnls if p <= 0)
    pf = gw / gl if gl else float("inf")
    return (f"{len(pnls):>3} trades  win {len(wins)/len(pnls)*100:>3.0f}%  "
            f"avg {sum(pnls)/len(pnls):+5.2f}%  total {sum(pnls):+7.2f}%  PF {pf:.2f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    a = ap.parse_args()

    # collect (date -> {phb_vwap:[], phb_ema:[], mfr:[]})
    by_day: dict = {}
    files = sorted(glob.glob(a.glob))
    for f in files:
        sym = os.path.basename(f).split("_")[0]
        df = pd.read_csv(f, parse_dates=["time"])
        for day, g in df.groupby(df["time"].dt.date):
            if len(g) < 30:
                continue
            sess = add_indicators(g.sort_values("time").reset_index(drop=True))
            d = by_day.setdefault(str(day), {"phb_vwap": [], "phb_ema": [], "mfr": []})
            for key, val in (("phb_vwap", phb_trade(sess, "vwap")),
                             ("phb_ema", phb_trade(sess, "ema_cross")),
                             ("mfr", mfr_trade(sess))):
                if val is not None:
                    d[key].append(val)

    days = sorted(by_day)
    print(f"\nMulti-day backtest: {len(days)} sessions, {len(files)} symbols "
          f"({days[0]} .. {days[-1]})\n")
    hdr = f"{'date':<12}{'PHBn':>5}{'PHB close%':>12}{'PHB 9/21%':>11}{'MFRn':>6}{'MFR%':>9}"
    print(hdr); print("-" * len(hdr))
    agg = {"phb_vwap": [], "phb_ema": [], "mfr": []}
    for day in days:
        d = by_day[day]
        for k in agg:
            agg[k] += d[k]
        print(f"{day:<12}{len(d['phb_vwap']):>5}{sum(d['phb_vwap']):>+11.1f}%"
              f"{sum(d['phb_ema']):>+10.1f}%{len(d['mfr']):>6}{sum(d['mfr']):>+8.1f}%")

    print("\n=== TOTALS ===")
    print(f"PHB  exit=VWAP/close : {stats(agg['phb_vwap'])}")
    print(f"PHB  exit=9/21 cross : {stats(agg['phb_ema'])}")
    print(f"MFR  flush reclaim   : {stats(agg['mfr'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
