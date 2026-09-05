#!/usr/bin/env python3
"""
Trailing-window retrospective: what is the tape doing, and what has been working,
over the last N sessions as of a date -- using only data available on that date.

Replaces the calendar-month view of data/studies/august_2026_retrospective.md
with a rolling one. DESCRIPTIVE ONLY: run_regime_validation.py showed the trailing
read has no forecasting power for the next window (see the footer it prints). Reads the Minervini day-cache (sync from S3 first:
  aws s3 cp s3://gmerton-stock-data/breakouts/minervini_matrix.parquet data/cache/).

Usage:
  PYTHONPATH=src python run_trailing_retro.py                     # as of last cached session
  PYTHONPATH=src python run_trailing_retro.py --asof 2026-08-18   # replay a past date
  PYTHONPATH=src python run_trailing_retro.py --window 21 --horizon 10
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from lib.regime.trailing import (REGIME_DEFAULTS, Panel, breadth, cohort_paths, liquid_universe, regime,
                                 scoreboard, style_spread)

REPO = Path(__file__).resolve().parent
CACHE = REPO / "data" / "cache" / "minervini_matrix.parquet"
INDMAP = REPO / "data" / "ticker_industry_map.csv"


def pct(x, w=6):
    return f"{100 * x:+{w}.1f}%" if pd.notna(x) else " " * (w + 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=None)
    ap.add_argument("--window", type=int, default=REGIME_DEFAULTS["window"])
    ap.add_argument("--horizon", type=int, default=10, help="forward sessions for the setup scoreboard")
    ap.add_argument("--cache", default=str(CACHE))
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()

    full = Panel.from_cache(a.cache)
    asof = pd.Timestamp(a.asof) if a.asof else full.close.index[-1]
    if asof not in full.close.index:
        asof = full.close.loc[:asof].index[-1]
    uni = liquid_universe(full, asof)
    p = full.restrict(uni).upto(asof)
    idx = p.close.index
    i_end = idx.get_loc(asof)
    start = idx[max(0, i_end - a.window)]
    # scoreboard needs `horizon` sessions AFTER each event; score events up to asof-horizon
    sb_end = idx[max(0, i_end - a.horizon)]

    r = regime(full, asof, universe=uni)
    print(f"=== TRAILING {a.window}-SESSION READ as of {asof.date()}  (window start {start.date()}, liquid universe n={len(uni)}) ===\n")
    print(f"REGIME:  breadth {'ON ' if r['breadth_on'] else 'OFF'} (10d advancer avg {100*r['adv10']:.1f}%)   style {r['style']}  "
          f"(laggard {pct(r['laggard_ret'])} vs leader {pct(r['leader_ret'])} over {a.window}s, spread {pct(r['spread'])})")
    print(f"         %>50sma {100*r['pct_above_50']:.1f}   %>200sma {100*r['pct_above_200']:.1f}   newHi {r['new_hi']}  newLo {r['new_lo']}  10d NH-NL {r['nh_nl_10']:+.0f}")

    b = breadth(p).loc[start:asof]
    s = style_spread(p, a.window).loc[start:asof]
    print("\nBREADTH + STYLE, last 10 sessions:")
    print("  date        adv%   adv10  %>50  newHi newLo  thrust | lag21   lead21  spread")
    for d in b.index[-10:]:
        print(f"  {d.date()}  {100*b.adv_pct[d]:5.1f}  {100*b.adv10[d]:5.1f}  {100*b.pct_above_50[d]:5.1f}  {b.new_hi[d]:5d} {b.new_lo[d]:5d}  {'  *' if b.thrust[d] else '   '}    | "
              f"{pct(s.laggard[d])} {pct(s.leader[d])} {pct(s.spread[d])}")

    cp = cohort_paths(p, start, asof)
    print(f"\nCOHORTS fixed at {start.date()} (equal-weight return to {asof.date()}):  " +
          "   ".join(f"{k}: {pct(v.iloc[-1])}" for k, v in cp.items()))

    ret = (p.close.loc[asof] / p.close.loc[start] - 1).mask(p.suspect().loc[asof]).dropna()
    if INDMAP.exists():
        m = pd.read_csv(INDMAP).set_index("ticker").reindex(ret.index)
        g = pd.DataFrame({"ret": ret, "ind": m.industry}).dropna()
        gi = g.groupby("ind").ret.agg(n="size", med="median", up=lambda x: (x > 0).mean())
        gi = gi[gi.n >= 6].sort_values("med", ascending=False)
        print(f"\nINDUSTRIES over the window (equal-weight median, n>=6) -- descriptive, not predictive:")
        print("  LEADING: " + "; ".join(f"{k} {pct(v.med,5).strip()} ({v.n:.0f}, {100*v.up:.0f}% up)" for k, v in gi.head(a.top).iterrows()))
        print("  LAGGING: " + "; ".join(f"{k} {pct(v.med,5).strip()} ({v.n:.0f})" for k, v in gi.tail(8).iterrows()))
    print(f"\nSTOCKS over the window: median {pct(ret.median())}, {100*(ret>0).mean():.0f}% up.  "
          f"Top: " + ", ".join(f"{t} {pct(v,4).strip()}" for t, v in ret.nlargest(a.top).items()))

    sb = scoreboard(p, start, sb_end, horizon=a.horizon)
    print(f"\nSETUP SCOREBOARD: events {start.date()}..{sb_end.date()}, {a.horizon}-session forward return, excess vs same-date baseline")
    print(f"  {'setup':28s} {'n':>6s} {'names':>5s} {'mean':>8s} {'median':>8s} {'win':>5s} {'excess':>8s}")
    for k, v in sb.iterrows():
        print(f"  {k:28s} {v.n:6.0f} {v.names:5.0f} {pct(v['mean'])} {pct(v['median'])} {100*v.win:4.0f}% {pct(v.excess)}")
    print("\nREAD THIS AS DESCRIPTIVE. run_regime_validation.py (2019-2026, point-in-time liquid universe) found NO persistence:\n"
          "  - trailing laggard-vs-leader spread vs next window: corr -0.11, sign agreement 48%\n"
          "  - a setup's trailing-21 excess vs its next-21 excess: corr within +/-0.2 for every setup\n"
          "  - breadth ON/OFF does not separate setup outcomes; weak breadth (adv10<50%) preceded HIGHER 21-session broad returns\n"
          "So: this tells you what the tape HAS been paying, not what it will pay next. Use it for exposure sanity and post-mortems.")


if __name__ == "__main__":
    main()
