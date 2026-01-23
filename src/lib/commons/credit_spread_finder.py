from __future__ import annotations

from typing import Optional, List, Dict, Any
import aiohttp
from lib.commons.get_underlying_price import get_underlying_price

import aiohttp
from datetime import date, timedelta
import pandas as pd
import pandas_ta as ta
from dataclasses import dataclass
import numpy as np
from lib.commons.nyse_arca_list import nyse_arca_list, ravish_list, vrp_list, vrp_list2, nasdaq_list
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.list_expirations import list_expirations
from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_daily_history
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
import math
import  asyncio
import os

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}


async def screen(symbol, client: TradierClient, verbose = False):
    try:
        end = date.today()
        start = end - timedelta(days=50)
        expirations = await list_expirations(symbol, client=client)
        df = await get_daily_history(symbol, start, end, client=client)

        # 10 DTE condor filter
        condor_10_rv_ok = rv20_not_rising(df, sma_window=3)

        # 30 DTE condor filter
        condor_30_rv_ok = rv20_not_rising(df, sma_window=10)
        
        #condor_rv_ok = rv20_ma_not_rising(df, ma_days=5)
        if df is None:
            return

        di_plus, di_minus, adx = compute_adx_14(symbol, df)
        # if adx >= 25:
        #    return

        skew_ratio, put_iv, call_iv, expiry = await compute_skew_30d_proxy(symbol, expirations, client=client)
        # if skew_ratio <= 1.15:
        #     return

        spot = await get_underlying_price(symbol, client=client)
        symbol_rv = compute_rv_20(df)
        iv30 = await compute_iv_30_interpolated(symbol, spot, expirations, client=client)
        vrp = round(iv30 / symbol_rv, 2)

        # if vrp < 1.1:
        #     return
        

        #Check for spread
        if (adx < 25 or di_plus > di_minus) and skew_ratio > 1.15 and vrp > 1.1:

            print(
            f"Spread: {symbol}, adx={adx:.2f}, "
            f"DI+ ={di_plus:.2f}, DI- ={di_minus:.2f},"
            f"rv={symbol_rv:.2f}, iv={iv30:.2f}, "
            f"vrp={vrp}, skew_ratio={skew_ratio:.2f}"
        )
            
        # Check for 10 DTE codor
        if abs(di_plus-di_minus) < 8 and vrp > 1.15 and skew_ratio > 1.05 and skew_ratio < 1.30 and condor_10_rv_ok and adx<20:
                print(
            f"30 DTE Condor: {symbol}, adx={adx:.2f}, "
            f"DI+ ={di_plus:.2f}, DI- ={di_minus:.2f},"
            f"rv={symbol_rv:.2f}, iv={iv30:.2f}, "
            f"vrp={vrp}, skew_ratio={skew_ratio:.2f}"
        )
                
        # Check for 30 DTE codor
        if abs(di_plus-di_minus) < 10 and vrp > 1.25 and skew_ratio > 1.05 and skew_ratio < 1.35 and condor_30_rv_ok and adx<25:
                print(
            f"10 DTE Condor: {symbol}, adx={adx:.2f}, "
            f"DI+ ={di_plus:.2f}, DI- ={di_minus:.2f},"
            f"rv={symbol_rv:.2f}, iv={iv30:.2f}, "
            f"vrp={vrp}, skew_ratio={skew_ratio:.2f}"
        )
    
    except RuntimeError as e:
        # Swallow known, non-fatal screening failures
        # Optional: log if you want visibility
        # print(f"[SKIP] {symbol}: {e}")
        # print(f"{symbol},  {e}")
        return

    



def rv20_not_rising(
    df: pd.DataFrame,
    *,
    sma_window: int,
    rv_window: int = 20,
) -> bool:
    """
    Generic "RV not rising" test used for condor regime filters.

    Returns True if:
        RV(rv_window)_today <= SMA_sma_window( RV(rv_window) )

    Examples:
        # 10 DTE condor filter:
        rv_ok_10dte = rv20_not_rising(df, sma_window=3)

        # 30 DTE condor filter:
        rv_ok_30dte = rv20_not_rising(df, sma_window=10)

    Notes:
      - Uses close-to-close log returns, annualized with sqrt(252).
      - Raises RuntimeError if df is None/empty or lacks sufficient data.
    """
    if df is None or df.empty or "close" not in df.columns:
        raise RuntimeError("rv20_not_rising: df is None/empty or missing 'close'")

    closes = pd.to_numeric(df["close"], errors="coerce").dropna()
    min_closes = rv_window + sma_window + 1
    if len(closes) < min_closes:
        raise RuntimeError(
            f"rv20_not_rising: not enough data (need >= {min_closes} closes; have {len(closes)})"
        )

    # log returns
    log_returns = np.log(closes / closes.shift(1)).dropna()

    # realized vol series (annualized)
    rv = log_returns.rolling(rv_window).std() * np.sqrt(252)
    rv = rv.dropna()

    if len(rv) < sma_window:
        raise RuntimeError(
            f"rv20_not_rising: insufficient RV history (need >= {sma_window} RV points; have {len(rv)})"
        )

    rv_today = float(rv.iloc[-1])
    rv_sma = float(rv.iloc[-sma_window:].mean())

    return rv_today <= rv_sma



def compute_rv_20(df: pd.DataFrame) -> float:
    """
    Compute 20-day realized volatility (close-to-close), annualized.

    Returns:
        float: RV20 as a decimal (e.g. 0.22 = 22%)
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must contain a 'close' column")

    closes = pd.to_numeric(df["close"], errors="coerce").dropna()
       
    if len(closes) < 21:
        print(len(closes))
        print("whatever")
        raise RuntimeError("Need at least 21 closing prices to compute RV20")

    # log returns
    log_returns = np.log(closes / closes.shift(1))

    # 20-day rolling realized vol, annualized
    rv20 = log_returns.rolling(20).std() * np.sqrt(252)

    return float(rv20.dropna().iloc[-1])

def compute_adx_14(symbol: str, df: pd.DataFrame):
    ind = ta.adx(high=df["high"], low = df["low"], close = df["close"], length=14)
    if ind is None:
        raise RuntimeError(f"ind is None for {symbol}")
    df2 = df.join(ind).dropna()
    if df2.empty:
        raise RuntimeError(f"Not enough data to compute ADX for {symbol}")
    last = df2.iloc[-1]
    asof = df2.index[-1]
    di_plus = float(last["DMP_14"])
    di_minus = float(last["DMN_14"])
    adx = float(last["ADX_14"])
    #print(f"{di_plus}, {di_minus}, {adx}")
    return (di_plus, di_minus, adx)

def _parse_ymd(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()

def _safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None

def atm_iv_for_expiry(
    contracts: List[Dict[str, Any]],
    underlying_price: float,
) -> Optional[float]:
    """
    Returns an ATM implied vol for this expiry (decimal, e.g. 0.24).
    Uses greeks['mid_iv'] or greeks['iv'] if present.
    Computes ATM IV as average(call_iv, put_iv) at the strike closest to spot.
    """
    if not contracts:
        return None

    # Group by strike
    by_strike: dict[float, dict[str, Dict[str, Any]]] = {}
    for c in contracts:
        k = c.get("strike")
        if k is None:
            continue
        by_strike.setdefault(float(k), {})[c.get("option_type")] = c

    if not by_strike:
        return None

    # Choose ATM strike
    atm_strike = min(by_strike.keys(), key=lambda k: abs(k - underlying_price))
    legs = by_strike[atm_strike]

    def extract_iv(opt: Dict[str, Any]) -> Optional[float]:
        g = opt.get("greeks") or {}
        # Tradier greeks commonly include mid_iv; sometimes iv.
        return _safe_float(g.get("mid_iv") or g.get("iv") or g.get("implied_volatility"))

    call_iv = extract_iv(legs.get("call")) if legs.get("call") else None
    put_iv  = extract_iv(legs.get("put"))  if legs.get("put")  else None

    # Prefer average of both if available; otherwise use the one we have.
    if call_iv is not None and put_iv is not None:
        return 0.5 * (call_iv + put_iv)
    return call_iv if call_iv is not None else put_iv

def _extract_iv(opt: Dict[str, Any]) -> Optional[float]:
    """
    Tradier greeks usually include 'mid_iv'. Sometimes 'iv' or similar.
    Returns decimal IV (e.g. 0.23).
    """
    g = opt.get("greeks") or {}
    return _safe_float(g.get("mid_iv") or g.get("iv") or g.get("implied_volatility"))

def _extract_delta(opt: Dict[str, Any]) -> Optional[float]:
    g = opt.get("greeks") or {}
    d = g.get("delta")
    try:
        return float(d) if d is not None else None
    except Exception:
        return None
    
def find_contract_closest_to_delta(
    contracts: List[Dict[str, Any]],
    option_type: str,          # 'call' or 'put'
    target_delta: float,       # +0.25 for calls, -0.25 for puts
) -> Optional[Dict[str, Any]]:
    """
    From a chain (single expiry), find the contract of given type whose delta
    is closest to target_delta.
    Requires greeks with delta.
    """
    best = None
    best_dist = float("inf")

    for c in contracts:
        if c.get("option_type") != option_type:
            continue
        delta = _extract_delta(c)
        iv = _extract_iv(c)
        if delta is None or iv is None:
            continue
        dist = abs(delta - target_delta)
        if dist < best_dist:
            best_dist = dist
            best = c

    return best

def fails_hard_liquidity(contract):
    return (
        contract["bid"] is None
        or contract["ask"] is None
        or contract["bid"] <= 0
        or contract["ask"] <= 0
        or contract["open_interest"] <= 0
    )

def spread_pct(contract):
    mid = (contract["bid"] + contract["ask"]) / 2
    return (contract["ask"] - contract["bid"]) / mid


def compute_skew_ratio_25d(contracts: List[Dict[str, Any]]) -> Tuple[float, float, float]:
    """
    Returns (skew_ratio, put_iv, call_iv) for ~25-delta options:
      skew_ratio = put_iv / call_iv
    """
    put = find_contract_closest_to_delta(contracts, "put", -0.25)
    call = find_contract_closest_to_delta(contracts, "call", +0.25)

    if not put or not call:
        raise RuntimeError("Could not find both -25Δ put and +25Δ call with IV+delta available.")

    if fails_hard_liquidity(put) or fails_hard_liquidity(call):
        raise RuntimeError("Lack of liquidity in compute_skew_ratio_25d")
    
    if spread_pct(put) > 0.35 or spread_pct(call) > 0.35:
        raise RuntimeError("Spread is too large")

    
    put_iv = _extract_iv(put)
    call_iv = _extract_iv(call)

    if put_iv is None or call_iv is None or call_iv <= 0:
        raise RuntimeError("Missing or invalid IV for skew calculation.")

    return (float(put_iv / call_iv), float(put_iv), float(call_iv))


def pick_expiry_closest_to_dte(expirations: List[str], target_dte: int = 30) -> str:
    today = date.today()
    best_e = None
    best_dist = float("inf")

    for e in expirations:
        dte = (_parse_ymd(e) - today).days
        if dte <= 0:
            continue
        dist = abs(dte - target_dte)
        if dist < best_dist:
            best_dist = dist
            best_e = e

    if not best_e:
        #raise RuntimeError("No valid future expiration found.")
        return None
    return best_e


async def compute_skew_30d_proxy(
    symbol: str,
    expirations,
    client: TradierClient,
    *,
    target_dte: int = 30,
) -> Tuple[float, float, float, str]:
    """
    Computes a 30D skew proxy:
      skew = IV(-25Δ put) / IV(+25Δ call)
    using the expiration closest to target_dte.

    Returns: (skew_ratio, put_iv, call_iv, expiry_used)
    """
    exp = pick_expiry_closest_to_dte(expirations, target_dte=target_dte)

    if exp is None:
        raise RuntimeError("No valid expiration date found for {symbol}")
    chain = await list_contracts_for_expiry(symbol, exp, client=client, include_greeks=True)
    if not chain:
        raise RuntimeError(f"No chain for {symbol} {exp}")

    skew_ratio, put_iv, call_iv = compute_skew_ratio_25d(chain)
    return skew_ratio, put_iv, call_iv, exp

def atm_iv_for_expiry(
    contracts: List[Dict[str, Any]],
    underlying_price: float,
) -> Optional[float]:
    """
    Returns ATM IV for this expiry:
    - find strike closest to spot
    - average call and put IV at that strike (if both available)
    """
    if not contracts:
        return None

    # strike -> {"call": contract, "put": contract}
    by_strike: dict[float, dict[str, Dict[str, Any]]] = {}
    for c in contracts:
        k = c.get("strike")
        t = c.get("option_type")
        if k is None or t not in ("call", "put"):
            continue
        by_strike.setdefault(float(k), {})[t] = c

    if not by_strike:
        return None

    atm_strike = min(by_strike.keys(), key=lambda k: abs(k - underlying_price))
    legs = by_strike[atm_strike]

    call_iv = _extract_iv(legs.get("call")) if legs.get("call") else None
    put_iv  = _extract_iv(legs.get("put"))  if legs.get("put") else None

    if call_iv is not None and put_iv is not None:
        return 0.5 * (call_iv + put_iv)
    return call_iv if call_iv is not None else put_iv


def pick_bracketing_expirations(
    expirations: List[str],
    target_dte: int = 30,
    today: Optional[date] = None,
) -> Tuple[str, int, str, int]:
    """
    Returns (exp1, dte1, exp2, dte2) where:
      dte1 <= target_dte <= dte2
    If target is outside the range, uses nearest two on that side.
    """
    if today is None:
        today = date.today()

    exp_dtes = []
    for e in expirations:
        ed = _parse_ymd(e)
        dte = (ed - today).days
        if dte > 0:
            exp_dtes.append((e, dte))

    if len(exp_dtes) < 2:
        raise RuntimeError("Need at least two future expirations to interpolate IV30.")

    exp_dtes.sort(key=lambda x: x[1])  # sort by dte

    below = [x for x in exp_dtes if x[1] <= target_dte]
    above = [x for x in exp_dtes if x[1] >= target_dte]

    if below and above:
        exp1, dte1 = below[-1]
        exp2, dte2 = above[0]
        # If exact match (same expiry both sides), shift one side if possible
        if exp1 == exp2:
            idx = exp_dtes.index((exp1, dte1))
            if idx + 1 < len(exp_dtes):
                exp2, dte2 = exp_dtes[idx + 1]
            elif idx - 1 >= 0:
                exp1, dte1 = exp_dtes[idx - 1]
        return exp1, dte1, exp2, dte2

    # Target earlier than earliest expiry
    if not below:
        (exp1, dte1), (exp2, dte2) = exp_dtes[0], exp_dtes[1]
        return exp1, dte1, exp2, dte2

    # Target later than latest expiry
    (exp1, dte1), (exp2, dte2) = exp_dtes[-2], exp_dtes[-1]
    return exp1, dte1, exp2, dte2




async def compute_iv_30_interpolated(
    symbol: str,
    underlying_price: float,
    expirations,
    client: TradierClient,
    *,
    target_dte: int = 30,
    session: Optional[aiohttp.ClientSession] = None,
) -> float:
    """
    Computes IV30 (decimal) by:
      - getting expirations from Tradier
      - selecting two expiries bracketing 30 DTE
      - pulling chains for both expiries
      - computing ATM IV for each
      - interpolating in variance-time to 30 days
    """
    # 1) expirations
    exp1, dte1, exp2, dte2 = pick_bracketing_expirations(expirations, target_dte=target_dte)

    # 2) chains
    c1 = await list_contracts_for_expiry(symbol, exp1, client=client, include_greeks=True)
    c2 = await list_contracts_for_expiry(symbol, exp2, client=client, include_greeks=True)
    
    # c1 = await list_contracts_for_expiry(symbol, exp1, include_greeks=True, session=session)
    # c2 = await list_contracts_for_expiry(symbol, exp2, include_greeks=True, session=session)

    if not c1 or not c2:
        raise RuntimeError(f"Missing option chain(s): {symbol} {exp1}={bool(c1)} {exp2}={bool(c2)}")

    # 3) ATM IVs
    iv1 = atm_iv_for_expiry(c1, underlying_price)
    iv2 = atm_iv_for_expiry(c2, underlying_price)

    if iv1 is None or iv2 is None:
        raise RuntimeError(f"Could not compute ATM IVs for {symbol}: {exp1}={iv1}, {exp2}={iv2}")

    # 4) variance-time interpolation
    # total variance to time T: (iv^2) * T
    T1 = dte1 / 365.0
    T2 = dte2 / 365.0
    Tt = target_dte / 365.0

    var1 = (iv1 ** 2) * T1
    var2 = (iv2 ** 2) * T2

    if T2 == T1:
        vart = var1
    else:
        w = (Tt - T1) / (T2 - T1)
        vart = var1 + w * (var2 - var1)

    iv30 = math.sqrt(max(vart / Tt, 0.0))
    return float(iv30)


async def compute_iv_30(
    symbol: str,
    expirations: List[str],          # list of 'YYYY-MM-DD'
    underlying_price: float,
    *,
    target_dte: int = 30,
    session: Optional[aiohttp.ClientSession] = None,
) -> float:
    """
    Compute IV_30 (decimal) by:
      - selecting expiries around 30 DTE
      - getting ATM IV at each expiry
      - interpolating in *variance time* to 30D
    """
    today = date.today()
    exps = sorted(expirations, key=_parse_ymd)

    # Build (expiry, T_years, dte_days)
    exp_info: List[Tuple[str, float, int]] = []
    for e in exps:
        ed = _parse_ymd(e)
        dte = (ed - today).days
        if dte <= 0:
            continue
        T = dte / 365.0
        exp_info.append((e, T, dte))

    if not exp_info:
        raise RuntimeError(f"No future expirations supplied for {symbol}")

    # Find expiries surrounding target DTE
    target = target_dte
    below = [x for x in exp_info if x[2] <= target]
    above = [x for x in exp_info if x[2] >= target]

    if not below:
        e1, T1, d1 = exp_info[0]
        e2, T2, d2 = exp_info[1] if len(exp_info) > 1 else exp_info[0]
    elif not above:
        e1, T1, d1 = exp_info[-2] if len(exp_info) > 1 else exp_info[-1]
        e2, T2, d2 = exp_info[-1]
    else:
        e1, T1, d1 = below[-1]
        e2, T2, d2 = above[0]

    # If exact 30D expiry exists, just use it
    if d1 == target:
        chain1 = await list_contracts_for_expiry(symbol, e1, include_greeks=True, session=session)
        iv1 = atm_iv_for_expiry(chain1, underlying_price)
        if iv1 is None:
            raise RuntimeError(f"Could not compute ATM IV for {symbol} {e1}")
        return float(iv1)

    # Otherwise interpolate using two expiries
    chain1 = await list_contracts_for_expiry(symbol, e1, include_greeks=True, session=session)
    chain2 = await list_contracts_for_expiry(symbol, e2, include_greeks=True, session=session)

    iv1 = atm_iv_for_expiry(chain1, underlying_price)
    iv2 = atm_iv_for_expiry(chain2, underlying_price)
    if iv1 is None or iv2 is None:
        raise RuntimeError(f"Could not compute ATM IV for interpolation: {symbol} {e1}={iv1}, {e2}={iv2}")

    # Variance-time interpolation:
    # total variance to expiry = iv^2 * T
    var1 = (iv1 ** 2) * T1
    var2 = (iv2 ** 2) * T2

    Tt = target / 365.0
    # Linear interpolate total variance between (T1,var1) and (T2,var2)
    if T2 == T1:
        vart = var1
    else:
        w = (Tt - T1) / (T2 - T1)
        vart = var1 + w * (var2 - var1)

    iv30 = math.sqrt(max(vart / Tt, 0.0))
    return float(iv30)


def rv20_ma_not_rising(df: pd.DataFrame, ma_days: int = 5) -> bool:
    if df is None:
        raise RuntimeError("df is none in rv20_ma_not_missing")
    closes = pd.to_numeric(df["close"], errors="coerce").dropna()
    rets = np.log(closes / closes.shift(1)).dropna()

    rv20 = (rets.rolling(20).std() * np.sqrt(252)).dropna()
    if len(rv20) < ma_days + 1:
        raise RuntimeError("Not enough RV20 points for MA test")

    rv20_today = float(rv20.iloc[-1])
    rv20_ma = float(rv20.iloc[-ma_days:].mean())
    return rv20_today <= rv20_ma


async def main():
    async with TradierClient(api_key=TRADIER_API_KEY) as client:
        for ticker in nasdaq_list:
            await screen(ticker, client, verbose=True)
   
if __name__ == "__main__":
    asyncio.run(main())
