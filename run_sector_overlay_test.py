#!/usr/bin/env python3
"""
Sector momentum spread as a BOOK OVERLAY -- is it the missing bear leg? (pre-registered 2026-09-24, before the run)

WHY. sector_momentum_spread_2026-09-24: 12-1 K3 has no return edge (-0.17%/mo, perm p 0.37) but beta -0.20 and
crisis payoffs beyond beta (2020 +16%, 2022 +31%, 2008 +25%). Its mean is slightly NEGATIVE, so -- unlike the RV
sleeve -- any drawdown cut it produces is hedging, not borrowed return. Scored exactly like the RV overlay and the
2026-09-20 put overlay.

DESIGN
  book      run_put_overlay_study.book_series() (straddle + bull put + breakout, equal-vol sleeves, 4%/mo, by entry
            month, 2018-04 -> 2026-02) and the no-straddle book (bull put + breakout) -- the live book runs heavier
            in stock + bull puts.
  sleeve    run_sector_momentum_spread.spread_series(12, 3): the PRIMARY, net of 20 bp + borrow, month t's return
            mapped to book period t.
  sizes     sleeve vol = 25 / 50 / 100% of the book's; PRIMARY 50%.
  CONTROL   (declared now) a SPY SHORT at the same vol: is the sector spread better than simply shorting the index?
            Also the DE-MEANED sleeve (declared now, unlike the RV run where it was added after).
  bar       CANDIDATE only if, at 50%, on BOTH books: maxDD falls, Sharpe does not fall, the sleeve's mean in the
            book's 10 worst months > 0, AND it beats the same-vol SPY short on maxDD. ~95 months, 2 stress episodes
            (2020, 2022): a screen for a forward test, never an adoption.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_sector_overlay_test.py > data/studies/logs/sector_overlay_test.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

import run_put_overlay_study as po
import run_sector_momentum_spread as sm

SIZES, PRIMARY = [0.25, 0.50, 1.00], 0.50


def stats(r: pd.Series) -> dict:
    cum = r.cumsum()
    return dict(mean=r.mean(), sharpe=r.mean() / r.std() * np.sqrt(12), maxDD=(cum.cummax() - cum).max(),
                worst=r.min(), worst3=r.nsmallest(3).mean(), y2020=r[r.index.year == 2020].sum(),
                y2022=r[r.index.year == 2022].sum())


def score(book: pd.Series, sl: pd.Series, label: str, kind: str) -> pd.DataFrame:
    rows = [dict(book=label, sleeve=kind, size="none", **stats(book))]
    for s in SIZES:
        k = s * book.std() / sl.std()
        rows.append(dict(book=label, sleeve=kind, size=f"{int(s*100)}%" + (" *P*" if s == PRIMARY else ""),
                         **stats(book + k * sl)))
    R = pd.DataFrame(rows); b0 = R.iloc[0]
    R["dSharpe"], R["dDD"] = R.sharpe - b0.sharpe, R.maxDD - b0.maxDD
    return R


def main() -> None:
    net, spy = sm.spread_series(12, 3)
    sl = (100 * net); sl.index = sl.index.to_period("M")
    sp = (100 * spy); sp.index = sp.index.to_period("M")
    B = po.book_series()
    idx = B.index.intersection(sl.index)
    B, sl, sp = B.loc[idx], sl.loc[idx], sp.loc[idx]
    z = B[["bullput", "breakout"]] / B[["bullput", "breakout"]].std()
    nb = z.sum(axis=1); nb = nb / nb.std() * po.BOOK_VOL
    short_spy = -sp
    print(f"window {idx.min()} -> {idx.max()} ({len(idx)} months)")
    print(f"sleeve in window: mean {sl.mean():+.2f}%/mo, sd {sl.std():.2f} | corr: book {sl.corr(B.book):+.2f}, "
          f"no-straddle {sl.corr(nb):+.2f}, SPY {sl.corr(sp):+.2f} | book vs SPY {B.book.corr(sp):+.2f}, "
          f"no-straddle vs SPY {nb.corr(sp):+.2f}\n")
    dm = sl - sl.mean()
    parts = []
    for lab, bk in (("full book", B.book), ("no-straddle", nb)):
        parts += [score(bk, sl, lab, "sector spread"), score(bk, dm, lab, "  de-meaned"),
                  score(bk, short_spy, lab, "  SPY short (control)")]
    R = pd.concat(parts, ignore_index=True)
    R = R[~((R["size"] == "none") & (R.sleeve != "sector spread"))]
    print(R[["book", "sleeve", "size", "mean", "sharpe", "dSharpe", "maxDD", "dDD", "worst", "worst3", "y2020", "y2022"]]
          .round(2).to_string(index=False))
    verdict = {}
    for lab, bk in (("full book", B.book), ("no-straddle", nb)):
        w = bk.nsmallest(10).index
        print(f"\n{lab}: its 10 worst months (%):")
        print(pd.DataFrame({"book": bk.loc[w], "sector spread": sl.loc[w], "spy": sp.loc[w]}).round(2).T.to_string())
        print(f"sector spread mean in those months {sl.loc[w].mean():+.2f}% vs all months {sl.mean():+.2f}%")
        g = lambda kind: R[(R.book == lab) & (R.sleeve.str.strip() == kind) & R["size"].str.contains(r"\*P\*")].iloc[0]
        s, c = g("sector spread"), g("SPY short (control)")
        verdict[lab] = bool(s.dDD < 0 and s.dSharpe >= 0 and sl.loc[w].mean() > 0 and s.maxDD < c.maxDD)
    print(f"\nPRIMARY (50%) candidate on {verdict} -> "
          f"{'CANDIDATE for a forward test' if all(verdict.values()) else 'not a candidate'}")
    R.to_csv("data/studies/sector_overlay_test_2026-09-24.csv", index=False)


if __name__ == "__main__":
    main()
