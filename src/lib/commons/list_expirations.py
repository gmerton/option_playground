from typing import List
import aiohttp
from lib.tradier.tradier_client_wrapper import TradierClient

async def list_expirations(
    symbol: str,
    *,
    include_all_roots: bool = True,
    client: TradierClient,
) -> List[str]:
    """Return sorted list of YYYY-MM-DD expirations from Tradier /markets/options/expirations."""
    params = {
        "symbol": symbol,
        "includeAllRoots": "true" if include_all_roots else "false",
        "strikes": "false",
        "contractSize": "false",
        "expirationType": "false",
    }

    data = await client.get_json("/markets/options/expirations", params=params)

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
