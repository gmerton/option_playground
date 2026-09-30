#!/usr/bin/env python3
"""
SMALL CAPS: does the book's equity evidence (12-1 momentum, the precision breakout) hold in the universe our studies
excluded? PRE-REGISTERED 2026-09-29 -- NOT RUN (Gabe: "pre-register, don't run now").

WHY. A coverage check (2026-09-29) found that of ~1,060 US small caps ($0.3-2B, price >= $5), only ~1% pass the
>= $50M ADDV filter every equity study uses and ~10% the $30M panel cut: the ledger's momentum / breakout / dip
evidence is mid- and large-cap evidence. Gabe wants a small-cap rebound plan (IWM -8.8% from 8/14).

DATA (built when run, never overwriting the nightly liquid panel)
  S  data/cache/smallcap_panel_2009.parquet:
       PYTHONPATH=src .venv/bin/python3 run_build_liquid_panel.py --addv 5e6 --addv-max 50e6 --start 2009-01-01 \
           --out data/cache/smallcap_panel_2009.parquet
     = yfinance adjusted OHLCV for names whose 50d ADDV is $5-50M and price >= $5 on the Minervini cache's last date
     (~1,200 names, ~88% of them $0.3-2B at the $5-15M end). SURVIVORSHIP-BIASED (today's names only).
  M  data/cache/liquid_panel_2009.parquet (mid/large reference, the same code paths).
  X  data/cache/chain_spot/chain_spot_daily.parquet (closes only, INCLUDES delisted) for the survivorship check.

TESTS
  T1 MOMENTUM (primary). Monthly: names eligible on the formation date (S: 50d ADDV $5-50M, price >= $5; point-in-time
     ADDV, so the band is re-applied every month). Sort on 12-1 return; hold top vs bottom decile equal-weight for one
     month; costs 20 bp per side (small-cap round trip ~40 bp; M uses 5 bp as elsewhere). Statistic: monthly
     top-minus-bottom net spread, Newey-West t (lag 3); also top decile minus the band's equal-weight mean (the
     long-only version the book would trade). Same code on M for the reference row.
     PASS iff small-cap top-minus-bottom net t >= 3, both halves (split 2018-01) positive, >= 60% of years positive.
  T2 PRECISION BREAKOUT (primary). The precision tier (run_oneil_pyramid_8wk.py definition) on S, house trade
     (close entry, day-low stop judged on the close, 20-EMA exit, 60-session cap), costs 20 bp per side, % per trade.
     Controls: (a) SELECTION = a random same-date eligible S name bought at the same close with the same exit rule
     (ADR-tercile matched); (b) TIMING = the same name at a random later session within 60 sessions.
     PASS (selection) iff signal - (a) >= 0 with t >= 3 (date-clustered) and both halves positive; timing reported.
  T3 SURVIVORSHIP CHECK (decides how T1 is read). Re-run T1 on X, restricted to names whose 50d mean option volume is
     in the bottom half of optionable names each month (the closest small-cap proxy X allows; no market cap there),
     closes only, same costs. If T1 passes on S but X's spread is <= 0 or < half of S's -> T1 is a SURVIVORSHIP
     ARTEFACT; if X confirms (same sign, >= half) -> T1 stands.
  Multiple testing: 2 primaries (T1, T2) -> Sidak-2 |t| >= 3.2 governs, not 3.
  Caveats: survivorship in S is worse than in M (small caps delist more); yfinance small-cap bars have more gaps
  (run_build_liquid_panel's Polygon gap-fill applies); no market-cap history -> the ADDV band is the size proxy.

Usage (when approved): build S (above), then PYTHONPATH=src:. .venv/bin/python3 run_smallcap_tests.py > data/studies/logs/smallcap_tests.log
"""
from __future__ import annotations

# ---- IMPLEMENTATION (added 2026-09-29 on Gabe's "yes, run the small-cap test"; the spec above is unchanged) ----------
# Interpretation notes, declared before the run:
#  * costs "per side" are charged on actual monthly turnover (T1) -- each leg pays 2 x cost x the share of its names
#    that changed -- and on both sides of every trade (T2).
#  * T2 selection control = the mean of 3 random same-date eligible S names in the signal's ADR tercile (the harness
#    convention); timing control = the same name at one random later session within 60. Stop = min(day low, 0.98 x
#    close), judged on the close; exit on a close under the stop or the 20 EMA; 60-session cap. Window 2010-01 on.
#  * The Sidak-2 bar (t >= 3.2) governs T1 and T2, per the multiple-testing line.

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel

REPO = Path(__file__).resolve().parent
SPLIT, BAR, SEED = "2018-01-01", 3.2, 20260929
ETF = ["SPY", "QQQ", "IWM", "RSP"]


def nw_t(x, lags=3):
    x = pd.Series(x).dropna()
    f = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(f.params[0]), float(f.tvalues[0])


def load(path):
    raw = pd.read_parquet(REPO / path)
    raw = raw[~raw.ticker.isin(ETF)]
    p = Panel.from_long(raw)
    return p, raw


def momentum(C, elig_me, cost, label):
    """C: daily closes (wide). elig_me: month-end eligibility (wide bool). Returns monthly net spreads."""
    ME = C.resample("ME").last()
    fwd = ME.shift(-1) / ME - 1
    sig = ME.shift(1) / ME.shift(12) - 1
    el = elig_me.reindex(ME.index).fillna(False).astype(bool)
    rows, prev = [], {"top": set(), "bot": set()}
    for d in ME.index[12:-1]:
        ok = el.loc[d] & sig.loc[d].notna() & fwd.loc[d].notna()
        s = sig.loc[d][ok]
        if len(s) < 50:
            continue
        q = pd.qcut(s.rank(method="first"), 10, labels=False)
        top, bot = set(s.index[q == 9]), set(s.index[q == 0])
        turn = lambda new, old: 1.0 if not old else 1 - len(new & old) / len(new)
        ct, cb = 2 * cost * turn(top, prev["top"]), 2 * cost * turn(bot, prev["bot"])
        rt, rb, rall = fwd.loc[d][list(top)].mean(), fwd.loc[d][list(bot)].mean(), fwd.loc[d][ok].mean()
        rows.append(dict(month=d, spread=(rt - ct) - (rb + cb), long_only=(rt - ct) - rall, n=len(s)))
        prev = {"top": top, "bot": bot}
    R = pd.DataFrame(rows).set_index("month")
    out = {}
    for col in ("spread", "long_only"):
        m, t = nw_t(R[col])
        h1, h2 = R[col][R.index < SPLIT].mean(), R[col][R.index >= SPLIT].mean()
        yr = R[col].groupby(R.index.year).mean()
        out[col] = dict(universe=label, stat=col, months=len(R), names_med=int(R.n.median()), mean_pct=100 * m, nw_t=t,
                        h1=100 * h1, h2=100 * h2, yrs_pos=f"{int((yr > 0).sum())}/{len(yr)}", pos_share=(yr > 0).mean())
    return out, R


def t1():
    res = {}
    for label, path, lo, hi, cost in (("S small", "data/cache/smallcap_panel_2009.parquet", 5e6, 50e6, 0.0020),
                                      ("M mid/large", "data/cache/liquid_panel_2009.parquet", 50e6, np.inf, 0.0005)):
        p, _ = load(path)
        addv = p.dolvol.rolling(50, min_periods=40).mean()
        el = ((addv >= lo) & (addv < hi) & (p.close >= 5) & ~p.suspect()).resample("ME").last()
        out, R = momentum(p.close, el, cost, label)
        res[label] = (out, R)
    return res


def trade(Cv, Lv, E, i, j, cost):
    n = len(Cv)
    entry = Cv[i, j]
    if not np.isfinite(entry) or i + 2 >= n:
        return np.nan
    stop = min(Lv[i, j], entry * 0.98)
    k_exit = None
    for k in range(i + 1, min(i + 61, n)):
        c = Cv[k, j]
        if not np.isfinite(c):
            continue
        k_exit = k
        if c < stop or c < E[k, j]:
            break
    if k_exit is None:
        return np.nan
    return 100 * (Cv[k_exit, j] * (1 - cost) / (entry * (1 + cost)) - 1)


def t2():
    p, raw = load("data/cache/smallcap_panel_2009.parquet")
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    addv = p.dolvol.rolling(50, min_periods=40).mean()
    elig = (addv >= 5e6) & (addv < 50e6) & (C >= 5) & ~p.suspect()
    e20 = C.ewm(span=20, adjust=False).mean()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    piv15 = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    stack_days = stack_run(C, adr=adr); off52 = (C / hi52 - 1) * 100
    gate = (adr >= 3) & (range52 >= 17) & elig
    brk = (gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5) & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15))
    prec = (brk & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stack_days <= 40)).fillna(False).astype(bool)
    prec[prec.index < "2010-01-01"] = False
    Cv, Lv, Ev, A, EL, PR = C.values, L.values, e20.values, adr.values, elig.fillna(False).values, prec.values
    rng = np.random.default_rng(SEED)
    rows = []
    for i, j in zip(*np.where(PR)):
        r = trade(Cv, Lv, Ev, i, j, 0.0020)
        if not np.isfinite(r):
            continue
        ok = EL[i] & np.isfinite(A[i]) & np.isfinite(Cv[i]) & ~PR[i]
        if ok.sum() < 30:
            continue
        q = np.nanquantile(A[i, ok], [1 / 3, 2 / 3])
        terc = lambda a: 0 if a <= q[0] else (1 if a <= q[1] else 2)
        pool = np.flatnonzero(ok & (np.array([terc(a) if np.isfinite(a) else -1 for a in A[i]]) == terc(A[i, j])))
        sel = [trade(Cv, Lv, Ev, i, int(c), 0.0020) for c in rng.choice(pool, size=min(3, len(pool)), replace=False)] if len(pool) else []
        sel = np.nanmean(sel) if len(sel) and np.isfinite(sel).any() else np.nan
        later = [k for k in range(i + 1, min(i + 61, len(Cv) - 2)) if EL[k, j] and not PR[k, j] and np.isfinite(Cv[k, j])]
        tim = trade(Cv, Lv, Ev, int(rng.choice(later)), j, 0.0020) if later else np.nan
        rows.append(dict(date=C.index[i], sym=C.columns[j], ret=r, sel=sel, tim=tim))
    T = pd.DataFrame(rows)
    T["x_sel"], T["x_tim"] = T.ret - T.sel, T.ret - T.tim
    out = {}
    for col in ("ret", "x_sel", "x_tim"):
        g = T.groupby("date")[col].mean().dropna()
        t = g.mean() / g.std(ddof=1) * sqrt(len(g))
        h = g.index < SPLIT
        out[col] = dict(stat=col, n=int(T[col].notna().sum()), dates=len(g), mean_pct=T[col].mean(), date_t=t,
                        h1=g[h].mean(), h2=g[~h].mean(), names=T.sym.nunique())
    return out, T


def t3():
    import run_dip_survivorship as ds
    C, V = ds.adjust_and_clean(ds.pull())
    ov = V.rolling(50, min_periods=30).mean()
    rank = ov.where(ov > 0).rank(axis=1, pct=True)
    el = ((rank <= 0.5) & (C >= 5)).resample("ME").last()
    out, R = momentum(C, el, 0.0020, "X chain-spot low-option-volume half (incl. delisted)")
    return out, R


def main():
    lines = ["# SMALL CAPS (pre-registration in the docstring; implementation notes above main)"]
    r1 = t1()
    lines.append("\n== T1 MOMENTUM 12-1, top vs bottom decile, monthly, net ==")
    T1 = pd.DataFrame([v for lab in r1 for v in r1[lab][0].values()])
    lines.append(T1.round(3).to_string(index=False))
    s = r1["S small"][0]["spread"]
    ok1 = s["nw_t"] >= BAR and s["h1"] > 0 and s["h2"] > 0 and s["pos_share"] >= 0.6
    lines.append(f"T1 PASS (S spread NW t >= {BAR}, both halves > 0, >= 60% yrs): {'YES' if ok1 else 'no'}")
    o2, T = t2()
    lines.append("\n== T2 PRECISION BREAKOUT on S (house trade, % per trade, 20 bp/side) ==")
    lines.append(pd.DataFrame(o2.values()).round(3).to_string(index=False))
    x = o2["x_sel"]
    ok2 = x["mean_pct"] >= 0 and x["date_t"] >= BAR and x["h1"] > 0 and x["h2"] > 0
    lines.append(f"T2 PASS (selection: signal - same-date ADR-tercile control, date t >= {BAR}, halves > 0): {'YES' if ok2 else 'no'}")
    o3, R3 = t3()
    lines.append("\n== T3 SURVIVORSHIP CHECK: T1 on chain-spot closes incl. delisted ==")
    lines.append(pd.DataFrame(o3.values()).round(3).to_string(index=False))
    xs = o3["spread"]["mean_pct"]
    if ok1:
        read = "T1 STANDS" if xs > 0 and xs >= 0.5 * s["mean_pct"] else "T1 is a SURVIVORSHIP ARTEFACT"
    else:
        read = "T1 did not pass; T3 is context only"
    lines.append(f"T3 READ: X spread {xs:+.3f}%/mo vs S {s['mean_pct']:+.3f}%/mo -> {read}")
    T.to_csv(REPO / "data/studies/logs/smallcap_t2_trades.csv", index=False)
    pd.concat({k: v[1] for k, v in r1.items()}).to_csv(REPO / "data/studies/logs/smallcap_t1_months.csv")
    txt = "\n".join(lines)
    (REPO / "data/studies/smallcap_tests_2026-09-29.log").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
