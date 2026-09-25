"""Pre-market scan of the breakout roster: gap, position vs trigger, pre-market volume.
Tradier quotes (extended-hours last/bid/ask) + daily history for pivots. Run pre-open."""
import os, asyncio, json
from datetime import date, timedelta
import numpy as np
import pandas as pd
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
ROSTER = ["KEYS","ADI","AMD","AMKR","INTC","ONTO","AMAT","UCTT","FTNT","CRWD","PANW",
          "DAL","UAL","STT","FITB","C","IBKR","MS","CVS","RVMD","RPRX","JBHT","CAT","ARMK"]
try:
    THEMES = json.load(open(os.path.join("data", "theme_scores.json")))
except Exception:
    THEMES = {}

async def get_quotes(t, syms):
    data = await t.get_json("/markets/quotes", params={"symbols": ",".join(syms), "greeks": "false"})
    q = ((data or {}).get("quotes") or {}).get("quote") or []
    if isinstance(q, dict):
        q = [q]
    return {x.get("symbol"): x for x in q}

async def get_levels(t, sym, start, end):
    try:
        df = await get_daily_history(sym, start, end, client=t)
        if df is None or len(df) < 30:
            return sym, None
        c = df["close"].astype(float); h = df["high"].astype(float); v = df["volume"].astype(float)
        return sym, {"pivot": float(h.tail(20).max()), "early": float(h.tail(5).max()),
                     "ema20": float(c.ewm(span=20, adjust=False).mean().iloc[-1]),
                     "avgvol": float(v.tail(50).mean())}
    except Exception:
        return sym, None

def f(x, d=2):
    try: return float(x)
    except (TypeError, ValueError): return None

async def main():
    end = date.today(); start = end - timedelta(days=120)
    async with TradierClient(api_key=TRADIER_API_KEY) as t:
        quotes = await get_quotes(t, ROSTER)
        levels = dict(await asyncio.gather(*[get_levels(t, s, start, end) for s in ROSTER]))

    rows = []
    for sym in ROSTER:
        q = quotes.get(sym) or {}
        lv = levels.get(sym)
        prevclose = f(q.get("prevclose"))
        last = f(q.get("last"))
        bid, ask = f(q.get("bid")), f(q.get("ask"))
        vol = f(q.get("volume"))
        # pre-market reference = bid/ask MID (Tradier 'last' is stale to prevclose pre-open)
        mid = (bid + ask) / 2 if (bid and ask) else None
        px = mid if mid else last
        spread = (ask - bid) / mid * 100 if (mid and mid > 0) else None
        if px is None or prevclose is None or not lv:
            rows.append({"sym": sym, "note": "no quote"}); continue
        gap = px / prevclose - 1
        wide = spread is not None and spread > 1.0   # >1% spread = illiquid, gap unreliable
        to_pivot = lv["pivot"] / px - 1
        to_early = lv["early"] / px - 1
        # position vs trigger
        if px >= lv["pivot"]:
            pos = "ABOVE-PIVOT"
        elif px >= lv["early"]:
            pos = "above-early"
        elif to_early <= 0.01:
            pos = "at-early"
        else:
            pos = "below"
        th = THEMES.get(sym, {})
        rows.append({"sym": sym, "theme": th.get("theme", "-"),
                     "prio": th.get("priority_mult", 1.0), "prevclose": prevclose,
                     "px": px, "gap": gap*100, "to_pivot": to_pivot*100,
                     "to_early": to_early*100, "pos": pos, "vol": vol,
                     "avgvol": lv["avgvol"], "spread": spread, "wide": wide})

    df = pd.DataFrame(rows)
    ok = df[~df.get("note", pd.Series([None]*len(df))).notna()] if "note" in df else df
    ok = ok.sort_values(["prio", "gap"], ascending=[False, False])
    pd.set_option("display.width", 220, "display.max_columns", 30)
    print(f"Pre-market scan {end} (Tradier ext-hours bid/ask mid)\n")
    print(f"{'SYM':5} {'THEME':14} {'prevcl':>8} {'premkt':>8} {'gap%':>6} {'pos':12} "
          f"{'to_piv%':>7} {'to_erl%':>7} {'pmVol':>8} {'spr%':>5}")
    for _, r in ok.iterrows():
        pv = f"{r['vol']/1e3:.0f}K" if r['vol'] else "-"
        flag = " !wide" if r["wide"] else ""
        spr = f"{r['spread']:.1f}" if r["spread"] is not None else "-"
        print(f"{r['sym']:5} {str(r['theme'])[:14]:14} {r['prevclose']:8.2f} {r['px']:8.2f} "
              f"{r['gap']:+6.1f} {r['pos']:12} {r['to_pivot']:7.1f} {r['to_early']:7.1f} "
              f"{pv:>8} {spr:>5}{flag}")
    bad = df[df.get("note").notna()] if "note" in df else None
    if bad is not None and len(bad):
        print("\nno quote:", ", ".join(bad["sym"]))

asyncio.run(main())
