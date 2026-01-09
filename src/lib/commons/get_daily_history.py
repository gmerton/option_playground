from typing import Optional, List, Dict, Any, Iterable
import aiohttp
import os
import time
from datetime import date, timedelta
import pandas as pd
import pandas_ta as ta
from dataclasses import dataclass

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}

async def adx(symbol):
    end = date.today()
    start = end - timedelta(days = 30)
    
    df = await get_daily_history(symbol, start,end)
    if df is None:
        return
    return compute_adx_14(symbol, df)

def compute_adx_14(symbol: str, df: pd.DataFrame):
    ind = ta.adx(high=df["high"], low = df["low"], close = df["close"], length=14)
    df2 = df.join(ind).dropna()
    if df2.empty:
        raise RuntimeError(f"Not enough data to compute ADX for {symbol}")
    last = df2.iloc[-1]
    asof = df2.index[-1]
    di_plus = float(last["DMP_14"])
    di_minus = float(last["DMN_14"])
    adx = float(last["ADX_14"])
    #print(f"{di_plus}, {di_minus}, {adx}")
    return adx

async def get_daily_history(
        ticker: str,
        start: date,
        end: date,
) :
    url = f"{TRADIER_ENDPOINT}/markets/history"
    params = {
        "symbol" : ticker,
        "interval" : "daily",
        "start" : start.isoformat(),
        "end" : end.isoformat()
        }
    session = aiohttp.ClientSession(
        headers=TRADIER_REQUEST_HEADERS
    )
    try:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
        #print(data)
        history = (data or {}).get("history", {})
        if history is None or "day" not in history:
            return None
        day = history.get("day")

        if day is None:
            single = history.get("day")
            if isinstance(single, dict):
                day = [single]
        if not day:
            raise RuntimeError(f"No history returned for {ticker}")
        df = pd.DataFrame(day)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()

        return df
    finally:
        await session.close()
