#!/usr/bin/env python3
"""
Is the crash-leader edge a real effect or one regime episode?

The era test showed the excess is concentrated in 2023-26 and absent 2006-18. Two
competing readings:
  (a) real edge that the older sample was too noisy to show
  (b) ONE regime: things that crashed in 2022 V-recovered through 2023-25, and the
      study is just measuring that single episode

Test: per-year excess (is it many years or two?), and a split on market breadth at
the signal date (% of the liquid universe above its own 200sma). If the edge only
exists when you buy crashes INTO a recovering tape, it is a regime bet, and the
signal itself carries no information about when that tape arrives.

Run:
    PYTHONPATH=src .venv/bin/python3 scratch_crash_leader_regime.py
"""
from __future__ import annotations

import glob

import numpy as np
import pandas as pd

HIST = "data/carter_mastering_the_trade/backtests/risk_architecture/broad_history/*.parquet"
EVENTS = "data/studies/crash_leader_events.parquet"


def breadth() -> pd.Series:
    parts = [pd.read_parquet(f, columns=["date", "ticker", "close", "volume"])
             for f in sorted(glob.glob(HIST))]
    df = pd.concat(parts, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    close = df.pivot(index="date", columns="ticker", values="close").astype("float32")
    vol = df.pivot(index="date", columns="ticker", values="volume").astype("float32")
    sma200 = close.rolling(200, min_periods=200).mean()
    addv = (close * vol).rolling(50, min_periods=50).mean()
    elig = (addv >= 10e6) & (close >= 5)
    above = (close > sma200).where(elig)
    n_elig = elig.sum(axis=1).replace(0, np.nan)   # early bars have no 200sma yet
    return (above.sum(axis=1) / n_elig).rename("breadth")


def per_year(ev, dd, h=252, entry="arrival"):
    s = ev[(ev.h == h) & (ev.entry == entry) & (ev.dd == dd)].dropna(subset=["excess"]).copy()
    s["yr"] = s.date.dt.year
    g = s.groupby("yr").agg(n=("excess", "size"),
                            exc=("excess", "mean"),
                            med=("excess", "median"),
                            win=("excess", lambda x: (x > 0).mean()))
    g["exc%"] = g.exc * 100
    g["med%"] = g.med * 100
    g["win%"] = g.win * 100
    return g[["n", "exc%", "med%", "win%"]]


def main() -> None:
    ev = pd.read_parquet(EVENTS)
    print("computing universe breadth ...", flush=True)
    b = breadth()

    for dd in (30, 50):
        print("\n" + "=" * 70)
        print(f"PER-YEAR EXCESS — dd{dd}/arrival, 252d forward")
        print("=" * 70)
        print(per_year(ev, dd).to_string(float_format=lambda v: f"{v:,.2f}"))

    ev = ev.merge(b.rename_axis("date").reset_index(), on="date", how="left")
    print("\n" + "=" * 70)
    print("BREADTH SPLIT — % of liquid universe above its own 200sma at signal")
    print("=" * 70)
    for dd in (30, 50):
        for h in (63, 252):
            s = ev[(ev.h == h) & (ev.entry == "arrival") & (ev.dd == dd)].dropna(subset=["excess", "breadth"])
            if s.empty:
                continue
            q = pd.qcut(s.breadth, 3, labels=["weak tape", "mid", "strong tape"])
            g = s.groupby(q, observed=True).agg(n=("excess", "size"),
                                                exc=("excess", "mean"),
                                                med=("excess", "median"),
                                                win=("excess", lambda x: (x > 0).mean()))
            g["exc%"], g["med%"], g["win%"] = g.exc * 100, g.med * 100, g.win * 100
            print(f"\ndd{dd} / {h}d:")
            print(g[["n", "exc%", "med%", "win%"]].to_string(float_format=lambda v: f"{v:,.2f}"))


if __name__ == "__main__":
    main()
