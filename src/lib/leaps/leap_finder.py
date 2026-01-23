import os, asyncio
from datetime import datetime, date
from lib.commons.get_underlying_price import get_underlying_price

from lib.commons.list_expirations import list_expirations
from dateutil.relativedelta import relativedelta
from lib.commons.nyse_arca_list import nyse_arca_list, ravish_list, vrp_list, vrp_list2, nasdaq_list
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.tradier.tradier_client_wrapper import TradierClient

# This module identifies opportunities for LEAP collar plays: long 100 shares, a protective ATM put, and a covered call.
# Been finding the LT skew column in oquants to be useful in pre-screening.

MAX_ANNUALIZED_BE_DRIFT = 8
MIN_ANNUALIZED_MAX_RETURN =  50.0
MIN_ANNUALIZED_MIN_RETURN = -12
MIN_REWARD_TO_RISK = 3



TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}

def find_call(spot, contracts, atm_put_contract):
    put_bid, put_ask = atm_put_contract["bid"], atm_put_contract["ask"]
    Kp = atm_put_contract["strike"]
    put_mid = (put_bid + put_ask) /2
   
    calls = [c for c in contracts if c.get("option_type").lower() == "call"]
    eligible = []
    
    
    for c in calls:
        bid, ask = c.get("bid"), c.get("ask")
        Kc = c["strike"]
        if bid is None or ask is None:
            continue
        call_mid = (bid + ask) / 2
        net_credit = call_mid - put_mid
        min_profit = -1*(spot - Kp - net_credit) * 100.0
     
     
        if min_profit >=0:
           eligible.append((call_mid,c))
    
    if not eligible:
        return None
    call =  min(
        eligible,
        key = lambda x:x[0]
    )[1]
    call_mid = (call["bid"] + call["ask"])/ 2

    return call

def spread_pct(contract):
    mid = (contract["bid"] + contract["ask"]) / 2
    return (contract["ask"] - contract["bid"]) / mid

async def analyze(ticker,client, expiry, spot,  global_min_roi, verbose = False):
    dte = ((datetime.strptime(expiry, "%Y-%m-%d")).date() - date.today()).days
    
    #spot = await get_underlying_price(ticker)
    #spot = 15.28
    #contracts = await list_contracts_for_expiry(ticker, expiry)
    contracts = await list_contracts_for_expiry(ticker, expiry, client=client, include_greeks=True)
    
    if contracts is None:
        return
    if verbose:
        print(f"underlying spot={round(spot,2)}")
    tie_breaker = "higher"
    
    
    put_contracts = [c for c in contracts if c.get("option_type").lower() == "put"]
    call_contracts = [c for c in contracts if c.get("option_type").lower() == "call"]
    
    tie_breaker = "higher"
    prefer_high = (tie_breaker != "lower")
    if not put_contracts:
        return
    atm_put_contract = min(
        put_contracts,
        key = lambda c: (
            abs(c["strike"]- spot),
            0 if (c["strike"] >= spot) == prefer_high else 1,
            c["strike"] if prefer_high else -c["strike"]
        )
    )
    put_bid, put_ask = atm_put_contract["bid"], atm_put_contract["ask"]
    if put_bid is None or put_ask is None:
        return
    put_mid = (put_bid + put_ask) /2
    breakeven_call_contract = find_call(spot, contracts, atm_put_contract)
    if breakeven_call_contract is None:
        return
    breakeven_call_contract_strike = breakeven_call_contract["strike"]
    atm_put_contract_strike = atm_put_contract["strike"]

    if verbose:
        # print(f"atm put strike ={atm_put_contract["strike"]}, price = {put_mid}")
        # print(f"call strike = {breakeven_call_contract_strike}")
        print(f"{ticker}, {expiry}")
    for call_contract in call_contracts:
        if call_contract["strike"] < breakeven_call_contract_strike:
            continue
        for put_contract in put_contracts:
            if put_contract["strike"] > atm_put_contract_strike or put_contract["strike"]>=call_contract["strike"]:
                continue
            if put_contract["bid"]==0 or call_contract["bid"]==0:
                continue
            if spread_pct(put_contract) > 0.35 or spread_pct(call_contract) > 0.35:
                continue
            if (call_contract["volume"]==0 and call_contract["open_interest"] < 50 and 
                (call_contract["last"] is not None and call_contract["ask"] > 2 * call_contract["last"]) and call_contract["ask"] > 5 * call_contract["bid"]
            ):
                continue
            if put_contract["bid"] is None or put_contract["ask"] is None or call_contract["bid"] is None or call_contract["ask"] is None:
                continue
            if put_contract["root_symbol"] != put_contract["underlying"] or call_contract["root_symbol"] != call_contract["underlying"]:
                continue
            global_min_roi = profitability(ticker, spot, call_contract, put_contract, dte, global_min_roi,  verbose)
    return global_min_roi



def profitability(ticker, spot, call_contract, put_contract, dte, global_min_roi, verbose = False):
    # strikes
    Kc = float(call_contract["strike"])
    Kp = float(put_contract["strike"])

    call_mid = (float(call_contract["bid"]) + float(call_contract["ask"])) /2.0
        
    put_mid = (float(put_contract["bid"]) + float(put_contract["ask"])) /2.0

    net_credit = call_mid - put_mid
    breakeven = round(spot + put_mid - call_mid,2)
    
    max_profit = (Kc - spot + net_credit) * 100.0
    min_profit = -1*(spot - Kp - net_credit) * 100.0

    initial_investment = (spot - net_credit) * 100.0
        
    min_return = round((min_profit / initial_investment) * 100,2)
    max_return = round((max_profit / initial_investment) * 100,2)

    annualized_min_return = round(100* (((1+min_return/100) ** (365/dte))-1),2)
    annualized_max_return = round(100* (((1+max_return/100) ** (365/dte))-1),2)
    

    reward_to_risk = -1 if min_profit == 0 else round(-1 * (max_profit) / (min_profit),1)
    term_BE_drift = (breakeven - spot) / spot
    annualized_BE_drift =100*((1+term_BE_drift) ** (365/dte) - 1)

    

    #if 1> 0:
    if annualized_BE_drift < MAX_ANNUALIZED_BE_DRIFT and annualized_max_return > MIN_ANNUALIZED_MAX_RETURN and annualized_min_return > MIN_ANNUALIZED_MIN_RETURN and (reward_to_risk >  MIN_REWARD_TO_RISK or reward_to_risk < 0):
        if global_min_roi is None or annualized_min_return > global_min_roi:
            global_min_roi = annualized_min_return
        # if 1>0:
        #     print(f"{ticker}, {put_contract["expiration_date"]}, {round(initial_investment)}, Kp={Kp}, Kc={Kc}, max profit = {round(max_profit)}, max loss = {round(min_profit)}, Min ROI: {annualized_min_return}%, Max ROI: {annualized_max_return}%, r-to-r={reward_to_risk}, BE={breakeven}, BE_drift = {round(annualized_BE_drift,1)}%")
        if verbose:
            print(f"call price = {call_mid}, put price = {put_mid}")
    return global_min_roi
        

async def find_valid_expirations(ticker, client):
    unfiltered_exps = await list_expirations(ticker, client=client)
    today =date.today()
    six_months_later = today + relativedelta(months=5)
    filtered = [
        d for d in unfiltered_exps
        if datetime.strptime(d, "%Y-%m-%d").date() >= six_months_later
    ]
    return filtered

# Retrieve a list of exps 6 months or more in the future.
async def find_best_leap(ticker,client, spot = None, verbose=False):
    global_min_roi = None
    if spot == None:
        spot = await get_underlying_price(ticker, client=client)
        if spot is None:
            if verbose:
                print(f"Can't find spot for {ticker}")
            return
        if spot > 30:
            return
    # print(f"{ticker} spot={round(spot,2)}")
    
    filtered = await find_valid_expirations(ticker, client)
    for expiration_date in filtered:
        # print(ticker, expiration_date, "...")
        global_min_roi = await analyze(ticker, client, expiration_date, spot, global_min_roi, verbose)
    if global_min_roi is not None:
        print(f"{ticker}, {global_min_roi}")     


async def main():
    async with TradierClient(api_key=TRADIER_API_KEY) as client:
        for ticker in nyse_arca_list:
            await find_best_leap(ticker, client,None, verbose=False)
   
if __name__ == "__main__":
    asyncio.run(main())


# if __name__ == "__main__":
    

#     smaller_list = ["HIMS", "AI", "ADT", "BOX", "ACHR", "BBAI", "BE", "ACVA", "CHGG", "QBTS"]

#     for ticker in smaller_list:
#         spot = None
#         asyncio.run(find_best_leap(ticker, spot, verbose=False))
        