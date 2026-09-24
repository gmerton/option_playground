#!/usr/bin/env python3
"""
Does ranking cash-secured puts by YIELD across names pick better puts? (2026-09-24, pre-registered here before the run.)

Source claim: OptionsPlay "How to Screen Both Legs of the Wheel" (VSLc-kHxFlw, 2026-08-01) ranks short-put ideas by
annualised yield. It is the put-sale sibling of the credit/width sort, whose cross-sectional half survived
(`premium_to_width_2026-09-22`, ARM A t 3.74; `ivrank_vs_cw_2026-09-22`, within-date zcw t 4.01) on 30d/20d bull
puts. What makes it NEW: the BCI study (`bci_csp_study_2026-09-17.md`) chose each name's strike by a yield TARGET
(0.75%/wk) and tested an IV 30-60% band, but never ranked names against each other by yield at a fixed delta.
⚠ At a fixed delta and tenor, yield is roughly IV x sqrt(T), so this is a cross-sectional sort on absolute IV level
(not IV rank, which is NULL per name).

DATA: `data/cache/bci_csp/trades.parquet` from `run_bci_csp_study.py` (straddle pool, ~326 names, Fridays
2018-01 -> 2026-02, real bid/ask, sold at mid - 25% of spread + $0.0065/share, held to expiry, settled at intrinsic).
Strike rule "30" only (nearest 0.30 delta, so delta is held fixed and yield varies only across names).
  yield  = sellpx / (strike - sellpx)          (return on collateral, the number he ranks)
  csp    = the put's return on collateral, %    excess = csp - stock held at the put's entry delta, %
QUINTILES are formed WITHIN each entry date (dates with >= 20 names only), so the market-wide IV level is removed.

PRIMARY (declared): tenor W (~7 DTE), Q5 - Q1 of EXCESS, one paired difference per entry week, t = mean / se over
  weeks. The question is whether high-yield puts carry premium BEYOND direction, which is what a seller is paid for.
  PASS: t >= 3, same sign in both halves (split 2022-01-01), and no single year supplying the result (report per year).
SECONDARY (exploratory, labelled): csp itself (Q5 - Q1), the full quintile table, tenor M (~28 DTE, month-clustered),
  and whether Q5's excess is positive at all.
One primary cell -> no multiple-testing charge.

Usage: PYTHONPATH=src .venv/bin/python3 run_csp_yield_rank.py   (writes data/studies/logs/csp_yield_rank_2026-09-24.log)
"""
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd

LOG = Path("data/studies/logs/csp_yield_rank_2026-09-24.log")
OUT = Path("data/studies/csp_yield_rank_2026-09-24.csv")
SPLIT = pd.Timestamp("2022-01-01")
lines = []


def P(s=""):
    print(s); lines.append(str(s))


def tstat(s: pd.Series) -> float:
    s = s.dropna()
    return s.mean() / s.std() * np.sqrt(len(s)) if len(s) > 2 else np.nan


t = pd.read_parquet("data/cache/bci_csp/trades.parquet")
t = t[(t.rule == "30") & t.excess.notna() & t.csp.notna()].copy()
t["yld"] = 100 * t.sellpx / (t.strike - t.sellpx)
out = []
for tenor, cl in (("W", "week"), ("M", "month")):
    d = t[t.tenor == tenor].copy()
    n_date = d.groupby("trade_date").ticker.transform("size")
    d = d[n_date >= 20].copy()
    d["q"] = d.groupby("trade_date").yld.transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False) + 1)
    out.append(d[["ticker", "trade_date", "tenor", "yld", "iv", "delta", "csp", "excess", "q", cl]])
    P(f"\n{'#' * 90}\n# tenor {tenor}: {len(d):,} puts, {d.ticker.nunique()} names, {d.trade_date.nunique()} dates, "
      f"{d.trade_date.min().date()} -> {d.trade_date.max().date()}  (clustered by {cl})\n{'#' * 90}")
    tab = d.groupby("q").agg(n=("csp", "size"), yld=("yld", "mean"), iv=("iv", "mean"), csp=("csp", "mean"),
                             csp_med=("csp", "median"), excess=("excess", "mean"), win=("csp", lambda s: 100 * (s > 0).mean()),
                             worst1=("csp", lambda s: s[s <= s.quantile(0.01)].mean()))
    P(tab.round(3).to_string())
    for y in ("excess", "csp"):
        g = d.groupby([cl, "q"])[y].mean().unstack()
        diff = (g[5] - g[1]).dropna()
        first_date = d.groupby(cl).trade_date.min()
        h1 = diff[first_date.reindex(diff.index) < SPLIT]; h2 = diff[first_date.reindex(diff.index) >= SPLIT]
        tag = "PRIMARY" if (tenor == "W" and y == "excess") else "secondary"
        P(f"\n[{tag}] Q5 - Q1 {y}: {diff.mean():+.3f}pp  t {tstat(diff):+.2f}  (n {len(diff)} {cl}s)  "
          f"halves {h1.mean():+.3f} (t {tstat(h1):+.2f}) / {h2.mean():+.3f} (t {tstat(h2):+.2f})")
        yr = diff.groupby(first_date.reindex(diff.index).dt.year)
        P("  by year: " + "  ".join(f"{k} {v.mean():+.2f}" for k, v in yr))
        if tag == "PRIMARY":
            ok = tstat(diff) >= 3 and np.sign(h1.mean()) == np.sign(h2.mean()) == 1
            P(f"  PRE-REGISTERED PASS: {'YES' if ok else 'NO'}")
    q5 = d[d.q == 5].groupby(cl).excess.mean()
    P(f"\nQ5 excess on its own: {q5.mean():+.3f}pp  t {tstat(q5):+.2f}")
pd.concat(out).to_csv(OUT, index=False)
LOG.parent.mkdir(parents=True, exist_ok=True); LOG.write_text("\n".join(lines) + "\n")
print(f"\n-> {LOG}\n-> {OUT}")
