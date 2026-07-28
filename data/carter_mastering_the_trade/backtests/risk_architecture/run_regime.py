#!/usr/bin/env python3
"""
MARKET-REGIME FILTER — the largest untested variable in the whole study.

The broad-universe run produced ~-53% drawdowns, which is what buying breakouts through 2008
looks like. Every test so far has been regime-blind, yet "market posture & regime" is Martin
Luk's SECOND-largest principle category (24 principles, 111 mentions, 20% of his corpus), and
Minervini/Qullamaggie both sit in cash in bad tape. So the omission is not a detail.

Two ways a regime rule can act, and they are very different claims:

  ENTRY GATE   Do not open anything while the market is below trend. Positions already on run
               their normal exit rules. This is "don't start fights in a bad tape."
  GATE + EXIT  The same, plus close every open position on the first close where regime turns
               off. This is "get flat in a bad tape." Strictly more protective, and strictly
               more prone to whipsaw around the threshold.

Regimes tested (all computed on SPY, all known at the signal bar's close — no lookahead):
  none            baseline, regime-blind
  SPY>200SMA      the classic
  SPY>200SMA+up   above the 200-day AND the 200-day itself rising over 20 days

Architecture is pinned to the two configurations that won earlier (2.0ATR / 20EMA stops,
close<50EMA / target 4R exits) — the architecture question is settled and this run is about
regime alone.

Usage: PYTHONPATH=src .venv/bin/python3 data/carter_mastering_the_trade/backtests/risk_architecture/run_regime.py
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
SPY_SRC = "data/carter_mastering_the_trade/backtests/opening_gap/gapdata.parquet"
SPY_CAGR = 10.7

A.STOPS = [s for s in A.STOPS if s[0] in ("2.0ATR", "20EMA")]
A.EXITS = ["close<50EMA", "target 4R"]
SLOT_GRID = [30, 50]


def regimes() -> dict[str, pd.Series]:
    spy = pd.read_parquet(SPY_SRC)
    spy = spy[spy.ticker == "SPY"].sort_values("date").set_index("date")["close"]
    ma200 = spy.rolling(200, min_periods=200).mean()
    rising = ma200 > ma200.shift(20)
    return {
        "none": pd.Series(True, index=spy.index),
        "SPY>200SMA": (spy > ma200).fillna(False),
        "SPY>200SMA+up": ((spy > ma200) & rising).fillna(False),
    }


def main() -> None:
    parts = sorted(glob.glob(BROAD))
    if not parts:
        sys.exit("no broad_history parts — run fetch_broad.py first")
    regs = regimes()
    for k, v in regs.items():
        print(f"  regime '{k}': ON {100*v.mean():.1f}% of sessions")

    panel = [pd.read_parquet(p) for p in parts]
    rows, per_trade = [], []

    for rname, rser in regs.items():
        for mode in (["gate"] if rname == "none" else ["gate", "gate+exit"]):
            trades = []
            for px in panel:
                px = px.dropna(subset=["open", "close"]).sort_values(["ticker", "date"])
                for tkr, g in px.groupby("ticker"):
                    if len(g) < 400:
                        continue
                    g = g.reset_index(drop=True)
                    a = A.prep(g)
                    on = rser.reindex(pd.DatetimeIndex(a["dates"])).ffill().fillna(False).to_numpy()
                    off = ~on
                    for name, mask in A.entry_tiers(a).items():
                        sig = A.to_indices(mask & on, len(a["c"]))
                        trades += A.run(a, sig, tkr, name,
                                        regime_off=off if mode == "gate+exit" else None)
            df = pd.DataFrame(trades)
            if df.empty:
                continue
            df["entry_date"] = pd.to_datetime(df["entry_date"])
            df["exit_date"] = pd.to_datetime(df["exit_date"])
            tag = "none" if rname == "none" else f"{rname} [{mode}]"
            print(f"\n{tag}: {len(df):,} trade rows", flush=True)

            q = df[(df["stop"] == "2.0ATR") & (df["exit"] == "close<50EMA")]
            for en, gg in q.groupby("entry"):
                per_trade.append({"regime": tag, "entry": en, "n": len(gg),
                                  "mean_pct": 100 * gg.ret.mean(),
                                  "win": 100 * (gg.ret > 0).mean(),
                                  "med_hold": gg.hold.median(),
                                  "t": gg.ret.mean() / (gg.ret.std(ddof=1) / np.sqrt(len(gg)))})
            for slots in SLOT_GRID:
                for (en, st, ex), gg in df.groupby(["entry", "stop", "exit"], observed=True):
                    r = A.simulate(gg, slots=slots)
                    if r:
                        rows.append({"regime": tag, "slots": slots, "entry": en,
                                     "stop": st, "exit": ex, **r})

    res = pd.DataFrame(rows)
    res.to_csv(f"{HERE}/regime_results.csv", index=False)
    pt = pd.DataFrame(per_trade)
    order = [e for e in A.ENTRY_ORDER]

    st, ex, slots = "2.0ATR", "close<50EMA", 30
    fx = res[(res["stop"] == st) & (res["exit"] == ex) & (res["slots"] == slots)]

    print("\n" + "=" * 118)
    print(f"1.  MAX DRAWDOWN %  ({st}, {ex}, {slots} slots) — does regime fix the -53%?")
    print("=" * 118)
    print(fx.pivot(index="entry", columns="regime", values="maxDD%")
          .reindex([e for e in order if e in fx.entry.values]).round(1).to_string())

    print("\n" + "=" * 118)
    print(f"2.  CAGR %   (SPY over the same window ~{SPY_CAGR}%)")
    print("=" * 118)
    print(fx.pivot(index="entry", columns="regime", values="CAGR%")
          .reindex([e for e in order if e in fx.entry.values]).round(2).to_string())

    print("\n" + "=" * 118)
    print("3.  MAR (CAGR / |maxDD|) — the metric regime filtering should actually improve")
    print("=" * 118)
    print(fx.pivot(index="entry", columns="regime", values="MAR")
          .reindex([e for e in order if e in fx.entry.values]).round(2).to_string())

    print("\n  avg exposure %:")
    print(fx.pivot(index="entry", columns="regime", values="avg_expo%")
          .reindex([e for e in order if e in fx.entry.values]).round(1).to_string())

    print("\n" + "=" * 118)
    print("4.  PER-TRADE MEAN % — is regime improving the trades, or only the equity path?")
    print("=" * 118)
    print(pt.pivot(index="entry", columns="regime", values="mean_pct")
          .reindex([e for e in order if e in pt.entry.values]).round(2).to_string())
    print("\n  n trades:")
    print(pt.pivot(index="entry", columns="regime", values="n")
          .reindex([e for e in order if e in pt.entry.values]).to_string())

    print("\n" + "=" * 118)
    print("5.  BEST OVERALL CONFIGURATIONS (any regime / slots / stop / exit), by MAR")
    print("=" * 118)
    top = res.sort_values("MAR", ascending=False).head(12)
    print(top[["regime", "entry", "slots", "stop", "exit", "avg_expo%",
               "CAGR%", "maxDD%", "MAR", "Sharpe"]].round(2).to_string(index=False))
    print(f"\n  cells beating SPY ({SPY_CAGR}% CAGR): {(res['CAGR%'] > SPY_CAGR).sum()} of {len(res)}")

    print(f"\n\nwrote {HERE}/regime_results.csv")


if __name__ == "__main__":
    main()
