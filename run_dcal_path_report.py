#!/usr/bin/env python3
"""Report for the DOUBLE-calendar path study (results_dcal.parquet) -> stdout + appended to data/studies/calendar_path_study.md."""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
pd.set_option("display.width", 240); pd.set_option("display.max_rows", 400)
R = pd.read_parquet(sys.argv[1] if len(sys.argv) > 1 else "data/cache/calendar_path/results_dcal.parquet")
TITLE = sys.argv[2] if len(sys.argv) > 2 else "IWM / SPY / QQQ"
R["entry"] = pd.to_datetime(R.entry); R["year"] = R.entry.dt.year; R["half"] = np.where(R.entry < "2022-07-01", "A", "B")
V = ["hold", "pt25", "pt50", "pt75", "stop40", "stop60", "recenter2s", "inversion", "drop_far", "close_far50"]
for v in V: R[f"roc_{v}"] = 100 * R[v] / R.cost
R["regime"] = np.where(R.spy_up == 1, "Bull", "Bear") + np.where(R.vix >= 20, "_HiVIX", "_LoVIX")
R["ba_b"] = pd.cut(R.ba_pct, [-1, 10, 25, 1e9], labels=["<=10%", "10-25%", ">25%"])
L = [f"\n## Double calendars ({pd.Timestamp.today().date()}): {TITLE}, {len(R):,} trades\n",
     "Put calendar below + call calendar above, same two expiries; strike sets by the short legs' delta: sym25 (0.25/0.25), sym35 (0.35/0.35 = the SPY playbook's Bullish_LowIV cell), asym35_10 (0.35P/0.10C = its Bearish_HighIV cell). Extra variants: drop_far (when the close crosses a short strike, close the far side, hold the tested side), close_far50 (close a side at half its entry debit). Costs on all four legs.\n"]
def t(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan
def tbl(title, df):
    rows = []
    for v in V:
        c = f"roc_{v}"; d = df[c] - df.roc_hold
        rows.append(dict(variant=v, n=len(df), roc=df[c].mean(), med=df[c].median(), win=100 * (df[c] > 0).mean(), t=t(df[c]), A=df[df.half == "A"][c].mean(), B=df[df.half == "B"][c].mean(), d_vs_hold=d.mean(), t_paired=t(d)))
    tb = pd.DataFrame(rows).round(2); print(f"\n== {title} ==\n" + tb.to_string(index=False)); L.append(f"### {title}\n\n```\n{tb.to_string(index=False)}\n```\n")
def agg(title, df, by):
    tb = df.groupby(by, observed=True).agg(n=("roc_hold", "size"), hold=("roc_hold", "mean"), med=("roc_hold", "median"), win=("roc_hold", lambda x: 100 * (x > 0).mean()), t=("roc_hold", t),
                                           A=("roc_hold", lambda x: x[df.loc[x.index, "half"] == "A"].mean()), B=("roc_hold", lambda x: x[df.loc[x.index, "half"] == "B"].mean()), debit=("debit", "median"), ba=("ba_pct", "median")).round(2)
    print(f"\n== {title} ==\n" + tb.to_string()); L.append(f"### {title}\n\n```\n{tb.to_string()}\n```\n")
if "earn_in_win" in R.columns:
    agg("HOLD by earnings-in-window x structure x strike set", R, ["earn_in_win", "struct", "dset"])
    R_all = R; R = R[~R.earn_in_win.astype(bool)]; L.append(f"_Tables below EXCLUDE entries with an earnings date inside (entry, long expiry] ({int(R_all.earn_in_win.sum())} of {len(R_all)})._\n")
agg("HOLD by ticker x structure x strike set", R, ["ticker", "struct", "dset"])
for (s_, ds), g in R.groupby(["struct", "dset"]):
    tbl(f"{s_} {ds}: variants, all three names", g)
for ds in ("sym35", "asym35_10", "sym25"):
    g = R[R.dset == ds]
    agg(f"{ds}: HOLD by regime (the SPY playbook cells) x structure", g, ["struct", "regime"])
agg("sym35: HOLD by entry bid-ask x structure", R[R.dset == "sym35"], ["struct", "ba_b"])
agg("sym35 DCAL: HOLD by year", R[(R.dset == "sym35") & (R.struct == "DCAL")], "year")
agg("sym35 ETF: HOLD by year", R[(R.dset == "sym35") & (R.struct == "ETF")], "year")
open("data/studies/calendar_path_study.md", "a").write("\n".join(L)); print("\nappended to data/studies/calendar_path_study.md")
