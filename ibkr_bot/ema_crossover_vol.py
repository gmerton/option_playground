#!/usr/bin/env python3
"""Does the 9/20-EMA crossover work better on more-volatile sessions?

For every (symbol, day) session in the cache, measures two kinds of intraday
volatility and runs the crossover, then buckets the pooled trades by the
session's volatility quintile and reports the edge per bucket:

  range%  -- (high-low)/open*100  : how much MOVE was available that day
  chop    -- path/net  = sum(|1-min returns|) / |close-open|  : whipsaw-iness
             (high chop = lots of motion, little net progress = crossover poison)

The point: range and chop are different. A crossover should LIKE high range
(trend to ride) but HATE high chop (whipsaw). Splitting them tells us which kind
of "volatility" actually helps.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_vol.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_vol.py --config "VWAP + before 11:30"
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ema_crossover_backtest import PRESETS, backtest  # noqa: E402


def session_vol(g: pd.DataFrame) -> tuple[float, float]:
    o = g["open"].iloc[0]
    rng = (g["high"].max() - g["low"].min()) / o * 100
    rets = g["close"].pct_change().abs().sum() * 100      # path length in %
    net = abs(g["close"].iloc[-1] / o - 1) * 100
    chop = rets / net if net > 1e-9 else float("inf")
    return rng, chop


def stats(pnls: list[float]) -> dict:
    wins = [p for p in pnls if p > 0]
    gw = sum(wins)
    gl = -sum(p for p in pnls if p <= 0)
    return {
        "n": len(pnls),
        "win": 100 * len(wins) / len(pnls) if pnls else 0.0,
        "total": sum(pnls),
        "avg": sum(pnls) / len(pnls) if pnls else 0.0,
        "pf": (gw / gl) if gl else float("inf"),
    }


def quintile_report(label: str, rows: list[tuple[float, list[float]]]) -> None:
    """rows = [(session_metric, [trade pnls]), ...]; bucket by metric quintile."""
    rows = sorted(rows, key=lambda r: r[0])
    n = len(rows)
    print(f"\n  by {label} (low -> high), quintiles of sessions:")
    print(f"    {'bucket':<9}{'metric rng':>16}{'sess':>6}{'trades':>8}"
          f"{'win%':>7}{'avg%':>7}{'PF':>6}{'total%':>9}")
    for q in range(5):
        lo_i, hi_i = q * n // 5, (q + 1) * n // 5
        chunk = rows[lo_i:hi_i]
        if not chunk:
            continue
        m_lo, m_hi = chunk[0][0], chunk[-1][0]
        pnls = [p for _, ps in chunk for p in ps]
        s = stats(pnls)
        pf = "inf" if s["pf"] == float("inf") else f"{s['pf']:.2f}"
        print(f"    Q{q + 1:<8}{m_lo:>7.1f}-{m_hi:<7.1f}{len(chunk):>6}"
              f"{s['n']:>8}{s['win']:>7.1f}{s['avg']:>+7.2f}{pf:>6}{s['total']:>+9.1f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--config", default="baseline (no filter)",
                    help="which PRESET filter to evaluate")
    a = ap.parse_args()

    kw = dict(PRESETS).get(a.config)
    if kw is None:
        print(f"unknown config '{a.config}'. options: {[n for n, _ in PRESETS]}")
        return 2

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    by_range: list[tuple[float, list[float]]] = []
    by_chop: list[tuple[float, list[float]]] = []
    sessions = 0
    for f in files:
        df = pd.read_csv(f, parse_dates=["time"])
        for day, g in df.groupby(df["time"].dt.date):
            if len(g) < a.min_bars:
                continue
            g = g.sort_values("time").reset_index(drop=True)
            sessions += 1
            rng, chop = session_vol(g)
            trades, _ = backtest(g, **kw)
            pnls = [t["ret_pct"] for t in trades]
            by_range.append((rng, pnls))
            if chop != float("inf"):
                by_chop.append((chop, pnls))

    print(f"\n9/20 EMA crossover vs intraday volatility  [config: {a.config}]")
    print(f"{sessions} sessions")
    quintile_report("RANGE%  (high-low)/open -- move available", by_range)
    quintile_report("CHOP  path/net -- whipsaw-iness", by_chop)
    print("\n  gross of costs; % on underlying; cache = hand-picked movers.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
