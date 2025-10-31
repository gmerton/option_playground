import os, asyncio
from datetime import datetime, date
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price
from lib.commons.list_expirations import list_expirations
from dateutil.relativedelta import relativedelta


# This module identifies opportunities for LEAP collar plays: long 100 shares, a protective ATM put, and a covered call.
# Been finding the LT skew column in oquants to be useful in pre-screening.


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



async def analyze(ticker, expiry, spot, verbose = False):
    
    dte = ((datetime.strptime(expiry, "%Y-%m-%d")).date() - date.today()).days
    
    #spot = await get_underlying_price(ticker)
    #spot = 15.28
    contracts = await list_contracts_for_expiry(ticker, expiry)
    if verbose:
        print(f"underlying spot={round(spot,2)}")
    tie_breaker = "higher"
    
    
    put_contracts = [c for c in contracts if c.get("option_type").lower() == "put"]
    call_contracts = [c for c in contracts if c.get("option_type").lower() == "call"]
    
    tie_breaker = "higher"
    prefer_high = (tie_breaker != "lower")
    atm_put_contract = min(
        put_contracts,
        key = lambda c: (
            abs(c["strike"]- spot),
            0 if (c["strike"] >= spot) == prefer_high else 1,
            c["strike"] if prefer_high else -c["strike"]
        )
    )
    put_bid, put_ask = atm_put_contract["bid"], atm_put_contract["ask"]
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
            if put_contract["strike"] > atm_put_contract_strike:
                continue
            # profitability(ticker, spot, breakeven_call_contract, atm_put_contract, dte)
            profitability(spot, call_contract, put_contract, dte, verbose)


MAX_ANNUALIZED_BE_DRIFT = 8
MIN_ANNUALIZED_MAX_RETURN =  50.0
MIN_ANNUALIZED_MIN_RETURN = -12
MIN_REWARD_TO_RISK = 3

# MAX_ANNUALIZED_BE_DRIFT = 30
# MIN_ANNUALIZED_MAX_RETURN =  0
# MIN_ANNUALIZED_MIN_RETURN = 0
# MIN_REWARD_TO_RISK = 0

def profitability(spot, call_contract, put_contract, dte, verbose = False):
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
        
        print(f"Kp={Kp}, Kc={Kc}, max profit = {round(max_profit)}, max loss = {round(min_profit)}, Min ROI: {annualized_min_return}%, Max ROI: {annualized_max_return}%, r-to-r={reward_to_risk}, BE={breakeven}, BE_drift = {round(annualized_BE_drift,1)}%")
        if verbose:
            print(f"call price = {call_mid}, put price = {put_mid}")
        

async def find_valid_expirations(ticker):
    unfiltered_exps = await list_expirations(ticker)
    today =date.today()
    six_months_later = today + relativedelta(months=5)
    filtered = [
        d for d in unfiltered_exps
        if datetime.strptime(d, "%Y-%m-%d").date() >= six_months_later
    ]
    return filtered
 # Retrieve a list of exps 6 months or more in the future.
async def find_best_leap(ticker, spot = None, verbose=False):
    if spot == None:
        spot = await get_underlying_price(ticker)
        if spot is None:
            print(f"Can't find spot for {ticker}")
            return
    print(f"{ticker} spot={round(spot,2)}")
    
    filtered = await find_valid_expirations(ticker)
    for expiration_date in filtered:
        print(ticker, expiration_date, "...")
        await analyze(ticker, expiration_date, spot, verbose)     

if __name__ == "__main__":
    #HPE: bad
    #APLD: good (1/15/2027)
    #HIMS: good
    #CHWY: mid
    #OXY bad
    #CMG mid
    #GTLB mid
    #BAC bad
    # SLV bad
    # Path mid
    # CPNG mid (14)
    # ONON bad
    # NVO bad
    # BROS bad
    # SIRI bad
    # KHC bad
    # BB mid (18)
    # HIVE bad
    # JBLUE good
    # AEO bad
    # BEKE bad
    # JOBY bad

    #GRAB 2027-01-15 ...Kp=5.5, Kc=10.0, max profit = 417, max loss = -33, Min ROI: -4.58%, Max ROI: 54.31%, r-to-r=12.6, BE=5.83, BE_drift = 2.5%
    #GRAB Kp=5.5, Kc=12.0, max profit = 600, max loss = -51, Min ROI: -6.82%, Max ROI: 74.47%, r-to-r=11.9, BE=6.0, BE_drift = 4.9%

    #GRAB, FUBO, AMC all have choices.
    #APLD has some expiring in 4/2026 that look good.
    # Kp=32.0, Kc=42.0, max profit = 854, max loss = -146, Min ROI: -8.58%, Max ROI: 58.2%, r-to-r=5.9, BE=33.45, BE_drift = -5.9%
    # NCLH bad
    # WRBY bad
    # SIRI bad
    # XPEV: 2027-01-15
    # UUUU: 2026-06-18, 2027-01-15
    # NLY 2026-04-17
    # RIOT multilple dates.  Best in 2026-05-15
    # MARA multiple. 
    # RUN: 2027-01-15
    # CAN: good
    # NB: good
    # DPRO: no
    # PATH: yes
    # ETH: yes
    # XRT: yes
    # ETHA: yes
    # IE: NO
    #AES: Yes
    # WBD: Yes
    #KHC: in buffet's portfolio. yes. But headed downhill.
    # QSI no
    # BTBT yes: has some nice ones due in May
    #tickers = [ "NB",  "ETH", "XRT", "ETHA", "AES", "WBD",  "HIMS", "CMG", "GRAB", "FUBO", "APLD", "XPEV", "UUUU",   "MARA"]
    
    ravish_list = ["AVGO",
"NVDA",
"GS",
"COST",
"META",
"BIDU",
"JPM",
"CRWD",
"PLTR",
"LULU",
"MSFT",
"TSLA",
"APP",
"WMT",
"TSM",
"ADBE",
"CAT",
"SNOW",
"COIN",
"NFLX",
"CRWV",
"PANW",
"ARM",
"ASML",
"XYZ",
"MU",
"SOFI",
"DELL",
"MS",
"JNJ",
"BAC",
"UBER",
"CHWY",
"CVNA",
"SGOV",
"GE",
"TGT",
"C",
"WFC",
"AMD",
"HPE",
"CMG",
"APLD",
"OXY",
"HD",
"QQQ",
"PEP",
"HIM",
"CRCL",
"FIG",
"SMCI",
"GTLB",
"DG",
"CRM"]
    tickers = ravish_list
    for ticker in tickers:
         # spot = 15.28
         spot = None
         asyncio.run(find_best_leap(ticker, spot, verbose=False))
         #asyncio.run(test("CMPO", '2026-03-20', True))
    
    
    
    #Run this for more details on a single idea
    #asyncio.run(test("JBLU", '2028-01-21', True))
    # asyncio.run(test("APLD", '2027-01-15', True))
 
 