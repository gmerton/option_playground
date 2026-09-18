#!/usr/bin/env python3
"""
Walk-forward + placebo for the MA-stack slack finding (2026-09-17). Sweeping the slack in the 10>20>50 rule made the
precision tier's mean R climb monotonically (strict +0.65 -> 1.0 ADR +1.21) and turned 2021/2022 positive. That sweep
was in-sample over 13 variants. This script asks whether it survives the house bar.

Design -- ONE event pool, so only the run-length definition varies:
  pool  = every 15-day pivot breakout (gate, RVOL >= 1.1, upper-half close, gap < 5%, day < 8%, prior close under the
          pivot) with ADR 4-7 and within 15% of the 52-week high, 2019-10 .. 2026-09. Hold = the Tito trail used in
          run_adhikary_validation.py (stop: close under the entry bar's low; exit: first close under the 20 EMA; 60-session
          cap); R = return / (entry - entry-day low).
  tier(slack) = pool events whose stacked run under that slack is 5..40 sessions.
  train = entry <= 2022-12-31, test = 2023-01-01 on. Pick the slack on train only (mean R), read it on test.
  SEs cluster by entry month. Placebo: permute the run-length values across pool events WITHIN the same month
  (keeps the time structure and the tier's monthly share, destroys the link between run and outcome), 500 draws.

Usage: PYTHONPATH=src .venv/bin/python3 run_stack_slack_walkforward.py
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
from lib.regime.trailing import Panel, liquidity_mask
from lib.commons.ma_stack import stack_run

warnings.filterwarnings("ignore")
SLACKS = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]          # in ADR units
SPLIT = pd.Timestamp("2022-12-31")

raw = pd.read_parquet("data/cache/liquid_panel_2019.parquet"); raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
p = Panel.from_long(raw); O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
e20 = C.ewm(span=20, adjust=False).mean()
adr = (H / L - 1).shift(1).rolling(20).mean() * 100
hi52, lo52 = H.shift(1).rolling(252, min_periods=120).max(), L.shift(1).rolling(252, min_periods=120).min(); range52 = (hi52 - lo52) / C * 100
piv15 = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
gate = (adr >= 3) & (range52 >= 17) & elig
pool = gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15) & (adr >= 4) & (adr <= 7) & (C / hi52 - 1 > -0.15)
pool = pool.fillna(False); pool = pool[pool.index >= "2019-10-01"]
ii, jj = np.where(pool.values); ii = ii + (len(C) - len(pool)); idx = C.index
Cv, Lv, E20v = C.values, L.values, e20.values


def trail(i, j):
    entry, stop = Cv[i, j], Lv[i, j]
    if not np.isfinite(entry) or not np.isfinite(stop) or entry <= stop: return np.nan
    for k in range(i + 1, min(i + 61, len(Cv))):
        c = Cv[k, j]
        if not np.isfinite(c): continue
        if c < stop or c < E20v[k, j]: return (c - entry) / (entry - stop)
    k = min(i + 60, len(Cv) - 1); return (Cv[k, j] - entry) / (entry - stop)


ev = pd.DataFrame({"date": idx[ii], "j": jj, "R": [trail(i, j) for i, j in zip(ii, jj)]}).dropna()
ev["month"] = ev["date"].dt.to_period("M"); ev["train"] = ev["date"] <= SPLIT
runs = {s: stack_run(C, fuzz=0, tol_pct=0.0, tol_adr=s, adr=adr).values for s in SLACKS}
for s in SLACKS: ev[f"run{s}"] = runs[s][ii[ev.index], jj[ev.index]]
print(f"pool: {len(ev):,} precision-shaped breakouts ({ev['train'].sum():,} train 2019-10..2022, {(~ev['train']).sum():,} test 2023..2026)  pool mean R {ev['R'].mean():+.3f}")


def stat(d, mask):
    x = d.loc[mask, "R"]; y = d.loc[~mask, "R"]
    dm = d.assign(t=np.where(mask, d["R"], np.nan), o=np.where(~mask, d["R"], np.nan)).groupby("month")[["t", "o"]].mean().dropna()
    diff = dm["t"] - dm["o"]; t = diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff)))
    return len(x), x.mean(), y.mean(), t, 100 * (x > 0).mean()


print("\n== tier(slack) = run 5..40 sessions, vs the REST of the pool | t = month-clustered t of (tier - rest) ==")
print(f"  {'slack':>6}  {'--- TRAIN 2019-22 ---':^44}   {'--- TEST 2023-26 ---':^44}")
print(f"  {'(ADR)':>6}  {'n':>5} {'tier R':>7} {'rest R':>7} {'t':>6} {'win%':>5}   {'n':>5} {'tier R':>7} {'rest R':>7} {'t':>6} {'win%':>5}")
res = {}
for s in SLACKS:
    m = ev[f"run{s}"].between(5, 40)
    tr = stat(ev[ev["train"]], m[ev["train"]]); te = stat(ev[~ev["train"]], m[~ev["train"]]); res[s] = (tr, te)
    print(f"  {s:>6.2f}  {tr[0]:5d} {tr[1]:+7.2f} {tr[2]:+7.2f} {tr[3]:+6.2f} {tr[4]:5.0f}   {te[0]:5d} {te[1]:+7.2f} {te[2]:+7.2f} {te[3]:+6.2f} {te[4]:5.0f}")
best = max(SLACKS, key=lambda s: res[s][0][1]); print(f"\n  chosen on TRAIN alone: slack {best} ADR (train tier R {res[best][0][1]:+.2f})  ->  TEST tier R {res[best][1][1]:+.2f} vs strict tier {res[0.0][1][1]:+.2f} and rest {res[best][1][2]:+.2f}")

print("\n== where the tier's edge sits: test-period R by run-length bucket, strict vs chosen slack ==")
for s in (0.0, best):
    d = ev[~ev["train"]]; b = pd.cut(d[f"run{s}"], [-1, 0, 4, 10, 20, 40, 10000], labels=["not stacked", "1-4", "5-10", "11-20", "21-40", ">40"])
    g = d.groupby(b, observed=True)["R"].agg(["size", "mean"]); print(f"  slack {s}: " + "  ".join(f"{k} n={int(v['size'])} R{v['mean']:+.2f}" for k, v in g.iterrows()))

print(f"\n== PLACEBO (500 draws): permute run-lengths across pool events within the same month, chosen slack {best}, TEST period ==")
rng = np.random.default_rng(7); d = ev[~ev["train"]].copy(); actual = d.loc[d[f"run{best}"].between(5, 40), "R"].mean(); draws = []
for _ in range(500):
    r = d.groupby("month")[f"run{best}"].transform(lambda x: rng.permutation(x.values)); draws.append(d.loc[r.between(5, 40), "R"].mean())
draws = np.array(draws); print(f"  actual tier R {actual:+.3f}   placebo mean {draws.mean():+.3f}  p95 {np.quantile(draws, .95):+.3f}  p99 {np.quantile(draws, .99):+.3f}   p-value {(draws >= actual).mean():.3f}")
print("\n== year by year, chosen slack vs strict (tier R, n) ==")
for y, d in ev.groupby(ev["date"].dt.year):
    a = d[d[f"run{best}"].between(5, 40)]["R"]; b = d[d["run0.0"].between(5, 40)]["R"]
    print(f"  {y}  slack {best}: n={len(a):4d} R {a.mean():+.2f}   strict: n={len(b):4d} R {b.mean():+.2f}")
