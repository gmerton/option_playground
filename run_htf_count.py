#!/usr/bin/env python3
"""
[WL-5g] Soreide high tight flag -- POWER GATE ONLY (pre-registered in data/traderlion/setups/soreide_high_tight_flag.md
s7-8): count arm-A events before any return is computed. If n < ~300 or effective dates < ~150 -> UNDERPOWERED, stop,
and do NOT loosen rules 2, 4 or 5 after seeing the count. No returns are computed here.

Arm A (defaults, liquid panel, eligible, 2019-10 on; every window ends at t):
  p      = session of the highest high in the last 60 sessions (before t)
  pole   H_p / min(low[p-40 .. p]) - 1 >= 0.90
  pole quality: no 10-session window inside the pole with high-low span <= 3 ADR
  flag   10-25 sessions since p; depth 1 - min(low[p+1 .. t-1]) / H_p <= 0.25
  volume mean volume over the flag <= 0.6x mean volume over the pole
  price  close >= $10
  trigger first close > H_p with RVOL (volume / 50d mean) >= 1.5; one signal per name per pole
Also reported (information only, not a test): the same count on liquid_panel_2009 for 2010-01 -> 2019-09.

Run: PYTHONPATH=src .venv/bin/python3 run_htf_count.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from lib.studies.pattern_test import load_panel


def count(path: str, start: str, end: str) -> pd.DataFrame:
    P = load_panel(path)
    raw = pd.read_parquet(path)
    V = raw.pivot(index="date", columns="ticker", values="volume").sort_index().reindex(index=P.close.index,
                                                                                         columns=P.close.columns)
    C, H, L = P.close.values, P.high.values, P.low.values
    Vv = V.values
    adrp = (P.adr / 100 * P.close).values
    vm50 = V.shift(1).rolling(50).mean().values
    elig = P.elig.fillna(False).values
    idx = P.close.index
    lo, hi = idx.searchsorted(pd.Timestamp(start)), idx.searchsorted(pd.Timestamp(end), side="right")
    rows = []
    for j in range(C.shape[1]):
        used_p = set()
        for t in range(max(lo, 110), hi):
            if not elig[t, j] or not np.isfinite(C[t, j]) or C[t, j] < 10:
                continue
            w = H[t - 60:t, j]
            if not np.isfinite(w).any():
                continue
            p = t - 60 + int(np.nanargmax(w))
            Hp = H[p, j]
            fl = t - p
            if not (10 <= fl <= 25) or not (C[t, j] > Hp) or p in used_p:
                continue
            if C[t - 1, j] > Hp:                       # first close above the pole top only
                continue
            base_lo = np.nanmin(L[p - 40:p + 1, j])
            if not (np.isfinite(base_lo) and Hp / base_lo - 1 >= 0.90):
                continue
            if 1 - np.nanmin(L[p + 1:t, j]) / Hp > 0.25:
                continue
            # pole quality: no 10-session sub-base inside the pole (from the pole low to p)
            pl = p - 40 + int(np.nanargmin(L[p - 40:p + 1, j]))
            sub = False
            for s in range(pl, p - 9):
                if np.nanmax(H[s:s + 10, j]) - np.nanmin(L[s:s + 10, j]) <= 3 * adrp[s + 9, j]:
                    sub = True; break
            if sub:
                continue
            fv, pv = np.nanmean(Vv[p + 1:t, j]), np.nanmean(Vv[pl:p + 1, j])
            if not (np.isfinite(fv) and np.isfinite(pv) and pv > 0 and fv <= 0.6 * pv):
                continue
            if not (np.isfinite(vm50[t, j]) and vm50[t, j] > 0 and Vv[t, j] / vm50[t, j] >= 1.5):
                continue
            used_p.add(p)
            rows.append(dict(date=idx[t], sym=P.close.columns[j], pole=Hp / base_lo - 1, flag_len=fl))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    A = count("data/cache/liquid_panel_2019.parquet", "2019-10-01", "2026-12-31")
    print(f"ARM A (pre-registered window, liquid_panel_2019, 2019-10 ->): n {len(A)}, names "
          f"{A.sym.nunique() if len(A) else 0}, effective dates {A.date.nunique() if len(A) else 0}")
    if len(A):
        print(A.groupby(A.date.dt.year).size().to_string())
    B = count("data/cache/liquid_panel_2009.parquet", "2010-01-01", "2019-09-30")
    print(f"\n(information only) liquid_panel_2009, 2010-01 -> 2019-09: n {len(B)}, dates {B.date.nunique() if len(B) else 0}")
    gate = len(A) >= 300 and (A.date.nunique() if len(A) else 0) >= 150
    print(f"\nPOWER GATE (n >= 300 and dates >= 150): {'PASS -> run the test' if gate else 'FAIL -> UNDERPOWERED, stop'}")
    A.to_csv("data/studies/logs/htf_count_events.csv", index=False)
