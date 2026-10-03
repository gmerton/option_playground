#!/usr/bin/env python3
"""
SIZING the certified 12-1 momentum sleeve: margin leverage x concentration (pre-registered 2026-10-02, before any run;
Gabe: "let's take a look at that" after the ranking refinements came back NULL).

WHAT THIS IS. A sizing study, not an edge test: leverage and concentration create no alpha, they trade drawdown for
growth. So there is no t-bar; the decision rule below is declared in advance instead. It extends the LEAP study's
leverage table (momentum_leap_leverage_2026-09-30.md, LEAP-quotable subset, flat 4% financing) to the FULL sleeve, real
T-bill financing, three book sizes, and a forward bootstrap.

BOOKS (run_momentum_topn.run, chain_spot incl. delisted, formations 2011-01 -> 2026-01, 10 bp/side on turnover)
  D1  top decile (~84 names) = the certified rule
  T30 the 30 highest 12-1 scores
  T20 the 20 highest 12-1 scores (tail-driven: winsorised at p95 its edge falls to t 1.47 -> treat its extra mean with
      suspicion)
LEVERAGE  L in {1.0, 1.25, 1.5, 2.0, 3.0}, reset monthly. Monthly return = L x r_book - (L - 1) x (3-month T-bill +
      1.5%) / 12 (IBKR-like margin rate). r_book already carries 10 bp/side, so costs scale with L.
HISTORY   per book x L: CAGR, vol, Sharpe (vs T-bill), maxDD, worst month, worst 12 months, longest underwater spell.
      Month-end only: intramonth drawdowns are deeper than shown (stated, not modelled).
FORWARD   stationary block bootstrap (mean block 6 months), 10,000 paths of 120 months, joint resampling of the book
      and T-bill months. Two scenarios: AS-IS (historical months) and HAIRCUT (every book's monthly return reduced by
      half the certified excess, 0.33pp/mo, because a t 2.9 in-sample mean overstates the forward mean). Report median
      CAGR, 5th-percentile CAGR, P(10-yr CAGR < 0), P(maxDD > 50%), median maxDD.
KELLY     growth-optimal leverage per book, numerically (max mean log return over the historical months), both scenarios.
DECISION RULE (declared now) recommend the LARGEST (book, L) with, under HAIRCUT: P(maxDD > 50%) <= 10% AND 5th-pct
      10-yr CAGR >= 0. Ties -> the less concentrated book. Answer explicitly whether any cell reaches 100%/yr.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_momentum_sizing.py
       (log -> data/studies/logs/momentum_sizing.log; table data/studies/momentum_sizing_2026-10-02.csv)
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

import run_momentum_portfolio as M

warnings.filterwarnings("ignore")
REPO = M.REPO
LOG = REPO / "data/studies/logs/momentum_sizing.log"
LEVS = [1.0, 1.25, 1.5, 2.0, 3.0]
BOOKS = ["D1", "T30", "T20"]
HAIRCUT = 0.0033
NPATH, HORIZON, BLOCK = 10_000, 120, 6


def tbill(months: pd.PeriodIndex) -> pd.Series:
    import yfinance as yf
    ir = yf.download("^IRX", start="2010-01-01", end="2026-03-01", progress=False)["Close"].squeeze() / 100
    m = ir.groupby(ir.index.to_period("M")).mean()
    return m.reindex(months).ffill().bfill() / 12


def lev(r: np.ndarray, rf: np.ndarray, L: float) -> np.ndarray:
    return L * r - (L - 1) * (rf + 0.015 / 12)


def maxdd(x: np.ndarray) -> float:
    c = np.cumprod(1 + x); return float((1 - c / np.maximum.accumulate(c)).max())


def hist_stats(x: np.ndarray, rf: np.ndarray, months: pd.PeriodIndex) -> dict:
    c = np.cumprod(1 + x); n = len(x)
    roll12 = pd.Series(1 + x).rolling(12).apply(np.prod, raw=True) - 1
    under, best = 0, 0
    pk = np.maximum.accumulate(c)
    for v, p in zip(c, pk):
        under = under + 1 if v < p else 0; best = max(best, under)
    ex = x - rf
    return dict(cagr=c[-1] ** (12 / n) - 1, vol=x.std(ddof=1) * np.sqrt(12), sharpe=ex.mean() / ex.std(ddof=1) * np.sqrt(12),
                maxdd=maxdd(x), worst_mo=x.min(), worst_mo_at=str(months[int(np.argmin(x))]), worst_12m=roll12.min(),
                underwater_mo=best, final=c[-1])


def boot_idx(n: int, rng: np.random.Generator) -> np.ndarray:
    out = np.empty((NPATH, HORIZON), dtype=int)
    for p in range(NPATH):
        i, k = 0, rng.integers(n)
        while i < HORIZON:
            out[p, i] = k; i += 1
            k = rng.integers(n) if rng.random() < 1 / BLOCK else (k + 1) % n
    return out


def main():
    import run_dip_survivorship as DS
    from run_momentum_topn import run
    out = ["# Sizing the 12-1 momentum sleeve: leverage x concentration (pre-registration in the docstring)"]
    C, V = DS.adjust_and_clean(DS.pull())
    liq = ((V.rolling(50, min_periods=30).mean() >= M.OPTVOL_MIN) & (C >= M.PX_MIN)).fillna(False)
    P, _ = run(C, liq)
    rf = tbill(P.index).values
    out.append(f"{len(P)} months {P.index[0]} -> {P.index[-1]}; T-bill mean {12*rf.mean():.2%}/yr; "
               + " | ".join(f"{k} {100*P[k].mean():+.2f}%/mo" for k in BOOKS))
    rng = np.random.default_rng(11)
    I = boot_idx(len(P), rng)
    rows = []
    for scen, hc in (("AS-IS", 0.0), ("HAIRCUT", HAIRCUT)):
        out.append(f"\n## {scen}" + (" (book returns - 0.33pp/mo)" if hc else ""))
        out.append(f"  {'book':4} {'L':>5} | {'CAGR':>6} {'vol':>5} {'Shrp':>5} {'maxDD':>6} {'worst mo':>16} {'worst12':>7} {'uw mo':>5}"
                   f" | boot10y: {'medCAGR':>7} {'p5CAGR':>7} {'P(<0)':>6} {'P(DD>50)':>8} {'medDD':>6}")
        for b in BOOKS:
            r = P[b].values - hc
            grid = np.linspace(0.5, 6, 111)
            kelly = grid[np.argmax([np.mean(np.log1p(lev(r, rf, L))) if (lev(r, rf, L) > -1).all() else -np.inf for L in grid])]
            for L in LEVS:
                x = lev(r, rf, L)
                h = hist_stats(x, rf, P.index)
                bx = lev(r[I], rf[I], L)
                ok = (bx > -1).all(axis=1)
                bc = np.where(ok, np.prod(1 + np.clip(bx, -0.999, None), axis=1) ** (12 / HORIZON) - 1, -1.0)
                c = np.cumprod(1 + np.clip(bx, -0.999, None), axis=1)
                bdd = (1 - c / np.maximum.accumulate(c, axis=1)).max(axis=1)
                row = dict(scenario=scen, book=b, L=L, **h, boot_med_cagr=np.median(bc), boot_p5_cagr=np.percentile(bc, 5),
                           boot_p_neg=(bc < 0).mean(), boot_p_dd50=(bdd > 0.5).mean(), boot_med_dd=np.median(bdd), kelly=kelly)
                rows.append(row)
                out.append(f"  {b:4} {L:5.2f} | {h['cagr']:6.1%} {h['vol']:5.0%} {h['sharpe']:5.2f} {h['maxdd']:6.1%} "
                           f"{h['worst_mo']:7.1%} {h['worst_mo_at']:>8} {h['worst_12m']:7.1%} {h['underwater_mo']:5d} | "
                           f"{row['boot_med_cagr']:7.1%} {row['boot_p5_cagr']:7.1%} {row['boot_p_neg']:6.1%} {row['boot_p_dd50']:8.1%} {row['boot_med_dd']:6.1%}")
            out.append(f"  {b}: growth-optimal (Kelly) leverage on history = {kelly:.2f}x")
    D = pd.DataFrame(rows)
    hc = D[D.scenario == "HAIRCUT"]
    ok = hc[(hc.boot_p_dd50 <= 0.10) & (hc.boot_p5_cagr >= 0)]
    order = {b: i for i, b in enumerate(BOOKS)}
    if len(ok):
        best = ok.assign(o=ok.book.map(order)).sort_values(["L", "o"], ascending=[False, True]).iloc[0]
        out.append(f"\nDECISION RULE -> largest passing cell under HAIRCUT: {best.book} at {best.L:.2f}x "
                   f"(hist CAGR {best.cagr:.1%}, maxDD {best.maxdd:.1%}; boot median {best.boot_med_cagr:.1%}, "
                   f"P(DD>50%) {best.boot_p_dd50:.1%}, p5 CAGR {best.boot_p5_cagr:.1%})")
    else:
        out.append("\nDECISION RULE -> no cell passes under HAIRCUT")
    top = D.loc[D.cagr.idxmax()]
    out.append(f"Highest historical CAGR in the grid: {top.book} {top.L:.2f}x ({top.scenario}) = {top.cagr:.1%}, maxDD {top.maxdd:.1%}. "
               f"100%/yr reached: {'YES' if (D.cagr >= 1).any() else 'NO'}")
    D.to_csv(REPO / "data/studies/momentum_sizing_2026-10-02.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
