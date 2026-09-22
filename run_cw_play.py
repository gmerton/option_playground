#!/usr/bin/env python3
"""
THE CROSS-SECTIONAL CREDIT/WIDTH BULL PUT -- a play built from the 2026-09-22 finding (pre-registered here).

Finding (run_premium_to_width.py): with the structure held fixed at 30d/20d, ranking bull put spreads by
credit/width ACROSS names sorts net ROC: within-date top-minus-bottom +7.64pp, t 4.15, positive in both the low
and high VIX terciles -> name selection, not regime timing. Dialling credit/width with your own wing does nothing.

THE RULE (fixed before this run, no tuning afterwards):
  universe   the 20 liquid names with deep chains (the ivrank cache)
  every Friday, expiry closest to 30 DTE, build the 30d/20d bull put on every name
  RANK by credit/width; take the TOP QUINTILE (>= 4 names when 20 quote)
  equal RISK per position (each sized to the same dollar risk), hold to EXPIRY, no stop, no roll
  fills: sell the bid / buy the ask + $0.0065/leg; settle on the RAW spot from the chain
BENCHMARKS: (a) the same structure on ALL names each Friday (the no-selection book), (b) the bottom quintile,
  (c) delta-matched stock on the selected names (the vehicle benchmark that killed the generic put spread).
REPORTED: mean and median net ROC, win rate, month-clustered t, both halves (split 2022-07), per year, the worst
month, and the threshold/N neighbourhood (is it a plateau?).
STATUS THIS IS ALLOWED TO REACH: candidate for the forward lockbox. The selection rule was derived on this same
sample, so an in-sample backtest cannot promote it; what it CAN do is show whether the rule is tradeable at all
(enough names, enough credit, sane drawdown) and whether the effect is a plateau or a spike.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_cw_play.py
"""
from __future__ import annotations
import warnings
from math import sqrt
import numpy as np, pandas as pd
from lib.studies.chain_spot import spot_from_chain

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250)
COMM = 0.0065
raw = pd.read_parquet("data/cache/ivrank_vehicle_chains.parquet")
raw["trade_date"] = pd.to_datetime(raw.trade_date).dt.normalize(); raw["expiry"] = pd.to_datetime(raw.expiry).dt.normalize()
SPOT = spot_from_chain(raw, delta="d")
panel = pd.read_parquet("data/cache/liquid_panel_2019.parquet"); panel["date"] = pd.to_datetime(panel.date)
C = panel.pivot(index="date", columns="ticker", values="close").sort_index()


def pick(g, target):
    if g.empty: return None
    r = g.iloc[(g.d.abs() - target).abs().argsort()[:1]].iloc[0]
    return r if abs(abs(r.d) - target) <= 0.06 else None


rows = []
for (tk, d), g in raw.groupby(["ticker", "trade_date"]):
    g = g.copy(); g["gap"] = (g.dte - 30).abs()
    exp = g.sort_values("gap").expiry.iloc[0]; g = g[(g.expiry == exp) & (g.cp == "P")]
    s_, l_ = pick(g, 0.30), pick(g, 0.20)
    if s_ is None or l_ is None or l_.strike >= s_.strike: continue
    S, ST = SPOT.get((tk, d), np.nan), SPOT.get((tk, exp), np.nan)
    if not (np.isfinite(S) and np.isfinite(ST)): continue
    width = s_.strike - l_.strike; credit = (s_.bid - l_.ask) - 2 * COMM
    if credit <= 0 or credit >= width: continue
    loss = min(max(s_.strike - ST, 0.0), width)
    dlt = abs(s_.d) - abs(l_.d)
    rows.append(dict(sym=tk, date=d, expiry=exp, cw=credit / width, credit=credit, width=width,
                     roc=(credit - loss) / (width - credit), win=(credit - loss) > 0, iv=float(s_.iv),
                     stock_roc=dlt * (ST - S) / (width - credit), S=S, ST=ST))
T = pd.DataFrame(rows)
T["month"] = T.date.dt.to_period("M")
T["rank"] = T.groupby("date").cw.rank(pct=True)
T["n_quotes"] = T.groupby("date").sym.transform("size")
T = T[T.n_quotes >= 10]
print(f"{len(T):,} spreads · {T.sym.nunique()} names · {T.date.nunique()} Fridays · {T.month.nunique()} months "
      f"(median {T.n_quotes.median():.0f} names quoting per Friday)")


def mt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def book(sub, lab):
    if len(sub) < 50: return None
    m = sub.groupby("month").roc.mean()
    mid = pd.Period("2022-07", "M")
    yr = sub.groupby(sub.date.dt.year).roc.mean() * 100
    return dict(book=lab, trades=len(sub), per_yr=len(sub) / max((sub.date.max() - sub.date.min()).days / 365.25, 1),
                mean=100 * sub.roc.mean(), median=100 * sub.roc.median(), win=100 * sub.win.mean(),
                t=mt(m), h1=100 * m[m.index < mid].mean(), h2=100 * m[m.index >= mid].mean(),
                worst_month=100 * m.min(), yrs_pos=f"{int((yr > 0).sum())}/{len(yr)}",
                vs_stock=100 * (sub.roc - sub.stock_roc).mean())


out = [book(T[T["rank"] > 0.8], "TOP quintile by credit/width  <- the play"),
       book(T[T["rank"] > 0.6], "top 40%"), book(T, "ALL names (no selection)"),
       book(T[T["rank"] <= 0.2], "BOTTOM quintile")]
print("\n== the play vs its benchmarks (net ROC on capital at risk, held to expiry) ==")
print(pd.DataFrame([o for o in out if o]).round(2).to_string(index=False))

print("\n== neighbourhood: how deep to cut? ==")
rows2 = [book(T[T["rank"] > q], f"top {int((1-q)*100)}% by cw") for q in (0.9, 0.8, 0.7, 0.6, 0.5)]
print(pd.DataFrame([r for r in rows2 if r]).round(2).to_string(index=False))

print("\n== absolute cut instead of a rank (is there a level that matters?) ==")
rows3 = [book(T[T.cw >= c], f"cw >= {c:.2f}") for c in (0.15, 0.20, 0.25, 0.30, 0.35)]
print(pd.DataFrame([r for r in rows3 if r]).round(2).to_string(index=False))

sel = T[T["rank"] > 0.8]
print(f"\nplay composition: {sel.sym.nunique()} names ever selected; top 5 by share: "
      f"{(sel.sym.value_counts(normalize=True).head(5) * 100).round(0).to_dict()}")
print(f"median credit ${sel.credit.median():.2f} on a ${sel.width.median():.0f} wide spread "
      f"(cw {sel.cw.median():.2f}); median entry IV {sel.iv.median():.2f}")
eq = sel.groupby("month").roc.mean()
print(f"equity: mean month {100*eq.mean():+.2f}%, worst {100*eq.min():+.2f}%, "
      f"positive months {100*(eq>0).mean():.0f}%, longest losing streak "
      f"{max((len(list(g)) for k, g in __import__('itertools').groupby(eq < 0) if k), default=0)} months")
T.to_csv("data/studies/cw_play_2026-09-22.csv", index=False)
