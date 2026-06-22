#!/usr/bin/env python3
"""Read-only evaluation of existing stops through a capital-protection lens.

For each stopped stock position, pulls current price + ATR(14) and computes:
  room%   = (price - stop)/price   -- downside left before the stop fires
  ATRs    = (price - stop)/ATR     -- stop distance in volatility units
            (<~1.5 ATR = whipsaw risk; >~4 ATR = a lot of capital exposed)
  riskNow$= (price - stop)*qty     -- $ at risk from HERE if stopped
  P/L@stop= (stop - cost)*qty      -- realized $ if the stop fills
Flags stops that sit ABOVE current price (would trigger at the open).
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402
from ib_async import Stock  # noqa: E402

# (qty, avg_cost, stop) from the read-only audit
STK = {
    "APLE": (300, 16.50, 16.00), "BIRD": (200, 5.51, 5.50), "TE": (100, 9.65, 8.75),
    "CIFR": (100, 24.33, 27.00), "FCEL": (50, 23.53, 22.50), "ARMG": (50, 52.04, 58.00),
    "GLW": (30, 189.55, 188.50), "MRNA": (20, 63.05, 62.26), "HOOD": (20, 103.36, 102.59),
    "MRVL": (20, 320.00, 300.00), "RY": (15, 202.18, 199.00), "AMD": (10, 527.22, 524.00),
    "VSH": (10, 65.51, 62.50), "GEV": (5, 1064.73, 1060.00), "ENTG": (5, 177.66, 172.00),
    "CAT": (5, 975.83, 975.00), "GWW": (4, 1351.70, 1340.00), "SOXL": (4, 293.70, 244.96),
    "AMAT": (2, 618.66, 570.00), "MU": (2, 1137.16, 1087.00),
}


def atr14(bars):
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = bars[i].high, bars[i].low, bars[i-1].close
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-14:]) / min(14, len(trs)) if trs else None


def main() -> int:
    ib = connect_ib(client_id=int(os.environ.get("IB_CLIENT_ID", "9")))
    print(f"CONNECTED {ib.managedAccounts()}\n", flush=True)
    rows = []
    for sym, (qty, cost, stop) in STK.items():
        c = Stock(sym, "SMART", "USD")
        ib.qualifyContracts(c)
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="30 D",
                                    barSizeSetting="1 day", whatToShow="TRADES", useRTH=True)
        if not bars:
            print(f"{sym}: no bars", flush=True); continue
        px = bars[-1].close
        atr = atr14(bars)
        room = (px - stop) / px * 100
        atrs = (px - stop) / atr if atr else float("nan")
        risk_now = (px - stop) * qty
        pl_stop = (stop - cost) * qty
        rows.append((sym, qty, cost, px, stop, room, atrs, atr / px * 100 if atr else 0,
                     risk_now, pl_stop))
    ib.disconnect()

    rows.sort(key=lambda r: r[5])  # by room% ascending (tightest / triggered first)
    hdr = f"{'sym':5s}{'qty':>5}{'cost':>9}{'price':>9}{'stop':>9}{'room%':>7}{'ATRs':>6}{'ATR%':>6}{'riskNow$':>10}{'P/L@stop$':>11}"
    print(hdr); print("-" * len(hdr))
    tot_risk = tot_pl = 0.0
    for r in rows:
        sym, qty, cost, px, stop, room, atrs, atrpct, risk_now, pl_stop = r
        flag = "  <-- ABOVE MKT (fires at open)" if stop > px else (
               "  <-- tight (<1.5 ATR)" if atrs < 1.5 else (
               "  <-- wide (>4 ATR)" if atrs > 4 else ""))
        print(f"{sym:5s}{qty:>5}{cost:>9.2f}{px:>9.2f}{stop:>9.2f}{room:>7.1f}{atrs:>6.1f}"
              f"{atrpct:>6.1f}{risk_now:>10.0f}{pl_stop:>11.0f}{flag}", flush=True)
        tot_risk += risk_now; tot_pl += pl_stop
    print("-" * len(hdr))
    print(f"TOTAL  $ at risk from current prices: {tot_risk:>8.0f}", flush=True)
    print(f"TOTAL  realized P/L if ALL stops fill: {tot_pl:>8.0f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
