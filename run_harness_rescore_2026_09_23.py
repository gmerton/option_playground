#!/usr/bin/env python3
"""
[WL-2] re-score: the daily ledger rows nearest the bar, under the upgraded harness (paired edge t + label-permutation
p_search, 2,000 perms), with the SAME signal builders as the original scripts. Nothing else changes, so any verdict
movement is the scoring rule.

Rows: precision-tier breakout (house) CLOSE entry hold 60 -- the only daily row that ever passed (t 3.29, IN BOOK);
earnings drift good+MUTED (t 2.65, PARKED); house breakout inside HYB-A (t 2.84); and today's VCP N3 / Kell wedge pop
as known-NULL sanity rows. Each under control=post and control=xname. ledger=False: re-scoring is not a new test.

Run: AWS/MySQL env as usual; PYTHONPATH=src .venv/bin/python3 run_harness_rescore_2026_09_23.py
"""
from __future__ import annotations

import sys
import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from lib.studies.pattern_test import daily_signals, load_panel, run_daily

LOG = pt.REPO / "data/studies/logs/harness_rescore_2026-09-23.log"
OUT = pt.REPO / "data/studies/harness_rescore_2026-09-23.csv"


def main():
    import run_precision_tier_control as pc
    import run_ledger_rerun as lr
    import run_universe_test as ut
    import run_vcp_damped_sine as vcp
    import run_kell_wedge_pop as kw
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    P = load_panel()
    Pb, brk, prec = pc.build()
    jobs = [("precision-tier breakout (house), CLOSE entry, hold 60",
             lambda _P, m=prec: daily_signals(m, stop=Pb.low, side="long"), 60, Pb, "close", "t 3.29, edge +0.144, PASSED (IN BOOK)")]
    cells, _E = lr.earnings_patterns(P, raw)
    for n, f, h in cells:
        if n == "earnings drift, good+MUTED":
            jobs.append((n, f, h, P, "next_open", "t 2.65, PARKED"))
    raw_x = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    masks = ut.build_masks(Pb, raw_x)
    m = (brk & masks["HYB-A"]).copy(); m[m.index < ut.START] = False
    jobs.append(("house breakout in HYB-A", lambda _P, mm=m: daily_signals(mm, stop=Pb.low, side="long"), 60, Pb,
                 "close", "t 2.84 (stop_hold), not passed"))

    def vcp_pat(P_):
        hit, stop, _ = vcp.vcp_signals(P_, 3)
        return daily_signals(hit, stop=stop, side="long", since=vcp.START)
    jobs.append(("vcp damped sine N3", vcp_pat, vcp.HOLD, P, "close", "NULL today (edge -0.008)"))

    def kw_pat(P_):
        wp, _, bl = kw.masks(P_, **kw.BASE)
        floor = P_.close - 0.5 * P_.adr / 100 * P_.close
        return daily_signals(wp, stop=np.minimum(bl, floor), side="long", since=kw.START)
    jobs.append(("kell wedge pop", kw_pat, kw.CAP, P, "close", "NULL today (edge +0.004)"))

    rows = []
    for name, fn, hold, panel, entry_at, old in jobs:
        for ctrl in ("post", "xname"):
            print(f"\n\n{'=' * 100}\nRESCORE {name} | control {ctrl} | old: {old}\n{'=' * 100}", flush=True)
            tab = run_daily(f"RESCORE {name} [{ctrl}]", fn, hold=hold, panel=panel, entry_at=entry_at,
                            control=ctrl, ledger=False)
            best = tab.edge_t.idxmax()
            rows.append(dict(row=name, control=ctrl, old=old, best_arm=best, n=int(tab.loc[best, "n"]),
                             meanR=tab.loc[best, "meanR"], raw_t=tab.loc[best, "t"], legacy_edge=tab.loc[best, "edge"],
                             paired_edge=tab.loc[best, "p_edge"], edge_t=tab.loc[best, "edge_t"],
                             ema20_edge_t=tab.loc["ema20", "edge_t"], ema20_paired_edge=tab.loc["ema20", "p_edge"],
                             p_search=tab.attrs.get("p_search", np.nan)))
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print("\n\n" + pd.DataFrame(rows).round(4).to_string(index=False))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(pd.read_csv(OUT).round(4).to_string(index=False))
