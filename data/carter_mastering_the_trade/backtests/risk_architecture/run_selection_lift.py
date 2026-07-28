#!/usr/bin/env python3
"""
SELECTION LIFT — what is the repo's own breakout scorecard actually worth?

The architecture test established that risk architecture cannot manufacture edge from a weak
entry. That leaves the reciprocal question, which is the one that matters: how much CAGR does
the SELECTION add, holding the architecture fixed?

Method: identical grid (10 stops x 6 exits), identical portfolio sim, identical universe and
dates. The ONLY thing that varies is the entry tier — from the deliberately dumb control up
through the production scorecard's own gates (see arch_lib.entry_tiers). Every added gate is
a nested restriction, so the marginal value of each is readable off the table.

The headline number is the difference between DUMB and the scorecard tiers at a FIXED
architecture. That difference is the price of selection, in CAGR.

⚠ Same limitations as RESULTS.md — survivorship-biased mega-cap universe, drawdowns marked on
realized exits only. They apply equally to every tier, which is exactly why the comparison
between tiers is the deliverable and the absolute levels are not.

Usage: PYTHONPATH=src .venv/bin/python3 data/carter_mastering_the_trade/backtests/risk_architecture/run_selection_lift.py
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, "data/carter_mastering_the_trade/backtests/risk_architecture")
import arch_lib as A  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

HERE = "data/carter_mastering_the_trade/backtests/risk_architecture"
SRC = "data/carter_mastering_the_trade/backtests/squeeze/longhistory.parquet"
FIXED = ("3.0%", "close<50EMA")     # the architecture that won the first test
SPY_CAGR = 10.7                     # SPY total return, same window, from run_checks


def main() -> None:
    px = pd.read_parquet(SRC).dropna(subset=["open", "close"]).sort_values(["ticker", "date"])

    trades, counts = [], {k: 0 for k in A.ENTRY_ORDER}
    for tkr, g in px.groupby("ticker"):
        if len(g) < 400:
            continue
        a = A.prep(g.reset_index(drop=True))
        for name, mask in A.entry_tiers(a).items():
            sig = A.to_indices(mask, len(a["c"]))
            counts[name] += len(sig)
            trades += A.run(a, sig, tkr, name)

    df = pd.DataFrame(trades)
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])
    df.to_parquet(f"{HERE}/lift_trades.parquet", index=False)

    print("=" * 118)
    print("SIGNAL COUNTS BY ENTRY TIER  (299 names, 2006-2026, 10-day cooldown)")
    print("=" * 118)
    base = counts["DUMB"]
    for k in A.ENTRY_ORDER:
        print(f"  {k:<11} {counts[k]:>7,} signals   ({100*counts[k]/base:5.1f}% of DUMB)")

    rows = []
    for (en, st, ex), g in df.groupby(["entry", "stop", "exit"], observed=True):
        r = A.simulate(g)
        if r:
            rows.append({"entry": en, "stop": st, "exit": ex, **r})
    res = pd.DataFrame(rows)
    res.to_csv(f"{HERE}/lift_results.csv", index=False)

    print("\n" + "=" * 118)
    print(f"A.  HEAD TO HEAD AT ONE FIXED ARCHITECTURE  —  stop {FIXED[0]}, exit {FIXED[1]}")
    print("    Architecture is identical across rows. Every difference here is SELECTION.")
    print("=" * 118)
    fx = res[(res["stop"] == FIXED[0]) & (res["exit"] == FIXED[1])].set_index("entry")
    fx = fx.reindex([e for e in A.ENTRY_ORDER if e in fx.index])
    print(fx[["taken", "fill%", "avg_expo%", "CAGR%", "maxDD%", "MAR", "Sharpe", "final_x"]]
          .round(2).to_string())
    if "DUMB" in fx.index:
        d = fx.loc["DUMB", "CAGR%"]
        print(f"\n  lift vs DUMB ({d:+.2f}% CAGR):")
        for e in fx.index:
            if e != "DUMB":
                print(f"    {e:<11} {fx.loc[e,'CAGR%']:+6.2f}%   lift {fx.loc[e,'CAGR%']-d:+6.2f} pp"
                      f"   vs SPY {fx.loc[e,'CAGR%']-SPY_CAGR:+6.2f} pp")

    print("\n" + "=" * 118)
    print("A2. SAME, BUT WITH A VOLATILITY-NORMALIZED STOP  —  2.0ATR, close<50EMA")
    print("    A fixed 3% stop is NOT neutral across tiers: the ADR>=3.5% gate selects names")
    print("    whose ordinary daily range already exceeds it, so a 3% stop is effectively much")
    print("    tighter for the gated tiers. An ATR stop self-scales and removes that artifact.")
    print("=" * 118)
    fa = res[(res["stop"] == "2.0ATR") & (res["exit"] == "close<50EMA")].set_index("entry")
    fa = fa.reindex([e for e in A.ENTRY_ORDER if e in fa.index])
    print(fa[["taken", "fill%", "avg_expo%", "CAGR%", "maxDD%", "MAR", "Sharpe"]].round(2).to_string())

    print("\n" + "=" * 118)
    print("A3. ⚠ THE EXPOSURE CONFOUND — CAGR per unit of capital actually deployed")
    print("    Adding gates cuts signal count, so the sparse tiers sit in CASH most of the time")
    print("    and their CAGR is mechanically depressed. This divides it out. Caveat: linear")
    print("    scaling is an approximation — levering a sparse tier up to full exposure would")
    print("    scale drawdowns too, and compounding is not linear. Read it as a ranking, not a")
    print("    forecast of what the levered version would return.")
    print("=" * 118)
    for label, tab in [("3.0% stop", fx), ("2.0ATR stop", fa)]:
        t = tab.copy()
        t["CAGR/expo"] = t["CAGR%"] / (t["avg_expo%"] / 100)
        print(f"\n  {label}, exit close<50EMA:")
        print(t[["avg_expo%", "CAGR%", "CAGR/expo", "MAR", "Sharpe"]].round(2).to_string())

    print("\n" + "=" * 118)
    print("B.  BEST ARCHITECTURE AVAILABLE TO EACH ENTRY TIER")
    print("    (best-of-60 per row is in-sample cherry-picking — read it as an upper bound)")
    print("=" * 118)
    best = res.loc[res.groupby("entry")["CAGR%"].idxmax()].set_index("entry")
    print(best.reindex([e for e in A.ENTRY_ORDER if e in best.index])
          [["stop", "exit", "taken", "avg_expo%", "CAGR%", "maxDD%", "MAR", "Sharpe"]]
          .round(2).to_string())

    print("\n" + "=" * 118)
    print("C.  ROBUSTNESS — mean and median CAGR across all 60 architectures, per tier")
    print("    A tier that only wins in its best cell is a fluke; one that lifts the whole")
    print("    distribution is real selection.")
    print("=" * 118)
    agg = res.groupby("entry")["CAGR%"].agg(["count", "mean", "median", "min", "max"])
    agg["% cells >0"] = res.groupby("entry")["CAGR%"].apply(lambda x: 100 * (x > 0).mean())
    agg["% cells >SPY"] = res.groupby("entry")["CAGR%"].apply(lambda x: 100 * (x > SPY_CAGR).mean())
    print(agg.reindex([e for e in A.ENTRY_ORDER if e in agg.index]).round(2).to_string())

    print("\n" + "=" * 118)
    print("D.  PER-TRADE QUALITY AT THE FIXED ARCHITECTURE — is selection improving the trades,")
    print("    or just trading less?")
    print("=" * 118)
    sub = df[(df["stop"] == FIXED[0]) & (df["exit"] == FIXED[1])]
    q = sub.groupby("entry").agg(
        n=("ret", "size"), win_pct=("ret", lambda x: 100 * (x > 0).mean()),
        mean_pct=("ret", lambda x: 100 * x.mean()),
        median_pct=("ret", lambda x: 100 * x.median()),
        p90_pct=("ret", lambda x: 100 * x.quantile(0.90)),
        worst_pct=("ret", lambda x: 100 * x.min()),
        med_hold=("hold", "median"),
        stopped_pct=("why", lambda x: 100 * (x == "stop").mean()))
    q["t"] = sub.groupby("entry")["ret"].apply(
        lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))
    print(q.reindex([e for e in A.ENTRY_ORDER if e in q.index]).round(2).to_string())

    print(f"\n\nwrote {HERE}/lift_trades.parquet and {HERE}/lift_results.csv")


if __name__ == "__main__":
    main()
