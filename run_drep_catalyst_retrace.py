#!/usr/bin/env python3
"""
DR-EP: does a CATALYST GATE improve the retrace entry?   (pre-registered 2026-09-22)

WHY. Two results point at the same design from opposite directions:
  (a) `run_retrace_entry.py` (2026-09-20): deferring entry until price retraces toward the breakout
      level beat entering at the breakout close in ALL 6 cells (edge -0.101 -> +0.065, both halves
      positive, B-C = +0.53R) but landed at **t 0.48** -> PARKED, not adopted.
  (b) Pradeep Bonde's "delayed reaction EP" (TraderLion 2026-07-22, reviewed today): after a
      catalyst day, he refuses to chase and instead waits for an orderly pullback, entering on the
      resumption within ~25 sessions off a 3-4 name watchlist.
  The PARKED result had NO catalyst gate. The catalyst gate is therefore the NEW VARIABLE, and it is
  exactly what catalyst-queue #1 specifies (catalyst as SELECTION first, entry later).

CATALYST DAY (mechanical proxy, fixed before running; we cannot replicate his discretionary research):
    gap up >= 3%   AND   RVOL >= 1.8   AND   ADR >= 3   AND   eligible
  Rationale for each: a >=3% gap is the observable footprint of news; RVOL 1.8 is OUR OWN validated
  event threshold (rotation study: <1.8 cohorts are negative, 1.8-2.5 = +0.86R t 3.64); ADR/elig match
  the house breakout pool so the comparison is apples-to-apples.

ARMS (all enter at a CLOSE, stop = that entry day's low, the house rule):
  A  catalyst-day close          "buy the event" -- our PEAD/catalyst work predicts ~0
  B  DR-EP  = after the catalyst day, require (i) at least one close BELOW the catalyst close
             (the orderly give-back), then (ii) the first close ABOVE the highest high since the
             catalyst day, within 25 sessions. If it never gives back, there is no entry -- which is
             faithful to Bonde ("sometimes it just goes straight and never gives you a DR entry").
  D  the SAME retrace rule with NO catalyst gate, on the house breakout pool -> isolates whether the
     catalyst gate adds anything over the PARKED result.

CONTROLS: the harness's `post` (random later session, same name = timing) and `xname` (random other
name, same date, same stop % = selection). Both reported.

PRE-REGISTERED PRIMARY: arm B vs its `post` control.
  PASS = beats control AND both halves positive AND |t| >= 3 (day-clustered).
SECONDARY (diagnostic, ledger=False, no new multiple-testing charge claimed):
  B vs A on the same catalyst events; B vs D (does the catalyst gate add?); and the Bonde
  absolute-volume floor (>= 9M) as an extra condition -- our diagnostic already says that floor is
  59% a size proxy, so the stated prior is that it adds NOTHING.

WHAT WOULD FALSIFY: B at |t| < 3, or either half negative, or B <= D (catalyst gate adds nothing).

Usage:  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_drep_catalyst_retrace.py
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)

from lib.studies.pattern_test import daily_signals, load_panel, run_daily

START = "2019-10-01"
GAP_MIN = 3.0      # %
RVOL_MIN = 1.8
WAIT = 25          # sessions to find the resumption
ABS_VOL = 9e6      # Bonde's EP9M floor (secondary cut only)


def _panel_extras(P, raw):
    V = raw.pivot(index="date", columns="ticker", values="volume").sort_index()
    V = V.reindex(index=P.close.index, columns=P.close.columns)
    rvol = V / V.shift(1).rolling(20).mean()
    gap = (P.open / P.close.shift(1) - 1) * 100
    return V, rvol, gap


def catalyst_mask(P, rvol, gap) -> pd.DataFrame:
    m = (gap >= GAP_MIN) & (rvol >= RVOL_MIN) & (P.adr >= 3) & P.elig
    m = m.fillna(False)
    m[m.index < START] = False
    return m


def house_breakout(P) -> pd.DataFrame:
    lvl = P.high.shift(1).rolling(20).max()
    m = ((P.close > lvl) & (P.adr >= 3) & P.elig).fillna(False)
    m[m.index < START] = False
    return m


def retrace_entries(P, trigger: pd.DataFrame) -> pd.DataFrame:
    """After each trigger day: require one close BELOW the trigger close, then the first close ABOVE
    the highest high since the trigger. Returns a boolean entry mask."""
    C, H = P.close.values, P.high.values
    tg = trigger.values
    out = np.zeros_like(tg, dtype=bool)
    n, m = C.shape
    for j in range(m):
        for i in np.flatnonzero(tg[:, j]):
            c0 = C[i, j]
            if not np.isfinite(c0):
                continue
            run_hi = H[i, j]
            gave_back = False
            for k in range(i + 1, min(i + 1 + WAIT, n)):
                c, h = C[k, j], H[k, j]
                if not np.isfinite(c):
                    continue
                if c < c0:
                    gave_back = True
                if gave_back and c > run_hi:
                    out[k, j] = True
                    break
                if np.isfinite(h):
                    run_hi = max(run_hi, h)
    return pd.DataFrame(out, index=trigger.index, columns=trigger.columns)


def main() -> None:
    P = load_panel()
    raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
    V, rvol, gap = _panel_extras(P, raw)

    cat = catalyst_mask(P, rvol, gap)
    brk = house_breakout(P)
    b_mask = retrace_entries(P, cat)
    d_mask = retrace_entries(P, brk)

    print(f"catalyst days (gap>={GAP_MIN}%, RVOL>={RVOL_MIN}, ADR>=3): {int(cat.values.sum()):,}")
    print(f"  -> DR-EP entries found within {WAIT} sessions: {int(b_mask.values.sum()):,} "
          f"({100*b_mask.values.sum()/max(cat.values.sum(),1):.1f}% gave back then resumed)")
    print(f"house breakouts: {int(brk.values.sum()):,} -> retrace entries {int(d_mask.values.sum()):,}")

    specs = [
        ("A catalyst-day close", cat, True),
        ("B DR-EP catalyst+retrace", b_mask, True),
        ("D retrace, NO catalyst gate", d_mask, False),
    ]
    for name, mask, ledger in specs:
        for ctrl in ("post", "xname"):
            lab = f"DR-EP 2026-09-22: {name} [{ctrl}]"
            print(f"\n\n{'='*104}\n{lab}: {int(mask.values.sum()):,} signals\n{'='*104}")
            sig = lambda _P, mm=mask: daily_signals(mm, stop=P.low, side="long")
            run_daily(lab, sig, hold=20, panel=P, entry_at="close", control=ctrl,
                      ledger=(ledger and ctrl == "post"),
                      note="pre-registered DR-EP; catalyst = gap>=3% & RVOL>=1.8; retrace = giveback then new high")

    # secondary: Bonde's absolute-volume floor on top of the catalyst gate
    cat9 = cat & (V >= ABS_VOL)
    b9 = retrace_entries(P, cat9.fillna(False))
    print(f"\n\n{'='*104}\nSECONDARY (diagnostic): + Bonde 9M absolute-volume floor — "
          f"{int(cat9.values.sum()):,} catalyst days -> {int(b9.values.sum()):,} entries\n{'='*104}")
    sig9 = lambda _P: daily_signals(b9, stop=P.low, side="long")
    run_daily("DR-EP 2026-09-22: B + 9M floor [post]", sig9, hold=20, panel=P, entry_at="close",
              control="post", ledger=False, note="diagnostic: does the absolute-volume floor add anything?")


if __name__ == "__main__":
    main()
