#!/usr/bin/env python3
"""
Sector momentum spread: long the strongest SPDR sectors, short the weakest, on a 6-12 MONTH lookback
(pre-registered 2026-09-24, before the first run).

WHY / WHAT IS NEW. The bearish search's last untested direction (short the weak group vs long the strong one).
industry_rotation_detection_study.md (2026-07) already showed 21d / 63d sector RS signals carry no edge on the 11
sector ETFs 2006-2026 ("RS ranking is descriptive, not predictive") -- so a short-lookback version would be a
re-test. The untouched axis is the academic industry-momentum lookback: 6-12 months, skipping the latest month.
Traded on the ETFs themselves, so no stock-to-sector map is needed.

DESIGN
  universe   XLB XLE XLF XLI XLK XLP XLU XLV XLY from 1999-01; XLRE from 2016-01, XLC from 2018-07 (a year after
             listing so a 12-month lookback exists). yfinance auto-adjusted closes = total return.
  signal     at each month-end: return over months t-12..t-1 (skip the latest month). 6-1 as the grid alternative.
  portfolio  long the top K, short the bottom K, equal weight, dollar-neutral, held one month.
  PRIMARY    12-1 lookback, K = 3.
  grid       {6-1, 12-1} x K {2, 3} = 4 cells; Sidak at 5% -> |t| 2.49; the house |t| >= 3 governs.
  costs      20 bp/month (full turnover, 5 bp per side per leg) + 0.25%/yr borrow on the short leg.
  controls   (1) alpha vs SPY: spread regressed on SPY's same-month return, alpha t >= 3.
             (2) RANDOM-RANK NULL: 2,000 permutations shuffling which sectors land long/short each month
                 (same K, same months); p = share of null mean >= observed. Must be < 0.003.
  bar        net mean > 0, t >= 3, alpha t >= 3, permutation p < 0.003, both halves (split 2013-01) positive,
             positive in >= 60% of years.
  bearish    reported, not part of the bar: mean in SPY-down months vs SPY-up months, and 2000-02 / 2008 / 2022.
  caveat     9-11 names: K = 3 is a third of the universe; low breadth -> a noisy spread by construction.

Usage: PYTHONPATH=src .venv/bin/python3 run_sector_momentum_spread.py > data/studies/logs/sector_momentum_spread.log
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

CORE = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
LATE = {"XLRE": "2016-01", "XLC": "2018-07"}
COST, BORROW = 0.0020, 0.0025 / 12
SPLIT, PERMS = "2013-01", 2000
RNG = np.random.default_rng(20260924)


def tstat(x) -> float:
    x = pd.Series(x).dropna(); return x.mean() / x.std(ddof=1) * sqrt(len(x))


def spread_series(lb: int = 12, K: int = 3) -> tuple[pd.Series, pd.Series]:
    """Monthly net spread (month-end index) and SPY monthly return -- the PRIMARY construction, no null. For overlays."""
    px = yf.download(CORE + list(LATE) + ["SPY"], start="1998-12-01", auto_adjust=True, progress=False)["Close"]
    m = px.resample("ME").last()
    m = m[m.index < pd.Timestamp.today().normalize() - pd.offsets.MonthEnd(0)]
    r = m.pct_change(); spy = r.pop("SPY")
    for tk, since in LATE.items():
        r.loc[r.index < pd.Timestamp(since), tk] = np.nan
    sig = ((m.shift(1) / m.shift(lb)) - 1)[r.columns].where(r.notna())
    net = {}
    for i in range(1, len(r)):
        s = sig.iloc[i - 1].dropna()
        if len(s) < 2 * K + 1:
            continue
        o = s.sort_values()
        net[r.index[i]] = r.iloc[i][list(o.index[-K:])].mean() - r.iloc[i][list(o.index[:K])].mean() - COST - BORROW
    net = pd.Series(net).dropna()
    return net, spy


def main() -> None:
    px = yf.download(CORE + list(LATE) + ["SPY"], start="1998-12-01", auto_adjust=True, progress=False)["Close"]
    m = px.resample("ME").last()
    m = m[m.index < pd.Timestamp.today().normalize() - pd.offsets.MonthEnd(0)]   # completed months only
    r = m.pct_change()
    spy = r.pop("SPY")
    for tk, since in LATE.items():
        r.loc[r.index < pd.Timestamp(since), tk] = np.nan
    rows, keep = [], {}
    for lb in (12, 6):
        sig = (m.shift(1) / m.shift(lb)) - 1                      # return t-lb .. t-1: skips the latest month
        sig = sig[r.columns].where(r.notna())
        for K in (3, 2):
            longs, shorts = {}, {}
            net = {}
            for i in range(1, len(r)):
                s = sig.iloc[i - 1].dropna()                      # ranked at the prior month-end
                if len(s) < 2 * K + 1:
                    continue
                o = s.sort_values()
                lo, hi = list(o.index[:K]), list(o.index[-K:])
                nxt = r.iloc[i]
                net[r.index[i]] = nxt[hi].mean() - nxt[lo].mean() - COST - BORROW
                longs[r.index[i]], shorts[r.index[i]] = hi, lo
            net = pd.Series(net).dropna()
            x = spy.reindex(net.index)
            X = np.column_stack([np.ones(len(x)), x.values])
            b, *_ = np.linalg.lstsq(X, net.values, rcond=None)
            res = net.values - X @ b; se = np.sqrt(res.var(ddof=2) * np.linalg.inv(X.T @ X)[0, 0])
            # random-rank null: same months, same K, random sectors long / short
            obs = net.mean(); null = np.empty(PERMS)
            Rv = r.loc[net.index].values
            avail = [np.flatnonzero(sig.iloc[r.index.get_loc(d) - 1].notna().values) for d in net.index]
            for p in range(PERMS):
                v = 0.0
                for row, av in zip(Rv, avail):
                    pick = RNG.permutation(av)
                    v += row[pick[-K:]].mean() - row[pick[:K]].mean()
                null[p] = v / len(avail) - COST - BORROW
            pval = (np.sum(null >= obs) + 1) / (PERMS + 1)
            yrs = net.groupby(net.index.year).sum()
            h1, h2 = net[net.index < SPLIT].mean(), net[net.index >= SPLIT].mean()
            prim = lb == 12 and K == 3
            passed = bool(obs > 0 and tstat(net) >= 3 and b[0] / se >= 3 and pval < 0.003 and h1 > 0 and h2 > 0
                          and (yrs > 0).mean() >= 0.6)
            dn, up = net[x < 0], net[x >= 0]
            rows.append(dict(cell=f"{lb}-1 K{K}" + (" *PRIMARY*" if prim else ""), months=len(net),
                             mean=100 * obs, t=tstat(net), alpha=100 * b[0], alpha_t=b[0] / se, beta=b[1],
                             perm_p=pval, h1=100 * h1, h2=100 * h2, yrs_pos=f"{(yrs > 0).sum()}/{len(yrs)}",
                             spy_down=100 * dn.mean(), spy_up=100 * up.mean(), passed=passed))
            keep[(lb, K)] = net
    R = pd.DataFrame(rows)
    print(f"sector momentum spread, monthly {r.index[1].date()} -> {r.index[-1].date()}; net of {COST*1e4:.0f} bp + "
          f"borrow; % per month\n")
    print(R.round(3).to_string(index=False))
    p = keep[(12, 3)]
    print("\nPRIMARY 12-1 K3, calendar-year sums (%):")
    print((100 * p.groupby(p.index.year).sum()).round(1).to_frame("net").T.to_string())
    for lab, a, z in (("2000-02 bear", "2000-03", "2002-10"), ("2008 GFC", "2007-10", "2009-03"),
                      ("2020 crash", "2020-02", "2020-03"), ("2022 bear", "2022-01", "2022-10")):
        s = p[(p.index >= a) & (p.index <= pd.Timestamp(z) + pd.offsets.MonthEnd(0))]
        sp = spy.reindex(s.index)
        print(f"  {lab:13s} spread {100 * s.sum():+6.1f}%  SPY {100 * ((1 + sp).prod() - 1):+6.1f}%  ({len(s)} months)")
    print(f"\ncells passing: {int(R.passed.sum())} of {len(R)}")
    R.to_csv("data/studies/sector_momentum_spread_2026-09-24.csv", index=False)


if __name__ == "__main__":
    main()
