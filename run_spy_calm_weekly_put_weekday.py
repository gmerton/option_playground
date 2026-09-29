#!/usr/bin/env python3
"""
Entry WEEKDAY for the calm-regime SPY 7-DTE put sale (extension of run_spy_calm_weekly_put.py; pre-registered
2026-09-28, committed before any run).

QUESTION (Gabe): does the CERTIFIED-CANDIDATE rule (CALM & dealer GEX > 0, short 7-DTE put, hold to expiry) work when
entered Monday, Tuesday, Wednesday or Thursday instead of Friday?
PRIOR: Friday best -- weekend options are richer (weekend_premium_spy_2026-09-21: realised/implied 0.89 vs 0.95), and a
Friday entry spans two non-trading days.

PRE-REGISTRATION
  Same data, cells, regime flags, fills and excess-over-beta statistic as run_spy_calm_weekly_put.py; entries on each
  weekday separately (7-DTE = expiry nearest 7 in [5, 9]; SPY had only Friday expiries until ~2016, Mon/Wed added
  ~2016-18, daily from 2022 -- each weekday reports the years it covers).
  Cells     weekday x {10-delta, 5-delta}, CALM & GAMMA+.
  PRIMARY   PAIRED vs Friday: for each weekday, (weekday entry excess) - (the same week's Friday entry excess), weeks
            where both qualify, month-clustered t. A weekday is BETTER / WORSE than Friday iff |t| >= 2.8 (Sidak for
            4 weekdays x the 10-delta primary) with both halves (split at the median week of the paired sample) the
            same sign; otherwise EQUIVALENT. 5-delta cells are secondary.
  Also      each weekday's own excess t (does it stand alone?), and the portfolio note: entering on several weekdays
            stacks overlapping positions, so returns do not simply add.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_spy_calm_weekly_put_weekday.py > data/studies/logs/spy_calm_weekly_put_weekday.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
Q = 0.018
DAYS = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri"}


def mclust(x, d):
    df = pd.DataFrame(dict(x=np.asarray(x), m=pd.to_datetime(np.asarray(d)).to_period("M"))).dropna()
    if len(df) < 10:
        return np.nan, np.nan
    mu = df.x.mean(); s = df.groupby("m").x.sum(); n = df.groupby("m").size()
    se = np.sqrt(((s - n * mu) ** 2).sum()) / n.sum()
    return mu, (mu / se if se > 0 else np.nan)


def main():
    import yfinance as yf
    r = yf.download("^IRX", start="2009-12-01", end="2026-04-01", progress=False, auto_adjust=False)["Close"].squeeze() / 100
    r.index = pd.to_datetime(r.index).normalize()
    E = pd.read_parquet("data/cache/spy_leg_surface_entries.parquet")
    E = E[(E.cp == "P") & (E.dtgt == 7) & (~E.stress) & (E.gamma > 0)].copy()
    E["r"] = r.reindex(E.trade_date, method="ffill").values
    E["excess"] = E.bp_n - E.ad * ((E.S_T - E.S_0) / E.S_0 + (Q - E.r) * E.dte / 365) * 1e4
    E["wd"] = E.trade_date.dt.dayofweek
    E["week"] = E.trade_date.dt.to_period("W-FRI")
    rows, paired = [], []
    for dc in (0.10, 0.05):
        X = E[E.dcen == dc]
        fri = X[X.wd == 4].set_index("week").excess
        for wd in range(5):
            g = X[X.wd == wd]
            mu, t = mclust(g.excess, g.trade_date); net, tn = mclust(g.bp_n, g.trade_date)
            rows.append(dict(delta=dc, day=DAYS[wd], n=len(g), years=f"{g.trade_date.dt.year.min()}-{g.trade_date.dt.year.max() % 100}",
                             dte_med=g.dte.median(), net_bp=net, excess_bp=mu, t_excess=t, win=100 * (g.bp_n > 0).mean(),
                             worst=g.bp_n.min(), yrs_pos=(g.groupby(g.trade_date.dt.year).excess.mean() > 0).mean()))
            if wd == 4:
                continue
            p = g.set_index("week").excess
            both = pd.concat([p.rename("d"), fri.rename("f")], axis=1).dropna()
            if len(both) < 10:
                paired.append(dict(delta=dc, day=DAYS[wd], weeks=len(both), note="too few paired weeks")); continue
            diff = both.d - both.f
            wk_dates = both.index.to_timestamp()
            mu_d, t_d = mclust(diff.values, wk_dates)
            med = wk_dates[len(wk_dates) // 2]
            h1, h2 = diff[wk_dates < med].mean(), diff[wk_dates >= med].mean()
            verdict = ("BETTER" if t_d >= 2.8 else "WORSE" if t_d <= -2.8 else "EQUIVALENT") if np.sign(h1) == np.sign(h2) else "EQUIVALENT"
            if abs(t_d) >= 2.8 and np.sign(h1) != np.sign(h2):
                verdict = "EQUIVALENT (halves split)"
            paired.append(dict(delta=dc, day=DAYS[wd], weeks=len(both), span=f"{wk_dates.min().date()}..{wk_dates.max().date()}",
                               day_excess=both.d.mean(), fri_excess=both.f.mean(), diff_bp=mu_d, t=t_d, h1=h1, h2=h2, verdict=verdict))
    print("== each weekday on its own (CALM & GAMMA+), bp of notional per trade ==")
    print(pd.DataFrame(rows).round(2).to_string(index=False))
    print("\n== PRIMARY: paired vs the SAME WEEK's Friday entry (weekday - Friday excess) ==")
    print(pd.DataFrame(paired).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
