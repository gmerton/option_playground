#!/usr/bin/env python3
"""Option-level version of buy&hold vs stop vs crossover.

On the UNDERLYING, holding a conviction pick beat every stop/trigger (stops clip
winners more than they save on losers, given a decent hit rate). But the vehicle
is a near-dated CALL: holding through a down day bleeds delta + THETA, while a
stop exits early (less delta loss, less theta). So the stop's downside discipline
may be worth far more on calls than on the stock -- possibly inverting the verdict.

Each variant's intraday underlying trade(s) are re-expressed as a call bought at
entry / sold at exit (BS, same model as ema_crossover_options). Crossover's
multiple round-trips are compounded within the session. Split by whether the pick
worked that day (underlying open->close > 0).

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_hybrid_options.py
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/ema_crossover_hybrid_options.py --delta 0.35 --iv 0.6
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from characterize import add_indicators            # noqa: E402
from ema_crossover_backtest import backtest         # noqa: E402
from ema_crossover_options import opt_return        # noqa: E402

FAST, SLOW = 12, 34
FULL = {"trend_vwap": True, "entry_before": "10:30", "fast_span": FAST, "slow_span": SLOW}


def prep(sess):
    g = add_indicators(sess.copy()).reset_index(drop=True)
    g["ema_f"] = g["close"].ewm(span=FAST, adjust=False).mean()
    g["ema_s"] = g["close"].ewm(span=SLOW, adjust=False).mean()
    g["hhmm"] = g["time"].dt.strftime("%H:%M")
    g["mod"] = g["time"].dt.hour * 60 + g["time"].dt.minute
    return g


def bh_trade(g):
    return (g["open"].iloc[0], g["close"].iloc[-1],
            int(g["mod"].iloc[-1] - g["mod"].iloc[0]))


def hybrid_trade(g, entry_time, stop):
    cand = g.index[g["hhmm"] >= entry_time]
    if len(cand) == 0:
        return None
    ei = cand[0]
    entry_px, em0 = g["open"].iloc[ei], g["mod"].iloc[ei]
    last = len(g) - 1
    for i in range(ei, len(g)):
        if i == last:
            break
        if i > ei:
            below_vwap = g["close"].iloc[i] < g["vwap"].iloc[i]
            below_ema = g["ema_f"].iloc[i] < g["ema_s"].iloc[i]
            if ((stop == "vwap" and below_vwap) or (stop == "ema" and below_ema)
                    or (stop == "both" and (below_vwap or below_ema))):
                return (entry_px, g["close"].iloc[i], int(g["mod"].iloc[i] - em0))
    return (entry_px, g["close"].iloc[last], int(g["mod"].iloc[last] - em0))


def opt_session(trades, dte, iv, delta):
    """Compound option round-trips within a session -> one % return (None if no data)."""
    mult, any_ok = 1.0, False
    for (epx, xpx, hold) in trades:
        o = opt_return(epx, xpx, max(1, hold), dte, iv, delta)
        if o is None:
            continue
        mult *= (1 + o / 100)
        any_ok = True
    return (mult - 1) * 100 if any_ok else None


def summ(xs):
    if not xs:
        return "      (none)"
    wins = [x for x in xs if x > 0]
    return (f"n={len(xs):>4}  mean {sum(xs)/len(xs):+7.2f}%  win {100*len(wins)/len(xs):>4.1f}%"
            f"  worst {min(xs):+6.1f}%  total {sum(xs):+8.0f}%")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=os.path.join(HERE, "data", "*_1min.csv"))
    ap.add_argument("--min-bars", type=int, default=200)
    ap.add_argument("--entry", default="09:30")
    ap.add_argument("--delta", type=float, default=0.50)
    ap.add_argument("--iv", type=float, default=0.60)
    ap.add_argument("--dte", type=int, default=5)
    a = ap.parse_args()

    files = sorted(glob.glob(a.glob if os.path.isabs(a.glob)
                             else os.path.join(HERE, a.glob)))
    cols = ["bh", "hy_vwap", "hy_both", "full"]
    rows = []
    for f in files:
        df = pd.read_csv(f, parse_dates=["time"])
        for _, sess in df.groupby(df["time"].dt.date):
            if len(sess) < a.min_bars:
                continue
            sess = sess.sort_values("time").reset_index(drop=True)
            g = prep(sess)
            bh_stock = (g["close"].iloc[-1] / g["open"].iloc[0] - 1) * 100
            tr, _ = backtest(sess, **FULL)
            xtr = [(t["entry"], t["exit"],
                    (int(t["exit_t"][:2]) * 60 + int(t["exit_t"][3:]))
                    - (int(t["entry_t"][:2]) * 60 + int(t["entry_t"][3:]))) for t in tr]
            hv, hb = hybrid_trade(g, a.entry, "vwap"), hybrid_trade(g, a.entry, "both")
            rows.append({
                "sign": bh_stock,
                "bh": opt_session([bh_trade(g)], a.dte, a.iv, a.delta),
                "hy_vwap": opt_session([hv], a.dte, a.iv, a.delta) if hv else None,
                "hy_both": opt_session([hb], a.dte, a.iv, a.delta) if hb else None,
                "full": opt_session(xtr, a.dte, a.iv, a.delta) if xtr else 0.0,
            })

    labels = {"bh": "buy&hold CALL (open->close)", "hy_vwap": "hybrid CALL: VWAP stop",
              "hy_both": "hybrid CALL: VWAP|EMA stop", "full": "full crossover CALL"}

    def col(name, subset):
        return [r[name] for r in subset if r[name] is not None]

    up = [r for r in rows if r["sign"] > 0]
    dn = [r for r in rows if r["sign"] <= 0]
    print(f"\nOPTION-LEVEL: buy&hold vs stop vs crossover   "
          f"[{a.delta:.2f}Δ call, IV={a.iv:.0%}, DTE={a.dte}, {len(rows)} sessions]\n")
    print("  ALL selected sessions:")
    for c in cols:
        print(f"    {labels[c]:<28}: {summ(col(c, rows))}")
    print(f"\n  Pick WORKED (underlying open->close > 0; {len(up)} sessions):")
    for c in cols:
        print(f"    {labels[c]:<28}: {summ(col(c, up))}")
    print(f"\n  Pick WRONG (underlying open->close <= 0; {len(dn)} sessions):")
    for c in cols:
        print(f"    {labels[c]:<28}: {summ(col(c, dn))}")
    print("\n  Per-session % on the CALL premium (crossover round-trips compounded).")
    print("  gross of spreads; cache mover-biased (wrong picks under-sampled).\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
