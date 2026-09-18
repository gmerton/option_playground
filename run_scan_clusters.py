#!/usr/bin/env python3
"""
Industry cluster view of the nightly scan (2026-09-17). A LEAD-TIME / WATCHLIST tool, explicitly NOT an edge.

Why: `group_move_study_2026-09-17.md` -- a group's relative strength cannot be traded (74% of signals are false
starts, a managed trail nets zero), but a real multi-month move keeps putting its MEMBERS on the layer-2 list for
months. So count where the qualifying names are bunching up, and whether the bunch is growing. The individual
name still has to trigger; nothing here is a buy signal and nothing here should gate a candidate.

Per industry (yfinance industry, data/ticker_industry_map.csv), on the VOLUME universe (50-day ADDV >= $50M):
  lead   names in the LEADER state: 10 > 20 > 50 SMA stacked (with 0.25 ADR of slack: 10d > 20d x (1 - 0.25 ADR),
         lib.commons.ma_stack) and within 15% of the 52-week high. NO ADR gate:
         the 3% ADR cutoff sits at the median stock, so with it the counts and the trend column moved with market
         volatility (927 gated names on 2026-08-14 vs 704 on 09-17 on ADR compression alone) and quiet groups
         (insurers, utilities) were invisible. ADR stays where it was validated: the three tags below use the
         Adhikary scan's gate (ADR20 >= 3%, 52wk range >= 17%).
  prec   the validated precision cohort (gated, leader, ADR 4-7, stacked 5-40 days)
  setup  coiled within 5% under the 15-day pivot (contraction <= 0.6, dry-up <= 0.8) -- the buy-stop list
  brk    cleared the pivot today on RVOL >= 1.1, upper-half close
  lift   the industry's share of all leaders / its share of the volume universe (1.0 = no concentration)
  trend  leader count 21 / 10 / 5 sessions ago -> today; GROWING = up >= 2 names and >= 50% vs 21 sessions ago

A row prints when it has >= --min leaders and lift >= --lift, or it is GROWING. Sector roll-up first.
Usage: PYTHONPATH=src:. .venv/bin/python3 run_scan_clusters.py [--asof 2026-04-07] [--min 3] [--lift 1.5]
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd
from lib.commons.ma_stack import stack_run

REPO = Path(__file__).resolve().parent
PANEL, INDMAP, OUT = REPO / "data/cache/liquid_panel_2019.parquet", REPO / "data/ticker_industry_map.csv", REPO / "data/watchlist"
ADDV_MIN, ADR_MIN, RANGE52_MIN, PIVOT_N = 50e6, 3.0, 17.0, 15          # same gates as run_adhikary_scan.py
LOOKS = (21, 10, 5, 0)

ap = argparse.ArgumentParser(); ap.add_argument("--asof", default=None); ap.add_argument("--min", type=int, default=3)
ap.add_argument("--lift", type=float, default=1.5); ap.add_argument("--quiet", action="store_true"); a = ap.parse_args()

raw = pd.read_parquet(PANEL); raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]; raw["date"] = pd.to_datetime(raw.date)
if a.asof: raw = raw[raw.date <= pd.Timestamp(a.asof)]
raw = raw[raw.date >= raw.date.max() - pd.Timedelta(days=600)]
piv = lambda v: raw.pivot(index="date", columns="ticker", values=v).sort_index()
H, L, C, V = piv("high"), piv("low"), piv("close"), piv("volume")
uni = (C * V).tail(50).mean(); uni = uni[uni >= ADDV_MIN].index; H, L, C, V = H[uni], L[uni], C[uni].ffill(limit=1), V[uni].fillna(0)
s10, s20, s50 = C.rolling(10).mean(), C.rolling(20).mean(), C.rolling(50).mean()
adr = (H / L - 1).shift(1).rolling(20).mean() * 100
hi52, lo52 = H.shift(1).rolling(252, min_periods=120).max(), L.shift(1).rolling(252, min_periods=120).min()
pivot = H.shift(1).rolling(PIVOT_N).max(); avgv = V.shift(1).rolling(50).mean()
run = stack_run(C, adr=adr); stacked = run > 0       # 10>20>50 with with the house slack (0.25 ADR, lib.commons.ma_stack)
gate = (adr >= ADR_MIN) & ((hi52 - lo52) / C * 100 >= RANGE52_MIN) & pivot.notna()
lead = stacked & (C / hi52 - 1 > -0.15)                                             # volume universe, no ADR gate
prec = lead & gate & (adr >= 4) & (adr <= 7) & (run >= 5) & (run <= 40)
contr = (H.rolling(10).max() - L.rolling(10).min()) / (H.shift(10).rolling(20).max() - L.shift(10).rolling(20).min())
vsp = C / pivot - 1
setup = gate & stacked & (vsp >= -0.05) & (vsp <= 0) & (contr <= 0.6) & (V.shift(1).rolling(5).mean() / avgv <= 0.8)
brk = gate & (C >= pivot) & (V / avgv >= 1.1) & ((C - L) / (H - L).replace(0, np.nan) >= 0.5) & (run >= 5)

im = pd.read_csv(INDMAP).set_index("ticker"); ind = im.industry.reindex(uni).fillna("?"); sec = im.sector.reindex(uni).fillna("?")
d = C.index[-1]; idx = [C.index[-1 - k] for k in LOOKS]


def table(groups: pd.Series, label: str, min_n: int):
    g_gate = C.loc[d].notna().groupby(groups).sum(); tot_gate, tot_lead = C.loc[d].notna().sum(), lead.loc[d].sum()
    cnt = pd.DataFrame({f"t-{k}" if k else "lead": lead.loc[i].groupby(groups).sum() for k, i in zip(LOOKS, idx)})
    cnt["univ"] = g_gate; cnt["prec"] = prec.loc[d].groupby(groups).sum(); cnt["setup"] = setup.loc[d].groupby(groups).sum(); cnt["brk"] = brk.loc[d].groupby(groups).sum()
    cnt = cnt[cnt.univ > 0]
    cnt["lift"] = (cnt["lead"] / tot_lead) / (cnt["univ"] / tot_gate)
    cnt["growing"] = (cnt["lead"] - cnt["t-21"] >= 2) & (cnt["lead"] >= 1.5 * cnt["t-21"].clip(lower=1))
    show = cnt[((cnt["lead"] >= min_n) & (cnt["lift"] >= a.lift)) | (cnt["growing"] & (cnt["lead"] >= min_n))].copy()
    show["trend"] = show.apply(lambda r: f"{int(r['t-21'])}>{int(r['t-10'])}>{int(r['t-5'])}>{int(r['lead'])}" + ("  GROWING" if r["growing"] else ""), axis=1)
    show = show.sort_values(["growing", "lift"], ascending=False)
    print(f"\n--- {label}: {len(show)} clusters ---   (lead/univ = leaders of the group's names in the $50M-volume universe)")
    rows = []
    for g, r in show.iterrows():
        mem = lead.loc[d][groups == g]; mem = mem[mem].index
        tag = lambda t: t + ("*" if prec.loc[d, t] else "") + ("^" if setup.loc[d, t] else "") + ("!" if brk.loc[d, t] else "")
        names = " ".join(tag(t) for t in sorted(mem, key=lambda t: -(C.loc[d, t] / C.shift(21).loc[d, t])))
        print(f"  {g[:30]:<30} lead {int(r['lead']):2d}/{int(r['univ']):<3d} lift {r['lift']:4.1f}  prec {int(r['prec']):2d}  setup {int(r['setup']):2d}  brk {int(r['brk']):2d}   {r['trend']:<22} {names}")
        rows.append(dict(date=d.date(), level=label, group=g, lead=int(r["lead"]), univ=int(r["univ"]), lift=round(r["lift"], 2), prec=int(r["prec"]),
                         setup=int(r["setup"]), brk=int(r["brk"]), trend=r["trend"], members=names))
    return rows


print(f"=== SCAN CLUSTERS -- {d.date()} | {int(C.loc[d].notna().sum())} names with ADDV >= $50M, {int(lead.loc[d].sum())} in the leader state ({100*lead.loc[d].sum()/C.loc[d].notna().sum():.0f}%), "
      f"{int(prec.loc[d].sum())} precision, {int(setup.loc[d].sum())} setups, {int(brk.loc[d].sum())} breakouts (those three on the {int(gate.loc[d].sum())} ADR-gated names) ===")
print("where the qualifying names are bunching up. A watchlist pointer, NOT a signal: group strength has no edge (group_move_study); the name must still trigger.")
print("member tags: * precision cohort   ^ setup (buy-stop at the pivot)   ! broke out today      members sorted by 21-day return")
rows = table(sec, "SECTORS", max(a.min, 5)) + table(ind, "INDUSTRIES", a.min)
if not a.asof and rows:
    pd.DataFrame(rows).to_csv(OUT / f"clusters_{d.date()}.csv", index=False); pd.DataFrame(rows).to_csv(OUT / "clusters_latest.csv", index=False)
