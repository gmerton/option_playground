#!/usr/bin/env python3
"""
Ariel's ACTUAL Follow-Through Day claim: do SINGLE NAMES work better after an FTD?

run_ftd_study.py tested whether the INDEX rallies after an FTD and found no timing edge. That was
the wrong target. Ariel's words (TraderLion 2026-09-13): "most follow-through days tend to fail"
-- he agrees the index is unreliable -- but "immediately after a valid follow-through day, you get
stock after stock after stock after stock really going to work". The claim is about the payoff to
single-name setups, with progressive exposure covering the FTDs that fail.

So: take the house breakout (close > 20-session high, ADR >= 3, eligible -- the same mask as the
regime-split study), split it into breakouts that fire WITHIN N sessions after an FTD and those that
do not, and run both through the standard harness so each gets the honest post/xname controls.

If Ariel is right, the post-FTD arm should carry a materially better meanR *and* a better edge over
its own control. If the two arms are the same, the FTD is not selecting better setups -- it is just
a label on the calendar.

Usage: PYTHONPATH=src .venv/bin/python3 run_ftd_names_split.py > data/studies/ftd_names_2026-09-20.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

from lib.studies import pattern_test as pt
from lib.studies.pattern_test import load_panel, daily_signals, run_daily
from run_ftd_study import find_ftds

WINDOWS = (5, 10, 21)


def ftd_dates(dd=0.05, th=0.010) -> pd.DatetimeIndex:
    raw = pd.read_parquet("data/cache/index_daily_ftd.parquet")
    spy = raw[raw.ticker == "SPY"].sort_index()
    _, first, _, _ = find_ftds(spy, dd, th)
    return spy.index[first]


def post_ftd_flag(index: pd.DatetimeIndex, ftds: pd.DatetimeIndex, win: int) -> pd.Series:
    """True for the `win` sessions starting at each FTD (inclusive)."""
    flag = pd.Series(False, index=index)
    pos = index.get_indexer(ftds, method="bfill")
    for p in pos[pos >= 0]:
        flag.iloc[p:p + win] = True
    return flag


def breakout_mask(P):
    return (P.close > P.high.shift(1).rolling(20).max()) & (P.adr >= 3) & P.elig


def arm(P, flag: pd.Series, want: bool, k: float = 1.0):
    brk = breakout_mask(P)
    sel = flag if want else ~flag
    m = brk & pd.DataFrame(np.repeat(sel.values[:, None], brk.shape[1], axis=1),
                           index=brk.index, columns=brk.columns)
    stop = P.close * (1 - k * P.adr / 100.0)
    return lambda _P: daily_signals(m, stop=stop, side="long")


def main():
    P = load_panel()
    idx = P.close.index
    ftds = ftd_dates()
    inpanel = ftds[(ftds >= idx.min()) & (ftds <= idx.max())]
    print(f"panel {idx.min().date()} -> {idx.max().date()} ({len(idx)} sessions x {P.close.shape[1]} names)")
    print(f"SPY first-FTDs total {len(ftds)}, inside the panel window: {len(inpanel)}")
    print("  " + ", ".join(str(d.date()) for d in inpanel))
    if len(inpanel) < 6:
        print("\n⚠ too few FTDs in the panel window to condition on -- report as underpowered")

    brk = breakout_mask(P)
    print(f"\nhouse breakouts in panel: {int(brk.sum().sum()):,}")

    out = {}
    for win in WINDOWS:
        flag = post_ftd_flag(idx, ftds, win)
        share = flag.mean()
        nb_in = int((brk & pd.DataFrame(np.repeat(flag.values[:, None], brk.shape[1], axis=1),
                                        index=brk.index, columns=brk.columns)).sum().sum())
        print(f"\n\n{'='*84}\nWINDOW {win} sessions after an FTD | {share:.1%} of sessions | "
              f"{nb_in:,} of {int(brk.sum().sum()):,} breakouts fall inside\n{'='*84}")
        tabs = {}
        for lab, want in (("POST-FTD", True), ("OTHER", False)):
            name = f"20d breakout ADR>=3, {lab} ({win}d window)"
            tabs[lab] = run_daily(name, arm(P, flag, want), hold=5, panel=P, ledger=False,
                                  note=f"Ariel FTD claim: do single names work better in the {win} sessions after an FTD")
        cols = {}
        for lab, t in tabs.items():
            for c in ("meanR", "ctrl", "edge", "t", "win", "n"):
                cols[f"{lab}_{c}"] = t[c]
        cmp = pd.DataFrame(cols)
        cmp["diff_meanR"] = cmp["POST-FTD_meanR"] - cmp["OTHER_meanR"]
        cmp["diff_edge"] = cmp["POST-FTD_edge"] - cmp["OTHER_edge"]
        print(f"\n##### window {win}d: POST-FTD vs OTHER, per exit arm #####")
        print(cmp.round(3).to_string())
        out[win] = cmp

    print("\n\n================ VERDICT INPUTS ================")
    for win, c in out.items():
        best = c["POST-FTD_meanR"].idxmax()
        print(f"  {win:>2}d window: POST-FTD best arm {best} meanR {c.loc[best,'POST-FTD_meanR']:+.3f} "
              f"(edge {c.loc[best,'POST-FTD_edge']:+.3f}, n {int(c.loc[best,'POST-FTD_n'])}) | "
              f"OTHER same arm meanR {c.loc[best,'OTHER_meanR']:+.3f} (edge {c.loc[best,'OTHER_edge']:+.3f}) | "
              f"diff {c.loc[best,'diff_meanR']:+.3f}")
    print("\nAriel is right only if POST-FTD carries a materially higher meanR AND a better edge over")
    print("its own control than OTHER does. Same-ish numbers = the FTD is a calendar label, not selection.")


if __name__ == "__main__":
    main()
