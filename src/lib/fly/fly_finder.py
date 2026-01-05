import os, asyncio
from datetime import datetime, date
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.get_underlying_price import get_underlying_price
from lib.commons.list_expirations import list_expirations
from dateutil.relativedelta import relativedelta


# Run this from the root directory with PYTHONPATH=src python -m lib.fly.fly_finder


async def find_fly(ticker, spot = None, verbose=False):
    global_min_roi = None
    if spot == None:
        spot = await get_underlying_price(ticker)
        print(spot)
        if spot is None:
            if verbose:
                print(f"Can't find spot for {ticker}")
            return
    print(f"{ticker} spot={round(spot,2)}")
    
    filtered = await find_valid_expirations(ticker)
    for expiration_date in filtered:
         global_min_roi = await get_contracts(ticker, expiration_date, spot, global_min_roi, verbose)
    # if global_min_roi is not None:
    #     print(f"{ticker}, {global_min_roi}") 

async def get_contracts(ticker, expiry, spot,  global_min_roi, verbose = False):
    dte = ((datetime.strptime(expiry, "%Y-%m-%d")).date() - date.today()).days
    
    contracts = await list_contracts_for_expiry(ticker, expiry)
    if contracts is None:
        return
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
    atm_strike = atm_put_contract["strike"]
    
    atm_call_contract = next(
    c for c in call_contracts if c["strike"] == atm_strike
    )


    call_above_atm = min(
        (c for c in call_contracts if c["strike"] > atm_strike),
        key=lambda c: c["strike"],
        default=None
    )

    if call_above_atm["bid"] is None:
        return

    
    put_below_atm = max(
        (c for c in put_contracts if c["strike"] < atm_strike),
        key=lambda c: c["strike"],
        default=None
    )

    profitability(spot, expiry, atm_put_contract, atm_call_contract, put_below_atm, call_above_atm,
    dte, global_min_roi,  verbose)

def profitability(spot,expiry,atm_put_contract, atm_call_contract, put_below_atm, call_above_atm, dte, global_min_roi, verbose = False):
    
    atm_strike = atm_put_contract["strike"]
    
    atm_put_mid = (float(atm_put_contract["bid"]) + float(atm_put_contract["ask"]))/2.0
    atm_call_mid = (float(atm_call_contract["bid"]) + float(atm_call_contract["ask"]))/2.0
    long_put_mid = (float(put_below_atm["bid"]) + float(put_below_atm["ask"]))/2.0
    long_call_mid = (float(call_above_atm["bid"]) + float(call_above_atm["ask"]))/2.0
    
    #initial credit is also the max profit.
    initial_credit = atm_put_mid + atm_call_mid - long_put_mid - long_call_mid
    
    

    bull_wing_max_loss = call_above_atm["strike"] - atm_strike - initial_credit
    bear_wing_max_loss = atm_strike - put_below_atm["strike"] -initial_credit

    max_loss = min(bull_wing_max_loss, bear_wing_max_loss)

    lower_breakeven = atm_strike - initial_credit
    upper_breakeven = atm_strike + initial_credit

    credit_per_wing_width = initial_credit / (call_above_atm["strike"] - atm_strike)

    width_over_spot = (call_above_atm["strike"] - atm_strike)/spot

    print(f"{expiry} strikes = {put_below_atm["strike"]},{atm_strike},{call_above_atm["strike"]}, max profit = {round(100*initial_credit,2)}, max loss = {round(100*max_loss,2)}, BE = {lower_breakeven}, {upper_breakeven}, C/W={round(credit_per_wing_width,2)}, W/S={round(100*width_over_spot,1)}%")


    # strikes
    # Kc = float(call_contract["strike"])
    # Kp = float(put_contract["strike"])

    # call_mid = (float(call_contract["bid"]) + float(call_contract["ask"])) /2.0
    # put_mid = (float(put_contract["bid"]) + float(put_contract["ask"])) /2.0

    # net_credit = call_mid - put_mid
    # breakeven = round(spot + put_mid - call_mid,2)
    
    # max_profit = (Kc - spot + net_credit) * 100.0
    # min_profit = -1*(spot - Kp - net_credit) * 100.0

    # initial_investment = (spot - net_credit) * 100.0
        
    # min_return = round((min_profit / initial_investment) * 100,2)
    # max_return = round((max_profit / initial_investment) * 100,2)

    # annualized_min_return = round(100* (((1+min_return/100) ** (365/dte))-1),2)
    # annualized_max_return = round(100* (((1+max_return/100) ** (365/dte))-1),2)
    

    # reward_to_risk = -1 if min_profit == 0 else round(-1 * (max_profit) / (min_profit),1)
    # term_BE_drift = (breakeven - spot) / spot
    # annualized_BE_drift =100*((1+term_BE_drift) ** (365/dte) - 1)

    

    # #if 1> 0:
    # if annualized_BE_drift < MAX_ANNUALIZED_BE_DRIFT and annualized_max_return > MIN_ANNUALIZED_MAX_RETURN and annualized_min_return > MIN_ANNUALIZED_MIN_RETURN and (reward_to_risk >  MIN_REWARD_TO_RISK or reward_to_risk < 0):
    #     if global_min_roi is None or annualized_min_return > global_min_roi:
    #         global_min_roi = annualized_min_return
    #     if verbose:
    #         print(f"Kp={Kp}, Kc={Kc}, max profit = {round(max_profit)}, max loss = {round(min_profit)}, Min ROI: {annualized_min_return}%, Max ROI: {annualized_max_return}%, r-to-r={reward_to_risk}, BE={breakeven}, BE_drift = {round(annualized_BE_drift,1)}%")
    #     if verbose:
    #         print(f"call price = {call_mid}, put price = {put_mid}")
    # return global_min_roi


async def find_valid_expirations(ticker):
    unfiltered_exps = await list_expirations(ticker)
    today =date.today()
    oldest_strike = today + relativedelta(days=12)
    filtered = [
        d for d in unfiltered_exps
        if datetime.strptime(d, "%Y-%m-%d").date() <= oldest_strike
    ]
    return filtered

if __name__ == "__main__":
    print("hello world")
    asyncio.run(find_fly('LUNR', None, verbose=False))
    # for ticker in ["AG", "USAR", "QS", "SOUN", "HL", "LUNR", "CDE", "PL", "PAAS", "UUUU", "JD", "CRML","PATH", "LUNR", "SERV", "CDE", "QUBT", "INTC", "GLXY", "CLSK", "QBTS", "RGTI", "NVO"]:
    #     asyncio.run(find_fly(ticker, None, verbose=False))
        