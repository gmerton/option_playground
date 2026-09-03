#!/usr/bin/env python3
"""
Long straddle — controlled DTE sweep (7 / 14 / 21 / 28, tolerance +/-2).

PRE-REGISTERED HYPOTHESIS (stated before looking at results):
  The entry gate is FVR >= 1.20, a 30->90 DAY forward-vol signal, but the trade
  lives 7 days. If the FVR signal is real, a longer-dated straddle should capture
  more of the vol expansion it predicts, so results should IMPROVE with DTE.
  A flat or declining profile falsifies it.

Tolerance is +/-2, not +/-5. Friday entry into Friday expiry gives exact 7-day
multiples, so +/-5 collapses a "10 DTE" target onto 7 (that is the mislabelling
corrected in the playbook on 2026-08-08). +/-2 keeps the buckets disjoint.

Guardrail: three striking DTE gradients turned up this week and two were artifacts
(selection bias, then parameterisation). Any monotonic result here must survive the
era split before it is believed.

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_track2_dte_sweep.py
"""
from __future__ import annotations

from datetime import date
import pandas as pd

import run_fvr_straddle_regression as R
from run_fvr_straddle_regression import BATCH_SIZE, DEFAULT_START, load_fvr

DTES = [7, 14, 21, 28]
TOL = 2
OUT = "track2_dte_sweep.csv"
TICKER_FILE = "data/watchlist/long_straddle_approved.txt"


def pull_one(tickers, dte, start, end) -> pd.DataFrame:
    # _straddle_sql reads these at call time
    R.DTE_TARGET, R.DTE_TOL = dte, TOL
    frames = []
    nb = (len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(tickers), BATCH_SIZE):
        b = tickers[i:i + BATCH_SIZE]
        print(f"  [DTE {dte:>2} batch {i//BATCH_SIZE+1}/{nb}] {b[0]}...{b[-1]}", end="  ", flush=True)
        sdf = R.fetch_straddle_batch(b, start, end)
        if sdf.empty:
            print("-> 0"); continue
        fdf = load_fvr(b, start, end)
        m = sdf.merge(fdf.rename(columns={"trade_date": "entry_date"}),
                      on=["ticker", "entry_date"], how="inner")
        m = m.dropna(subset=["payout", "fvr_put_30_90"])
        m = m[m["entry_premium"] > 0]
        m["ret_pct_long"] = (m["payout"] - m["entry_premium"]) / m["entry_premium"] * 100
        m["dte_target"] = dte
        print(f"-> {len(m):,}")
        if len(m):
            frames.append(m)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def main() -> None:
    tickers = [l.strip().upper() for l in open(TICKER_FILE) if l.strip()]
    start, end = DEFAULT_START, date.today()
    print(f"DTE sweep — {len(tickers)} tickers, targets {DTES} (+/-{TOL}), {start} -> {end}")
    out = []
    for d in DTES:
        t = pull_one(tickers, d, start, end)
        if len(t):
            print(f"  DTE {d}: {len(t):,} trades, actual DTE mean {t.dte.mean():.2f}\n")
            out.append(t)
    if not out:
        print("no data"); return
    df = pd.concat(out, ignore_index=True)
    df.to_csv(OUT, index=False)
    print(f"\n{len(df):,} rows saved -> {OUT}")
    print(df.groupby("dte_target").agg(n=("ret_pct_long", "size"),
                                       actual_dte=("dte", "mean"),
                                       mean_ret=("ret_pct_long", "mean")).round(2).to_string())


if __name__ == "__main__":
    main()
