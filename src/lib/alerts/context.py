"""Per-symbol daily context the intraday detectors need, from Tradier daily bars.

prev_close / prev_high / prev_low, daily EMA9 / EMA21 (as of the prior close),
ADR20 (%), avg20 volume, high15 (the 15-session pivot the LVL detector watches), hi52, stack_days. Cached per session date in data/cache/alert_ctx_<date>.parquet.
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
from lib.alerts.daily_state import classify

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
    day_state: str = "OUT"          # LONG | SHORT | OUT, from lib.alerts.daily_state (prior close)
    day_reason: str = ""
    ext21_close_adr: float = 0.0
    res_level: float = 0.0
    res_gap_adr: float = 99.0
    sma10: float = 0.0              # parabolic-short cover targets
    sma20: float = 0.0
    up_days: int = 0
    hi52: float = 0.0               # 52-week high (prior close basis) -- LVL precision tag
    ema21_rising: bool = False      # 21 EMA above its value 5 sessions ago (for the gap-day re-classification)
    ema21_slope5_pct: float = 0.0
    day_state_prior: str = ""       # set by the engine when a gap re-classification changed the state (original state)
    setup: str = ""                 # daily-setup text (pullback to the 50 / coil under the pivot / precision cohort ...), context only
    ret20_pct: float = 0.0          # 20-session return, % (the engine subtracts SPY's for RS)
    contr10_20: float = 0.0         # 10-day range / prior 20-day range
    dryup5_50: float = 0.0          # 5-day avg volume / 50-day avg
    pct_vs_sma50: float = 0.0
    sma50_rising: bool = False
    off_20d_high_pct: float = 0.0
    stack_days: int = 0             # consecutive sessions with 10 > 20 > 50 SMA into the prior close

    def levels_above(self) -> list[tuple[str, float]]:
        """Daily resistance candidates for the short-side detectors, named."""
        out = [("9 EMA", self.ema9), ("21 EMA", self.ema21), ("50 EMA", self.ema50), ("50 SMA", self.sma50),
               ("200 SMA", self.sma200), ("PDH", self.prev_high), ("prior high", self.res_level)]
        return [(n, v) for n, v in out if v and v > 0]

    @property
    def bearish(self) -> bool:
        """Below the 9 and 21 EMA at the prior close = the BIR daily gate."""
        return self.prev_close < self.ema9 and self.prev_close < self.ema21


def _ctx_from_hist(sym: str, hist: pd.DataFrame) -> DailyCtx:
    c = hist["close"]
    ds = classify(hist)
    s10, s20, s50 = c.rolling(10).mean(), c.rolling(20).mean(), c.rolling(50).mean()
    stacked = ((s10 > s20) & (s20 > s50)).fillna(False)
    stack_days = 0
    for x in stacked.iloc[::-1]:
        if not x: break
        stack_days += 1
    h_, l_, v_ = hist["high"].astype(float), hist["low"].astype(float), hist["volume"].astype(float)
    sma50 = c.rolling(50).mean(); adr20 = float((h_ / l_ - 1).tail(20).mean() * 100) or 1.0
    r10 = float(h_.tail(10).max() - l_.tail(10).min()); r20p = float(h_.iloc[-30:-10].max() - l_.iloc[-30:-10].min()) if len(c) >= 30 else 0.0
    contr = r10 / r20p if r20p > 0 else 0.0
    dry = float(v_.tail(5).mean() / v_.tail(50).mean()) if len(v_) >= 50 and v_.tail(50).mean() > 0 else 0.0
    s50 = float(sma50.iloc[-1]) if len(c) >= 50 else 0.0; s50_10 = float(sma50.iloc[-11]) if len(c) >= 61 else 0.0
    s50_rising = bool(s50 and s50_10 and s50 > s50_10); pct50 = (float(c.iloc[-1]) / s50 - 1) * 100 if s50 else 0.0
    off20 = (float(h_.tail(20).max()) / float(c.iloc[-1]) - 1) * 100
    ret20 = (float(c.iloc[-1]) / float(c.iloc[-21]) - 1) * 100 if len(c) >= 21 else 0.0
    lo5_vs50 = abs(float(l_.tail(5).min()) / s50 - 1) * 100 if s50 else 99.0
    hist15 = float(h_.iloc[-16:-1].max()) if len(h_) >= 16 else 0.0; vs_piv = (float(c.iloc[-1]) / hist15 - 1) * 100 if hist15 else -99.0
    tags = []
    if s50_rising and lo5_vs50 <= adr20 and off20 >= 6 and contr <= 0.6 and pct50 > -3:
        tags.append(f"pullback to the rising 50 SMA (contr {contr:.2f}, {off20:.0f}% under the 20d high)")
    if stacked.iloc[-1] and -5 <= vs_piv <= 0 and contr <= 0.6 and dry <= 0.8:
        tags.append(f"coil under the 15d pivot {hist15:.2f} (Adhikary SETUP: contr {contr:.2f}, dry-up {dry:.2f})")
    hi52 = float(hist["high"].tail(252).max())
    if 4 <= adr20 <= 7 and (float(c.iloc[-1]) / hi52 - 1) * 100 > -15 and 5 <= stack_days <= 40:
        tags.append("precision cohort")
    if not tags and s50_rising and pct50 > 0:
        tags.append(f"above the rising 50 SMA ({pct50:+.1f}%)")
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
        day_state=ds.state, day_reason=ds.reason, ext21_close_adr=ds.ext21_adr,
        res_level=ds.res_level, res_gap_adr=ds.res_gap_adr,
        sma10=float(c.rolling(10).mean().iloc[-1]), sma20=float(c.rolling(20).mean().iloc[-1]), up_days=ds.up_days,
        hi52=float(hist["high"].tail(252).max()), stack_days=stack_days,
        ema21_rising=bool(ds.ema21_rising), ema21_slope5_pct=float(ds.ema21_slope5_pct),
        setup="; ".join(tags), ret20_pct=round(ret20, 2), contr10_20=round(contr, 3), dryup5_50=round(dry, 3), pct_vs_sma50=round(pct50, 2),
        sma50_rising=s50_rising, off_20d_high_pct=round(off20, 2),
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
    p = CACHE / f"alert_ctx_v7_{session.isoformat()}.parquet"   # v7 = + hi52 / stack_days (LVL precision tag); v6 = parabolic SHORT state
    have: dict[str, DailyCtx] = {}
    if p.exists() and not refresh:
        df = pd.read_parquet(p)
        have = {r.symbol: DailyCtx(**r._asdict()) for r in df.itertuples(index=False)}
        # FLAT (2026-09-15) derived from the cached fields so older caches classify the same way as fresh ones
        from lib.alerts.daily_state import FLAT_ADR
        for c in have.values():
            if c.adr_pct and c.ema9 and c.ema21 and c.day_state in ("LONG", "SHORT", "OUT"):
                e21 = (c.prev_close / c.ema21 - 1) * 100 / c.adr_pct; e9 = (c.prev_close / c.ema9 - 1) * 100 / c.adr_pct
                if abs(e21) <= FLAT_ADR and abs(e9) <= FLAT_ADR:
                    c.day_state_prior, c.day_state = c.day_state, "FLAT"
                    c.day_reason = f"on the 9/21 EMAs ({e21:+.1f} ADR from the 21, {e9:+.1f} from the 9): either side"
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
