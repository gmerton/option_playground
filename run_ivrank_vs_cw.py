#!/usr/bin/env python3
"""
IV RANK vs CREDIT/WIDTH: which one actually ranks single-name bull put spreads? (pre-registered 2026-09-22)

WHY. Two creators give two different cross-sectional sorts for the same trade, and we have tested only one.
  * OptionsPlay ranks candidates by **credit / width**. We tested it and ADOPTED it: net ROC −2.96% (cheapest
    quintile) → +4.07% (richest), top−bottom **+8.57pp t 3.74**, both halves; **within-date +7.64pp t 4.15**;
    holds in the low-VIX tercile (+9.17) and the high (+7.84). It cleared Sidak by a hair (p 0.00037 vs the
    BH rank-1 line 0.00038 at M=133). ⚠ And it works ACROSS names only — dialling credit/width with your own
    wing does nothing (ARM B null; inside the certified cell it INVERTS, −10.14pp t −1.23).
  * Sosnoff (OptionsPlay interview 2024-10-14) selects by **IV RANK** — "only sell premium in high-IV-rank
    names" — and in the same hour denies that cross-sectional richness exists at all. Untested here.

THE QUESTION IS NOT "does IV rank work" BUT "does it add anything beyond credit/width, or vice versa".
They may be the same fact twice: credit/width's mechanism IS entry IV, so a rich spread is usually a
high-IV spread. But they differ in one important way — **IV rank is own-history-relative and therefore NOT
comparable across names** (a 90th-percentile TLT is not a 90th-percentile TSLA), whereas credit/width is an
absolute, dimensionless price. That is the reason to expect cw to win.

⭐ WHY IT MATTERS EVEN IF cw WINS: IV rank needs no option chain — it is computable from an IV series alone.
If ivr were competitive it would be far cheaper to run live. So this is worth knowing either way.

DATA: the same 18-name Friday chain cache as run_premium_to_width.py (options_daily_v3, real bid/ask +
greeks, 2019-10 → 2026-01), RAW spot from lib.studies.chain_spot, held to expiry, credit at a REAL FILL
(short bid − long ask − commissions). Structure held FIXED at the 30d short / 20d wing, exactly as ARM A.

IV RANK, defined before looking: for each name, the 30-delta short leg's IV series on the Friday grid.
  ivr  = (iv − min(prior 52 obs)) / (max − min)   — the classic definition Sosnoff uses
  ivp  = share of the prior 52 obs below today's iv   — the percentile form OUR straddle gate uses
Both need >= 30 prior observations, else the row is dropped. Strictly trailing: the current obs is excluded
from its own window, so there is no look-ahead.

PRE-REGISTERED, primary — ONE cell: in a month-clustered joint regression of net ROC on BOTH standardised
sorts, does **ivr** carry a coefficient with |t| >= 2 after cw is included? That is the whole question.
  PASS for ivr  = ivr survives the joint fit.
  PASS for cw   = cw survives (expected; this is a replication check on a result we already adopted).
Secondary, reported but not decisive: marginal quintiles of each, the 5x5 double sort, and the same fit
run within-date (date-demeaned) so the market's own IV level is removed.

PRIOR (stated before running): cw wins and subsumes ivr. If ivr wins instead, it matters a lot.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 -u run_ivrank_vs_cw.py
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from lib.studies.chain_spot import spot_from_chain

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)
COMM, WIN = 0.0065, 52
MIN_OBS = 30

raw = pd.read_parquet("data/cache/ivrank_vehicle_chains.parquet")
raw["trade_date"] = pd.to_datetime(raw.trade_date).dt.normalize()
raw["expiry"] = pd.to_datetime(raw.expiry).dt.normalize()
SPOT = spot_from_chain(raw, delta="d")


def pick(g, target):
    if g.empty: return None
    r = g.iloc[(g.d.abs() - target).abs().argsort()[:1]].iloc[0]
    return r if abs(abs(r.d) - target) <= 0.06 else None


rows = []
for (tk, d), g in raw.groupby(["ticker", "trade_date"]):
    g = g.copy(); g["gap"] = (g.dte - 30).abs()
    exp = g.sort_values("gap").expiry.iloc[0]; g = g[(g.expiry == exp) & (g.cp == "P")]
    short = pick(g, 0.30)
    if short is None: continue
    lng = pick(g, 0.20)
    if lng is None or lng.strike >= short.strike: continue
    ST, S = SPOT.get((tk, exp), np.nan), SPOT.get((tk, d), np.nan)
    if not (np.isfinite(ST) and np.isfinite(S)): continue
    width = short.strike - lng.strike
    credit = (short.bid - lng.ask) - 2 * COMM
    if credit <= 0 or credit >= width: continue
    loss = min(max(short.strike - ST, 0.0), width)
    rows.append(dict(sym=tk, date=d, width=width, credit=credit, cw=credit / width,
                     roc=(credit - loss) / (width - credit), win=(credit - loss) > 0,
                     iv=float(short.iv)))
T = pd.DataFrame(rows).sort_values(["sym", "date"]).reset_index(drop=True)

# ── IV rank / percentile, strictly trailing, per name ─────────────────────────
def add_ivr(x):
    s = x.iv
    lo = s.shift(1).rolling(WIN, min_periods=MIN_OBS).min()
    hi = s.shift(1).rolling(WIN, min_periods=MIN_OBS).max()
    x["ivr"] = (s - lo) / (hi - lo).replace(0, np.nan)
    x["ivp"] = s.shift(1).rolling(WIN, min_periods=MIN_OBS).apply(
        lambda w: np.nan, raw=True)          # placeholder, filled below
    pct = []
    arr = s.to_numpy()
    for i in range(len(arr)):
        j0 = max(0, i - WIN)
        w = arr[j0:i]
        pct.append(np.nan if len(w) < MIN_OBS else float((w < arr[i]).mean()))
    x["ivp"] = pct
    return x

T = T.groupby("sym", group_keys=False).apply(add_ivr)
T["month"] = T.date.dt.to_period("M")
T = T.dropna(subset=["ivr", "ivp"])
print(f"{len(T):,} spreads · {T.sym.nunique()} names · {T.date.nunique()} dates · {T.month.nunique()} months")
print(f"corr(cw, ivr) {T.cw.corr(T.ivr):+.3f}   corr(cw, iv) {T.cw.corr(T.iv):+.3f}   corr(ivr, ivp) {T.ivr.corr(T.ivp):+.3f}\n")


def mt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def quintiles(col, label):
    A = T.copy(); A["q"] = pd.qcut(A[col], 5, labels=False, duplicates="drop")
    tab = A.groupby("q").agg(n=("roc", "size"), sort=(col, "mean"),
                             net_roc=("roc", lambda x: 100 * x.mean()),
                             win=("win", lambda x: 100 * x.mean()), iv=("iv", "mean"))
    print(f"== marginal quintiles of {label} ==")
    print(tab.round(2).to_string())
    hi, lo = A[A.q == A.q.max()], A[A.q == 0]
    dd = (hi.groupby("month").roc.mean() - lo.groupby("month").roc.mean()).dropna()
    h1 = dd[dd.index < pd.Period("2022-07", "M")]; h2 = dd[dd.index >= pd.Period("2022-07", "M")]
    print(f"  top−bottom {100*dd.mean():+.2f}pp  month-clustered t {mt(dd):+.2f}  "
          f"halves {100*h1.mean():+.2f} / {100*h2.mean():+.2f}\n")


quintiles("cw", "CREDIT/WIDTH (adopted)")
quintiles("ivr", "IV RANK (Sosnoff)")
quintiles("ivp", "IV percentile (our straddle-gate form)")

print("== 5x5 double sort: mean net ROC % (rows = cw quintile, cols = ivr quintile) ==")
D = T.copy()
D["qcw"] = pd.qcut(D.cw, 5, labels=False, duplicates="drop")
D["qivr"] = pd.qcut(D.ivr, 5, labels=False, duplicates="drop")
print((D.pivot_table(index="qcw", columns="qivr", values="roc", aggfunc="mean") * 100).round(2).to_string())
print("\n   cell counts:")
print(D.pivot_table(index="qcw", columns="qivr", values="roc", aggfunc="size").to_string())

# ── PRIMARY: the joint fit ────────────────────────────────────────────────────
z = lambda s: (s - s.mean()) / s.std(ddof=0)
D["zcw"], D["zivr"], D["zivp"] = z(D.cw), z(D.ivr), z(D.ivp)
D["mstr"] = D.month.astype(str)
print("\n" + "=" * 96)
print("PRIMARY — month-clustered joint regression, net ROC on both standardised sorts")
print("=" * 96)
for f in ("roc ~ zcw", "roc ~ zivr", "roc ~ zcw + zivr"):
    m = smf.ols(f, D).fit(cov_type="cluster", cov_kwds={"groups": D.mstr})
    terms = " ".join(f"{k} {100*m.params[k]:+.2f}pp (t {m.tvalues[k]:+.2f})" for k in m.params.index if k != "Intercept")
    print(f"  {f:22s} {terms}")

print("\n  within-date (date-demeaned — the market's own IV level removed):")
for c in ("roc", "zcw", "zivr"):
    D[c + "_dm"] = D[c] - D.groupby("date")[c].transform("mean")
m = smf.ols("roc_dm ~ zcw_dm + zivr_dm - 1", D).fit(cov_type="cluster", cov_kwds={"groups": D.mstr})
print("   " + "  ".join(f"{k} {100*m.params[k]:+.2f}pp (t {m.tvalues[k]:+.2f})" for k in m.params.index))

mj = smf.ols("roc ~ zcw + zivr", D).fit(cov_type="cluster", cov_kwds={"groups": D.mstr})
print(f"\nVERDICT  cw survives the joint fit: {abs(mj.tvalues['zcw']) >= 2}   "
      f"ivr survives the joint fit: {abs(mj.tvalues['zivr']) >= 2}")
D.to_csv("data/studies/ivrank_vs_cw_2026-09-22.csv", index=False)
print("wrote data/studies/ivrank_vs_cw_2026-09-22.csv")
