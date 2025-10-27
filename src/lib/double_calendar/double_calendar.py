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
    
    print(start_date_str, end_date_str)
   
    return near_chain, far_chain




async def run(ticker):
    spot = await get_underlying_price(ticker)
    near_contracts, far_contracts = await get_chains(ticker)
    
    #These are the approximate strikes of the two spreads
    left_expected, right_expected = expected_move(near_contracts, spot)
    print(left_expected, right_expected)
    near_strike_put_contract = nearest_strike_contract(near_contracts, spot, "put")
    near_strike_call_contract = nearest_strike_contract(near_contracts, spot, "call")
    far_strike_put_contract = nearest_strike_contract(far_contracts, spot, "put")
    far_strike_call_contract = nearest_strike_contract(far_contracts, spot, "call")
    profitability( near_strike_put_contract, near_strike_call_contract, far_strike_put_contract, far_strike_call_contract)

def contract_mid(contract):
    return (contract["bid"]+contract["ask"])/2

def profitability(near_strike_put_contract, near_strike_call_contract, far_strike_put_contract, far_strike_call_contract):
    initial_debit = 100* (contract_mid(far_strike_call_contract) + contract_mid(far_strike_put_contract) - contract_mid(near_strike_call_contract)- contract_mid(near_strike_put_contract))
    print(round(initial_debit))

    # Calculate break even
    #wing_width = near_strike_call_contract["strike"]-near_strike_put_contract["strike"]
    # upper_be = near_strike_call_contract[]




if __name__=="__main__":
    ticker = "AMZN"
    range = asyncio.run(run(ticker))
    # spot = await get_underlying_price(ticker)
    # print(range)
