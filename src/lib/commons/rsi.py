"""
Wilder RSI, and the long-straddle playbook's RSI gate (gate 5, added 2026-09-16).

Gate: skip a 7-DTE long-straddle entry when the name's RSI(14) on daily closes is >= 70.
Evidence: data/studies/rsi_conditioning_study_2026-09-16.md, sections B, D, F. Those
entries lost ~12pp/trade (within-week t -3.4). The walk-forward held in 7 of 8 years,
with within-week placebo p = 0.0002. The loss is on the PUT leg: extended names move
less than even their cheaper straddle implies. RSI >= 70 is ~2.8 ADR above the 21 EMA.

The study read RSI at the entry-day close on split/dividend-adjusted closes. A live run
during Friday's session gets today's partial bar as the last close, which is the
nearest live equivalent.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RSI_PERIOD = 14
RSI_MAX = 70.0          # gate passes when RSI < RSI_MAX
MIN_BARS = 50           # warm-up the study required before trusting a reading


def wilder_rsi(close: pd.Series, n: int = RSI_PERIOD) -> pd.Series:
    """Wilder's RSI (EWM with alpha = 1/n), identical to run_rsi_conditioning_study.py."""
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn)


def latest_rsi(close: pd.Series | None, n: int = RSI_PERIOD) -> float:
    """RSI at the last bar, NaN if there is not enough clean history."""
    if close is None:
        return np.nan
    s = close.dropna()
    if len(s) < MIN_BARS:
        return np.nan
    return float(wilder_rsi(s, n).iloc[-1])


def latest_rsi_yf(tickers: list[str], period: str = "1y") -> dict[str, float]:
    """{ticker: RSI(14) at the most recent bar} from yfinance adjusted closes.

    yfinance, not Tradier: the study used split-adjusted closes, and one un-adjusted
    split inside the lookback would read as a crash. Missing names map to NaN.
    """
    import yfinance as yf

    if not tickers:
        return {}
    raw = yf.download(tickers, period=period, auto_adjust=True, progress=False, threads=True)
    close = raw["Close"]
    if isinstance(close, pd.Series):                       # single ticker
        close = close.to_frame(tickers[0])
    return {t: (latest_rsi(close[t]) if t in close.columns else np.nan) for t in tickers}


def rsi_gate(value: float) -> bool | None:
    """True = passes (RSI < 70), False = blocked, None = no reading (gate not applied)."""
    if value is None or not np.isfinite(value):
        return None
    return value < RSI_MAX
