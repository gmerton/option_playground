#!/usr/bin/env python3
"""
Does capping the tail destroy the event-convexity edge?

The 2026-09-18 study found that far-OTM calls bought the session before a scheduled event beat the
same purchase on a random date on every exit (0.12d, sell after 5 sessions: +30.7% vs -3.6%). That
is a RIGHT-TAIL result -- the mean is carried by the 5x and 10x outcomes.

Ravish's "super bull call spread" (reviewed 2026-09-20) expresses the same bullish convexity as a
DEBIT SPREAD, which caps the payoff at the width. If the event edge lives in the tail, a short leg
should remove most of it. This measures that directly rather than asserting it.

Construction: for every (ticker, entry date, expiry) in the event-convexity cache that has BOTH a
~0.25d and a ~0.12d call at distinct strikes, build
    long the 0.25d call, short the 0.12d call        (a real OTM debit call spread)
and compare it against each leg bought naked, ON EXACTLY THE SAME ENTRIES. Restricting all three
arms to the identical sample is the whole point: the naked numbers from the 2026-09-18 run cover a
wider set of entries, so quoting them against this subset would be the sample-composition error the
2026-09-19 honest-control re-run was built to catch.

Fills match the parent study: buy at mid + 25% of the spread, sell at mid - 25%, per leg, both ways.
A debit spread is floored at zero and capped at the width.

Usage: PYTHONPATH=src .venv/bin/python3 run_event_spread_study.py \
           > data/studies/event_spread_2026-09-20.log
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)

E = pd.read_parquet("data/cache/event_convexity/entries.parquet")
P = pd.read_parquet("data/cache/event_convexity/paths.parquet")
for d in (E, P):
    d["trade_date"] = pd.to_datetime(d.trade_date); d["expiry"] = pd.to_datetime(d.expiry)
ev = json.load(open("data/fomc_dates.json"))
EVT = set(pd.to_datetime(ev["scheduled"])) | set(pd.to_datetime(["2020-11-03", "2022-11-08", "2024-11-05"]))

paths = {k: g.sort_values("trade_date") for k, g in P.groupby(["ticker", "expiry", "strike"], sort=False)}
FILL = 0.25


def _entry_cost(bid, ask, side):
    """side=+1 buy (pay up), -1 sell (receive less)."""
    mid, sp = (bid + ask) / 2, (ask - bid)
    return mid + side * FILL * sp


def _path_marks(tk, exp, strike, after):
    g = paths.get((tk, exp, strike))
    if g is None:
        return None
    fwd = g[(g.trade_date > after) & (g.trade_date <= exp)]
    return None if fwd.empty else fwd


def _is_event(d):
    return any(d < e <= d + pd.Timedelta(days=5) for e in EVT)


rows = []
for (tk, td, exp), g in E.groupby(["ticker", "trade_date", "expiry"], sort=False):
    if g.strike.nunique() < 2:
        continue                                   # one contract was nearest both deltas: no spread
    lng = g[g.is25].sort_values("delta", ascending=False).head(1)
    sht = g[g.is12].sort_values("delta").head(1)
    if lng.empty or sht.empty:
        continue
    L, S = lng.iloc[0], sht.iloc[0]
    if not (S.strike > L.strike):
        continue
    width = S.strike - L.strike
    dl, ds = _entry_cost(L.bid, L.ask, +1), _entry_cost(S.bid, S.ask, -1)
    debit = dl - ds
    if not np.isfinite(debit) or debit <= 0.02 or debit >= width:
        continue                                   # no edge to measure in a spread priced at/over width

    pl, ps = _path_marks(tk, exp, L.strike, td), _path_marks(tk, exp, S.strike, td)
    if pl is None or ps is None:
        continue
    j = pl.merge(ps, on="trade_date", suffixes=("_l", "_s"))
    if j.empty:
        continue

    out = dict(ticker=tk, date=td, kind="event" if _is_event(td) else "control",
               width=width, debit=debit, max_ret=width / debit - 1,
               dte=int(L.dte), d_long=L.delta, d_short=S.delta)

    # Run every arm at the house fill (mid +/- 25% of the spread, per leg, both ways) AND at mid.
    # The spread crosses FOUR bid/asks round trip against the naked call's two, so the two regimes
    # separate "the cap removed the tail" from "the extra leg's friction ate the edge".
    for fill, sfx_f in ((FILL, ""), (0.0, "_mid")):
        el = (L.bid + L.ask) / 2 + fill * (L.ask - L.bid)
        es = (S.bid + S.ask) / 2 + fill * (S.ask - S.bid)      # naked 0.12d: pay up
        cs = (S.bid + S.ask) / 2 - fill * (S.ask - S.bid)      # short leg: receive less
        deb = el - cs
        if not np.isfinite(deb) or deb <= 0.02 or deb >= width or el <= 0.02 or es <= 0.02:
            continue
        sell_l = ((j.bid_l + j.ask_l) / 2 - fill * (j.ask_l - j.bid_l)).clip(lower=0)
        buy_s = ((j.bid_s + j.ask_s) / 2 + fill * (j.ask_s - j.bid_s)).clip(lower=0)
        sell_s = ((j.bid_s + j.ask_s) / 2 - fill * (j.ask_s - j.bid_s)).clip(lower=0)
        series = (("spread", (sell_l - buy_s).clip(lower=0, upper=width).values, deb),
                  ("naked25", sell_l.values, el),
                  ("naked12", sell_s.values, es))
        for lab, arr, cost in series:
            out[f"{lab}_hold{sfx_f}"] = arr[-1] / cost - 1
            for n, sx in ((5, "5d"), (10, "10d")):
                out[f"{lab}_{sx}{sfx_f}"] = arr[min(n, len(arr)) - 1] / cost - 1
        if fill == FILL:
            out["debit"] = deb; out["max_ret"] = width / deb - 1

    rows.append(out)

T = pd.DataFrame(rows)
T.to_parquet("data/cache/event_convexity/spread_trades.parquet", index=False)
ARMS = ["hold", "5d", "10d"]
LABS = ["spread", "naked25", "naked12"]
print(f"{len(T):,} constructible spreads | {(T.kind=='event').sum():,} event / {(T.kind=='control').sum():,} control")
print(f"median width ${T.width.median():.1f} | median debit ${T.debit.median():.2f} "
      f"({100*(T.debit/T.width).median():.0f}% of width) | median MAX return {100*T.max_ret.median():.0f}%")
print(f"median long delta {T.d_long.median():.3f} | median short delta {T.d_short.median():.3f} | median DTE {T.dte.median():.0f}")


def dist(x, col):
    s = x[col].dropna()
    return dict(n=len(s), mean=100 * s.mean(), median=100 * s.median(),
                p_2x=100 * (s >= 1).mean(), p_5x=100 * (s >= 4).mean(),
                p_10x=100 * (s >= 9).mean(), p_tot_loss=100 * (s <= -0.95).mean(), best=100 * s.max())


for lab in LABS:
    for k in ("event", "control"):
        x = T[T.kind == k]
        print(f"\n=== {lab} — {k} ({len(x):,}) ===")
        print(pd.DataFrame({a: dist(x, f"{lab}_{a}") for a in ARMS}).T.round(2).to_string())

print("\n\n=== EVENT MINUS CONTROL (percentage points) — this is the finding ===")
e, c = T[T.kind == "event"], T[T.kind == "control"]
for sfx_f, title in (("", "house fill: mid +/- 25% of spread, per leg"), ("_mid", "mid-to-mid, zero friction")):
    tab = {}
    for lab in LABS:
        for a in ARMS:
            col = f"{lab}_{a}{sfx_f}"
            if col not in T:
                continue
            tab[f"{lab}_{a}"] = dict(
                event_mean=100 * e[col].mean(), control_mean=100 * c[col].mean(),
                gap_pp=100 * (e[col].mean() - c[col].mean()),
                p5x_gap_pp=100 * ((e[col] >= 4).mean() - (c[col] >= 4).mean()),
                tot_loss_evt=100 * (e[col] <= -0.95).mean())
    print(f"\n--- {title} ---")
    print(pd.DataFrame(tab).T.round(2).to_string())

print("\n=== friction cost: house fill minus mid, event entries, mean pp ===")
for lab in LABS:
    for a in ARMS:
        if f"{lab}_{a}_mid" in T:
            d = 100 * (e[f"{lab}_{a}"].mean() - e[f"{lab}_{a}_mid"].mean())
            print(f"  {lab:>8} {a:>4}: {d:+7.2f} pp")

print("\n=== does the cap bind? share of EVENT trades whose naked leg beat the spread's max ===")
for a in ARMS:
    binds = (e[f"naked25_{a}"] > e.max_ret).mean() * 100
    print(f"  {a:>4}: {binds:5.1f}% of event trades had the long leg exceed the spread's capped max return")
