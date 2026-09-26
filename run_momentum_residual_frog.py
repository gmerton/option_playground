#!/usr/bin/env python3
"""
Two momentum refinements aimed at the sleeve's weakness: RESIDUAL momentum and FROG-IN-THE-PAN (pre-registered 2026-09-25,
before any run; Gabe chose both after run_momentum_topn.py showed the 12-1 edge is carried by a few extreme winners --
winsorised at p95 the 20-name book falls from t 2.68 to t 1.47).

WHY NEW. The ledger has raw 12-1 momentum (decile +0.67pp/mo vs EW, t_NW 2.93, SUPPORTED near-miss) and a
trend-smoothness signal on BREAKOUTS (row "Trend smoothness / EMA slope", a different population and horizon).
Neither refinement has been run on a momentum portfolio.
  R  Residual momentum (Blitz, Huij & Martens 2011): rank on the stock's own return after removing the market's.
     Their result: about double the Sharpe of raw momentum and much smaller crashes, because raw momentum loads on the
     factor that just paid.
  F  Frog in the pan (Da, Gurun & Warachka 2014): among past winners, those that got there by many small steps
     (continuous information) keep going; those that got there by a few jumps don't.

DATA     identical to run_momentum_portfolio.py: silver.chain_spot_daily (survivorship-free, split-adjusted, >45% jumps
         cut), liquidity = 50-session mean option volume >= 1,000 and px >= $5 at formation, formations 2011-01 ->
         2026-01, delisted names exit at their last close, 10 bp per side on turnover, equal weight, monthly.
SIGNALS  (all known at the month-end formation t)
  RAW    close(t-21)/close(t-252) - 1                                   (the existing sleeve; the reference)
  R      monthly returns from month-end closes; market = the EW mean of eligible names. For each name with >= 24 of the
         last 36 monthly returns: beta by OLS on the market; residuals e over the 11 months t-11..t-1 (the 12-1
         window); score = sum(e) / std(e).  Top DECILE.
  F      ID = sign(PRET) x (share of negative days - share of positive days) over the sessions (t-252, t-21], PRET = the
         RAW score. Book = the top QUINTILE by RAW with ID below that quintile's median (the most continuous half),
         so it's about 10% of names, the same size as the decile.
CELLS (M = 2 -> Sidak |t| >= 2.24; the house |t| >= 3 GOVERNS; both halves (2018-01) positive; majority of years)
  PRIMARY R-cert  R top decile excess vs the EW universe, Newey-West lag 3.
  PRIMARY F-cert  F book excess vs the EW universe.
  For each, the IMPROVEMENT test: the monthly difference vs the RAW decile, NW t. "Better than raw" needs t >= 2 AND
  the p95-winsorised check below to hold up. Otherwise it's at most a substitute.
TAIL CHECK (declared, the reason for the test): winsorise name-month excess returns at the pooled p95 and recompute
  each book's excess t. The RAW decile is reported the same way as the reference.
  Also: max drawdown, worst 5 months, per-year excess.
METHOD CHECK (F only): chain_spot is a put-call-parity spot, and daily noise can flip the signs that ID counts. ID from
  chain_spot vs ID from liquid_panel_2009 (real closes) on overlapping names at the same formations: rank correlation
  must be >= 0.7, else the F result on chain_spot is uninterpretable and the panel-name replication governs.
EXPLORATORY  R and F combined (R top quintile, then the continuous half by ID); the R and F books run on the survivor
  panel.
PRIOR    R: moderate (well replicated out of sample, but our universe is optionable large caps, where the gain is
  smaller). F: low-moderate (the published effect is weaker in large caps, and our smoothness null on breakouts).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_momentum_residual_frog.py  (log -> data/studies/logs/momentum_residual_frog.log)
       Heavy? ~2-3 min locally in the parent study; use services/study-runner/ if memory is tight.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import run_momentum_portfolio as M

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/momentum_residual_frog.log"
LOOKBACK, SKIP = 252, 21


def formations(idx):
    return [i for i in M.month_ends(idx) if pd.Timestamp(M.START) <= idx[i] <= pd.Timestamp(M.END)]


def signals(C: pd.DataFrame, elig: pd.DataFrame) -> dict[int, dict[str, np.ndarray]]:
    """Per formation index a: dict of name-index arrays for each book."""
    idx = C.index; Cv = C.values; E = elig.values
    me_all = M.month_ends(idx)
    CM = Cv[me_all]                                            # month-end closes
    RM = CM[1:] / CM[:-1] - 1                                  # RM[k] = return over month k+1
    EM = E[me_all]
    mkt = np.array([np.nanmean(RM[k][EM[k] & np.isfinite(RM[k])]) if (EM[k] & np.isfinite(RM[k])).any() else np.nan
                    for k in range(len(RM))])
    pos = {a: k for k, a in enumerate(me_all)}
    out = {}
    for a in formations(idx):
        if a - LOOKBACK < 0:
            continue
        raw = Cv[a - SKIP] / Cv[a - LOOKBACK] - 1
        ok = E[a] & np.isfinite(raw) & np.isfinite(Cv[a])
        names = np.flatnonzero(ok)
        if len(names) < 50:
            continue
        k = pos[a]                                             # month-end index of formation
        books = {"names": names, "RAW": names[raw[names] >= np.nanquantile(raw[names], 0.9)]}
        # residual momentum: 36 months of returns ending at month k (RM[k-1] is the month ending at a)
        if k >= 36:
            Y = RM[k - 36:k][:, names]; X = mkt[k - 36:k]
            fin = np.isfinite(Y) & np.isfinite(X)[:, None]
            nobs = fin.sum(0)
            Xm = np.where(fin, X[:, None], np.nan)
            xb, yb = np.nanmean(Xm, 0), np.nanmean(np.where(fin, Y, np.nan), 0)
            cov = np.nansum(np.where(fin, (Xm - xb) * (Y - yb), np.nan), 0) / (nobs - 1)
            var = np.nansum(np.where(fin, (Xm - xb) ** 2, np.nan), 0) / (nobs - 1)
            beta = cov / var; alpha = yb - beta * xb
            e = Y - alpha - beta * X[:, None]
            w = e[-12:-1]                                     # months t-11 .. t-1 (skip the most recent month)
            sc = np.nansum(w, 0) / np.nanstd(w, 0, ddof=1)
            good = (nobs >= 24) & (np.isfinite(w).sum(0) >= 9) & np.isfinite(sc)
            if good.sum() >= 50:
                g = names[good]; s = sc[good]
                books["R"] = g[s >= np.nanquantile(s, 0.9)]
                rq = g[s >= np.nanquantile(s, 0.8)]
                books["_Rq"] = rq
        # frog in the pan: information discreteness over (a-252, a-21]
        dr = Cv[a - LOOKBACK + 1:a - SKIP + 1, names] / Cv[a - LOOKBACK:a - SKIP, names] - 1
        pos_d, neg_d = (dr > 0).sum(0), (dr < 0).sum(0); nd = np.isfinite(dr).sum(0)
        ID = np.sign(raw[names]) * (neg_d - pos_d) / np.maximum(nd, 1)
        idm = pd.Series(ID, index=names)
        q = names[raw[names] >= np.nanquantile(raw[names], 0.8)]
        books["F"] = q[idm[q].values <= np.nanmedian(idm[q].values)]
        books["_ID"] = idm
        if "_Rq" in books:
            rq = books["_Rq"]; idr = idm.reindex(rq).values
            books["RF"] = rq[idr <= np.nanmedian(idr)]
        out[a] = books
    return out


def returns(C: pd.DataFrame, S: dict, keys=("RAW", "R", "F", "RF")) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Monthly net returns per book + EW, and name-month excess rows for the tail check."""
    idx = C.index; Cv = C.values
    last_valid = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                           for j in range(Cv.shape[1])])
    fs = sorted(S); me = M.month_ends(idx); nxt = {a: b for a, b in zip(me[:-1], me[1:])}
    rows, nm, prev = [], [], {}
    for a in fs:
        if a not in nxt:
            continue
        b = nxt[a]; B = S[a]; names = B["names"]
        exit_i = np.minimum(b, last_valid[names])
        r = pd.Series(Cv[exit_i, names] / Cv[a, names] - 1, index=names).replace([np.inf, -np.inf], np.nan)
        ew = r.mean()
        row = dict(month=idx[b].to_period("M"), EW=ew)
        for k in keys:
            if k not in B:
                row[k] = np.nan; continue
            s = set(B[k]); to = 1 - len(s & prev.get(k, set())) / max(len(s), 1); prev[k] = s
            row[k] = r.reindex(B[k]).mean() - 2 * M.COST * to
            row[f"n_{k}"] = len(B[k])
            nm += [dict(month=row["month"], book=k, x=v - ew) for v in r.reindex(B[k]).dropna().values]
        rows.append(row)
    return pd.DataFrame(rows).set_index("month"), pd.DataFrame(nm)


def evaluate(P: pd.DataFrame, NM: pd.DataFrame, k: str, label: str, out: list, primary=False) -> dict:
    ok = P[k].notna()
    x = (P.loc[ok, k] - P.loc[ok, "EW"]) * 100
    h = x.index < pd.Period(M.SPLIT, "M"); yr = x.groupby(x.index.year).sum()
    d = ((P.loc[ok, k] - P.loc[ok, "RAW"]) * 100) if k != "RAW" else None
    cap = NM.x.quantile(0.95)
    w = NM[NM.book == k].assign(x=lambda z: z.x.clip(upper=cap)).groupby("month").x.mean() * 100
    cum = (1 + P.loc[ok, k]).cumprod(); dd = (1 - cum / cum.cummax()).max() * 100
    res = dict(book=k, months=len(x), excess=x.mean(), t_nw=M.nw_t(x), h1=x[h].mean(), h2=x[~h].mean(),
               yrs_pos=f"{(yr > 0).sum()}/{len(yr)}", vs_raw=d.mean() if d is not None else np.nan,
               t_vs_raw=M.nw_t(d) if d is not None else np.nan, wins_p95=w.mean(), t_wins=M.nw_t(w), maxDD=dd,
               n=P.loc[ok, f"n_{k}"].mean())
    res["PASS"] = bool(res["t_nw"] >= 3 and res["h1"] > 0 and res["h2"] > 0 and (yr > 0).sum() > len(yr) / 2)
    res["BETTER"] = bool(d is not None and res["t_vs_raw"] >= 2 and res["t_wins"] > M.nw_t(
        NM[NM.book == "RAW"].assign(x=lambda z: z.x.clip(upper=cap)).groupby("month").x.mean() * 100))
    out.append(f"\n## {label}{'  <- PRIMARY' if primary else ''}: ~{res['n']:.0f} names, excess {x.mean():+.2f}pp/mo t_NW {res['t_nw']:+.2f} "
               f"halves {res['h1']:+.2f}/{res['h2']:+.2f} yrs {res['yrs_pos']} | "
               + ("" if d is None else f"vs RAW {d.mean():+.2f}pp t {res['t_vs_raw']:+.2f} | ")
               + f"p95-winsorised {w.mean():+.2f} t {res['t_wins']:+.2f} | maxDD {dd:.0f}%")
    out.append("  worst 5 excess months: " + ", ".join(f"{m}: {v:+.1f}" for m, v in x.nsmallest(5).items()))
    out.append("  excess by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in yr.items()))
    return res


def main():
    import run_dip_survivorship as DS
    out = ["# Residual momentum + frog in the pan (pre-registration in the docstring)"]
    C, V = DS.adjust_and_clean(DS.pull())
    liq = ((V.rolling(50, min_periods=30).mean() >= M.OPTVOL_MIN) & (C >= M.PX_MIN)).fillna(False)
    S = signals(C, liq)
    P, NM = returns(C, S)
    R = [evaluate(P, NM, "RAW", "RAW 12-1 decile (reference)", out),
         evaluate(P, NM, "R", "R residual momentum decile", out, True),
         evaluate(P, NM, "F", "F frog-in-the-pan (top quintile, continuous half)", out, True),
         evaluate(P, NM, "RF", "[exploratory] R quintile, continuous half", out)]
    # method check for F: ID on chain_spot vs the survivor panel's real closes
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "close"])
    raw["date"] = pd.to_datetime(raw.date)
    PC = raw.pivot(index="date", columns="ticker", values="close").sort_index()
    rhos = []
    for a, B in list(S.items())[::6]:
        dt = C.index[a]
        if dt not in PC.index:
            continue
        j = PC.index.get_loc(dt)
        if j < LOOKBACK:
            continue
        idc = B["_ID"]; tick = C.columns[idc.index]
        common = [t for t in tick if t in PC.columns]
        if len(common) < 50:
            continue
        pw = PC[common].iloc[j - LOOKBACK:j - SKIP + 1]
        dr = pw.pct_change().iloc[1:]
        pret = pw.iloc[-1] / pw.iloc[0] - 1
        idp = np.sign(pret) * ((dr < 0).sum() - (dr > 0).sum()) / dr.notna().sum().clip(lower=1)
        a_ = pd.Series(idc.values, index=tick).reindex(common)
        rhos.append(a_.rank().corr(idp.rank()))
    rho = float(np.nanmedian(rhos)) if rhos else np.nan
    out.append(f"\n## METHOD CHECK (F): median rank corr of ID chain_spot vs panel closes over {len(rhos)} formations: {rho:.2f} "
               f"({'OK' if rho >= 0.7 else 'FAILED -> F on chain_spot uninterpretable; see the panel replication'})")
    # exploratory: survivor panel replication of R and F
    from lib.regime.trailing import Panel, liquidity_mask
    pr = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet")
    pr["date"] = pd.to_datetime(pr.date); pr = pr[~pr.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(pr)
    ep = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()).fillna(False)
    Pp, NMp = returns(p.close, signals(p.close, ep))
    out.append("\n## [exploratory] survivor panel (liquid_panel_2009, ADDV >= $50M)")
    for k in ("RAW", "R", "F"):
        evaluate(Pp, NMp, k, f"panel {k}", out)
    D = pd.DataFrame(R)
    out.append("\n" + D.round(3).to_string(index=False))
    for k in ("R", "F"):
        r = D[D.book == k].iloc[0]
        out.append(f"VERDICT {k}: certification {'PASS' if r.PASS else 'fail'} (excess {r.excess:+.2f} t {r.t_nw:+.2f}); "
                   f"vs RAW {r.vs_raw:+.2f} t {r.t_vs_raw:+.2f} -> {'BETTER than raw' if r.BETTER else 'not better than raw'}"
                   + ("" if k == "R" else f"; method check {'OK' if rho >= 0.7 else 'FAILED'}"))
    D.to_csv(REPO / "data/studies/momentum_residual_frog_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
