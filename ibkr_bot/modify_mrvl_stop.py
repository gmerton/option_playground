#!/usr/bin/env python3
"""Modify the EXISTING MRVL GTC stop from 300 -> 232 (no new order = no stacking).

Live account. Connects on clientId 0 (master) so it can modify a manually/other-client
placed order. Finds the single MRVL SELL STP, changes ONLY its auxPrice, re-places under
the same orderId, then re-reads to confirm. Aborts if it can't find exactly one match.

  IB_PORT=4001 IB_ALLOW_LIVE=1 PYTHONPATH=src .venv/bin/python3 -u ibkr_bot/modify_mrvl_stop.py
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402

SYMBOL = "MRVL"
NEW_STOP = 232.00
EXPECT_QTY = 20.0
EXPECT_OLD = 300.00


def main() -> int:
    ib = connect_ib(client_id=0)
    print(f"CONNECTED {ib.managedAccounts()} (clientId=0)", flush=True)
    ib.reqAllOpenOrders()
    ib.sleep(2.0)

    matches = [t for t in ib.openTrades()
               if t.contract.symbol == SYMBOL and t.contract.secType == "STK"
               and t.order.orderType == "STP" and t.order.action == "SELL"]
    if len(matches) != 1:
        print(f"ABORT: expected exactly 1 {SYMBOL} SELL STP, found {len(matches)}. "
              f"No changes made.", flush=True)
        for t in matches:
            print(f"   id={t.order.orderId} qty={t.order.totalQuantity} aux={t.order.auxPrice}",
                  flush=True)
        ib.disconnect(); return 1

    trade = matches[0]
    o = trade.order
    print(f"\nFOUND existing stop: id={o.orderId} permId={o.permId} {o.action} "
          f"{o.totalQuantity} {SYMBOL} STP aux={o.auxPrice} tif={o.tif} "
          f"status={trade.orderStatus.status}", flush=True)

    if float(o.totalQuantity) != EXPECT_QTY:
        print(f"ABORT: qty {o.totalQuantity} != expected {EXPECT_QTY}. No changes.", flush=True)
        ib.disconnect(); return 1
    if abs(float(o.auxPrice) - EXPECT_OLD) > 0.01:
        print(f"ABORT: current aux {o.auxPrice} != expected {EXPECT_OLD}. "
              f"Order may have changed -- review manually. No changes.", flush=True)
        ib.disconnect(); return 1

    # modify ONLY the stop price; keep same orderId/qty/tif -> this is an amend, not a new order
    o.auxPrice = NEW_STOP
    o.transmit = True
    print(f"\nMODIFYING aux {EXPECT_OLD} -> {NEW_STOP} (same orderId {o.orderId}) ...", flush=True)
    ib.placeOrder(trade.contract, o)
    ib.sleep(2.5)

    # verify
    ib.reqAllOpenOrders(); ib.sleep(1.5)
    after = [t for t in ib.openTrades()
             if t.contract.symbol == SYMBOL and t.order.orderType == "STP" and t.order.action == "SELL"]
    ok = False
    for t in after:
        print(f"NOW: id={t.order.orderId} qty={t.order.totalQuantity} aux={t.order.auxPrice} "
              f"tif={t.order.tif} status={t.orderStatus.status}", flush=True)
        if abs(float(t.order.auxPrice) - NEW_STOP) < 0.01:
            ok = True
    print(f"\n{'SUCCESS: stop moved to '+str(NEW_STOP) if ok else 'WARNING: could not confirm new stop -- CHECK TWS'}",
          flush=True)
    print(f"Open {SYMBOL} SELL STP count = {len(after)} (must be 1 -- no duplicate)", flush=True)
    ib.disconnect()
    return 0 if ok and len(after) == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
