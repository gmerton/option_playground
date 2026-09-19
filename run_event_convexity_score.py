#!/usr/bin/env python3
"""
Event convexity: is buying cheap OTM calls into a SCHEDULED event a positive-expectancy lottery?

Motivating instance: Tito's 2024 election calls (0.12 / 0.23 delta, ~40x). Means are the wrong statistic for
this -- the question is the RIGHT TAIL. So this reports the full distribution: median, mean, and P(>=2x, 5x, 10x).

Entries (run_event_convexity_pull.py): 0.12 and 0.25 delta calls, 10-45 DTE, on the 40 highest-ADR liquid
names, bought the session BEFORE each scheduled event (55 FOMC + 3 elections) and, as control, on mid-month
Wednesdays in the same months with no event within 3 sessions.
Fills: buy at mid + 25% of the spread, sell at mid - 25%. Exits: hold to the last quote before expiry, or
take profit at +100 / +200 / +500% (first daily close through it), or sell 5 / 10 sessions in.

Usage: PYTHONPATH=src .venv/bin/python3 run_event_convexity_score.py > data/studies/event_convexity_2026-09-18.log
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); pd.set_option("display.width", 220)

E = pd.read_parquet("data/cache/event_convexity/entries.parquet")
P = pd.read_parquet("data/cache/event_convexity/paths.parquet")
for d in (E, P):
    d["trade_date"] = pd.to_datetime(d.trade_date); d["expiry"] = pd.to_datetime(d.expiry)
ev = json.load(open("data/fomc_dates.json"))
EVT = set(pd.to_datetime(ev["scheduled"])) | set(pd.to_datetime(["2020-11-03", "2022-11-08", "2024-11-05"]))
# an entry is an "event" entry if the NEXT session is an event day
nxt = {d: True for d in EVT}
P = P.sort_values("trade_date")
key = ["ticker", "expiry", "strike"]
paths = {k: g for k, g in P.groupby(key, sort=False)}

rows = []
for r in E.itertuples(index=False):
    g = paths.get((r.ticker, r.expiry, r.strike))
    if g is None:
        continue
    entry = (r.bid + r.ask) / 2 + 0.25 * (r.ask - r.bid)
    if not np.isfinite(entry) or entry <= 0.02:
        continue
    fwd = g[(g.trade_date > r.trade_date) & (g.trade_date <= r.expiry)]
    if fwd.empty:
        continue
    mid = (fwd.bid + fwd.ask) / 2
    sell = (mid - 0.25 * (fwd.ask - fwd.bid)).clip(lower=0).values
    out = dict(ticker=r.ticker, date=r.trade_date, delta=r.delta,
               kind="event" if any((r.trade_date < d <= r.trade_date + pd.Timedelta(days=5)) and d in EVT
                                   for d in EVT) else "control",
               hold_expiry=sell[-1] / entry - 1)
    for mult, lab in ((2.0, "tp_100"), (3.0, "tp_200"), (6.0, "tp_500")):
        hit = np.flatnonzero(sell >= entry * mult)
        out[lab] = (mult - 1) if len(hit) else sell[-1] / entry - 1
    for n, lab in ((5, "sell_5d"), (10, "sell_10d")):
        out[lab] = (sell[min(n, len(sell)) - 1] / entry - 1)
    rows.append(out)
T = pd.DataFrame(rows)
T["bucket"] = np.where(T.delta <= 0.18, "0.12d (far OTM)", "0.25d")
T.to_parquet("data/cache/event_convexity/trades.parquet", index=False)
ARMS = ["hold_expiry", "tp_100", "tp_200", "tp_500", "sell_5d", "sell_10d"]
print(f"{len(T):,} call purchases | {(T.kind=='event').sum():,} event / {(T.kind=='control').sum():,} control")

def dist(x, arm):
    s = x[arm].dropna()
    return dict(n=len(s), mean=100 * s.mean(), median=100 * s.median(),
                p_2x=100 * (s >= 1).mean(), p_5x=100 * (s >= 4).mean(), p_10x=100 * (s >= 9).mean(),
                p_total_loss=100 * (s <= -0.95).mean(), best=100 * s.max())

for b in sorted(T.bucket.unique()):
    for k in ("event", "control"):
        x = T[(T.bucket == b) & (T.kind == k)]
        if len(x) < 50:
            continue
        print(f"\n=== {b} — {k} ({len(x):,}) ===")
        print(pd.DataFrame({a: dist(x, a) for a in ARMS}).T.round(2).to_string())

print("\n=== event minus control (percentage points) ===")
for b in sorted(T.bucket.unique()):
    e, c = T[(T.bucket == b) & (T.kind == "event")], T[(T.bucket == b) & (T.kind == "control")]
    if len(e) < 50 or len(c) < 50:
        continue
    d = {a: dict(mean_pp=100 * (e[a].mean() - c[a].mean()), p5x_pp=100 * ((e[a] >= 4).mean() - (c[a] >= 4).mean()),
                 p10x_pp=100 * ((e[a] >= 9).mean() - (c[a] >= 9).mean())) for a in ARMS}
    print(f"\n{b}:"); print(pd.DataFrame(d).T.round(2).to_string())

el = T[T.date.isin(pd.to_datetime(["2020-11-02", "2022-11-07", "2024-11-04"]))]
if len(el):
    print(f"\n=== the 3 election-eve dates only ({len(el)} purchases) ===")
    print(pd.DataFrame({a: dist(el, a) for a in ARMS}).T.round(2).to_string())
