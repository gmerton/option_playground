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