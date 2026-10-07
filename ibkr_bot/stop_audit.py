#!/usr/bin/env python3
"""READ-ONLY stop audit for the live stock book: what rests at the broker vs where the house stops sit now.

For every STK position: today's close / low, ADR (20-session mean of high/low - 1, incl. today), the resting
protective orders found via reqAllOpenOrders (any client), and the two house levels from stop_definitions.md:
  disaster = 1.0 ADR from today's close -> RESTS with the broker, fires intraday, GTC
  tight    = today's session low        -> JUDGED ON THE CLOSE, never rested; quoted as low/ADR (< 0.5 => widen + cut size)
Sends nothing. Fresh non-zero clientId so it can never bind TWS-created orders.

Usage: IB_PORT=7496 IB_ALLOW_LIVE=1 PYTHONPATH=src .venv/bin/python3 -u ibkr_bot/stop_audit.py
"""
from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402
from ib_async import Stock  # noqa: E402


def main() -> int:
    ib = connect_ib(client_id=int(os.environ.get("IB_CLIENT_ID", "27")))
    print(f"connected {ib.managedAccounts()}  server time {ib.reqCurrentTime()}", flush=True)
    ib.reqAllOpenOrders(); ib.sleep(3)
    orders: dict[str, list] = {}
    for t in ib.openTrades():
        c, o = t.contract, t.order
        orders.setdefault((c.symbol, c.secType), []).append(
            f"{o.action} {o.totalQuantity:g} {o.orderType}@{o.auxPrice if o.orderType in ('STP','STP LMT','TRAIL') else o.lmtPrice:g} {o.tif} id{o.orderId}/c{o.clientId}")
    rows = []
    for p in ib.positions():
        if p.contract.secType != "STK":
            continue
        sym, qty = p.contract.symbol, p.position
        c = Stock(sym, "SMART", "USD"); ib.qualifyContracts(c)
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr="40 D", barSizeSetting="1 day",
                                    whatToShow="TRADES", useRTH=True)
        if not bars:
            rows.append(dict(sym=sym, qty=qty, note="no bars")); continue
        b = pd.DataFrame([dict(date=x.date, high=x.high, low=x.low, close=x.close) for x in bars])
        adr = float((b.high / b.low - 1).tail(20).mean() * 100)
        last = b.iloc[-1]
        sgn = 1 if qty > 0 else -1
        disaster = last.close * (1 - sgn * adr / 100)
        tight = last.low if sgn > 0 else last.high
        rows.append(dict(sym=sym, qty=qty, cost=round(p.avgCost, 2), close=round(last.close, 2), bar_date=str(last.date),
                         adr_pct=round(adr, 1), disaster=round(disaster, 2), risk_at_disaster=round(abs(qty) * (last.close - disaster) * sgn, 0),
                         tight=round(tight, 2), tight_adr=round(abs(last.close - tight) / last.close / (adr / 100), 2),
                         resting=" | ".join(orders.get((sym, "STK"), [])) or "NONE"))
    ib.disconnect()
    df = pd.DataFrame(rows).sort_values("sym")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
    print(df.to_string(index=False))
    other = {k: v for k, v in orders.items() if k[1] != "STK"}
    if other:
        print("\nnon-stock resting orders:")
        for k, v in other.items():
            print(" ", k, v)
    os.makedirs("data/studies/logs", exist_ok=True)
    df.to_csv("data/studies/logs/stop_audit_latest.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
