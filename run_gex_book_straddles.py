#!/usr/bin/env python3
"""Book 7-DTE long straddles (arm 7, both gates) by SPY net GEX sign at the entry close (2026-09-21).
PRE-REGISTERED: data/studies/gex_book_straddles_2026-09-21.md. Usage:
  PYTHONPATH=src:. .venv/bin/python3 run_gex_book_straddles.py | tee data/studies/gex_book_straddles_2026-09-21.log"""
import numpy as np, pandas as pd
import run_gex_regime_pin as base

r = pd.read_parquet("data/cache/straddle_recenter/recenter_results.parquet")
r = r[(r.arm == 7) & (r.both)].copy(); r["entry_date"] = pd.to_datetime(r.entry_date)
bars = base.daily_bars("SPY"); _, net, _ = base.gex_series("SPY", bars)
n0 = len(r); r["gex"] = r.entry_date.map(net); r = r.dropna(subset=["gex", "hold"])
print(f"trades {n0:,}; with SPY GEX at entry {len(r):,} (dropped {n0 - len(r):,}); dates {r.entry_date.nunique():,} "
      f"{r.entry_date.min().date()} -> {r.entry_date.max().date()}")
r["NEG"] = r.gex < 0; r["ret"] = r.hold * 100
D = r.groupby("entry_date").agg(ret=("ret", "mean"), NEG=("NEG", "first"), n=("ret", "size"))
dates = np.sort(D.index.unique()); cut = dates[len(dates) // 2]
D["half"] = np.where(D.index < cut, "H1", "H2"); r["half"] = np.where(r.entry_date < cut, "H1", "H2")
def welch(a, b): return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))
def top1(x):
    s = x.sort_values(ascending=False); k = max(1, len(s) // 100)
    return 100 * s.head(k).sum() / s.sum() if s.sum() != 0 else np.nan
rows = []
for lab, g, gd in [("full", r, D), ("H1", r[r.half == "H1"], D[D.half == "H1"]), ("H2", r[r.half == "H2"], D[D.half == "H2"])]:
    for neg in (True, False):
        x = g[g.NEG == neg].ret; xd = gd[gd.NEG == neg].ret
        rows.append(dict(sample=lab, gamma="NEG" if neg else "POS", dates=len(xd), trades=len(x), date_mean=xd.mean(),
                         trade_mean=x.mean(), median=x.median(), win=100 * (x > 0).mean(), top1pct_share=top1(x)))
    a, b = gd[gd.NEG].ret, gd[~gd.NEG].ret
    rows.append(dict(sample=lab, gamma="NEG-POS", dates=len(gd), date_mean=a.mean() - b.mean(), trade_mean=welch(a, b)))
T = pd.DataFrame(rows)
print("\n(date_mean = mean of per-date means, %; for NEG-POS rows date_mean = difference, trade_mean column = Welch t across dates)")
print(T.round(2).to_string(index=False)); print(f"half cut: {pd.Timestamp(cut).date()}")
full = T[(T["sample"] == "full") & (T.gamma == "NEG-POS")].iloc[0]
hs = T[(T["sample"] != "full") & (T.gamma == "NEG-POS")]
ok = full.date_mean > 0 and abs(full.trade_mean) >= 3 and (hs.date_mean > 0).all()
print(f"\nPASS (NEG-POS > 0, |t| >= 3 across dates, > 0 both halves): {'YES' if ok else 'no'}")
T.to_csv("data/studies/gex_book_straddles_2026-09-21.csv", index=False)
