#!/usr/bin/env python3
"""
Is there ANY stop level / timing that helps the 7-DTE straddle?

straddle_stop_path_2026-09-20.md killed the -50% stop: path-simulated it is worth nothing at mid and
-3.84pp once the exit crossing is counted. But -50% is one arbitrary point. Two levers worth sweeping:

  LEVEL  -- a deeper stop only fires when the position is nearly dead, so it cuts far fewer trades
            that still have time to come back. "down 75%" = exit when worth 25% of cost.
  TIMING -- Gabe's point: theta is brutal on the Wed/Thu before a Friday expiry. A straddle down hard
            with 1-2 days left is mostly time value that is about to vanish, and has very little
            chance of recovering. Gating the stop to DTE <= k targets exactly that window and leaves
            early-cycle dips alone, which is where the -50% stop did its damage.

Everything at the measured realistic entry fill, selling the BID to close (a stopped trade crosses the
spread; it does not settle at intrinsic). Baseline is the same population unstopped.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_straddle_stop_sweep.py \\
           > data/studies/straddle_stop_sweep_2026-09-20.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); pd.set_option("display.width", 230)
from run_straddle_rebuild_wf import load, FOLDS

ENTRY_FILL = 0.50
LEVELS = [0.50, 0.35, 0.25, 0.15, 0.10]        # fraction of cost REMAINING at the exit
DTE_GATES = [None, 3, 2, 1]                     # only allow the stop when DTE <= k


def main():
    d = load().reset_index(drop=True); d["row_id"] = np.arange(len(d), dtype=np.int64)
    q = pd.read_parquet("data/cache/straddle_entry_quotes.parquet")
    w = q.pivot_table(index="row_id", columns="cp", values=["bid", "ask"], aggfunc="last")
    w.columns = [f"{a}_{b.lower()}" for a, b in w.columns]
    d = d.merge(w.reset_index(), on="row_id", how="left")
    d = d[d[["bid_c", "ask_c", "bid_p", "ask_p"]].notna().all(axis=1)]
    d["mid_q"] = (d.bid_c + d.ask_c) / 2 + (d.bid_p + d.ask_p) / 2
    d["ask_q"] = d.ask_c + d.ask_p
    d["payout"] = d.entry_premium * (1 + d.ret_pct_long / 100.0)
    a4 = d[d.pass_both & d.yr.isin(FOLDS)].set_index("row_id")
    cost = a4.mid_q + ENTRY_FILL * (a4.ask_q - a4.mid_q)

    P = pd.read_parquet("data/cache/straddle_stop_paths.parquet")
    g = P.groupby(["row_id", "trade_date"]).agg(n=("cp", "nunique"), bid=("bid", "sum")).reset_index()
    g = g[g.n == 2].copy()
    g["expiry"] = g.row_id.map(pd.to_datetime(a4.expiry))
    g["dte"] = (g.expiry - pd.to_datetime(g.trade_date)).dt.days
    g["cost"] = g.row_id.map(cost)
    g = g.sort_values(["row_id", "trade_date"])

    base = ((a4.payout / cost - 1) * 100)
    print(f"arm 4, folds {FOLDS[0]}-{FOLDS[-1]}: {len(a4):,} trades at the measured entry fill")
    print(f"  NO STOP baseline: {base.mean():+.2f}%   (median {base.median():+.1f}%, win {100*(base>0).mean():.1f}%)")
    print(f"  marks available on {g.row_id.nunique():,} trades | DTE at mark: "
          f"{', '.join(f'{k}d={v}' for k, v in sorted(g.dte.value_counts().items())[:6])}\n")

    rows = []
    for lvl in LEVELS:
        for gate in DTE_GATES:
            m = g.bid <= lvl * g.cost
            if gate is not None:
                m &= g.dte <= gate
            first = g[m].groupby("row_id").first()
            stopped = a4.index.isin(first.index)
            val = np.where(stopped, first["bid"].reindex(a4.index), a4.payout)
            roc = (val / cost - 1) * 100
            per = [roc[a4.yr == y].mean() for y in FOLDS]
            rows.append(dict(down_pct=f"-{100*(1-lvl):.0f}%", dte_gate=("any" if gate is None else f"<={gate}d"),
                             stopped_pct=100 * stopped.mean(), mean=roc.mean(),
                             vs_nostop=roc.mean() - base.mean(),
                             median=roc.median(), win=100 * (roc > 0).mean(),
                             worst_fold=min(per), neg_folds=sum(1 for v in per if v < 0)))
    T = pd.DataFrame(rows)
    print("=" * 112)
    print("  STOP SWEEP — level x timing, realistic entry fill, selling the bid")
    print("=" * 112)
    print(T.round(2).to_string(index=False))
    best = T.loc[T["mean"].idxmax()]
    print(f"\n  best cell: exit at {best.down_pct}, DTE gate {best.dte_gate} -> {best['mean']:+.2f}% "
          f"({best.vs_nostop:+.2f}pp vs no stop), stops {best.stopped_pct:.1f}% of trades")
    better = T[T.vs_nostop > 0]
    print(f"  cells beating NO STOP: {len(better)} of {len(T)}")
    if len(better):
        print(better.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
