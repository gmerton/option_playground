#!/usr/bin/env python3
"""
⛔ BLOCKED 2026-09-24: the POLYGON_API_KEY here is FREE tier (5 requests/min, ~2y history -> 403/429 on the first
40-ticker test). Stages 1-2 (tickers incl. 5,663 delisted, 17,729 splits) work; stage 3+ needs a PAID source
(paid Polygon: this script as-is; or Sharadar SEP+SF1). See memory feedback_conviction_selection_is_the_strategy.

Build a SURVIVORSHIP-FREE, POINT-IN-TIME equity panel + fundamentals from Polygon and register them in Athena (Glue)
(2026-09-24; Gabe: "do it ... and write the data to athena"). Motivation: every equity study here runs on
liquid_panel_20xx, which holds only names liquid AS OF 2026 -- delisted and failed names are missing, which flatters
every beaten-down / value / reversal test. Undervalued idea #3 (value + quality) cannot be run honestly without this.

STAGES (each resumable; local cache under data/cache/pit/):
  1 tickers      /v3/reference/tickers, type CS, active AND delisted, primary exchange NYSE/Nasdaq/NYSE American/
                 NYSE Arca/Cboe BZX -> tickers.parquet (ticker, name, cik, composite_figi, active, delisted_utc).
  2 splits       /v3/reference/splits (all) -> splits.parquet.
  3 daily bars   /v2/aggs/.../1/day, adjusted=FALSE (raw, so price x reported shares = market cap at the time),
                 2012-01-01 -> today; a delisted ticker's bars are cut at its delisted date. ⚠ Ticker REUSE: a symbol
                 held by a delisted company and later by an active one -> the active entity's bars start at its
                 /v3/reference/tickers/{t} list_date. Output adds `adj_factor` (cumulative split factor) so
                 close_adj = close / adj_factor.
  4 fundamentals /vX/reference/financials by CIK (quarterly + annual), for every company whose 50-day ADDV ever
                 reached $20M -> one row per filing: filing_date (the point-in-time key), period dates, revenues, gross
                 profit, operating income, net income, operating cash flow, capex proxy, assets, liabilities, equity,
                 long-term debt, basic/diluted weighted shares.
  5 upload       awswrangler -> s3://gmerton-stock-data/pit/ + Glue: silver.equity_daily_pit (partitioned by year),
                 silver.fundamentals_pit, silver.tickers_pit.

Usage (background; ~1-2 h, Polygon-bound):
  source ~/.trading_env; AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_build_pit_panel.py [--stage N]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import time
from pathlib import Path

import aiohttp
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent
D = REPO / "data/cache/pit"
BARS = D / "bars"
FUND = D / "fund"
API = "https://api.polygon.io"
KEY = os.environ.get("POLYGON_API_KEY", "")
EXCH = {"XNYS", "XNAS", "XASE", "ARCX", "BATS"}
START = "2012-01-01"
CONC = 8
S3 = "s3://gmerton-stock-data/pit"


async def fetch(session, url, params=None, tries=6):
    params = dict(params or {}); params["apiKey"] = KEY
    for k in range(tries):
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=90)) as r:
                if r.status == 429 or r.status >= 500:
                    await asyncio.sleep(2 ** k); continue
                if r.status != 200:
                    return None
                return await r.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            await asyncio.sleep(2 ** k)
    return None


async def paginate(session, url, params):
    out, nxt, p = [], url, params
    while nxt:
        j = await fetch(session, nxt, p)
        if not j:
            break
        out += j.get("results", []) or []
        nxt, p = j.get("next_url"), {}
    return out


# ── stage 1 / 2 ──────────────────────────────────────────────────────────────
async def stage_tickers():
    D.mkdir(parents=True, exist_ok=True)
    f = D / "tickers.parquet"
    if f.exists():
        return pd.read_parquet(f)
    async with aiohttp.ClientSession() as s:
        rows = []
        for active in ("true", "false"):
            rows += await paginate(s, f"{API}/v3/reference/tickers",
                                   dict(market="stocks", type="CS", active=active, limit=1000))
    T = pd.DataFrame(rows)
    T = T[T.primary_exchange.isin(EXCH)].copy()
    T["delisted_utc"] = pd.to_datetime(T.get("delisted_utc"), errors="coerce", utc=True).dt.tz_localize(None)
    T = T[T.delisted_utc.isna() | (T.delisted_utc >= START)]
    keep = ["ticker", "name", "cik", "composite_figi", "primary_exchange", "active", "delisted_utc"]
    T = T[[c for c in keep if c in T]].reset_index(drop=True)
    T.to_parquet(f, index=False)
    print(f"stage 1: {len(T):,} CS tickers ({int(T.active.sum()):,} active, {int((~T.active).sum()):,} delisted since {START})", flush=True)
    return T


async def stage_splits():
    f = D / "splits.parquet"
    if f.exists():
        return pd.read_parquet(f)
    async with aiohttp.ClientSession() as s:
        rows = await paginate(s, f"{API}/v3/reference/splits", dict(limit=1000, **{"execution_date.gte": START}))
    S = pd.DataFrame(rows)
    S.to_parquet(f, index=False)
    print(f"stage 2: {len(S):,} splits", flush=True)
    return S


# ── stage 3 ──────────────────────────────────────────────────────────────────
async def stage_bars(T: pd.DataFrame):
    BARS.mkdir(parents=True, exist_ok=True)
    reused = set(T[~T.active].ticker) & set(T[T.active].ticker)
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    sem = asyncio.Semaphore(CONC)
    done = {p.stem for p in BARS.glob("*.parquet")}
    todo = [r for r in T.itertuples(index=False) if f"{r.ticker}__{'A' if r.active else 'D'}" not in done]
    print(f"stage 3: {len(todo):,} ticker entities to pull ({len(done):,} cached; {len(reused)} reused symbols)", flush=True)
    t0 = time.time(); cnt = [0]

    async def one(s, r):
        async with sem:
            start, end = START, today
            if not r.active and pd.notna(r.delisted_utc):
                end = r.delisted_utc.strftime("%Y-%m-%d")
            if r.active and r.ticker in reused:
                det = await fetch(s, f"{API}/v3/reference/tickers/{r.ticker}")
                ld = (det or {}).get("results", {}).get("list_date")
                if ld:
                    start = max(start, ld)
            j = await fetch(s, f"{API}/v2/aggs/ticker/{r.ticker}/range/1/day/{start}/{end}",
                            dict(adjusted="false", sort="asc", limit=50000))
            res = (j or {}).get("results") or []
            df = pd.DataFrame(res)
            if len(df):
                df = pd.DataFrame(dict(date=pd.to_datetime(df.t, unit="ms").dt.normalize(), open=df.o, high=df.h,
                                       low=df.l, close=df.c, volume=df.v, vwap=df.get("vw")))
                df.insert(0, "ticker", r.ticker); df["entity"] = "A" if r.active else "D"
                df["cik"] = r.cik
            df.to_parquet(BARS / f"{r.ticker}__{'A' if r.active else 'D'}.parquet", index=False)
            cnt[0] += 1
            if cnt[0] % 500 == 0:
                print(f"  bars {cnt[0]:,}/{len(todo):,}  {time.time() - t0:.0f}s", flush=True)

    async with aiohttp.ClientSession() as s:
        await asyncio.gather(*(one(s, r) for r in todo))


def assemble_bars(S: pd.DataFrame) -> pd.DataFrame:
    parts = [pd.read_parquet(p) for p in BARS.glob("*.parquet")]
    B = pd.concat([p for p in parts if len(p)], ignore_index=True)
    B = B.sort_values(["ticker", "entity", "date"])
    # cumulative split factor: close_adj = close / adj_factor (1 for the latest bar)
    S = S.copy(); S["execution_date"] = pd.to_datetime(S.execution_date)
    S["ratio"] = S.split_to / S.split_from
    B["adj_factor"] = 1.0
    for tk, g in S.groupby("ticker"):
        m = B.ticker == tk
        if not m.any():
            continue
        f = np.ones(m.sum())
        dts = B.loc[m, "date"].values
        for r in g.itertuples(index=False):
            f = np.where(dts < np.datetime64(r.execution_date), f * r.ratio, f)
        B.loc[m, "adj_factor"] = f
    B["dollar_volume"] = B.close * B.volume
    B["year"] = B.date.dt.year
    return B


# ── stage 4 ──────────────────────────────────────────────────────────────────
FIELDS = {
    "income_statement": ["revenues", "gross_profit", "operating_income_loss", "net_income_loss",
                         "basic_average_shares", "diluted_average_shares", "basic_earnings_per_share"],
    "balance_sheet": ["assets", "liabilities", "equity", "long_term_debt", "current_assets", "current_liabilities"],
    "cash_flow_statement": ["net_cash_flow_from_operating_activities", "net_cash_flow_from_investing_activities"],
}


async def stage_fund(ciks: list[str]):
    FUND.mkdir(parents=True, exist_ok=True)
    done = {p.stem for p in FUND.glob("*.parquet")}
    todo = [c for c in ciks if c not in done]
    print(f"stage 4: {len(todo):,} CIKs to pull ({len(done):,} cached)", flush=True)
    sem = asyncio.Semaphore(CONC); t0 = time.time(); cnt = [0]

    async def one(s, cik):
        async with sem:
            rows = []
            for tf in ("quarterly", "annual"):
                rows += await paginate(s, f"{API}/vX/reference/financials",
                                       dict(cik=cik, timeframe=tf, limit=100, order="asc", sort="filing_date"))
            out = []
            for r in rows:
                rec = dict(cik=cik, tickers=",".join(r.get("tickers") or []), filing_date=r.get("filing_date"),
                           start_date=r.get("start_date"), end_date=r.get("end_date"), timeframe=r.get("timeframe"),
                           fiscal_period=r.get("fiscal_period"), fiscal_year=r.get("fiscal_year"), sic=r.get("sic"))
                fin = r.get("financials") or {}
                for sec, keys in FIELDS.items():
                    for k in keys:
                        rec[k] = ((fin.get(sec) or {}).get(k) or {}).get("value")
                out.append(rec)
            pd.DataFrame(out).to_parquet(FUND / f"{cik}.parquet", index=False)
            cnt[0] += 1
            if cnt[0] % 250 == 0:
                print(f"  fundamentals {cnt[0]:,}/{len(todo):,}  {time.time() - t0:.0f}s", flush=True)

    async with aiohttp.ClientSession() as s:
        await asyncio.gather(*(one(s, c) for c in todo))


# ── stage 5 ──────────────────────────────────────────────────────────────────
def upload(B: pd.DataFrame, Fd: pd.DataFrame, T: pd.DataFrame):
    import awswrangler as wr
    wr.s3.to_parquet(B, path=f"{S3}/equity_daily/", dataset=True, mode="overwrite", partition_cols=["year"],
                     database="silver", table="equity_daily_pit")
    wr.s3.to_parquet(Fd, path=f"{S3}/fundamentals/", dataset=True, mode="overwrite",
                     database="silver", table="fundamentals_pit")
    wr.s3.to_parquet(T, path=f"{S3}/tickers/", dataset=True, mode="overwrite", database="silver", table="tickers_pit")
    print(f"stage 5: uploaded {len(B):,} bars, {len(Fd):,} filings, {len(T):,} tickers -> silver.*_pit", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", type=int, default=0); a = ap.parse_args()
    assert KEY, "POLYGON_API_KEY not set"
    D.mkdir(parents=True, exist_ok=True)
    T = asyncio.run(stage_tickers())
    S = asyncio.run(stage_splits())
    if a.stage in (0, 3):
        asyncio.run(stage_bars(T))
    B = assemble_bars(S)
    B.to_parquet(D / "equity_daily_pit.parquet", index=False)
    print(f"bars assembled: {len(B):,} rows, {B.ticker.nunique():,} tickers, {B.date.min().date()} -> {B.date.max().date()}", flush=True)
    addv = (B.assign(dv=B.close * B.volume).groupby(["ticker", "entity"]).dv
              .apply(lambda x: x.rolling(50, min_periods=30).mean().max()))
    liq = addv[addv >= 20e6].reset_index()
    ciks = sorted(set(B.merge(liq[["ticker", "entity"]], on=["ticker", "entity"]).cik.dropna().astype(str)))
    if a.stage in (0, 4):
        asyncio.run(stage_fund(ciks))
    Fd = pd.concat([pd.read_parquet(p) for p in FUND.glob("*.parquet")], ignore_index=True)
    for c in ("filing_date", "start_date", "end_date"):
        Fd[c] = pd.to_datetime(Fd[c], errors="coerce")
    Fd.to_parquet(D / "fundamentals_pit.parquet", index=False)
    print(f"fundamentals: {len(Fd):,} filings for {Fd.cik.nunique():,} companies", flush=True)
    if a.stage in (0, 5):
        upload(B, Fd, T)


if __name__ == "__main__":
    main()
