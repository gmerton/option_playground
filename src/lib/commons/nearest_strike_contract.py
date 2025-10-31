def expected_move(contracts, spot):
    call_contract = nearest_strike_contract(contracts, spot, "call")
    put_contract  = nearest_strike_contract(contracts, spot, "put")
    c_mid = (call_contract["bid"] + call_contract["ask"])/2.0
    p_mid = (put_contract["bid"] + put_contract["ask"]) / 2.0
    straddle_mid = c_mid + p_mid
    expected_move = straddle_mid / spot
    expected_left = spot * (1-expected_move)
    expected_right = spot * (1+ expected_move)
    #c_iv = call_contract["greeks"]["mid_iv"]
    # p_iv = put_contract["greeks"]["mid_iv"]
    return round(expected_left,2), round(expected_right,2)



def nearest_strike_contract(contracts, spot, cp):
    """
    Pick the contract dict from _list_contracts_for_expiry nearest to spot
    cp can be 'call' or 'put'
    """
    side = [c for c in contracts if c["option_type"]==cp]
    if not side:
        return None
    return min(side, key=lambda c: abs(c["strike"]-spot))

# Suppose your list is named `option_chain`

def find_nearest_delta_option(option_chain, target_delta):
    # Filter out any options that are missing delta values
    # valid_options = [opt for opt in option_chain if opt.get("greeks") and "delta" in opt["greeks"]]
    # if not valid_options:
    #     return None

    
    # Find the option whose delta is closest to the target_delta
    return min(option_chain, key=lambda opt: abs(opt["greeks"]["delta"] - target_delta))

# Example usage:
# nearest_30_delta = find_nearest_delta_option(option_chain, 0.30)
# print(nearest_30_delta)
