#!/usr/bin/env python3
"""
ADX(14) <= 12 gate on the house breakout -- HOLDOUT confirmation of the WL-3a exploratory lead (pre-registered
2026-09-23, before the 2009+ panel was opened).

THE LEAD (run_rmv_gate.py, 2019-10 -> 2026-09, exploratory cell, no verdict): house breakouts whose ADX(14) at t-1 was
<= 12 earned +1.48pp per trade vs same-date other-name breakouts, t 2.87, halves +0.68 / +2.15, 4.7% of breakouts.
It was found by looking at that data, so re-testing it there proves nothing.

HOLDOUT (PRIMARY): the same universe rebuilt from 2009 (run_build_liquid_panel.py --start 2009-01-01 ->
data/cache/liquid_panel_2009.parquet), window 2010-01-01 -> 2019-09-30 -- years the lead never saw.
Definitions IDENTICAL to the lead: house breakout = close > prior 20d high, ADR20 >= 3%, liquid-eligible, entered at the
CLOSE; stop = breakout day's low judged on the close; exit first close < EMA20, max 60 sessions, 0.10% a side;
metric % per trade; gate = Wilder ADX(14) at t-1 <= 12; control = same-date ungated breakouts in other names,
diff per date, t clustered by date.
Bar: t >= 3 on the holdout diff, both halves of the holdout (split 2015-01-01) positive, per-year shown.
  (A holdout confirmation of a lead that sat at t 2.87 in-sample: a positive holdout t of ~2 with both halves positive
  would be reported as SUPPORTED but not ADOPTED; t >= 3 = ADOPTED as a breakout-desk gate candidate.)
Secondary / descriptive: the same cell on the 2009 panel for 2019-10+ (panel-consistency check vs the original +1.48);
harness rows (paired rule) on the holdout vs post and xname; mechanism medians (ext, stop/ADR, ADR) gated vs ungated;
neighbourhood on the holdout: ADX <= 10 / 15, period 10 / 20 (report only).
Caveat: the universe is today's liquid names, so the holdout is survivorship-biased (names that became big). Both arms
share that bias, so the paired diff is what counts.

Run: PYTHONPATH=src .venv/bin/python3 run_adx_gate_holdout.py   (log -> data/studies/logs/adx_gate_holdout.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.pattern_test import daily_signals, load_panel, run_daily
import run_vcp_damped_sine as V
import run_rmv_gate as R

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/adx_gate_holdout.log"
PANEL = "data/cache/liquid_panel_2009.parquet"
HO_START, HO_END, HO_SPLIT = "2010-01-01", "2019-09-30", "2015-01-01"


def trades(P, start: str, end: str) -> pd.DataFrame:
    lvl = P.high.shift(1).rolling(20).max()
    hb = ((P.close > lvl) & (P.adr >= 3) & P.elig).fillna(False)
    hb[(hb.index < start) | (hb.index > end)] = False
    C, L = P.close.values, P.low.values
    adrpx = (P.adr / 100 * P.close).values
    rows = []
    for i, j in zip(*np.where(hb.values)):
        r = V.pct_trade(P, j, i, L[i, j], lvl.values[i, j])
        if r is None:
            continue
        rows.append(dict(i=i, j=j, date=hb.index[i], sym=hb.columns[j], ret=r[0], held=r[1],
                         ext=(C[i, j] - lvl.values[i, j]) / adrpx[i, j], stop_adr=(C[i, j] - L[i, j]) / adrpx[i, j],
                         adr=P.adr.values[i, j]))
    return pd.DataFrame(rows)


def cell(P, T, n=14, thr=12.0, split=HO_SPLIT):
    g = pd.Series(R.adx(P, n).shift(1).values[T.i.values, T.j.values] <= thr)
    R.SPLIT = split
    return g, R.date_matched(T, g)


def main():
    P = load_panel(PANEL)
    print(f"# ADX(14)<=12 gate -- HOLDOUT {HO_START} -> {HO_END} on {PANEL} ({P.close.shape[1]} names)")
    T = trades(P, HO_START, HO_END)
    print(f"holdout house breakouts {len(T):,} ({T.sym.nunique()} names), mean {T.ret.mean():+.2f}%")
    g, r = cell(P, T)
    print(f"gated share {g.mean():.1%}")
    print("\n## PRIMARY (holdout): gated vs same-date ungated other-name breakouts, % per trade")
    print(R.fmt(r))
    yr = r["_dd"].groupby(r["_dd"].index.year).agg(["size", "mean"]).round(2)
    print("per year:\n" + yr.T.to_string())
    h = R.date_matched(T, g, "held")
    print(f"held-the-level share: gated {100 * h['gated']:.1f}% vs ungated {100 * h['ungated']:.1f}% | "
          f"diff {100 * h['diff']:+.1f}pp t {h['t']:+.2f}")
    print("mechanism medians (gated=True):\n" + T.assign(g=g.values).groupby("g")[["ext", "stop_adr", "adr"]]
          .median().round(3).to_string())
    print("\n## neighbourhood on the holdout (report only)")
    for n, thr in ((14, 10), (14, 15), (10, 12), (20, 12)):
        gg, rr = cell(P, T, n, thr)
        print(f"  ADX({n}) <= {thr:<4} share {gg.mean():5.1%} | {R.fmt(rr)}")
    print("\n## secondary: same cell on this panel for 2019-10+ (consistency with the original +1.48 / t 2.87)")
    T2 = trades(P, "2019-10-01", "2026-12-31")
    g2, r2 = cell(P, T2, split="2023-01-01")
    print(f"  share {g2.mean():.1%} | {R.fmt(r2)}")
    print("\n\n# harness rows on the holdout (paired rule; close entry, day-low stop, hold 60)")
    gm = pd.DataFrame(False, index=P.close.index, columns=P.close.columns)
    gm.values[T.i.values[g.values], T.j.values[g.values]] = True

    def pattern(_P):
        return daily_signals(gm, stop=P.low, side="long", since=HO_START)
    run_daily("adx14<=12 gate on house breakout HOLDOUT 2010-2019", pattern, hold=60, entry_at="close",
              control="post", panel=P, split=HO_SPLIT,
              note="holdout confirmation of the WL-3a ADX lead; liquid_panel_2009, 2010-01 -> 2019-09")
    run_daily("adx14<=12 gate HOLDOUT xname", pattern, hold=60, entry_at="close", control="xname", panel=P,
              split=HO_SPLIT, ledger=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    txt = open(LOG).read()
    print(txt.split("# harness rows")[0])
    for ln in txt.splitlines():
        if "paired edge by half" in ln or "passes the bar" in ln or ln.startswith("===") or "paired edge by year" in ln:
            print(ln)
