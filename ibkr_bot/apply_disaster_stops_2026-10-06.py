#!/usr/bin/env python3
"""Set the 1-ADR DISASTER stops of 2026-10-06 (off the 2026-10-06 close) on the live account -- RUN BY GABE.

Levels from ibkr_bot/stop_audit.py (data/studies/logs/stop_audit_latest.csv): 1.0 ADR (20-session mean high/low - 1)
below the 2026-10-06 close, RESTING with the broker, intraday, GTC, regular hours only (stop_definitions.md).
Excluded: TNA (new level 57.59 is BELOW the resting 59.01 -- a stop is never lowered) and DRAM (Gabe's standing exclusion).
Same safety model as apply_disaster_stops_2026-10-04.py: DRY RUN by default, --apply asks for 'yes', clientId 0,
MODIFY an existing single STP in place, SKIP stacked / TRAIL / STP LMT / quantity mismatch / anything that moved since
the dry-run snapshot, VERIFY after sending.

Usage (live TWS on 7496):
  IB_PORT=7496 IB_ALLOW_LIVE=1 PYTHONPATH=src .venv/bin/python3 ibkr_bot/apply_disaster_stops_2026-10-06.py           # dry run
  IB_PORT=7496 IB_ALLOW_LIVE=1 PYTHONPATH=src .venv/bin/python3 ibkr_bot/apply_disaster_stops_2026-10-06.py --apply   # send
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ib_async import Stock, StopOrder  # noqa: E402
from conn import connect_ib  # noqa: E402

# symbol: (position quantity expected, stop side, stop price)   -- 1 ADR off the 2026-10-06 close
PLAN = {
    # raise existing resting stops
    "ALAB": (6, "SELL", 365.76),
    "CIBR": (50, "SELL", 105.56),
    "DELL": (5, "SELL", 546.71),
    "LITE": (1, "SELL", 1063.90),
    "MSFU": (100, "SELL", 40.07),
    "NBIS": (15, "SELL", 234.08),
    "ON":   (15, "SELL", 82.52),
    "PANW": (20, "SELL", 401.16),
    "SOXL": (4, "SELL", 153.75),
    # new stops on lines that have none
    "DOCN": (30, "SELL", 121.93),
    "MU":   (3, "SELL", 1008.01),
    "NESR": (40, "SELL", 23.25),
    "SNDK": (3, "SELL", 1577.50),
    "WDC":  (6, "SELL", 389.60),
}

# The dry run records each name's resting stop here; --apply refuses any name whose stop changed since.
SNAPSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "disaster_stops_2026-10-06_dryrun.json")


def stop_state(t) -> dict | None:
    return None if t is None else {"orderId": t.order.orderId, "type": t.order.orderType,
                                   "aux": round(float(t.order.auxPrice), 2), "qty": float(t.order.totalQuantity)}


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

    seen = None
    if a.apply:
        try:
            seen = json.load(open(SNAPSHOT))
        except FileNotFoundError:
            print(f"no dry-run snapshot at {SNAPSHOT} -- run without --apply first, check the plan, then --apply"); ib.disconnect(); return 1

    actions, state = [], {}
    for sym, (qty, side, px) in PLAN.items():
        have = pos.get(sym, 0)
        mine = [t for t in stops.get(sym, []) if t.order.action == side]
        state[sym] = stop_state(mine[0]) if len(mine) == 1 else None
        if seen is not None and (sym not in seen or seen[sym] != state[sym]):
            print(f"SKIP {sym}: resting stop changed since the dry run ({seen.get(sym)} -> {state[sym]}) -- dry-run again"); continue
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
        os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
        json.dump(state, open(SNAPSHOT, "w"), indent=1)
        print(f"\nsnapshot of resting stops -> {SNAPSHOT}")
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
