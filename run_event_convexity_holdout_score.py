#!/usr/bin/env python3
"""Event convexity HOLDOUT scorer (2026-09-29). PRE-REGISTERED: data/studies/event_convexity_holdout_2026-09-29.md.
Scoring logic from run_event_convexity_score.py (entry mid + 25% spread, sell mid - 25%; sell_5d / sell_10d / hold);
primary = 0.25-delta bucket, sell_5d, event - control, Welch t on date-level means >= 3, both halves (2015 split).
Usage: PYTHONPATH=src .venv/bin/python3 run_event_convexity_holdout_score.py > data/studies/event_convexity_holdout_2026-09-29.log
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)
D = "data/cache/event_convexity_2010"
ELEC = pd.to_datetime(["2010-11-02", "2012-11-06", "2014-11-04", "2016-11-08", "2018-11-06"])
FOMC = pd.to_datetime(json.load(open("data/fomc_dates_2010_2019.json"))["scheduled"])
EVT = set(FOMC) | set(ELEC)
SPLIT = pd.Timestamp("2015-01-01")


def score(E, P, evt):
    for d in (E, P):
        d["trade_date"] = pd.to_datetime(d.trade_date); d["expiry"] = pd.to_datetime(d.expiry)
    paths = {k: g for k, g in P.sort_values("trade_date").groupby(["ticker", "expiry", "strike"], sort=False)}
    rows = []
    for r in E.itertuples(index=False):
        g = paths.get((r.ticker, r.expiry, r.strike))
        if g is None: continue
        entry = (r.bid + r.ask) / 2 + 0.25 * (r.ask - r.bid)
        if not np.isfinite(entry) or entry <= 0.02: continue
        fwd = g[(g.trade_date > r.trade_date) & (g.trade_date <= r.expiry)]
        if fwd.empty: continue
        sell = ((fwd.bid + fwd.ask) / 2 - 0.25 * (fwd.ask - fwd.bid)).clip(lower=0).values
        nxt = [d for d in evt if r.trade_date < d <= r.trade_date + pd.Timedelta(days=5)]
        rows.append(dict(ticker=r.ticker, date=r.trade_date, delta=r.delta, kind="event" if nxt else "control",
                         etype=("election" if any(d in set(ELEC) for d in nxt) else "fomc") if nxt else "",
                         hold_expiry=sell[-1] / entry - 1, sell_5d=sell[min(5, len(sell)) - 1] / entry - 1,
                         sell_10d=sell[min(10, len(sell)) - 1] / entry - 1))
    T = pd.DataFrame(rows)
    T["bucket"] = np.where(T.delta <= 0.18, "0.12d", "0.25d")
    return T


def welch(T, arm, mask=None):
    X = T if mask is None else T[mask]
    ge = X[X.kind == "event"].groupby("date")[arm].mean().dropna()
    gc = T[T.kind == "control"].groupby("date")[arm].mean().dropna()
    if mask is not None:
        gc = T[(T.kind == "control") & T.bucket.isin(X.bucket.unique())].groupby("date")[arm].mean().dropna()
    se = np.sqrt(ge.var(ddof=1) / len(ge) + gc.var(ddof=1) / len(gc))
    return 100 * (ge.mean() - gc.mean()), (ge.mean() - gc.mean()) / se, len(ge), len(gc)


def main():
    T = score(pd.read_parquet(f"{D}/entries.parquet"), pd.read_parquet(f"{D}/paths.parquet"), EVT)
    T = T[(T.date >= "2010-01-01") & (T.date <= "2019-09-30")]
    T.to_parquet(f"{D}/trades.parquet", index=False)
    print(f"{len(T):,} purchases | event {(T.kind == 'event').sum():,} / control {(T.kind == 'control').sum():,} | "
          f"event dates {T[T.kind == 'event'].date.nunique()}, control dates {T[T.kind == 'control'].date.nunique()}")
    out = []
    for b in ("0.25d", "0.12d"):
        B = T[T.bucket == b]
        for arm in ("sell_5d", "sell_10d", "hold_expiry"):
            m, t, ne, nc = welch(B, arm)
            h1 = welch(B[B.date < SPLIT], arm); h2 = welch(B[B.date >= SPLIT], arm)
            e, c = B[B.kind == "event"][arm], B[B.kind == "control"][arm]
            out.append(dict(bucket=b, arm=arm, event_mean=100 * e.mean(), control_mean=100 * c.mean(), diff_pp=m, welch_t=t,
                            h1=h1[0], h2=h2[0], ev_dates=ne, ctl_dates=nc, p5x_ev=100 * (e >= 4).mean(), p5x_ctl=100 * (c >= 4).mean()))
    R = pd.DataFrame(out)
    print(R.round(2).to_string(index=False))
    p = R[(R.bucket == "0.25d") & (R.arm == "sell_5d")].iloc[0]
    ok = p.diff_pp > 0 and p.welch_t >= 3 and p.h1 > 0 and p.h2 > 0
    print(f"\nPRIMARY 0.25d sell_5d: {p.diff_pp:+.2f}pp, Welch t {p.welch_t:+.2f}, halves {p.h1:+.2f}/{p.h2:+.2f} -> {'PASS' if ok else 'FAIL'}")
    B = T[T.bucket == "0.25d"]
    for et in ("fomc", "election"):
        x = B[(B.kind == "event") & (B.etype == et)]
        print(f"  {et}: {x.date.nunique()} dates, {len(x)} purchases, sell_5d mean {100 * x.sell_5d.mean():+.1f}% median {100 * x.sell_5d.median():+.1f}%")
    for d, g in B[(B.kind == "event") & (B.etype == "election")].groupby("date"):
        print(f"    election eve {d.date()}: n {len(g)} sell_5d mean {100 * g.sell_5d.mean():+.1f}% median {100 * g.sell_5d.median():+.1f}%")
    # pooled with the original 2019-26 trades
    O = pd.read_parquet("data/cache/event_convexity/trades.parquet"); O["date"] = pd.to_datetime(O.date)
    O["bucket"] = np.where(O.delta <= 0.18, "0.12d", "0.25d")
    Pl = pd.concat([T[["date", "kind", "bucket", "sell_5d"]], O[["date", "kind", "bucket", "sell_5d"]]])
    m, t, ne, nc = welch(Pl[Pl.bucket == "0.25d"], "sell_5d")
    print(f"\nexploratory POOLED 2010-2026, 0.25d sell_5d: {m:+.2f}pp, Welch t {t:+.2f} ({ne} event / {nc} control dates)")
    R.to_csv("data/studies/event_convexity_holdout_2026-09-29.csv", index=False)


if __name__ == "__main__":
    main()
