from datetime import date, timedelta
from typing import Any, Dict, Optional, List
from lib.tradier.tradier_client_wrapper import TradierClient
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FiftyTwoWeekRange:
    symbol: str
    start: str        # YYYY-MM-DD
    end: str          # YYYY-MM-DD
    high_52w: Optional[float]
    low_52w: Optional[float]
    days_used: int


async def get_52w_high_low(
    tradier: TradierClient,
    symbol: str,
    *,
    end: Optional[date] = None,
    lookback_calendar_days: int = 365,
) -> FiftyTwoWeekRange:
    """
    Return the 52-week high and low using daily OHLC data from Tradier.
    """
    if not symbol or not symbol.strip():
        raise ValueError("symbol is required")

    end = end or date.today()
    start = end - timedelta(days=lookback_calendar_days)

    params = {
        "symbol": symbol.strip().upper(),
        "start": start.isoformat(),
        "end": end.isoformat(),
    }

    payload: Dict[str, Any] = await tradier.get_json(
        "/markets/history",
        params=params,
    )

    history = (payload or {}).get("history") or {}
    days = history.get("day")

    if not days:
        return FiftyTwoWeekRange(
            symbol=params["symbol"],
            start=start.isoformat(),
            end=end.isoformat(),
            high_52w=None,
            low_52w=None,
            days_used=0,
        )

    # Single-day edge case
    if isinstance(days, dict):
        days = [days]

    highs: List[float] = []
    lows: List[float] = []

    for d in days:
        h = d.get("high")
        l = d.get("low")
        if h is None or l is None:
            continue
        highs.append(float(h))
        lows.append(float(l))

    if not highs or not lows:
        return FiftyTwoWeekRange(
            symbol=params["symbol"],
            start=start.isoformat(),
            end=end.isoformat(),
            high_52w=None,
            low_52w=None,
            days_used=0,
        )

    return FiftyTwoWeekRange(
        symbol=params["symbol"],
        start=start.isoformat(),
        end=end.isoformat(),
        high_52w=max(highs),
        low_52w=min(lows),
        days_used=min(len(highs), len(lows)),
    )
