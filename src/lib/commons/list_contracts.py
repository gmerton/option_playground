from typing import Optional, List, Dict, Any
import aiohttp
import os

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}

async def list_contracts_for_expiry(
    symbol: str,
    expiration: str,                  # 'YYYY-MM-DD'
    *,
    option_type: Optional[str] = None,  # 'call' | 'put' | None (both)
    include_greeks: bool = True,
    min_strike: Optional[float] = None,
    max_strike: Optional[float] = None,
    timeout_sec: float = 8.0,
    session: Optional[aiohttp.ClientSession] = None,
) -> List[Dict[str, Any]]:
    """
    Return a normalized list of option contracts for the given symbol+expiration
    from Tradier /markets/options/chains.

    Each item includes:
      - symbol (OCC option symbol)
      - option_type ('call' or 'put')
      - strike (float)
      - expiration_date (YYYY-MM-DD)
      - root_symbol, underlying
      - bid, ask, last, volume, open_interest, bid_size, ask_size
      - greeks (dict) if include_greeks=True and available
    """
    close_session = False
    if session is None:
        session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout_sec),
            headers=TRADIER_REQUEST_HEADERS
        )
        close_session = True
    else:
        session.headers.update(TRADIER_REQUEST_HEADERS)

    try:
        url = f"{TRADIER_ENDPOINT}/markets/options/chains"
        params = {
            "symbol": symbol,
            "expiration": expiration,
            "greeks": "true" if include_greeks else "false",
        }
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

        raw = (data or {}).get("options", {}).get("option")
        if not raw:
            return []

        # Normalize to list
        options = raw if isinstance(raw, list) else [raw]

        # Optional filters
        if option_type in ("call", "put"):
            options = [o for o in options if o.get("option_type") == option_type]

        if min_strike is not None:
            options = [o for o in options if o.get("strike") is not None and float(o["strike"]) >= min_strike]
        if max_strike is not None:
            options = [o for o in options if o.get("strike") is not None and float(o["strike"]) <= max_strike]

        # Normalize fields we commonly care about
        out: List[Dict[str, Any]] = []
        for o in options:
            out.append({
                "symbol": o.get("symbol"),
                "option_type": o.get("option_type"),                 # 'call' | 'put'
                "strike": float(o["strike"]) if o.get("strike") is not None else None,
                "expiration_date": o.get("expiration_date"),
                "root_symbol": o.get("root_symbol"),
                "underlying": o.get("underlying"),
                "bid": o.get("bid"),
                "ask": o.get("ask"),
                "last": o.get("last"),
                "volume": o.get("volume"),
                "open_interest": o.get("open_interest"),
                "bid_size": o.get("bid_size"),
                "ask_size": o.get("ask_size"),
                "greeks": o.get("greeks") if include_greeks else None,
            })

        # Sort by strike, then calls before puts (or vice versa if you prefer)
        out.sort(key=lambda x: (x["strike"] if x["strike"] is not None else float("inf"),
                                0 if x["option_type"] == "call" else 1))
        return out
    finally:
        if close_session:
            await session.close()
