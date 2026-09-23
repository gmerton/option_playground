#!/usr/bin/env python3
"""
Does moving UR's VWAP reclaim band help? (pre-registered 2026-09-23, before the run)

THE LIVE RULE. `detectors.py`: UR arms when a 1-min close sits `UR_ARM_BAND = 0.0010` (0.10%) UNDER VWAP
and triggers when a close clears VWAP by `UR_TRIG_BAND = 0.0010` (0.10%). This sweeps the TRIGGER band
only; the undercut-then-reclaim structure is preserved exactly.

⚠ THIS IS NOT BLIND PARAMETER TUNING, and it is not being run in hope. Two findings from today frame it:
  1. The UR trigger does NOT beat a random minute in its own window (+0.033pp, t -0.31, halves disagree),
     and loses to a random OTHER curated name at the same minute (-0.121pp, t -4.55). So the prior on any
     band being a real edge is low.
  2. But there IS a directional hypothesis worth one test, and it is the book's most replicated finding:
     **we select well and enter badly** -- the daily breakout buys 2.6 ADR above a random later entry, the
     within-date extension work says extension is a TIMING variable, and ORB9 (which buys a break of the
     OR high, i.e. strength) just came in at -0.425pp vs a random minute, t -8.50. A SMALLER or NEGATIVE
     band enters CLOSER TO OR BELOW VWAP -- a lower price, less confirmation. If the extension finding
     generalises to the intraday reclaim, the lower bands should beat +0.0010.
  So the pre-registered directional expectation is monotone: return should DECREASE as the band widens.

METHOD. For each curated UR alert, the actual trigger minute anchors the search. The last bar before it
whose close sat under VWAP approximates the ARM. From that bar forward, band b fires at the first close
with `close / vwap - 1 >= b`. Every arm then trades identically: 0.5 ADR stop, else mark out at the
session close, measured in PERCENT (not R -- the stop is fixed, but % is what meets costs).
Bands: -0.0020, -0.0010, 0.0000, +0.0010 (LIVE), +0.0020, +0.0040.

CONTROL. Each band is also compared against the same POST control used in the trigger test -- a random
minute in UR's own window on the same name-day. **A band only matters if it beats that.** Reporting a
band's raw return alone would repeat the ORB9 mistake, where +0.352%/trade looked strong until the control
showed a random minute earned +0.775%.

PRE-REGISTERED PASS: some band beats the LIVE +0.0010 band with date-clustered |t| >= 3 on the paired
difference AND both halves the same sign AND that band also beats the POST control. 6 bands -> Sidak
|t| >= 2.64; the house 3.0 governs. A win at one isolated band with neighbours flat is a SPIKE, not a
plateau, and is reported as such rather than adopted.

PRIOR: ~20% that any band clears the bar. Most likely outcome is a monotone but small gradient -- lower
band, slightly better fill, no cell beating the control -- which would confirm the extension mechanism
without producing a tradeable rule.

Usage: PYTHONPATH=src .venv/bin/python3 -u run_ur_vwap_band_sweep.py
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
BANDS = [-0.0020, -0.0010, 0.0000, 0.0010, 0.0020, 0.0040]
LIVE = 0.0010
STOP_ADR = 0.50
WIN_LO, WIN_HI = "09:40", "15:00"
N_DRAWS, SEED = 3, 20260923


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
    return m if len(m) and "vwap" in m.columns else None


def run(m: pd.DataFrame, i: int, adr_px: float) -> float | None:
    """Enter at bar position i's close; 0.5 ADR stop; else out at the session close. Percent."""
    entry = float(m.close.iloc[i])
    if entry <= 0 or i + 1 >= len(m):
        return None
    seg = m.iloc[i + 1:]
    stop = entry - STOP_ADR * adr_px
    hit = (seg.low <= stop).any()
    return ((stop if hit else float(seg.close.iloc[-1])) / entry - 1) * 100


def main() -> None:
    rng = np.random.default_rng(SEED)
    d = pd.read_csv("data/watchlist/logs/alert_study_scores.csv")
    ctl = {l.split()[0] for l in open("data/watchlist/universe_study_extra.txt")
           if l.strip() and not l.startswith("#")}
    a = d[(d.kind == "UR") & d.R.notna()].drop_duplicates(["date", "t", "sym"])
    a = a[~a.sym.isin(ctl)]
    print(f"curated UR alerts: {len(a):,} over {a.date.nunique()} dates\n")

    rows, skipped = [], 0
    for r in a.itertuples():
        c, m = ctx(r.date), bars(r.sym, r.date)
        if c is None or m is None or r.sym not in c.index:
            skipped += 1; continue
        adr = c.loc[r.sym, "adr_pct"]
        if not adr or adr != adr:
            skipped += 1; continue
        adr_px = r.px * adr / 100.0
        hm = m.index.strftime("%H:%M")
        tpos = np.nonzero(hm == r.t)[0]
        if not len(tpos):
            skipped += 1; continue
        tpos = int(tpos[0])

        rel = (m.close.to_numpy() / m.vwap.to_numpy() - 1.0)
        under = np.nonzero(rel[:tpos] < 0)[0]          # the arm: last close under VWAP before the trigger
        if not len(under):
            skipped += 1; continue
        arm = int(under[-1])

        out = dict(date=r.date, sym=r.sym, t=r.t)
        for b in BANDS:
            cand = np.nonzero(rel[arm:] >= b)[0]
            out[f"b{b:+.4f}"] = run(m, arm + int(cand[0]), adr_px) if len(cand) else np.nan

        pool = [j for j in range(len(m)) if WIN_LO <= hm[j] < WIN_HI and j != tpos]
        post = [v for v in (run(m, int(rng.choice(pool)), adr_px) for _ in range(N_DRAWS)) if v is not None] if pool else []
        out["post"] = np.mean(post) if post else np.nan
        rows.append(out)

    X = pd.DataFrame(rows)
    X.to_csv("data/studies/ur_vwap_band_2026-09-23.csv", index=False)
    print(f"scored {len(X):,}, skipped {skipped:,}\n")

    days = sorted(X.date.unique()); A = set(days[:len(days) // 2])
    def ct(s: pd.Series, dates: pd.Series) -> float:
        md = s.groupby(dates).mean().dropna()
        return float(md.mean() / (md.std(ddof=1) / sqrt(len(md)))) if len(md) > 2 else np.nan

    live = f"b{LIVE:+.4f}"
    print(f"{'='*112}\nUR VWAP reclaim band sweep — curated names, {STOP_ADR} ADR stop, % return\n{'='*112}")
    tab = []
    for b in BANDS:
        col = f"b{b:+.4f}"
        s = X.dropna(subset=[col])
        vs_live = X.dropna(subset=[col, live])
        vs_post = X.dropna(subset=[col, "post"])
        dl = vs_live[col] - vs_live[live]
        dp = vs_post[col] - vs_post["post"]
        ha = X[X.date.isin(A)].dropna(subset=[col, live])
        hb = X[~X.date.isin(A)].dropna(subset=[col, live])
        tab.append(dict(band=f"{100*b:+.2f}%" + ("  <LIVE" if b == LIVE else ""), n=len(s),
                        ret=s[col].mean(), vs_live=dl.mean(), t_live=ct(dl, vs_live.date),
                        vs_post=dp.mean(), t_post=ct(dp, vs_post.date),
                        halfA=(ha[col] - ha[live]).mean(), halfB=(hb[col] - hb[live]).mean()))
    T = pd.DataFrame(tab)
    print(T.to_string(index=False, float_format=lambda v: f"{v:,.3f}"))
    print(f"\n  POST control (random minute, same name-day): {X['post'].mean():+.3f}%")

    cands = T[(T.vs_live > 0) & (T.t_live.abs() >= 3) & (np.sign(T.halfA) == np.sign(T.halfB)) & (T.vs_post > 0)]
    print(f"\n  bands beating LIVE at |t|>=3 with both halves agreeing AND beating the control: "
          f"{len(cands)} of {len(BANDS)}")
    print(f"  PRE-REGISTERED PASS: {'YES' if len(cands) else 'NO'}")
    print("\nwrote data/studies/ur_vwap_band_2026-09-23.csv")


if __name__ == "__main__":
    main()
