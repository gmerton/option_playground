#!/usr/bin/env python3
"""Set the 1-ADR DISASTER stops of 2026-10-04 (off the 2026-10-02 close) on the live account -- RUN BY GABE.

Levels: data/studies/stop_definitions.md -- the disaster stop is 1.0 ADR from the latest close, RESTS with the broker,
executes intraday, GTC, regular hours only. DRAM is excluded at Gabe's request.

Safety:
  * DRY RUN by default: connects, reads positions + open orders, prints the plan. Sends nothing.
  * --apply sends orders only after you type 'yes'.
  * clientId 0 (the only id that may modify / cancel orders created in TWS -- repo gotcha); reqAutoOpenOrders binds them.
  * An EXISTING protective stop is MODIFIED in place (price, and quantity if it differs) -- never a second stop.
    More than one protective stop on a name = stacked -> that name is SKIPPED and reported.
    An existing TRAIL or STP LMT is never modified (auxPrice means something else on those) -> SKIPPED.
  * Position quantity must match the plan exactly, else the name is SKIPPED (the book changed since the plan).
  * After --apply it re-reads the account and prints one line per name.

Usage (live TWS on 7496):
  IB_PORT=7496 IB_ALLOW_LIVE=1 PYTHONPATH=src .venv/bin/python3 ibkr_bot/apply_disaster_stops_2026-10-04.py           # dry run
  IB_PORT=7496 IB_ALLOW_LIVE=1 PYTHONPATH=src .venv/bin/python3 ibkr_bot/apply_disaster_stops_2026-10-04.py --apply   # send
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ib_async import Stock, StopOrder  # noqa: E402
from conn import connect_ib  # noqa: E402

# symbol: (position quantity expected, stop side, stop price)   -- 1 ADR off the 2026-10-02 close
PLAN = {
    "DELL": (3, "SELL", 533.16),
    "CIBR": (50, "SELL", 102.18),
    "ALAB": (6, "SELL", 327.08),
    "ON":   (15, "SELL", 81.04),
    "USAR": (-200, "BUY", 14.27),
    "SOXL": (4, "SELL", 152.49),
    "PANW": (20, "SELL", 384.85),
    "LITE": (1, "SELL", 1013.39),
    "MSFU": (100, "SELL", 38.30),
    "TNA":  (15, "SELL", 57.83),
}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); a = ap.parse_args()
    ib = connect_ib(client_id=0)
    print(f"connected: {ib.managedAccounts()}  mode: {'APPLY' if a.apply else 'DRY RUN (nothing will be sent)'}")
    ib.reqAutoOpenOrders(True)
    ib.reqAllOpenOrders(); ib.sleep(2.5)
    pos = {p.contract.symbol: p.position for p in ib.positions() if p.contract.secType == "STK"}
    stops: dict[str, list] = {}
    for t in ib.openTrades():
        c, o = t.contract, t.order
        if c.secType == "STK" and o.orderType in ("STP", "STP LMT", "TRAIL"):
            stops.setdefault(c.symbol, []).append(t)

    actions = []
    for sym, (qty, side, px) in PLAN.items():
        have = pos.get(sym, 0)
        mine = [t for t in stops.get(sym, []) if t.order.action == side]
        if have != qty:
            print(f"SKIP {sym}: position is {have:g}, plan expects {qty} -- re-run the stop calculation"); continue
        if len(mine) > 1:
            print(f"SKIP {sym}: {len(mine)} {side} stops already resting (stacked) -- clean up in TWS first"); continue
        if mine and mine[0].order.orderType != "STP":
            # TRAIL: auxPrice is the trail AMOUNT, not a stop price; STP LMT: lmtPrice would be left stale.
            # Either way a modify here would mis-set it, and a new STP alongside it would stack -> skip.
            t = mine[0]
            print(f"SKIP {sym}: existing {t.order.orderType} stop (orderId {t.order.orderId}) -- change it in TWS, not here"); continue
        if mine:
            t = mine[0]
            print(f"MODIFY {sym}: {side} {t.order.totalQuantity:g} STP {t.order.auxPrice:g} -> {side} {abs(qty)} STP {px:.2f} (orderId {t.order.orderId})")
            actions.append(("modify", sym, t, abs(qty), px))
        else:
            print(f"NEW    {sym}: {side} {abs(qty)} STP {px:.2f} GTC")
            actions.append(("new", sym, side, abs(qty), px))

    if not a.apply:
        print("\nDry run only. Re-run with --apply to send these orders."); ib.disconnect(); return 0
    if input(f"\nSend {len(actions)} order changes to the LIVE account? type 'yes': ").strip() != "yes":
        print("aborted, nothing sent"); ib.disconnect(); return 1

    for act in actions:
        if act[0] == "modify":
            _, sym, t, q, px = act
            o = t.order; o.auxPrice = round(px, 2); o.totalQuantity = q; o.tif = "GTC"; o.outsideRth = False
            ib.placeOrder(t.contract, o)
        else:
            _, sym, side, q, px = act
            c = Stock(sym, "SMART", "USD"); ib.qualifyContracts(c)
            o = StopOrder(side, q, round(px, 2)); o.tif = "GTC"; o.outsideRth = False
            ib.placeOrder(c, o)
        ib.sleep(0.5)
    ib.sleep(3.0)

    ib.reqAllOpenOrders(); ib.sleep(2.5)
    print("\nVERIFY (resting stops after the changes):")
    after: dict[str, list] = {}
    for t in ib.openTrades():
        if t.contract.secType == "STK" and t.order.orderType in ("STP", "STP LMT", "TRAIL"):
            after.setdefault(t.contract.symbol, []).append(f"{t.order.action} {t.order.totalQuantity:g} @{t.order.auxPrice:g} [{t.orderStatus.status}]")
    for sym, (qty, side, px) in PLAN.items():
        s = after.get(sym, [])
        flag = "OK" if len(s) == 1 and f"@{round(px, 2):g}" in s[0] else "CHECK"
        print(f"  {flag:5s} {sym:5s} plan {side} {abs(qty)} @{px:.2f} | resting: {'; '.join(s) or 'none'}")
    ib.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
