#!/usr/bin/env python3
"""
Stage 1 of the spike-vs-grind exit test: pull real call prints for the breakout pool.

Tito's documented vehicle is a 0.20-0.35 delta call at >= 15 DTE. This pulls every call on the top-200
breakout names with DTE 0-80 and delta 0.02-0.98, which covers BOTH the entry selection (0.20-0.35 delta
on the signal day) and the contract's whole forward path (delta drifts anywhere once the trade works or
fails, so the path cannot be delta-filtered).

⚠ `options_cache` (MySQL) cannot serve this: 49 tickers, almost all ETFs and mega-caps -- not the
breakout universe. v3 has 11.5k tickers.
⚠ bid/ask coverage in v3 ends ~2026-03, so the test window stops there.
⚠ v3 strikes and greeks are RAW (never split-adjusted) while the equity panel is adjusted. Strikes are
only ever compared to other v3 rows for the SAME contract, and P&L is computed from bid/ask alone, so no
cross-source price comparison is made. Spot is never taken from the panel for settlement.

One query per year (year is a partition key). Writes one parquet per year to the scratchpad.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 -u pull_spike_exit_chains.py
"""
from __future__ import annotations

import pathlib
import sys
import time

import pandas as pd

from lib.athena_lib import athena
from lib import constants as K

OUT = pathlib.Path("/private/tmp/claude-501/-Users-gmerton-v2-options-playground/"
                   "0dc56bae-9a64-43e3-9215-162f5d8a0c59/scratchpad/chains")
EVENTS = pathlib.Path("data/studies/precision_tier_freeze_forward_2026-09-23.csv")
N_TICKERS = 200
YEARS = range(2019, 2027)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    E = pd.read_csv(EVENTS, parse_dates=["date"])
    E = E[E.date <= "2026-03-01"]
    tickers = sorted(E.sym.value_counts().head(N_TICKERS).index)
    print(f"{len(tickers)} tickers covering {int(E.sym.isin(tickers).sum()):,} of {len(E):,} events "
          f"({100*E.sym.isin(tickers).mean():.0f}%)")
    tk = "','".join(tickers)

    for y in YEARS:
        f = OUT / f"calls_{y}.parquet"
        if f.exists():
            print(f"  {y}: already have {f.name} ({f.stat().st_size/1e6:.0f} MB) — skip")
            continue
        q = f"""
        SELECT trade_date, ticker, strike, expiry, bid, ask, delta, open_interest, volume
        FROM "{K.S3TABLES_CATALOG}"."{K.DB}"."{K.TABLE}"
        WHERE year(trade_date) = {y}
          AND cp = 'C'
          AND ticker IN ('{tk}')
          AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 80
          AND delta BETWEEN 0.02 AND 0.98
        """
        t0 = time.time()
        try:
            d = athena(q)
        except Exception as e:
            print(f"  {y}: ERROR {type(e).__name__}: {str(e)[:200]}")
            continue
        d.to_parquet(f, index=False)
        print(f"  {y}: {len(d):>10,} rows, {d.ticker.nunique():>3} names, "
              f"{time.time()-t0:>5.0f}s -> {f.name} ({f.stat().st_size/1e6:.0f} MB)", flush=True)

    got = sorted(OUT.glob("calls_*.parquet"))
    print(f"\ndone: {len(got)} files, {sum(p.stat().st_size for p in got)/1e9:.2f} GB total")


if __name__ == "__main__":
    sys.exit(main())
