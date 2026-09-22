#!/usr/bin/env python3
"""VWAP double-rejection short (2026-09-21, prompted by SNDK 9/21): a name flushes early, trades under a falling
VWAP, rallies back to touch it twice and fails -- is the failure after the SECOND touch a bearish day-trade entry?

Pre-registered before the run (thresholds in ADR units, not fitted to SNDK):
  setup        by 10:30 the session low is >= 0.3 ADR below the open; VWAP falling (VWAP now < VWAP 30 min ago)
  touch        after >= 10 consecutive 1-min closes below VWAP*(1-0.15%), a 1-min HIGH >= VWAP*(1-0.15%)
  touch ends   (= a rejection) at the first 1-min close <= VWAP - 0.1 ADR
  invalidation any completed 5-min close > VWAP + 0.1 ADR kills the setup for the day
  signal       the rejection that ends touch #2 (arm "2nd"), or touch #1 (arm "1st", for comparison),
               10:00-14:30 ET; entry = next bar's open (harness); one signal per name-day per arm
  stop         max high since that touch began + 0.1 ADR (never below VWAP + 0.05 ADR)
Harness: lib.studies.pattern_test.run_intraday (control = same name-day, random minute 09:45-15:30; bar = beats
control, both halves positive, |t| >= 3). Universe = the cached 1-min bars (192 names, 2026-02-02 -> 09-18): the
curated alert universe + the 39-name no-hindsight control set (universe_study_extra.txt), reported separately.

Usage: PYTHONPATH=src .venv/bin/python3 run_vwap_rejection_short.py | tee data/studies/vwap_rejection_short_2026-09-21.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 230)
from lib.studies import pattern_test as pt
from lib.studies.pattern_test import run_intraday

FLUSH_ADR, FLUSH_BY = 0.30, "10:30"
TOUCH_BAND = 0.0015
BELOW_RUN = 10
REJECT_ADR = 0.10
KILL_ADR = 0.10
STOP_ADR = 0.10
WIN = ("10:00", "14:30")


def rejections(sym: str, day: str, b: pd.DataFrame, a_pct: float) -> list[dict]:
    """All rejection events of the day (1st, 2nd, ...), with the touch's high."""
    b = b[(b.index.strftime("%H:%M") >= "09:30") & (b.index.strftime("%H:%M") < "16:00")]
    if len(b) < 120 or not np.isfinite(a_pct) or a_pct <= 0:
        return []
    cv = ((b.vwap * b.volume).cumsum() / b.volume.cumsum().replace(0, np.nan)).values
    hm = b.index.strftime("%H:%M").values
    o0 = float(b.open.iloc[0])
    lo_by = b.low[hm < FLUSH_BY].min()
    if not (lo_by <= o0 * (1 - FLUSH_ADR * a_pct / 100)):
        return []
    a = a_pct / 100
    H, C = b.high.values, b.close.values
    c5 = b.close.resample("5min", label="left", closed="left").last()
    v5 = pd.Series(cv, index=b.index).resample("5min", label="left", closed="left").last()
    kill5 = c5 > v5 * (1 + KILL_ADR * a)
    kill_t = (kill5[kill5].index[0] + pd.Timedelta(minutes=5)) if kill5.any() else None   # 5-min bar completes
    out, below, in_touch, t_start, t_hi = [], 0, False, None, -np.inf
    for k in range(len(b)):
        t = b.index[k]
        if kill_t is not None and t >= kill_t:
            break
        v = cv[k]
        if not np.isfinite(v):
            continue
        if not in_touch:
            if below >= BELOW_RUN and H[k] >= v * (1 - TOUCH_BAND):
                k30 = max(k - 30, 0)
                if np.isfinite(cv[k30]) and v < cv[k30]:          # VWAP falling
                    in_touch, t_start, t_hi = True, k, H[k]
                    continue
            below = below + 1 if C[k] < v * (1 - TOUCH_BAND) else 0
        else:
            t_hi = max(t_hi, H[k])
            if C[k] <= v * (1 - REJECT_ADR * a):                   # rejection
                stop = max(t_hi * (1 + STOP_ADR * a), v * (1 + 0.05 * a))
                out.append(dict(t=t, stop=stop, side="short", n=len(out) + 1, touch_min=k - t_start,
                                ext_adr=(o0 - C[k]) / o0 / a))
                in_touch, below = False, 0
    return out


def arm(which: int):
    def pattern(sym, day, b, a_pct):
        ev = [e for e in rejections(sym, day, b, a_pct) if e["n"] == which
              and WIN[0] <= e["t"].strftime("%H:%M") <= WIN[1]]
        return [{k: v for k, v in e.items() if k != "n"} for e in ev[:1]]
    return pattern


def main():
    ctl = {l.split()[0] for l in open(pt.REPO / "data/watchlist/universe_study_extra.txt")
           if l.strip() and not l.startswith("#")}
    for which, lab in ((2, "2nd"), (1, "1st")):
        name = f"VWAP rejection short {lab} touch 2026-09-21"
        print(f"\n\n{'=' * 100}\n{name}\n{'=' * 100}")
        run_intraday(name, arm(which), note="pre-registered (SNDK 9/21); flush>=0.3ADR by 10:30, falling VWAP, "
                     f"touch within 0.15%, rejection close <= VWAP-0.1ADR, stop touch-high+0.1ADR; arm {lab}")
        T = pd.read_parquet(pt.REPO / f"data/cache/pattern_{name.replace(' ', '_').lower()}_intraday.parquet")
        T["set"] = np.where(T.sym.isin(ctl), "control set", "curated")
        print("\nby universe set (mean R per arm):")
        print(T.groupby("set")[pt.INTRA_ARMS].mean().round(3).assign(n=T.groupby("set").size()).to_string())
        print(f"\nSNDK rows:\n{T[T.sym == 'SNDK'][['date', 'stop_close', 'vwap_flip', 'next_close']].tail(8).to_string()}")


if __name__ == "__main__":
    main()
