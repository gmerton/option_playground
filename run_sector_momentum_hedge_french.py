#!/usr/bin/env python3
"""Industry-momentum 12-1 spread as a bear-market HEDGE on Ken French 10 industries, 1927-2026 (2026-09-29).

PRE-REGISTERED: data/studies/sector_momentum_hedge_french_2026-09-29.md (committed d34e706 / 87747e0 before this ran).
Spread: rank on months h-12..h-2, long top 3 / short bottom 3, net 20 bp/mo + 0.25%/yr borrow. Ten market drawdown
episodes (>= 20%, fixed in the pre-reg). Primary: spread > 0 in >= 7/10 episodes AND de-meaned 50%-vol overlay cuts the
market's in-episode max drawdown in >= 7/10. Label: beats the beta-equivalent market short in >= 7/10.

Usage: PYTHONPATH=src .venv/bin/python3 run_sector_momentum_hedge_french.py > data/studies/sector_momentum_hedge_french_2026-09-29.log
"""
from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm

from lib.studies.french_data import factors, industries10

pd.set_option("display.width", 220)
COST, BORROW, K = 0.0020, 0.0025 / 12, 3
EPISODES = [("1929-08", "1932-06"), ("1946-05", "1947-05"), ("1961-12", "1962-06"), ("1968-11", "1970-06"),
            ("1972-12", "1974-09"), ("1987-08", "1987-11"), ("2000-08", "2002-09"), ("2007-10", "2009-02"),
            ("2020-01", "2020-03"), ("2021-12", "2022-09")]
SEEN = {"2000-08", "2007-10", "2020-01", "2021-12"}


def maxdd(r: pd.Series) -> float:
    w = (1 + r).cumprod(); w = pd.concat([pd.Series([1.0]), w.reset_index(drop=True)])
    return float((w / w.cummax() - 1).min())


def main():
    I, F = industries10(), factors()
    sig = (1 + I).rolling(11).apply(np.prod, raw=True) - 1          # months h-12..h-2 once shifted by 2
    sig = sig.shift(2)
    rows = {}
    for h in I.index:
        s = sig.loc[h].dropna()
        if len(s) < 10 or h < pd.Period("1927-07", "M"):
            continue
        o = s.sort_values()
        rows[h] = I.loc[h, list(o.index[-K:])].mean() - I.loc[h, list(o.index[:K])].mean() - COST - BORROW
    sp = pd.Series(rows, name="spread"); m = F.Mkt.reindex(sp.index)
    fit = sm.OLS(sp, sm.add_constant(m.rename("Mkt"))).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    beta = fit.params.Mkt
    print(f"spread {sp.index.min()} -> {sp.index.max()}, {len(sp)} months; net mean {sp.mean() * 100:+.3f}%/mo "
          f"(t {sp.mean() / sp.std() * sqrt(len(sp)):.2f}), vol {sp.std() * sqrt(12) * 100:.1f}%/yr; "
          f"beta {beta:+.3f} (t {fit.tvalues.Mkt:.2f}), alpha {fit.params.const * 100:+.3f}%/mo (t {fit.tvalues.const:.2f})")
    print("per decade, mean %/mo:", (sp.groupby(sp.index.year // 10 * 10).mean() * 100).round(2).to_dict())

    sleeve = (sp - sp.mean()) * (0.5 * m.std() / sp.std())
    out = []
    for pk, tr in EPISODES:
        win = slice(pd.Period(pk, "M") + 1, pd.Period(tr, "M"))
        s, mk, sl = sp[win], m[win], sleeve[win]
        after = sp[pd.Period(tr, "M") + 1: pd.Period(tr, "M") + 12]
        thru = sp[pd.Period(pk, "M") + 1: pd.Period(tr, "M") + 12]           # exploratory: hold through the rebound
        out.append(dict(peak=pk, trough=tr, seen=pk in SEEN, months=len(s), mkt=((1 + mk).prod() - 1) * 100,
                        spread=((1 + s).prod() - 1) * 100, beta_short=((1 + beta * mk).prod() - 1) * 100,   # same-beta index position: beta x Mkt (fixed 2026-09-29: sign was flipped)
                        dd_host=maxdd(mk) * 100, dd_overlay=maxdd(mk + sl) * 100, next12=((1 + after).prod() - 1) * 100, peak_to_trough12=((1 + thru).prod() - 1) * 100))
    E = pd.DataFrame(out)
    E["pays"] = E.spread > 0; E["dd_cut"] = E.dd_overlay > E.dd_host; E["beats_beta"] = E.spread > E.beta_short
    print(f"\n== episodes (cumulative %, window = peak+1 .. trough; beta-equivalent short uses beta {beta:+.3f}) ==")
    print(E.round(1).to_string(index=False))
    c1, c2, c3 = E.pays.sum(), E.dd_cut.sum(), E.beats_beta.sum()
    new = E[~E.seen]
    print(f"\nCOND 1 spread > 0: {c1}/10 (new episodes {new.pays.sum()}/6)  -> {'YES' if c1 >= 7 else 'no'}")
    print(f"COND 2 de-meaned 50%-vol overlay cuts in-episode max DD: {c2}/10 (new {new.dd_cut.sum()}/6) -> {'YES' if c2 >= 7 else 'no'}")
    print(f"LABEL beats beta-equivalent market short: {c3}/10 (new {new.beats_beta.sum()}/6) -> {'YES' if c3 >= 7 else 'no'}")
    v = "PASS" if c1 >= 7 and c2 >= 7 else "FAIL"
    print(f"VERDICT: {v}" + ("" if v == "FAIL" else (" -- more than a beta hedge" if c3 >= 7 else " -- but no better than a beta-equivalent index short")))
    print(f"\nexploratory: 12 months after each trough (momentum-crash check): {E.next12.round(1).tolist()}")
    E.to_csv("data/studies/sector_momentum_hedge_french_2026-09-29.csv", index=False)


if __name__ == "__main__":
    main()
