#!/usr/bin/env python3
"""
Widen the earnings event set, and add the two variables the old one lacked.

The 2026-09-18 drift study was limited three ways, all of which it flagged: coverage was
**241 of 1,743** panel names (MySQL `earnings_report` carries only 275 tickers); there was no
EPS-surprise data, so "good" was proxied by the tape's own reaction -- which conflates drift with
momentum; and AMC/BMO timing was unknown, so the reaction day was guessed as whichever of
[report, report+1] moved more.

yfinance's earnings calendar fixes all three: ~50 quarters per name, an `EPS Estimate` /
`Reported EPS` / `Surprise(%)` triple, and a timestamped report hour (16:00 = after the close,
morning = before the open).

Output: data/cache/earnings_yf.parquet -- ticker, ts, session, timing, eps_est, eps_act, surprise_pct.

Usage: PYTHONPATH=src .venv/bin/python3 run_earnings_calendar_pull.py
"""
from __future__ import annotations
import sys, time, warnings
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd, yfinance as yf
warnings.filterwarnings("ignore")

OUT = "data/cache/earnings_yf.parquet"
LIMIT, WORKERS = 60, 3          # 8 workers got rate-limited after ~200 names; 3 + retry is slower but lands


def one(t: str):
    for attempt in range(2):
        try:
            e = yf.Ticker(t).get_earnings_dates(limit=LIMIT)
            if e is None or not len(e):
                return None
            e = e.reset_index()
            e.columns = [str(c) for c in e.columns]
            dc = e.columns[0]
            out = pd.DataFrame({
                "ticker": t,
                "ts": pd.to_datetime(e[dc], utc=True),
                "eps_est": pd.to_numeric(e.get("EPS Estimate"), errors="coerce"),
                "eps_act": pd.to_numeric(e.get("Reported EPS"), errors="coerce"),
                "surprise_pct": pd.to_numeric(e.get("Surprise(%)"), errors="coerce")})
            return out
        except Exception:
            if attempt: return None
            time.sleep(1.5)
    return None


def main():
    panel = sorted(pd.read_parquet("data/cache/liquid_panel_2019.parquet").ticker.unique())
    # --resume: only fetch names missing from the cache, so a rate-limited run can be topped up
    prior = None
    if "--resume" in sys.argv and Path(OUT).exists():
        prior = pd.read_parquet(OUT)
        panel = [t for t in panel if t not in set(prior.ticker)]
        print(f"resume: {len(prior.ticker.unique()):,} cached, {len(panel):,} still to fetch", flush=True)
    print(f"pulling earnings history for {len(panel):,} panel names ({WORKERS} workers)...", flush=True)
    got, fail, t0 = [], 0, time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, t): t for t in panel}
        for k, f in enumerate(as_completed(futs), 1):
            r = f.result()
            if r is None or not len(r): fail += 1
            else: got.append(r)
            if k % 200 == 0:
                print(f"  {k:,}/{len(panel):,}  ok {len(got):,}  fail {fail:,}  "
                      f"{time.time()-t0:.0f}s", flush=True)
    E = pd.concat(([prior] if prior is not None else []) + got, ignore_index=True)
    # the report hour is the AMC/BMO tell: 16:00 ET = after the close, morning = before the open
    et = E.ts.dt.tz_convert("America/New_York")
    E["session"] = et.dt.date
    E["timing"] = pd.cut(et.dt.hour, [-1, 11, 15, 24], labels=["BMO", "midday", "AMC"]).astype(str)
    E = E.sort_values(["ticker", "ts"]).drop_duplicates(["ticker", "session"])
    E.to_parquet(OUT, index=False)
    print(f"\n{len(E):,} earnings events | {E.ticker.nunique():,} tickers "
          f"({100*E.ticker.nunique()/len(panel):.0f}% of the panel) | failed {fail:,}")
    print(f"  with surprise%: {E.surprise_pct.notna().sum():,} ({100*E.surprise_pct.notna().mean():.0f}%)")
    print(f"  timing: {E.timing.value_counts().to_dict()}")
    print(f"  dates {E.session.min()} -> {E.session.max()}  ->  {OUT}")


if __name__ == "__main__":
    main()
