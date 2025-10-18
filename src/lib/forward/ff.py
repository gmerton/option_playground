import os, asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from lib.commons.bs import implied_vol
from lib.commons.list_contracts import list_contracts_for_expiry
from datetime import datetime, date

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}

async def _list_expirations(
        ticker:str
):
    url = f"{TRADIER_ENDPOINT}/markets/options/expirations"
    params =  {
        "symbol"
    }
    session = aiohttp.ClientSession(
        headers = TRADIER_REQUEST_HEADERS
    )
    try:
        params = {
            "symbol":ticker,
            "includeAllRoots" : "true",
            "strikes" : "false",
            "contractSize" : "false",
            "expirationType" : "false",
        }
        async with session.get(url, params = params) as resp:
            resp.raise_for_status()
            data = await resp.json()
            exp_root = (data or {}).get("expirations") or {}
            dates: List[str] = []
            maybe_dates = exp_root.get("date")
            if maybe_dates:
                dates = [str(d) for d in (maybe_dates if isinstance(maybe_dates, list) else [maybe_dates])]
            else:
                exps = exp_root.get("expiration")
                if exps:
                    if isinstance(exps,dict):
                        exps = [exps]
                    dates = [str(x.get("date")) for x in exps if x.get("date")]
            return sorted(set(filter(None,dates)))
    finally:
        await session.close()
    
async def _get_underlying_price(
        ticker: str
) :
    url = f"{TRADIER_ENDPOINT}/markets/quotes"
    params = {"symbols" : ticker}
    close_session = False
    session = aiohttp.ClientSession(
        headers=TRADIER_REQUEST_HEADERS
    )
    try:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
        q = (data or {}).get("quotes", {}).get("quote")
        if q is None:
            return None
        if isinstance(q, list):
            q = q[0]
        bid = q.get("bid")
        ask = q.get("ask")
        last = q.get("last")
        close = q.get("close") or q.get("prevclose")

        if bid and ask and bid > 0 and ask > 0:
            return float((bid+ask)/2.0)
        if last and last > 0:
            return float(last)
        if close and close > 0:
            return float(close)
        return None
    finally:
        await session.close()



def nearest_strike_contract(contracts, spot, cp):
    side = [c for c in contracts if c["option_type"]==cp]
    if not side:
        return None
    return min(side, key=lambda c: abs(c["strike"]-spot))

def dte(expiration_date_str:str)->int:
    today = date.today()
    expiration = datetime.strptime(expiration_date_str, "%Y-%m-%d").date()
    return (expiration-today).days

async def test():
    ticker = "WBD"
    front_expiration_date = '2025-11-14'
    back_expiration_date = '2025-12-19'
    # Step 1: get price of underlying
    spot = await _get_underlying_price(ticker)
    print(spot)

    # Step 2: get dates of available options for a symbol
    exps = await _list_expirations(ticker)
    print(exps)
    # Step 3: Given two dates, get the ATM contracts
    front_contracts = await list_contracts_for_expiry(ticker, front_expiration_date)
    back_contracts = await list_contracts_for_expiry(ticker,back_expiration_date)
    
    # print(contracts)
    front_call_contract = nearest_strike_contract(front_contracts, spot, "call")
    front_put_contract = nearest_strike_contract(front_contracts, spot, "put")

    back_call_contract = nearest_strike_contract(back_contracts, spot, "call")
    back_put_contract = nearest_strike_contract(back_contracts, spot, "put")

    print(f"front strike = {front_call_contract["strike"]}, back strike = {back_call_contract["strike"]}" )

    front_call_iv = front_call_contract["greeks"]["mid_iv"]
    front_put_iv = front_put_contract["greeks"]["mid_iv"]

    front_iv = (front_call_iv+front_put_iv)/2
    
    back_call_iv = back_call_contract["greeks"]["mid_iv"]
    back_put_iv = back_put_contract["greeks"]["mid_iv"]

    back_iv = (back_call_iv + back_put_iv)/2
    
    dte_front = dte(front_expiration_date)
    dte_back = dte(back_expiration_date)
    print(f"dtes={dte_front}, {dte_back}")
    print(front_call_iv, front_put_iv, front_iv, back_call_iv, back_put_iv, back_iv)

    ff_numerator = (back_iv**2)*dte_back - (front_iv**2)*dte_front
    ff_denominator = (dte_back-dte_front)
    ff_var_sq = ff_numerator/ff_denominator
    ff_var_sq = max(ff_var_sq, 0)
    ff_var = ff_var_sq ** 0.5
    
    bid_iv = implied_vol(
    price=0.35,
    S=18.591,     # spot aligned to the quote timestamp
    K=18.5,
    T=1/252,      # or your precise ACT/365—just be consistent
    r=0.0,
    q=0.0,
    opt_type="call"
)
    print(f"bid_iv={bid_iv}")

    print(f"ff={ff_var}")

    #print(front_call_contract)
    # put_contract = nearest_strike_contract(contracts, spot, "put")
    # print(call_contract)
    # print(put_contract)
    # # Step 4: for those strikes, get bid and ask vols.
    # s# print(sig)
if __name__ == "__main__":
    asyncio.run(test())