#!/usr/bin/env python3
"""
Relative-value spread as a BOOK OVERLAY (pre-registered 2026-09-24, before the first run).

WHY. rv_spread_test_2026-09-24: long INT / short DIST nets +1.31%/period but t 1.48 (UNDERPOWERED) -- with beta
-0.18 and +6.5%/period in 2022. It cannot certify as a return source; the question here is the one the negative
beta raises: does a SMALL sleeve of it cut the book's bad months by more than it costs? This is the same question
the cheap-convexity put overlay answered NULL on 2026-09-20 (run_put_overlay_study.py), scored the same way.

DESIGN
  book      run_put_overlay_study.book_series(): straddle + bull put + breakout, each sleeve scaled to equal monthly
            vol, book at 4%/month, by ENTRY month (the put-overlay study's stated assumption, reused unchanged).
  sleeve    long INT / short DIST (the rv_spread_test PRIMARY, masks reused verbatim), rebalanced on each month's
            first session, held to the next month's first session, equal weight, dollar-neutral, net of 40 bp per
            month (100% turnover) + 0.5%/yr borrow. >= 5 names per leg.
  sizes     sleeve scaled so its monthly vol = 25% / 50% / 100% of the book's; PRIMARY = 50%. Scale fixed from the
            full-sample sleeve vol (a known in-sample choice, stated).
  window    months where both exist: 2020-01 -> 2026-02 (masks need 252 sessions of history).
  bar       the overlay is a CANDIDATE only if, at the PRIMARY size: maxDD falls, Sharpe does not fall, AND the sleeve's
            mean in the book's 10 worst months is positive. Also required to hold in the no-straddle book
            (the live book runs heavier in stock + bull puts). No t bar: ~74 months cannot certify an overlay; this
            is a screen for whether a forward test is worth running, not an adoption.
  ADDED AFTER THE FIRST RUN (robustness, not the primary): (1) months where a leg had < 5 names are kept in the
            book with the sleeve FLAT (0) -- the first run dropped them from the book too, which removed bear months
            from the baseline; (2) a DE-MEANED sleeve (its uncertified mean set to 0) -- if the drawdown cut survives,
            it is hedging; if not, it was only the sleeve's positive mean.
  report    corr(sleeve, book), corr(sleeve, SPY), per-year, 2020 / 2022, the book's 10 worst months side by side.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_rv_overlay_test.py > data/studies/logs/rv_overlay_test.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

import run_precision_tier_control as pc
import run_put_overlay_study as po
import run_short_universe_test as su
import run_universe_test as ut
from lib.studies import pattern_test as pt

COST, BORROW = 0.0040, 0.005 / 12
SIZES, PRIMARY = [0.25, 0.50, 1.00], 0.50


def sleeve_monthly() -> tuple[pd.Series, pd.Series]:
    P, _b, _p = pc.build()
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    spy = raw[raw.ticker == "SPY"].set_index("date").close.sort_index(); spy.index = pd.to_datetime(spy.index)
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    L, S = ut.build_masks(P, raw), su.build_masks(P, raw, spy)
    C = P.close
    starts = pd.Series(C.index, index=C.index).groupby(C.index.to_period("M")).min()
    starts = starts[starts >= pd.Timestamp("2020-01-01")]
    out, spy_m = {}, {}
    for d0, d1 in zip(starts.values[:-1], starts.values[1:]):
        d0, d1 = pd.Timestamp(d0), pd.Timestamp(d1)
        r = C.loc[d1] / C.loc[d0] - 1
        lr, sr = r[L["INT"].loc[d0]].dropna(), r[S["DIST"].loc[d0]].dropna()
        if len(lr) >= 5 and len(sr) >= 5:
            out[d0.to_period("M")] = lr.mean() - sr.mean() - COST - BORROW
            spy_m[d0.to_period("M")] = spy.asof(d1) / spy.asof(d0) - 1
    return pd.Series(out) * 100, pd.Series(spy_m) * 100


def stats(r: pd.Series) -> dict:
    cum = r.cumsum()
    return dict(mean=r.mean(), sharpe=r.mean() / r.std() * np.sqrt(12), maxDD=(cum.cummax() - cum).max(),
                worst=r.min(), worst3=r.nsmallest(3).mean(), y2020=r[r.index.year == 2020].sum(),
                y2022=r[r.index.year == 2022].sum())


def score(book: pd.Series, sl: pd.Series, label: str) -> pd.DataFrame:
    rows = [dict(book=label, size="none", **stats(book))]
    for s in SIZES:
        k = s * book.std() / sl.std()
        rows.append(dict(book=label, size=f"{int(s*100)}%" + (" *PRIMARY*" if s == PRIMARY else ""),
                         **stats(book + k * sl)))
    R = pd.DataFrame(rows); b0 = R.iloc[0]
    R["dSharpe"], R["dDD"] = R.sharpe - b0.sharpe, R.maxDD - b0.maxDD
    return R


def main() -> None:
    sl, spy_m = sleeve_monthly()
    B = po.book_series()
    B = B[B.index >= sl.index.min()]
    idx = B.index
    n_flat = int((~idx.isin(sl.index)).sum())
    sl, spy_m = sl.reindex(idx).fillna(0.0), spy_m.reindex(idx)
    print(f"months with the sleeve FLAT (a leg had < 5 names): {n_flat} -> {[str(m) for m in idx[~idx.isin(pd.Series(sl[sl != 0].index))]]}")
    z = B[["bullput", "breakout"]] / B[["bullput", "breakout"]].std()
    nb = z.sum(axis=1); nb = nb / nb.std() * po.BOOK_VOL
    print(f"window {idx.min()} -> {idx.max()} ({len(idx)} months)")
    print(f"sleeve (long INT / short DIST, monthly, net): mean {sl.mean():+.2f}%/mo, sd {sl.std():.2f}, "
          f"t {sl.mean()/sl.std()*np.sqrt(len(sl)):.2f}, months + {(sl > 0).mean():.0%}")
    print(f"corr sleeve vs book {sl.corr(B.book):+.2f} | vs no-straddle book {sl.corr(nb):+.2f} | vs SPY {sl.corr(spy_m):+.2f} "
          f"| book vs SPY {B.book.corr(spy_m):+.2f}\n")
    R = pd.concat([score(B.book, sl, "full book"), score(nb, sl, "no-straddle book")], ignore_index=True)
    dm = sl - sl[sl != 0].mean() * (sl != 0)
    R0 = pd.concat([score(B.book, dm, "full book"), score(nb, dm, "no-straddle book")], ignore_index=True)
    print("DE-MEANED sleeve (robustness: is it hedging, or only its positive mean?):")
    print(R0[["book", "size", "mean", "sharpe", "dSharpe", "maxDD", "dDD", "worst", "y2020", "y2022"]].round(2).to_string(index=False))
    print()
    print(R[["book", "size", "mean", "sharpe", "dSharpe", "maxDD", "dDD", "worst", "worst3", "y2020", "y2022"]]
          .round(2).to_string(index=False))
    for lab, bk in (("full book", B.book), ("no-straddle book", nb)):
        w = bk.nsmallest(10).index
        print(f"\n{lab}: its 10 worst months, sleeve alongside (%):")
        print(pd.DataFrame({"book": bk.loc[w], "sleeve": sl.loc[w], "spy": spy_m.loc[w]}).round(2).T.to_string())
        print(f"sleeve mean in those months {sl.loc[w].mean():+.2f}% vs all months {sl.mean():+.2f}%")
    print("\nsleeve by year (%/mo):")
    print(sl.groupby(sl.index.year).agg(["size", "mean"]).round(2).T.to_string())
    ok = {}
    for lab, bk in (("full book", B.book), ("no-straddle book", nb)):
        r = R[(R.book == lab) & R["size"].str.contains("PRIMARY")].iloc[0]
        ok[lab] = bool(r.dDD < 0 and r.dSharpe >= 0 and sl.loc[bk.nsmallest(10).index].mean() > 0)
    print(f"\nPRIMARY (50% of book vol) candidate on: {ok} -> "
          f"{'CANDIDATE for a forward test' if all(ok.values()) else 'not a candidate'}")
    R.to_csv(pt.REPO / "data/studies/rv_overlay_test_2026-09-24.csv", index=False)


if __name__ == "__main__":
    main()
