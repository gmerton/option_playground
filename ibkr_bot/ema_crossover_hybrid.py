#!/usr/bin/env python3
"""Conviction-entry + crossover-STOP hybrid.

The reframe (selection is the user's edge; the machinery is execution/insurance)
implies: don't let the crossover pick the ENTRY (that's where it whipsaws away
upside) -- enter like a conviction long at the open, and use the crossover/VWAP
only as the disciplined STOP (where its value is). One position per day, no
re-entry.

Entry = the open price (same as buy&hold) so the comparison isolates ONLY the
stop. Stops (checked each bar after entry, exit at that bar's close; else EOD):
  vwap -- close < session VWAP        (buyers lost control)
  ema  -- ema_fast < ema_slow (12/34) (trend rolled over; laggier)
  both -- whichever triggers first

Compared against buy&hold (open->close, no stop) and the FULL crossover (entry on
cross-up too), split by whether the pick WORKED that day (buy&hold>0) vs WRONG.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_hybrid.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_hybrid.py --entry 09:45
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from characterize import add_indicators       # noqa: E402
from ema_crossover_backtest import backtest    # noqa: E402

FAST, SLOW = 12, 34
FULL = {"trend_vwap": True, "entry_before": "10:30", "fast_span": FAST, "slow_span": SLOW}


def prep(sess: pd.DataFrame) -> pd.DataFrame:
    g = add_indicators(sess.copy()).reset_index(drop=True)
    g["ema_f"] = g["close"].ewm(span=FAST, adjust=False).mean()
    g["ema_s"] = g["close"].ewm(span=SLOW, adjust=False).mean()
    g["hhmm"] = g["time"].dt.strftime("%H:%M")
    return g


def hybrid(g: pd.DataFrame, entry_time: str, stop: str):
    """Enter at the open of the first bar >= entry_time; exit on the stop or EOD."""
    cand = g.index[g["hhmm"] >= entry_time]
    if len(cand) == 0:
        return None
    ei = cand[0]
    entry_px = g["open"].iloc[ei]
    last = len(g) - 1
    for i in range(ei, len(g)):
        if i == last:
            return (g["close"].iloc[i] / entry_px - 1) * 100        # EOD flat
        if i > ei:
            below_vwap = g["close"].iloc[i] < g["vwap"].iloc[i]
            below_ema = g["ema_f"].iloc[i] < g["ema_s"].iloc[i]
            hit = ((stop == "vwap" and below_vwap)
                   or (stop == "ema" and below_ema)
                   or (stop == "both" and (below_vwap or below_ema)))
            if hit:
                return (g["close"].iloc[i] / entry_px - 1) * 100
    return (g["close"].iloc[last] / entry_px - 1) * 100


def summ(xs):
    if not xs:
        return "      (none)"
    wins = [x for x in xs if x > 0]
    return (f"n={len(xs):>4}  mean {sum(xs)/len(xs):+6.2f}%  win {100*len(wins)/len(xs):>4.1f}%"
            f"  worst {min(xs):+6.1f}%  total {sum(xs):+7.0f}%")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--entry", default="09:30", help="conviction entry time")
    a = ap.parse_args()

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    cols = ["bh", "hy_vwap", "hy_ema", "hy_both", "full"]
    rows = []
    for f in files:
        df = pd.read_csv(f, parse_dates=["time"])
        for _, sess in df.groupby(df["time"].dt.date):
            if len(sess) < a.min_bars:
                continue
            sess = sess.sort_values("time").reset_index(drop=True)
            g = prep(sess)
            bh = (g["close"].iloc[-1] / g["open"].iloc[0] - 1) * 100
            tr, _ = backtest(sess, **FULL)
            mult = 1.0
            for t in tr:
                mult *= (1 + t["ret_pct"] / 100)
            rows.append({
                "bh": bh,
                "hy_vwap": hybrid(g, a.entry, "vwap"),
                "hy_ema": hybrid(g, a.entry, "ema"),
                "hy_both": hybrid(g, a.entry, "both"),
                "full": (mult - 1) * 100,
            })

    def col(name, subset=None):
        src = subset if subset is not None else rows
        return [r[name] for r in src if r[name] is not None]

    labels = {"bh": "buy&hold (open->close)", "hy_vwap": "hybrid: VWAP stop",
              "hy_ema": "hybrid: EMA stop", "hy_both": "hybrid: VWAP|EMA stop",
              "full": "full crossover"}
    print(f"\nCONVICTION-ENTRY + CROSSOVER-STOP HYBRID   "
          f"[{len(rows)} sessions, entry @ {a.entry}]\n")
    print("  ALL selected sessions:")
    for c in cols:
        print(f"    {labels[c]:<24}: {summ(col(c))}")

    up = [r for r in rows if r["bh"] > 0]
    dn = [r for r in rows if r["bh"] <= 0]
    print(f"\n  Pick WORKED (buy&hold>0; {len(up)} sessions)  -- upside capture:")
    for c in cols:
        print(f"    {labels[c]:<24}: {summ(col(c, up))}")
    print(f"\n  Pick WRONG (buy&hold<=0; {len(dn)} sessions)  -- downside discipline:")
    for c in cols:
        print(f"    {labels[c]:<24}: {summ(col(c, dn))}")

    print("\n  Entry = open price for buy&hold AND the hybrids -> differences are the")
    print("  STOP alone. % on underlying, gross of costs. Cache mover-biased (wrong")
    print("  picks under-sampled -> hybrid downside value UNDERstated).\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
