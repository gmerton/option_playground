#!/usr/bin/env python3
"""
RECLAIM vs PULLBACK-LOW: the creator variant of our retrace entry (pre-registered 2026-09-23).

THE DISAGREEMENT. Three creators independently describe our entry finding on the right axis with the
OPPOSITE sign, and nobody has tested their version.
  * Ariel 2026-09-23: a higher low "would also have to **take out that 199 spot**" (likewise 378 on PANW,
    59 on TGTX, the 20 SMA on NEM) -- i.e. he will not buy the dip, he buys the RECLAIM of the prior high.
  * Mari Trades: declined 36.75 and paid **45.70 for the first green print**.
  * Our tested retrace arm buys the LOWER price (`run_retrace_entry.py`: edge -0.101 -> +0.065,
    B-C = +0.53R, but t 0.48 -> PARKED).
Both camps say "wait for the pullback". They are NOT the same trade: one buys weakness, one buys the
recovery. Our whole entry-extension result (+2.6 ADR paid, and that gap IS the loss) says the lower entry
must win. The creators are consistently profitable and say the opposite. That is worth one clean test.

EVENT. A pullback inside an uptrend, on the liquid panel:
  uptrend   close > 20 EMA, ADR >= 3, eligible (ADDV >= $50M, px >= $5, not suspect)
  PEAK      a session whose high is the highest of the trailing 10 -- the "pre-pullback high"
  PULLBACK  a later close at least PB_ADR (1.0) ADR BELOW that peak high, within WAIT sessions

ARMS (identical stop = 1 ADR under the entry, identical horizon; only the ENTRY differs):
  A  PULLBACK-LOW  buy the close of the first bar that is >= PB_ADR below the peak high. Implementable:
                   it is a level, not the actual low (the low is unknowable in advance -- that is exactly
                   the look-ahead that got the UR band sweep retracted today).
  B  RECLAIM       buy the first close back ABOVE the peak high, within WAIT sessions of the pullback.
  C  DIP-MATCHED   arm A restricted to the events that LATER produced a reclaim. Not tradeable -- it
                   conditions on a recovery that has not happened yet -- and it exists only to separate
                   the two things B changes at once.

⚠ THE BIMODALITY PROBLEM, which is the whole reason C exists. B can only ever buy the cohort that came
back. Comparing B to A therefore mixes an ENTRY-TIMING effect with a POPULATION effect (B skips every
pullback that kept falling). **B vs C is the timing question; C vs A is the population question.** Quoting
B vs A alone would repeat today's ORB9 error, where a control that moved the names got read as a verdict
on the trigger.

⚠ ext_above_level IS THE COMPARABLE. For every arm we report (entry - peak_high) in ADR units. That is the
one variable with a measured mechanism (2.6 ADR = -0.4R on the house breakout). A buys below the level
(negative), B above it (positive). If the mechanism generalises, the gap between the arms should predict
the gap in returns.

⚠ The reclaim RESEMBLES the house breakout, which loses -0.21..-0.33R -- but a reclaim inside a pullback
is not a fresh 20-day-high break, and that distinction is precisely what is untested.

PRE-REGISTERED PASS for the creators' version: B beats C (the same events, entered later and higher) with
date-clustered |t| >= 3 and both halves the same sign. B must ALSO beat its own `post` and `xname`
controls. 2 primary comparisons x 3 (WAIT) x 2 (PB_ADR) = 12 cells -> Sidak |t| >= 2.87; house 3.0 governs.

PRIOR: B loses to C on the mean (~70%). The extension mechanism is the most replicated finding here and
it points one way. The interesting outcome is not "who wins the mean" but whether B wins the WIN RATE
while losing the mean -- the risk-vs-return split that both the 21-DTE rule and the spike branch produced
today. If so the creators are right about consistency and wrong about expectancy, which would also explain
how they can run it profitably with discretionary sizing on top.

Usage: PYTHONPATH=src .venv/bin/python3 -u run_reclaim_vs_pullback.py 2>&1 | tee data/studies/logs/reclaim_vs_pullback.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250)

from lib.studies import pattern_test as pt
from lib.studies.pattern_test import daily_signals, load_panel, run_daily

PEAK_N = 10          # the pre-pullback high is the highest high of the trailing PEAK_N sessions
PB_ADRS = (1.0, 1.5)
WAITS = (5, 10, 20)
SPLIT = "2023-01-01"


def build(P, pb_adr: float, wait: int):
    """(pullback_low_entry, reclaim_entry, dip_matched) boolean frames + per-event ext_above_level in ADR."""
    C, H, A = P.close, P.high, P.adr
    ema20 = P.ema20
    peak = H.rolling(PEAK_N).max()                      # includes today; the peak bar itself qualifies
    up = (C > ema20) & (A >= 3) & P.elig
    cv, hv, av, pv = C.to_numpy(), H.to_numpy(), A.to_numpy(), peak.to_numpy()
    upv = up.to_numpy()
    n, m = cv.shape
    a_ent = np.zeros((n, m), bool); b_ent = np.zeros((n, m), bool); c_mat = np.zeros((n, m), bool)
    ext_a = np.full((n, m), np.nan); ext_b = np.full((n, m), np.nan)

    for j in range(m):
        col_up = np.flatnonzero(upv[:, j])
        for i in col_up:
            ph, a = pv[i, j], av[i, j]
            if not np.isfinite(ph) or not np.isfinite(a) or a <= 0:
                continue
            if not (np.isfinite(hv[i, j]) and hv[i, j] >= ph - 1e-12):
                continue                                 # this bar must BE the peak of its window
            apx = ph * a / 100.0                         # one ADR in price terms, off the peak
            dip = None
            hi = min(i + wait, n - 1)
            for k in range(i + 1, hi + 1):               # first close >= pb_adr ADR below the peak high
                if np.isfinite(cv[k, j]) and cv[k, j] <= ph - pb_adr * apx:
                    dip = k; break
            if dip is None:
                continue
            a_ent[dip, j] = True
            ext_a[dip, j] = (cv[dip, j] - ph) / apx
            hi2 = min(dip + wait, n - 1)
            for k2 in range(dip + 1, hi2 + 1):           # first close back ABOVE the peak high
                if np.isfinite(cv[k2, j]) and cv[k2, j] > ph:
                    b_ent[k2, j] = True
                    ext_b[k2, j] = (cv[k2, j] - ph) / apx
                    c_mat[dip, j] = True
                    break
    f = lambda x: pd.DataFrame(x, index=C.index, columns=C.columns)
    return f(a_ent), f(b_ent), f(c_mat), f(ext_a), f(ext_b)


def main() -> None:
    P = load_panel()
    stop = P.close * (1 - 1.0 * P.adr / 100.0)           # 1 ADR under the entry, every arm
    out = []
    for pb in PB_ADRS:
        for wait in WAITS:
            A_, B_, C_, xa, xb = build(P, pb, wait)
            na, nb = int(A_.to_numpy().sum()), int(B_.to_numpy().sum())
            print(f"\n\n{'='*118}\nPULLBACK >= {pb} ADR below a {PEAK_N}-session high, WAIT <= {wait} sessions"
                  f"\n{na:,} pullbacks -> {nb:,} reclaimed ({100*nb/max(na,1):.1f}% came back)"
                  f"\nmedian ext_above_level:  A pullback-low {np.nanmedian(xa.to_numpy()):+.2f} ADR   "
                  f"B reclaim {np.nanmedian(xb.to_numpy()):+.2f} ADR\n{'='*118}", flush=True)
            tabs = {}
            for lab, mask in (("A pullback-low", A_), ("B reclaim", B_), ("C dip-matched", C_)):
                print(f"\n---- {lab}")
                tabs[lab] = run_daily(f"{lab} | pb>={pb}ADR wait<={wait}d",
                                      lambda _P, mm=mask: daily_signals(mm, stop=stop, side="long"),
                                      hold=20, panel=P, ledger=False, entry_at="close", control="post",
                                      note=f"reclaim-vs-pullback {pb}ADR/{wait}d; 1-ADR stop, close entry")
            for lab, t in tabs.items():
                best = t.edge.idxmax()
                out.append(dict(pb=pb, wait=wait, arm=lab, n=int(t.loc[best, "n"]), arm_best=best,
                                meanR=t.loc[best, "meanR"], win=t.loc[best, "win"],
                                t=t.loc[best, "t"], ctrl=t.loc[best, "ctrl"], edge=t.loc[best, "edge"]))
    S = pd.DataFrame(out)
    S.to_csv("data/studies/reclaim_vs_pullback_2026-09-23.csv", index=False)
    print(f"\n\n{'#'*118}\nSUMMARY — best arm per cell (control = same name, random later session)\n{'#'*118}")
    print(S.round(3).to_string(index=False))
    print("\n⚠ B vs C is the TIMING question (same events). C vs A is the POPULATION question.")
    print("wrote data/studies/reclaim_vs_pullback_2026-09-23.csv")


if __name__ == "__main__":
    main()
