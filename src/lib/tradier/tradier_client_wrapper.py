from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional
import aiohttp


@dataclass
class TradierClient:
    api_key: str
    endpoint: str = "https://api.tradier.com/v1"
    timeout_s: int = 30
    max_retries: int = 4        # retries on 429 / 5xx before giving up
    retry_base_s: float = 1.0   # backoff: retry_base_s * 2**attempt

    _session: Optional[aiohttp.ClientSession] = None

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    async def __aenter__(self) -> "TradierClient":
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout_s)
            connector = aiohttp.TCPConnector(
                limit=50,          # tune for your concurrency
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
            )
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=connector,
            )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError("TradierClient session is not initialized. Use `async with TradierClient(...)`.")
        return self._session

    async def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.endpoint}{path}"
        for attempt in range(self.max_retries + 1):
            async with self.session.get(url, params=params) as resp:
                if resp.status == 429 or 500 <= resp.status < 600:
                    if attempt == self.max_retries:
                        resp.raise_for_status()
                    retry_after = resp.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else self.retry_base_s * 2 ** attempt
                    await resp.read()  # drain before the connection is released back to the pool
                    await asyncio.sleep(delay)
                    continue
                resp.raise_for_status()
                return await resp.json()
