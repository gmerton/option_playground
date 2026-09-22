#!/usr/bin/env python3
"""
The long straddle's IV gate: is the threshold a plateau or a spike, and does IV RANK beat IV PERCENTILE?
(2026-09-22; item 2 of the post-correction queue + method-queue item 2 "parameter-neighbourhood robustness",
applied to the one strategy the correction rates SUPPORTED.)

The 7-DTE long straddle's edge is carried by its IV gate (both gates +4.14%/trade vs +1.3% for the FVR-only
superset). The gate is `iv_pct <= 30`, a RANK percentile of the name's 10-day put IV. Two questions:

  A. NEIGHBOURHOOD: sweep the threshold 10/20/30/40/50/60 with FVR >= 1.20 held fixed. A real gate is a plateau;
     a tuned one is a spike at 30 with neighbours falling away.
  B. IV RANK vs IV PERCENTILE (the OptionsPlay distinction, his @19:51): rank = (iv - min) / (max - min) over the
     trailing window, percentile = share of the window below today. His claimed cheap/rich line is 33 on rank.
     Both are computed here over the trailing 52 ENTRIES per ticker (about a year of weekly entries), strictly
     prior, so this is also a like-for-like rebuild of our own gate on a bounded window.

Returns are `ret_pct_long` = % of premium at MID. The straddle slippage study measured a realistic fill at
-1.9pp of premium, so a "net" column subtracts that flat. t is month-clustered (weekly entries overlap inside a
month); halves split at 2022-01-01.
PRE-REGISTERED READ: the gate is robust if 20/30/40 are all positive with the same sign in both halves and no more
than ~2pp apart at mid. If 30 is a spike, the published number is curve-fit and the honest expectation is the
plateau average. No new rule is adopted here either way.

Usage: PYTHONPATH=src .venv/bin/python3 run_straddle_ivgate_robust.py
"""
from __future__ import annotations
import warnings
from math import sqrt
import numpy as np, pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250)
FILL = 1.9          # pp of premium, the measured realistic-fill haircut
FVR_GATE = 1.20
WIN = 52            # trailing entries per ticker

d = pd.read_parquet("data/cache/straddle_recenter/straddle_gated.parquet")
d["entry_date"] = pd.to_datetime(d.entry_date)
d = d.sort_values(["ticker", "entry_date"]).reset_index(drop=True)
d["month"] = d.entry_date.dt.to_period("M")


def roll_pct(s: pd.Series) -> pd.Series:      # share of the trailing window strictly below today
    return s.rolling(WIN, min_periods=30).apply(lambda w: (w[-1] > w[:-1]).mean() * 100, raw=True)


def roll_rank(s: pd.Series) -> pd.Series:     # (x - min) / (max - min) over the trailing window
    lo = s.rolling(WIN, min_periods=30).min(); hi = s.rolling(WIN, min_periods=30).max()
    return (s - lo) / (hi - lo).replace(0, np.nan) * 100


g = d.groupby("ticker").iv_put_10
d["iv_pct52"] = g.transform(roll_pct)
d["iv_rank52"] = g.transform(roll_rank)
d = d.dropna(subset=["iv_pct52", "iv_rank52"])
print(f"pool: {len(d):,} gated-universe entries, {d.ticker.nunique()} names, "
      f"{d.entry_date.min().date()}..{d.entry_date.max().date()}, {d.month.nunique()} months")
print(f"correlation between our stored iv_pct and the rebuilt 52-entry percentile: {d.iv_pct.corr(d.iv_pct52):.2f}; "
      f"percentile vs rank: {d.iv_pct52.corr(d.iv_rank52):.2f}")


def mt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def row(lab, sub):
    if len(sub) < 50: return dict(cut=lab, n=len(sub), mid=np.nan, net=np.nan, t=np.nan, h1=np.nan, h2=np.nan, per_yr=np.nan)
    m = sub.groupby("month").ret_pct_long.mean()
    h1 = sub[sub.entry_date < "2022-01-01"].ret_pct_long.mean(); h2 = sub[sub.entry_date >= "2022-01-01"].ret_pct_long.mean()
    yrs = (sub.entry_date.max() - sub.entry_date.min()).days / 365.25
    return dict(cut=lab, n=len(sub), mid=sub.ret_pct_long.mean(), net=sub.ret_pct_long.mean() - FILL,
                t=mt(m), h1=h1, h2=h2, per_yr=len(sub) / max(yrs, 1))


fvr = d[d.fvr_put_30_90 >= FVR_GATE]
print("\nA. THRESHOLD NEIGHBOURHOOD (FVR >= 1.20 held fixed), % of premium")
outs = [row("no IV gate", fvr)]
for thr in (10, 20, 30, 40, 50, 60):
    outs.append(row(f"iv percentile <= {thr}", fvr[fvr.iv_pct52 <= thr]))
print(pd.DataFrame(outs).round(2).to_string(index=False))

print("\nB. IV RANK (range-based, the OptionsPlay metric) vs the same thresholds")
outs = [row("no IV gate", fvr)]
for thr in (10, 20, 33, 40, 50, 60):
    outs.append(row(f"iv rank <= {thr}", fvr[fvr.iv_rank52 <= thr]))
print(pd.DataFrame(outs).round(2).to_string(index=False))

print("\nC. the stored gate (iv_pct <= 30, expanding window) for reference, and FVR alone")
print(pd.DataFrame([row("stored iv_pct <= 30 + FVR", d[(d.fvr_put_30_90 >= FVR_GATE) & (d.iv_pct <= 30)]),
                    row("FVR only", fvr), row("whole pool", d)]).round(2).to_string(index=False))

print("\nD. does the gate still work inside the HIGH-IV half? (sanity: is it just buying cheap vol?)")
for lab, sub in (("iv percentile <= 30", fvr[fvr.iv_pct52 <= 30]), ("iv percentile 30-60", fvr[(fvr.iv_pct52 > 30) & (fvr.iv_pct52 <= 60)]),
                 ("iv percentile > 60", fvr[fvr.iv_pct52 > 60])):
    r = row(lab, sub); print(f"  {r['cut']:24} n {r['n']:5}  mid {r['mid']:+6.2f}  net {r['net']:+6.2f}  t {r['t']:+5.2f}  halves {r['h1']:+6.2f} / {r['h2']:+6.2f}")
d.to_parquet("data/cache/straddle_ivgate_robust.parquet", index=False)
