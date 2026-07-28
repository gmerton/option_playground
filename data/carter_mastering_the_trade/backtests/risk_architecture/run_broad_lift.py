#!/usr/bin/env python3
"""
BROAD-UNIVERSE selection lift — does the measured per-trade edge convert to CAGR
once the universe is wide enough to fill a portfolio?

SELECTION_LIFT.md found the scorecard tiers earn ~3x the control per trade, but sit 77-92%
in cash on a 299-name universe, so none beat SPY. Two things could cause that:

  (a) SIGNAL SCARCITY  — too few qualifying setups to fill the book.
  (b) THE RISK BUDGET  — at 2.0ATR the mean stop is 9.2% wide, so 0.3% risk buys a 3.3%
                         position. TEN of those is 33% gross. Exposure was capped by
                         slots x risk budget regardless of how many signals existed.

(b) was not controlled for in the earlier run and is probably the larger effect: GATES filled
only 39% of its signals at 2.0ATR, meaning 61% were turned away for want of a slot. So slot
count is treated as a VARIABLE here, not a constant, and the universe is widened ~9x at the
same time. Reporting both separates the two causes.

Grid is deliberately reduced to 3 stops x 3 exits: RESULTS.md already settled the architecture
question, and the open question is capacity.

Usage: PYTHONPATH=src .venv/bin/python3 data/carter_mastering_the_trade/backtests/risk_architecture/run_broad_lift.py
"""
from __future__ import annotations

import glob
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
BROAD = f"{HERE}/broad_history/part_*.parquet"
NARROW = "data/carter_mastering_the_trade/backtests/squeeze/longhistory.parquet"
SPY_CAGR = 10.7

# architecture held near the volatility-matched optimum from the prior run
A.STOPS = [s for s in A.STOPS if s[0] in ("2.0ATR", "3.0%", "20EMA")]
A.EXITS = ["close<50EMA", "hold 20d", "target 4R"]
SLOT_GRID = [10, 20, 30, 50]
FIXED = ("2.0ATR", "close<50EMA")


def build_trades(frames, label: str) -> pd.DataFrame:
    trades, counts, nnames = [], {k: 0 for k in A.ENTRY_ORDER}, 0
    for px in frames:
        px = px.dropna(subset=["open", "close"]).sort_values(["ticker", "date"])
        for tkr, g in px.groupby("ticker"):
            if len(g) < 400:
                continue
            nnames += 1
            a = A.prep(g.reset_index(drop=True))
            for name, mask in A.entry_tiers(a).items():
                sig = A.to_indices(mask, len(a["c"]))
                counts[name] += len(sig)
                trades += A.run(a, sig, tkr, name)
    df = pd.DataFrame(trades)
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])
    print(f"\n{label}: {nnames} names with >=400 bars, {len(df):,} trade rows")
    print("  signals by tier: " + "  ".join(f"{k}={counts[k]:,}" for k in A.ENTRY_ORDER))
    return df


def sim_grid(df: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for slots in SLOT_GRID:
        for (en, st, ex), g in df.groupby(["entry", "stop", "exit"], observed=True):
            r = A.simulate(g, slots=slots)
            if r:
                rows.append({"universe": label, "slots": slots, "entry": en,
                             "stop": st, "exit": ex, **r})
    return pd.DataFrame(rows)


def main() -> None:
    parts = sorted(glob.glob(BROAD))
    if not parts:
        sys.exit("no broad_history parts found — run fetch_broad.py first")

    broad = build_trades((pd.read_parquet(p) for p in parts), "BROAD (Minervini universe)")
    narrow = build_trades([pd.read_parquet(NARROW)], "NARROW (299 liquid names)")

    res = pd.concat([sim_grid(broad, "BROAD"), sim_grid(narrow, "NARROW")], ignore_index=True)
    res.to_csv(f"{HERE}/broad_results.csv", index=False)

    st, ex = FIXED
    fx = res[(res["stop"] == st) & (res["exit"] == ex)]

    print("\n" + "=" * 118)
    print(f"1.  DOES A WIDER UNIVERSE + MORE SLOTS FILL THE BOOK?   ({st}, {ex})")
    print("    avg exposure %, by entry tier x slot count")
    print("=" * 118)
    for u in ("NARROW", "BROAD"):
        sub = fx[fx.universe == u]
        if sub.empty:
            continue
        print(f"\n  {u}:")
        print(sub.pivot(index="entry", columns="slots", values="avg_expo%")
              .reindex([e for e in A.ENTRY_ORDER if e in sub.entry.values]).round(1).to_string())

    print("\n" + "=" * 118)
    print(f"2.  CAGR %   ({st}, {ex})   —  SPY over the same window ~{SPY_CAGR}%")
    print("=" * 118)
    for u in ("NARROW", "BROAD"):
        sub = fx[fx.universe == u]
        if sub.empty:
            continue
        print(f"\n  {u}:")
        print(sub.pivot(index="entry", columns="slots", values="CAGR%")
              .reindex([e for e in A.ENTRY_ORDER if e in sub.entry.values]).round(2).to_string())

    print("\n" + "=" * 118)
    print("3.  BEST CONFIGURATION PER TIER ON THE BROAD UNIVERSE (any slots/stop/exit)")
    print("=" * 118)
    b = res[res.universe == "BROAD"]
    if not b.empty:
        best = b.loc[b.groupby("entry")["CAGR%"].idxmax()].set_index("entry")
        print(best.reindex([e for e in A.ENTRY_ORDER if e in best.index])
              [["slots", "stop", "exit", "taken", "fill%", "avg_expo%",
                "CAGR%", "maxDD%", "MAR", "Sharpe"]].round(2).to_string())
        print(f"\n  cells beating SPY ({SPY_CAGR}%): "
              f"{(b['CAGR%'] > SPY_CAGR).sum()} of {len(b)}")

    print("\n" + "=" * 118)
    print("4.  PER-TRADE QUALITY, BROAD vs NARROW — does the edge survive the wider universe,")
    print("    or was it an artifact of the 299 mega-caps?")
    print("=" * 118)
    for label, d in (("NARROW", narrow), ("BROAD", broad)):
        sub = d[(d["stop"] == st) & (d["exit"] == ex)]
        q = sub.groupby("entry").agg(
            n=("ret", "size"), win=("ret", lambda x: 100 * (x > 0).mean()),
            mean_pct=("ret", lambda x: 100 * x.mean()),
            p99=("ret", lambda x: 100 * x.quantile(0.99)),
            med_hold=("hold", "median"))
        q["t"] = sub.groupby("entry")["ret"].apply(
            lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))
        print(f"\n  {label}:")
        print(q.reindex([e for e in A.ENTRY_ORDER if e in q.index]).round(2).to_string())

    print(f"\n\nwrote {HERE}/broad_results.csv")


if __name__ == "__main__":
    main()
