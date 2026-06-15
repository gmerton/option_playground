#!/usr/bin/env python3
"""Isolate relative strength as a VCB discriminator.

Holds the intraday gate at BASELINE (loose: vol>=2, contract<=0.7, rsi>=60,
vwapDist=0) and 1-min/vwap-stop, then sweeps ONLY the RS threshold (name's
ret-from-open minus index ret-from-open, in pts, at the breakout bar). If win%
/PF climb past the ~48% ceiling the intraday knobs hit, RS is the lever.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb_rs_sweep.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vcb  # noqa: E402

RS_GRID = [None, -2.0, 0.0, 1.0, 2.0, 3.0, 5.0]


def main() -> int:
    sessions = vcb.load_sessions(os.path.join(vcb.DATA_DIR, "*_1min.csv"))
    idx = vcb.load_index("SPY")
    if not idx:
        print("no SPY index data; run fetch_intraday.py SPY --days 40"); return 1
    # baseline loose intraday gate (best PF in the gate sweep)
    vcb.VOL_MULT, vcb.CONTRACT, vcb.RSI_MIN, vcb.MIN_VWAP_DIST = 2.0, 0.70, 60, 0.0

    print(f"\nVCB relative-strength sweep — 1-min, stop=vwap, baseline intraday gate, "
          f"{len(sessions)} sessions vs SPY")
    print("(selection-biased cache -> upper bound)\n")
    hdr = (f"{'RS_min':>8}   {'fires':>5}{'win%':>5}{'avg%':>6}{'total%':>8}{'PF':>6}"
           f"{'medCap':>7}{'recall':>8}{'falseF':>7}")
    print(hdr); print("-" * len(hdr))
    for rs in RS_GRID:
        vcb.RS_MIN = rs
        rows = [vcb.evaluate(s, dt, df, 1, "vwap", idx.get(dt)) for (s, dt), df in sessions.items()]
        fires = [r for r in rows if r["fired"]]
        label = "off" if rs is None else f"{rs:+.1f}"
        if not fires:
            print(f"{label:>8}   {'0':>5}"); continue
        pnl = [r["trade"] for r in fires]
        wins = [p for p in pnl if p > 0]
        gw, gl = sum(wins), -sum(p for p in pnl if p <= 0)
        pf = gw / gl if gl else float("inf")
        opps = [r for r in rows if r["opportunity"]]
        hit = [r for r in opps if r["fired"] and r["trade"] > 0]
        fp = sum(1 for r in fires if not r["opportunity"])
        caps = sorted(r["captured"] for r in fires if r["captured"] is not None)
        medcap = caps[len(caps) // 2] if caps else 0
        pfs = "inf" if pf == float("inf") else f"{pf:.2f}"
        print(f"{label:>8}   {len(fires):>5}{len(wins)/len(fires)*100:>5.0f}"
              f"{sum(pnl)/len(pnl):>+6.2f}{sum(pnl):>+8.1f}{pfs:>6}{medcap:>+6}%"
              f"{f'{len(hit)}/{len(opps)}':>8}{fp:>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
