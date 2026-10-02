#!/usr/bin/env python3
"""
IS A DIVERSIFIED BASKET OF BULL PUT SPREADS SMOOTHER THAN THE SAME EXPOSURE IN SPY? (pre-registered 2026-10-01,
before any scoring; Gabe: "allocate part of our portfolio to the smooth, retail friendly, strategy while we wait for
A+ setups ... a diversified basket of put spreads" -> "yes").

WHY. Every put-spread test in the ledger scored MEAN return, and each came out as delta exposure minus costs
(single-name 30/20 vs own delta +$7/contract NS; OptionsPlay spec vs delta-matched stock -2.68pp t -2.21; ETF roster put
leg fails after costs; paid-to-wait vs stock -9.1pp t -3.21). The tastylive case is really about SMOOTHNESS (win rate,
steady months). Never tested: does a diversified basket give a better risk-adjusted equity curve than holding the
same market exposure? Sharpe is scale-free, so it is the right yardstick for "smoother at the same exposure".

DATA  data/studies/premium_to_width_2026-09-22.csv: the 20-name Friday chain study (options_daily_v3, real bid/ask
      fills = short bid - long ask - $0.0065/leg x2; RAW spot recovered from the chain; held to expiry), 2018-01-05 ->
      2026-01-23, 395 Fridays, every spread 28 DTE. Names: AAPL AMD AMZN AVGO COST CRM GLD GOOGL IWM JPM META MSFT NFLX
      NVDA QQQ SMH SPY TSLA WMT XOM. Structure: 30-delta short / 20-delta long put (wing == 0.20 rows).
      ⚠ The chain cache that built it is gone, so entry deltas are NOMINAL (0.30 - 0.20 = 0.10 per share, the
      selection tolerance was +/-0.06). ⚠ Today's mega-cap list: survivor bias flatters every long-exposure arm alike.
PORTFOLIO each Friday open one spread per available name, each sized to the same max loss (1 risk unit = width -
      credit). Four weekly cohorts overlap (28 DTE), so committed capital = 4 cohorts of risk. Cohort P&L is realised
      at its expiry; weekly portfolio return = mean cohort ROC / 4; monthly = sum of the weeks expiring that month.
      Cash collateral earns the same T-bill rate in every arm, so interest is left out of all of them.
ARMS
  A   BASKET: all names, equal max loss.                                     <- the strategy
  T5  TOP-5 by credit/width each Friday (the OptionsPlay ranking, which passed as a ranking, t 3.74).
BENCHMARKS (same dates, same risk unit, same 28-day windows)
  B2  SPY at the basket's DOLLAR DELTA: per spread, 0.10 x S / SPY_S shares of SPY, held entry -> expiry, 5 bp/side.
      "What you would do instead."                                           <- primary benchmark
  B1  the SAME NAME at the spread's delta: 0.10 shares, held entry -> expiry, 5 bp/side (holds names fixed).
PRIMARY  Sharpe(A monthly) - Sharpe(B2 monthly) (annualised). Stationary block bootstrap on paired months (mean block
         6 months, 10,000 draws, seed 20261001). PASS = the 95% interval lies above 0.
SECONDARY (2; Bonferroni 98.3% intervals)  S1 A vs B1   S2 T5 vs B2.
REPORTED  mean monthly return, vol, max drawdown, worst month, monthly CVaR 5%, % months positive, for every arm;
          drawdown with B2 rescaled to A's volatility (smoothness at equal risk); Feb-Mar 2020 and 2022 by month.
VERDICT  PASS -> a smoothness case exists for the parking-lot sleeve; FAIL -> the same exposure in SPY is at least as
         smooth, and the calm weekly put + T-bills is the better parking lot.
Local, seconds.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path("data/studies/premium_to_width_2026-09-22.csv")
LOG = Path("data/studies/logs/putspread_basket_smoothness.log")
SEED, NBOOT, BLOCK = 20261001, 10_000, 6
DELTA, STK_COST = 0.10, 0.0005


def monthly(df: pd.DataFrame, col: str) -> pd.Series:
    wk = df.groupby("expiry")[col].mean() / 4.0                # one cohort of 4 overlapping
    return wk.groupby(wk.index.to_period("M")).sum()


def stats(m: pd.Series) -> dict:
    eq = (1 + m).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    q = m.quantile(0.05)
    return dict(mean=m.mean(), vol=m.std(ddof=1), sharpe=m.mean() / m.std(ddof=1) * np.sqrt(12), maxdd=dd,
                worst=m.min(), cvar5=m[m <= q].mean(), pos=(m > 0).mean())


def sharpe(x: np.ndarray) -> float:
    return x.mean() / x.std(ddof=1) * np.sqrt(12)


def boot_diff(a: pd.Series, b: pd.Series, level: float) -> tuple[float, float, float]:
    j = a.index.intersection(b.index)
    X, Y = a.loc[j].values, b.loc[j].values
    n, rng, d = len(j), np.random.default_rng(SEED), []
    for _ in range(NBOOT):
        idx, i = [], rng.integers(n)
        while len(idx) < n:                                     # stationary bootstrap
            idx.append(i)
            i = rng.integers(n) if rng.random() < 1 / BLOCK else (i + 1) % n
        idx = np.array(idx)
        d.append(sharpe(X[idx]) - sharpe(Y[idx]))
    lo, hi = np.percentile(d, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return sharpe(X) - sharpe(Y), lo, hi


def main() -> None:
    t = pd.read_csv(SRC, parse_dates=["date", "expiry"])
    t = t[t.wing == 0.20].copy()
    spy = t[t.sym == "SPY"].set_index("date")[["S", "ST"]].rename(columns={"S": "spyS", "ST": "spyT"})
    t = t.join(spy, on="date").dropna(subset=["spyS", "spyT"])
    risk = t.width - t.credit
    t["A"] = t.roc
    t["B1"] = (DELTA * (t.ST - t.S) - 2 * STK_COST * DELTA * t.S) / risk
    sh = DELTA * t.S / t.spyS
    t["B2"] = (sh * (t.spyT - t.spyS) - 2 * STK_COST * sh * t.spyS) / risk
    t["rk"] = t.groupby("date").cw.rank(ascending=False, method="first")
    T5 = t[t.rk <= 5]

    M = pd.DataFrame({"A": monthly(t, "A"), "T5": monthly(T5, "A"), "B1": monthly(t, "B1"), "B2": monthly(t, "B2")}).dropna()
    out = ["# Put-spread basket smoothness vs the same exposure (pre-registered 2026-10-01); see docstring",
           f"{len(t):,} spreads, {t.sym.nunique()} names, {t.date.nunique()} Fridays, {len(M)} months "
           f"{M.index.min()} -> {M.index.max()}; returns are on committed max-loss capital", ""]
    S = {k: stats(M[k]) for k in M}
    out.append(f"{'arm':4s} {'mean/mo':>8s} {'vol/mo':>8s} {'Sharpe':>7s} {'maxDD':>8s} {'worst mo':>9s} {'CVaR5':>8s} {'% mo +':>7s}")
    for k, s in S.items():
        out.append(f"{k:4s} {100*s['mean']:+7.2f}% {100*s['vol']:7.2f}% {s['sharpe']:+7.2f} {100*s['maxdd']:+7.1f}% "
                   f"{100*s['worst']:+8.1f}% {100*s['cvar5']:+7.1f}% {100*s['pos']:6.0f}%")
    k = M.A.std() / M.B2.std()
    b2s = stats(M.B2 * k)
    out.append(f"B2 rescaled to A's vol (x{k:.2f}): mean {100*b2s['mean']:+.2f}%/mo, maxDD {100*b2s['maxdd']:+.1f}%, "
               f"worst {100*b2s['worst']:+.1f}%, CVaR5 {100*b2s['cvar5']:+.1f}%")
    d, lo, hi = boot_diff(M.A, M.B2, 0.95)
    out.append(f"\n## PRIMARY Sharpe(A) - Sharpe(B2): {d:+.2f}, 95% block-bootstrap [{lo:+.2f}, {hi:+.2f}] -> "
               f"{'PASS' if lo > 0 else 'FAIL'}")
    for lab, a, b in [("S1 A vs B1 (same names at delta)", "A", "B1"), ("S2 T5 vs B2", "T5", "B2")]:
        d, lo, hi = boot_diff(M[a], M[b], 0.983)
        out.append(f"  {lab:34s} {d:+.2f}, 98.3% [{lo:+.2f}, {hi:+.2f}]")
    out.append("\n## crash months")
    for per in ["2020-02", "2020-03", "2022-05", "2022-06", "2022-09"]:
        p = pd.Period(per, "M")
        if p in M.index:
            out.append(f"  {per}: " + "  ".join(f"{c} {100*M.at[p, c]:+.1f}%" for c in M.columns))
    out.append("\n## by year (sum of monthly returns)")
    y = M.groupby(M.index.year).sum()
    for yr, r in y.iterrows():
        out.append(f"  {yr}: " + "  ".join(f"{c} {100*r[c]:+.1f}%" for c in M.columns))
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
