"""
TTM Squeeze — vectorized implementation (John F. Carter, Mastering the Trade, 3rd ed.).

Definition used (the standard TTM formulation):
  BB     : SMA(close,20) +/- 2.0 * stdev(close,20)          [ddof=0]
  KC     : SMA(close,20) +/- 1.5 * SMA(TrueRange,20)
  ON     : BB_upper < KC_upper AND BB_lower > KC_lower       (bands inside the channel)
  FIRE   : ON at t-1 and not ON at t                          (the "squeeze release")
  MOM    : linreg endpoint over 20 bars of
             close - ( (donchian_mid(20) + SMA(close,20)) / 2 )
           where donchian_mid = (highest(high,20) + lowest(low,20)) / 2

All functions take wide (date x ticker) DataFrames and return the same shape, so the whole
~5,300-name universe is computed at once. No .apply / no per-ticker loops.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def true_range(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    pc = close.shift(1)
    return pd.concat(
        [(high - low).stack(), (high - pc).abs().stack(), (low - pc).abs().stack()],
        axis=1,
    ).max(axis=1).unstack()


def linreg_endpoint(y: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Value of the least-squares line fitted over the trailing n bars, evaluated at the
    current bar. This is what TTM plots as the momentum histogram.

    endpoint = mean(y) + slope * (n-1)/2,  slope = sum((k - kbar) * y_k) / sum((k - kbar)^2)
    with k = 0..n-1 over the window. sum((k-kbar)^2) = n(n^2-1)/12 is constant, and the
    numerator is a fixed-weight dot product -> computed as a sum of shifted frames.
    """
    kbar = (n - 1) / 2.0
    denom = n * (n * n - 1) / 12.0
    num = None
    for k in range(n):
        w = k - kbar
        if w == 0:
            continue
        term = y.shift(n - 1 - k) * w
        num = term if num is None else num + term
    slope = num / denom
    return y.rolling(n, min_periods=n).mean() + slope * kbar


def squeeze(
    close: pd.DataFrame,
    high: pd.DataFrame,
    low: pd.DataFrame,
    *,
    length: int = 20,
    bb_mult: float = 2.0,
    kc_mult: float = 1.5,
) -> dict:
    basis = close.rolling(length, min_periods=length).mean()
    dev = close.rolling(length, min_periods=length).std(ddof=0)
    bb_u, bb_l = basis + bb_mult * dev, basis - bb_mult * dev

    atr = true_range(high, low, close).rolling(length, min_periods=length).mean()
    kc_u, kc_l = basis + kc_mult * atr, basis - kc_mult * atr

    on = (bb_u < kc_u) & (bb_l > kc_l)
    on = on.where(bb_u.notna() & kc_u.notna())          # keep NaN where undefined

    dc_mid = (high.rolling(length, min_periods=length).max()
              + low.rolling(length, min_periods=length).min()) / 2.0
    mom = linreg_endpoint(close - (dc_mid + basis) / 2.0, length)

    on_b = on.fillna(False).astype(bool)
    fire = (~on_b) & on_b.shift(1).fillna(False)
    fire = fire.where(on.shift(1).notna() & on.notna(), False)

    return {"on": on_b, "fire": fire, "mom": mom, "basis": basis, "atr": atr}


def squeeze_duration(on: pd.DataFrame) -> pd.DataFrame:
    """Consecutive-bar count of the ON state, per column, vectorized.

    Standard trick: cumulative count minus the cumulative count as of the last False.
    """
    onb = on.fillna(False).astype(bool)
    csum = onb.cumsum()
    # value of csum at the most recent False bar, forward-filled
    reset = csum.where(~onb).ffill().fillna(0)
    return (csum - reset).where(onb, 0).astype(int)


def forward_returns(close: pd.DataFrame, horizons=(5, 10, 20)) -> dict:
    return {h: close.shift(-h) / close - 1.0 for h in horizons}
