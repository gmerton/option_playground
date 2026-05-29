#!/usr/bin/env python3
"""
IBKR hello-world — proves the ib_async connection and the core API surfaces the
EMA bot will need: connect, account state, live quote, and 1-min bars.

Prereqs (one-time, on the TWS / IB Gateway side):
  - Run TWS or IB Gateway and log into a PAPER account.
  - Enable the API: TWS -> Global Configuration -> API -> Settings ->
    check "Enable ActiveX and Socket Clients", and add 127.0.0.1 to
    "Trusted IPs". Note the socket port.
  - Paper socket port: 7497 (TWS) or 4002 (IB Gateway).

Usage:
  .venv/bin/python3 ibkr_bot/hello.py              # default symbol SPY
  .venv/bin/python3 ibkr_bot/hello.py AAPL
  IB_PORT=7497 .venv/bin/python3 ibkr_bot/hello.py # TWS paper instead of Gateway

Env:
  IB_HOST        (default 127.0.0.1)
  IB_PORT        (default 4002  -- paper IB Gateway; use 7497 for paper TWS)
  IB_CLIENT_ID   (default 11)
  IB_ALLOW_LIVE  (set to 1 to permit live ports 7496/4001; off by default)
"""

from __future__ import annotations

import math
import os
import sys

from ib_async import IB, Stock, util

PAPER_PORTS = {7497, 4002}
LIVE_PORTS = {7496, 4001}


def main() -> int:
    host = os.environ.get("IB_HOST", "127.0.0.1")
    port = int(os.environ.get("IB_PORT", "4002"))
    client_id = int(os.environ.get("IB_CLIENT_ID", "11"))
    symbol = (sys.argv[1] if len(sys.argv) > 1 else "SPY").upper()

    # Safety guard: refuse live ports unless explicitly allowed.
    if port in LIVE_PORTS and os.environ.get("IB_ALLOW_LIVE") != "1":
        print(f"x Port {port} is a LIVE trading port. Refusing to connect.")
        print("  Use a paper port (7497 TWS / 4002 Gateway), or set "
              "IB_ALLOW_LIVE=1 to override.")
        return 1
    if port not in PAPER_PORTS and port not in LIVE_PORTS:
        print(f"! Port {port} is non-standard -- proceeding, but double-check "
              "it points at a PAPER account.")

    ib = IB()
    print(f"-> Connecting to {host}:{port} (clientId={client_id}) ...")
    try:
        ib.connect(host, port, clientId=client_id, timeout=10)
    except Exception as exc:
        print(f"x Could not connect: {exc}")
        print("  Is TWS / IB Gateway running, logged into the PAPER account, "
              "with API socket clients enabled on this port?")
        return 1

    print(f"OK Connected. Server v{ib.client.serverVersion()}, "
          f"accounts: {ib.managedAccounts()}\n")

    # 1. Account state.
    print("-- Account summary --")
    wanted = {"NetLiquidation", "AvailableFunds", "BuyingPower", "TotalCashValue"}
    for av in ib.accountSummary():
        if av.tag in wanted:
            print(f"  {av.tag:<16} {av.value:>14} {av.currency}")

    positions = ib.positions()
    print(f"\n-- Open positions ({len(positions)}) --")
    if not positions:
        print("  (none)")
    for p in positions:
        name = p.contract.localSymbol or p.contract.symbol
        print(f"  {name:<10} qty={p.position:>8}  avgCost={p.avgCost:.2f}")

    # 2. Qualify the contract.
    print(f"\n-- Contract: {symbol} --")
    contract = Stock(symbol, "SMART", "USD")
    if not ib.qualifyContracts(contract):
        print(f"x Could not qualify {symbol}. Check the symbol/exchange.")
        ib.disconnect()
        return 1
    print(f"  conId={contract.conId}  primaryExchange={contract.primaryExchange}")

    # 3. Live quote (falls back to delayed per account permissions).
    print(f"\n-- Quote: {symbol} --")
    ib.reqMarketDataType(1)  # 1 = live
    [ticker] = ib.reqTickers(contract)
    print(f"  bid={ticker.bid}  ask={ticker.ask}  last={ticker.last}")
    if ticker.last is None or math.isnan(ticker.last):
        print("  ! No real-time quote -- likely no live US-equity market-data "
              "subscription. 1-min signals will need real-time data.")

    # 4. Historical 1-min bars (foundation for the 9/20 EMAs).
    print(f"\n-- Last 1-min bars: {symbol} --")
    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr="3600 S",  # last hour
        barSizeSetting="1 min",
        whatToShow="TRADES",
        useRTH=True,
        formatDate=1,
    )
    if not bars:
        print("  (no bars -- market may be closed, or no data permission)")
    else:
        df = util.df(bars)
        df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
        df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
        print(f"  {len(df)} bars; last 5 with EMAs:")
        for _, r in df[["date", "close", "ema9", "ema20"]].tail(5).iterrows():
            print(f"    {str(r['date'])[-14:]}  close={r['close']:.2f}  "
                  f"ema9={r['ema9']:.3f}  ema20={r['ema20']:.3f}")

    ib.disconnect()
    print("\nOK Done -- disconnected cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
