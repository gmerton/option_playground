from typing import Optional, List, Dict, Any
import aiohttp
import os

TRADIER_API_KEY = os.getenv("TRADIER_API_KEY")
TRADIER_ENDPOINT = "https://api.tradier.com/v1"
TRADIER_REQUEST_HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}", 
    "Accept": "application/json"
}

async def list_expirations(
    symbol: str,
    *,
    include_all_roots: bool = True,
    timeout_sec: float = 6.0,
    session: Optional[aiohttp.ClientSession] = None,
) -> List[str]:
    """Return sorted list of YYYY-MM-DD expirations from Tradier /markets/options/expirations."""
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
        url = f"{TRADIER_ENDPOINT}/markets/options/expirations"
        params = {
            "symbol": symbol,
            "includeAllRoots": "true" if include_all_roots else "false",
            "strikes": "false",
            "contractSize": "false",
            "expirationType": "false",
        }
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

        exp_root = (data or {}).get("expirations") or {}
        dates: List[str] = []

        maybe_dates = exp_root.get("date")
        if maybe_dates:
            dates = [str(d) for d in (maybe_dates if isinstance(maybe_dates, list) else [maybe_dates])]
        else:
            exps = exp_root.get("expiration")
            if exps:
                if isinstance(exps, dict):
                    exps = [exps]
                dates = [str(x.get("date")) for x in exps if x.get("date")]

        return sorted(set(filter(None, dates)))
    finally:
        if close_session:
            await session.close()