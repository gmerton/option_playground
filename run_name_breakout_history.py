#!/usr/bin/env python3
"""
Per-name breakout history as a selection signal (2026-09-27, Gabe: Luk "looks at the historical price action of
individual stocks" -- do some names have breakout behaviour that pooling throws away?).

WHAT IS NEW. TEST_INDEX row 187 tested per-name affinity for an intraday trigger (Stage A) and for a daily
gap-down reclaim; rows 188-189 tested gap share (a risk-shape trait). Nobody has tested whether a name's OWN
track record on the daily breakout -- the house entry -- predicts its next breakout.

PRE-REGISTRATION (written before the first run; nothing below was changed after it)
  Universe   liquid_panel_2009 (2009-01 -> 2026-09, 1,728 names; ADDV >= $50M, px >= $5, not suspect), ETFs out.
  Event      house breakout: close > prior 20-session high, ADR >= 3, eligible. De-clustered: no event in the
             same name in the prior 10 sessions.
  Outcome    close entry, 20-session % return, no stop (fixed horizon, judged in percent). x = return minus the
             mean of the same date's other breakouts (date held fixed, name varies) -> costs cancel.
  Signal     TR = sum(x over the name's prior events whose 20-session outcome had COMPLETED before this entry)
                  / (n_prior + 5)      -- shrunk to 0 with k0 = 5 pseudo-events. Requires n_prior >= 3.
  Arms       terciles of TR, formed within calendar year. PRIMARY = top minus bottom tercile mean x, computed per
             entry month and t'd over months (month-clustered).
  Control    (1) date-demeaning (above) removes market/date. (2) DRIFT placebo: D = the name's mean date-demeaned
             20-session return over ALL its prior eligible days (same completion rule). If breakout history is
             just "this stock goes up", D carries it. Gate: in x ~ TR_z + D_z + mom_z (mom = 12-1 return),
             month-clustered, TR's coefficient keeps the sign with t >= 2.
  Bar        PRIMARY |t| >= 3, both halves (split 2018-01-01) the same sign, AND the drift gate. Per-year signs
             reported (halves do not catch a back-half regime).
  Charge     one primary cell. Exploratory, not certifiable: k0 in {0, 20}, n_prior >= 6, horizons 5 / 60,
             and the split-half per-name rank correlation vs a within-date shuffle null (row 187's benchmark).
  Caveat     liquid_panel is built from names liquid today -> survivorship lifts absolute returns; the
             date-demeaned contrast is what is tested.

Usage: PYTHONPATH=src .venv/bin/python3 run_name_breakout_history.py > data/studies/logs/name_breakout_history.log
"""
from __future__ import annotations
import warnings
import numpy as np, pandas as pd
from scipy import stats
from lib.studies.pattern_test import load_panel

warnings.filterwarnings("ignore"); pd.set_option("display.width", 200)
RNG = np.random.default_rng(20260927)
SPLIT = pd.Timestamp("2018-01-01")
ETF = {"SPY", "QQQ", "IWM", "RSP", "DIA"}


def month_t(df, col="d"):
    g = df.groupby(df.date.dt.to_period("M"))[col].mean().dropna()
    return g.mean(), g.mean() / (g.std(ddof=1) / np.sqrt(len(g))), len(g)


def build(P, hold):
    C, H, A = P.close, P.high, P.adr
    keep = [c for c in C.columns if c not in ETF]
    C, H, A, E = C[keep], H[keep], A[keep], P.elig[keep].fillna(False)
    fwd = C.shift(-hold) / C - 1
    brk = ((C > H.shift(1).rolling(20).max()) & (A >= 3) & E).fillna(False).values
    # de-cluster: drop an event if the same name had one in the prior 10 sessions
    b = brk.copy()
    for k in range(1, 11):
        b[k:] &= ~brk[:-k]
    # drift placebo: date-demeaned fwd return over all eligible days, expanding mean known at entry (completed)
    fe = fwd.where(E)
    xall = fe.sub(fe.mean(axis=1), axis=0)
    csum = xall.fillna(0).cumsum().shift(hold + 1); ccnt = xall.notna().cumsum().shift(hold + 1)
    D = (csum / ccnt.replace(0, np.nan)).values
    mom = (C.shift(21) / C.shift(252) - 1).values
    ii, jj = np.where(b)
    ev = pd.DataFrame(dict(i=ii, j=jj, date=C.index[ii], sym=np.array(keep)[jj], r=fwd.values[ii, jj],
                           D=D[ii, jj], mom=mom[ii, jj])).dropna(subset=["r"])
    ev["x"] = ev.r - ev.groupby("date").r.transform("mean")
    ev["nd"] = ev.groupby("date").r.transform("size")
    return ev[ev.nd >= 2].sort_values(["j", "i"]).reset_index(drop=True)


def track(ev, hold, k0):
    """TR, n_prior per event: prior events of the same name whose outcome completed (i_prev + hold < i)."""
    tr = np.full(len(ev), np.nan); npri = np.zeros(len(ev), int)
    for j, g in ev.groupby("j"):
        idx, ii, xx = g.index.values, g.i.values, g.x.values
        cx = np.concatenate([[0], np.cumsum(xx)])
        done = np.searchsorted(ii + hold, ii, side="left")   # count of prior events with i_prev + hold < i
        npri[idx] = done
        tr[idx] = cx[done] / (done + k0) if k0 > 0 else np.where(done > 0, cx[done] / np.maximum(done, 1), np.nan)
    return tr, npri


def evaluate(ev, hold, k0, nmin, label, full=False):
    e = ev.copy()
    e["TR"], e["n"] = track(e, hold, k0)
    e = e[(e.n >= nmin) & e.TR.notna()].copy()
    e["yr"] = e.date.dt.year
    e["terc"] = e.groupby("yr").TR.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False))
    m = e.groupby([e.date.dt.to_period("M"), "terc"]).x.mean().unstack()
    d = (m[2] - m[0]).dropna()
    t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    mo = d.index.to_timestamp()
    h1, h2 = d[mo < SPLIT], d[mo >= SPLIT]
    out = dict(cell=label, events=len(e), names=e.sym.nunique(), months=len(d),
               bot=100 * e[e.terc == 0].x.mean(), mid=100 * e[e.terc == 1].x.mean(), top=100 * e[e.terc == 2].x.mean(),
               top_minus_bot_pp=100 * d.mean(), t=t, h1_pp=100 * h1.mean(), h2_pp=100 * h2.mean())
    # drift gate: x ~ TR_z + D_z + mom_z, month-clustered
    g = e.dropna(subset=["D", "mom"]).copy()
    for c in ("TR", "D", "mom"):
        g[c + "_z"] = (g[c] - g[c].mean()) / g[c].std()
    import statsmodels.formula.api as smf
    fit = smf.ols("x ~ TR_z + D_z + mom_z", g).fit(cov_type="cluster",
                                                     cov_kwds={"groups": g.date.dt.to_period("M").astype(str).factorize()[0]})
    out.update(TR_coef_pp=100 * fit.params["TR_z"], TR_t_ctrl=fit.tvalues["TR_z"],
               D_t=fit.tvalues["D_z"], mom_t=fit.tvalues["mom_z"])
    # drift-only placebo sort, same machinery (does D alone produce the same spread?)
    g["tD"] = g.groupby("yr").D.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False))
    mD = g.groupby([g.date.dt.to_period("M"), "tD"]).x.mean().unstack(); dD = (mD[2] - mD[0]).dropna()
    out.update(D_sort_pp=100 * dD.mean(), D_sort_t=dD.mean() / (dD.std(ddof=1) / np.sqrt(len(dD))))
    if full:
        yr = pd.Series(d.values, index=mo.year).groupby(level=0).agg(["mean", "size"])
        yr["mean"] *= 100
        out["per_year"] = yr
        out["events_df"] = e
    return out


def split_half_rank(ev, nmin=10, nperm=500):
    """Row-187 benchmark: per-name mean x pre-2018 vs 2018+, rank corr vs a within-date shuffle null."""
    def rc(df, xcol):
        a = df[df.date < SPLIT].groupby("sym")[xcol].agg(["mean", "size"])
        b = df[df.date >= SPLIT].groupby("sym")[xcol].agg(["mean", "size"])
        z = a.join(b, lsuffix="1", rsuffix="2", how="inner")
        z = z[(z.size1 >= nmin) & (z.size2 >= nmin)]
        return stats.spearmanr(z.mean1, z.mean2).correlation, len(z)
    obs, nn = rc(ev, "x")
    e = ev[["date", "sym", "x"]].sort_values("date").reset_index(drop=True); null = []
    dcode = e.date.factorize()[0]
    for _ in range(nperm):
        order = np.lexsort((RNG.random(len(e)), dcode))     # shuffle x among the same date's events
        e["xs"] = e.x.values[order]
        null.append(rc(e, "xs")[0])
    null = np.array(null)
    return obs, nn, np.percentile(null, 95), np.percentile(null, 99), (null >= obs).mean()


def main():
    P = load_panel("data/cache/liquid_panel_2009.parquet")
    res, prim = [], None
    for hold in (20, 5, 60):
        ev = build(P, hold)
        print(f"hold {hold}: {len(ev):,} de-clustered breakouts, {ev.sym.nunique()} names, "
              f"{ev.date.min().date()} -> {ev.date.max().date()}")
        cells = [(5, 3, "PRIMARY k0=5 n>=3")] if hold == 20 else [(5, 3, f"k0=5 n>=3")]
        if hold == 20:
            cells += [(0, 3, "k0=0 n>=3"), (20, 3, "k0=20 n>=3"), (5, 6, "k0=5 n>=6")]
        for k0, nmin, lab in cells:
            o = evaluate(ev, hold, k0, nmin, f"h{hold} {lab}", full=(lab.startswith("PRIMARY")))
            if lab.startswith("PRIMARY"):
                prim, ev20 = o, ev
            res.append({k: v for k, v in o.items() if k not in ("per_year", "events_df")})
    t = pd.DataFrame(res)
    print("\n" + t.round(3).to_string(index=False))
    print("\nPRIMARY per-year top-minus-bottom (pp, months):")
    print(prim["per_year"].round(3).to_string())
    obs, nn, p95, p99, p = split_half_rank(ev20)
    print(f"\nsplit-half per-name rank corr (>=10 events each half): {obs:+.3f} over {nn} names; "
          f"shuffle null 95th {p95:+.3f} / 99th {p99:+.3f}; perm p {p:.3f}")
    ok = abs(prim["t"]) >= 3 and np.sign(prim["h1_pp"]) == np.sign(prim["h2_pp"]) == np.sign(prim["t"]) \
        and np.sign(prim["TR_t_ctrl"]) == np.sign(prim["t"]) and abs(prim["TR_t_ctrl"]) >= 2
    print(f"\nPRE-REGISTERED BAR: {'PASS' if ok else 'FAIL'}")
    prim["events_df"].to_csv("data/studies/logs/name_breakout_history_events.csv", index=False)


if __name__ == "__main__":
    main()
