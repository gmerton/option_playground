#!/usr/bin/env python3
"""
Pull SEC Form 3/4/5 structured data sets (https://www.sec.gov/dera/data/form-345) and keep only OPEN-MARKET PURCHASES
(non-derivative, TRANS_CODE 'P', acquired 'A') on Form 4 -- the input to the insider cluster-buying test
(run_insider_clusters.py). Point-in-time key = FILING_DATE (when the market could know), not the trade date.

Output: data/cache/insider_purchases.parquet  (one row per purchase line: ticker, filing_date, trans_date, owner,
relationship, title, shares, price, value). Quarterly zips are downloaded one at a time and deleted after parsing.
SEC fair-access rules: a descriptive User-Agent and <= 10 requests/second (we make one request per quarter).

Usage: PYTHONPATH=src .venv/bin/python3 run_sec_insider_pull.py [--start 2010] [--end 2026]
"""
from __future__ import annotations

import argparse
import io
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parent
DIR = REPO / "data/cache/sec_form345"
OUT = REPO / "data/cache/insider_purchases.parquet"
URL = "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{q}_form345.zip"
UA = {"User-Agent": "Gabe Merton research gabe@drivven.ai"}


def parse(zbytes: bytes) -> pd.DataFrame:
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    rd = lambda n, cols: pd.read_csv(z.open(n), sep="\t", usecols=cols, dtype=str, quoting=3, on_bad_lines="skip")
    sub = rd("SUBMISSION.tsv", ["ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE", "ISSUERCIK", "ISSUERTRADINGSYMBOL"])
    tr = rd("NONDERIV_TRANS.tsv", ["ACCESSION_NUMBER", "TRANS_DATE", "TRANS_CODE", "TRANS_SHARES",
                                   "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD"])
    own = rd("REPORTINGOWNER.tsv", ["ACCESSION_NUMBER", "RPTOWNERCIK", "RPTOWNERNAME", "RPTOWNER_RELATIONSHIP",
                                    "RPTOWNER_TITLE"])
    tr = tr[(tr.TRANS_CODE == "P") & (tr.TRANS_ACQUIRED_DISP_CD == "A")]
    sub = sub[sub.DOCUMENT_TYPE.isin(["4", "4/A"])]
    own = own.drop_duplicates("ACCESSION_NUMBER")          # multi-owner filings: first reporting owner
    d = tr.merge(sub, on="ACCESSION_NUMBER").merge(own, on="ACCESSION_NUMBER", how="left")
    d = d.rename(columns=str.lower)
    d["filing_date"] = pd.to_datetime(d.filing_date, format="%d-%b-%Y", errors="coerce")
    d["trans_date"] = pd.to_datetime(d.trans_date, format="%d-%b-%Y", errors="coerce")
    d["shares"] = pd.to_numeric(d.trans_shares, errors="coerce")
    d["price"] = pd.to_numeric(d.trans_pricepershare, errors="coerce")
    d["value"] = d.shares * d.price
    d["ticker"] = d.issuertradingsymbol.str.upper().str.strip()
    return d[["ticker", "issuercik", "filing_date", "trans_date", "rptownercik", "rptownername",
              "rptowner_relationship", "rptowner_title", "shares", "price", "value", "document_type", "accession_number"]]


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--start", type=int, default=2010); ap.add_argument("--end", type=int, default=2026)
    a = ap.parse_args()
    DIR.mkdir(parents=True, exist_ok=True)
    parts = []
    for y in range(a.start, a.end + 1):
        for qn in (1, 2, 3, 4):
            q = f"{y}q{qn}"
            part = DIR / f"{q}_purchases.parquet"
            if part.exists():
                parts.append(pd.read_parquet(part)); continue
            r = requests.get(URL.format(q=q), headers=UA, timeout=120)
            if r.status_code != 200:
                print(f"  {q}: HTTP {r.status_code} (not published yet?)", flush=True); continue
            d = parse(r.content)
            d.to_parquet(part, index=False)
            parts.append(d)
            print(f"  {q}: {len(d):,} purchase lines, {d.ticker.nunique():,} tickers", flush=True)
            time.sleep(0.5)
    P = pd.concat(parts, ignore_index=True).drop_duplicates(["accession_number", "trans_date", "shares", "price"])
    P.to_parquet(OUT, index=False)
    print(f"{len(P):,} purchase lines -> {OUT}; filing dates {P.filing_date.min().date()} -> {P.filing_date.max().date()}")


if __name__ == "__main__":
    main()
