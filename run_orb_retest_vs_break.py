#!/usr/bin/env python3
"""
ORB RETEST vs ORB BREAK — the Fit Mom Trader remedy (pre-registered 2026-09-23, TEST_INDEX §10).

THE CLAIM. Fit Mom Trader (2026-07-24, reviewed 3/5): do NOT trade the opening-range break. Retail buy
stops sit at the obvious level, institutions sweep them, and price comes back. **Trade the retest** --
specifically the pullback to the anchored VWAP or the 50% midpoint of the opening range, which she notes
usually coincide. She accepts the cost explicitly: you miss the days that run and never come back.

WHY IT IS WORTH RUNNING. Our own ORB9 trigger came in **INVERTED** on 2026-09-23: entering the break
earns +0.351%/trade against +0.775% for a random minute in the same window, **-0.425pp, t -8.50**, both
halves agreeing. We concluded it "buys the break, so it buys high". She reached the same diagnosis from
screen time two months earlier. The open question is not whether the retest beats the break -- the break
is already known to be bad -- but whether the retest beats **doing nothing in particular**, which no
intraday arm in this book has ever managed (Stage A: every arm -0.10..-0.13R and ~ a random later minute).

ARMS -- same name-day, same 0.6 ADR stop, all held to the session close; only the ENTRY MINUTE differs:
  BREAK        the ORB9 trigger bar's close (the live rule)
  RETEST_VWAP  first close at or below the SESSION VWAP (rebuilt from price x volume; the cached
               `vwap` column is per-bar and useless for this) within RETEST_MAX_MIN of the trigger
  RETEST_MID   first close at or below the opening-range midpoint, same time cap
  RANDOM       a random minute in 09:45-12:00, same name-day (3 draws, averaged) -- the control that
               killed the break arm

⚠ THE SELECTION TRAP, pre-registered. The retest arm can only trade breaks that COME BACK. Comparing it
to the break arm across all events would mix entry timing with a change in which trades get taken -- the
arm-C error from `reclaim_vs_pullback_2026-09-23`, and a cousin of the look-ahead that got the UR band
sweep retracted the same day. So TWO views are reported and neither alone is the answer:
  (1) PAIRED   -- only events where the retest actually fires. This is the TIMING question.
  (2) STRATEGY -- the full population, with **no-retest days scored as NO TRADE (0.0%)**, never dropped.
                  This is the TRADEABLE question and it charges her for the runaways she forfeits.
The no-retest share is reported explicitly, along with what the BREAK arm earned on exactly those days --
i.e. the cost of waiting.

PRE-REGISTERED PASS: RETEST beats RANDOM on the STRATEGY view, date-clustered |t| >= 3, both halves the
same sign. Beating BREAK is necessary but not sufficient and is not the test -- the break is inverted, so
clearing it is a low bar. 2 retest definitions x 2 views = 4 primary cells -> Sidak |t| >= 2.49; house 3.0.

PRIOR: RETEST beats BREAK comfortably (~85%) and FAILS to beat RANDOM (~75%). The extension mechanism
says a lower entry is better and the retest is mechanically lower, so the first is near-certain and nearly
arithmetic. The second is the real question, and nothing intraday has ever cleared it.

Usage: PYTHONPATH=src .venv/bin/python3 -u run_orb_retest_vs_break.py 2>&1 | tee data/studies/logs/orb_retest.log
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
STOP_ADR = 0.60
OR_END = "09:45"                 # ORB9 uses the 15-minute opening range
WIN_LO, WIN_HI = "09:45", "12:00"
N_DRAWS, SEED = 3, 20260923
# ⚠ THE RETEST MUST BE TIME-BOUNDED. Without this the session-VWAP arm fires on 100.0% of breaks —
# VWAP drifts toward price all session, so "price eventually closes at or below VWAP" is near-certain by
# late afternoon. That is not her setup (a pullback shortly after the break); it is an arbitrary later
# entry. She describes the retest as the next move after the break, so it is capped here.
RETEST_MAX_MIN = 60


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
    if not len(m) or "vwap" not in m.columns:
        return None
    hm = m.index.strftime("%H:%M")
    m = m[(hm >= "09:30") & (hm < "16:00")].copy()
    if not len(m):
        return None
    # ⚠ THE CACHED `vwap` COLUMN IS PER-BAR, NOT SESSION-CUMULATIVE — it is byte-identical to `price`
    # on every bar (verified 2026-09-23). Using it as "VWAP" makes `close <= vwap` a near-coinflip each
    # minute, so a "pullback to VWAP" fires on 100% of breaks within an hour and tests nothing.
    # The session VWAP is rebuilt here from price x volume.
    m["svwap"] = (m.price * m.volume).cumsum() / m.volume.cumsum().replace(0, np.nan)
    return m


def trade_at(m: pd.DataFrame, i: int, adr_px: float) -> float | None:
    """Enter at bar position i's close, 0.6 ADR stop, else out at the session close. Percent."""
    if i + 1 >= len(m):
        return None
    entry = float(m.close.iloc[i])
    if not np.isfinite(entry) or entry <= 0:
        return None
    seg = m.iloc[i + 1:]
    stop = entry - STOP_ADR * adr_px
    hit = (seg.low <= stop).any()
    return ((stop if hit else float(seg.close.iloc[-1])) / entry - 1) * 100


def ct(s: pd.Series, dates: pd.Series) -> float:
    md = s.groupby(dates).mean().dropna()
    return float(md.mean() / (md.std(ddof=1) / sqrt(len(md)))) if len(md) > 2 else np.nan


def main() -> None:
    rng = np.random.default_rng(SEED)
    d = pd.read_csv("data/watchlist/logs/alert_study_scores.csv")
    ctl = {l.split()[0] for l in open("data/watchlist/universe_study_extra.txt")
           if l.strip() and not l.startswith("#")}
    a = d[(d.kind == "ORB9") & d.R.notna()].drop_duplicates(["date", "t", "sym"])
    a = a[~a.sym.isin(ctl)]
    print(f"curated ORB9 alerts: {len(a):,} over {a.date.nunique()} dates\n")

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
        tp = np.nonzero(hm == r.t)[0]
        if not len(tp):
            skipped += 1; continue
        tp = int(tp[0])

        brk = trade_at(m, tp, adr_px)
        if brk is None:
            skipped += 1; continue

        orb = m[hm < OR_END]
        mid = (float(orb.high.max()) + float(orb.low.min())) / 2 if len(orb) else np.nan
        close_a, vwap_a = m.close.to_numpy(), m.svwap.to_numpy()

        hi_i = min(tp + 1 + RETEST_MAX_MIN, len(m))

        def first_at_or_below(level_arr) -> int | None:
            seg = close_a[tp + 1:hi_i] <= level_arr[tp + 1:hi_i]
            cand = np.nonzero(seg)[0]
            return tp + 1 + int(cand[0]) if len(cand) else None

        iv = first_at_or_below(vwap_a)
        im = first_at_or_below(np.full(len(m), mid)) if np.isfinite(mid) else None

        pool = [j for j in range(len(m)) if WIN_LO <= hm[j] < WIN_HI and j != tp]
        rnd = [v for v in (trade_at(m, int(rng.choice(pool)), adr_px) for _ in range(N_DRAWS))
               if v is not None] if pool else []

        rows.append(dict(date=r.date, sym=r.sym, t=r.t, brk=brk,
                         rt_vwap=trade_at(m, iv, adr_px) if iv is not None else np.nan,
                         rt_mid=trade_at(m, im, adr_px) if im is not None else np.nan,
                         rnd=np.mean(rnd) if rnd else np.nan))
    X = pd.DataFrame(rows)
    X.to_csv("data/studies/orb_retest_vs_break_2026-09-23.csv", index=False)
    print(f"scored {len(X):,}, skipped {skipped:,}\n")

    days = sorted(X.date.unique()); A = set(days[:len(days) // 2])
    for col, lab in (("rt_vwap", "RETEST = pullback to session VWAP"),
                     ("rt_mid", "RETEST = pullback to the opening-range midpoint")):
        fired = X[col].notna()
        print(f"\n{'='*110}\n{lab}\n{'='*110}")
        print(f"  retest fires on {100*fired.mean():.1f}% of breaks ({int(fired.sum()):,} of {len(X):,})")
        print(f"  ⚠ on the {int((~fired).sum()):,} days it never comes back, the BREAK arm earned "
              f"{X.loc[~fired, 'brk'].mean():+.3f}% — that is what waiting forfeits")

        p = X[fired]
        print(f"\n  (1) PAIRED — events where the retest fires (the TIMING question), n={len(p):,}")
        for other, oname in (("brk", "BREAK"), ("rnd", "RANDOM minute")):
            s = p.dropna(subset=[col, other]); dd = s[col] - s[other]
            print(f"      {col} {s[col].mean():+.3f}%  vs {oname:<13s} {s[other].mean():+.3f}%   "
                  f"edge {dd.mean():+.3f}pp   t {ct(dd, s.date):+.2f}")

        print(f"\n  (2) STRATEGY — full population, no-retest days scored as NO TRADE 0.0%, n={len(X):,}")
        S = X.copy(); S["rt"] = S[col].fillna(0.0)
        for other, oname in (("brk", "BREAK"), ("rnd", "RANDOM minute")):
            s = S.dropna(subset=[other]); dd = s["rt"] - s[other]
            ha, hb = s[s.date.isin(A)], s[~s.date.isin(A)]
            e1, e2 = (ha["rt"] - ha[other]).mean(), (hb["rt"] - hb[other]).mean()
            t = ct(dd, s.date)
            flag = ""
            if other == "rnd":
                flag = "  <<< PASS" if (dd.mean() > 0 and abs(t) >= 3 and np.sign(e1) == np.sign(e2)) else "  <<< no pass"
            print(f"      retest {s['rt'].mean():+.3f}%  vs {oname:<13s} {s[other].mean():+.3f}%   "
                  f"edge {dd.mean():+.3f}pp   t {t:+.2f}   halves {e1:+.3f}/{e2:+.3f}{flag}")

    print("\nwrote data/studies/orb_retest_vs_break_2026-09-23.csv")


if __name__ == "__main__":
    main()
