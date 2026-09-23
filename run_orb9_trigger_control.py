#!/usr/bin/env python3
"""
Does the ORB9 TRIGGER add anything, or is it just being long a curated name that day?
(pre-registered 2026-09-23, before the run)

WHY THE EXISTING CONTROL IS THE WRONG ONE. `run_orb9_stop_floor_study.py` splits alerts by NAME --
curated watchlist vs the 39 extra names in `universe_study_extra.txt`. On the 0.6-ADR floor that gives
curated +0.352%/trade (t 4.21) against control +0.151% (n=371, t 1.29), an edge of +0.20pp at t 1.40.
Two problems: the control is far too small to resolve anything, and more importantly it varies the
NAMES, not the TRIGGER. It answers "is my watchlist better than other names", which we already believe.

THE QUESTION THAT MATTERS: on the same name, on the same day, does entering at the ORB9 trigger beat
entering at an arbitrary moment? If it does not, ORB9 is a clock, not a signal -- and the honest framing
is that the curated names drifted up and the trigger merely picked a minute.

ARMS (all on the same name-days, identical stop and exit -- only the ENTRY MINUTE differs):
  SIGNAL   enter at the ORB9 trigger bar's close
  POST     enter at a RANDOM minute drawn from the trigger's own eligible window (09:45-12:00), same day,
           same name. This is the direct test of the trigger.
  XNAME    enter at the same minute as the signal, but on a RANDOM OTHER curated name that also has bars
           that day. Tests whether the MINUTE carried information across the book (a market-wide move).
  Every arm: stop 0.6 ADR under the entry (the live floor), else mark out at the session close.
  3 control draws per alert, averaged, so a single unlucky minute cannot decide a cell.

⚠ MEASURED IN PERCENT, NOT R. Established earlier today: R = return / risk, so any comparison whose arms
carry different stop distances is partly a denominator artefact. Here the stop is a fixed 0.6 ADR in every
arm, so R and % agree -- but % is reported because it is what survives contact with costs.

PRE-REGISTERED PASS: SIGNAL minus POST > 0, date-clustered |t| >= 3, both halves of the date range the
same sign. Anything less and ORB9 does not beat a random minute in its own window.

PRIOR: no edge (~75%). Stage A already found every intraday arm -0.10 to -0.13R and indistinguishable
from a random later minute, and the alert-funnel test found alerts add nothing beyond the daily state.
The likely outcome is SIGNAL ~= POST, both positive, with the positive coming from the curated names'
intraday drift rather than from the trigger. If so the correct conclusion is NOT "ORB9 works" but
"the names work, and ORB9 is execution timing".

Usage: PYTHONPATH=src .venv/bin/python3 -u run_orb9_trigger_control.py
"""
from __future__ import annotations

import os
import warnings
from functools import lru_cache
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)

BARS = "data/cache/intraday_1min"
FLOOR_ADR = 0.60
WIN = {"ORB9": ("09:45", "12:00"), "UR": ("09:40", "15:00")}   # each trigger's own eligible window
N_DRAWS = 3
SEED = 20260923


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


def trade(m: pd.DataFrame, t: str, adr_px: float) -> float | None:
    """Enter at the close of bar `t`, stop 0.6 ADR under, else mark out at the session close. Returns %."""
    hm = m.index.strftime("%H:%M")
    at = m[hm == t]
    if at.empty:
        return None
    entry = float(at.close.iloc[0])
    seg = m[hm > t]
    if seg.empty or entry <= 0:
        return None
    stop = entry - FLOOR_ADR * adr_px
    hit = (seg.low <= stop).any()
    exit_px = stop if hit else float(seg.close.iloc[-1])
    return (exit_px / entry - 1) * 100


def main() -> None:
    rng = np.random.default_rng(SEED)
    d = pd.read_csv("data/watchlist/logs/alert_study_scores.csv")
    control_names = {l.split()[0] for l in open("data/watchlist/universe_study_extra.txt")
                     if l.strip() and not l.startswith("#")}
    KIND = os.environ.get("KIND", "ORB9")
    WIN_LO, WIN_HI = WIN[KIND]
    a = d[(d.kind == KIND) & d.R.notna()].drop_duplicates(["date", "t", "sym"])
    a = a[~a.sym.isin(control_names)]                      # curated watchlist only
    print(f"curated {KIND} alerts: {len(a):,} over {a.date.nunique()} dates, {a.sym.nunique()} names")

    # pool of curated names with bars, per date, for the xname arm
    by_date: dict[str, list[str]] = {}
    for dt, g in a.groupby("date"):
        by_date[dt] = sorted(g.sym.unique())

    rows, skipped = [], 0
    for r in a.itertuples():
        c = ctx(r.date)
        m = bars(r.sym, r.date)
        if c is None or m is None or r.sym not in c.index:
            skipped += 1; continue
        adr = c.loc[r.sym, "adr_pct"]
        if not adr or adr != adr:
            skipped += 1; continue
        adr_px = r.px * adr / 100.0
        sig = trade(m, r.t, adr_px)
        if sig is None:
            skipped += 1; continue

        hm = m.index.strftime("%H:%M")
        pool = sorted(set(hm[(hm >= WIN_LO) & (hm < WIN_HI)]) - {r.t})
        post = []
        for _ in range(N_DRAWS):
            if not pool:
                break
            v = trade(m, str(rng.choice(pool)), adr_px)
            if v is not None:
                post.append(v)

        xn = []
        peers = [s for s in by_date.get(r.date, []) if s != r.sym]
        for _ in range(N_DRAWS):
            if not peers:
                break
            p = str(rng.choice(peers))
            mp = bars(p, r.date)
            if mp is None or p not in c.index:
                continue
            ap = c.loc[p, "adr_pct"]
            if not ap or ap != ap:
                continue
            px0 = mp[mp.index.strftime("%H:%M") == r.t]
            if px0.empty:
                continue
            v = trade(mp, r.t, float(px0.close.iloc[0]) * ap / 100.0)
            if v is not None:
                xn.append(v)

        rows.append(dict(date=r.date, sym=r.sym, t=r.t, signal=sig,
                         post=np.mean(post) if post else np.nan,
                         xname=np.mean(xn) if xn else np.nan))
    X = pd.DataFrame(rows)
    X.to_csv(f"data/studies/{KIND.lower()}_trigger_control_2026-09-23.csv", index=False)
    print(f"scored {len(X):,}, skipped {skipped:,}\n")

    days = sorted(X.date.unique()); A = set(days[:len(days) // 2])
    def clustered_t(s: pd.Series, dates: pd.Series) -> float:
        md = s.groupby(dates).mean().dropna()
        return float(md.mean() / (md.std(ddof=1) / sqrt(len(md)))) if len(md) > 2 else np.nan

    print(f"{'='*104}\n{KIND} trigger vs a random minute in its OWN window — curated names, 0.6 ADR stop\n{'='*104}")
    for lbl, g in [("FULL", X), ("half A", X[X.date.isin(A)]), ("half B", X[~X.date.isin(A)])]:
        sub = g.dropna(subset=["signal", "post"])
        if len(sub) < 30:
            continue
        d_post = sub.signal - sub.post
        print(f"\n  {lbl}  n={len(sub):,}")
        print(f"    SIGNAL {sub.signal.mean():+.3f}%   POST(random minute) {sub.post.mean():+.3f}%   "
              f"EDGE {d_post.mean():+.3f}pp   date-clustered t {clustered_t(d_post, sub.date):+.2f}")
        sx = g.dropna(subset=["signal", "xname"])
        if len(sx) >= 30:
            d_x = sx.signal - sx.xname
            print(f"    XNAME(other curated name, same minute) {sx.xname.mean():+.3f}%   "
                  f"EDGE {d_x.mean():+.3f}pp   t {clustered_t(d_x, sx.date):+.2f}")

    sub = X.dropna(subset=["signal", "post"])
    d_post = sub.signal - sub.post
    ha = X[X.date.isin(A)].dropna(subset=["signal", "post"])
    hb = X[~X.date.isin(A)].dropna(subset=["signal", "post"])
    t = clustered_t(d_post, sub.date)
    agree = np.sign((ha.signal - ha.post).mean()) == np.sign((hb.signal - hb.post).mean())
    passed = bool(d_post.mean() > 0 and abs(t) >= 3 and agree)
    print(f"\n  halves agree: {agree}")
    print(f"  PRE-REGISTERED PASS: {'YES' if passed else 'NO'}")
    print(f"\nwrote data/studies/{KIND.lower()}_trigger_control_2026-09-23.csv")


if __name__ == "__main__":
    main()
