#!/usr/bin/env python3
"""
Do VWAP-reclaim (UR) alerts work on gap-down days? Prompted by 2026-09-14: MRVL and TER fired UR at 09:41/09:43
after semis gapped down ~7%. Joins the scored replay alerts (logs/alert_study_scores.csv) with the session open
(data/cache/intraday_1min) and the prior close / ADR (data/cache/alert_ctx_v7_<date>.parquet) to get, per alert:
the NAME's gap (open vs prior close, % and ADR), its GROUP's mean gap (data/watchlist/universe_groups.csv), and
QQQ's gap. Then R by gap bucket x set (curated / control) x half, for UR and for all longs.

Usage: PYTHONPATH=src python run_gap_reclaim_study.py [--since 2026-02-02] [--until 2026-09-10]
"""
from __future__ import annotations
import argparse, glob
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).resolve().parent; CACHE = REPO / "data" / "cache"; WL = REPO / "data" / "watchlist"
pd.set_option("display.width", 230); pd.set_option("display.max_rows", 300)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--since", default="2026-02-02"); ap.add_argument("--until", default="2026-09-10"); a = ap.parse_args()
    S = pd.read_csv(WL / "logs" / "alert_study_scores.csv"); S = S[(S.date >= a.since) & (S.date <= a.until)].copy()
    ctrl = {l.split("#")[0].strip().upper() for l in (WL / "universe_study_extra.txt").read_text().splitlines() if l.split("#")[0].strip()}
    groups = {}
    for line in (WL / "universe_groups.csv").read_text().splitlines()[1:]:
        if "," in line: t, g = line.split(",", 1); groups[t.strip().upper()] = g.strip()
    # session opens + prior closes for every (date, sym) the alerts need, plus QQQ
    need = set(zip(S.date, S.sym)) | {(d, "QQQ") for d in S.date.unique()}
    for d in S.date.unique():
        for s in S[S.date == d].sym.unique():
            for peer, g in groups.items():
                if g == groups.get(s): need.add((d, peer))
    ctx = {}
    for d in sorted({d for d, _ in need}):
        p = CACHE / f"alert_ctx_v7_{d}.parquet"
        if p.exists():
            c = pd.read_parquet(p).set_index("symbol"); ctx[d] = c
    rows = []
    for d, s in need:
        p = CACHE / "intraday_1min" / f"{s}_{d}.parquet"
        c = ctx.get(d)
        if c is None or s not in c.index or not p.exists(): continue
        b = pd.read_parquet(p)
        if b.empty or "open" not in b: continue
        o = float(b.open.iloc[0]); pc = float(c.loc[s, "prev_close"]); adr = float(c.loc[s, "adr_pct"]) or np.nan
        rows.append(dict(date=d, sym=s, gap_pct=100 * (o / pc - 1), gap_adr=100 * (o / pc - 1) / adr))
    G = pd.DataFrame(rows)
    G["group"] = G.sym.map(groups)
    grp = G.dropna(subset=["group"]).groupby(["date", "group"]).gap_pct.agg(["mean", "size"]).rename(columns={"mean": "grp_gap", "size": "grp_n"}).reset_index()
    qqq = G[G.sym == "QQQ"][["date", "gap_pct"]].rename(columns={"gap_pct": "qqq_gap"})
    S = S.merge(G[["date", "sym", "gap_pct", "gap_adr"]], on=["date", "sym"], how="left")
    S["group"] = S.sym.map(groups); S = S.merge(grp, on=["date", "group"], how="left").merge(qqq, on="date", how="left")
    S["set"] = np.where(S.sym.isin(ctrl), "ctl", "cur"); S["side"] = np.where(S.kind.isin(["BIR", "FBO", "PARA"]), "short", "long")
    S["mins"] = S.t.str.slice(0, 2).astype(int) * 60 + S.t.str.slice(3, 5).astype(int)
    days = sorted(S.date.unique()); half = set(days[:len(days) // 2]); S["half"] = np.where(S.date.isin(half), "A", "B")
    print(f"{len(S)} alerts, gap known for {S.gap_pct.notna().sum()}, group gap for {S.grp_gap.notna().sum()}, QQQ gap for {S.qqq_gap.notna().sum()}")
    S["name_gap"] = pd.cut(S.gap_adr, [-99, -1.5, -1.0, -0.5, -0.15, 0.15, 0.5, 99], labels=["dn>1.5ADR", "dn1-1.5", "dn0.5-1", "dn0.15-0.5", "flat", "up0.15-0.5", "up>0.5"])
    S["grp_gapb"] = pd.cut(S.grp_gap, [-99, -4, -2, -1, -0.3, 0.3, 1, 99], labels=["grp<-4%", "-4..-2", "-2..-1", "-1..-0.3", "flat", "0.3..1", ">1"])
    S["qqq_gapb"] = pd.cut(S.qqq_gap, [-99, -1.5, -0.75, -0.25, 0.25, 0.75, 99], labels=["qqq<-1.5%", "-1.5..-0.75", "-0.75..-0.25", "flat", "0.25..0.75", ">0.75"])
    S["tb"] = np.where(S.mins <= 580, "09:30-40", np.where(S.mins <= 600, "09:41-10", np.where(S.mins < 720, "10-12", "pm")))

    def cell(g):
        return pd.Series(dict(n=len(g), R=g.R.mean(), win=100 * (g.R > 0).mean(), stop=100 * g.stopped.mean(), curA=g[(g.set == "cur") & (g.half == "A")].R.mean(),
                              curB=g[(g.set == "cur") & (g.half == "B")].R.mean(), ctlA=g[(g.set == "ctl") & (g.half == "A")].R.mean(), ctlB=g[(g.set == "ctl") & (g.half == "B")].R.mean()))

    def show(title, df, by):
        t = df.groupby(by, observed=True).apply(cell, include_groups=False).round(2); t["all4pos"] = (t[["curA", "curB", "ctlA", "ctlB"]] > 0).all(axis=1)
        print(f"\n== {title} ==\n" + t.to_string())
    U = S[S.kind == "UR"]
    show("UR by the NAME's gap (open vs prior close, ADR units)", U, "name_gap")
    show("UR by the GROUP's mean gap (%)", U, "grp_gapb")
    show("UR by QQQ's gap (%)", U, "qqq_gapb")
    show("UR, name gap-down >= 0.5 ADR, by time of the alert", U[U.gap_adr <= -0.5], "tb")
    show("UR, name gap-down >= 1 ADR, by time of the alert", U[U.gap_adr <= -1.0], "tb")
    show("UR, GROUP gap <= -2%, by time", U[U.grp_gap <= -2], "tb")
    show("UR, GROUP gap <= -2% AND name gap <= -1 ADR (the MRVL/TER case), by time", U[(U.grp_gap <= -2) & (U.gap_adr <= -1)], "tb")
    show("UR on gap-down >= 1 ADR: reclaim still below the daily 9 EMA vs above", U[U.gap_adr <= -1.0].assign(below9=U.tags.fillna("").str.contains("still below 9 EMA")), "below9")
    show("ALL longs by the name's gap", S[S.side == "long"], "name_gap")
    show("shorts by the name's gap", S[S.side == "short"], "name_gap")
    # the flush-and-reclaim on gap days: does the gap fill by the close? (R to close vs MFE)
    g = U[U.gap_adr <= -1.0]; print(f"\nUR on >=1 ADR gap-downs: n {len(g)}, mean R {g.R.mean():+.2f}, MFE mean {g.mfe_R.mean():.2f}, reached +1R {100*(g.mfe_R>=1).mean():.0f}%, stopped {100*g.stopped.mean():.0f}%")
    g = U[U.gap_adr > -0.15]; print(f"UR on non-gap days:         n {len(g)}, mean R {g.R.mean():+.2f}, MFE mean {g.mfe_R.mean():.2f}, reached +1R {100*(g.mfe_R>=1).mean():.0f}%, stopped {100*g.stopped.mean():.0f}%")


if __name__ == "__main__":
    main()
