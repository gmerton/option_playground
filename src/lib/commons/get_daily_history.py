from typing import Optional, List, Dict, Any, Iterable
import aiohttp
import os
import time
from datetime import date, timedelta
import pandas as pd
import pandas_ta as ta

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}


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
        print(data)
        history = (data or {}).get("history", {})
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
