#!/usr/bin/env python3
"""Does the intraday EXECUTION layer add value over just holding a conviction pick?

Reframe (per the user): stock SELECTION is discretionary/human ("names I strongly
believe go up") and is NOT backtestable. What IS testable is whether the crossover
machinery beats the simplest expression of a conviction long -- buy at the open,
hold to the close. The cache's mover-bias inflates BOTH the strategy and
buy-and-hold, so their DIFFERENCE is a far more honest read of what the execution
layer contributes.

For each session compares:
  BH      -- buy 09:30 open, sell 16:00 close (the conviction long, no machinery)
  STRAT   -- open-hour + 12/34 crossover, exit on down-cross / EOD (machinery;
             multiple intraday round-trips compounded; flat = 0 when no signal)

and -- the key cut -- splits by whether the pick WORKED that day (BH>0) vs went
WRONG (BH<=0), because the execution layer's job is downside discipline on the
wrong picks (which the mover-biased cache under-samples, so this UNDERstates it).

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_vs_hold.py
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ema_crossover_backtest import backtest  # noqa: E402

BASE = {"trend_vwap": True, "entry_before": "10:30", "fast_span": 12, "slow_span": 34}


def summ(xs):
    if not xs:
        return "      (none)"
    wins = [x for x in xs if x > 0]
    return (f"n={len(xs):>4}  mean {sum(xs)/len(xs):+6.2f}%  "
            f"win {100*len(wins)/len(xs):>4.1f}%  "
            f"worst {min(xs):+6.1f}%  best {max(xs):+6.1f}%  total {sum(xs):+7.0f}%")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    a = ap.parse_args()

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    rows = []  # (bh, strat, n_trades)
    for f in files:
        df = pd.read_csv(f, parse_dates=["time"])
        for _, g in df.groupby(df["time"].dt.date):
            if len(g) < a.min_bars:
                continue
            g = g.sort_values("time").reset_index(drop=True)
            bh = (g["close"].iloc[-1] / g["open"].iloc[0] - 1) * 100
            tr, _ = backtest(g, **BASE)
            mult = 1.0
            for t in tr:
                mult *= (1 + t["ret_pct"] / 100)
            strat = (mult - 1) * 100        # compounded intraday round-trips; 0 if flat
            rows.append((bh, strat, len(tr)))

    bh_all = [r[0] for r in rows]
    st_all = [r[1] for r in rows]
    traded = [r for r in rows if r[2] > 0]
    print(f"\nEXECUTION vs BUY-AND-HOLD   [{len(rows)} sessions, "
          f"{len(traded)} had >=1 crossover signal]\n")
    print("  ALL selected sessions:")
    print(f"    buy&hold (open->close) : {summ(bh_all)}")
    print(f"    crossover execution    : {summ(st_all)}")

    # the key cut: pick worked vs pick went wrong (by BH sign)
    up = [r for r in rows if r[0] > 0]
    dn = [r for r in rows if r[0] <= 0]
    print(f"\n  When the pick WORKED that day (buy&hold > 0; {len(up)} sessions):")
    print(f"    buy&hold               : {summ([r[0] for r in up])}")
    print(f"    crossover execution    : {summ([r[1] for r in up])}   <- upside capture")
    print(f"\n  When the pick went WRONG that day (buy&hold <= 0; {len(dn)} sessions):")
    print(f"    buy&hold               : {summ([r[0] for r in dn])}")
    print(f"    crossover execution    : {summ([r[1] for r in dn])}   <- downside discipline")

    # head-to-head
    beat = sum(1 for r in rows if r[1] > r[0])
    dn_beat = sum(1 for r in dn if r[1] > r[0])
    print(f"\n  Execution beat buy&hold in {beat}/{len(rows)} sessions "
          f"({100*beat/len(rows):.0f}%); on WRONG-pick days {dn_beat}/{len(dn)} "
          f"({100*dn_beat/max(1,len(dn)):.0f}%).")
    print("\n  % on underlying, gross of costs. Cache = mover-biased -> wrong-pick days")
    print("  under-sampled, so execution's downside value is UNDERstated here.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
