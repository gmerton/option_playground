import math
from typing import Literal, Optional

OptionType = Literal["call", "put"]

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def _d1_d2(S: float, K: float, T: float, r: float, q: float, sigma: float):
    if sigma <= 0 or T <= 0:
        raise ValueError("sigma and T must be positive")
    sqT = math.sqrt(T)
    fwd = math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T
    d1 = fwd / (sigma * sqT)
    d2 = d1 - sigma * sqT
    return d1, d2

def bs_price(S: float, K: float, T: float, r: float, q: float, sigma: float, opt_type: OptionType) -> float:
    d1, d2 = _d1_d2(S, K, T, r, q, sigma)
    disc_r = math.exp(-r * T)
    disc_q = math.exp(-q * T)
    if opt_type == "call":
        return S * disc_q * _norm_cdf(d1) - K * disc_r * _norm_cdf(d2)
    else:  # put
        return K * disc_r * _norm_cdf(-d2) - S * disc_q * _norm_cdf(-d1)

def vega(S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:
    d1, _ = _d1_d2(S, K, T, r, q, sigma)
    return S * math.exp(-q * T) * _norm_pdf(d1) * math.sqrt(T)

def implied_vol(
    price: float, S: float, K: float, T: float, r: float = 0.0, q: float = 0.0,
    opt_type: OptionType = "call", 
    sigma_init: float = 0.3, 
    tol: float = 1e-8, 
    max_iter: int = 100,
    # bisection fallback bounds:
    sigma_lo: float = 1e-4, 
    sigma_hi: float = 5.0
) -> Optional[float]:
    """
    Returns IV (annualized, as a decimal), or None if it cannot be found.
    """
    # Guard: price must lie within no-arbitrage BS bounds at some sigma
    # First try Newton
    sigma = sigma_init
    for _ in range(max_iter):
        try:
            model = bs_price(S,K,T,r,q,sigma,opt_type)
            diff = model - price
            if abs(diff) < tol:
                return sigma
            v = vega(S,K,T,r,q,sigma)
            if v < 1e-12:  # flat vega -> Newton unstable
                break
            sigma -= diff / v
            if sigma <= 0 or sigma > sigma_hi:
                break  # fall back to bisection
        except ValueError:
            break

    # Robust bisection fallback
    lo, hi = sigma_lo, sigma_hi
    f_lo = bs_price(S,K,T,r,q,lo,opt_type) - price
    f_hi = bs_price(S,K,T,r,q,hi,opt_type) - price
    if f_lo * f_hi > 0:
        # Price not bracketed within [lo, hi]
        return None

    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        f_mid = bs_price(S,K,T,r,q,mid,opt_type) - price
        if abs(f_mid) < tol:
            return mid
        # keep the root bracketed
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return 0.5 * (lo + hi)
