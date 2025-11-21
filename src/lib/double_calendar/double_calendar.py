import os, asyncio
from datetime import datetime, date
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price
from lib.commons.nearest_strike_contract import expected_move, nearest_strike_contract
from lib.commons.list_expirations import list_expirations

from dateutil.relativedelta import relativedelta


# Find expected move based on near date ATM straddle


#Ravish likes to find near date that expires in 10-15 days.
async def get_chains(ticker):
    unfiltered_exps = await  list_expirations(ticker)
    today = date.today()
    
    unfiltered_exps = await list_expirations(ticker)
    today =date.today()
    
    start_date_near_boundary = today + relativedelta(days=10)
    start_date_far_boundary = today + relativedelta(days=15)
    
    filtered_start_dates = [
        d for d in unfiltered_exps
        if datetime.strptime(d, "%Y-%m-%d").date() >= start_date_near_boundary and datetime.strptime(d, "%Y-%m-%d").date()<= start_date_far_boundary
    ]

    if len(filtered_start_dates)==0:
        return None, None
    start_date_str = filtered_start_dates[0]
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() 
    
    end_date_near_boundary = start_date + relativedelta(days=7)
    end_date_far_boundary = start_date + relativedelta(days = 14)

    filtered_end_dates = [
        d for d in unfiltered_exps
        if datetime.strptime(d, "%Y-%m-%d").date() >= end_date_near_boundary and datetime.strptime(d, "%Y-%m-%d").date() <= end_date_far_boundary
    ]
    
    end_date_str = filtered_end_dates[0]
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    near_chain = await list_contracts_for_expiry(ticker, start_date_str)
    far_chain = await list_contracts_for_expiry(ticker, end_date_str)
    
    
    return near_chain, far_chain




async def run(ticker):
    spot = await get_underlying_price(ticker)
    near_contracts, far_contracts = await get_chains(ticker)
    if near_contracts is None:
        return
    atm_near_contract = nearest_strike_contract(near_contracts, spot, "call")
    atm_far_contract = nearest_strike_contract(far_contracts, spot, "call")

    #These are the approximate strikes of the two spreads
    left_expected, right_expected = expected_move(near_contracts, spot)
    #print(left_expected, right_expected)
    near_strike_put_contract = nearest_strike_contract(near_contracts, spot, "put")
    near_strike_call_contract = nearest_strike_contract(near_contracts, spot, "call")
    far_strike_put_contract = nearest_strike_contract(far_contracts, spot, "put")
    far_strike_call_contract = nearest_strike_contract(far_contracts, spot, "call")
    
    near_atm_call_iv = atm_near_contract["greeks"]["mid_iv"]
    far_atm_call_iv = atm_far_contract["greeks"]["mid_iv"]
    
    atm_iv_drop = round(100 * (near_atm_call_iv - far_atm_call_iv),1)
    
    near_strike_call_iv = near_strike_call_contract["greeks"]["mid_iv"]
    far_strike_call_iv = far_strike_call_contract["greeks"]["mid_iv"]
    
    near_call_strike = near_strike_call_contract["strike"]
    
    iv_drop = round(100*near_strike_call_iv - far_strike_call_iv,1)
    print(f"{ticker}, {atm_near_contract["expiration_date"]}, {atm_far_contract["expiration_date"]},near={near_atm_call_iv}, far={far_atm_call_iv},atm_iv_drop={atm_iv_drop}")
    
    # profitability( near_strike_put_contract, near_strike_call_contract, far_strike_put_contract, far_strike_call_contract)

def contract_mid(contract):
    return (contract["bid"]+contract["ask"])/2

def profitability(near_strike_put_contract, near_strike_call_contract, far_strike_put_contract, far_strike_call_contract):
    initial_debit = 100* (contract_mid(far_strike_call_contract) + contract_mid(far_strike_put_contract) - contract_mid(near_strike_call_contract)- contract_mid(near_strike_put_contract))
    print(round(initial_debit))

    # Calculate break even
    #wing_width = near_strike_call_contract["strike"]-near_strike_put_contract["strike"]
    # upper_be = near_strike_call_contract[]


ravish_list = [
#     "AVGO",
# "NVDA",
# "GS",
# "COST",
# "META",
# "BIDU",
# "JPM",
# "CRWD",
# "PLTR",
# "LULU",
# "MSFT",
# "TSLA",
# "APP",
# "WMT",
# "TSM",
# "ADBE",
# "CAT",
# "SNOW",
# "COIN",
# "NFLX",
# "CRWV",
# "PANW",
# "ARM",
# "ASML",
# "XYZ",
# "MU",
# "SOFI",
# "DELL",
# "MS",
# "JNJ",
# "BAC",
# "UBER",
# "CHWY",
# "CVNA",
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

if __name__=="__main__":
    #ticker = "AMZN"
    tickers = ravish_list
    for ticker in ravish_list:
        range = asyncio.run(run(ticker))
    