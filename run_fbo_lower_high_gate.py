#!/usr/bin/env python3
"""
FBO short: does a LOWER-HIGH gate rescue the trigger? (pre-registered 2026-09-30, BEFORE running; TEST_INDEX §10
"FBO short lower-high gate"; source data/lance_breitstein/principles/muln-layup-anatomy.md -- Breitstein's day-2 MULN
short: drive above the level, fail, a LOWER HIGH, then break of the mini-support below VWAP; stop at the highs.)

CONTEXT. FBO was retired as a short entry on 2026-09-23 (alert_triggers_2026-09-23.md): −0.148%/trade, t −3.80,
worse than its control in both halves. The live detector already accepts EITHER a fail margin OR a swing lower high
(detectors.swing_lower_high), so the cached alerts mix both kinds. This splits them.

SAMPLE  curated-watchlist FBO alerts in data/watchlist/logs/alert_study_scores.csv (2026-02-02 -> 2026-09-10; the
        universe_study_extra.txt control names excluded), deduped on (date, t, sym) -- the 9/23 sample.
TAG     computed point-in-time from the cached 1-min bars, 09:30 through the alert bar only:
        LH   = detectors.swing_lower_high: after the session high, a trough, then a later bar whose high is >= trough
               low x (1 + 0.10 ADR) and still < the session high.          [the detector's own definition]
        LH+  = LH AND the alert bar's close < that trough low (the mini-support break in his words).
TRADE   short at the alert bar's close; stop = the emitted stop (above the failed high); exit at the stop if touched,
        else the session close. Measured in % (stop widths differ across alerts).
CONTROL POST: same name, same day, entry at a random minute in FBO's own window (09:50-15:00, != t), stop at the SAME %
        distance above entry as the signal's; 5 draws averaged. Holds name-day and stop width fixed, varies the minute.
PRIMARY LH alerts: SIGNAL - POST, date-clustered t. BAR |t| >= 3, both halves of the date range (median date split)
        the same sign. Two-sided (FBO overall was INVERTED).
SECONDARY (Sidak over 2 -> |t| >= 2.24): LH+ SIGNAL - POST; LH minus not-LH on SIGNAL (date-paired where both occur).
Prior: low (~80% no edge): Stage A, the alert funnel and FBO's own −3.80 all say intraday triggers ~ a random minute.

Run: PYTHONPATH=src .venv/bin/python3 run_fbo_lower_high_gate.py   (log -> data/studies/logs/fbo_lower_high_gate.log)
"""
from __future__ import annotations

import os
import sys
import warnings
from functools import lru_cache
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/fbo_lower_high_gate.log"
BARS = "data/cache/intraday_1min"
WIN_LO, WIN_HI = "09:50", "15:00"
N_DRAWS = 5
SEED = 20260930


@lru_cache(None)
def ctx(dt: str):
    f = f"data/cache/alert_ctx_v7_{dt}.parquet"
    return pd.read_parquet(f).set_index("symbol") if os.path.exists(f) else None


@lru_cache(None)
def bars(sym: str, dt: str):
    f = f"{BARS}/{sym}_{dt}.parquet"
    if not os.path.exists(f):
        return None
    m = pd.read_parquet(f)
    hm = m.index.strftime("%H:%M")
    m = m[(hm >= "09:30") & (hm < "16:00")]
    return m if len(m) else None


def lh_tags(m: pd.DataFrame, t: str, adr_pct: float, close_t: float) -> tuple[bool, bool]:
    hm = m.index.strftime("%H:%M")
    seen = m[hm <= t]
    if len(seen) < 3:
        return False, False
    hi_pos = int(np.argmax(seen.high.values))
    hi = seen.high.values[hi_pos]
    since = seen.iloc[hi_pos + 1:]
    if len(since) < 2:
        return False, False
    tr_pos = int(np.argmin(since.low.values))
    trough = since.low.values[tr_pos]
    after = since.iloc[tr_pos + 1:]
    need = trough * (1 + 0.10 * adr_pct / 100)
    lh = bool(((after.high >= need) & (after.high < hi)).any())
    # LH+ (fixed after the first run returned n = 0: the trough above includes the alert bar, so a close below it is
    # impossible). Mini-support = the low between the session high and a lower-high bar that printed BEFORE the alert
    # bar; LH+ = the alert close breaks that support.
    prior = since.iloc[:-1]
    lows, highs = prior.low.values, prior.high.values
    lhp = False
    for k in range(1, len(prior)):
        sup = lows[:k].min()
        if sup * (1 + 0.10 * adr_pct / 100) <= highs[k] < hi and close_t < sup:
            lhp = True
            break
    return lh, lhp


def short_trade(m: pd.DataFrame, t: str, stop_pct: float) -> float | None:
    hm = m.index.strftime("%H:%M")
    at = m[hm == t]
    if at.empty:
        return None
    entry = float(at.close.iloc[0])
    seg = m[hm > t]
    if seg.empty or entry <= 0:
        return None
    stop = entry * (1 + stop_pct / 100)
    hit = (seg.high >= stop).any()
    exit_px = stop if hit else float(seg.close.iloc[-1])
    return (1 - exit_px / entry) * 100


def ct(s: pd.Series, dates: pd.Series) -> float:
    md = s.groupby(dates).mean().dropna()
    return float(md.mean() / (md.std(ddof=1) / sqrt(len(md)))) if len(md) > 2 else np.nan


def main():
    rng = np.random.default_rng(SEED)
    d = pd.read_csv(REPO / "data/watchlist/logs/alert_study_scores.csv")
    control_names = {l.split()[0] for l in open(REPO / "data/watchlist/universe_study_extra.txt")
                     if l.strip() and not l.startswith("#")}
    a = d[(d.kind == "FBO") & d.R.notna()].drop_duplicates(["date", "t", "sym"])
    a = a[~a.sym.isin(control_names)]
    rows, skipped = [], 0
    for r in a.itertuples():
        c, m = ctx(r.date), bars(r.sym, r.date)
        if c is None or m is None or r.sym not in c.index:
            skipped += 1; continue
        adr = c.loc[r.sym, "adr_pct"]
        if not adr or adr != adr or not np.isfinite(r.stop) or r.stop <= r.px:
            skipped += 1; continue
        stop_pct = (r.stop / r.px - 1) * 100
        hm = m.index.strftime("%H:%M")
        at = m[hm == r.t]
        if at.empty:
            skipped += 1; continue
        lh, lhp = lh_tags(m, r.t, adr, float(at.close.iloc[0]))
        sig = short_trade(m, r.t, stop_pct)
        if sig is None:
            skipped += 1; continue
        pool = sorted(set(hm[(hm >= WIN_LO) & (hm < WIN_HI)]) - {r.t})
        post = [v for v in (short_trade(m, str(rng.choice(pool)), stop_pct) for _ in range(N_DRAWS)) if v is not None] \
            if pool else []
        rows.append(dict(date=r.date, sym=r.sym, t=r.t, LH=lh, LHp=lhp, stop_adr=stop_pct / adr,
                         signal=sig, post=np.mean(post) if post else np.nan))
    X = pd.DataFrame(rows).dropna(subset=["signal", "post"])
    X.to_csv(REPO / "data/studies/logs/fbo_lower_high_gate_alerts.csv", index=False)
    days = sorted(X.date.unique())
    A = set(days[:len(days) // 2])
    L = ["# FBO lower-high gate (pre-registration in the docstring)",
         f"curated FBO alerts scored {len(X):,} (skipped {skipped:,}) over {X.date.nunique()} dates, {X.sym.nunique()} names; "
         f"LH {100 * X.LH.mean():.0f}%, LH+ {100 * X.LHp.mean():.0f}%; median stop {X.stop_adr.median():.2f} ADR"]
    out = {}
    for lab, g in [("ALL FBO (reproduces 9/23)", X), ("PRIMARY  LH", X[X.LH]), ("not LH", X[~X.LH]),
                   ("LH+ (mini-support break)", X[X.LHp])]:
        dd = g.signal - g.post
        ha, hb = dd[g.date.isin(A)], dd[~g.date.isin(A)]
        out[lab] = (dd.mean(), ct(dd, g.date), ha.mean(), hb.mean(), len(g))
        L.append(f"  {lab:28s} n {len(g):5,}  SIGNAL {g.signal.mean():+.3f}%  POST {g.post.mean():+.3f}%  "
                 f"edge {dd.mean():+.3f}pp t {out[lab][1]:+.2f}  halves {ha.mean():+.3f} / {hb.mean():+.3f}  "
                 f"win {100 * (g.signal > 0).mean():.0f}%")
    # LH vs not-LH, date-paired
    p = X.groupby(["date", "LH"]).signal.mean().unstack().dropna()
    dl = p[True] - p[False]
    L.append(f"\n  LH minus not-LH (SIGNAL, date-paired, {len(dl)} dates): {dl.mean():+.3f}pp  "
             f"t {dl.mean() / dl.std(ddof=1) * sqrt(len(dl)):+.2f}")
    print("\n".join(L))
    m_, t_, a_, b_, n_ = out["PRIMARY  LH"]
    print(f"\nPRIMARY LH SIGNAL - POST: {m_:+.3f}pp t {t_:+.2f} halves {a_:+.3f}/{b_:+.3f} n {n_}")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
