#!/usr/bin/env python3
"""
The house entry through the pattern harness: does the precision-tier breakout beat a RANDOM session in the same
name and month? The +0.79R in exit_timing_study_2026-09-18 was never run against that control (ledger row flagged).

Signal = exactly run_exit_timing_study.py's `precision` mask:
  gate       ADR >= 3, 52wk range >= 17% of price, elig (ADDV >= $50M, px >= $5, not suspect), SPY/QQQ/IWM/RSP excluded
  breakout   close >= 15-day pivot (prior close below it), RVOL >= 1.1 vs 50d, upper-half close, gap < 5%, day < 8%,
             EMA stack (10 > 20 > 50 with house slack) running >= 5 sessions
  precision  ADR 4-7, within 15% of the 52wk high, stack run 5-40 sessions
Stop = the breakout bar's low. Harness: entry NEXT open (+10 bps), R = move / (entry - stop).

Runs (same-name random-session-same-month control on every one):
  precision tier, hold 5   -> ledger (the standard row)
  precision tier, hold 60  -> ledger (the house horizon: ema20 trail is the process exit; the hold cap rarely binds)
  all breakouts, hold 5 / 60 -> report only (what the tier's selection adds over the generic breakout)

Usage: PYTHONPATH=src .venv/bin/python3 run_precision_tier_control.py > data/studies/breitstein_tests/logs/precision_tier_control_<date>.log
"""
from __future__ import annotations

import warnings
from datetime import date

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask
from lib.studies import pattern_test as pt
from lib.studies.pattern_test import DailyPanel, daily_signals, run_daily

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
TODAY = date.today().isoformat()


def build():
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max()
    lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    piv15 = H.shift(1).rolling(15).max()
    rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan)
    gap = O / C.shift(1) - 1
    chg = C.pct_change(fill_method=None)
    stack_days = stack_run(C, adr=adr)
    off52 = (C / hi52 - 1) * 100
    gate = (adr >= 3) & (range52 >= 17) & elig
    brk = (gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5)
           & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15))
    precision = brk & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stack_days >= 5) & (stack_days <= 40)
    P = DailyPanel(open=O, high=H, low=L, close=C, adr=adr, elig=elig, ema20=C.ewm(span=20, adjust=False).mean())
    return P, brk.fillna(False), precision.fillna(False)


def main():
    P, brk, prec = build()
    print(f"panel {P.close.shape}; all-breakout days {int(brk[brk.index >= '2019-10-01'].values.sum()):,}; "
          f"precision days {int(prec[prec.index >= '2019-10-01'].values.sum()):,}")
    rows = []
    for name, mask, hold, ledger in [
        ("precision-tier breakout (house), next-open entry", prec, 5, True),
        ("precision-tier breakout (house), next-open entry, hold 60", prec, 60, True),
        ("all breakouts (generic pool), next-open entry", brk, 5, False),
        ("all breakouts (generic pool), next-open entry, hold 60", brk, 60, False),
    ]:
        print(f"\n\n================ {name} | hold {hold} ================")
        tab = run_daily(name, lambda _P, m=mask: daily_signals(m, stop=P.low, side="long"), hold=hold, panel=P,
                        ledger=ledger, note="exit_timing pool through the harness; ctrl = same name, random session, same month, same stop %")
        for arm in tab.index:
            rows.append(dict(pool=name, hold=hold, arm=arm, n=int(tab.loc[arm, "n"]), meanR=tab.loc[arm, "meanR"],
                             win=tab.loc[arm, "win"], t=tab.loc[arm, "t"], ctrl=tab.loc[arm, "ctrl"], edge=tab.loc[arm, "edge"]))
    S = pd.DataFrame(rows)
    print("\n\n################ SUMMARY ################")
    print(S.round(3).to_string(index=False))
    S.to_csv(pt.REPO / f"data/studies/breitstein_tests/precision_tier_control_summary_{TODAY}.csv", index=False)



def close_entry_runs():
    """The house process itself: enter at the breakout CLOSE, stop = day's low on the close, ema20 trail."""
    P, brk, prec = build()
    rows = []
    for name, mask, hold, ledger in [
        ("precision-tier breakout (house), CLOSE entry, hold 60", prec, 60, True),
        ("precision-tier breakout (house), CLOSE entry", prec, 5, False),
        ("all breakouts (generic pool), CLOSE entry, hold 60", brk, 60, False),
    ]:
        print(f"\n\n================ {name} | hold {hold} | entry at the signal close ================")
        tab = run_daily(name, lambda _P, m=mask: daily_signals(m, stop=P.low, side="long"), hold=hold, panel=P,
                        ledger=ledger, entry_at="close",
                        note="the house process (close entry, stop = day low on the close); ctrl = same name, random session close, same month, same stop %")
        for arm in tab.index:
            rows.append(dict(pool=name, hold=hold, arm=arm, n=int(tab.loc[arm, "n"]), meanR=tab.loc[arm, "meanR"],
                             win=tab.loc[arm, "win"], t=tab.loc[arm, "t"], ctrl=tab.loc[arm, "ctrl"], edge=tab.loc[arm, "edge"]))
    S = pd.DataFrame(rows)
    print("\n\n################ SUMMARY (close entry) ################")
    print(S.round(3).to_string(index=False))
    S.to_csv(pt.REPO / f"data/studies/breitstein_tests/precision_tier_control_close_summary_{TODAY}.csv", index=False)


if __name__ == "__main__":
    import sys
    close_entry_runs() if sys.argv[1:] == ["--close"] else main()
