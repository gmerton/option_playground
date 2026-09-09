"""Tradier market-data WebSocket: trade prints for a symbol list.

One session at a time per account (Tradier rule). Reconnects with a fresh session
id on drop. Yields (symbol, et_datetime, price, size) for regular-hours prints only.
"""
from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
from datetime import datetime, time
from zoneinfo import ZoneInfo

import aiohttp

ET = ZoneInfo("America/New_York")
API = "https://api.tradier.com/v1"
WS = "wss://ws.tradier.com/v1/markets/events"
RTH_START, RTH_END = time(9, 30), time(16, 0)


async def _session_id(http: aiohttp.ClientSession) -> str:
    hdr = {"Authorization": f"Bearer {os.environ['TRADIER_API_KEY']}", "Accept": "application/json"}
    async with http.post(f"{API}/markets/events/session", headers=hdr, data=b"") as r:
        r.raise_for_status()
        return (await r.json())["stream"]["sessionid"]


async def trades(symbols: list[str], *, rth_only: bool = True,
                 max_backoff: float = 30.0) -> AsyncIterator[tuple[str, datetime, float, float]]:
    backoff = 1.0
    async with aiohttp.ClientSession() as http:
        while True:
            try:
                sid = await _session_id(http)
                async with http.ws_connect(WS, heartbeat=25) as ws:
                    await ws.send_str(json.dumps({"symbols": symbols, "sessionid": sid,
                                                  "linebreak": True, "filter": ["trade"],
                                                  "validOnly": True}))
                    backoff = 1.0
                    async for m in ws:
                        if m.type != aiohttp.WSMsgType.TEXT:
                            if m.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break
                            continue
                        for line in m.data.splitlines():
                            try:
                                ev = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if ev.get("type") != "trade":
                                continue
                            t = datetime.fromtimestamp(int(ev["date"]) / 1000, tz=ET).replace(tzinfo=None)
                            if rth_only and not (RTH_START <= t.time() < RTH_END):
                                continue
                            yield ev["symbol"], t, float(ev["price"]), float(ev.get("size") or 0)
            except (aiohttp.ClientError, asyncio.TimeoutError, KeyError) as exc:
                print(f"  ! stream: {exc.__class__.__name__}: {exc} -- reconnecting in {backoff:.0f}s", flush=True)
            await asyncio.sleep(backoff)
            backoff = min(max_backoff, backoff * 2)
