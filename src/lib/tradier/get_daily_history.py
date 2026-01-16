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
from lib.commons.list_contracts import list_contracts_for_expiry
from lib.commons.list_expirations import list_expirations
from lib.tradier.tradier_client_wrapper import TradierClient
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
import math
import  asyncio
import os

async def get_daily_history(
    ticker: str,
    start: date,
    end: date,
    *,
    client: TradierClient,
) -> Optional[pd.DataFrame]:
    params = {
        "symbol": ticker,
        "interval": "daily",
        "start": start.isoformat(),
        "end": end.isoformat(),
    }

    data = await client.get_json("/markets/history", params=params)

    history = (data or {}).get("history") or {}
    day = history.get("day")

    if not day:
        return None

    if isinstance(day, dict):
        day = [day]

    df = pd.DataFrame(day)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df
