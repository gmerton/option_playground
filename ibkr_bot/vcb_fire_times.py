#!/usr/bin/env python3
"""Time-of-day distribution of VCB trigger fires across the cache.

Recommended config: 1-min, baseline intraday gate + RS>=+3 vs SPY. One fire per
session (first qualifying bar). Buckets fire times by 30 min and splits by
winner/loser (hold-to-close P&L) to see if early vs late fires differ.

  PYTHONPATH=src .venv/bin/python3 ibkr_bot/vcb_fire_times.py
"""
from __future__ import annotations

import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vcb  # noqa: E402


def bucket(hhmm: str) -> str:
    h, m = int(hhmm[:2]), int(hhmm[3:])
    half = 0 if m < 30 else 30
    return f"{h:02d}:{half:02d}"


def main() -> int:
    sessions = vcb.load_sessions(os.path.join(vcb.DATA_DIR, "*_1min.csv"))
    sessions = {k: v for k, v in sessions.items() if k[0] not in ("SPY", "QQQ")}
    idx = vcb.load_index("SPY")
    vcb.VOL_MULT, vcb.CONTRACT, vcb.RSI_MIN, vcb.MIN_VWAP_DIST = 2.0, 0.70, 60, 0.0
    vcb.RS_MIN = 3.0

    times, win_b, loss_b = [], Counter(), Counter()
    for (s, dt), df in sessions.items():
        d = vcb.decision_frame(df, 1, idx.get(dt))
        trig = vcb.find_vcb(d)
        if not trig:
            continue
        b = bucket(trig["time"])
        times.append(trig["time"])
        # hold-to-close P&L to tag winner/loser
        last = d["close"].iloc[-1]
        (win_b if last >= trig["px"] else loss_b)[b] += 1

    if not times:
        print("no fires"); return 0
    n = len(times)
    hhmm_sorted = sorted(times)
    median = hhmm_sorted[n // 2]
    counts = Counter(bucket(t) for t in times)

    print(f"\nVCB fire-time distribution — {n} fires over {len(sessions)} sessions "
          f"(RS>=+3, 1-min)\n")
    print(f"{'window':>12}{'fires':>7}{'share':>8}{'cum%':>7}   {'win/loss (hold-to-close)':<26}")
    print("-" * 70)
    cum = 0
    for b in sorted(counts):
        c = counts[b]
        cum += c
        bar = "#" * round(c / n * 100)
        print(f"{b+'-'+bucket_end(b):>12}{c:>7}{c/n*100:>7.0f}%{cum/n*100:>6.0f}%   "
              f"{win_b[b]:>3}W/{loss_b[b]:>3}L  {bar}")
    print(f"\nmedian fire time: {median}   earliest: {hhmm_sorted[0]}   latest: {hhmm_sorted[-1]}")
    before_1130 = sum(1 for t in times if t < "11:30")
    print(f"fires before 11:30: {before_1130}/{n} ({before_1130/n*100:.0f}%)")
    return 0


def bucket_end(b: str) -> str:
    h, m = int(b[:2]), int(b[3:])
    return f"{h:02d}:59" if m == 30 else f"{h:02d}:29"


if __name__ == "__main__":
    raise SystemExit(main())
