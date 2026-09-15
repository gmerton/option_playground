#!/usr/bin/env python3
"""
Step 3/3 of the CALENDAR path study (2026-09-15): tables from results.parquet -> stdout + data/studies/calendar_path_study.md.
ROC = P&L / entry cost (after costs), per trade. Halves = entries 2018-11..2022-06 vs 2022-07..2026-07. Paired deltas vs hold.
Usage: PYTHONPATH=src python run_calendar_path_report.py [results.parquet]
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
pd.set_option("display.width", 240); pd.set_option("display.max_rows", 300)
R = pd.read_parquet(sys.argv[1] if len(sys.argv) > 1 else "data/cache/calendar_path/results.parquet")
R["entry"] = pd.to_datetime(R.entry); R["year"] = R.entry.dt.year; R["half"] = np.where(R.entry < "2022-07-01", "A", "B")
V = [c for c in ("hold", "pt25", "pt50", "pt75", "stop40", "stop60", "recenter1s", "recenter2s", "inversion") if c in R.columns]
for v in V: R[f"roc_{v}"] = 100 * R[v] / R.cost
R["fvf_b"] = pd.cut(R.fvf, [0, 0.8, 0.9, 1.0, 1.1, 9], labels=["<=0.8", "0.8-0.9", "0.9-1.0", "1.0-1.1", ">1.1"])
R["ivp_b"] = pd.cut(R.ivp, [-1, 30, 60, 80, 101], labels=["<=30", "30-60", "60-80", ">80"])
R["regime"] = np.where(R.spy_up == 1, "Bull", "Bear") + np.where(R.vix >= 20, "_HiVIX", "_LoVIX")
R["ba_b"] = pd.cut(R.ba_pct, [-1, 10, 25, 50, 1e9], labels=["<=10%", "10-25%", "25-50%", ">50%"])
L = []
def t(df, col): x = df[col].dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan
def block(title, df, by=None):
    rows = []
    groups = [("all", df)] if by is None else list(df.groupby(by, observed=True))
    for k, g in groups:
        for v in V:
            c = f"roc_{v}"; d = g[c] - g["roc_hold"]
            rows.append(dict(group=str(k), variant=v, n=len(g), roc=g[c].mean(), med=g[c].median(), win=100 * (g[c] > 0).mean(), t=t(g, c),
                             A=g[g.half == "A"][c].mean(), B=g[g.half == "B"][c].mean(), d_vs_hold=d.mean(), t_paired=(d.mean() / d.std() * np.sqrt(len(d)) if d.std() > 0 else np.nan)))
    tb = pd.DataFrame(rows).round(2); s = f"\n== {title} ==\n" + tb.to_string(index=False); print(s); L.append(f"### {title}\n\n```\n{tb.to_string(index=False)}\n```\n")
L.append(f"# Calendar path study (single put calendars)\n\n*{pd.Timestamp.today().date()}. `run_calendar_path_{{pull,sim,report}}.py`. {len(R):,} calendars on {R.ticker.nunique()} ETFs, Friday entries {R.entry.min().date()} -> {R.entry.max().date()}, real daily bid/ask (options_daily_v3), house cost model (mid +/- 25% BA + $0.0065/sh/leg). ROC = P&L / entry cost. Halves split at 2022-07-01. `d_vs_hold` = paired mean difference vs holding to the short expiry.*\n")
print(f"{len(R):,} calendars | tickers {sorted(R.ticker.unique())} | structs {R.struct.value_counts().to_dict()} | median debit {R.debit.median():.2f} cost {R.cost.median():.2f} BA% {R.ba_pct.median():.0f}")
for s_, g in R.groupby("struct"):
    block(f"{s_} structure, all names: variants", g)
    block(f"{s_}: hold by ticker", g[g.columns], "ticker") if False else None
    tb = g.groupby("ticker").agg(n=("roc_hold", "size"), hold=("roc_hold", "mean"), pt50=("roc_pt50", "mean"), win_hold=("roc_hold", lambda x: 100 * (x > 0).mean()), debit=("debit", "median"), ba_pct=("ba_pct", "median"), gap=("gap", "median")).round(2)
    print(f"\n== {s_}: by ticker ==\n" + tb.to_string()); L.append(f"### {s_}: by ticker\n\n```\n{tb.to_string()}\n```\n")
    for gate in ("fvf_b", "ivp_b", "regime", "ba_b"):
        tb = g.groupby(gate, observed=True).agg(n=("roc_hold", "size"), hold=("roc_hold", "mean"), hold_med=("roc_hold", "median"), win=("roc_hold", lambda x: 100 * (x > 0).mean()), pt50=("roc_pt50", "mean"), A=("roc_hold", lambda x: x[g.loc[x.index, "half"] == "A"].mean()), B=("roc_hold", lambda x: x[g.loc[x.index, "half"] == "B"].mean())).round(2)
        print(f"\n== {s_}: hold / pt50 by {gate} ==\n" + tb.to_string()); L.append(f"### {s_}: by {gate}\n\n```\n{tb.to_string()}\n```\n")
    tb = g.groupby("year").agg(n=("roc_hold", "size"), hold=("roc_hold", "mean"), pt50=("roc_pt50", "mean"), win=("roc_hold", lambda x: 100 * (x > 0).mean())).round(2)
    print(f"\n== {s_}: by year ==\n" + tb.to_string()); L.append(f"### {s_}: by year\n\n```\n{tb.to_string()}\n```\n")
    gg = g[(g.fvf <= 0.9)]
    if len(gg) > 30: block(f"{s_}: FVF <= 0.90 gate (the playbook gate): variants", gg)
open("data/studies/calendar_path_study.md", "w").write("\n".join(x for x in L if x)); print("\nwrote data/studies/calendar_path_study.md")
