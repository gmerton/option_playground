#!/usr/bin/env python3
"""
Option-implied SHORT signals on single names: IV smirk and put-call IV spread (pre-registered 2026-09-25, before
the first run; Gabe: "profitable short strategies on individual stocks").

WHY. Every price-pattern single-name short in the ledger has failed, and the failed-retest test showed why: the
breakdown EVENT carries no information (20d excess -0.02pp). Weak names drift UP in absolute terms (short-universe
test: 0/10 negative absolute). A short therefore needs INFORMATION the price does not yet show. The literature's
best-documented single-name candidates are option-implied, and they are a NEW axis here (the 9/24 put-burst test
used VOLUME; nothing in TEST_INDEX has used the IV surface's shape as a stock signal):
  SKEW  Xing, Zhang & Zhao (2010): steep smirk (OTM put IV - ATM call IV) -> lower next-week/-month returns.
  CW    Cremers & Weinbaum (2010): puts rich vs parity (low call IV - put IV, same strike/expiry) -> lower returns.

DESIGN
  data      silver.options_iv_daily (run_build_options_iv_daily.py; DTE 10-60, quoted legs, delta-selected so the
            RAW-strike problem does not arise). Price panel data/cache/liquid_panel_2009.parquet (adjusted);
            eligibility = the harness liquid mask (ADDV >= $50M, px >= $5) AND a signal value that day.
  window    formation dates 2010-02 -> 2026-02 (bid/ask ends ~Mar 2026; +20-session exits must land by then).
  formation weekly: the LAST session of each calendar week, signal as of that CLOSE.
  SIGNAL    SKEW: top decile of the cross-section that date. CW: bottom decile (puts richest).
  trade     SHORT at the next session's OPEN, cover at the close of session +h. Costs: 10 bp per side (harness
            SLIP) + 1.0%/yr borrow pro-rated (liquid names are usually general collateral; 1% is conservative).
  CONTROL   (declared now) same-date eligible NON-signal names in the same prior-20-session-return quintile x ADR
            tercile cell -- the smirk steepens after declines and in volatile names, so without holding those
            fixed the signal would just re-find momentum/volatility. Excess = signal names' mean forward return
            minus their matched cells' means.
  cells     {SKEW, CW} x {+20 (PRIMARY for SKEW), +5} = 4. PRIMARY = SKEW +20.
  t         month-clustered (formation-date excesses averaged per month; weekly formation with a 20d hold overlaps).
            Sidak(4) at 0.05 -> |t| >= 2.49; the house |t| >= 3 is stricter and GOVERNS.
  BAR       (declared now) a cell PASSES as a SHORT only if ALL of:
              (a) excess < 0 with |t| >= 3, (b) both halves (split 2018-01) negative, (c) the ABSOLUTE short P&L
              after costs + borrow > 0 (the stock must actually FALL, not merely lag), (d) negative excess in a
              majority of years. Per-year is printed.
            Fallback read, declared now so it cannot be invented later: a cell with (a)+(b)+(d) but not (c) is a
            long-book VETO candidate (avoid these names), NOT a short strategy.
  PRIOR     most likely: excess negative but absolute positive (the short-universe pattern), i.e. at best a veto.
  EXPLORATORY decile gradient of SKEW excess (+20); the PRIMARY within uptrend names (close > 50 SMA) -- where a
            veto would matter to the long book.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_iv_skew_short.py
       (log -> data/studies/logs/iv_skew_short.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.pattern_test import load_panel, SLIP

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/iv_skew_short.log"
PANEL = "data/cache/liquid_panel_2009.parquet"
IVC = REPO / "data/cache/options_iv_liquid.parquet"
START, END, SPLIT = "2010-02-01", "2026-02-27", "2018-01-01"
BORROW = 0.01
HORIZONS = (20, 5)


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def pull_iv(tickers):
    if IVC.exists():
        return pd.read_parquet(IVC)
    import awswrangler as wr
    from lib.constants import WORKGROUP, S3_OUTPUT
    lst = ",".join(f"'{t}'" for t in tickers)
    frames = []
    for y in range(2010, 2027):
        sql = f"SELECT ticker, trade_date, skew, cw, cw_pairs FROM silver.options_iv_daily WHERE year = {y} AND ticker IN ({lst})"
        df = wr.athena.read_sql_query(sql, database="silver", workgroup=WORKGROUP, data_source="AwsDataCatalog",
                                      s3_output=S3_OUTPUT, ctas_approach=False)
        print(f"  iv {y}: {len(df):,}", flush=True)
        frames.append(df)
    f = pd.concat(frames, ignore_index=True)
    f["trade_date"] = pd.to_datetime(f.trade_date)
    f.to_parquet(IVC, index=False)
    return f


def run_cell(sig, signal_mask_fn, P, form_idx, r20p, adr, up, h):
    """Per formation date: signal names' mean raw fwd return, matched-control mean, count."""
    O, C = P.open.values, P.close.values
    n = len(P.close.index)
    rows, names_rows = [], []
    for i in form_idx:
        if i + h >= n:
            continue
        s = sig[i]
        ok = np.isfinite(s) & P.elig.values[i] & np.isfinite(O[i + 1]) & np.isfinite(C[i + h]) \
            & np.isfinite(r20p[i]) & np.isfinite(adr[i])
        if ok.sum() < 100:
            continue
        fr = C[i + h] / O[i + 1] - 1
        sel = signal_mask_fn(s, ok)
        rq = pd.qcut(pd.Series(r20p[i, ok]), 5, labels=False, duplicates="drop").values
        aq = pd.qcut(pd.Series(adr[i, ok]), 3, labels=False, duplicates="drop").values
        cell = np.full(len(s), -1); cell[ok] = rq * 3 + aq
        ctl_mean = pd.Series(fr[ok & ~sel]).groupby(cell[ok & ~sel]).mean()
        js = np.flatnonzero(sel)
        cm = ctl_mean.reindex(cell[js]).values
        keep = np.isfinite(cm)
        if keep.sum() == 0:
            continue
        rows.append(dict(i=i, sig=np.mean(fr[js][keep]), ctl=np.mean(cm[keep]), n=int(keep.sum()),
                         sig_up=np.mean((fr[js] - np.nan_to_num(cm))[keep & up[i, js]]) if (keep & up[i, js]).any() else np.nan))
    return pd.DataFrame(rows)


def summarise(T, idx, h, label, out):
    T = T.copy(); T["date"] = idx[T.i.values]; T["x"] = 100 * (T.sig - T.ctl)
    mo = T.groupby(T.date.dt.to_period("M")).x.mean()
    h1, h2 = mo[mo.index < pd.Period(SPLIT, "M")], mo[mo.index >= pd.Period(SPLIT, "M")]
    cost = 100 * (2 * SLIP + BORROW * h / 252)
    short_pnl = -100 * T.sig - cost
    yr = T.groupby(T.date.dt.year).x.mean()
    res = dict(label=label, h=h, dates=len(T), names_per_date=T.n.mean(), abs_ret=100 * T.sig.mean(),
               ctl_ret=100 * T.ctl.mean(), excess=mo.mean(), t=tstat(mo), h1=h1.mean(), h2=h2.mean(),
               short_pnl=short_pnl.mean(), t_short=tstat(short_pnl.groupby(T.date.dt.to_period("M")).mean()),
               yrs_neg=f"{(yr < 0).sum()}/{len(yr)}")
    res["PASS"] = bool(res["excess"] < 0 and abs(res["t"]) >= 3 and res["h1"] < 0 and res["h2"] < 0
                       and res["short_pnl"] > 0 and (yr < 0).sum() > len(yr) / 2)
    res["VETO"] = bool(not res["PASS"] and res["excess"] < 0 and abs(res["t"]) >= 3 and res["h1"] < 0 and res["h2"] < 0
                       and (yr < 0).sum() > len(yr) / 2)
    out.append(f"\n# {label} +{h}: {len(T)} formation dates, {T.n.mean():.0f} names/date")
    out.append(f"  signal fwd {res['abs_ret']:+.3f}% vs matched control {res['ctl_ret']:+.3f}% | excess {res['excess']:+.3f}pp "
               f"t {res['t']:+.2f} (month-clustered) | halves {res['h1']:+.3f} / {res['h2']:+.3f} | years negative {res['yrs_neg']}")
    out.append(f"  SHORT P&L after {cost:.2f}% costs+borrow: {res['short_pnl']:+.3f}% per trade (t {res['t_short']:+.2f})")
    out.append("  excess by year: " + " ".join(f"{y}:{v:+.2f}" for y, v in yr.items()))
    return res, T


def main():
    P = load_panel(PANEL)
    idx, cols = P.close.index, P.close.columns
    f = pull_iv(list(cols))
    pv = lambda c: f.pivot_table(index="trade_date", columns="ticker", values=c).reindex(index=idx, columns=cols)
    skew, cw = pv("skew").values, pv("cw").values
    C = P.close
    r20p = (C / C.shift(20) - 1).values
    adr = P.adr.values
    up = (C > C.rolling(50).mean()).values
    d = pd.Series(idx, index=idx)
    wk = d[(idx >= START) & (idx <= END)].groupby(d.dt.to_period("W")).max()
    form_idx = np.searchsorted(idx, wk.values)
    out = ["# Option-implied short signals (pre-registration in the docstring)",
           f"# formation weeks {len(form_idx)}, {idx[form_idx[0]].date()} -> {idx[form_idx[-1]].date()}; costs 10 bp/side + {BORROW:.0%}/yr borrow"]

    def top_dec(s, ok):
        q = np.nanquantile(s[ok], 0.9); return ok & (s >= q)

    def bot_dec(s, ok):
        q = np.nanquantile(s[ok], 0.1); return ok & (s <= q)

    R = []
    for lab, sig, fn in (("SKEW top decile", skew, top_dec), ("CW bottom decile", cw, bot_dec)):
        for h in HORIZONS:
            T = run_cell(sig, fn, P, form_idx, r20p, adr, up, h)
            res, T2 = summarise(T, idx, h, lab + (" *PRIMARY*" if (lab.startswith("SKEW") and h == 20) else ""), out)
            R.append(res)
            if lab.startswith("SKEW") and h == 20:
                um = T2.groupby(T2.date.dt.to_period("M")).sig_up.mean() * 100
                out.append(f"  [exploratory] PRIMARY within uptrend names (close > 50 SMA): excess {um.mean():+.3f}pp t {tstat(um):+.2f}")
    # exploratory decile gradient, SKEW +20
    out.append("\n# [exploratory] SKEW decile gradient, +20 excess vs matched control (pp), month-clustered t")
    for dcl in range(10):
        fn = lambda s, ok, dcl=dcl: ok & (s >= np.nanquantile(s[ok], dcl / 10)) & (s < np.nanquantile(s[ok], (dcl + 1) / 10) + (1e-12 if dcl == 9 else 0))
        T = run_cell(skew, fn, P, form_idx, r20p, adr, up, 20)
        T["date"] = idx[T.i.values]; mo = T.groupby(T.date.dt.to_period("M")).apply(lambda g: 100 * (g.sig - g.ctl).mean())
        out.append(f"  D{dcl+1:2d}: {mo.mean():+.3f}  t {tstat(mo):+.2f}")
    D = pd.DataFrame(R)
    out.append("\n" + D.round(3).to_string(index=False))
    out.append("\nVERDICT: " + ("; ".join(f"{r.label} +{r.h}: " + ("PASS (short)" if r.PASS else "VETO candidate" if r.VETO else "fail")
                                      for r in D.itertuples())))
    D.to_csv(REPO / "data/studies/iv_skew_short_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
