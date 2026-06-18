"""Pressure-test the 20-EMA-close trail against Tito's actual intraday-strength exits, on the
6 trades he EXITED EARLY. He sold strength, so the trail (hold until a daily close < 20-EMA)
holds longer. Question: how much does his intraday-peak selling beat a mechanical trail the
user could actually run without watching intraday?

Step 1 (Tradier): find each trade's 20-EMA-close-break date (else expiry).
Step 2 (Athena): price the inferred strike on that exit date -> trail return vs Tito's actual.
"""
import os, asyncio
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.athena_lib import athena

# (csv_t, athena_t, strike, expiry, cp, entry_px, tito_ret, tito_exit_date, at_exp_ret)
EARLY = [
    ("ARM", "ARM", 108.0, "2024-02-16","C", 3.00, 1966, "2024-02-13",  578),
    ("BRKB","BRK", 430.0, "2024-08-16","C", 2.40,  858, "2024-07-24",  516),
    ("GEV", "GEV", 200.0, "2024-09-20","C", 3.40, 1332, "2024-09-13", 1237),
    ("BABA","BABA",95.0, "2024-10-18","C", 0.95, 2269, "2024-10-09",  829),
    ("DJT", "DJT", 48.0, "2024-11-22","C", 6.00,  217, "2024-10-31", -100),
    ("COST","COST",945.0,"2024-11-15","C", 2.23,  842, "2024-11-11", -100),
]
ENTRY = {"ARM":"2024-02-08","BRKB":"2024-07-11","GEV":"2024-08-29","BABA":"2024-09-19",
         "DJT":"2024-10-22","COST":"2024-11-08"}
SYMAP = {"BRKB":"BRK/B"}


def ema(vals, n):
    k = 2/(n+1); out=[vals[0]]
    for v in vals[1:]: out.append(v*k+out[-1]*(1-k))
    return out


async def hist(c, sym, s, e):
    r = await c.get_json("/markets/history", {"symbol":sym,"interval":"daily","start":s,"end":e})
    d = r["history"]["day"]; return d if isinstance(d,list) else [d]


async def find_break(c, csv_t, expiry):
    sym = SYMAP.get(csv_t, csv_t)
    entry = ENTRY[csv_t]
    days = await hist(c, sym, "2023-09-01", expiry)
    closes=[d["close"] for d in days]; dates=[d["date"] for d in days]
    e20 = ema(closes, 20)
    ei = dates.index(entry); xi = dates.index(expiry)
    for i in range(ei+1, xi+1):
        if closes[i] < e20[i]:
            return dates[i], i-ei, False     # break date, day#, not-expiry
    return expiry, xi-ei, True               # no break -> held to expiry


async def main():
    key = os.environ["TRADIER_API_KEY"]
    async with TradierClient(api_key=key) as c:
        breaks = {}
        for (csv_t,_at,_k,exp,_cp,_ep,_tr,_td,_ae) in EARLY:
            breaks[csv_t] = await find_break(c, csv_t, exp)

    # price the inferred strike on each trail-exit date (skip those held to expiry -> use at_exp)
    need = [(at,k,e,cp,breaks[csv_t][0]) for (csv_t,at,k,e,cp,_ep,_tr,_td,_ae) in EARLY
            if not breaks[csv_t][2]]
    px_map = {}
    if need:
        conds = " OR ".join(
            f"(ticker='{at}' AND strike={k} AND expiry=DATE '{e}' AND cp='{cp}' AND trade_date=DATE '{d}')"
            for (at,k,e,cp,d) in need)
        df = athena(f"""SELECT ticker, strike, CAST(expiry AS DATE) AS expiry, CAST(trade_date AS DATE) AS d,
                        ROUND(AVG(last),2) AS last, ROUND(AVG((bid+ask)/2.0),2) AS mid
                        FROM silver.options_daily_v3 WHERE ({conds})
                        GROUP BY ticker, strike, expiry, trade_date""")
        df["expiry"]=df["expiry"].astype(str); df["d"]=df["d"].astype(str); df["strike"]=df["strike"].astype(float)
        for r in df.itertuples():
            px_map[(r.ticker, r.strike, r.expiry, r.d)] = (r.last, r.mid)

    print(f"{'trade':6} {'tito_exit':10}{'tito%':>7} | {'trail_exit':10}{'day':>4} {'held2exp?':>9} {'trail%':>8} | {'verdict'}")
    for (csv_t,at,k,exp,cp,ep,tito,tdate,ae) in EARLY:
        bdate, bday, held = breaks[csv_t]
        if held:
            trail_ret = ae   # no break -> trail holds to expiry = at-expiry intrinsic
            tpx = "(exp intrinsic)"
        else:
            last, mid = px_map.get((at,k,exp,bdate), (None,None))
            px = last if last and last>0 else mid
            trail_ret = round((px-ep)/ep*100) if px else None
            tpx = f"@{px}"
        v = "Tito WINS" if (trail_ret is None or tito>trail_ret) else "trail wins"
        tr = "n/a" if trail_ret is None else f"{trail_ret:+.0f}%"
        print(f"{csv_t:6} {tdate:10}{tito:+6.0f}% | {bdate:10}{bday:>4} {str(held):>9} {tr:>8} | {v} {tpx}")

    print("\nReads: trail 'held2exp?'=True means price never closed below the 20-EMA before expiry,")
    print("so the mechanical trail would hold to expiry (at-expiry intrinsic shown).")


if __name__ == "__main__":
    asyncio.run(main())
