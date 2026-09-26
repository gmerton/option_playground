#!/usr/bin/env python3
"""
Can the 12-1 momentum sleeve be held as ~20 NAMES? (pre-registered 2026-09-25, before any run; Gabe: yes to a
smaller cut after the live screener showed a 133-name top decile.)

WHY NEW. run_momentum_portfolio.py (same day) tested only fractional buckets: top decile +0.67pp/mo vs the EW universe,
t_NW 2.93 (SUPPORTED near-miss); top quintile +0.42, t 2.64. A fixed-count book has never been run. It isn't the same
rule: the top 20 by RAW score are the most extreme winners (high-vol small caps, biotech), which the literature
says is where momentum is weakest and crashes hardest. So "top 20" could be WORSE than the decile, not just noisier.

DATA     identical to the momentum study: silver.chain_spot_daily (survivorship-free, split-adjusted, >45% jumps cut),
         liquidity = 50-session mean option volume >= 1,000 contracts and px >= $5; formations 2011-01 -> 2026-01;
         delisted names exit at their last close; 10 bp per side on turnover.
SCORE    12-1: close(t-21)/close(t-252) - 1 at each month-end; hold one month, equal weight.
CELLS (M = 3 -> Sidak |t| >= 2.39; the house |t| >= 3 GOVERNS; both halves (2018-01) positive; majority of years)
  PRIMARY T20   the 20 highest scores.
          T30   the 30 highest scores.
          LV20  the 20 names with the LOWEST 126-session realised vol among the top decile (a risk-managed pick that avoids
                the extreme tail; volatility known at formation).
MEASURE  (1) excess vs the EW universe (the study's benchmark), Newey-West lag 3. That is the certification question.
         (2) IMPLEMENTATION question, declared now: each cell MINUS the top decile, monthly, NW t. A cell is an
             ACCEPTABLE way to hold the sleeve if its excess vs EW is > 0 and |t(cell - decile)| < 2 (not
             distinguishable from the decile). A cell with t(cell - decile) <= -2 is WORSE than the decile. Don't
             hold it that way.
DISPERSION (descriptive): 1,000 random 20-name draws from the top decile each month -> the distribution of the
         15-year mean monthly excess. Its 5th-95th percentile is the "which 20 you happen to pick" risk, and shows whether T20 / LV20 sit
         inside it.
READ     the decile itself missed t 3, so no 20-name cell is expected to certify; the realistic outcome is (2). The
         forward lockbox logs the decile regardless; a 20-name variant goes live only if it is ACCEPTABLE.
PRIOR    T20 worse than the decile (extreme-winner tail); LV20 about equal to the decile, with a smaller drawdown.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_momentum_topn.py   (log -> data/studies/logs/momentum_topn.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import run_momentum_portfolio as M

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/momentum_topn.log"
LOOKBACK, SKIP, NDRAW = 252, 21, 1000


def run(C: pd.DataFrame, elig: pd.DataFrame, seed: int = 7) -> tuple[pd.DataFrame, np.ndarray]:
    idx = C.index; Cv = C.values; E = elig.values
    lr = np.log(C).diff()
    vol = lr.rolling(126, min_periods=100).std().values
    last_valid = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                           for j in range(Cv.shape[1])])
    me = [i for i in M.month_ends(idx) if pd.Timestamp(M.START) <= idx[i] <= pd.Timestamp(M.END)]
    rng = np.random.default_rng(seed)
    rows, draws, prev = [], [], {}
    for a, b in zip(me[:-1], me[1:]):
        if a - LOOKBACK < 0:
            continue
        score = Cv[a - SKIP] / Cv[a - LOOKBACK] - 1
        ok = E[a] & np.isfinite(score) & np.isfinite(Cv[a])
        if ok.sum() < 50:
            continue
        names = np.flatnonzero(ok)
        order = names[np.argsort(-score[names])]
        dec = names[score[names] >= np.nanquantile(score[names], 0.9)]
        exit_i = np.minimum(b, last_valid[names])
        r = pd.Series(Cv[exit_i, names] / Cv[a, names] - 1, index=names).replace([np.inf, -np.inf], np.nan)
        dv = dec[np.isfinite(vol[a, dec])]
        books = {"D1": dec, "T20": order[:20], "T30": order[:30], "LV20": dv[np.argsort(vol[a, dv])][:20], "EW": names}
        row = dict(month=idx[b].to_period("M"))
        for k, v in books.items():
            s = set(v); to = 1 - len(s & prev.get(k, set())) / max(len(s), 1)
            row[k] = r.reindex(v).mean() - 2 * M.COST * to
            row[f"to_{k}"] = to; prev[k] = s
        rd = r.reindex(dec).values
        pick = np.array([rng.choice(len(dec), size=min(20, len(dec)), replace=False) for _ in range(NDRAW)])
        draws.append(np.nanmean(rd[pick], axis=1) - 2 * M.COST * row["to_D1"] - row["EW"])   # decile turnover as the cost proxy
        rows.append(row)
    return pd.DataFrame(rows).set_index("month"), np.array(draws)


def main():
    import run_dip_survivorship as DS
    out = ["# 12-1 momentum as a ~20-name book (pre-registration in the docstring)"]
    C, V = DS.adjust_and_clean(DS.pull())
    liq = ((V.rolling(50, min_periods=30).mean() >= M.OPTVOL_MIN) & (C >= M.PX_MIN)).fillna(False)
    P, D = run(C, liq)
    h = P.index < pd.Period(M.SPLIT, "M")
    R = []
    for k in ("D1", "T20", "T30", "LV20"):
        x = (P[k] - P.EW) * 100
        d = (P[k] - P.D1) * 100
        yr = x.groupby(x.index.year).sum()
        cum = (1 + P[k]).cumprod(); dd = (1 - cum / cum.cummax()).max() * 100
        res = dict(cell=k, months=len(x), ret_mo=100 * P[k].mean(), excess=x.mean(), t_nw=M.nw_t(x), h1=x[h].mean(),
                   h2=x[~h].mean(), yrs_pos=f"{(yr > 0).sum()}/{len(yr)}", vs_D1=d.mean() if k != "D1" else np.nan,
                   t_vs_D1=M.nw_t(d) if k != "D1" else np.nan, maxDD=dd, vol_mo=100 * P[k].std(),
                   turnover=P[f"to_{k}"].mean())
        res["PASS"] = bool(res["t_nw"] >= 3 and res["h1"] > 0 and res["h2"] > 0 and (yr > 0).sum() > len(yr) / 2)
        res["ACCEPTABLE"] = bool(k != "D1" and res["excess"] > 0 and abs(res["t_vs_D1"]) < 2)
        res["WORSE"] = bool(k != "D1" and res["t_vs_D1"] <= -2)
        R.append(res)
        out.append(f"\n## {k}{'  <- PRIMARY' if k == 'T20' else ''}: {100 * P[k].mean():+.2f}%/mo, excess vs EW {x.mean():+.2f}pp "
                   f"t_NW {res['t_nw']:+.2f} halves {res['h1']:+.2f}/{res['h2']:+.2f} yrs {res['yrs_pos']} | "
                   + ("" if k == "D1" else f"minus decile {d.mean():+.2f}pp t {res['t_vs_D1']:+.2f} | ")
                   + f"maxDD {dd:.0f}%, monthly sd {100 * P[k].std():.1f}%, turnover {P[f'to_{k}'].mean():.0%}")
        out.append("  excess by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in yr.items()))
    mean_draw = D.mean(axis=0) * 100          # 15-yr mean monthly excess of each random 20-name path
    q = np.percentile(mean_draw, [5, 25, 50, 75, 95])
    out.append(f"\n## DISPERSION: {NDRAW} random 20-name picks from the decile, 15-yr mean monthly excess vs EW: "
               f"p5 {q[0]:+.2f} p25 {q[1]:+.2f} p50 {q[2]:+.2f} p75 {q[3]:+.2f} p95 {q[4]:+.2f}pp; "
               f"share of draws with excess <= 0: {(mean_draw <= 0).mean():.0%}")
    T = pd.DataFrame(R)
    out.append("\n" + T.round(3).to_string(index=False))
    p = T[T.cell == "T20"].iloc[0]
    out.append(f"\nVERDICT (PRIMARY T20): certification {'PASS' if p.PASS else 'fail'}; implementation "
               f"{'ACCEPTABLE' if p.ACCEPTABLE else ('WORSE than the decile' if p.WORSE else 'not acceptable')}. "
               + "Acceptable cells: " + (", ".join(T[T.ACCEPTABLE].cell) or "none"))
    T.to_csv(REPO / "data/studies/momentum_topn_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
