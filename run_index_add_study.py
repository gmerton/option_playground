"""Does the index-add rebalance auction pop hold, or give it back?

Event = a name added to the S&P 500 or Nasdaq-100 (data/studies/index_adds_events.csv).
Anchor = the T-1 close, i.e. the rebalance auction close, which is the tradeable decision point:
hold the position through the effective date, or sell into the index bid.

Arms: plain forward return from the anchor close over +1 / +3 / +5 / +10 sessions (no stop -- this
is a drift question, not an entry pattern, so the R harness does not apply).

Controls (3 draws each, same horizons):
  post      same name, random session in the 20 AFTER the anchor  -> is the auction close special?
  xname     random eligible other name, same date                 -> does the name selection matter?
  extmatch  random eligible name-day matched on extension over the 21 EMA in ADR units (+-0.25)
            and on ADR20 (+-1pp)                                  -> THE control: adds are extended
            by construction, so an unmatched control rediscovers mean reversion.

t-stats are clustered by calendar date (events pile onto quarterly rebalance dates).
Pre-registered test: T+5 vs xname, t >= 3, n >= 150.  Kill: |t| < 2 on every arm.
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd
from lib.studies.pattern_test import load_panel

RNG = np.random.default_rng(20260920)
HOR = [1, 3, 5, 10]
NCTRL = 3


def fwd(C, i, j, k):
    if i + k >= len(C):
        return np.nan
    a, b = C[i, j], C[i + k, j]
    return (b / a - 1) * 100 if np.isfinite(a) and np.isfinite(b) and a > 0 else np.nan


def main():
    P = load_panel()
    C, O = P.close.values, P.open.values
    idx, cols = P.close.index, list(P.close.columns)
    col = {t: n for n, t in enumerate(cols)}
    ext = ((P.close / P.ema20 - 1) * 100 / P.adr.where(P.adr > 0.05)).values   # extension over the 20 EMA, ADR units
    adr = P.adr.values
    elig = P.elig.values

    E = pd.read_csv("data/studies/index_adds_events.csv")
    ev = []
    for r in E.itertuples():
        if r.ticker not in col:
            continue
        j = col[r.ticker]
        pos = idx.searchsorted(pd.Timestamp(r.anchor_date))
        if pos >= len(idx) or idx[pos] != pd.Timestamp(r.anchor_date):
            continue
        ev.append((r.ticker, j, int(pos), r.index, r.kind, float(ext[pos, j]), float(adr[pos, j]),
                   str(idx[pos].date())))
    print(f"events matched to panel sessions: {len(ev)} of {len(E)}")

    # pool of eligible name-days for the extension-matched control
    ii, jj = np.where(elig & np.isfinite(ext) & np.isfinite(adr))
    keep = (ii > 60) & (ii < len(idx) - 12)
    ii, jj = ii[keep], jj[keep]
    pool_ext, pool_adr = ext[ii, jj], adr[ii, jj]
    print(f"control pool: {len(ii):,} eligible name-days")

    rows, ctrl = [], []
    evkeys = {(j, i) for _, j, i, *_ in ev}
    for tick, j, i, index, kind, e_ext, e_adr, adate in ev:
        rec = dict(ticker=tick, date=adate, index=index, kind=kind, ext=e_ext, adr=e_adr)
        for k in HOR:
            rec[f"r{k}"] = fwd(C, i, j, k)
        rec["overnight"] = (O[i + 1, j] / C[i, j] - 1) * 100 if i + 1 < len(C) else np.nan
        rows.append(rec)

        # post: same name, later session
        cand = [k for k in range(i + 1, min(i + 21, len(idx) - 11)) if elig[k, j] and (j, k) not in evkeys]
        for k in RNG.choice(cand, size=min(NCTRL, len(cand)), replace=False) if cand else []:
            ctrl.append(dict(kind="post", date=adate, **{f"r{h}": fwd(C, int(k), j, h) for h in HOR}))
        # xname: other name, same date
        cand = [x for x in np.flatnonzero(elig[i] & np.isfinite(C[i])) if x != j and (x, i) not in evkeys]
        for x in RNG.choice(cand, size=min(NCTRL, len(cand)), replace=False) if cand else []:
            ctrl.append(dict(kind="xname", date=adate, **{f"r{h}": fwd(C, i, int(x), h) for h in HOR}))
        # extmatch: same extension + ADR, any name-day
        m = np.flatnonzero((np.abs(pool_ext - e_ext) <= 0.25) & (np.abs(pool_adr - e_adr) <= 1.0))
        for s in RNG.choice(m, size=min(NCTRL, len(m)), replace=False) if len(m) else []:
            ctrl.append(dict(kind="extmatch", date=adate,
                             **{f"r{h}": fwd(C, int(ii[s]), int(jj[s]), h) for h in HOR}))

    T, K = pd.DataFrame(rows), pd.DataFrame(ctrl)
    T.to_csv("data/studies/index_adds_returns.csv", index=False)
    K.to_csv("data/studies/index_adds_controls.csv", index=False)

    def stat(s, d):
        s = pd.Series(s).dropna()
        if len(s) < 20:
            return dict(n=len(s))
        g = s.groupby(pd.Series(d).loc[s.index]).mean()
        return dict(n=len(s), mean=s.mean(), med=s.median(), win=100 * (s > 0).mean(),
                    t=g.mean() / g.std() * np.sqrt(len(g)), clusters=len(g))

    print(f"\n=== EVENT: hold from the rebalance auction close ({len(T)} adds, "
          f"{T.date.nunique()} distinct dates) ===")
    print(pd.DataFrame({f"T+{k}": stat(T[f"r{k}"], T.date) for k in HOR}).T.round(3).to_string())
    print(f"\novernight (anchor close -> effective-day open): mean {T.overnight.mean():+.3f}%  "
          f"med {T.overnight.median():+.3f}%  share negative {100*(T.overnight<0).mean():.0f}%")

    for c in ("post", "xname", "extmatch"):
        k_ = K[K.kind == c]
        print(f"\n--- CONTROL {c} ({len(k_):,} draws) ---")
        print(pd.DataFrame({f"T+{k}": stat(k_[f"r{k}"], k_.date) for k in HOR}).T.round(3).to_string())

    print("\n=== EDGE (event mean - control mean, pp) and the PAIRED test ===")
    print("paired by calendar date: per-date (event mean - control mean), t across dates\n")
    tab, tt = {}, {}
    for c in ("post", "xname", "extmatch"):
        k_ = K[K.kind == c]
        tab[c] = {f"T+{k}": T[f"r{k}"].mean() - k_[f"r{k}"].mean() for k in HOR}
        row = {}
        for k in HOR:
            a = T.groupby("date")[f"r{k}"].mean()
            b = k_.groupby("date")[f"r{k}"].mean()
            d = (a - b).dropna()
            row[f"T+{k}"] = d.mean() / d.std() * np.sqrt(len(d))
        tt[c] = row
    print("edge (pp):");  print(pd.DataFrame(tab).round(3).to_string())
    print("\nt on the paired difference:"); print(pd.DataFrame(tt).round(2).to_string())

    print("\n=== SPLITS (event mean %) ===")
    T["half"] = np.where(T.date < "2023-01-01", "<2023", ">=2023")
    T["exttier"] = pd.qcut(T.ext, 3, labels=["low ext", "mid", "high ext"])
    for by in ("half", "index", "kind", "exttier"):
        print(f"\nby {by}:")
        print(T.groupby(by, observed=True)[[f"r{k}" for k in HOR]].agg(["mean", "count"]).round(2).to_string())


if __name__ == "__main__":
    main()
