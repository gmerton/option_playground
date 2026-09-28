#!/usr/bin/env python3
"""
SINCLAIR: SELL VOL IN CONTANGO, BUY IT IN BACKWARDATION -- does the VIX term structure sort index vol-selling returns?
(pre-registered 2026-09-28, before the run; Gabe typed the rule from Euan Sinclair, "Positional Option Trading" (2020):
"Sell VIX futures or index options when the term structure is in contango. Buy VIX futures or index options when the
term structure is in backwardation.")

WHY NEW. The ledger has the VIX LEVEL (the certified stress bucket sells SPY puts when VIX >= 20 and SPY < 50MA) and
the curve as a coincident drawdown WARNING (tastylive batch 2026-09-23: VIX/VIX3M >= 1 in 7/7 >= 10% drawdowns, but
only after the index is already down 3-9%). The curve as a GATE on the P&L was specced there and never run. It also
cuts straight against the certified trade: VIX >= 20 is when the curve tends to invert, and Sinclair says BUY then.

CURVE    R = VIX / VIX3M at the entry close (CBOE daily histories, VIX3M from 2009-09). BACKWARDATION = R >= 1,
         CONTANGO = R < 1. (VIX3M is the standard proxy for the VX1/VX2 futures slope; we hold no futures data.)
PRIMARY  the certified stress bucket, i.e. the 113 paired regime entries of stress_bucket_h2h_2026-09-28.csv (20-DTE
         0.25/0.15 SPY bull put, 50% take, no stop, real fills; ROC on width - credit). Statistic: ROC(backwardation) -
         ROC(contango), OLS on a backwardation dummy, SEs clustered by entry month. Sinclair predicts < 0.
         BAR: a curve GATE on the stress bucket is ADOPTED only if the difference is < 0 with t <= -3, both halves
         (split 2018-01) negative. A difference that is NOT negative means the certified trade already sells into
         backwardation profitably and the rule, applied to this book, is contradicted.
SECONDARY (a) the same split on the 45-DTE 12-delta naked put inside the regime (roc_B, same entries).
         (b) all 748 weekly always-on 45-DTE 12-delta SPY put sales (always_on_index_put_2026-09-26.csv, % of Reg-T
         margin, ARM A 50% take / 21-DTE close): OLS of return on [backwardation dummy, VIX level, certified-regime
         dummy], month-clustered -- does the curve carry information BEYOND the VIX level and the regime?
         (c) Sinclair's SELL leg as a stand-alone rule: sell the 45-DTE put in every CONTANGO week (mean, month-clustered
         t, halves, per year, worst trade) vs the certified rule.
         (d) the BUY leg: buying that put in backwardation weeks earns -(the sale) minus both sides' costs; reported
         from (b), not simulated separately.
TERTIARY the VIX-futures leg via UVXY (1.5x short-term VIX futures; data from 2018-03 when the leverage changed):
         Friday close -> next Friday close. Rule: SHORT in contango, LONG in backwardation, flat never. Costs 10 bp per
         side + 20%/yr borrow on the short (declared; UVXY borrow is often higher). Weekly returns, Newey-West t (lag 4).
         Compared with ALWAYS-SHORT (the carry, no timing): the timing adds value only if the rule beats always-short.
EXPLORATORY a deeper inversion threshold (R >= 1.05) for the primary; no bar.
PRIOR    the stress bucket's profits come from selling fear after it spikes, which is often backwardation, so expect
         the primary NOT negative (Sinclair's buy leg contradicted on this book). Contango selling alone ~= the weak
         always-on complement (+0.67%, t 1.7). Short UVXY in contango = the famous carry trade with fat left tails.
Local (cached CSVs, one CBOE download, minutes).

Run: PYTHONPATH=src:. .venv/bin/python3 run_vix_term_structure.py   (log -> data/studies/logs/vix_term_structure.log)
"""
from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/vix_term_structure.log"
CURVE = REPO / "data/cache/vix_term_cboe.parquet"
SPLIT = "2018-01-01"
URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{}_History.csv"


def curve() -> pd.Series:
    if not CURVE.exists():
        s = {}
        for k in ("VIX", "VIX3M"):
            raw = urllib.request.urlopen(URL.format(k), timeout=60).read().decode()
            d = pd.read_csv(io.StringIO(raw))
            d["DATE"] = pd.to_datetime(d.DATE)
            s[k] = d.set_index("DATE").CLOSE
        pd.DataFrame(s).dropna().rename_axis("trade_date").reset_index().to_parquet(CURVE, index=False)
    d = pd.read_parquet(CURVE).set_index("trade_date")
    return (d.VIX / d.VIX3M).rename("R")


def attach(df, R, col="trade_date"):
    r = R.reindex(pd.to_datetime(df[col]), method="ffill")
    return df.assign(R=r.values, bw=(r.values >= 1.0))


def cl_ols(y, X, g):
    fit = sm.OLS(y, sm.add_constant(X.astype(float))).fit(cov_type="cluster", cov_kwds={"groups": g})
    return fit


def mclu(x, d):
    g = x.groupby(d.dt.to_period("M")).mean()
    return g.mean(), g.mean() / g.std(ddof=1) * np.sqrt(len(g))


def nw_t(x, lag=4):
    x = pd.Series(x).dropna(); fit = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    return float(fit.tvalues[0])


def split_line(M, col, lab, out, thr=1.0):
    M = M.assign(b=M.R >= thr)
    g = M.trade_date.dt.to_period("M").astype(str).factorize()[0]
    f = cl_ols(M[col].values, M[["b"]], g)
    d, t = f.params.iloc[1], f.tvalues.iloc[1]
    h = M.trade_date < SPLIT
    h1 = M[h & M.b][col].mean() - M[h & ~M.b][col].mean()
    h2 = M[~h & M.b][col].mean() - M[~h & ~M.b][col].mean()
    out.append(f"  {lab}: backwardation n {int(M.b.sum())} ROC {M[M.b][col].mean():+.2f}% (worst {M[M.b][col].min():+.1f}) | "
               f"contango n {int((~M.b).sum())} ROC {M[~M.b][col].mean():+.2f}% (worst {M[~M.b][col].min():+.1f}) -> "
               f"diff {d:+.2f}pp t {t:+.2f} halves {h1:+.2f} / {h2:+.2f}")
    return d, t, h1, h2


def main():
    R = curve()
    out = ["# Sinclair: VIX term structure as a vol-selling gate (pre-registration in the docstring)",
           f"curve: VIX/VIX3M {R.index.min().date()} -> {R.index.max().date()}; backwardation on {100 * (R >= 1).mean():.0f}% of days"]
    # PRIMARY
    M = attach(pd.read_csv(REPO / "data/studies/stress_bucket_h2h_2026-09-28.csv", parse_dates=["trade_date"]), R)
    M = M.dropna(subset=["R"])
    out.append(f"\n## PRIMARY: certified stress bucket, {len(M)} entries (median R {M.R.median():.3f}; "
               f"{100 * M.bw.mean():.0f}% in backwardation)")
    prim = split_line(M, "roc_A", "20-DTE spread (ROC on width-credit)  *PRIMARY*", out)
    split_line(M, "roc_B", "45-DTE 12d naked (ROC on Reg-T)     (a)", out)
    split_line(M, "roc_A", "EXPLORATORY R >= 1.05, spread       ", out, thr=1.05)
    # SECONDARY (b)-(d)
    A = attach(pd.read_csv(REPO / "data/studies/always_on_index_put_2026-09-26.csv", parse_dates=["trade_date"]), R).dropna(subset=["R"])
    g = A.trade_date.dt.to_period("M").astype(str).factorize()[0]
    X = pd.DataFrame({"backwardation": A.bw, "vix": A.vix, "cert": A.cert})
    f = cl_ols(A.retA.values, X, g)
    out.append(f"\n## SECONDARY (b): all {len(A)} weekly 45-DTE 12d put sales (% of Reg-T), month-clustered OLS")
    out.append("  " + "  ".join(f"{k} {f.params[k]:+.3f} (t {f.tvalues[k]:+.2f})" for k in ["const", "backwardation", "vix", "cert"]))
    f0 = cl_ols(A.retA.values, A[["bw"]], g)
    out.append(f"  backwardation alone: {f0.params.iloc[1]:+.2f}pp t {f0.tvalues.iloc[1]:+.2f} (bw n {int(A.bw.sum())}, contango n {int((~A.bw).sum())})")
    for lab, s in (("contango weeks (Sinclair SELL rule)", A[~A.bw]), ("certified regime (book rule)", A[A.cert]),
                   ("backwardation weeks", A[A.bw]), ("contango AND not certified", A[~A.bw & ~A.cert])):
        m, t = mclu(s.retA, s.trade_date); h = s.trade_date < SPLIT
        yr = s.groupby(s.trade_date.dt.year).retA.mean()
        out.append(f"  (c) {lab:34s} n {len(s):3d}: {m:+.2f}%/trade t {t:+.2f} halves {s[h].retA.mean():+.2f} / {s[~h].retA.mean():+.2f} "
                   f"yrs+ {(yr > 0).sum()}/{len(yr)} worst {s.retA.min():+.1f}%")
    bwA = A[A.bw]
    cost_rt = 2 * (0.25 * bwA.spr_pct * bwA.credit + 0.0065) / bwA.margin * 100 if "spr_pct" in bwA else np.nan
    out.append(f"  (d) BUY leg in backwardation weeks ≈ -(sale) - round-trip cost: {-bwA.retA.mean() - np.nanmean(cost_rt):+.2f}% of the same margin "
               f"(the sale earned {bwA.retA.mean():+.2f}%)")
    # TERTIARY: UVXY
    u = pd.read_parquet(REPO / "data/cache/UVXY_stock.parquet")
    u["trade_date"] = pd.to_datetime(u.trade_date)
    u = u.set_index("trade_date").close.sort_index()
    u = u[u.index >= "2018-03-01"]
    fri = u.groupby(u.index.to_period("W")).tail(1)
    wk = pd.DataFrame({"px": fri})
    wk["ret"] = wk.px.shift(-1) / wk.px - 1
    wk["R"] = R.reindex(wk.index, method="ffill").values
    wk = wk.dropna()
    wk["bw"] = wk.R >= 1
    borrow = 0.20 / 52
    short = -wk.ret - 0.002 - borrow
    long_ = wk.ret - 0.002
    rule = np.where(wk.bw, long_, short)
    out.append(f"\n## TERTIARY: UVXY weekly {wk.index.min().date()} -> {wk.index.max().date()} ({len(wk)} weeks, {int(wk.bw.sum())} backwardation)")
    for lab, x in (("Sinclair rule (short contango / long backwardation)", pd.Series(rule, index=wk.index)),
                   ("always short (carry, no timing)", short), ("short in contango only, flat otherwise", short.where(~wk.bw, 0.0)),
                   ("long in backwardation only, flat otherwise", long_.where(wk.bw, 0.0))):
        cum = (1 + x).prod() - 1
        out.append(f"  {lab:48s} mean {100 * x.mean():+.2f}%/wk NW t {nw_t(x):+.2f} worst week {100 * x.min():+.1f}% "
                   f"compounded {100 * cum:+.0f}%")
    d = pd.Series(rule, index=wk.index) - short
    out.append(f"  timing value = rule - always short: {100 * d.mean():+.2f}%/wk NW t {nw_t(d):+.2f}")
    d, t, h1, h2 = prim
    ok = d < 0 and t <= -3 and h1 < 0 and h2 < 0
    out.append(f"\nVERDICT (PRIMARY): {'ADOPTED gate: skip backwardation entries' if ok else ('CONTRADICTED on this book: backwardation entries do NOT underperform' if d >= 0 else 'NOT MET (backwardation worse but not at the bar)')}")
    M.to_csv(REPO / "data/studies/vix_term_structure_2026-09-28.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
