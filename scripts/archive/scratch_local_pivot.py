"""Recipe #5 fix — anchor the breakout pivot on the LOCAL base, not the multi-month high.

Tito labels COIN 2/9 and MSTR 2/8 "Breakout," but vs the 3-month-high pivot they entered
BELOW it (looked like no breakout). His pivot is the most-recent consolidation high. Test a
local-pivot = max high over the prior N days against all 15 of his "Breakout" trades: a good N
makes entry_close clear the pivot for ALL of them (matching his labels) while staying meaningful
(a real level, not a trivially-broken 1-day high). Compare to the 3mo pivot that fails on COIN/MSTR.
"""
import os, asyncio, statistics as st
from lib.tradier.tradier_client_wrapper import TradierClient

SYMAP = {"BRKB": "BRK/B", "BTC": "IBIT"}
# Tito's 15 "Breakout"-labeled trades: (csv_ticker, entry_date)
BREAKOUTS = [
    ("NVDA","2024-01-08"),("SMCI","2024-01-19"),("MSTR","2024-02-08"),("COIN","2024-02-09"),
    ("GLD","2024-03-01"),("AAPL","2024-06-11"),("BRKB","2024-07-11"),("IWM","2024-07-11"),
    ("GEV","2024-08-29"),("APP","2024-09-11"),("BABA","2024-09-19"),("MSTR","2024-10-11"),
    ("PLTR","2024-11-05"),("BTC","2024-11-06"),("COST","2024-11-08"),
]
NS = [8, 10, 15, 20]


async def hist(c, sym, s, e):
    r = await c.get_json("/markets/history", {"symbol": sym, "interval": "daily", "start": s, "end": e})
    d = r["history"]["day"]; return d if isinstance(d, list) else [d]


async def analyze(c, csv_t, entry):
    sym = SYMAP.get(csv_t, csv_t)
    days = await hist(c, sym, "2023-08-01", entry)
    highs = [d["high"] for d in days]; closes = [d["close"] for d in days]
    lows = [d["low"] for d in days]; dates = [d["date"] for d in days]
    ei = dates.index(entry)
    ec = closes[ei]
    piv_3mo = max(highs[max(0, ei-65):ei])
    out = {"t": csv_t, "entry": entry, "ec": ec, "p3mo": piv_3mo,
           "above_3mo": ec > piv_3mo}
    for N in NS:
        pv = max(highs[max(0, ei-N):ei])
        # tightness of that window = range as % of its low (is it actually a base?)
        wlo = min(lows[max(0, ei-N):ei]); rng = (pv - wlo) / wlo * 100
        out[f"p{N}"] = pv; out[f"above_{N}"] = ec > pv; out[f"tight_{N}"] = rng
    return out


async def main():
    key = os.environ["TRADIER_API_KEY"]
    async with TradierClient(api_key=key) as c:
        res = []
        for t, e in BREAKOUTS:
            res.append(await analyze(c, t, e))
    print(f"{'trade':16} {'entry_cl':>8} | {'3mo':>7} {'>?':>3} | " +
          " | ".join(f"N{N}:piv>?tight" for N in NS))
    counts = {f"N{N}": 0 for N in NS}; c3 = 0
    for r in res:
        line = f"{r['t']+' '+r['entry'][5:]:16} {r['ec']:8.2f} | {r['p3mo']:7.2f} {'Y' if r['above_3mo'] else '.':>3} |"
        if r["above_3mo"]: c3 += 1
        for N in NS:
            ab = r[f"above_{N}"]; counts[f"N{N}"] += ab
            line += f" {r[f'p{N}']:6.2f} {'Y' if ab else '.'}{r[f'tight_{N}']:5.0f}% |"
        print(line)
    n = len(res)
    print(f"\nBreakout-confirm rate (entry clears pivot) — target = 15/15 to match Tito's labels:")
    print(f"  3-month-high pivot: {c3}/{n}   <-- the one that mis-flags COIN/MSTR")
    for N in NS:
        print(f"  local N={N:2d} pivot:    {counts[f'N{N}']}/{n}")


if __name__ == "__main__":
    asyncio.run(main())
