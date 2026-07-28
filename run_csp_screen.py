"""CSP candidate screen over the low-ADR 'just right' cohort.

Per name: ~30-45 DTE expiry, put nearest 0.27 delta -> yield, annualized, BA%, OI, IV vs RV20.
"""
import asyncio, os, sys
sys.path.insert(0, "/Users/gmerton/v2/options_playground")
sys.path.insert(0, "/Users/gmerton/v2/options_playground/src")
from datetime import date
from market_conditions import fetch_days, _realized_vol
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.commons.list_expirations import list_expirations
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price

TICKERS = ("JPM BAC USB PNC TRV AFL CB V AXP MET "
           "RF FITB MTB ZION KEY CFG "
           "UNP NSC CNI GWW GD HWM WST ABBV JNJ UNH").split()
TODAY = date(2026, 7, 14)
SEM = asyncio.Semaphore(8)


async def one(client, sym):
    async with SEM:
        try:
            spot = await get_underlying_price(sym, client=client)
            exps = await list_expirations(sym, client=client)
            days = await fetch_days(client, sym, days_back=90)
        except Exception as e:
            return f"{sym:<5} ERROR {e}"
        rv20 = _realized_vol([d["close"] for d in days])
        # target expiry: 28-45 DTE, closest to 35
        cands = [(abs((date.fromisoformat(e) - TODAY).days - 35), e) for e in exps
                 if 28 <= (date.fromisoformat(e) - TODAY).days <= 45]
        if not cands or spot is None:
            return f"{sym:<5} no 28-45 DTE expiry"
        exp = min(cands)[1]
        dte = (date.fromisoformat(exp) - TODAY).days
        try:
            chain = await list_contracts_for_expiry(sym, exp, option_type="put", client=client)
        except Exception as e:
            return f"{sym:<5} chain err {e}"
        puts = []
        for c in chain:
            if c.get("option_type") != "put":
                continue
            g = c.get("greeks") or {}
            d = g.get("delta")
            b, a = c.get("bid"), c.get("ask")
            if d is None or not b or not a or b <= 0:
                continue
            puts.append({"strike": float(c["strike"]), "delta": d, "bid": b, "ask": a,
                         "mid": (b + a) / 2, "iv": g.get("mid_iv") or g.get("smv_vol") or 0,
                         "oi": c.get("open_interest") or 0})
        if not puts:
            return f"{sym:<5} no usable puts {exp}"
        p = min(puts, key=lambda x: abs(abs(x["delta"]) - 0.27))
        yld = p["mid"] / p["strike"] * 100
        ann = yld * 365 / dte
        ba = (p["ask"] - p["bid"]) / p["mid"] * 100
        vrp = (p["iv"] - (rv20 or 0)) * 100
        return (f"{sym:<5} {spot:>8.2f} {exp} {dte:>3} {p['strike']:>7.1f} {abs(p['delta']):>4.2f} "
                f"{p['mid']:>6.2f} {yld:>5.2f}% {ann:>5.1f}% {ba:>4.0f}% {p['oi']:>6} "
                f"{p['iv']*100:>4.0f}% {(rv20 or 0)*100:>4.0f}% {vrp:>+5.1f}")


async def main():
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as client:
        rows = await asyncio.gather(*[one(client, s) for s in TICKERS])
    print(f"{'sym':<5} {'spot':>8} {'expiry':<10} {'dte':>3} {'strike':>7} {'Δ':>4} "
          f"{'mid':>6} {'yield':>6} {'ann':>6} {'BA%':>4} {'OI':>6} {'IV':>4} {'RV20':>4} {'VRP':>5}")
    for r in rows:
        print(r)

asyncio.run(main())
