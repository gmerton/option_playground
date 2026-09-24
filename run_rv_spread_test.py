#!/usr/bin/env python3
"""
Relative-value spread: long the strong universe, short the weak one (pre-registered 2026-09-24, before the first run).

WHY. short_universe_test_2026-09-23: 10/10 weak-name cells have NEGATIVE ADR-matched excess but 0/10 a negative
ABSOLUTE return -- weak names lag and still drift up, so there is nothing to short outright. Its carry-forward note:
"negative excess + positive absolute = the signature of RELATIVE VALUE". The failed-retest breakdown short
(2026-09-24) confirmed the outright route is dead. Neither universe test was ever scored as a SPREAD, which removes
the market drift both legs share. New axis: the spread is the unit.

DESIGN
  legs       membership masks reused verbatim: long from run_universe_test.build_masks (INT, TT), short from
             run_short_universe_test.build_masks (INV-TT, DOWN, LAGGARD, CRASH-H, DIST). Membership = prior close.
  rebalance  every 20th session from 2020-01-01 (non-overlapping), equal weight within each leg, dollar-neutral;
             spread_t = mean fwd-20d return(long members) - mean fwd-20d return(short members); >= 5 names per leg.
  costs      40 bp per period (100% turnover assumed: 10 bp per side per leg) + borrow 0.5%/yr on the short leg.
  PRIMARY    long INT vs short DIST (INT = the production long universe, adopted on its own evidence; DIST = the
             broadest non-nested weak screen). Declared before seeing any spread.
  grid       2 long x 5 short = 10 cells, exploratory, Sidak-charged: |t| >= max(3, Sidak 10 cells) = 3.
  bar        net spread mean > 0 with t >= 3; both halves (split 2023-01-01) positive; positive in >= 5 of 7 years;
             AND alpha vs SPY (spread regressed on SPY's same-period return) > 0 with t >= 3 -- the long leg is
             higher-beta, so a raw spread can be a disguised long-market bet.
  caveats    survivor panel (delisted shorts absent -> understates the short leg); RS ranked inside the liquid panel.

Usage: PYTHONPATH=src .venv/bin/python3 run_rv_spread_test.py > data/studies/logs/rv_spread_test.log
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

import run_precision_tier_control as pc
import run_short_universe_test as su
import run_universe_test as ut
from lib.studies import pattern_test as pt

START, SPLIT, H = "2020-01-01", "2023-01-01", 20
COST, BORROW = 0.0040, 0.005 * H / 252
LONGS, SHORTS = ["INT", "TT"], ["DIST", "INV-TT", "DOWN", "LAGGARD", "CRASH-H"]


def tstat(x: pd.Series) -> float:
    x = x.dropna(); return x.mean() / x.std(ddof=1) * sqrt(len(x)) if len(x) > 2 else np.nan


def main() -> None:
    P, _brk, _p = pc.build()
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    spy = raw[raw.ticker == "SPY"].set_index("date").close.sort_index(); spy.index = pd.to_datetime(spy.index)
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    L = ut.build_masks(P, raw); S = su.build_masks(P, raw, spy)
    C = P.close
    fr = C.shift(-H) / C - 1
    dates = C.index[C.index >= START][::H]; dates = dates[dates <= C.index[-1 - H]]
    spy_fr = (spy.shift(-H) / spy - 1).reindex(dates)
    rows, series = [], {}
    for lg in LONGS:
        for sh in SHORTS:
            lm, sm = fr.where(L[lg]).loc[dates], fr.where(S[sh]).loc[dates]
            ok = (lm.count(axis=1) >= 5) & (sm.count(axis=1) >= 5)
            lr, sr = lm.mean(axis=1)[ok], sm.mean(axis=1)[ok]
            gross = lr - sr; net = gross - COST - BORROW
            x = spy_fr[ok]; X = np.column_stack([np.ones(len(x)), x.values])
            b, *_ = np.linalg.lstsq(X, net.values, rcond=None)
            res = net.values - X @ b; se = np.sqrt(res.var(ddof=2) * np.linalg.inv(X.T @ X)[0, 0])
            yrs = net.groupby(net.index.year).mean()
            h1, h2 = net[net.index < SPLIT].mean(), net[net.index >= SPLIT].mean()
            prim = lg == "INT" and sh == "DIST"
            passed = bool(net.mean() > 0 and tstat(net) >= 3 and h1 > 0 and h2 > 0 and (yrs > 0).sum() >= 5
                          and b[0] > 0 and b[0] / se >= 3)
            rows.append(dict(cell=f"{lg} - {sh}" + (" *PRIMARY*" if prim else ""), periods=int(ok.sum()),
                             long_pct=100 * lr.mean(), short_pct=100 * sr.mean(), gross=100 * gross.mean(),
                             net=100 * net.mean(), t_net=tstat(net), alpha=100 * b[0], alpha_t=b[0] / se,
                             beta=b[1], h1=100 * h1, h2=100 * h2, yrs_pos=f"{(yrs > 0).sum()}/{len(yrs)}",
                             worst=100 * net.min(), passed=passed))
            series[f"{lg}-{sh}"] = net
    R = pd.DataFrame(rows)
    print(f"20-session non-overlapping periods from {START}; costs {COST*1e4:.0f} bp + borrow {BORROW*1e4:.1f} bp "
          f"per period; % per period (dollar-neutral, per $1 long)\n")
    print(R.round(2).to_string(index=False))
    p = series["INT-DIST"]
    print("\nPRIMARY INT - DIST net by year (%/period):")
    print(p.groupby(p.index.year).agg(size="size", mean=lambda s: 100 * s.mean()).round(2).T.to_string())
    ann = (1 + p).prod() ** (252 / H / len(p)) - 1
    print(f"PRIMARY compounded {100*ann:+.1f}%/yr, worst period {100*p.min():+.1f}%, "
          f"periods positive {(p > 0).mean():.0%}")
    R.to_csv(pt.REPO / "data/studies/rv_spread_test_2026-09-24.csv", index=False)
    print(f"\ncells passing: {int(R.passed.sum())} of {len(R)} | wrote data/studies/rv_spread_test_2026-09-24.csv")


if __name__ == "__main__":
    main()
