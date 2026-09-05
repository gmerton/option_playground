#!/usr/bin/env python3
"""
Validate the trailing-window regime rules (lib/regime/trailing.py) on a long
history so they are not fit to August 2026.

Panel: data/cache/liquid_panel_2019.parquet -- yfinance adjusted OHLCV, 2019-01
to date, for the names that were liquid on 2026-07-31 (+SPY/QQQ/IWM/RSP).
Caveat: survivorship -- the universe is today's liquid names. Eligibility is
applied point-in-time (trailing-50 ADDV >= $30M, px >= $5) which trims but does
not remove the bias. Absolute levels are optimistic; RELATIVE comparisons
(regime A vs regime B, laggard vs leader on the same dates) are what matter here.

Tests:
  1. Style persistence: does the trailing-21 laggard-minus-leader spread predict
     the next-21 spread?  (If not, the trailing read is descriptive only.)
  2. Breadth gate: setup forward returns when 10d advancer avg >= 50% vs < 50%.
  3. Laggard vs leader breakouts by style regime.
  4. Threshold sensitivity (style band, breadth level) -- results must be stable.
  5. August 2026 replay of the reads.

Usage: PYTHONPATH=src python run_regime_validation.py [--panel path] [--horizon 10]
"""
from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd

from lib.regime.trailing import (REGIME_DEFAULTS, Panel, breadth, forward_returns, liquidity_mask, setup_events,
                                 style_spread)

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)


def tstat(x):
    x = pd.Series(x).dropna()
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan


def fmt(x, w=6):
    return f"{100 * x:+{w}.2f}" if pd.notna(x) else " " * (w + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default="data/cache/liquid_panel_2019.parquet")
    ap.add_argument("--horizon", type=int, default=10)
    ap.add_argument("--window", type=int, default=REGIME_DEFAULTS["window"])
    a = ap.parse_args()
    W, HZ = a.window, a.horizon

    raw = pd.read_parquet(a.panel)
    bench = raw[raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    spy = bench[bench.ticker == "SPY"].set_index("date").close.sort_index()
    p = Panel.from_long(raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])])
    elig = liquidity_mask(p)
    print(f"panel: {p.close.shape[1]} names, {p.close.index[0].date()} -> {p.close.index[-1].date()}; "
          f"eligible names/day median {int(elig.sum(axis=1).median())}")

    b = breadth(Panel(*(f.where(elig) for f in (p.close, p.high, p.low, p.dolvol))))
    s = style_spread(p, W, eligible=elig)
    years = p.close.index.year

    # ------------------------------------------------------------ 1. style persistence
    print("\n" + "=" * 25 + " 1. STYLE PERSISTENCE: trailing spread -> next-window spread " + "=" * 25)
    fwd = s.spread.shift(-W)  # spread over (t, t+W] with cohorts fixed at t  == style_spread evaluated at t+W
    df = pd.DataFrame({"trail": s.spread, "fwd": fwd}).dropna()
    df = df[df.index >= "2019-12-01"]
    print(f"all days n={len(df)}  corr(trail, fwd) = {df.trail.corr(df.fwd):+.3f}   "
          f"sign agreement {100 * (np.sign(df.trail) == np.sign(df.fwd)).mean():.1f}%")
    for band in (0.02, 0.03, 0.05):
        for lab, m in (("LAGGARD-TURN", df.trail > band), ("MOMENTUM", df.trail < -band), ("NEUTRAL", df.trail.abs() <= band)):
            sub = df[m]
            # non-overlapping sample for a t-stat
            nov = sub.iloc[::W]
            print(f"  band {band:.2f} {lab:13s} n={len(sub):5d}  next-spread mean {fmt(sub.fwd.mean())}  median {fmt(sub.fwd.median())}  "
                  f"P(next>0) {100 * (sub.fwd > 0).mean():4.1f}%   t(non-overlap n={len(nov)}) {tstat(nov.fwd):+.2f}")
    print("  by year (band 0.03): year | LAGGARD-TURN days, next-spread mean | MOMENTUM days, next-spread mean")
    for y, g in df.groupby(df.index.year):
        lt, mo = g[g.trail > 0.03], g[g.trail < -0.03]
        print(f"    {y} | {len(lt):4d} {fmt(lt.fwd.mean()) if len(lt) else '   --  '} | {len(mo):4d} {fmt(mo.fwd.mean()) if len(mo) else '   --  '}")
    # what does the level of the spread say about the NEXT window's broad tape?
    fr_all = forward_returns(p, W).where(elig)
    tape = fr_all.median(axis=1)
    print("\n  Trailing style -> next-window median stock return (does laggard-turn tape carry on / roll over?):")
    for lab, m in (("LAGGARD-TURN", s.spread > 0.03), ("MOMENTUM", s.spread < -0.03), ("NEUTRAL", s.spread.abs() <= 0.03)):
        x = tape[m & (tape.index >= "2019-12-01")].dropna()
        print(f"    {lab:13s} n={len(x):5d}  next-{W} median-stock ret mean {fmt(x.mean())}  P(>0) {100 * (x > 0).mean():4.1f}%")

    # ------------------------------------------------------------ 2. breadth gate
    print("\n" + "=" * 25 + f" 2. BREADTH GATE on setup entries ({HZ}-session fwd, excess vs same-date baseline) " + "=" * 25)
    ev = setup_events(p)
    fr = forward_returns(p, HZ).where(elig)
    base_by_date = fr.mean(axis=1)
    adv10 = b.adv10
    pct50_rising = b.pct_above_50 > b.pct_above_50.shift(5)

    def cond_table(name, mask, conds):
        mm = mask & elig
        x = fr.where(mm).stack().dropna()
        d = x.index.get_level_values(0)
        xs = pd.Series(x.values - base_by_date.reindex(d).values, index=x.index)
        out = []
        for lab, c in conds:
            sel = c.reindex(d).fillna(False).values.astype(bool)
            xx, xe = x[sel], xs[sel]
            # date-level t-stat on excess (cluster by date)
            de = xe.groupby(level=0).mean()
            out.append(f"{lab}: n={len(xx):6d} raw {fmt(xx.mean())} win {100 * (xx > 0).mean():4.1f}% xs {fmt(xe.mean())} t {tstat(de):+.2f}")
        print(f"  {name:26s} | " + " | ".join(out))
        return x, xs

    conds_b = [("breadth ON ", adv10 >= 0.50), ("breadth OFF", adv10 < 0.50)]
    for k in ("pullback_20ema", "ur_50sma", "ur_20dlow", "ur_20dlow_rvol1.5", "meanrev_3down_uptrend",
              "breakout_leader_house", "breakout_leader_rvol1.5", "breakout_laggard_rvol1.5", "breakout_52wk_rvol1.5",
              "ep_gap10_rvol3", "laggard_squeeze", "SHORT_breakdown_rvol1.3", "SHORT_gapdown10_rvol3"):
        cond_table(k, ev[k], conds_b)
    print("\n  sensitivity: pullback_20ema and ur_20dlow excess by adv10 threshold")
    for thr in (0.45, 0.50, 0.55):
        for k in ("pullback_20ema", "ur_20dlow"):
            cond_table(f"{k} @{thr:.2f}", ev[k], [("ON ", adv10 >= thr), ("OFF", adv10 < thr)])
    print("\n  alt gate: %>50sma rising over 5 sessions")
    for k in ("pullback_20ema", "ur_20dlow", "breakout_leader_rvol1.5"):
        cond_table(k, ev[k], [("rising ", pct50_rising), ("falling", ~pct50_rising)])
    print("\n  by year, pullback_20ema excess ON vs OFF (stability check):")
    x, xs = cond_table("pullback_20ema", ev["pullback_20ema"], conds_b)
    d = xs.index.get_level_values(0)
    on = adv10.reindex(d).values >= 0.5
    for y in sorted(set(d.year)):
        yy = d.year == y
        print(f"    {y}: ON n={int((yy & on).sum()):5d} xs {fmt(xs[yy & on].mean())}   OFF n={int((yy & ~on).sum()):5d} xs {fmt(xs[yy & ~on].mean())}")

    # ------------------------------------------------------------ 3. laggard vs leader breakouts by style regime
    print("\n" + "=" * 25 + " 3. LAGGARD vs LEADER BREAKOUTS by style regime " + "=" * 25)
    conds_s = [("LAGGARD-TURN", s.spread > 0.03), ("NEUTRAL", s.spread.abs() <= 0.03), ("MOMENTUM", s.spread < -0.03)]
    for hz in (HZ, 21):
        frh = forward_returns(p, hz).where(elig); bbd = frh.mean(axis=1)
        print(f"  horizon {hz}:")
        for k in ("breakout_laggard_rvol1.5", "breakout_leader_rvol1.5", "breakout_leader_house", "breakout_52wk_rvol1.5", "laggard_squeeze"):
            mm = ev[k] & elig
            x = frh.where(mm).stack().dropna(); d = x.index.get_level_values(0)
            xs = pd.Series(x.values - bbd.reindex(d).values, index=x.index)
            parts = []
            for lab, c in conds_s:
                sel = c.reindex(d).fillna(False).values.astype(bool)
                de = xs[sel].groupby(level=0).mean()
                parts.append(f"{lab}: n={int(sel.sum()):5d} xs {fmt(xs[sel].mean())} win {100 * (x[sel] > 0).mean():4.1f}% t {tstat(de):+.2f}")
            print(f"    {k:26s} | " + " | ".join(parts))
    print("\n  by year: laggard-breakout minus leader-breakout excess (10s):")
    for k in ("breakout_laggard_rvol1.5", "breakout_leader_rvol1.5"):
        mm = ev[k] & elig; x = fr.where(mm).stack().dropna(); d = x.index.get_level_values(0)
        xs = pd.Series(x.values - base_by_date.reindex(d).values, index=d)
        ev[k + "_xs_by_year"] = xs.groupby(xs.index.year).agg(["size", "mean"])
    yr = ev["breakout_laggard_rvol1.5_xs_by_year"].join(ev["breakout_leader_rvol1.5_xs_by_year"], lsuffix="_lag", rsuffix="_lead")
    yr["diff_pp"] = 100 * (yr.mean_lag - yr.mean_lead)
    yr[["mean_lag", "mean_lead"]] = 100 * yr[["mean_lag", "mean_lead"]]
    print(yr.round(2).to_string())

    # ------------------------------------------------------------ 5. August replay
    print("\n" + "=" * 25 + " 5. AUGUST 2026 REPLAY of the reads (this panel) " + "=" * 25)
    for d in ("2026-07-31", "2026-08-04", "2026-08-14", "2026-08-18", "2026-08-31", "2026-09-04"):
        d = pd.Timestamp(d)
        if d not in b.index:
            continue
        st = "LAGGARD-TURN" if s.spread[d] > 0.03 else ("MOMENTUM" if s.spread[d] < -0.03 else "NEUTRAL")
        print(f"  {d.date()}  adv10 {100 * b.adv10[d]:5.1f}% -> breadth {'ON ' if b.adv10[d] >= 0.5 else 'OFF'} | %>50 {100 * b.pct_above_50[d]:5.1f} | "
              f"spread {fmt(s.spread[d])} -> {st} | next-{W} median stock {fmt(tape.get(d, np.nan))}")


if __name__ == "__main__":
    main()
