#!/usr/bin/env python3
"""
UR "VWAP chop" study (2026-09-15: HOOD 09:47 fired on the ~6th crossing of a flat VWAP; IREN 09:47 fired after a
4-cent dip under a VWAP it had held since 09:32). For every scored UR alert, from the cached 1-min bars up to the
alert bar: the reclaim MARGIN (close over VWAP, ADR units), the DIP depth under VWAP in the 10 bars before the
reclaim (ADR), the consecutive bars BELOW VWAP right before the reclaim, and the number of VWAP CROSSINGS in the
prior 15 bars. R by bucket, curated / control x halves. Decides whether UR needs a decisiveness / chop gate.

Usage: PYTHONPATH=src python run_ur_chop_study.py
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
WL = Path("data/watchlist"); CACHE = Path("data/cache/intraday_1min")
pd.set_option("display.width", 230)
S = pd.read_csv(WL / "logs/alert_study_scores.csv"); S = S[(S.date >= "2026-02-02") & (S.date <= "2026-09-10") & (S.kind == "UR")].copy()
ctrl = {l.split("#")[0].strip().upper() for l in (WL / "universe_study_extra.txt").read_text().splitlines() if l.split("#")[0].strip()}
S["set"] = np.where(S.sym.isin(ctrl), "ctl", "cur"); days = sorted(S.date.unique()); half = set(days[:len(days) // 2]); S["half"] = np.where(S.date.isin(half), "A", "B")
ctx_cache: dict[str, pd.DataFrame] = {}
rows = []
for r in S.itertuples():
    p = CACHE / f"{r.sym}_{r.date}.parquet"
    if not p.exists(): continue
    if r.date not in ctx_cache:
        q = Path(f"data/cache/alert_ctx_v7_{r.date}.parquet"); ctx_cache[r.date] = pd.read_parquet(q).set_index("symbol") if q.exists() else pd.DataFrame()
    c = ctx_cache[r.date]
    if r.sym not in c.index: continue
    adr = float(c.loc[r.sym, "adr_pct"]) or 1.0
    b = pd.read_parquet(p)
    if b.empty or "vwap" not in b: continue
    vw = (b.vwap * b.volume).cumsum() / b.volume.cumsum()
    hm = b.index.strftime("%H:%M"); k = np.searchsorted(hm, r.t, side="right") - 1
    if k < 5: continue
    d = ((b.close - vw) / vw * 100 / adr).values
    margin = d[k]; prior = d[max(0, k - 10):k]; dip = prior.min() if len(prior) else np.nan
    below = 0
    for x in prior[::-1]:
        if x < 0: below += 1
        else: break
    seg = np.sign(d[max(0, k - 15):k + 1]); crosses = int((np.diff(seg) != 0).sum())
    rows.append(dict(date=r.date, t=r.t, sym=r.sym, R=r.R, stopped=r.stopped, set=r.set, half=r.half, margin=margin, dip=dip, below=below, crosses=crosses))
D = pd.DataFrame(rows); print(f"UR alerts with bars: {len(D)} of {len(S)}")
def cell(g): return pd.Series(dict(n=len(g), R=g.R.mean(), win=100 * (g.R > 0).mean(), stop=100 * g.stopped.mean(), curA=g[(g.set == "cur") & (g.half == "A")].R.mean(), curB=g[(g.set == "cur") & (g.half == "B")].R.mean(), ctlA=g[(g.set == "ctl") & (g.half == "A")].R.mean(), ctlB=g[(g.set == "ctl") & (g.half == "B")].R.mean()))
def show(title, by):
    t = D.groupby(by, observed=True).apply(cell, include_groups=False).round(2); t["all4pos"] = (t[["curA", "curB", "ctlA", "ctlB"]] > 0).all(axis=1); print(f"\n== {title} ==\n" + t.to_string())
D["margin_b"] = pd.cut(D.margin, [-9, 0.02, 0.05, 0.1, 0.2, 9], labels=["<=0.02", "0.02-0.05", "0.05-0.1", "0.1-0.2", ">0.2"])
D["dip_b"] = pd.cut(D.dip, [-99, -0.5, -0.25, -0.1, -0.03, 0], labels=["<-0.5", "-0.5..-0.25", "-0.25..-0.1", "-0.1..-0.03", ">-0.03"])
D["below_b"] = pd.cut(D.below, [-1, 0, 1, 3, 6, 99], labels=["0", "1", "2-3", "4-6", "7+"])
D["cross_b"] = pd.cut(D.crosses, [-1, 1, 2, 4, 6, 99], labels=["0-1", "2", "3-4", "5-6", "7+"])
show("reclaim margin over VWAP at the alert bar (ADR)", "margin_b")
show("depth of the dip under VWAP in the 10 bars before (ADR)", "dip_b")
show("consecutive bars under VWAP right before the reclaim", "below_b")
show("VWAP crossings in the prior 15 bars (chop)", "cross_b")
D["chop"] = (D.crosses >= 5) | (D.dip > -0.1); show("CHOP = 5+ crossings OR dip shallower than 0.1 ADR", "chop")
D.to_csv(WL / "logs/ur_chop_features.csv", index=False)
