#!/usr/bin/env python3
"""Pull every 424B4 (final prospectus) from the EDGAR quarterly full index, 2010Q1 -> 2025Q4.

Output: data/cache/sec_424b4_index.parquet (cik, company, form, date). One request per quarter; SEC fair access:
descriptive User-Agent (the repo's convention, run_sec_companyfacts_pull.py), well under 10 requests/second.
Usage: .venv/bin/python3 run_sec_424b4_index.py
"""
import time
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parent
OUT = REPO / "data/cache/sec_424b4_index.parquet"
UA = {"User-Agent": "Gabe Merton research gabe@drivven.ai", "Accept-Encoding": "gzip, deflate"}

rows = []
for y in range(2010, 2026):
    for q in range(1, 5):
        r = requests.get(f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.idx", headers=UA, timeout=120)
        r.raise_for_status()
        for ln in r.text.splitlines():
            if ln.startswith("424B4 "):
                head, cik, date, _fn = ln.rsplit(None, 3)          # company names vary in width; parse from the right
                rows.append(dict(form="424B4", company=head[5:].strip(), cik=cik.zfill(10), date=date))
        print(f"{y}Q{q}: {len(rows):,}", flush=True)
        time.sleep(0.3)
d = pd.DataFrame(rows)
d["date"] = pd.to_datetime(d.date)
d.to_parquet(OUT, index=False)
print(f"saved {len(d):,} rows, {d.cik.nunique():,} CIKs -> {OUT}")
