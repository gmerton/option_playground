#!/usr/bin/env python3
"""
IV percentile / IV rank straight from IBKR (2026-09-15, Gabe: "can you pull IV percentile directly from IBKR?").

IBKR has no percentile field over the API, but reqHistoricalData(whatToShow='OPTION_IMPLIED_VOLATILITY') returns a
daily series of the underlying's 30-day implied vol (IBKR's own composite), and 'HISTORICAL_VOLATILITY' the 30-day
realized. From a year of those: today's IV30, its 1-year percentile (share of days below today), IV rank
((today - min) / (max - min)), the latest realized vol and IV/RV. This is CURRENT, unlike the straddle screener's
percentile, which ranks a ~10-DTE ATM put IV against silver.fwd_vol_daily (ends 2026-02-20). Read-only.

Usage (TWS live 7496 or paper 7497 / Gateway 4002):
  IB_PORT=7496 IB_ALLOW_LIVE=1 PYTHONPATH=src:. .venv/bin/python3 run_ibkr_iv_percentile.py ASTS PLTR AVGO
"""
from __future__ import annotations
import argparse, os, sys
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ibkr_bot"))
from ib_async import Stock, util
from conn import connect_ib


def series(ib, sym: str, what: str, dur: str = "1 Y") -> pd.Series:
    c = Stock(sym, "SMART", "USD"); ib.qualifyContracts(c)
    bars = ib.reqHistoricalData(c, endDateTime="", durationStr=dur, barSizeSetting="1 day", whatToShow=what, useRTH=True, formatDate=1)
    if not bars:
        return pd.Series(dtype=float)
    df = util.df(bars); return pd.Series(df["close"].values, index=pd.to_datetime(df["date"]))


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("symbols", nargs="+"); ap.add_argument("--client-id", type=int, default=47); a = ap.parse_args()
    ib = connect_ib(client_id=a.client_id, timeout=15)
    rows = []
    for s in [x.upper() for x in a.symbols]:
        try:
            iv, rv = series(ib, s, "OPTION_IMPLIED_VOLATILITY"), series(ib, s, "HISTORICAL_VOLATILITY")
        except Exception as exc:  # noqa: BLE001
            rows.append(dict(sym=s, err=type(exc).__name__)); continue
        if iv.empty:
            rows.append(dict(sym=s, err="no IV history")); continue
        iv = iv[iv > 0]; today = float(iv.iloc[-1]); hist = iv.iloc[:-1]
        pct = 100 * (hist < today).mean(); rank = 100 * (today - hist.min()) / (hist.max() - hist.min()) if hist.max() > hist.min() else float("nan")
        rv_now = float(rv[rv > 0].iloc[-1]) if len(rv[rv > 0]) else float("nan")
        rows.append(dict(sym=s, asof=iv.index[-1].date(), iv30=round(100 * today, 1), iv_pctile_1y=round(pct, 0), iv_rank_1y=round(rank, 0),
                         iv_1y_min=round(100 * hist.min(), 1), iv_1y_med=round(100 * hist.median(), 1), iv_1y_max=round(100 * hist.max(), 1),
                         rv30=round(100 * rv_now, 1), iv_over_rv=round(today / rv_now, 2) if rv_now else None, days=len(iv)))
    ib.disconnect()
    pd.set_option("display.width", 200); print(pd.DataFrame(rows).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
