#!/usr/bin/env python3
"""
LET WINNERS RUN: hold a momentum name while it stays in the top quintile instead of rotating monthly
(pre-registered 2026-09-25, before any run; Gabe: "our main goal is to be massively profitable like Luk and Qullamaggie").

WHY NEW. Every momentum run so far (run_momentum_portfolio.py, _topn.py, _residual_frog.py) rebalances to the fresh top
names each month, so a monster that slips from rank 5 to rank 40 is sold. The traders' rule is the opposite: ride the
leader until it stops leading. The edge here lives in a few extreme, jumpy winners (winsorised at p95 even raw 12-1 goes
to t -0.64), so how long those winners are held is the lever the ledger has not touched. A buffer/hysteresis rule is the
systematic version.

DATA     identical to run_momentum_portfolio.py: silver.chain_spot_daily (survivorship-free, split-adjusted, >45% jumps
         cut), eligibility = 50-session mean option volume >= 1,000 and px >= $5, formations 2011-01 -> 2026-01, 12-1
         score close(t-21)/close(t-252) - 1, delisted names exit at their last close, 10 bp per side on turnover, equal
         weight at each rebalance.
BOOKS
  T20     plain: the top 20 by score each month (the reference; run_momentum_topn.py: +1.22pp/mo vs EW, t 2.68)
  T20-B   buffer: keep each held name while it is still eligible AND ranked inside the top QUINTILE; fill empty slots
          with the highest-ranked names not held, back to 20
  D1      plain: the top decile (reference, t 2.93)
  D1-B    buffer: keep a held name while it is eligible and in the top quintile; refill with the highest-ranked names
          not held, back to the decile count
CELLS (M = 2 -> Sidak |t| >= 2.24 on the improvement; the house |t| >= 3 GOVERNS certification)
  PRIMARY  T20-B minus T20, monthly, Newey-West lag 3: BETTER needs t >= 2.24, both halves (2018-01) > 0 and a
           majority of years > 0.
           D1-B minus D1, the same bar.
  Also, for each buffered book: excess vs the EW universe (certification: t >= 3, halves, years), maxDD, turnover, mean
  holding period in months, and the share of the book's excess from names held >= 6 months.
TAIL CHECK  name-month excess winsorised at p95, then each book's excess t recomputed (declared: the buffer's gain, if
  any, should come from the tail, i.e. from holding monsters longer; if it survives winsorising it's something else).
PRIOR    moderate. Buffers are known to cut turnover at little cost to returns. Whether they ADD return is the
  question. Momentum decays in 6-12 months, so holding longer could give back gains as well as keep monsters.

Usage: PYTHONPATH=src:. python run_momentum_buffer.py  (log -> data/studies/logs/momentum_buffer.log); run on Fargate via
       services/study-runner/.
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
LOG = REPO / "data/studies/logs/momentum_buffer.log"
LOOKBACK, SKIP = 252, 21


def simulate(C: pd.DataFrame, elig: pd.DataFrame):
    idx = C.index; Cv = C.values; E = elig.values
    last_valid = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                           for j in range(Cv.shape[1])])
    me = [i for i in M.month_ends(idx) if pd.Timestamp(M.START) <= idx[i] <= pd.Timestamp(M.END)]
    hold = {"T20": set(), "T20-B": set(), "D1": set(), "D1-B": set()}
    age = {k: {} for k in hold}
    rows, nm = [], []
    for a, b in zip(me[:-1], me[1:]):
        if a - LOOKBACK < 0:
            continue
        score = Cv[a - SKIP] / Cv[a - LOOKBACK] - 1
        ok = E[a] & np.isfinite(score) & np.isfinite(Cv[a])
        names = np.flatnonzero(ok)
        if len(names) < 50:
            continue
        order = names[np.argsort(-score[names])]
        n10 = int(np.ceil(len(names) * 0.10)); q20 = set(order[:int(np.ceil(len(names) * 0.20))])
        new = {}
        for k, cnt in (("T20", 20), ("D1", n10)):
            new[k] = set(order[:cnt])
            keep = {j for j in hold[f"{k}-B"] if j in q20}
            fill = [j for j in order if j not in keep][:max(cnt - len(keep), 0)]
            new[f"{k}-B"] = keep | set(fill)
        exit_i = np.minimum(b, last_valid[names])
        r = pd.Series(Cv[exit_i, names] / Cv[a, names] - 1, index=names).replace([np.inf, -np.inf], np.nan)
        ew = r.mean()
        row = dict(month=idx[b].to_period("M"), EW=ew)
        for k, s in new.items():
            to = 1 - len(s & hold[k]) / max(len(s), 1)
            ag = {j: age[k].get(j, 0) + 1 for j in s}
            age[k] = ag; hold[k] = s
            rr = r.reindex(list(s))
            row[k] = rr.mean() - 2 * M.COST * to
            row[f"to_{k}"] = to; row[f"age_{k}"] = np.mean(list(ag.values()))
            nm += [dict(month=row["month"], book=k, x=v - ew, age=ag[j]) for j, v in rr.dropna().items()]
        rows.append(row)
    return pd.DataFrame(rows).set_index("month"), pd.DataFrame(nm)


def main():
    import run_dip_survivorship as DS
    out = ["# Let winners run: top-quintile buffer on 12-1 momentum (pre-registration in the docstring)"]
    C, V = DS.adjust_and_clean(DS.pull())
    liq = ((V.rolling(50, min_periods=30).mean() >= M.OPTVOL_MIN) & (C >= M.PX_MIN)).fillna(False)
    P, NM = simulate(C, liq)
    cap = NM.x.quantile(0.95)
    h = P.index < pd.Period(M.SPLIT, "M")
    R = []
    for k in ("T20", "T20-B", "D1", "D1-B"):
        x = (P[k] - P.EW) * 100; yr = x.groupby(x.index.year).sum()
        w = NM[NM.book == k].assign(x=lambda z: z.x.clip(upper=cap)).groupby("month").x.mean() * 100
        cum = (1 + P[k]).cumprod(); dd = (1 - cum / cum.cummax()).max() * 100
        sub = NM[NM.book == k]; share6 = sub[sub.age >= 6].x.sum() / sub.x.sum() if sub.x.sum() else np.nan
        res = dict(book=k, excess=x.mean(), t_nw=M.nw_t(x), h1=x[h].mean(), h2=x[~h].mean(),
                   yrs_pos=f"{(yr > 0).sum()}/{len(yr)}", wins_p95=w.mean(), t_wins=M.nw_t(w), maxDD=dd,
                   turnover=P[f"to_{k}"].mean(), mean_age_mo=P[f"age_{k}"].mean(), share_excess_age6=share6)
        res["CERT"] = bool(res["t_nw"] >= 3 and res["h1"] > 0 and res["h2"] > 0 and (yr > 0).sum() > len(yr) / 2)
        if k.endswith("-B"):
            d = (P[k] - P[k[:-2]]) * 100; yd = d.groupby(d.index.year).sum()
            res.update(vs_plain=d.mean(), t_vs_plain=M.nw_t(d), d_h1=d[h].mean(), d_h2=d[~h].mean(),
                       d_yrs=f"{(yd > 0).sum()}/{len(yd)}")
            res["BETTER"] = bool(res["t_vs_plain"] >= 2.24 and res["d_h1"] > 0 and res["d_h2"] > 0 and (yd > 0).sum() > len(yd) / 2)
        R.append(res)
        out.append(f"\n## {k}{'  <- PRIMARY (vs T20)' if k == 'T20-B' else ''}: excess {x.mean():+.2f}pp/mo t_NW {res['t_nw']:+.2f} "
                   f"halves {res['h1']:+.2f}/{res['h2']:+.2f} yrs {res['yrs_pos']} | p95-winsorised {w.mean():+.2f} t {res['t_wins']:+.2f} | "
                   f"maxDD {dd:.0f}% turnover {res['turnover']:.0%}/mo, mean age {res['mean_age_mo']:.1f} mo, "
                   f"excess from names held >= 6 mo {share6:.0%}"
                   + (f" | vs plain {res['vs_plain']:+.2f}pp t {res['t_vs_plain']:+.2f} halves {res['d_h1']:+.2f}/{res['d_h2']:+.2f} "
                      f"yrs {res['d_yrs']}" if k.endswith("-B") else ""))
        out.append("  excess by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in yr.items()))
    D = pd.DataFrame(R)
    out.append("\n" + D.round(3).to_string(index=False))
    for k in ("T20-B", "D1-B"):
        r = D[D.book == k].iloc[0]
        out.append(f"VERDICT {k}: vs plain {r.vs_plain:+.2f}pp t {r.t_vs_plain:+.2f} -> {'BETTER' if r.BETTER else 'not better'}; "
                   f"certification {'PASS' if r.CERT else 'fail'}")
    D.to_csv(REPO / "data/studies/momentum_buffer_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
