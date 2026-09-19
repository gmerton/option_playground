#!/usr/bin/env python3
"""
Pull OTM calls for the event-convexity study: is buying cheap convexity into a SCHEDULED event a
positive-expectancy lottery? (Tito's election 40x trades are the motivating instance.)

Entry dates: the session BEFORE each scheduled event (55 FOMC + 4 election days) and, as the control,
every other Wednesday in the same months. Universe: liquid high-ADR names (ADR>=4, ADDV>=$50M) as of the
entry date, capped at TOP_N by ADR so the pull stays bounded.

For each (ticker, entry date) we take calls with 10-45 DTE and delta 0.08-0.30, keeping the row nearest
0.12 and nearest 0.25 delta, plus the full daily path of those contracts (for exits).

Output: data/cache/event_convexity/{entries,paths}.parquet   (gitignored)
Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_event_convexity_pull.py
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np, pandas as pd
from lib.athena_lib import athena

def athena_retry(sql: str, tries: int = 4):
    """Athena throws INTERNAL_ERROR_QUERY_ENGINE on large OR-lists; retry with backoff."""
    for k in range(tries):
        try:
            return athena(sql)
        except Exception as exc:                      # noqa: BLE001
            if k == tries - 1:
                raise
            print(f"    retry {k+1}/{tries-1} after {type(exc).__name__}", flush=True)
            time.sleep(5 * (k + 1))
from lib.regime.trailing import Panel, liquidity_mask

OUT = Path("data/cache/event_convexity"); OUT.mkdir(parents=True, exist_ok=True)
TOP_N = 40
ELECTIONS = ["2020-11-03", "2022-11-08", "2024-11-05"]          # 2026-11-03 is ahead of us

raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
p = Panel.from_long(raw); C, H, L = p.close, p.high, p.low
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
adr = (H / L - 1).shift(1).rolling(20).mean() * 100
idx = C.index

ev = json.load(open("data/fomc_dates.json"))
events = sorted(set(ev["scheduled"]) | set(ELECTIONS))
events = [e for e in events if pd.Timestamp(e) >= idx[0] and pd.Timestamp(e) <= idx[-1]]

def entry_before(d: str) -> pd.Timestamp | None:
    pos = idx.searchsorted(pd.Timestamp(d))
    return idx[pos - 1] if 0 < pos < len(idx) else None

rows = []
for e in events:
    d = entry_before(e)
    if d is None:
        continue
    i = idx.get_loc(d)
    a = adr.iloc[i][elig.iloc[i]].dropna()
    top = a[a >= 4].sort_values(ascending=False).head(TOP_N)
    for sym in top.index:
        rows.append(dict(entry=str(d.date()), event=e, sym=sym, kind="event", adr=float(top[sym])))
# control: mid-month Wednesdays in the same months, no event within 3 sessions
evset = {pd.Timestamp(x) for x in events}
for m in sorted({pd.Timestamp(e).to_period("M") for e in events}):
    days = [x for x in idx if x.to_period("M") == m and x.weekday() == 2]
    for d in days:
        if any(abs((d - x).days) <= 3 for x in evset):
            continue
        i = idx.get_loc(d)
        a = adr.iloc[i][elig.iloc[i]].dropna()
        top = a[a >= 4].sort_values(ascending=False).head(TOP_N)
        for sym in top.index:
            rows.append(dict(entry=str(d.date()), event="", sym=sym, kind="control", adr=float(top[sym])))
E = pd.DataFrame(rows).drop_duplicates(["entry", "sym"])
print(f"{len(E):,} (ticker, date) entries: {(E.kind=='event').sum()} event / {(E.kind=='control').sum()} control, "
      f"{E.sym.nunique()} names, {E.entry.nunique()} dates", flush=True)

def chunk_sql(pairs: list[tuple[str, str]]) -> str:
    ors = " OR ".join(f"(ticker='{s}' AND trade_date=DATE '{d}')" for d, s in pairs)
    return f"""
WITH c AS (
  SELECT ticker, trade_date, expiry, strike, bid, ask, delta, (bid_iv+ask_iv)/2 iv,
         date_diff('day', trade_date, expiry) dte
  FROM silver.options_daily_v3
  WHERE cp='C' AND bid>0 AND ask>=bid AND delta BETWEEN 0.08 AND 0.30
    AND date_diff('day', trade_date, expiry) BETWEEN 10 AND 45 AND ({ors})
),
r AS (SELECT c.*, row_number() OVER (PARTITION BY ticker, trade_date ORDER BY abs(delta-0.12)) r12,
                  row_number() OVER (PARTITION BY ticker, trade_date ORDER BY abs(delta-0.25)) r25 FROM c)
SELECT ticker, trade_date, expiry, strike, bid, ask, delta, iv, dte, r12=1 AS is12, r25=1 AS is25
FROM r WHERE r12=1 OR r25=1"""

pairs = list(E[["entry", "sym"]].itertuples(index=False, name=None))
frames, CH = [], 150
for k in range(0, len(pairs), CH):
    part = OUT / f"entries_part_{k:05d}.parquet"
    if part.exists():
        frames.append(pd.read_parquet(part)); continue
    t0 = time.time()
    d = athena_retry(chunk_sql(pairs[k:k + CH]))
    d.to_parquet(part, index=False); frames.append(d)
    print(f"  entries {min(k + CH, len(pairs))}/{len(pairs)} ({time.time()-t0:.0f}s)", flush=True)
ENT = pd.concat(frames, ignore_index=True)
ENT.to_parquet(OUT / "entries.parquet", index=False)
print(f"entry contracts: {len(ENT):,}", flush=True)

con = ENT[["ticker", "expiry", "strike"]].drop_duplicates()
frames = []
exps = sorted(con.expiry.unique())
for k in range(0, len(exps), 3):
    ch = exps[k:k + 3]
    ors = " OR ".join(
        f"(expiry=DATE '{pd.Timestamp(e).date()}' AND ticker IN ({','.join(chr(39)+t+chr(39) for t in con[con.expiry==e].ticker.unique())}))"
        for e in ch)
    part = OUT / f"paths_part_{k:05d}.parquet"
    if part.exists():
        frames.append(pd.read_parquet(part)); continue
    t0 = time.time()
    d = athena_retry(f"""SELECT ticker, trade_date, expiry, strike, bid, ask, delta
                         FROM silver.options_daily_v3 WHERE cp='C' AND ({ors})""")
    d.to_parquet(part, index=False); frames.append(d)
    print(f"  paths expiries {k + len(ch)}/{len(exps)} ({time.time()-t0:.0f}s)", flush=True)
pd.concat(frames, ignore_index=True).to_parquet(OUT / "paths.parquet", index=False)
print("done")
