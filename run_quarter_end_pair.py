#!/usr/bin/env python3
"""
Quarter-end pair from Cem Karsan (tastylive QAFDAuK_tqU, 2026-09-30). Pre-registered in
data/tastylive/videos/2026-09-30_QAFDAuK_tqU/notes.md "Not tested, could be" A and B (committed 5598cbc BEFORE any data
was touched); implemented as written. Only deviation: VIX3M starts 2009-09 (vix_term_cboe), so B's VIX3M placebo is
2009-10 -> 2016, VIX's is 2008-06 -> 2016.

A. Quarter-end vs month-end turn (low prior; turn-of-month already NULL, SPY t 0.94)
   SPY adjusted closes (yfinance) 1993 ->. W = close-to-close return of the last trading day of the month (day -1) and
   the first of the next (day +1). Dummies QE_W (quarter-end months), ME_W (other month ends); OLS HAC(5) on daily bp
   returns vs all other days, 2000-01 -> 2026-09. PRIMARY = b(QE_W) - b(ME_W).
   S1: QE_W after an UP quarter (SPY quarter return through day -2 > 0) minus after a DOWN quarter.
   S2: year-end W minus other QE_W (descriptive, tiny n).
   Bar: |t| >= 3, halves 2000-12 / 2013-26 same sign, per-year table; Sidak over 2 secondaries |t| >= 2.24.
   MDE ~35 bp/day: a non-negative null is UNDERPOWERED, a <= 0 point estimate is NULL.
B. Quarter-end IV bottom from the JHEQX collar roll (the new axis)
   Event = last trading day of each month. V = dlogVIX[0 -> +5] - dlogVIX[-5 -> 0] (a trough at the roll -> V > 0).
   PRIMARY: mean V at quarter ends minus mean V at non-quarter month ends, 2017-01 -> 2026-09, Welch t, per-year signs.
   Secondary: same on VIX3M; dose = (2017+ difference) - (placebo 2008/09-2016 difference) -> should be > 0.
   Bar: |t| >= 3, halves of 2017-26 (split 2022-01-01) same sign, placebo smaller. Confound (pre-declared): SPX
   quarterly expiry, index rebalances and window dressing share the date -> a pass is a calendar MECHANISM, not JHEQX.

Run: PYTHONPATH=src .venv/bin/python3 run_quarter_end_pair.py   (log -> data/studies/logs/quarter_end_pair.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf
from scipy import stats

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/quarter_end_pair.log"


def spy_frame() -> pd.DataFrame:
    px = yf.download("SPY", start="1993-01-01", end="2026-09-30", auto_adjust=True, progress=False)["Close"].squeeze()
    d = pd.DataFrame({"px": px, "r": px.pct_change() * 1e4}).dropna()
    ym = d.index.to_period("M")
    pos = d.groupby(ym).cumcount()
    size = d.groupby(ym).r.transform("size")
    last = pos == size - 1
    first = pos == 0
    m = d.index.month
    qe_month = np.isin(m, [3, 6, 9, 12])
    prev_qe = np.isin(m, [1, 4, 7, 10])                   # day +1 of a quarter turn
    d["QE_W"] = (last & qe_month) | (first & prev_qe)
    d["ME_W"] = (last | first) & ~d.QE_W
    # tag each W day with its turn (the month-end date it belongs to) and its quarter's return through day -2
    lasts = d.index[last]
    d["turn"] = pd.NaT
    for i, t in enumerate(lasts):
        d.loc[t, "turn"] = t
        nxt = d.index.get_loc(t) + 1
        if nxt < len(d):
            d.iloc[nxt, d.columns.get_loc("turn")] = t
    qret = {}
    for t in lasts[np.isin(lasts.month, [3, 6, 9, 12])]:
        i = d.index.get_loc(t)
        q0 = t.to_period("Q").start_time
        prior = d.index[d.index < q0]
        if len(prior) == 0 or i < 2:
            continue
        qret[t] = d.px.iloc[i - 1] / d.px.loc[prior[-1]] - 1   # through day -2's close (= day -1's open level)
    d["q_up"] = d.turn.map(lambda t: qret.get(t, np.nan) > 0 if pd.notna(t) and t in qret else np.nan)
    d["year_end"] = d.turn.map(lambda t: pd.notna(t) and t.month == 12)
    return d


def hac(x: pd.DataFrame, cols: list[str], contrast: np.ndarray):
    X = sm.add_constant(x[cols].astype(float))
    fit = sm.OLS(x.r, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    tt = fit.t_test(np.r_[0, contrast])
    return float(np.squeeze(tt.effect)), float(np.squeeze(tt.tvalue)), fit


def part_a(L: list[str]):
    d = spy_frame()
    L.append(f"## A. SPY quarter-end vs month-end turn ({d.index.min().date()} -> {d.index.max().date()})")
    rows = []
    for lab, a, b in (("PRIMARY 2000-2026", "2000", "2026"), ("half 2000-2012", "2000", "2012"),
                      ("half 2013-2026", "2013", "2026"), ("in-sample era 1993-1999", "1993", "1999")):
        x = d.loc[a:b]
        diff, t, fit = hac(x, ["QE_W", "ME_W"], np.array([1, -1]))
        rows.append(dict(window=lab, QE_W_bp=x[x.QE_W].r.mean(), ME_W_bp=x[x.ME_W].r.mean(),
                         other_bp=x[~x.QE_W & ~x.ME_W].r.mean(), b_QE=fit.params.QE_W, t_QE=fit.tvalues.QE_W,
                         b_ME=fit.params.ME_W, t_ME=fit.tvalues.ME_W, QE_minus_ME=diff, t=t,
                         n_QE=int(x.QE_W.sum()), n_ME=int(x.ME_W.sum())))
    A = pd.DataFrame(rows)
    L.append(A.round(2).to_string(index=False))
    x = d.loc["2000":"2026"].copy()
    x["QE_up"] = x.QE_W & (x.q_up == True)
    x["QE_dn"] = x.QE_W & (x.q_up == False)
    s1, t1, _ = hac(x, ["QE_up", "QE_dn", "ME_W"], np.array([1, -1, 0]))
    L.append(f"\nS1 up-quarter QE_W minus down-quarter QE_W: {s1:+.2f} bp/day t {t1:+.2f} "
             f"(n up {int(x.QE_up.sum())}, down {int(x.QE_dn.sum())}; means {x[x.QE_up].r.mean():+.2f} / {x[x.QE_dn].r.mean():+.2f})")
    ye = x[x.QE_W & (x.year_end == True)].r
    oq = x[x.QE_W & (x.year_end == False)].r
    L.append(f"S2 year-end W {ye.mean():+.2f} bp (n {len(ye)}) vs other QE_W {oq.mean():+.2f} bp (n {len(oq)}) [descriptive]")
    Y = pd.DataFrame({"QE_W": x[x.QE_W].r.groupby(x[x.QE_W].index.year).mean(),
                      "ME_W": x[x.ME_W].r.groupby(x[x.ME_W].index.year).mean()})
    Y["diff"] = Y.QE_W - Y.ME_W
    L.append(f"per year QE_W - ME_W (bp/day): positive in {(Y['diff'] > 0).sum()} of {len(Y)} years\n"
             + Y["diff"].round(1).to_frame().T.to_string())
    # exploratory: day -1 return vs next-quarter return
    qe_last = x[x.QE_W & x.index.isin(x.turn.dropna().unique())]
    nq = []
    for t in qe_last.index:
        q1 = (t + pd.offsets.QuarterEnd(1))
        nxt = d.px.loc[t:q1]
        if len(nxt) > 40:
            nq.append((qe_last.r.loc[t], (nxt.iloc[-1] / nxt.iloc[0] - 1) * 100))
    if nq:
        a_, b_ = zip(*nq)
        rho, p = stats.spearmanr(a_, b_)
        L.append(f"exploratory: day -1 return vs next-quarter return, Spearman {rho:+.2f} (p {p:.2f}, n {len(nq)})")
    return A


def vstats(series: pd.Series) -> pd.DataFrame:
    s = np.log(series.dropna())
    idx = s.index
    ym = idx.to_period("M")
    lasts = pd.Series(idx, index=idx).groupby(ym).max().values
    rows = []
    for t in lasts:
        i = idx.get_loc(t)
        if i < 5 or i + 5 >= len(idx):
            continue
        rows.append(dict(date=t, pre=s.iloc[i] - s.iloc[i - 5], post=s.iloc[i + 5] - s.iloc[i]))
    V = pd.DataFrame(rows).set_index("date")
    V["V"] = V.post - V.pre
    V["qe"] = V.index.month.isin([3, 6, 9, 12])
    return V


def contrast(V: pd.DataFrame, a: str, b: str) -> dict:
    x = V.loc[a:b]
    q, m = x[x.qe].V, x[~x.qe].V
    t, p = stats.ttest_ind(q, m, equal_var=False)
    return dict(window=f"{a}-{b}", n_qe=len(q), n_me=len(m), V_qe=q.mean() * 100, V_me=m.mean() * 100,
                diff=(q.mean() - m.mean()) * 100, t=t, pre_qe=x[x.qe].pre.mean() * 100, post_qe=x[x.qe].post.mean() * 100,
                share_qe_trough=100 * ((x[x.qe].pre < 0) & (x[x.qe].post > 0)).mean(),
                share_me_trough=100 * ((x[~x.qe].pre < 0) & (x[~x.qe].post > 0)).mean())


def part_b(L: list[str]):
    lng = pd.read_parquet(REPO / "data/cache/vix_daily_long.parquet")
    term = pd.read_parquet(REPO / "data/cache/vix_term_cboe.parquet")
    lng["trade_date"] = pd.to_datetime(lng.trade_date)
    term["trade_date"] = pd.to_datetime(term.trade_date)
    vix = lng.set_index("trade_date").vix_close.combine_first(term.set_index("trade_date").VIX).sort_index()
    v3m = term.set_index("trade_date").VIX3M.sort_index()
    L.append(f"\n## B. Quarter-end IV V-shape (VIX {vix.index.min().date()} -> {vix.index.max().date()}; "
             f"VIX3M {v3m.index.min().date()} -> {v3m.index.max().date()})")
    out = {}
    for name, s, plac in (("VIX", vix, "2008"), ("VIX3M", v3m, "2009")):
        V = vstats(s)
        rows = [contrast(V, "2017", "2026"), contrast(V, "2017", "2021"), contrast(V, "2022", "2026"),
                contrast(V, plac, "2016")]
        R = pd.DataFrame(rows)
        R.insert(0, "series", name)
        L.append(f"\n{name}: V = dlog[0->+5] - dlog[-5->0], in % log points; quarter ends (qe) vs other month ends (me)")
        L.append(R.round(2).to_string(index=False))
        L.append(f"dose (2017+ diff minus placebo diff): {R['diff'].iloc[0] - R['diff'].iloc[3]:+.2f}")
        x = V.loc["2017":"2026"]
        Y = x[x.qe].V.groupby(x[x.qe].index.year).mean() - x[~x.qe].V.groupby(x[~x.qe].index.year).mean()
        L.append(f"per year qe - me V: positive in {(Y > 0).sum()} of {len(Y)}\n" + (Y * 100).round(1).to_frame().T.to_string())
        out[name] = R
    return out


def main():
    L = ["# Quarter-end pair (Karsan QAFDAuK_tqU) — pre-registration in the notes, see docstring"]
    A = part_a(L)
    B = part_b(L)
    print("\n".join(L))
    p = A.iloc[0]
    h = A.iloc[1:3].QE_minus_ME.values
    b = B["VIX"].iloc[0]
    print(f"\nA PRIMARY QE_W - ME_W: {p.QE_minus_ME:+.2f} bp/day t {p.t:+.2f} halves {h[0]:+.2f}/{h[1]:+.2f}")
    print(f"B PRIMARY VIX V (qe - me) 2017-26: {b['diff']:+.2f} t {b.t:+.2f} halves "
          f"{B['VIX'].iloc[1]['diff']:+.2f}/{B['VIX'].iloc[2]['diff']:+.2f} placebo {B['VIX'].iloc[3]['diff']:+.2f}")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
