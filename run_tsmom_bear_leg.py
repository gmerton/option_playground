#!/usr/bin/env python3
"""
Time-series momentum (trend-following) as the book's BEAR LEG (pre-registered 2026-09-25, before the run)

WHY. The book is long-only in effect. Every single-name short has failed (weak names drift UP; short-universe
test 0/10), tail puts bleed (cheap-convexity NULL), and a plain SPY short cuts no drawdown. The one genuine hedge
found so far, the sector-momentum 12-1 sleeve (sector_overlay_test 2026-09-24), pays in 2008/2020/2022 but LOST
in 2000-02 and costs Sharpe. NEW AXIS (not in TEST_INDEX): trend-following on the ASSET's OWN past return --
hold a short / be flat only while its trend is down (Faber 10-month SMA; Moskowitz-Ooi-Pedersen 2012 TSMOM
"crisis alpha"). Target: slow bear markets (2000-02, 2008, 2022), which is where the sector sleeve failed.

DESIGN (monthly; signal on the month-end close, position held the NEXT month -- no lookahead)
  data      yfinance adjusted closes (total return). Long-history proxies so 2000-02 is in-sample:
            VFINX (S&P 500), VGTSX (intl equity, 1996+), VUSTX (long Treasury), VFITX (intermediate Treasury),
            then GLD (2004+), DBC (2006+), UUP (2007+) as they list. SPY / QQQ / IWM for family A.
  FAMILY B (PRIMARY) -- multi-asset TSMOM: each asset long if its trailing 12-month return > 0, else short;
            inverse-vol weights (trailing 63-day daily vol at the month-end), gross 1. Assets enter once they
            have 13 months of history. Standalone window 1998-01 -> 2026-08.
  FAMILY A -- equity short-or-FLAT (the pure bear leg): short the index when the signal is down, flat otherwise.
            {SPY, QQQ, IWM} x {close < 10-month SMA, 12-month return < 0} = 6 cells.
  M = 7 cells. Pass threshold = max(3, Sidak(7)) = |t| >= 3, both halves same sign, per-year shown.
  costs     5 bp per side per unit of turnover + 0.25%/yr borrow on short exposure; flat earns 0 (no T-bill
            credit -- conservative for family A).
  CONTROLS  (declared now)
            B: 2,000-permutation null -- the same assets, weights and costs with each month's signal vector
               drawn from another month (keeps the long/short mix, breaks the timing).
            A: a same-vol ALWAYS-SHORT of the same index (is the timing worth anything beyond being short?)
               and beta: net alpha vs the index.
            Crisis payoffs vs a beta-equivalent index short (beta x index return), per episode:
            2000-03 -> 2002-09, 2007-11 -> 2009-02, 2020-02 -> 2020-03, 2022-01 -> 2022-10.
  OVERLAY   exactly as sector_overlay_test: run_put_overlay_study.book_series() (straddle + bull put + breakout,
            2018-04 -> 2026-02) and the no-straddle book; sleeve at 25 / 50 / 100% of book vol, PRIMARY 50%.
            Same controls: DE-MEANED sleeve and a same-vol SPY short.
  BAR       RETURN EDGE: a cell certifies only at |t| >= 3 with both halves positive.
            BEAR LEG (the question asked): PRIMARY B is a CANDIDATE only if (i) its net mean >= 0 standalone,
            (ii) it is positive in >= 3 of the 4 crisis episodes AND beats the beta-equivalent short in them on
            aggregate, and (iii) at 50% on BOTH books: maxDD falls, Sharpe does not fall, mean in the book's
            10 worst months > 0, the DE-MEANED sleeve still cuts maxDD, and it beats the SPY short on maxDD.
            ~95 overlay months and 2 stress episodes: a screen for a forward test, never an adoption.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_tsmom_bear_leg.py > data/studies/logs/tsmom_bear_leg.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

B_ASSETS = ["VFINX", "VGTSX", "VUSTX", "VFITX", "GLD", "DBC", "UUP"]
A_INDEX = ["SPY", "QQQ", "IWM"]
SIDE_COST, BORROW = 0.0005, 0.0025 / 12
EPISODES = {"2000-02": ("2000-03", "2002-09"), "2008 GFC": ("2007-11", "2009-02"),
            "2020 crash": ("2020-02", "2020-03"), "2022 bear": ("2022-01", "2022-10")}
START, END = "1998-01", "2026-08"
M_CELLS = 7


def tstat(x: pd.Series) -> float:
    x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    px = yf.download(B_ASSETS + A_INDEX, start="1990-01-01", auto_adjust=True, progress=False)["Close"]
    return px, px.resample("ME").last()


def book_returns(w: pd.DataFrame, r: pd.DataFrame) -> pd.Series:
    """w = weights decided at month-end t (rows), applied to month t+1's return."""
    w = w.fillna(0.0); wl = w.shift(1).fillna(0.0)
    gross = (wl * r).sum(axis=1)
    turn = (w - wl).abs().sum(axis=1).shift(1).fillna(0.0)
    short = (-wl.clip(upper=0)).sum(axis=1)
    return gross - SIDE_COST * turn - BORROW * short


def family_b(px: pd.DataFrame, mo: pd.DataFrame, sig_override: pd.DataFrame | None = None) -> pd.Series:
    m = mo[B_ASSETS]; r = m.pct_change()
    r12 = m / m.shift(12) - 1
    sig = np.sign(r12).where(r12.notna())
    if sig_override is not None: sig = sig_override
    vol = px[B_ASSETS].pct_change().rolling(63).std().resample("ME").last() * np.sqrt(252)
    iv = (1 / vol).where(sig.notna())
    w = sig * iv.div(iv.sum(axis=1), axis=0)
    return book_returns(w, r)


def family_a(mo: pd.DataFrame, tk: str, rule: str) -> pd.Series:
    c = mo[[tk]]; r = c.pct_change()
    down = (c < c.rolling(10).mean()) if rule == "sma10" else (c / c.shift(12) - 1 < 0)
    valid = c.rolling(10 if rule == "sma10" else 13).count() >= (10 if rule == "sma10" else 13)
    w = (-down.astype(float)).where(valid)
    return book_returns(w, r)


def window(s: pd.Series) -> pd.Series:
    s = s.copy(); s.index = s.index.to_period("M"); return s.loc[START:END]


def describe(name: str, s: pd.Series, spy: pd.Series) -> dict:
    s = s.dropna(); h = len(s) // 2; sp = spy.reindex(s.index)
    beta = np.cov(s, sp)[0, 1] / sp.var()
    ep = {}
    for k, (a, b) in EPISODES.items():
        seg = s.loc[a:b]
        ep[k] = 100 * seg.sum() if len(seg) else np.nan
        ep[k + " betaSh"] = 100 * (beta * sp.loc[a:b]).sum() if len(seg) else np.nan
    return dict(cell=name, start=str(s.index[0]), n=len(s), mean=100 * s.mean(), t=tstat(s),
                h1=100 * s.iloc[:h].mean(), h2=100 * s.iloc[h:].mean(), beta=beta,
                alpha=100 * (s - beta * sp).mean(), t_alpha=tstat(s - beta * sp),
                yrs_pos=f"{(s.groupby(s.index.year).sum() > 0).sum()}/{s.index.year.nunique()}", **ep)


def main() -> None:
    px, mo = load()
    spy = window(mo["VFINX"].pct_change())  # S&P total return from 1990 for beta / crisis comparisons
    cells = {"B TSMOM multi-asset *P*": window(family_b(px, mo))}
    for tk in A_INDEX:
        for rule in ("sma10", "r12"):
            cells[f"A {tk} short-or-flat {rule}"] = window(family_a(mo, tk, rule))
    print(f"TSMOM bear leg -- monthly, net of {SIDE_COST*1e4:.0f} bp/side + {BORROW*12*100:.2f}%/yr borrow; "
          f"window {START} -> {END}; M = {M_CELLS}, pass |t| >= 3 + both halves > 0\n")
    D = pd.DataFrame([describe(k, v, spy) for k, v in cells.items()])
    cols = ["cell", "start", "n", "mean", "t", "h1", "h2", "beta", "alpha", "t_alpha", "yrs_pos"]
    print("STANDALONE (% per month)"); print(D[cols].round(2).to_string(index=False))
    ecols = ["cell"] + [c for k in EPISODES for c in (k, k + " betaSh")]
    print("\nCRISIS EPISODES (cumulative %, sleeve vs the beta-equivalent S&P short 'betaSh')")
    print(D[ecols].round(1).to_string(index=False))

    # same-vol ALWAYS-SHORT control for family A
    print("\nFAMILY A vs a same-vol ALWAYS-SHORT of the same index (mean %/mo, maxDD % of the cum sum)")
    for tk in A_INDEX:
        alw = window(-mo[tk].pct_change() - BORROW).dropna()
        for rule in ("sma10", "r12"):
            s = cells[f"A {tk} short-or-flat {rule}"].dropna(); a = alw.reindex(s.index)
            a = a * s.std() / a.std()
            dd = lambda x: (x.cumsum().cummax() - x.cumsum()).max() * 100
            print(f"  {tk:4s} {rule:6s} timed {100*s.mean():+.2f} (dd {dd(s):5.1f})   always-short {100*a.mean():+.2f} "
                  f"(dd {dd(a):5.1f})   diff t {tstat(s - a):+.2f}")

    # permutation null for the primary
    rng = np.random.default_rng(20260925)
    m = mo[B_ASSETS]; r12 = m / m.shift(12) - 1; sig = np.sign(r12).where(r12.notna())
    months = sig.index[sig.notna().any(axis=1)]
    real = cells["B TSMOM multi-asset *P*"].mean()
    null = []
    for _ in range(2000):
        perm = sig.copy()
        src = rng.choice(months, size=len(months))
        vals = sig.loc[src].values
        perm.loc[months] = np.where(sig.loc[months].notna().values, vals, np.nan)
        perm = perm.where(sig.notna())
        null.append(window(family_b(px, mo, perm)).mean())
    null = np.array(null)
    p_perm = (null >= real).mean()
    print(f"\nPRIMARY permutation null (2,000 shuffles of the signal month): real {100*real:+.3f}%/mo, "
          f"null mean {100*null.mean():+.3f}, 95th pct {100*np.percentile(null,95):+.3f} -> p {p_perm:.3f}")

    P = cells["B TSMOM multi-asset *P*"].dropna()
    print("\nPRIMARY by year (% sum):")
    print((100 * P.groupby(P.index.year).sum()).round(1).to_frame("B").T.to_string())

    # ---- book overlay, scored exactly like sector_overlay_test ----
    import run_put_overlay_study as po
    from run_sector_overlay_test import score
    Bk = po.book_series()
    sl, sp = 100 * P, 100 * spy
    idx = Bk.index.intersection(sl.index)
    Bk, sl, sp = Bk.loc[idx], sl.loc[idx], sp.loc[idx]
    z = Bk[["bullput", "breakout"]] / Bk[["bullput", "breakout"]].std()
    nb = z.sum(axis=1); nb = nb / nb.std() * po.BOOK_VOL
    print(f"\nOVERLAY window {idx.min()} -> {idx.max()} ({len(idx)} months); sleeve mean {sl.mean():+.2f}%/mo, "
          f"corr: book {sl.corr(Bk.book):+.2f}, no-straddle {sl.corr(nb):+.2f}, S&P {sl.corr(sp):+.2f}")
    dm = sl - sl.mean(); parts = []
    for lab, bk in (("full book", Bk.book), ("no-straddle", nb)):
        parts += [score(bk, sl, lab, "TSMOM"), score(bk, dm, lab, "  de-meaned"), score(bk, -sp, lab, "  SPY short (control)")]
    R = pd.concat(parts, ignore_index=True)
    R = R[~((R["size"] == "none") & (R.sleeve != "TSMOM"))]
    print(R[["book", "sleeve", "size", "mean", "sharpe", "dSharpe", "maxDD", "dDD", "worst", "worst3", "y2020", "y2022"]]
          .round(2).to_string(index=False))
    ov = {}
    for lab, bk in (("full book", Bk.book), ("no-straddle", nb)):
        w = bk.nsmallest(10).index
        g = lambda kind: R[(R.book == lab) & (R.sleeve.str.strip() == kind) & R["size"].str.contains(r"\*P\*")].iloc[0]
        s, d, c = g("TSMOM"), g("de-meaned"), g("SPY short (control)")
        worst = sl.loc[w].mean()
        print(f"{lab}: TSMOM mean in the book's 10 worst months {worst:+.2f}% vs all {sl.mean():+.2f}%")
        ov[lab] = bool(s.dDD < 0 and s.dSharpe >= 0 and worst > 0 and d.dDD < 0 and s.maxDD < c.maxDD)

    # ---- verdict per the pre-registered bar ----
    Pd = D.iloc[0]
    eps = [k for k in EPISODES if not np.isnan(Pd[k])]
    n_pos = sum(Pd[k] > 0 for k in eps)
    beat = sum(Pd[k] for k in eps) > sum(Pd[k + " betaSh"] for k in eps)
    crit = {"(i) mean >= 0": Pd["mean"] >= 0, f"(ii) crisis +{n_pos}/{len(eps)} & beats beta-short": n_pos >= 3 and beat,
            "(iii) overlay full": ov["full book"], "(iii) overlay no-straddle": ov["no-straddle"]}
    print("\nBEAR-LEG criteria (PRIMARY):", {k: bool(v) for k, v in crit.items()},
          "->", "CANDIDATE for a forward test" if all(crit.values()) else "not a candidate")
    cert = D[(D.t.abs() >= 3) & (np.sign(D.h1) == np.sign(D.h2))]
    print("RETURN-EDGE certifications (|t|>=3, halves agree):", list(cert.cell) or "none")
    D.to_csv("data/studies/tsmom_bear_leg_2026-09-25.csv", index=False)
    R.to_csv("data/studies/tsmom_bear_leg_overlay_2026-09-25.csv", index=False)


if __name__ == "__main__":
    main()
