import os, asyncio
from datetime import datetime, date
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price
from lib.commons.list_expirations import list_expirations
from lib.commons.nearest_strike_contract import find_nearest_delta_option
from dateutil.relativedelta import relativedelta





async def analyze(ticker, expiry,short_delta, long_delta):
    
    dte = ((datetime.strptime(expiry, "%Y-%m-%d")).date() - date.today()).days
    
    #spot = await get_underlying_price(ticker)
    #spot = 15.28
    contracts = await list_contracts_for_expiry(ticker, expiry)
    
    
    put_contracts = [c for c in contracts if c.get("option_type").lower() == "put"]
    short_put = find_nearest_delta_option(put_contracts, target_delta=-1*short_delta)
    long_put = find_nearest_delta_option(put_contracts, target_delta=-1*long_delta)
    

    short_put_mid = (short_put["bid"] + long_put["ask"])/2
    long_put_mid = (long_put["bid"] + long_put["ask"])/2
    short_put_strike = short_put["strike"]
    long_put_strike = long_put["strike"]

    max_profit = 100*(short_put_mid - long_put_mid)
    min_profit = 100*((short_put_mid-long_put_mid) - short_put_strike + long_put_strike)
    reward_to_risk = -1 if min_profit == 0 else  round(max_profit / abs(min_profit),3)
    print(f"{ticker}, {expiry}, Short=({short_put_strike}, {round(short_put_mid,3)}), Long=({long_put_strike},{round(long_put_mid,3)}), max={round(max_profit)}, min={round(min_profit)}, r_to_r={reward_to_risk}")


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
        
#Look for expirations between 30 and 45 days.
async def find_valid_expirations(ticker):
    unfiltered_exps = await list_expirations(ticker)
    today =date.today()
    earliest_dte = today + relativedelta(days=30)
    latest_dte = today + relativedelta(days=45)
    filtered = [
        d for d in unfiltered_exps
        if datetime.strptime(d, "%Y-%m-%d").date() >= earliest_dte and datetime.strptime(d, "%Y-%m-%d").date()<= latest_dte
    ]
    return filtered

# Retrieve a list of exps 6 months or more in the future.
async def evaluate_credit_spread(ticker, short_delta, long_delta):
    
    filtered = await find_valid_expirations(ticker)
    for expiration_date in filtered:
        #print(ticker, expiration_date, "...")
        await analyze(ticker, expiration_date, short_delta, long_delta)     

if __name__ == "__main__":
  
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

    ff_list = ["FTNT", "FUBO", "CSIQ", "WYNN", "SNAP", "IRBT", "XPEV", "CELH", "AMKR", ]
    tickers = ["STZ", "SIRI"]
    for ticker in ["TLT", "USO", "IBIT"]:
         asyncio.run(evaluate_credit_spread(ticker,0.3,0.15 ))
     
 
 