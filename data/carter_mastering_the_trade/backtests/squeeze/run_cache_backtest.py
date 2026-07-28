#!/usr/bin/env python3
"""
Squeeze backtest #1 — broad cross-section, off the Minervini day-cache.

~5,300 names, 2025-05 -> 2026-07 (one regime). Answers "is the squeeze-release a
tradable cross-sectional signal in the CURRENT tape?" It cannot answer regime decay
(see run_longhistory_backtest.py for that).

Method: every (ticker, date) where the squeeze fires is a signal. Forward close-to-close
returns at 5/10/20d are compared against the BASELINE = every eligible (ticker, date)
cell in the same universe and window. Without that baseline you are measuring market
drift, not the signal.

Cross-sectional correlation is handled by also reporting date-level stats: average the
signal's excess return across names within a date, then take stats over the ~230 dates.
That is the number to trust; the raw n is not 6,000 independent observations.

Run:  PYTHONPATH=src:<thisdir> .venv/bin/python3 run_cache_backtest.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from lib.minervini.scan import load_cache
from squeeze_lib import squeeze, squeeze_duration, forward_returns

CACHE = "data/cache/minervini_matrix.parquet"
HORIZONS = (5, 10, 20)
PRICE_MIN = 10.0
ADDV_MIN = 20e6


def stats(sig_mask: pd.DataFrame, fwd: dict, elig: pd.DataFrame, label: str) -> list[dict]:
    out = []
    for h, f in fwd.items():
        s = f.where(sig_mask & elig).stack().dropna()
        b = f.where(elig).stack().dropna()
        if len(s) < 30:
            out.append({"setup": label, "h": h, "n": len(s)})
            continue
        # date-level: mean excess per date, then stats across dates
        base_by_date = f.where(elig).mean(axis=1)
        sig_by_date = f.where(sig_mask & elig).mean(axis=1)
        exc = (sig_by_date - base_by_date).dropna()
        t = exc.mean() / (exc.std(ddof=1) / np.sqrt(len(exc))) if len(exc) > 2 else np.nan
        out.append({
            "setup": label, "h": h, "n": len(s),
            "mean%": s.mean() * 100, "med%": s.median() * 100,
            "win%": (s > 0).mean() * 100,
            "base%": b.mean() * 100, "basewin%": (b > 0).mean() * 100,
            "edge%": (s.mean() - b.mean()) * 100,
            "dates": len(exc), "t_date": t,
        })
    return out


def main() -> None:
    close, high, low, dolvol = load_cache(CACHE)
    print(f"cache: {close.shape[1]} names, {close.index.min().date()} -> {close.index.max().date()} "
          f"({len(close)} sessions)\n")

    addv = dolvol.rolling(50, min_periods=50).mean()
    elig = (close >= PRICE_MIN) & (addv >= ADDV_MIN) & close.notna()

    r = squeeze(close, high, low)
    fire, mom, on = r["fire"], r["mom"], r["on"]
    dur = squeeze_duration(on).shift(1)          # length of the squeeze that just ended
    fwd = forward_returns(close, HORIZONS)

    mom_up = mom > 0
    mom_rising = mom > mom.shift(1)

    print(f"eligible cells: {int(elig.sum().sum()):,}   squeeze-ON rate: "
          f"{on.where(elig).stack().mean()*100:.1f}% of eligible bars")
    print(f"total fires (eligible): {int((fire & elig).sum().sum()):,}\n")

    rows = []
    rows += stats(fire, fwd, elig, "fire (any direction)")
    rows += stats(fire & mom_up, fwd, elig, "fire + mom>0  [LONG]")
    rows += stats(fire & ~mom_up, fwd, elig, "fire + mom<0  [SHORT sig]")
    rows += stats(fire & mom_up & mom_rising, fwd, elig, "fire + mom>0 + rising")
    rows += stats(fire & mom_up & (dur >= 6), fwd, elig, "fire + mom>0 + dur>=6")
    rows += stats(fire & mom_up & (dur >= 12), fwd, elig, "fire + mom>0 + dur>=12")
    rows += stats(on & mom_up, fwd, elig, "still IN squeeze + mom>0 (control)")

    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200, "display.max_columns", 50)
    print(df.to_string(index=False, float_format=lambda x: f"{x:8.3f}"))

    # --- KC-multiplier sensitivity: the hard-coded threshold ---
    print("\n\nKC multiplier sensitivity (fire + mom>0, h=10):")
    sens = []
    for kc in (1.0, 1.5, 2.0, 2.5):
        rr = squeeze(close, high, low, kc_mult=kc)
        m = rr["fire"] & (rr["mom"] > 0)
        st = stats(m, {10: fwd[10]}, elig, f"kc={kc}")[0]
        st["on_rate%"] = rr["on"].where(elig).stack().mean() * 100
        sens.append(st)
    print(pd.DataFrame(sens).to_string(index=False, float_format=lambda x: f"{x:8.3f}"))

    df.to_csv("data/carter_mastering_the_trade/backtests/squeeze/cache_results.csv", index=False)
    print("\nwrote cache_results.csv")


if __name__ == "__main__":
    main()
