"""Recover the RAW underlying price from an option chain (2026-09-22).

Why this exists: `options_daily_v3` strikes and greeks are RAW (never adjusted), while every price panel we keep
(`liquid_panel_2019.parquet`, yfinance caches, Tradier history) is split-adjusted, and some are dividend-adjusted
too. Settling a v3 option against a panel close therefore compares two different price scales. The median
mismatch measured across 18 liquid names 2019-2026 is **3.1%**, and for a name that split inside the sample it is
the whole split factor. This has produced two wrong results already:

  * earnings vol premium (2026-09-20): +6.37% / 74% win, which was a split/dividend artefact;
  * IV-rank vehicle test (2026-09-22): -38% mean on bull put spreads held to expiry.

Both were fixed the same way: take the spot from the chain itself.

    spot_from_chain(df)            -> Series indexed by (ticker, trade_date)
    implied_spot(strike, delta, iv, dte, cp)  -> the per-row estimate

Method (r = q = 0, which is accurate enough for a 30-day option): a Black-Scholes delta inverts to
    d1 = Phi^-1(delta)          for a call
    d1 = Phi^-1(1 + delta)      for a put (delta is negative)
and the strike then gives
    S = K * exp(d1 * iv * sqrt(T) - iv^2 * T / 2).
Taking the median across every quoted leg on that date makes it robust to a bad print or a stale greek.

Use this (or put-call parity at the near-ATM strike, which is equivalent and slightly more accurate when you have
both sides at one strike) for ANY settlement, moneyness or extension calculation that mixes v3 with a price panel.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


def implied_spot(strike, delta, iv, dte, cp) -> np.ndarray:
    """Per-row raw spot implied by a leg's delta. Arrays or scalars; cp is 'C'/'P'."""
    strike = np.asarray(strike, dtype=float); delta = np.asarray(delta, dtype=float)
    iv = np.asarray(iv, dtype=float); T = np.clip(np.asarray(dte, dtype=float), 1, None) / 365.0
    is_call = np.asarray(cp) == "C"
    p = np.where(is_call, np.abs(delta), 1.0 + delta)
    d1 = norm.ppf(np.clip(p, 0.01, 0.99))
    return strike * np.exp(d1 * iv * np.sqrt(T) - 0.5 * iv ** 2 * T)


def spot_from_chain(df: pd.DataFrame, *, ticker="ticker", date="trade_date", strike="strike",
                    delta="delta", iv="iv", dte="dte", cp="cp") -> pd.Series:
    """Median implied spot per (ticker, date). Pass a frame of quoted legs with greeks."""
    s = implied_spot(df[strike], df[delta], df[iv], df[dte], df[cp])
    return pd.Series(s, index=df.index).groupby([df[ticker], df[date]]).median()
