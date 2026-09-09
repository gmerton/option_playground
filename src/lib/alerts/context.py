"""Per-symbol daily context the intraday detectors need, from Tradier daily bars.

prev_close / prev_high / prev_low, daily EMA9 / EMA21 (as of the prior close),
ADR20 (%), avg20 volume. Cached per session date in data/cache/alert_ctx_<date>.parquet.
Tradier concurrency is capped at 2 (higher -> ClientResponseError skips).
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from lib.tradier.get_daily_history import get_daily_history
from lib.tradier.tradier_client_wrapper import TradierClient

REPO = Path(__file__).resolve().parents[3]
CACHE = REPO / "data" / "cache"


@dataclass
class DailyCtx:
    symbol: str
    prev_close: float
    prev_high: float
    prev_low: float
    ema9: float
    ema21: float
    adr_pct: float
    avg_vol20: float
    high15: float
    ema50: float = 0.0
    sma50: float = 0.0
    sma200: float = 0.0

    def levels_above(self) -> list[tuple[str, float]]:
        """Daily resistance candidates for the short-side detectors, named."""
        out = [("9 EMA", self.ema9), ("21 EMA", self.ema21), ("50 EMA", self.ema50), ("50 SMA", self.sma50),
               ("200 SMA", self.sma200), ("PDH", self.prev_high)]
        return [(n, v) for n, v in out if v and v > 0]

    @property
    def bearish(self) -> bool:
        """Below the 9 and 21 EMA at the prior close = the BIR daily gate."""
        return self.prev_close < self.ema9 and self.prev_close < self.ema21


def _ctx_from_hist(sym: str, hist: pd.DataFrame) -> DailyCtx:
    c = hist["close"]
    return DailyCtx(
        symbol=sym,
        prev_close=float(c.iloc[-1]),
        prev_high=float(hist["high"].iloc[-1]),
        prev_low=float(hist["low"].iloc[-1]),
        ema9=float(c.ewm(span=9, adjust=False).mean().iloc[-1]),
        ema21=float(c.ewm(span=21, adjust=False).mean().iloc[-1]),
        adr_pct=float(((hist["high"] / hist["low"] - 1).tail(20).mean()) * 100),
        avg_vol20=float(hist["volume"].tail(20).mean()),
        high15=float(hist["high"].tail(15).max()),
        ema50=float(c.ewm(span=50, adjust=False).mean().iloc[-1]),
        sma50=float(c.rolling(50).mean().iloc[-1]) if len(c) >= 50 else 0.0,
        sma200=float(c.rolling(200).mean().iloc[-1]) if len(c) >= 200 else 0.0,
    )


async def _one(sym: str, session: date, client: TradierClient, sem: asyncio.Semaphore) -> DailyCtx | None:
    async with sem:
        try:
            d = await get_daily_history(sym, session - timedelta(days=330), session, client=client)
        except Exception as exc:  # noqa: BLE001 - skip the symbol, keep the run
            print(f"  ! {sym}: {exc.__class__.__name__}")
            return None
    if d is None or len(d) < 25:
        return None
    d = d.copy()
    if "date" not in d.columns:            # helper returns the date as the index
        d = d.reset_index().rename(columns={"index": "date"})
    d["date"] = pd.to_datetime(d["date"]).dt.date
    hist = d[d["date"] < session]          # strip the in-progress session bar
    if len(hist) < 25:
        return None
    return _ctx_from_hist(sym, hist)


async def load_context(symbols: list[str], session: date, *, refresh: bool = False) -> dict[str, DailyCtx]:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"alert_ctx_v2_{session.isoformat()}.parquet"
    have: dict[str, DailyCtx] = {}
    if p.exists() and not refresh:
        df = pd.read_parquet(p)
        have = {r.symbol: DailyCtx(**r._asdict()) for r in df.itertuples(index=False)}
    missing = [s for s in symbols if s not in have]
    if missing:
        sem = asyncio.Semaphore(2)
        async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as client:
            res = await asyncio.gather(*(_one(s, session, client, sem) for s in missing))
        for r in res:
            if r is not None:
                have[r.symbol] = r
        pd.DataFrame([vars(v) for v in have.values()]).to_parquet(p, index=False)
    return {s: have[s] for s in symbols if s in have}
