#!/usr/bin/env python3
"""
Pull SEC XBRL "company facts" (https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json) for the liquid-panel
names: free, POINT-IN-TIME fundamentals -- every fact carries the date it was FILED (2009 ->). 2026-09-24, for the net
share issuance test (Fama & French 2008) and as a free partial unblock of the value + quality test.

Kept tags (value, period end/start, fiscal year/period, form, FILED date):
  dei:EntityCommonStockSharesOutstanding   cover-page share count (the cleanest point-in-time share count)
  us-gaap: CommonStockSharesOutstanding, WeightedAverageNumberOfSharesOutstandingBasic, NetIncomeLoss, Revenues,
           RevenueFromContractWithCustomerExcludingAssessedTax, Assets, Liabilities, StockholdersEquity,
           NetCashProvidedByUsedInOperatingActivities, LongTermDebtNoncurrent
CIK mapping: SEC company_tickers.json (current) + the Form 4 issuer map (data/cache/insider_purchases.parquet), so
tickers that changed hands or delisted still resolve where possible.
Output: data/cache/sec_companyfacts.parquet. SEC fair access: descriptive User-Agent, <= 10 requests/second.

Usage: PYTHONPATH=src .venv/bin/python3 run_sec_companyfacts_pull.py
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import aiohttp
import pandas as pd
import requests

REPO = Path(__file__).resolve().parent
OUT = REPO / "data/cache/sec_companyfacts.parquet"
PART = REPO / "data/cache/sec_companyfacts"
UA = {"User-Agent": "Gabe Merton research gabe@drivven.ai", "Accept-Encoding": "gzip, deflate"}
TAGS = {"dei": ["EntityCommonStockSharesOutstanding"],
        "us-gaap": ["CommonStockSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic", "NetIncomeLoss",
                    "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "Assets", "Liabilities",
                    "StockholdersEquity", "NetCashProvidedByUsedInOperatingActivities", "LongTermDebtNoncurrent"]}


def cik_map(tickers: list[str]) -> dict[str, str]:
    ct = requests.get("https://www.sec.gov/files/company_tickers.json", headers=UA, timeout=60).json()
    m = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in ct.values()}
    ip = pd.read_parquet(REPO / "data/cache/insider_purchases.parquet", columns=["issuercik", "ticker", "filing_date"])
    m2 = ip.dropna().sort_values("filing_date").groupby("ticker").issuercik.last().to_dict()
    return {t: m.get(t) or (str(m2[t]).zfill(10) if t in m2 else None) for t in tickers}


async def main_async(pairs):
    PART.mkdir(parents=True, exist_ok=True)
    done = {p.stem for p in PART.glob("*.parquet")}
    todo = [(t, c) for t, c in pairs if c and c not in done]
    print(f"{len(todo):,} CIKs to pull ({len(done):,} cached)", flush=True)
    sem = asyncio.Semaphore(6); t0 = time.time(); cnt = [0]

    async def one(s, t, cik):
        async with sem:
            for k in range(5):
                try:
                    async with s.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                                     timeout=aiohttp.ClientTimeout(total=120)) as r:
                        if r.status == 404:
                            j = None; break
                        if r.status != 200:
                            await asyncio.sleep(2 ** k); continue
                        j = await r.json(); break
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    await asyncio.sleep(2 ** k)
            else:
                j = None
            await asyncio.sleep(0.12)
            rows = []
            for ns, tags in TAGS.items():
                facts = ((j or {}).get("facts") or {}).get(ns) or {}
                for tag in tags:
                    for unit, arr in ((facts.get(tag) or {}).get("units") or {}).items():
                        for f in arr:
                            rows.append(dict(cik=cik, ticker=t, tag=tag, unit=unit, val=f.get("val"), start=f.get("start"),
                                             end=f.get("end"), fy=f.get("fy"), fp=f.get("fp"), form=f.get("form"),
                                             filed=f.get("filed"), frame=f.get("frame")))
            pd.DataFrame(rows).to_parquet(PART / f"{cik}.parquet", index=False)
            cnt[0] += 1
            if cnt[0] % 200 == 0:
                print(f"  {cnt[0]:,}/{len(todo):,}  {time.time() - t0:.0f}s", flush=True)

    async with aiohttp.ClientSession(headers=UA) as s:
        await asyncio.gather(*(one(s, t, c) for t, c in todo))


def main() -> None:
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet", columns=["ticker"])
    tickers = sorted(set(raw.ticker) - {"SPY", "QQQ", "IWM", "RSP", "DIA"})
    m = cik_map(tickers)
    pairs = sorted(m.items())
    print(f"{len(tickers):,} panel tickers, {sum(1 for c in m.values() if c):,} with a CIK", flush=True)
    asyncio.run(main_async(pairs))
    parts = [pd.read_parquet(p) for p in PART.glob("*.parquet")]
    F = pd.concat([p for p in parts if len(p)], ignore_index=True)
    for c in ("start", "end", "filed"):
        F[c] = pd.to_datetime(F[c], errors="coerce")
    F.to_parquet(OUT, index=False)
    print(f"{len(F):,} facts, {F.cik.nunique():,} companies, filed {F.filed.min().date()} -> {F.filed.max().date()} -> {OUT}")


if __name__ == "__main__":
    main()
