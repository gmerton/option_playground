#!/usr/bin/env python3
"""Fast VCB stop sweep — same output as vcb_stop_sweep.py, ~14x faster.

The entry (decision frame + find_vcb trigger) is identical across every stop, so
we precompute it ONCE per session and only re-run simulate_exit per stop config.
Gate = baseline intraday + RS>=+3 vs SPY, 1-min.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb_stop_sweep_fast.py
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

    # precompute decision frame + trigger + opportunity label ONCE per session
    prep = []
    for (s, dt), df in sessions.items():
        d = vcb.decision_frame(df, 1, idx.get(dt))
        or_bars = d[d["hhmm"] < vcb.OR_END]
        or_high = or_bars["high"].max() if len(or_bars) else float("nan")
        dlo, dhi, last = d["low"].min(), d["high"].max(), d["close"].iloc[-1]
        close_pos = (last - dlo) / (dhi - dlo) * 100 if dhi > dlo else 0
        ran = (dhi / or_high - 1) * 100 if or_high == or_high else 0
        opp = ran >= vcb.BIG_MOVE and close_pos >= vcb.CLOSE_STRONG
        prep.append((d, vcb.find_vcb(d), adr.get(s, {}).get(dt), opp))

    print(f"\n(mean ADR across cache = {avg_adr:.1f}%/day; adr:K trails K x each symbol's own ADR)")
    print(f"\nVCB stop sweep [FAST] — 1-min, gate=baseline+RS>=+3 vs SPY, {len(sessions)} sessions "
          f"(SPY/QQQ excluded; selection-biased -> upper bound)\n")
    hdr = (f"{'stop':>14}   {'fires':>5}{'win%':>5}{'avg%':>6}{'total%':>8}{'PF':>6}"
           f"{'avgWin':>7}{'avgLoss':>8}{'worst':>7}{'medCap':>7}")
    print(hdr); print("-" * len(hdr))
    for stop in STOPS:
        pnl, caps = [], []
        for d, trig, adr_pct, opp in prep:
            if not trig:
                continue
            i = trig["i"]
            _, xpx, _ = vcb.simulate_exit(d, i, trig["or_high"], stop, adr_pct)
            entry = trig["px"]
            pnl.append((xpx / entry - 1) * 100)
            mf = d["high"].iloc[i:].max() - entry
            if mf > 0:
                caps.append((xpx - entry) / mf * 100)
        if not pnl:
            print(f"{stop:>14}   {'0':>5}"); continue
        wins = [p for p in pnl if p > 0]
        losses = [p for p in pnl if p <= 0]
        gw, gl = sum(wins), -sum(losses)
        pf = gw / gl if gl else float("inf")
        aw = gw / len(wins) if wins else 0
        al = sum(losses) / len(losses) if losses else 0
        medcap = sorted(caps)[len(caps) // 2] if caps else 0
        pfs = "inf" if pf == float("inf") else f"{pf:.2f}"
        print(f"{stop:>14}   {len(pnl):>5}{len(wins)/len(pnl)*100:>5.0f}"
              f"{sum(pnl)/len(pnl):>+6.2f}{sum(pnl):>+8.1f}{pfs:>6}"
              f"{aw:>+7.2f}{al:>+8.2f}{min(pnl):>+7.1f}{medcap:>+6.0f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
