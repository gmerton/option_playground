#!/usr/bin/env python3
"""
Does the credit/width filter improve the ONE certified cell? (2026-09-22, pre-registered here before the run.)

Certified 2026-09-22 (run_tierab_significance.py): selling index put risk below the 50 SMA with VIX >= 20 --
SPY bull put 0.25/0.15 (t 6.07) and SPX condor 0.20c/0.30p (t 5.21); QQQ's same-regime cell (t 3.53) is the same
trade. Separately, credit/width sorts bull put spreads ACROSS liquid names (+7.64pp within-date, t 4.15), but it
did NOT rescue junk names, and within one name it is really a VIX/richness timing variable rather than a
cross-sectional chooser. So this asks the narrow question we can act on:

  inside the certified bearish-high-IV cell, does the credit/width of the specific spread sort the outcome?

Cells: QQQ 0.25/0.15 no stop and SPY 0.25/0.15 no stop, 20 DTE, 50% profit take, Friday entries, Bearish_HighIV
only (below the 50 SMA and VIX >= 20), net of the 2026-09-08 cost model -- i.e. exactly the trade in the book.
Split: terciles of `credit_pct_of_width` within the cell, plus a fixed cw >= 0.20 / 0.25 cut (the filter proposed
from the play), each with month-clustered t and both halves.
PRE-REGISTERED PASS for adopting the filter: the high-cw tercile beats the low by month-clustered t >= 2 with the
same sign in both halves AND the filtered book's mean beats the unfiltered cell. Otherwise the cell is traded as
is and credit/width stays a cross-sectional tool only.

Usage: AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src:. .venv/bin/python3 run_cw_on_certified.py
"""
from __future__ import annotations
import warnings
from datetime import timedelta
from math import sqrt
import numpy as np, pandas as pd
import run_qqq_regime_put_sweep as S
from lib.studies.put_study import fetch_vix_data
from lib.studies.put_spread_study import build_put_spread_trades, find_put_spread_exits, compute_spread_metrics, add_ma_column

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)


def cell(ticker: str) -> pd.DataFrame:
    S.TICKER = ticker; S.SPLIT_DATES = S._SPLIT_DATES.get(ticker, []); S.DTE_TARGET = 20; S.DTE_TOL = 5
    vix = fetch_vix_data(S.START - timedelta(days=5), S.END)
    opts = S._load_options_cache(ticker, S.START, S.END + timedelta(days=30))
    stock = S._load_stock_cache(ticker)
    pos = build_put_spread_trades(opts, short_delta_target=0.25, wing_delta_width=0.10, dte_target=20, dte_tol=5,
                                  entry_weekday=4, split_dates=S.SPLIT_DATES, max_delta_err=0.08, max_spread_pct=None)
    pos["vix_on_entry"] = pos["entry_date"].map(vix.set_index("trade_date")["vix_close"])
    pos = add_ma_column(pos, stock, S.MA_DAYS)
    pos = compute_spread_metrics(find_put_spread_exits(pos, opts, profit_take_pct=0.50, stop_multiple=None))
    pos["regime"] = pos.apply(S.assign_regime, axis=1)
    c = pos[~pos.is_open & ~pos.split_flag & (pos.regime == "Bearish_HighIV")].copy()
    c["ticker"] = ticker
    return c[["ticker", "entry_date", "roc_net", "roc", "credit_pct_of_width", "vix_on_entry", "max_loss"]]


T = pd.concat([cell("QQQ"), cell("SPY")], ignore_index=True)
T["entry"] = pd.to_datetime(T.entry_date); T["month"] = T.entry.dt.to_period("M"); T["cw"] = T.credit_pct_of_width
print(f"certified cell: {len(T)} trades ({T.ticker.value_counts().to_dict()}), "
      f"{T.entry.min().date()}..{T.entry.max().date()}, {T.month.nunique()} months")
print(f"credit/width: median {T.cw.median():.2f}, p10 {T.cw.quantile(.1):.2f}, p90 {T.cw.quantile(.9):.2f}; "
      f"correlation with entry VIX {T.cw.corr(T.vix_on_entry):+.2f}")


def mt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def line(lab, sub):
    if len(sub) < 10:
        print(f"  {lab:28} n {len(sub):>3}  (too few)"); return None
    m = sub.groupby("month").roc_net.mean(); mid = T.entry.min() + (T.entry.max() - T.entry.min()) / 2
    h1 = sub[sub.entry < mid].roc_net.mean() * 100; h2 = sub[sub.entry >= mid].roc_net.mean() * 100
    print(f"  {lab:28} n {len(sub):>3}  net ROC {100*sub.roc_net.mean():+6.2f}%  month {100*m.mean():+6.2f}%  "
          f"t {mt(m):+5.2f}  halves {h1:+6.2f} / {h2:+6.2f}  win {100*(sub.roc_net>0).mean():3.0f}%")
    return dict(mean=sub.roc_net.mean(), t=mt(m), h1=h1, h2=h2)


print("\n== the cell as traded, then by credit/width ==")
base = line("ALL (the certified cell)", T)
q = pd.qcut(T.cw, 3, labels=["low cw", "mid cw", "high cw"])
cells = {k: line(f"{k} (median {T[q==k].cw.median():.2f})", T[q == k]) for k in ["low cw", "mid cw", "high cw"]}
print("\n== the proposed fixed filter ==")
f20 = line("cw >= 0.20", T[T.cw >= 0.20]); f25 = line("cw >= 0.25", T[T.cw >= 0.25]); line("cw < 0.20", T[T.cw < 0.20])

hi = T[q == "high cw"]; lo = T[q == "low cw"]
d = (hi.groupby("month").roc_net.mean() - lo.groupby("month").roc_net.mean()).dropna()
mid = T.entry.min() + (T.entry.max() - T.entry.min()) / 2
dh1 = hi[hi.entry < mid].roc_net.mean() - lo[lo.entry < mid].roc_net.mean()
dh2 = hi[hi.entry >= mid].roc_net.mean() - lo[lo.entry >= mid].roc_net.mean()
print(f"\nhigh-cw minus low-cw: {100*d.mean():+.2f}pp  t {mt(d):+.2f}  halves {100*dh1:+.2f} / {100*dh2:+.2f}  ({len(d)} shared months)")
ok = (mt(d) >= 2 and np.sign(dh1) == np.sign(dh2) == 1 and cells["high cw"] and base and cells["high cw"]["mean"] > base["mean"])
print("PRE-REGISTERED PASS:", "YES — adopt the filter inside the cell" if ok else "NO — trade the cell as is")
T.to_csv("data/studies/cw_on_certified_2026-09-22.csv", index=False)
