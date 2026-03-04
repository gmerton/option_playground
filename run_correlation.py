#!/usr/bin/env python3
"""
Three-strategy simultaneous failure analysis.

Strategies (confirmed parameters):
  UVXY: bear call spread (0.50Δ/0.40Δ, All VIX, 50% take)
        + short put       (0.40Δ, VIX<20, 50% take)
        equal-capital blend when both active
  TLT:  bear call spread  (0.35Δ/0.30Δ, VIX≥20 entry filter, 70% take)
  GLD:  bull put spread   (0.30Δ/0.25Δ, VIX<25, 50% take)

Joins all three on entry_date (Friday), then reports:
  - Pairwise simultaneous loss rates and ROC correlation
  - Triple simultaneous loss frequency
  - Per-year breakdown
  - Dates when all three lost on the same week
"""

from __future__ import annotations

import math
from glob import glob

import numpy as np
import pandas as pd


def latest_csv(pattern: str) -> str:
    files = sorted(glob(pattern))
    if not files:
        raise FileNotFoundError(f"No CSV matching: {pattern}")
    return files[-1]


# ── 1. Load & filter each strategy ────────────────────────────────────────────

# UVXY call spreads: 0.50Δ short, 0.10Δ wing, All VIX (vix_threshold is NaN)
uvxy_cs = pd.read_csv(
    latest_csv("uvxy_call_spreads_20dte_spread25_*.csv"),
    parse_dates=["entry_date"],
)
uvxy_cs = uvxy_cs[
    (uvxy_cs["short_delta_target"] == 0.50)
    & (uvxy_cs["wing_delta_width"]  == 0.10)
    & uvxy_cs["vix_threshold"].isna()
    & ~uvxy_cs["split_flag"]
    & ~uvxy_cs["is_open"]
].copy()

# UVXY puts: 0.40Δ, VIX<20
uvxy_put = pd.read_csv(
    latest_csv("uvxy_puts_20dte_spread25_*.csv"),
    parse_dates=["entry_date"],
)
uvxy_put = uvxy_put[
    (uvxy_put["delta_target"]   == 0.40)
    & (uvxy_put["vix_threshold"] == 20.0)
    & ~uvxy_put["split_flag"]
    & ~uvxy_put["is_open"]
].copy()

# TLT call spreads: 0.35Δ short, 0.05Δ wing, 70% profit take (separate CSV),
# VIX≥20 entry filter applied manually on vix_on_entry
tlt_cs = pd.read_csv(
    latest_csv("tlt_call_spreads_pt70_*.csv"),
    parse_dates=["entry_date"],
)
tlt_cs = tlt_cs[
    (tlt_cs["short_delta_target"] == 0.35)
    & (tlt_cs["wing_delta_width"]  == 0.05)
    & tlt_cs["vix_threshold"].isna()
    & ~tlt_cs["split_flag"]
    & ~tlt_cs["is_open"]
    & (tlt_cs["vix_on_entry"] >= 20.0)
].copy()

# GLD put spreads: 0.30Δ short, 0.05Δ wing, VIX<25
gld_ps = pd.read_csv(
    latest_csv("gld_put_spreads_*.csv"),
    parse_dates=["entry_date"],
)
gld_ps = gld_ps[
    (gld_ps["short_delta_target"] == 0.30)
    & (gld_ps["wing_delta_width"]  == 0.05)
    & (gld_ps["vix_threshold"]     == 25.0)
    & ~gld_ps["split_flag"]
    & ~gld_ps["is_open"]
].copy()

print(f"Loaded: UVXY spread={len(uvxy_cs)}  UVXY put={len(uvxy_put)}"
      f"  TLT={len(tlt_cs)}  GLD={len(gld_ps)}")


# ── 2. Build per-week series ───────────────────────────────────────────────────

# UVXY combined: spread is always base; put joins when VIX<20
# ROC = equal-capital blend (0.5/0.5) when both active, spread-only otherwise
cs_w = uvxy_cs[["entry_date", "roc", "is_win"]].rename(
    columns={"roc": "cs_roc", "is_win": "cs_win"}
)
put_w = uvxy_put[["entry_date", "roc", "is_win"]].rename(
    columns={"roc": "put_roc", "is_win": "put_win"}
)
uvxy_w = cs_w.merge(put_w, on="entry_date", how="left")
uvxy_w["uvxy_roc"] = np.where(
    uvxy_w["put_roc"].notna(),
    0.5 * uvxy_w["cs_roc"] + 0.5 * uvxy_w["put_roc"],
    uvxy_w["cs_roc"],
)
uvxy_w["uvxy_win"] = uvxy_w["uvxy_roc"] > 0
uvxy_w = uvxy_w[["entry_date", "uvxy_roc", "uvxy_win"]].copy()

tlt_w = tlt_cs[["entry_date", "roc", "is_win"]].rename(
    columns={"roc": "tlt_roc", "is_win": "tlt_win"}
)

gld_w = gld_ps[["entry_date", "roc", "is_win"]].rename(
    columns={"roc": "gld_roc", "is_win": "gld_win"}
)

# Outer join — preserve all weeks any strategy was active
df = (
    uvxy_w
    .merge(tlt_w, on="entry_date", how="outer")
    .merge(gld_w, on="entry_date", how="outer")
    .sort_values("entry_date")
    .reset_index(drop=True)
)
df["entry_date"] = pd.to_datetime(df["entry_date"])
df["year"] = df["entry_date"].dt.year


# ── 3. Report ─────────────────────────────────────────────────────────────────

BAR = "=" * 72

print(f"\n{BAR}")
print("  THREE-STRATEGY SIMULTANEOUS FAILURE ANALYSIS")
print(f"  UVXY(call spread + put)  |  TLT(call spread)  |  GLD(put spread)")
print(BAR)

# ── 3a. Individual strategy stats ────────────────────────────────────────────
print(f"\n── Individual strategy summary ──────────────────────────────────────")
print(f"  {'Strategy':<8} {'N':>4} {'Win%':>6} {'Avg ROC%':>9} {'Losing wks':>11}")
print("  " + "-" * 42)
for name, col_win, col_roc in [
    ("UVXY",  "uvxy_win", "uvxy_roc"),
    ("TLT",   "tlt_win",  "tlt_roc"),
    ("GLD",   "gld_win",  "gld_roc"),
]:
    sub = df[df[col_win].notna()].copy()
    n       = len(sub)
    win_pct = sub[col_win].mean() * 100
    avg_roc = sub[col_roc].mean() * 100
    n_lose  = (sub[col_win] == False).sum()
    print(f"  {name:<8} {n:>4} {win_pct:>5.1f}% {avg_roc:>+8.2f}% {n_lose:>11}")

# ── 3b. Pairwise simultaneous loss ───────────────────────────────────────────
print(f"\n── Pairwise simultaneous losses ─────────────────────────────────────")
print(f"  {'Pair':<13} {'Both active':>11} {'Both lose':>10} {'Rate':>6} {'ROC corr':>9}")
print("  " + "-" * 52)

pairs = [
    ("UVXY", "uvxy_win", "uvxy_roc", "TLT",  "tlt_win",  "tlt_roc"),
    ("UVXY", "uvxy_win", "uvxy_roc", "GLD",  "gld_win",  "gld_roc"),
    ("TLT",  "tlt_win",  "tlt_roc",  "GLD",  "gld_win",  "gld_roc"),
]
for a_name, a_win, a_roc, b_name, b_win, b_roc in pairs:
    both      = df[df[a_win].notna() & df[b_win].notna()].copy()
    both_lose = both[(both[a_win] == False) & (both[b_win] == False)]
    corr      = both[[a_roc, b_roc]].corr(min_periods=10).iloc[0, 1]
    rate      = len(both_lose) / len(both) * 100 if len(both) else float("nan")
    print(
        f"  {a_name+'/'+b_name:<13}"
        f" {len(both):>11}"
        f" {len(both_lose):>10}"
        f" {rate:>5.1f}%"
        f" {corr:>+9.3f}"
    )

# ── 3c. All three simultaneously ─────────────────────────────────────────────
triple = df[
    df["uvxy_win"].notna() & df["tlt_win"].notna() & df["gld_win"].notna()
].copy()

lose_count = (
    (triple["uvxy_win"] == False).astype(int)
    + (triple["tlt_win"] == False).astype(int)
    + (triple["gld_win"] == False).astype(int)
)
all3_lose   = triple[lose_count == 3]
two_lose    = triple[lose_count >= 2]

print(f"\n── All three strategies active on same week ─────────────────────────")
print(f"  Weeks all 3 active:          {len(triple):>4}")
print(f"  All 3 lose same week:        {len(all3_lose):>4}  ({len(all3_lose)/len(triple)*100:.1f}%)")
print(f"  At least 2 of 3 lose:        {len(two_lose):>4}  ({len(two_lose)/len(triple)*100:.1f}%)")

if not all3_lose.empty:
    print(f"\n  Dates when all 3 lost simultaneously:")
    print(f"  {'Date':<12} {'UVXY ROC':>9} {'TLT ROC':>8} {'GLD ROC':>8}  VIX")
    print("  " + "-" * 48)
    for _, r in all3_lose.sort_values("entry_date").iterrows():
        vix = f"{r['uvxy_roc']:.0%}"  # placeholder — use entry_date to look up VIX
        print(
            f"  {str(r['entry_date'].date()):<12}"
            f" {r['uvxy_roc']*100:>+8.1f}%"
            f" {r['tlt_roc']*100:>+7.1f}%"
            f" {r['gld_roc']*100:>+7.1f}%"
        )
else:
    print("\n  No weeks where all 3 strategies lost simultaneously.")

if not two_lose.empty and len(all3_lose) == 0:
    print(f"\n  Dates when at least 2 of 3 lost (worst joint drawdown weeks):")
    print(f"  {'Date':<12} {'UVXY':>9} {'TLT':>8} {'GLD':>8} {'#Lose':>6}")
    print("  " + "-" * 48)
    for _, r in two_lose.sort_values("entry_date").iterrows():
        u = f"{r['uvxy_roc']*100:>+8.1f}%" if pd.notna(r["uvxy_roc"]) else "    n/a "
        t = f"{r['tlt_roc']*100:>+7.1f}%"  if pd.notna(r["tlt_roc"])  else "   n/a "
        g = f"{r['gld_roc']*100:>+7.1f}%"  if pd.notna(r["gld_roc"])  else "   n/a "
        n_l = lose_count.loc[r.name]
        print(f"  {str(r['entry_date'].date()):<12} {u} {t} {g} {n_l:>6}")

# ── 3d. ROC correlation matrix ───────────────────────────────────────────────
print(f"\n── ROC correlation matrix ───────────────────────────────────────────")
roc_df = df[["uvxy_roc", "tlt_roc", "gld_roc"]].rename(
    columns={"uvxy_roc": "UVXY", "tlt_roc": "TLT", "gld_roc": "GLD"}
)
corr = roc_df.corr(min_periods=20)
print(corr.to_string())

# ── 3e. Per-year breakdown ───────────────────────────────────────────────────
print(f"\n── Per-year: weeks all 3 active, joint loss counts ──────────────────")
print(f"  {'Year':>4}  {'Active':>6}  {'All-3-lose':>10}  {'2-of-3-lose':>12}  "
      f"{'UVXY wins':>10}  {'TLT wins':>9}  {'GLD wins':>9}")
print("  " + "-" * 72)
for yr, grp in triple.groupby("year"):
    n = len(grp)
    lc = (
        (grp["uvxy_win"] == False).astype(int)
        + (grp["tlt_win"] == False).astype(int)
        + (grp["gld_win"] == False).astype(int)
    )
    all3 = (lc == 3).sum()
    two  = (lc >= 2).sum()
    uw   = (grp["uvxy_win"] == True).sum()
    tw   = (grp["tlt_win"] == True).sum()
    gw   = (grp["gld_win"] == True).sum()
    print(
        f"  {yr:>4}  {n:>6}  {all3:>10}  {two:>12}"
        f"  {uw:>4}/{n:<4}  {tw:>4}/{n:<4}  {gw:>4}/{n:<4}"
    )
print(BAR)
