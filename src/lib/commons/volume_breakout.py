from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple
import math
import aiohttp


@dataclass(frozen=True)
class VolumeConfirmResult:
    symbol: str
    asof: str  # YYYY-MM-DD (latest candle date)
    signal: bool

    vol: float
    avg_vol: float
    vol_ratio: float

    lookback: int
    threshold: float

    reasons: Tuple[str, ...]


def _safe_int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        v = int(x)
        return v
    except Exception:
        return None


async def _tradier_get_json(
    session: aiohttp.ClientSession,
    url: str,
    headers: Dict[str, str],
    params: Dict[str, Any],
) -> Dict[str, Any]:
    async with session.get(url, headers=headers, params=params, timeout=30) as resp:
        resp.raise_for_status()
        return await resp.json()


async def volume_confirmation_eod(
    client,  # your TradierClient wrapper
    symbol: str,
    end: Optional[date] = None,
    avg_volume_lookback: int = 50,
    vol_mult: float = 1.5,
) -> VolumeConfirmResult:
    """
    EOD 'volume spike' confirmation:
      signal = volume_today >= vol_mult * average(volume over prior N days)
    """
    if end is None:
        end = date.today()

    # Buffer for weekends/holidays
    start = end - timedelta(days=int((avg_volume_lookback + 10) * 1.8))

    async with aiohttp.ClientSession() as session:
        url = f"{client.endpoint}/markets/history"
        data = await _tradier_get_json(
            session,
            url,
            client.headers,
            params={
                "symbol": symbol,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "interval": "daily",
            },
        )

    days = (((data or {}).get("history") or {}).get("day")) or []
    if isinstance(days, dict):
        days = [days]

    # Extract (date, volume) and sort
    rows: List[Dict[str, Any]] = []
    for d in days:
        dt = d.get("date")
        v = _safe_int(d.get("volume"))
        if dt and v is not None:
            rows.append({"date": dt, "volume": float(v)})

    rows.sort(key=lambda r: r["date"])

    if len(rows) < avg_volume_lookback + 1:
        return VolumeConfirmResult(
            symbol=symbol,
            asof=rows[-1]["date"] if rows else end.isoformat(),
            signal=False,
            vol=float("nan"),
            avg_vol=float("nan"),
            vol_ratio=float("nan"),
            lookback=avg_volume_lookback,
            threshold=vol_mult,
            reasons=(f"Not enough history: have {len(rows)} days, need {avg_volume_lookback + 1}",),
        )

    today = rows[-1]
    prior = rows[-(avg_volume_lookback + 1):-1]  # prior N days excluding today

    avg_vol = sum(r["volume"] for r in prior) / avg_volume_lookback
    vol = today["volume"]
    vol_ratio = (vol / avg_vol) if avg_vol > 0 else float("inf")

    signal = vol_ratio >= vol_mult
    reasons = []
    if signal:
        reasons.append(f"Volume confirmed: vol_ratio {vol_ratio:.2f} >= {vol_mult:.2f}")
    else:
        reasons.append(f"Volume not confirmed: vol_ratio {vol_ratio:.2f} < {vol_mult:.2f}")

    return VolumeConfirmResult(
        symbol=symbol,
        asof=today["date"],
        signal=signal,
        vol=vol,
        avg_vol=avg_vol,
        vol_ratio=vol_ratio,
        lookback=avg_volume_lookback,
        threshold=vol_mult,
        reasons=tuple(reasons),
    )
