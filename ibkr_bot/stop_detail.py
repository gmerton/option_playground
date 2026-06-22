#!/usr/bin/env python3
"""Detail view for sizing a stop on one name: structure + candidate stop levels.

Prints recent daily bars and, for each candidate stop, the room%, distance in ATRs,
$ at risk from current price, and realized P/L if hit. Read-only.

Usage:
  IB_PORT=4001 IB_ALLOW_LIVE=1 PYTHONPATH=src .venv/bin/python3 -u ibkr_bot/stop_detail.py
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402
from ib_async import Stock  # noqa: E402

# sym -> (qty, avg_cost, current_stop)
POS = {
    "MRVL": (20, 320.00, 300.00),
    "SOXL": (4, 293.70, 244.96),
}


def ema(vals, n):
    k = 2 / (n + 1); e = vals[0]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
    return e


def atr14(bars):
    trs = [max(bars[i].high - bars[i].low, abs(bars[i].high - bars[i-1].close),
               abs(bars[i].low - bars[i-1].close)) for i in range(1, len(bars))]
    return sum(trs[-14:]) / min(14, len(trs))


def main() -> int:
    ib = connect_ib(client_id=int(os.environ.get("IB_CLIENT_ID", "14")))
    print(f"CONNECTED {ib.managedAccounts()}\n", flush=True)
    for sym, (qty, cost, cur_stop) in POS.items():
        c = Stock(sym, "SMART", "USD"); ib.qualifyContracts(c)
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="1 Y",
                                    barSizeSetting="1 day", whatToShow="TRADES", useRTH=True)
        closes = [b.close for b in bars]
        lows = [b.low for b in bars]
        price = closes[-1]
        atr = atr14(bars)
        e20 = ema(closes[-50:], 20)
        sma50 = sum(closes[-50:]) / 50
        swing10 = min(lows[-10:])
        swing20 = min(lows[-20:])
        hi1y = max(closes)

        print(f"========== {sym}  qty={qty}  cost={cost:.2f}  price={price:.2f}  "
              f"({(price/cost-1)*100:+.1f}% vs cost) ==========", flush=True)
        print(f"  1y-high {hi1y:.2f} ({(price/hi1y-1)*100:+.1f}%)  ATR(14) {atr:.2f} "
              f"({atr/price*100:.1f}%/day)", flush=True)
        print(f"  20-EMA {e20:.2f} ({(price/e20-1)*100:+.1f}%)   50-SMA {sma50:.2f} "
              f"({(price/sma50-1)*100:+.1f}%)", flush=True)
        print(f"  swing low 10d {swing10:.2f}   swing low 20d {swing20:.2f}", flush=True)
        print(f"  recent 12 bars (O/H/L/C):", flush=True)
        for b in bars[-12:]:
            print(f"    {b.date}  O{b.open:.2f} H{b.high:.2f} L{b.low:.2f} C{b.close:.2f}",
                  flush=True)

        cands = [
            ("CURRENT", cur_stop),
            ("under 10d swing (-0.3ATR)", swing10 - 0.3 * atr),
            ("under 20d swing (-0.3ATR)", swing20 - 0.3 * atr),
            ("under 20-EMA (-0.5ATR)", e20 - 0.5 * atr),
            ("under 50-SMA (disaster)", sma50 - 0.3 * atr),
        ]
        print(f"  {'candidate':28s}{'stop':>9}{'room%':>7}{'ATRs':>6}{'$risk':>8}{'P/L@hit':>9}",
              flush=True)
        for name, stop in cands:
            room = (price - stop) / price * 100
            atrs = (price - stop) / atr
            risk = (price - stop) * qty
            pl = (stop - cost) * qty
            print(f"  {name:28s}{stop:>9.2f}{room:>7.1f}{atrs:>6.1f}{risk:>8.0f}{pl:>9.0f}",
                  flush=True)
        print(flush=True)
    ib.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
