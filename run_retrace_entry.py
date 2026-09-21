#!/usr/bin/env python3
"""
The tradeable version of the ledger's control: wait for the breakout to come back to you.

entry_vs_stop_2026-09-20.md measured the mechanism: a house breakout enters +0.52 ADR ABOVE the
prior 20-session high, while the same-name random-later control enters -2.09 ADR below it. 2.6 ADR
of price paid for the same name, and that gap -- not the stop -- is the whole -0.4R.

The control is not tradeable ("a random later session"). This is: take the same breakout, then defer
entry until price retraces to within RETRACE ADR of the breakout level, giving up if it has not come
back within WAIT sessions. If the location gap is the mechanism, this recovers most of the 0.4R.

Three arms, because two different questions are in play:
  A  breakout        -- the current rule, every breakout, entered on the breakout close
  B  retrace         -- TRADEABLE: entered on the retrace close; breakouts that never retrace are skipped
  C  breakout-matched -- the SAME breakouts as B, entered on the breakout close. NOT tradeable (it
                        conditions on a retrace that has not happened yet); it exists only to isolate
                        the entry-timing effect from the change in which breakouts get taken.

B vs A is the decision. C vs B is the explanation.

Usage: PYTHONPATH=src .venv/bin/python3 run_retrace_entry.py > data/studies/retrace_entry_2026-09-20.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); pd.set_option("display.width", 230)
from lib.studies.pattern_test import load_panel, daily_signals, run_daily

WAITS = (5, 10, 20)
RETRACES = (0.0, 0.5)          # ADR above the breakout level we are willing to pay


def masks(P, wait: int, retrace: float):
    """Return (breakout_all, retrace_entry, breakout_matched) boolean frames."""
    C, H, A = P.close, P.high, P.adr
    level = H.shift(1).rolling(20).max()
    brk = (C > level) & (A >= 3) & P.elig
    cv, lvv, av = C.values, level.values, A.values
    bk = brk.values
    n, m = cv.shape
    ent = np.zeros_like(bk); matched = np.zeros_like(bk)
    for j in range(m):
        for i in np.flatnonzero(bk[:, j]):
            lv, a = lvv[i, j], av[i, j]
            if not np.isfinite(lv) or not np.isfinite(a) or a <= 0:
                continue
            cap = lv * (1 + retrace * a / 100.0)       # price we are willing to pay
            hi = min(i + wait, n - 1)
            for k in range(i + 1, hi + 1):
                if np.isfinite(cv[k, j]) and cv[k, j] <= cap:
                    ent[k, j] = True; matched[i, j] = True
                    break
    f = lambda x: pd.DataFrame(x, index=C.index, columns=C.columns)
    return brk, f(ent), f(matched) & brk


def main():
    P = load_panel()
    stop = P.close * (1 - 1.0 * P.adr / 100.0)
    rows = []
    for retrace in RETRACES:
        for wait in WAITS:
            brk, ent, mat = masks(P, wait, retrace)
            nb, ne = int(brk.sum().sum()), int(ent.sum().sum())
            print(f"\n\n{'='*92}\nRETRACE <= {retrace:g} ADR above the breakout level, WAIT <= {wait} sessions"
                  f"\n{nb:,} breakouts -> {ne:,} retrace entries ({100*ne/max(nb,1):.1f}% came back)\n{'='*92}")
            tabs = {}
            for lab, m_ in (("A breakout(all)", brk), ("B retrace", ent), ("C breakout-matched", mat)):
                tabs[lab] = run_daily(f"{lab} | retrace<={retrace:g}ADR wait<={wait}d",
                                      (lambda mm: (lambda _P: daily_signals(mm, stop=stop, side="long")))(m_),
                                      hold=5, panel=P, ledger=False,
                                      note="retrace-entry test off entry_vs_stop_2026-09-20")
            cols = {}
            for lab, t in tabs.items():
                for c in ("meanR", "ctrl", "edge", "t", "win", "n"):
                    cols[f"{lab.split()[0]}_{c}"] = t[c]
            cmp = pd.DataFrame(cols)
            cmp["B_minus_A"] = cmp["B_meanR"] - cmp["A_meanR"]
            cmp["B_minus_C"] = cmp["B_meanR"] - cmp["C_meanR"]
            print(f"\n##### retrace<={retrace:g}ADR wait<={wait}d: per exit arm #####")
            print(cmp.round(3).to_string())
            best = cmp["B_meanR"].idxmax()
            rows.append(dict(retrace=retrace, wait=wait, came_back_pct=100*ne/max(nb,1), n_entries=ne,
                             arm=best, A=cmp.loc[best,"A_meanR"], B=cmp.loc[best,"B_meanR"],
                             C=cmp.loc[best,"C_meanR"], B_edge=cmp.loc[best,"B_edge"],
                             A_edge=cmp.loc[best,"A_edge"], B_t=cmp.loc[best,"B_t"]))
    print("\n\n================ SUMMARY (best arm per cell by B meanR) ================")
    S = pd.DataFrame(rows)
    print(S.round(3).to_string(index=False))
    print("\nB > A  => deferring entry beats the current rule (the decision)")
    print("B > C  => the gain is entry TIMING, not a change in which breakouts get taken")


if __name__ == "__main__":
    main()
