#!/usr/bin/env python3
"""
Is "buy the dip in an uptrend" a SURVIVORSHIP artefact? + the support-low lead on UNSEEN names
(pre-registered 2026-09-25, before any run; follow-up to low_confirmation_ladder_2026-09-25, PARKED on survivorship).

WHY. The ladder found uptrend names that dipped >= 1 ADR beat same-date non-dipping uptrend names by ~+1pp / 20d
(P2, t 2.5-5.5) -- on liquid_panel_2009, which holds only names liquid IN 2026. Dips that became collapses and
delistings are missing, and that flatters exactly this comparison. And the exploratory "low at support" lead
(P1 +3.47pp t 3.63; P2 +2.00 t 4.75) was seen on ALL years of that panel, so no in-panel holdout exists.
The names NOT in the panel are both the survivorship test and a clean holdout.

DATA  silver.chain_spot_daily (run_build_chain_spot_daily.py): RAW daily spot for every optionable ticker incl.
      delisted, from put-call parity, 2010 -> 2026-02. Split-adjusted here with data/cache/pit/splits.parquet.
      Series hygiene (declared now): a day-over-day move > +/-45% not explained by a split CUTS the series (ticker
      reuse / bad prints); only the segment after the cut is kept. Closes only -- no high/low/open exist.
      Liquidity proxy (declared now): 50-session mean option volume >= 1,000 contracts and spot >= $5 on the event
      date (v3 carries no share volume).
GROUPS  SURV = tickers in liquid_panel_2009 (the survivor set the ladder used); NONSURV = every other ticker that
      passes the liquidity proxy (delisted, acquired, or not liquid in 2026). ALL = both.
CLOSE-ONLY DEFINITIONS (the ladder's, translated; declared now)
  ADRp       20-session mean |close-to-close return| x k, where k = the median of ADR(H/L) / mean|ret| over the
             survivor panel's name-days -- computed in-script from prices only, before any outcome is touched.
  P2c        close > 50 SMA > 200 SMA and ADRp >= 3%.   P1c: ADRp 4-7%, close within 15% of the 252d high close,
             10 > 20 > 50 SMA (stack via lib.commons.ma_stack.stack_run on closes) held 5-40 sessions.
  episode    peak = a close that is the highest of the last 10 closes; running low = lowest close since; opens when
             (peak - low) >= 1.0 ADRp$; ends on a close above the peak or 30 sessions after it.
  K0         the close the pullback first reaches 1 ADRp (the dip).     K3: first close above the 5 EMA after the low.
  K1c        first close above the prior session's close after the low (the close-only analogue of K1).
  support    the low is within 0.5 ADRp$ of the 50 SMA, the 200 SMA, or the prior base high (max close peak-60..peak-20).
  forward    close -> close +20, 10 bp per side. A series that ENDS inside the window (delisting) exits at its last
             close; the truncated share is reported.
  CONTROL    same-date names in the same population and group-universe, ADRp tercile (terciles over the full liquid
             cross-section), not in an episode; fallback all same-date population names (>= 5).
TESTS
  T1 (method check, not bar-bearing): SURV, P2c, K0 and K3 -- the close-only translation should roughly reproduce the
     ladder's +1pp; if it does not, the translation failed and T2 is uninterpretable.
  T2 SURVIVORSHIP (PRIMARY): P2c K0 +20 excess on ALL (control from ALL) and on NONSURV (control from NONSURV); same
     for K3. -> 4 cells.
  T3 SUPPORT HOLDOUT: NONSURV only, K1c, support-tagged minus untagged +20 excess (difference of the two cells'
     month-clustered series), for P2c and P1c. -> 2 cells.
  M = 6; Sidak(6) |t| >= 2.64; the house |t| >= 3 GOVERNS, both halves (split 2018-01) the same sign, majority of years.
READ (declared now)
  The dip effect SURVIVES if ALL K0 passes the bar AND NONSURV K0 excess > 0. It is a SURVIVORSHIP ARTEFACT if ALL K0 is
  < half the SURV value or NONSURV K0 <= 0. In between -> PARKED stays.
  The support lead is CONFIRMED only if T3 (P2c) passes on NONSURV.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_dip_survivorship.py
       (log -> data/studies/logs/dip_survivorship.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.commons.ma_stack import stack_run

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/dip_survivorship.log"
CACHE = REPO / "data/cache/chain_spot"
START, END, SPLIT = "2010-01-01", "2026-01-31", "2018-01-01"
SLIP, T_BAR, H = 0.0010, 3.0, 20
OPTVOL_MIN, PX_MIN, CUT = 1000, 5.0, 0.45
RNG = np.random.default_rng(20260925)


def tstat(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


def pull() -> pd.DataFrame:
    f = CACHE / "chain_spot_daily.parquet"
    if f.exists():
        return pd.read_parquet(f)
    import awswrangler as wr
    from lib.constants import WORKGROUP, S3_OUTPUT
    CACHE.mkdir(parents=True, exist_ok=True)
    fr = []
    for y in range(2010, 2027):
        fr.append(wr.athena.read_sql_query(f"SELECT ticker, trade_date, spot, opt_vol FROM silver.chain_spot_daily WHERE year = {y}",
                                           database="silver", workgroup=WORKGROUP, data_source="AwsDataCatalog",
                                           s3_output=S3_OUTPUT, ctas_approach=False))
        print(f"  chain spot {y}: {len(fr[-1]):,}", flush=True)
    d = pd.concat(fr, ignore_index=True); d["trade_date"] = pd.to_datetime(d.trade_date)
    d.to_parquet(f, index=False)
    return d


def adjust_and_clean(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    C = d.pivot_table(index="trade_date", columns="ticker", values="spot").sort_index()
    V = d.pivot_table(index="trade_date", columns="ticker", values="opt_vol").reindex_like(C)
    sp = pd.read_parquet(REPO / "data/cache/pit/splits.parquet")
    sp["execution_date"] = pd.to_datetime(sp.execution_date)
    sp = sp[sp.ticker.isin(C.columns) & (sp.split_from > 0) & (sp.split_to > 0)]
    for r in sp.itertuples():                       # divide prices BEFORE the split by to/from
        ratio = r.split_to / r.split_from
        m = C.index < r.execution_date
        C.loc[m, r.ticker] = C.loc[m, r.ticker] / ratio
    ret = C / C.ffill().shift(1) - 1
    brk = ret.abs() > CUT
    for tk in brk.columns[brk.any()]:
        last = brk.index[brk[tk]].max()
        C.loc[C.index <= last, tk] = np.nan         # keep only the segment after the last unexplained break
    return C, V


def k_scale() -> float:
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet")
    raw["date"] = pd.to_datetime(raw.date)
    pv = lambda c: raw.pivot(index="date", columns="ticker", values=c).sort_index()
    Cc, Hh, Ll = pv("close"), pv("high"), pv("low")
    adr = ((Hh / Ll - 1).shift(1).rolling(20).mean())
    mar = (Cc.pct_change().abs().shift(1).rolling(20).mean())
    ratio = (adr / mar).stack()
    return float(ratio[np.isfinite(ratio)].median())


def run(C, V, surv, k):
    idx = C.index
    ret = C.pct_change()
    adrp = ret.abs().shift(1).rolling(20, min_periods=15).mean() * k * 100
    s10, s20, s50, s200 = (C.rolling(n, min_periods=int(n * .8)).mean() for n in (10, 20, 50, 200))
    e5 = C.ewm(span=5, adjust=False).mean()
    hi252 = C.shift(1).rolling(252, min_periods=120).max()
    stack = stack_run(C, adr=adrp)
    liq = (V.rolling(50, min_periods=30).mean() >= OPTVOL_MIN) & (C >= PX_MIN)
    P2 = liq & (C > s50) & (s50 > s200) & (adrp >= 3)
    P1 = liq & (adrp >= 4) & (adrp <= 7) & (C / hi252 - 1 > -0.15) & (stack >= 5) & (stack <= 40)
    hh = C >= C.rolling(10).max()
    Cv, A, E5, S50, S200 = C.values, adrp.values, e5.values, s50.values, s200.values
    n, m = Cv.shape
    last_valid = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1 for j in range(m)])
    lo_i, hi_i = idx.searchsorted(pd.Timestamp(START)), idx.searchsorted(pd.Timestamp(END), side="right")
    ev = []
    for j in range(m):
        t = max(lo_i, 200)
        while t < min(hi_i, n - 1):
            if not hh.values[t, j] or not (P1.values[t, j] or P2.values[t, j]) or not np.isfinite(A[t, j]):
                t += 1; continue
            p, pk = t, Cv[t, j]; ad = A[p, j] / 100 * pk
            pops = [nm for nm, M in (("P1", P1), ("P2", P2)) if M.values[p, j]]
            base_hi = np.nanmax(Cv[max(0, p - 60):max(1, p - 19), j]) if p > 60 else np.nan
            lo_v, lo_d, opened, fired, u = np.inf, None, False, {}, p + 1
            while u <= min(p + 30, n - 1) and np.isfinite(Cv[u, j]):
                if Cv[u, j] < lo_v:
                    lo_v, lo_d = Cv[u, j], u
                if Cv[u, j] > pk:
                    break
                if not opened and pk - lo_v >= ad:
                    opened = True; fired["K0"] = (u, lo_v, lo_d)
                if opened and u > lo_d:
                    if "K1c" not in fired and Cv[u, j] > Cv[u - 1, j]:
                        fired["K1c"] = (u, lo_v, lo_d)
                    if "K3" not in fired and Cv[u, j] > E5[u, j]:
                        fired["K3"] = (u, lo_v, lo_d)
                u += 1
            if opened:
                # support judged on the low KNOWN AT ENTRY (look-ahead fix 2026-09-25)
                near = lambda low, lvl: bool(np.isfinite(lvl) and abs(low - lvl) <= 0.5 * ad)
                for r, (e, lv, ld) in fired.items():
                    sup = near(lv, S50[ld, j]) or near(lv, S200[ld, j]) or near(lv, base_hi)
                    for pop in pops:
                        ev.append((j, p, r, pop, e, sup))
            t = max(u, t + 1)
    E = pd.DataFrame(ev, columns=["j", "peak", "rung", "pop", "i", "support"])
    # forward returns with delisting truncation
    fr = np.full(Cv.shape, np.nan); trunc = np.zeros(Cv.shape, bool)
    for j in range(m):
        col = Cv[:, j]; lv = last_valid[j]
        if lv < 0:
            continue
        ex_i = np.minimum(np.arange(n) + H, lv)
        ok = np.isfinite(col)
        fr[ok, j] = col[ex_i[ok]] * (1 - SLIP) / (col[ok] * (1 + SLIP)) - 1
        trunc[ok, j] = (np.arange(n)[ok] + H) > lv
        fr[np.arange(n) + H > n - 1, j] = np.nan
    in_ep = np.zeros(Cv.shape, bool)
    for r in E.itertuples():
        in_ep[r.peak:r.i + 1, r.j] = True
    elig = liq.values & np.isfinite(A)
    terc = np.full(Cv.shape, -1)
    for i in range(n):
        if elig[i].sum() >= 30:
            q = np.nanquantile(A[i, elig[i]], [1 / 3, 2 / 3])
            terc[i] = np.where(A[i] <= q[0], 0, np.where(A[i] <= q[1], 1, 2))
    E["date"] = idx[E.i.values]; E["sym"] = C.columns[E.j.values]; E["surv"] = E.sym.isin(surv)
    E["fwd"] = 100 * fr[E.i.values, E.j.values]; E["trunc"] = trunc[E.i.values, E.j.values]
    return E, fr, in_ep, terc, dict(P1=P1.values, P2=P2.values), C.columns


def excess(E, fr, in_ep, terc, pops, cols, surv, group):
    """Control drawn from the same group-universe."""
    gmask = np.isin(cols, list(surv)) if group == "SURV" else (~np.isin(cols, list(surv)) if group == "NONSURV" else np.ones(len(cols), bool))
    out = np.full(len(E), np.nan)
    cache = {}
    for n_, r in enumerate(E.itertuples()):
        key = (r.pop, r.i)
        if key not in cache:
            base = pops[r.pop][r.i] & ~in_ep[r.i] & np.isfinite(fr[r.i]) & gmask
            cm = {k: (fr[r.i, base & (terc[r.i] == k)].mean() if (base & (terc[r.i] == k)).sum() >= 5 else np.nan) for k in range(3)}
            cm[-1] = fr[r.i, base].mean() if base.sum() >= 5 else np.nan
            cache[key] = cm
        cm = cache[key]; tk = terc[r.i, r.j]
        c = cm.get(tk, np.nan)
        if not np.isfinite(c):
            c = cm[-1]
        out[n_] = r.fwd - 100 * c if np.isfinite(c) else np.nan
    return out


def cellstats(x, d):
    s = pd.Series(x, index=d.index).dropna(); dd = d.loc[s.index]
    mo = s.groupby(dd.dt.to_period("M")).mean(); hh = mo.index < pd.Period(SPLIT, "M")
    yr = s.groupby(dd.dt.year).mean(); same = int((np.sign(yr) == np.sign(mo.mean())).sum())
    ok = abs(tstat(mo)) >= T_BAR and np.sign(mo[hh].mean()) == np.sign(mo[~hh].mean()) and same > len(yr) / 2
    return dict(n=len(s), excess=mo.mean(), t=tstat(mo), h1=mo[hh].mean(), h2=mo[~hh].mean(), yrs=f"{same}/{len(yr)}", PASS=ok), mo


def main():
    d = pull()
    C, V = adjust_and_clean(d)
    surv = set(pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet", columns=["ticker"]).ticker.unique())
    k = k_scale()
    E, fr, in_ep, terc, pops, cols = run(C, V, surv, k)
    out = ["# Dip-in-uptrend: survivorship check + support holdout (pre-registration in the docstring)",
           f"# chain-spot tickers {C.shape[1]:,}; ADRp scale k = {k:.3f} (median ADR / mean|ret| on the survivor panel)",
           f"# events: {len(E):,}; SURV names {E[E.surv].sym.nunique()}, NONSURV names {E[~E.surv].sym.nunique()}; "
           f"delisting-truncated forward windows: SURV {E[E.surv].trunc.mean():.1%}, NONSURV {E[~E.surv].trunc.mean():.1%}"]
    R = []
    for grp in ("SURV", "ALL", "NONSURV"):
        S = E if grp == "ALL" else E[E.surv] if grp == "SURV" else E[~E.surv]
        S = S.copy(); S["x"] = excess(S, fr, in_ep, terc, pops, cols, surv, grp)
        out.append(f"\n## {grp}")
        for pop, rung in (("P2", "K0"), ("P2", "K3"), ("P2", "K1c"), ("P1", "K0"), ("P1", "K1c")):
            T = S[(S["pop"] == pop) & (S.rung == rung)]
            if len(T) < 30:
                out.append(f"  {pop} {rung}: n {len(T)} -- too few"); continue
            st, _ = cellstats(T.x.values, T.date)
            role = ("T1 method check" if grp == "SURV" and pop == "P2" and rung in ("K0", "K3") else
                    "T2 PRIMARY" if grp in ("ALL", "NONSURV") and pop == "P2" and rung in ("K0", "K3") else "context")
            out.append(f"  {pop} {rung:3s} n {st['n']:6d} fwd {T.fwd.mean():+.2f}% excess {st['excess']:+.2f}pp t {st['t']:+.2f} "
                       f"halves {st['h1']:+.2f}/{st['h2']:+.2f} yrs {st['yrs']} {'PASS' if st['PASS'] else ''}  [{role}]")
            R.append(dict(group=grp, pop=pop, rung=rung, role=role, **st))
        if grp == "NONSURV":
            out.append("\n## T3 SUPPORT HOLDOUT (NONSURV, K1c, support-tagged minus untagged)")
            for pop in ("P2", "P1"):
                T = S[(S["pop"] == pop) & (S.rung == "K1c")]
                a, moa = cellstats(T[T.support].x.values, T[T.support].date)
                b, mob = cellstats(T[~T.support].x.values, T[~T.support].date)
                dm = (moa - mob).dropna(); hh = dm.index < pd.Period(SPLIT, "M")
                ok = abs(tstat(dm)) >= T_BAR and np.sign(dm[hh].mean()) == np.sign(dm[~hh].mean())
                out.append(f"  {pop}: at support n {a['n']} excess {a['excess']:+.2f} | elsewhere n {b['n']} excess {b['excess']:+.2f} "
                           f"| diff {dm.mean():+.2f}pp t {tstat(dm):+.2f} halves {dm[hh].mean():+.2f}/{dm[~hh].mean():+.2f} "
                           f"{'PASS' if ok else 'fail'}{'  [T3 PRIMARY]' if pop == 'P2' else ''}")
                R.append(dict(group="NONSURV", pop=pop, rung="K1c support-diff", role="T3", n=a["n"], excess=dm.mean(),
                              t=tstat(dm), h1=dm[hh].mean(), h2=dm[~hh].mean(), PASS=ok))
    D = pd.DataFrame(R)
    g = lambda grp: D[(D.group == grp) & (D["pop"] == "P2") & (D.rung == "K0")].iloc[0]
    sv, al, ns = g("SURV"), g("ALL"), g("NONSURV")
    if al.PASS and ns.excess > 0:
        v = "SURVIVES survivorship"
    elif al.excess < sv.excess / 2 or ns.excess <= 0:
        v = "SURVIVORSHIP ARTEFACT"
    else:
        v = "in between -> stays PARKED"
    out.append(f"\nREAD (P2 K0): SURV {sv.excess:+.2f} / ALL {al.excess:+.2f} (t {al.t:+.2f}) / NONSURV {ns.excess:+.2f} -> {v}")
    D.to_csv(REPO / "data/studies/dip_survivorship_2026-09-25.csv", index=False)
    E.drop(columns=["j"]).to_csv(REPO / "data/studies/logs/dip_survivorship_events.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
