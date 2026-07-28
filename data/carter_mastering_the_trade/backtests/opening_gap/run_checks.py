#!/usr/bin/env python3
"""Confounder checks on the opening-gap study. Run run_gap_study.py first (writes the CSV)."""
from __future__ import annotations

import numpy as np
import pandas as pd

pd.set_option("display.width", 200)
HERE = "data/carter_mastering_the_trade/backtests/opening_gap"

d = pd.read_csv(f"{HERE}/gap_trades.csv", parse_dates=["date"])
sp = d[d.ticker == "SPY"].copy()

print("=" * 90)
print("A. DATA SANITY — 10 largest gaps (looking for split/dividend artifacts)")
print("=" * 90)
big = d.reindex(d.gap_pct.abs().sort_values(ascending=False).index).head(10)
print(big[["date", "ticker", "prev_close", "open", "high", "low", "close",
           "gap_pct", "filled"]].to_string(index=False))

print("\n" + "=" * 90)
print("B. IS THE FILL-RATE DECLINE REAL, OR JUST BIGGER GAPS?")
print("=" * 90)
print("\n  gap size distribution by era (|gap| in ATR units):")
print(d.groupby(["ticker", "era"])["agap_atr"]
      .agg(median="median", p75=lambda x: x.quantile(0.75), mean="mean").round(3).to_string())

print("\n  fill % by era WITHIN each gap-size bucket (composition held fixed):")
piv = d.pivot_table(index="bucket", columns="era", values="filled",
                    aggfunc="mean", observed=True) * 100
n = d.pivot_table(index="bucket", columns="era", values="filled",
                  aggfunc="size", observed=True)
print(pd.concat([piv.round(1), n.add_suffix(" n")], axis=1).to_string())

print("\n  SPY only, fill % by era within bucket:")
piv = sp.pivot_table(index="bucket", columns="era", values="filled",
                     aggfunc="mean", observed=True) * 100
n = sp.pivot_table(index="bucket", columns="era", values="filled",
                   aggfunc="size", observed=True)
print(pd.concat([piv.round(1), n.add_suffix(" n")], axis=1).to_string())

print("\n  SPY 5-year blocks: fill% overall vs. fill% for 0.25-0.5 ATR gaps only")
sp["block"] = (sp.year // 5) * 5
b = sp.groupby("block").agg(n=("filled", "size"),
                            fill_all=("filled", lambda x: 100 * x.mean()),
                            med_gap_atr=("agap_atr", "median"))
mid = sp[sp.bucket == "0.25-0.5"].groupby("block")["filled"].agg(
    n_mid="size", fill_mid=lambda x: 100 * x.mean())
print(pd.concat([b, mid], axis=1).round(2).to_string())

print("\n" + "=" * 90)
print("C. IS 'DAY AFTER A BIG MOVE' JUST THE VIX EFFECT?")
print("=" * 90)
sp["vix_bucket"] = pd.qcut(sp["vix_prev"], 3, labels=["VIX low", "VIX mid", "VIX high"])
tab = sp.pivot_table(index="vix_bucket", columns="after_trend_day", values="r_nostop",
                     aggfunc=["size", "mean"], observed=True)
tab[("mean", False)] *= 1e4
tab[("mean", True)] *= 1e4
print("\n  mean bp per trade (no stop), VIX tercile x day-after->=1ATR-move:")
print(tab.round(2).to_string())


def tstat(x):
    x = x.dropna()
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 20 else np.nan


print("\n  t-stats of the same cells:")
print(sp.pivot_table(index="vix_bucket", columns="after_trend_day", values="r_nostop",
                     aggfunc=tstat, observed=True).round(2).to_string())

print("\n" + "=" * 90)
print("D. HOW MUCH OF THE GAP-DOWN EDGE IS JUST LONG DRIFT?")
print("=" * 90)
for tkr in ["SPY", "QQQ", "IWM", "DIA"]:
    g = d[d.ticker == tkr]
    dn = g[g.gap < 0]
    up = g[g.gap > 0]
    print(f"  {tkr}  gap-down fade (=long): {dn.r_nostop.mean()*1e4:+.2f} bp   "
          f"passive open->close on those days: {dn.oc_long.mean()*1e4:+.2f} bp   "
          f"-> excess {(dn.r_nostop.mean()-dn.oc_long.mean())*1e4:+.2f} bp")
    print(f"  {tkr}  gap-up   fade (=short): {up.r_nostop.mean()*1e4:+.2f} bp   "
          f"passive open->close on those days: {up.oc_long.mean()*1e4:+.2f} bp   "
          f"-> excess {(up.r_nostop.mean()+up.oc_long.mean())*1e4:+.2f} bp")

print("\n" + "=" * 90)
print("E. TRADEABLE SUBSET (>=0.5 ATR), POST-2022 ONLY — the live question")
print("=" * 90)
sub = d[(d.agap_atr >= 0.5) & (d.era.str.startswith("post"))]
r = sub.groupby("ticker")["r_nostop"].agg(
    n="size", win_pct=lambda x: 100 * (x > 0).mean(),
    mean_bp=lambda x: x.mean() * 1e4, t=tstat,
    worst_bp=lambda x: x.min() * 1e4, sum_pct=lambda x: x.sum() * 100)
print(r.round(2).to_string())
print(f"\n  pooled across 4 ETFs: n={len(sub)}  mean={sub.r_nostop.mean()*1e4:+.2f} bp  "
      f"t={tstat(sub.r_nostop):+.2f}  (t overstated: the 4 ETFs share dates)")
print(f"  fill% on this subset: {100*sub.filled.mean():.1f}%")
