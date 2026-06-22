#!/usr/bin/env python3
"""Widen CAT & GLW stops (modify in place) and ADD a tight NBIS stop (new order).

Live account, clientId 0. Safety:
  - CAT/GLW: require exactly one existing STK SELL STP whose qty+aux match expectations,
    else SKIP. Modify ONLY the price (same orderId -> no stacking).
  - NBIS: require ZERO existing STK SELL STP (else SKIP to avoid a duplicate) AND a live
    long position of the expected size, then place ONE new GTC stop.
Verifies all three at the end.

  IB_PORT=4001 IB_ALLOW_LIVE=1 PYTHONPATH=src .venv/bin/python3 -u ibkr_bot/apply_stops_catglwnbis.py
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conn import connect_ib  # noqa: E402
from ib_async import Stock, StopOrder  # noqa: E402

# modify existing: sym -> (expected_qty, expected_old_aux, new_aux)
MODIFY = {
    "CAT": (5.0, 975.00, 905.00),
    "GLW": (30.0, 188.50, 171.00),
}
# add new: sym -> (expected_pos_qty, stop_price)
ADD = {
    "NBIS": (4.0, 274.00),
}


def stops_for(ib, sym):
    return [t for t in ib.openTrades()
            if t.contract.symbol == sym and t.contract.secType == "STK"
            and t.order.orderType == "STP" and t.order.action == "SELL"]


def pos_for(ib, sym):
    for p in ib.positions():
        if p.contract.symbol == sym and p.contract.secType == "STK":
            return p.position
    return 0.0


def main() -> int:
    ib = connect_ib(client_id=0)
    print(f"CONNECTED {ib.managedAccounts()} (clientId=0)", flush=True)
    ib.reqAllOpenOrders(); ib.sleep(2.0)

    # --- modifications ---
    for sym, (eqty, old, new) in MODIFY.items():
        m = stops_for(ib, sym)
        if len(m) != 1:
            print(f"SKIP {sym}: expected 1 SELL STP, found {len(m)}", flush=True); continue
        o = m[0].order
        if float(o.totalQuantity) != eqty or abs(float(o.auxPrice) - old) > 0.01:
            print(f"SKIP {sym}: mismatch qty={o.totalQuantity} aux={o.auxPrice} "
                  f"(want {eqty}/{old})", flush=True); continue
        print(f"{sym}: modify id={o.orderId} aux {old} -> {new}", flush=True)
        o.auxPrice = new; o.transmit = True
        ib.placeOrder(m[0].contract, o)

    # --- new orders ---
    for sym, (eqty, stop) in ADD.items():
        existing = stops_for(ib, sym)
        if existing:
            print(f"SKIP {sym}: already has {len(existing)} SELL STP -- not adding "
                  f"(avoid duplicate)", flush=True); continue
        held = pos_for(ib, sym)
        if held != eqty:
            print(f"SKIP {sym}: live pos {held} != expected {eqty}", flush=True); continue
        c = Stock(sym, "SMART", "USD"); ib.qualifyContracts(c)
        order = StopOrder("SELL", eqty, stop); order.tif = "GTC"
        print(f"{sym}: ADD new SELL {eqty:.0f} STP @ {stop} GTC", flush=True)
        ib.placeOrder(c, order)

    ib.sleep(3.0)
    ib.reqAllOpenOrders(); ib.sleep(1.5)

    # --- verify ---
    print("\n--- verify ---", flush=True)
    targets = {"CAT": 905.00, "GLW": 171.00, "NBIS": 274.00}
    allok = True
    for sym, want in targets.items():
        m = stops_for(ib, sym)
        aux = float(m[0].order.auxPrice) if len(m) == 1 else None
        ok = (len(m) == 1 and aux is not None and abs(aux - want) < 0.01)
        allok &= ok
        print(f"  {sym}: {len(m)} SELL STP, aux={aux}  {'OK' if ok else 'CHECK'}", flush=True)
    ib.disconnect()
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
