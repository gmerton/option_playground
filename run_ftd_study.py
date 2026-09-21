#!/usr/bin/env python3
"""
Does O'Neil's Follow-Through Day time the turn?

Claim (Ariel Hernandez on TraderLion 2026-09-13, citing O'Neil/Webster): after a correction, an FTD
confirms a new uptrend, and you should be ~30% invested within a day or two of it. Our own regime
work says trailing regime state has no persistence and that regime management is fixed small sizing
rather than a switch -- an FTD is a specific, dated, rule-based switch, so it is a sharp test of that.

FTD as coded (the canonical rules):
  * Correction: index closes below (1 - DD) x its 252-day rolling max close.
  * Rally attempt: day 1 is the session holding the lowest close so far in the correction. A new
    lower close RESETS the count to 1 -- that is the undercut rule.
  * FTD: day 4 or later of the attempt, index closes up >= THRESH, on volume above the prior session.
  * Only the FIRST FTD of a correction is the signal (it confirms the turn); `--all-ftd` scores every one.

Two comparisons, because they answer different questions:
  1. vs OTHER DAYS IN THE SAME CORRECTION -- did the FTD time the bottom, given you were already in a
     drawdown and looking for the turn? This is the claim.
  2. vs ALL DAYS unconditional -- did it beat simply being invested? This is the benchmark that matters
     for a desk that is otherwise long anyway.

Significance is a bootstrap, not a t-test: forward windows overlap heavily and there are only a few
dozen FTDs. The null draws the same number of days from the same eligible pool 10,000 times, so it
inherits the same overlap structure.

Usage: PYTHONPATH=src .venv/bin/python3 run_ftd_study.py > data/studies/ftd_2026-09-20.log
"""
from __future__ import annotations
import argparse, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); pd.set_option("display.width", 200)

RNG = np.random.default_rng(20260920)
HORIZONS = [5, 10, 21, 63]


def find_ftds(df: pd.DataFrame, dd: float, thresh: float, min_day: int = 4):
    """Return (ftd_mask, in_correction_mask, attempt_day)."""
    c, v = df.Close.values, df.Volume.values
    n = len(c)
    peak = pd.Series(c).rolling(252, min_periods=60).max().values
    incorr = c < peak * (1 - dd)
    chg = np.concatenate([[0.0], c[1:] / c[:-1] - 1])
    volup = np.concatenate([[False], v[1:] > v[:-1]])

    day = np.zeros(n, dtype=int)
    ftd = np.zeros(n, dtype=bool)
    first = np.zeros(n, dtype=bool)
    low = np.inf; counting = False; seen_ftd = False
    for i in range(n):
        if not incorr[i]:
            counting = False; low = np.inf; seen_ftd = False; continue
        if not counting or c[i] < low:      # new correction, or an undercut: attempt resets
            low = c[i]; day[i] = 1; counting = True; continue
        day[i] = day[i - 1] + 1 if day[i - 1] else 1
        if day[i] >= min_day and chg[i] >= thresh and volup[i]:
            ftd[i] = True
            if not seen_ftd:
                first[i] = True; seen_ftd = True
    return ftd, first, incorr, day


def fwd(df: pd.DataFrame, idx: np.ndarray, h: int) -> np.ndarray:
    c = df.Close.values; n = len(c)
    ok = idx[idx + h < n]
    return c[ok + h] / c[ok] - 1


def boot_p(df, sig_idx, pool_idx, h, iters=10000):
    """P(random draw from the pool beats the signal's mean) -- one-sided."""
    obs = fwd(df, sig_idx, h)
    if len(obs) == 0: return np.nan, np.nan, np.nan
    om = obs.mean()
    pool = fwd(df, pool_idx, h)
    if len(pool) < 10: return om, np.nan, np.nan
    k = len(obs)
    draws = RNG.choice(pool, size=(iters, k), replace=True).mean(axis=1)
    return om, pool.mean(), float((draws >= om).mean())


def report(name, df, sig, pool_mask, label_pool, tag):
    idx = np.flatnonzero(sig)
    pool = np.flatnonzero(pool_mask & ~sig)
    rows = []
    for h in HORIZONS:
        om, pm, p = boot_p(df, idx, pool, h)
        rows.append(dict(horizon=f"+{h}d", n=int((idx + h < len(df)).sum()),
                         ftd_mean=100 * om if om == om else np.nan,
                         pool_mean=100 * pm if pm == pm else np.nan,
                         edge_pp=100 * (om - pm) if pm == pm else np.nan,
                         p_boot=p))
    t = pd.DataFrame(rows)
    print(f"\n--- {name}: FTD vs {label_pool} ({tag}) ---")
    print(t.round(2).to_string(index=False))
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-ftd", action="store_true", help="score every FTD, not just the first per correction")
    a = ap.parse_args()
    raw = pd.read_parquet("data/cache/index_daily_ftd.parquet")

    for tk in ("SPY", "QQQ", "IWM"):
        df = raw[raw.ticker == tk].sort_index()
        print(f"\n{'='*78}\n{tk}  {df.index.min().date()} -> {df.index.max().date()}  ({len(df):,} sessions)")
        for dd, th in ((0.05, 0.010), (0.08, 0.010), (0.05, 0.017), (0.10, 0.010)):
            ftd, first, incorr, day = find_ftds(df, dd, th)
            sig = ftd if a.all_ftd else first
            if sig.sum() < 8:
                print(f"\n  [DD>={dd:.0%}, up>={th:.1%}] only {sig.sum()} signals -- skipped"); continue
            print(f"\n  [DD>={dd:.0%}, up>={th:.1%}]  {sig.sum()} {'FTDs' if a.all_ftd else 'first-FTDs'}"
                  f" | {incorr.sum():,} correction sessions ({incorr.mean():.0%} of history)")
            report(tk, df, sig, incorr, "other correction days", f"DD{dd:.0%}/{th:.1%}")
            report(tk, df, sig, np.ones(len(df), bool), "ALL days (being invested)", f"DD{dd:.0%}/{th:.1%}")
            # Does the RULE earn its keep? Naive arm = the first day >= min_day of the rally attempt,
            # ignoring the up-% and volume conditions entirely. If FTD does not beat just waiting four
            # days, the up-% and volume gates are decoration and the signal is "time since the low".
            naive = np.zeros(len(df), bool)
            seen = False
            for i in range(len(df)):
                if not incorr[i]: seen = False; continue
                if day[i] == 1: seen = False
                if day[i] >= 4 and not seen: naive[i] = True; seen = True
            print(f"    naive 'day-4 of the attempt' arm: {naive.sum()} signals")
            rows = []
            for h in HORIZONS:
                f_ = fwd(df, np.flatnonzero(sig), h); n_ = fwd(df, np.flatnonzero(naive), h)
                rows.append(dict(horizon=f"+{h}d", ftd=100*f_.mean() if len(f_) else np.nan,
                                 naive_day4=100*n_.mean() if len(n_) else np.nan,
                                 rule_edge_pp=100*(f_.mean()-n_.mean()) if len(f_) and len(n_) else np.nan))
            print(f"\n--- {tk}: does the RULE beat just waiting 4 days? (DD{dd:.0%}/{th:.1%}) ---")
            print(pd.DataFrame(rows).round(2).to_string(index=False))
    print("\n\nBar: to justify a regime switch, the FTD must beat OTHER CORRECTION DAYS (it timed the turn)")
    print("AND beat ALL DAYS (it beat simply being invested), with a bootstrap p well under 0.05.")


if __name__ == "__main__":
    main()
