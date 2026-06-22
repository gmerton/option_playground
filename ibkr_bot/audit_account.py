#!/usr/bin/env python3
"""Read-only audit of the connected IB account: positions + open orders.

Usage (LIVE Gateway on 4001 requires the live override):
  IB_PORT=4001 IB_ALLOW_LIVE=1 PYTHONPATH=src .venv/bin/python3 -u ibkr_bot/audit_account.py

Reads only -- never places or cancels anything. Uses a non-zero clientId (reads work on
any id; clientId 0 is reserved for cancels of manual/TWS orders).
"""
from __future__ import annotations
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402


def _opt_tag(c):
    if c.secType == "OPT":
        return f"{c.symbol} {c.lastTradeDateOrContractMonth} {c.right}{c.strike}"
    return f"{c.symbol} {c.secType}"


def main() -> int:
    cid = int(os.environ.get("IB_CLIENT_ID", "7"))
    print(f"Connecting (clientId={cid}) ...", flush=True)
    ib = connect_ib(client_id=cid)
    print(f"CONNECTED: {ib.isConnected()} | accounts: {ib.managedAccounts()}", flush=True)

    ib.reqAllOpenOrders()
    ib.sleep(2.0)

    print("\n=== POSITIONS ===", flush=True)
    poss = ib.positions()
    if not poss:
        print("  (none)", flush=True)
    for p in poss:
        print(f"  {_opt_tag(p.contract):34s} qty={p.position:>9}  avgCost={p.avgCost:.2f}",
              flush=True)

    print("\n=== OPEN ORDERS ===", flush=True)
    trades = ib.openTrades()
    if not trades:
        print("  (none)", flush=True)
    for t in trades:
        o, c = t.order, t.contract
        print(f"  id={o.orderId} {o.action} {o.totalQuantity} {_opt_tag(c)} "
              f"{o.orderType} aux={getattr(o,'auxPrice',None)} lmt={getattr(o,'lmtPrice',None)} "
              f"tif={o.tif} status={t.orderStatus.status}", flush=True)

    ib.disconnect()
    print("\nOK (disconnected, read-only).", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
