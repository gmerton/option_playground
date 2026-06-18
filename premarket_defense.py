"""Pre-market DEFENSE check: for each held position, show the gap and distance to its
protective stop, so you know what to act on at the open. Tradier ext-hours bid/ask mid
(the `last` field is stale pre-open). Run 8-9am ET. Edit HOLDINGS if positions change."""
import os, asyncio
from lib.tradier.tradier_client_wrapper import TradierClient

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")

# ticker -> qty, entry, recommended GTC stop, action (from 2026-06-15 close).
# NOTE: long-call positions (INTC, KLAC, AAPL, APLD, HOOD, COCO, QQQ, CIFR-calls)
# are NOT here -- they can't take a share-stop; manage by taking profit / selling on a break.
HOLDINGS = {
    "MRVU": {"qty": 30, "entry": 228.45, "stop": 243.00, "act": "TRIM"},
    "MU":   {"qty": 2,  "entry": 994.20, "stop": 1051.00, "act": "TRIM"},
    "NBIS": {"qty": 10, "entry": 246.39, "stop": 254.00, "act": "TRIM"},
    "ARM":  {"qty": 10, "entry": 370.83, "stop": 396.00, "act": "TRIM"},
    "CIFR": {"qty": 100, "entry": 24.33, "stop": 25.60,  "act": "STOP"},
    "UNH":  {"qty": 5,  "entry": 399.81, "stop": 396.00, "act": "KEEP"},
    "SOXL": {"qty": 3,  "entry": 263.74, "stop": 262.00, "act": "TRIM"},
    "WDC":  {"qty": 4,  "entry": 642.31, "stop": 639.00, "act": "TRIM"},
    "SNDK": {"qty": 1,  "entry": 1991.74, "stop": 2020.00, "act": "TRIM"},
    "MUU":  {"qty": 3,  "entry": 991.49, "stop": 982.00, "act": "TRIM"},
    "ARMG": {"qty": 30, "entry": 47.82,  "stop": 50.80,  "act": "TRIM"},
    "SPCX": {"qty": 2,  "entry": 179.02, "stop": 185.00, "act": "TRIM"},
    "AAOI": {"qty": 5,  "entry": 185.83, "stop": 187.00, "act": "TRIM"},
    "STX":  {"qty": 3,  "entry": 939.21, "stop": 991.00, "act": "STOP"},
    "AMD":  {"qty": 10, "entry": 512.14, "stop": 530.00, "act": "STOP"},
    "AMKR": {"qty": 45, "entry": 82.50,  "stop": 82.60,  "act": "STOP"},
    "RVMD": {"qty": 30, "entry": 156.97, "stop": 156.00, "act": "STOP"},
    "FIX":  {"qty": 4,  "entry": 1904.15, "stop": 1935.00, "act": "STOP"},
    "ROKU": {"qty": 15, "entry": 130.64, "stop": 139.50, "act": "STOP"},
    "ONTO": {"qty": 10, "entry": 339.82, "stop": 333.00, "act": "CUT"},
    "CVS":  {"qty": 30, "entry": 101.91, "stop": 98.90,  "act": "CUT"},
}

def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None

async def get_quotes(t, syms):
    data = await t.get_json("/markets/quotes", params={"symbols": ",".join(syms), "greeks": "false"})
    q = ((data or {}).get("quotes") or {}).get("quote") or []
    if isinstance(q, dict): q = [q]
    return {x.get("symbol"): x for x in q}

async def main():
    async with TradierClient(api_key=TRADIER_API_KEY) as t:
        quotes = await get_quotes(t, list(HOLDINGS))
    rows = []
    for sym, h in HOLDINGS.items():
        q = quotes.get(sym) or {}
        prevclose = f(q.get("prevclose")); bid = f(q.get("bid")); ask = f(q.get("ask")); last = f(q.get("last"))
        mid = (bid + ask) / 2 if (bid and ask) else last
        if mid is None or prevclose is None:
            rows.append({"sym": sym, "act": h["act"], "note": "no quote"}); continue
        gap = (mid / prevclose - 1) * 100
        to_stop = (mid - h["stop"]) / mid * 100          # +ve = cushion above stop; -ve = below
        spread = (ask - bid) / mid * 100 if (mid and bid and ask) else None
        below = mid <= h["stop"]
        flag = "** BELOW STOP **" if below else ("near stop" if (gap < 0 and to_stop < 2) else "")
        if spread is not None and spread > 1.5: flag += " (!wide)"
        rows.append({"sym": sym, "act": h["act"], "entry": h["entry"], "stop": h["stop"],
                     "prevclose": prevclose, "mid": mid, "gap": gap, "to_stop": to_stop, "flag": flag})
    ok = [r for r in rows if "note" not in r]
    ok.sort(key=lambda r: r["gap"])                       # worst (biggest gap-down) first
    print("PRE-MARKET DEFENSE  (sorted worst gap first; act on BELOW/near-stop at the open)\n")
    print(f"{'SYM':5} {'act':5} {'entry':>9} {'premkt':>9} {'gap%':>6} {'stop':>9} {'toStop%':>8}  flag")
    for r in ok:
        print(f"{r['sym']:5} {r['act']:5} {r['entry']:9.2f} {r['mid']:9.2f} {r['gap']:+6.1f} "
              f"{r['stop']:9.2f} {r['to_stop']:+8.1f}  {r['flag']}")
    miss = [r['sym'] for r in rows if "note" in r]
    if miss: print("\nno quote:", ", ".join(miss))

asyncio.run(main())
