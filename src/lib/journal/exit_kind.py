"""Classify same-day stock round trips by HOW they ended, from fills + 1-min bars.

  INVALIDATION   exit within 0.15 ADR of the trade's worst price AND a pre-entry level broke
                 (long: the post-entry low took out the session low before entry; short: mirror)
  NOISE_STOP     exit within 0.15 ADR of the worst price, but no pre-entry level broke
  DISCRETIONARY  exit away from the worst price with the level intact (a working trade sold)

Only INVALIDATION is a legitimate fast cut (Tito's sub-10-min bucket); the other two are the
same-day-exit leak the process report card penalizes. Bars come from Tradier timesales
(~20 sessions of retention) via the journal price cache.
"""
from __future__ import annotations

import asyncio
import os
from datetime import date

import pandas as pd

from pathlib import Path

from lib.tradier.tradier_client_wrapper import TradierClient
from lib.tradier.get_daily_history import get_intraday_bars

NEAR_WORST_ADR = 0.15
CACHE = Path(__file__).resolve().parents[3] / "data" / "cache" / "intraday_1min"


async def bars_1min(sym: str, day: date, client: TradierClient) -> pd.DataFrame | None:
    """1-min bars for a closed session, cached to parquet (the journal cache holds 5-min only)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{sym}_{day.isoformat()}.parquet"
    if day < date.today() and p.exists():
        m = pd.read_parquet(p)
        return None if m.empty else m
    m = await get_intraday_bars(sym, day, interval="1min", client=client)
    if day < date.today():
        (m if m is not None else pd.DataFrame()).to_parquet(p)
    return m


def cycles_from_fills(t: pd.DataFrame) -> list[dict]:
    """Flat-to-flat same-day stock cycles from journal_trades rows (trade_date, underlying_symbol,
    trade_datetime, buy_sell, quantity, trade_price)."""
    out = []
    for (d, s), g in t.sort_values("trade_datetime").groupby(["trade_date", "underlying_symbol"]):
        pos = 0; cur = None
        for r in g.itertuples():
            signed = r.quantity if r.buy_sell == "BUY" else -abs(r.quantity)
            if pos == 0:
                cur = dict(date=d, sym=s, side="L" if signed > 0 else "S", t_in=r.trade_datetime, px_in=float(r.trade_price))
            pos += signed
            if pos == 0 and cur:
                cur["t_out"] = r.trade_datetime; cur["px_out"] = float(r.trade_price); out.append(cur); cur = None
    return [c for c in out if pd.Timestamp(c["t_in"]).date() == pd.Timestamp(c["t_out"]).date()]


async def classify(cycles: list[dict], adr: dict[str, float], client: TradierClient) -> list[dict]:
    rows = []
    for x in cycles:
        try:
            m = await bars_1min(x["sym"], pd.Timestamp(x["date"]).date(), client)
        except Exception:  # noqa: BLE001
            m = None
        if m is None or m.empty:
            rows.append({**x, "kind": "UNKNOWN"}); continue
        a = adr.get(x["sym"], 3.0)
        t_in, t_out = pd.Timestamp(x["t_in"]).floor("min"), pd.Timestamp(x["t_out"]).floor("min")
        seg = m.loc[(m.index >= t_in) & (m.index <= t_out)]; pre = m.loc[m.index < t_in]
        if seg.empty:
            rows.append({**x, "kind": "UNKNOWN"}); continue
        if x["side"] == "L":
            worst = seg["low"].min(); near = (x["px_out"] / worst - 1) * 100 <= NEAR_WORST_ADR * a
            broke = (worst < pre["low"].min()) if len(pre) else True
            mfe = (seg["high"].max() / x["px_in"] - 1) * 100; pnl = (x["px_out"] / x["px_in"] - 1) * 100
        else:
            worst = seg["high"].max(); near = (worst / x["px_out"] - 1) * 100 <= NEAR_WORST_ADR * a
            broke = (worst > pre["high"].max()) if len(pre) else True
            mfe = (1 - seg["low"].min() / x["px_in"]) * 100; pnl = (1 - x["px_out"] / x["px_in"]) * 100
        kind = "INVALIDATION" if (near and broke) else ("NOISE_STOP" if near else "DISCRETIONARY")
        rows.append({**x, "kind": kind, "pnl_pct": round(pnl, 2), "mfe_pct": round(mfe, 2), "level_broke": bool(broke)})
    return rows


def classify_sync(cycles: list[dict], adr: dict[str, float]) -> list[dict]:
    async def run():
        async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
            return await classify(cycles, adr, c)
    return asyncio.run(run())
