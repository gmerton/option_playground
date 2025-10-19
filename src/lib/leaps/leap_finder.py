import os, asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price
from lib.commons.list_expirations import list_expirations
from dateutil.relativedelta import relativedelta

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
    call =  min(
        eligible,
        key = lambda x:x[0]
    )[1]
    call_mid = (call["bid"] + call["ask"])/ 2

    return call



async def test(ticker, expiry, verbose = False):
    
    dte = ((datetime.strptime(expiry, "%Y-%m-%d")).date() - date.today()).days
    spot = await get_underlying_price(ticker)
    contracts = await list_contracts_for_expiry(ticker, expiry)
    if verbose:
        print(f"underlying spot={spot}")
    tie_breaker = "higher"
    puts = [c for c in contracts if c.get("option_type").lower() == "put"]
    tie_breaker = "higher"
    prefer_high = (tie_breaker != "lower")
    atm_put_contract = min(
        puts,
        key = lambda c: (
            abs(c["strike"]- spot),
            0 if (c["strike"] >= spot) == prefer_high else 1,
            c["strike"] if prefer_high else -c["strike"]
        )
    )
    put_bid, put_ask = atm_put_contract["bid"], atm_put_contract["ask"]
    put_mid = (put_bid + put_ask) /2
    call_contract = find_call(spot, contracts, atm_put_contract)
    if verbose:
        print(f"atm put strike ={atm_put_contract["strike"]}, price = {put_mid}")
        print(f"call strike = {call_contract["strike"]}")
    profitability(ticker, spot, call_contract, atm_put_contract, dte)

def profitability(ticker, spot, call_contract, put_contract, dte):
    # strikes
    Kc = float(call_contract["strike"])
    Kp = float(put_contract["strike"])

    call_mid = (float(call_contract["bid"]) + float(call_contract["ask"])) /2.0
    put_mid = (float(put_contract["bid"]) + float(put_contract["ask"])) /2.0

    net_credit = call_mid - put_mid
    max_profit = (Kc - spot + net_credit) * 100.0
    min_profit = -1*(spot - Kp - net_credit) * 100.0

    initial_investment = (spot + net_credit) * 100.0
        
    min_return = round((min_profit / initial_investment) * 100,2)
    max_return = round((max_profit / initial_investment) * 100,2)

    annualized_min_return = round(100* (((1+min_return/100) ** (365/dte))-1),2)
    annualized_max_return = round(100* (((1+max_return/100) ** (365/dte))-1),2)
    expiry = call_contract["expiration_date"]
    # print(f"put delta = {put_contract["greeks"]["delta"]}, call delta = {call_contract["greeks"]["delta"]}")
    # print(f"put IV = {round(put_contract["greeks"]["smv_vol"],3)}, call IV = {round(call_contract["greeks"]["smv_vol"],3)}")
    
    # print(f"  Profit range: [{round(min_profit)},{round(max_profit)}]")
    # print(f"  [{min_return},{max_return}]")
    #print(f"Annualized profit range: [{annualized_min_return},{annualized_max_return}]")
    print(f"{ticker}, {expiry}, max guaranteed annualized profit: {annualized_max_return}")
        

 # Retrieve a list of exps 6 months or more in the future.
async def find_best_leap(ticker):
    unfiltered_exps = await list_expirations(ticker)
    today =date.today()
    six_months_later = today + relativedelta(months=12)
    filtered = [
        d for d in unfiltered_exps
        if datetime.strptime(d, "%Y-%m-%d").date() >= six_months_later
    ]
    for expiration_date in filtered:
        await test(ticker, expiration_date)     

if __name__ == "__main__":
    #HPE: bad
    #SOFI: good
    #APLD: good (1/15/2027)
    #HIMS: good
    #CHWY: mid
    #OXY bad
    #CMG mid
    #GTLB mid
    #BAC bad
    # SLV bad
    # Path mid
    # GRAB, 2027-01-15, max guaranteed annualized 
    # FUBO, 2027-01-15, max guaranteed annualized profit: 22.69
    # AMC, 2027-01-15, max guaranteed annualized profit: 31.09
    
    # profit: 27.02
    # tickers = ["PATH", "FUBO", "SLV", "OPEN", "AMC"]
    # for ticker in tickers:
    #     asyncio.run(find_best_leap(ticker))
    # */
    
    #Run this for more details on a single idea
    #asyncio.run(test("AMC", '2027-01-15', True))
 