#!/usr/bin/env python3
"""Three PARKED equity candidates on the unused 2010-01 -> 2019-09 holdout (2026-09-29, audit step 3 item 2).

PRE-REGISTERED: data/studies/equity_holdout_2010_19_2026-09-29.md (committed before this ran). Signal builders, exits and
controls are the originals, unchanged; only the panel (liquid_panel_2009) and the window change.
  H1 earnings drift good+MUTED  harness, hold 10, next open, arm t1R, control xname
  H2 house breakout in HYB-A    harness, hold 60, close entry, arm stop_hold, control post
  H3 HYB-B selection            ADR-decile-matched 20d excess, non-overlapping dates, >= 5 members
Bar per test: stat > 0, t >= 3, both halves (split 2015-01-01) > 0, positive in a majority of years.

Usage: AWS/MySQL env; PYTHONPATH=src:. .venv/bin/python3 run_equity_holdout_2010_19.py
       (verbose harness output -> data/studies/logs/equity_holdout_2010_19.log; summary -> stdout + .csv)
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import run_ledger_rerun as lr
import run_precision_tier_control as pc
import run_universe_test as ut
from lib.studies import pattern_test as pt
from lib.studies.pattern_test import DailyPanel, run_daily

PANEL = "data/cache/liquid_panel_2009.parquet"
HO_START, HO_END, SPLIT, H = "2010-01-01", "2019-09-30", "2015-01-01", 20
LOG = pt.REPO / "data/studies/logs/equity_holdout_2010_19.log"
OUT = pt.REPO / "data/studies/equity_holdout_2010_19_2026-09-29.csv"


def holdout_signals(hit, stop, side="long", since=None):
    """daily_signals restricted to the holdout window (replaces the builders' default since=2019-10-01)."""
    h = hit.fillna(False).astype(bool).copy()
    h[(h.index < HO_START) | (h.index > HO_END)] = False
    return pt.daily_signals(h, stop=stop, side=side, since=HO_START)


def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def harness_row(test, name, fn, hold, panel, entry_at, control, arm):
    tab = run_daily(name, fn, hold=hold, panel=panel, entry_at=entry_at, control=control, split=SPLIT, ledger=False)
    T = pd.read_parquet(pt.REPO / f"data/cache/pattern_{name.replace(' ', '_').lower()}_daily.parquet")
    yrs = T.assign(y=pd.to_datetime(T.date).dt.year).groupby("y")[arm].mean()
    pa = tab.attrs["arms"][arm]
    return dict(test=test, control=control, arm=arm, n=int(tab.loc[arm, "n"]), meanR=tab.loc[arm, "meanR"],
                stat=pa["pedge"], t=pa["edge_t"], h1=pa["eh1"], h2=pa["eh2"],
                yrs_pos=f"{int((yrs > 0).sum())}/{len(yrs)} (raw R)", p_search=tab.attrs.get("p_search", np.nan))


def main():
    raw = pd.read_parquet(pt.REPO / PANEL)
    raw_x = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    Pb, brk, _prec = pc.build(PANEL)
    print(f"panel {Pb.close.shape} {Pb.close.index.min().date()} -> {Pb.close.index.max().date()}; holdout {HO_START} -> {HO_END}")
    rows = []

    # H1 -- earnings drift good+MUTED (builder uses the harness panel P from load_panel)
    P = pt.load_panel(PANEL)
    lr.daily_signals = holdout_signals                     # the builder's lambdas call this name at run time
    cells, _E = lr.earnings_patterns(P, raw)
    fn = next(f for n, f, h in cells if n == "earnings drift, good+MUTED")
    for ctrl, arm in (("xname", "t1R"), ("post", "t1R"), ("xname", "ema20")):
        rows.append(harness_row("H1 earnings good+MUTED", f"HOLDOUT earnings good+MUTED [{ctrl}]", fn, 10, P, "next_open", ctrl, arm))

    # H2 -- house breakout inside HYB-A
    masks = ut.build_masks(Pb, raw_x, start=HO_START)
    m = (brk & masks["HYB-A"]).copy()
    fn2 = lambda _P, mm=m: holdout_signals(mm, stop=Pb.low)
    for ctrl, arm in (("post", "stop_hold"), ("xname", "stop_hold"), ("post", "ema20")):
        panel = Pb if ctrl == "post" else DailyPanel(open=Pb.open, high=Pb.high, low=Pb.low, close=Pb.close, adr=Pb.adr,
                                                      elig=masks["HYB-A"], ema20=Pb.ema20)   # xname drawn in-mask, as the original
        rows.append(harness_row("H2 breakout in HYB-A", f"HOLDOUT breakout in HYB-A [{ctrl}]", fn2, 60, panel, "close", ctrl, arm))

    # H3 -- HYB-B selection, ADR-decile matched (run_hybb_neighbourhood.matched, cell ADR 4 / $100M)
    C = Pb.close
    base = Pb.elig.shift(1).fillna(False).astype(bool)
    fr = C.shift(-H) / C - 1
    dates = C.index[(C.index >= HO_START) & (C.index <= HO_END)][::H]
    F = fr.loc[dates].values
    B = base.loc[dates].values & np.isfinite(F)
    panel_mean = np.nanmean(np.where(B, F, np.nan), axis=1)
    adr = masks["_adr"]
    dec = adr.loc[dates].rank(axis=1, pct=True).mul(10).clip(upper=9.999).fillna(-1).astype(int).values
    dec = np.where(B, dec, -1)
    decmean = np.stack([np.nanmean(np.where(dec == d, F, np.nan), axis=1) for d in range(10)], axis=1)
    mm = masks["HYB-B"].loc[dates].values & B
    cnt = mm.sum(axis=1)
    cd = np.stack([(mm & (dec == d)).sum(axis=1) for d in range(10)], axis=1)
    w = cd / np.maximum(cnt, 1)[:, None]
    bench = np.nansum(w * np.nan_to_num(decmean), axis=1) / np.maximum(np.sum(w * np.isfinite(decmean), axis=1), 1e-12)
    mem = np.nanmean(np.where(mm, F, np.nan), axis=1)
    ex = pd.Series(np.where(cnt >= 5, mem - bench, np.nan), index=dates) * 100
    rawx = pd.Series(np.where(cnt >= 5, mem - panel_mean, np.nan), index=dates) * 100
    exd = ex.dropna(); yrs = exd.groupby(exd.index.year).mean()
    for lab, s in (("ADR-matched", ex), ("raw", rawx)):
        s = s.dropna()
        rows.append(dict(test="H3 HYB-B selection", control=lab, arm="20d", n=len(s), meanR=np.nan, stat=s.mean(), t=tstat(s),
                         h1=s[s.index < SPLIT].mean(), h2=s[s.index >= SPLIT].mean(),
                         yrs_pos=f"{int((s.groupby(s.index.year).mean() > 0).sum())}/{s.index.year.nunique()}", p_search=np.nan))
    print(f"\nH3 members per date: median {np.median(cnt):.0f}; dates with >= 5 members {int((cnt >= 5).sum())}/{len(dates)}")
    print("H3 ADR-matched excess by year (%):", yrs.round(2).to_dict())

    R = pd.DataFrame(rows)
    R.to_csv(OUT, index=False)
    return R


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        R = main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(R.round(3).to_string(index=False))
    for test, prim in (("H1 earnings good+MUTED", ("xname", "t1R")), ("H2 breakout in HYB-A", ("post", "stop_hold")),
                       ("H3 HYB-B selection", ("ADR-matched", "20d"))):
        r = R[(R.test == test) & (R.control == prim[0]) & (R.arm == prim[1])].iloc[0]
        y_ok = int(r.yrs_pos.split("/")[0]) > int(r.yrs_pos.split("/")[1].split()[0]) / 2
        ok = r.stat > 0 and r.t >= 3 and r.h1 > 0 and r.h2 > 0 and y_ok
        print(f"PASS {test} ({prim[0]}, {prim[1]}): {'YES' if ok else 'no'}  (stat {r.stat:+.3f}, t {r.t:.2f}, halves {r.h1:+.3f}/{r.h2:+.3f}, yrs {r.yrs_pos})")
