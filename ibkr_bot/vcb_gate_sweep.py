#!/usr/bin/env python3
"""Sweep the VCB gate toward precision (raise win%, cut false fires).

Loads every cached session ONCE, then re-evaluates the 1-min detector under a
grid of gate configs by mutating vcb's module-level params. Reports each config
sorted by win-rate so we can see the precision frontier (and what it costs in
fires/recall). stop=vwap, minutes=1 (the sweep showed 1m is optimal).

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb_gate_sweep.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vcb  # noqa: E402

CONFIGS = [
    # (vol_mult, contract, rsi_min, min_vwap_dist)
    (2.0, 0.70, 60, 0.0),   # baseline
    (3.0, 0.70, 60, 0.0),   # +volume
    (4.0, 0.70, 60, 0.0),
    (3.0, 0.70, 70, 0.0),   # +momentum
    (3.0, 0.50, 70, 0.0),   # +tighter coil
    (3.0, 0.50, 70, 1.0),   # +distance above VWAP
    (4.0, 0.50, 70, 1.0),
    (4.0, 0.40, 70, 1.5),   # strict
    (5.0, 0.40, 70, 1.5),
]


def main() -> int:
    sessions = vcb.load_sessions(os.path.join(vcb.DATA_DIR, "*_1min.csv"))
    print(f"\nVCB gate sweep — 1-min, stop=vwap, {len(sessions)} sessions "
          f"(selection-biased -> upper bound)\n")
    hdr = (f"{'vol':>4}{'contr':>6}{'rsi':>4}{'vwapD':>6}   {'fires':>5}{'win%':>5}"
           f"{'avg%':>6}{'total%':>8}{'PF':>6}{'medCap':>7}{'recall':>8}{'falseF':>7}")
    print(hdr); print("-" * len(hdr))
    out = []
    for vol, contr, rsi, vd in CONFIGS:
        vcb.VOL_MULT, vcb.CONTRACT, vcb.RSI_MIN, vcb.MIN_VWAP_DIST = vol, contr, rsi, vd
        rows = [vcb.evaluate(s, dt, df, 1, "vwap") for (s, dt), df in sessions.items()]
        fires = [r for r in rows if r["fired"]]
        if not fires:
            out.append((vol, contr, rsi, vd, 0, 0, 0, 0, 0, 0, "0/0", 0)); continue
        pnl = [r["trade"] for r in fires]
        wins = [p for p in pnl if p > 0]
        gw, gl = sum(wins), -sum(p for p in pnl if p <= 0)
        pf = gw / gl if gl else float("inf")
        opps = [r for r in rows if r["opportunity"]]
        hit = [r for r in opps if r["fired"] and r["trade"] > 0]
        fp = sum(1 for r in fires if not r["opportunity"])
        caps = sorted(r["captured"] for r in fires if r["captured"] is not None)
        medcap = caps[len(caps) // 2] if caps else 0
        out.append((vol, contr, rsi, vd, len(fires), len(wins) / len(fires) * 100,
                    sum(pnl) / len(pnl), sum(pnl), pf, medcap,
                    f"{len(hit)}/{len(opps)}", fp))
    for r in sorted(out, key=lambda x: x[5]):  # sort by win%
        vol, contr, rsi, vd, n, w, avg, tot, pf, mc, rec, fp = r
        pfs = "inf" if pf == float("inf") else f"{pf:.2f}"
        print(f"{vol:>4.1f}{contr:>6.2f}{rsi:>4}{vd:>6.1f}   {n:>5}{w:>5.0f}"
              f"{avg:>+6.2f}{tot:>+8.1f}{pfs:>6}{mc:>+6}%{rec:>8}{fp:>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
