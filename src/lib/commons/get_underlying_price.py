from typing import Optional, List, Dict, Any
import aiohttp
import os

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}


async def get_underlying_price(
        ticker: str
) :
    url = f"{TRADIER_ENDPOINT}/markets/quotes"
    params = {"symbols" : ticker}
    close_session = False
    session = aiohttp.ClientSession(
        headers=TRADIER_REQUEST_HEADERS
    )
    try:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
        q = (data or {}).get("quotes", {}).get("quote")
        if q is None:
            return None
        if isinstance(q, list):
            q = q[0]
        bid = q.get("bid")
        ask = q.get("ask")
        last = q.get("last")
        close = q.get("close") or q.get("prevclose")

        if bid and ask and bid > 0 and ask > 0:
            return float((bid+ask)/2.0)
        if last and last > 0:
            return float(last)
        if close and close > 0:
            return float(close)
        return None
    finally:
        await session.close()
