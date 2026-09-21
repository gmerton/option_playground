#!/usr/bin/env python3
"""
Post-earnings announcement drift, on the ACTUAL surprise.

The 2026-09-18 drift study produced the closest thing to a pass in a 50-pattern ledger --
"earnings drift, good+MUTED", +0.272R, edge +0.246, t 2.652, both halves positive, failing only
|t| >= 3. It flagged three limitations, all now fixed by the yfinance calendar pull:

  coverage  241 of 1,743 panel names  ->  457
  "good"    proxied by the TAPE'S REACTION (price up, volume up, upper-half close), which conflates
            drift with momentum  ->  the ACTUAL EPS surprise
  timing    AMC/BMO unknown, so the reaction day was guessed as whichever of [report, report+1] moved
            more  ->  the report hour is known, so BMO reacts same session and AMC the next

Construction is otherwise identical to the old study so the rows are comparable: entry at the close
AFTER the reaction day, 3-session-low stop, hold 10, harness controls (post + xname).

Real PEAD is defined on the surprise, not the reaction. If the old row was momentum wearing an
earnings costume, splitting on surprise should weaken it; if it is drift, it should sharpen.

Usage: PYTHONPATH=src .venv/bin/python3 run_pead_study.py > data/studies/pead_2026-09-20.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); pd.set_option("display.width", 210)
from lib.studies.pattern_test import load_panel, daily_signals, run_daily

P = load_panel()
C, L = P.close, P.low
idx, cols = C.index, list(C.columns)
colpos = {t: k for k, t in enumerate(cols)}
ret = C.pct_change(fill_method=None)

E = pd.read_parquet("data/cache/earnings_yf.parquet")
E["session"] = pd.to_datetime(E.session)
E = E[E.ticker.isin(colpos) & E.session.between(idx[0], idx[-1]) & E.surprise_pct.notna()]

rows = []
for r in E.itertuples(index=False):
    j = colpos[r.ticker]
    i0 = idx.searchsorted(r.session)
    # known timing: a BMO report is reacted to in the SAME session, an AMC report the NEXT one
    i = i0 if r.timing == "BMO" else i0 + 1
    if i + 2 >= len(idx) or not np.isfinite(ret.values[i, j]):
        continue
    rows.append((i, j, float(r.surprise_pct), float(ret.values[i, j])))
R = pd.DataFrame(rows, columns=["i", "j", "surp", "rx"])
print(f"{len(R):,} earnings events on {R.j.nunique()} names, {idx[0].date()} -> {idx[-1].date()}")
print(f"  surprise: p25 {R.surp.quantile(.25):+.1f}%  median {R.surp.median():+.1f}%  p75 {R.surp.quantile(.75):+.1f}%")
print(f"  reaction | surprise: beat>10% {R[R.surp>10].rx.mean()*100:+.2f}%  "
      f"inline {R[R.surp.between(-2,2)].rx.mean()*100:+.2f}%  miss<-10% {R[R.surp<-10].rx.mean()*100:+.2f}%")
print(f"  corr(surprise, reaction) = {R.surp.clip(-100,100).corr(R.rx):.3f}   "
      f"<- if ~0 the tape-reaction proxy was NOT measuring surprise\n")


def mask(sub):
    m = pd.DataFrame(False, index=idx, columns=cols)
    for x in sub.itertuples():
        k = int(x.i) + 1
        if k < len(idx):
            m.iat[k, int(x.j)] = True
    return m


stop = L.shift(1).rolling(3).min()            # identical to the 2026-09-18 study
BUCKETS = [
    ("surprise BEAT >10%",      R[R.surp > 10]),
    ("surprise beat 2-10%",     R[R.surp.between(2, 10)]),
    ("surprise INLINE -2..2%",  R[R.surp.between(-2, 2)]),
    ("surprise MISS <-10%",     R[R.surp < -10]),
    # the classic PEAD cut: big beat AND the tape did not already take it
    ("BEAT>10% + MUTED reaction (<=4%)", R[(R.surp > 10) & (R.rx <= 0.04)]),
    ("BEAT>10% + BIG reaction (>4%)",    R[(R.surp > 10) & (R.rx > 0.04)]),
]
for lab, sub in BUCKETS:
    if len(sub) < 120:
        print(f"-- {lab}: n {len(sub)} too thin, skipped"); continue
    h = mask(sub)
    run_daily(f"PEAD {lab}", lambda Pp, hh=h, s=stop: daily_signals(hh, stop=s, side="long"),
              hold=10, panel=P, ledger=False,
              note="actual EPS surprise + known AMC/BMO timing; entry the close after the reaction day")

# --- decomposition: the SAME events under the OLD tape-reaction definition -------------------
# If the reaction definition works on this wider data while the surprise definition does not, the
# 2026-09-18 near-pass was momentum that happens to sit near earnings -- not drift on the surprise.
raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
V = raw.pivot(index="date", columns="ticker", values="volume").reindex(index=idx, columns=cols)
vrel = V / V.rolling(50).mean()
uphalf = (C - P.low) / (P.high - P.low).replace(0, np.nan) > 0.5
R["good_tape"] = [(R.rx.iloc[k] > 0) and (vrel.values[int(R.i.iloc[k]), int(R.j.iloc[k])] >= 1.5)
                  and bool(uphalf.values[int(R.i.iloc[k]), int(R.j.iloc[k])]) for k in range(len(R))]
print(f"\n\n{'='*84}\nDECOMPOSITION — same events, OLD tape-reaction definition\n{'='*84}")
print(f"  good_tape: {R.good_tape.mean():.0%} of events | "
      f"mean surprise when good_tape {R[R.good_tape].surp.median():+.1f}% vs "
      f"{R[~R.good_tape].surp.median():+.1f}% otherwise")
for lab, sub in (("good_tape + MUTED (<=4%)", R[R.good_tape & (R.rx <= 0.04)]),
                 ("good_tape + BIG (>4%)",    R[R.good_tape & (R.rx > 0.04)])):
    if len(sub) < 120: continue
    h = mask(sub)
    run_daily(f"OLD-DEF {lab}", lambda Pp, hh=h, s=stop: daily_signals(hh, stop=s, side="long"),
              hold=10, panel=P, ledger=False, note="tape-reaction definition on the WIDER event set")
