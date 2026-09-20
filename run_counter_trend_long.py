#!/usr/bin/env python3
"""
Breitstein test 3: the capitulation counter-trend LONG with a prior-bar-high trigger (ZOHG-OnQuos), A/B'd
against the same trigger without the extension gate. Mirror image of the bouncy-ball short the harness
killed (-0.34R daily vs control +0.34/+0.48).

Pre-registered spec (principles/trend-definition-and-counter-trend-entry.md, "Harness spec"):
  A  setup (as of yesterday): (ema20 - close) / (close * ADR/100) >= K  [K = 3 primary; 2 / 5 sweeps]
                              and close < close[-5]                    (still in the down leg)
     trigger (today):         close > high[-1]                         (break of the prior bar high)
     stop:                    the signal bar's low (primary); sweep: the flush low = min(low[-1], low)
  B  control gate: the same trigger + close < close[-5], NO extension precondition
  V  volume arm: A + flush-bar dolvol >= 2x its trailing-20 mean (capitulation per the writeups file)
  entry next open, 10 bps; harness arms stop_hold / t1R / t2R / trail_bar / ema20; hold 5 (sweep 10)
  control = same name, random session, same month.  Ledger rows: A(K=3) and B only.
  The comparison he provokes: trail_bar (his trail) vs ema20 (our best arm).

Intraday VWAP-veto arm (optional in the spec) NOT run here -- parked.

Usage:
  PYTHONPATH=src .venv/bin/python3 run_counter_trend_long.py > data/studies/breitstein_tests/logs/counter_trend_long_<date>.log
"""
from __future__ import annotations

import warnings
from datetime import date

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from lib.studies.pattern_test import daily_signals, load_panel, run_daily

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
TODAY = date.today().isoformat()


def masks(P, dolvol: pd.DataFrame):
    ext = (P.ema20 - P.close) / (P.close * P.adr / 100.0)
    down = P.close < P.close.shift(5)
    trig = (P.close > P.high.shift(1)) & P.elig
    vol2x = dolvol >= 2 * dolvol.shift(1).rolling(20).mean()
    return ext, down, trig, vol2x


def build(P, ext, down, trig, vol2x, kind: str, K: float, stop: str):
    if kind == "A":
        hit = (ext.shift(1) >= K) & down.shift(1) & trig
    elif kind == "B":
        hit = down.shift(1) & trig & ~(ext.shift(1) >= K)          # trigger WITHOUT the extension (disjoint from A)
    elif kind == "Ball":
        hit = down.shift(1) & trig                                 # trigger, any extension (his rule as stated)
    elif kind == "V":
        hit = (ext.shift(1) >= K) & down.shift(1) & trig & vol2x.shift(1)
    else:
        raise ValueError(kind)
    st = P.low if stop == "signal" else np.minimum(P.low, P.low.shift(1))
    return hit, st


def main():
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    P = load_panel()
    dolvol = raw.pivot(index="date", columns="ticker", values="dolvol").sort_index().reindex(P.close.index)
    ext, down, trig, vol2x = masks(P, dolvol)
    e = ext.shift(1).where(down.shift(1) & trig)
    print(f"panel {P.close.shape}; extension below the 20 EMA on trigger days (ADR units): "
          f"p50 {e.stack().quantile(.5):.2f} p90 {e.stack().quantile(.9):.2f} p99 {e.stack().quantile(.99):.2f}")

    runs = [  # kind, K, stop, hold, ledger, label
        ("A", 3.0, "signal", 5, True,  "counter-trend long: >=3 ADR below 20 EMA + prior-bar-high break"),
        ("B", 3.0, "signal", 5, True,  "prior-bar-high break in a down leg, <3 ADR below 20 EMA (no extension gate)"),
        ("Ball", 3.0, "signal", 5, False, "prior-bar-high break in a down leg, any extension"),
        ("A", 2.0, "signal", 5, False, "counter-trend long: >=2 ADR below 20 EMA"),
        ("A", 5.0, "signal", 5, False, "counter-trend long: >=5 ADR below 20 EMA"),
        ("A", 3.0, "flush", 5, False,  "counter-trend long: >=3 ADR, stop = flush low (min of the two bars)"),
        ("V", 3.0, "signal", 5, False, "counter-trend long: >=3 ADR + flush-bar dolvol >= 2x 20d mean"),
        ("A", 3.0, "signal", 10, False, "counter-trend long: >=3 ADR, hold 10"),
    ]
    rows = []
    for kind, K, stop, hold, ledger, label in runs:
        hit, st = build(P, ext, down, trig, vol2x, kind, K, stop)
        S = daily_signals(hit, stop=st, side="long")
        print(f"\n\n================ {label} | {len(S):,} raw signals ================")
        tab = run_daily(label, lambda _P, h=hit, s=st: daily_signals(h, stop=s, side="long"), hold=hold, panel=P,
                        ledger=ledger, note="Breitstein test 3" + ("" if kind == "A" else f"; {kind} arm of the A/B"))
        if tab is None or len(tab) == 0:
            continue
        rows.append(dict(arm=label[:70], K=K, stop=stop, hold=hold, n=int(tab.n.max()),
                         trail_bar=tab.loc["trail_bar", "meanR"], ema20=tab.loc["ema20", "meanR"],
                         t1R=tab.loc["t1R", "meanR"], stop_hold=tab.loc["stop_hold", "meanR"],
                         best=tab.meanR.idxmax(), best_meanR=tab.meanR.max(),
                         best_ctrl=tab.loc[tab.meanR.idxmax(), "ctrl"], best_t=tab.loc[tab.meanR.idxmax(), "t"],
                         edge_best=tab.edge.max(), win_best=tab.loc[tab.meanR.idxmax(), "win"]))
    S = pd.DataFrame(rows)
    print("\n\n################ SUMMARY (mean R per arm; ctrl/t/edge for the best arm) ################")
    print(S.round(3).to_string(index=False))
    S.to_csv(pt.REPO / f"data/studies/breitstein_tests/counter_trend_long_summary_{TODAY}.csv", index=False)


if __name__ == "__main__":
    main()
