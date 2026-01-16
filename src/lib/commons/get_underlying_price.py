from typing import Optional, List, Dict, Any
import aiohttp
import os

from lib.tradier.tradier_client_wrapper import TradierClient



async def get_underlying_price(
    ticker: str,
    *,
    client: TradierClient,
) -> Optional[float]:
    params = {"symbols": ticker}

    data = await client.get_json("/markets/quotes", params=params)

    q = ((data or {}).get("quotes") or {}).get("quote")
    if not q:
        return None

    if isinstance(q, list):
        q = q[0] if q else None
        if not q:
            return None

    bid = q.get("bid")
    ask = q.get("ask")
    last = q.get("last")
    close = q.get("close") or q.get("prevclose")

    # Prefer mid if we have a real market
    if bid is not None and ask is not None:
        try:
            bid_f = float(bid)
            ask_f = float(ask)
            if bid_f > 0 and ask_f > 0:
                return (bid_f + ask_f) / 2.0
        except (TypeError, ValueError):
            pass

    # Fall back to last, then close
    for x in (last, close):
        try:
            if x is not None and float(x) > 0:
                return float(x)
        except (TypeError, ValueError):
            continue

    return None