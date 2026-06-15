#!/usr/bin/env python3
"""Sweep the VCB exit on the recommended gate (baseline intraday + RS>=+3 vs SPY).

The signal is fat-tailed (~47% win), so the exit decides how much of the big
winners we keep vs how fast we cut losers. Tests hold-to-close, VWAP, EMA9,
level, fixed trailing stops, and a "VWAP-cut-then-trail" combo. Reports the
payoff shape (PF, avg win vs avg loss, worst trade) not just totals.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb_stop_sweep.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vcb  # noqa: E402

STOPS = ["none", "vwap", "ema9", "level",
         "trail:1.0", "trail:2.0", "trail:3.0",
         "adr:0.20", "adr:0.30", "adr:0.40", "adr:0.50",
         "vwap+trail:2.0", "vwap+adr:0.30", "vwap+adr:0.40"]


def main() -> int:
    sessions = vcb.load_sessions(os.path.join(vcb.DATA_DIR, "*_1min.csv"))
    sessions = {k: v for k, v in sessions.items() if k[0] not in ("SPY", "QQQ")}
    idx = vcb.load_index("SPY")
    adr = vcb.adr_table(sessions)
    avg_adr = sum(d for sym in adr for d in adr[sym].values()) / sum(len(v) for v in adr.values())
    vcb.VOL_MULT, vcb.CONTRACT, vcb.RSI_MIN, vcb.MIN_VWAP_DIST = 2.0, 0.70, 60, 0.0
    vcb.RS_MIN = 3.0
    print(f"\n(mean ADR across cache = {avg_adr:.1f}%/day; adr:K trails K x each symbol's own ADR)")

    print(f"\nVCB stop sweep — 1-min, gate=baseline+RS>=+3 vs SPY, {len(sessions)} sessions "
          f"(SPY/QQQ excluded; selection-biased -> upper bound)\n")
    hdr = (f"{'stop':>14}   {'fires':>5}{'win%':>5}{'avg%':>6}{'total%':>8}{'PF':>6}"
           f"{'avgWin':>7}{'avgLoss':>8}{'worst':>7}{'medCap':>7}")
    print(hdr); print("-" * len(hdr))
    for stop in STOPS:
        rows = [vcb.evaluate(s, dt, df, 1, stop, idx.get(dt), adr.get(s, {}).get(dt))
                for (s, dt), df in sessions.items()]
        fires = [r for r in rows if r["fired"]]
        if not fires:
            print(f"{stop:>14}   {'0':>5}"); continue
        pnl = [r["trade"] for r in fires]
        wins = [p for p in pnl if p > 0]
        losses = [p for p in pnl if p <= 0]
        gw, gl = sum(wins), -sum(losses)
        pf = gw / gl if gl else float("inf")
        caps = sorted(r["captured"] for r in fires if r["captured"] is not None)
        medcap = caps[len(caps) // 2] if caps else 0
        aw = gw / len(wins) if wins else 0
        al = sum(losses) / len(losses) if losses else 0
        pfs = "inf" if pf == float("inf") else f"{pf:.2f}"
        print(f"{stop:>14}   {len(fires):>5}{len(wins)/len(fires)*100:>5.0f}"
              f"{sum(pnl)/len(pnl):>+6.2f}{sum(pnl):>+8.1f}{pfs:>6}"
              f"{aw:>+7.2f}{al:>+8.2f}{min(pnl):>+7.1f}{medcap:>+6}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
