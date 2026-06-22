#!/usr/bin/env python3
"""Per-name trend-health scorecard -- is each holding still in an uptrend or topping?

Objective Stage read (Weinstein/Minervini) from daily bars. NOT a prediction -- a
snapshot of current trend structure that decides whether a stop should be WIDE (let an
intact uptrend run) or TIGHT (protect a gain that's rolling over).

Per name:
  vs20/vs50 : price above (+) or below (-) the 20-EMA / 50-SMA, in %
  stack     : 10EMA > 20EMA > 50SMA aligned (clean uptrend) -> Y/N
  50slope   : 50-SMA now vs 20 bars ago (+ rising / - falling)
  ddHigh    : % off the 1y closing high (0 = at highs)
  r20       : 20-day return
  STAGE     : 2 STRONG / 2 (extended) / 3 WEAKENING / 4 BROKEN
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402
from ib_async import Stock  # noqa: E402

NAMES = ["APLE", "BIRD", "TE", "CIFR", "FCEL", "ARMG", "GLW", "MRNA", "HOOD", "MRVL",
         "RY", "AMD", "VSH", "GEV", "ENTG", "CAT", "GWW", "SOXL", "AMAT", "MU", "NBIS"]


def ema(vals, n):
    k = 2 / (n + 1)
    e = vals[0]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
    return e


def sma_series(vals, n):
    return [sum(vals[i - n + 1:i + 1]) / n for i in range(n - 1, len(vals))]


def classify(price, ema10, ema20, sma50, slope50, dd_high, ext50):
    above50 = price > sma50
    stack = ema10 > ema20 > sma50
    if above50 and slope50 > 0 and stack:
        return "2 STRONG" if ext50 < 25 else "2 EXTENDED"
    if above50 and slope50 >= 0:
        return "2 (consolidating)"
    if not above50 and slope50 < 0:
        return "4 BROKEN"
    return "3 WEAKENING"


def main() -> int:
    ib = connect_ib(client_id=int(os.environ.get("IB_CLIENT_ID", "13")))
    print(f"CONNECTED {ib.managedAccounts()}\n", flush=True)
    hdr = (f"{'sym':5s}{'price':>9}{'vs20%':>7}{'vs50%':>7}{'stack':>6}{'50slope%':>9}"
           f"{'ddHigh%':>8}{'r20%':>7}  STAGE")
    print(hdr); print("-" * len(hdr), flush=True)
    rows = []
    for sym in NAMES:
        c = Stock(sym, "SMART", "USD")
        ib.qualifyContracts(c)
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="1 Y",
                                    barSizeSetting="1 day", whatToShow="TRADES", useRTH=True)
        if not bars or len(bars) < 60:
            print(f"{sym:5s}  insufficient bars ({len(bars) if bars else 0})", flush=True)
            continue
        closes = [b.close for b in bars]
        price = closes[-1]
        e10, e20 = ema(closes[-40:], 10), ema(closes[-50:], 20)
        s50 = sma_series(closes, 50)
        sma50 = s50[-1]
        slope50 = (s50[-1] / s50[-21] - 1) * 100 if len(s50) > 21 else 0.0
        hi = max(closes)
        dd_high = (price / hi - 1) * 100
        r20 = (price / closes[-21] - 1) * 100
        vs20 = (price / e20 - 1) * 100
        vs50 = (price / sma50 - 1) * 100
        stage = classify(price, e10, e20, sma50, slope50, dd_high, vs50)
        stack = "Y" if e10 > e20 > sma50 else "n"
        rows.append((sym, stage))
        print(f"{sym:5s}{price:>9.2f}{vs20:>7.1f}{vs50:>7.1f}{stack:>6}{slope50:>9.1f}"
              f"{dd_high:>8.1f}{r20:>7.1f}  {stage}", flush=True)
    ib.disconnect()
    print("\n--- tally ---", flush=True)
    from collections import Counter
    for k, v in sorted(Counter(s for _, s in rows).items()):
        names = ", ".join(n for n, s in rows if s == k)
        print(f"  {k:18s} {v:>2}: {names}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
