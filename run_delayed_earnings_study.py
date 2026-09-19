#!/usr/bin/env python3
"""
Tito's "good earnings, delayed bump": the report lands well but the stock does not run that day; the move
comes later.

Pre-registered (no EPS-surprise data in the repo, so "good" is proxied by the tape's reaction):
  reaction day r  the session in [report, report+1] with the larger |return| (AMC/BMO timing is unknown)
  GOOD            reaction return > 0, volume >= 1.5x its 50-day average, close in the upper half of the bar
  MUTED           reaction return <= +4%   |   BIG: > +4%
  entry variants
    A  drift_now     buy the close of r+1, hold -- does the drift exist without any trigger?
    B  delayed_break buy when price first closes above the reaction-day HIGH, 3-20 sessions later
                     (the "delayed bump" as a trigger), stop = entry-day low
  arms/control/splits/ledger all from lib.studies.pattern_test (same-name random control, same month)
  universe        panel names with earnings coverage (241 of 1,743)

Usage: PYTHONPATH=src .venv/bin/python3 run_delayed_earnings_study.py > data/studies/delayed_earnings_2026-09-18.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
from lib.mysql_lib import _get_engine
from lib.studies.pattern_test import load_panel, daily_signals, run_daily
warnings.filterwarnings("ignore"); pd.set_option("display.width", 200)

P = load_panel()
raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
V = raw.pivot(index="date", columns="ticker", values="volume").sort_index()
C, H, L = P.close, P.high, P.low
ret = C.pct_change(fill_method=None)
vrel = V / V.shift(1).rolling(50).mean()
uphalf = (C - L) / (H - L).replace(0, np.nan) >= 0.5
idx, cols = C.index, list(C.columns)
colpos = {c: k for k, c in enumerate(cols)}

E = pd.read_sql("SELECT ticker, raw_date FROM earnings_report", _get_engine())
E["raw_date"] = pd.to_datetime(E.raw_date)
E = E[(E.raw_date >= idx[0]) & (E.raw_date <= idx[-1]) & E.ticker.isin(colpos)]

react = []                                   # (i, j, muted, good)
for r in E.itertuples(index=False):
    j = colpos[r.ticker]
    i0 = idx.searchsorted(r.raw_date)
    if i0 + 2 >= len(idx):
        continue
    cand = [i0, i0 + 1]
    rr = [ret.values[i, j] for i in cand]
    if not np.isfinite(rr).any():
        continue
    i = cand[int(np.nanargmax(np.abs(rr)))]
    rv = ret.values[i, j]
    good = (rv > 0) and (vrel.values[i, j] >= 1.5) and bool(uphalf.values[i, j])
    react.append((i, j, bool(good), bool(rv <= 0.04), float(rv)))
R = pd.DataFrame(react, columns=["i", "j", "good", "muted", "rx"])
print(f"{len(R):,} earnings reactions on {R.j.nunique()} names | good {R.good.mean():.0%} | "
      f"of the good ones, muted {R[R.good].muted.mean():.0%}")

def mask_from(rows) -> pd.DataFrame:
    m = pd.DataFrame(False, index=idx, columns=cols)
    for i, j in rows:
        m.iat[i, j] = True
    return m

# --- A: no trigger, buy the close of r+1
for lab, sub in (("good+MUTED", R[R.good & R.muted]), ("good+BIG", R[R.good & ~R.muted]),
                 ("bad reaction", R[~R.good])):
    rows = [(int(x.i) + 1, int(x.j)) for x in sub.itertuples() if int(x.i) + 1 < len(idx)]
    hit = mask_from(rows)
    stop = L.shift(1).rolling(3).min()        # 3-session low as the stop for a no-trigger entry
    run_daily(f"earnings drift, {lab}", lambda Pp, h=hit, s=stop: daily_signals(h, stop=s, side="long"),
              hold=10, note="buy the close after the earnings reaction, no price trigger", panel=P)

# --- B: the delayed bump -- first close above the reaction-day high, 3-20 sessions later
for lab, sub in (("good+MUTED", R[R.good & R.muted]), ("good+BIG", R[R.good & ~R.muted])):
    rows = []
    for x in sub.itertuples():
        i, j = int(x.i), int(x.j)
        hi = H.values[i, j]
        for k in range(i + 3, min(i + 21, len(idx) - 1)):
            c = C.values[k, j]
            if np.isfinite(c) and c > hi:
                rows.append((k, j)); break
    hit = mask_from(rows)
    print(f"\n[{lab}] delayed breaks: {len(rows):,} of {len(sub):,} reactions "
          f"({100*len(rows)/max(len(sub),1):.0f}% eventually cleared the reaction high in 3-20 sessions)")
    run_daily(f"delayed bump after {lab} earnings", lambda Pp, h=hit: daily_signals(h, stop=L, side="long"),
              hold=10, note="first close above the reaction-day high, 3-20 sessions after a good report", panel=P)
