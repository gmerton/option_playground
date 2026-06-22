#!/usr/bin/env python3
"""Tighten EXISTING stops for a set of names (modify-in-place, no new orders).

Each entry: symbol -> (expected_qty, expected_old_aux, new_aux). Safety: requires exactly
one matching STK SELL STP per symbol AND that its qty + current aux match expectations,
else that symbol is SKIPPED untouched. clientId 0 so it can modify manual orders.

  IB_PORT=4001 IB_ALLOW_LIVE=1 PYTHONPATH=src .venv/bin/python3 -u ibkr_bot/modify_stops_batch.py
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402

# symbol -> (expected_qty, expected_old_aux, new_aux)
CHANGES = {
    "VSH": (10.0, 62.50, 62.90),
    "MU":  (2.0, 1087.00, 1090.00),
}


def find_stop(ib, sym):
    m = [t for t in ib.openTrades()
         if t.contract.symbol == sym and t.contract.secType == "STK"
         and t.order.orderType == "STP" and t.order.action == "SELL"]
    return m


def main() -> int:
    ib = connect_ib(client_id=0)
    print(f"CONNECTED {ib.managedAccounts()} (clientId=0)", flush=True)
    ib.reqAllOpenOrders(); ib.sleep(2.0)

    for sym, (eqty, old, new) in CHANGES.items():
        m = find_stop(ib, sym)
        if len(m) != 1:
            print(f"SKIP {sym}: expected 1 SELL STP, found {len(m)}", flush=True); continue
        o = m[0].order
        if float(o.totalQuantity) != eqty or abs(float(o.auxPrice) - old) > 0.01:
            print(f"SKIP {sym}: qty/aux mismatch (qty={o.totalQuantity} aux={o.auxPrice}, "
                  f"expected {eqty}/{old})", flush=True); continue
        print(f"{sym}: modifying id={o.orderId} aux {old} -> {new}", flush=True)
        o.auxPrice = new; o.transmit = True
        ib.placeOrder(m[0].contract, o)
    ib.sleep(2.5)

    # verify
    ib.reqAllOpenOrders(); ib.sleep(1.5)
    print("\n--- verify ---", flush=True)
    allok = True
    for sym, (eqty, old, new) in CHANGES.items():
        m = find_stop(ib, sym)
        n = len(m)
        aux = float(m[0].order.auxPrice) if n == 1 else None
        ok = (n == 1 and abs(aux - new) < 0.01)
        allok &= ok
        print(f"  {sym}: {n} SELL STP, aux={aux}  {'OK' if ok else 'CHECK'}", flush=True)
    ib.disconnect()
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
