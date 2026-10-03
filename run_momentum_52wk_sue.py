#!/usr/bin/env python3
"""
12-1 MOMENTUM vs/with the 52-WEEK-HIGH score (George & Hwang 2004) and EARNINGS MOMENTUM (SUE; Chan, Jegadeesh &
Lakonishok 1996; Novy-Marx 2015). Pre-registered 2026-10-02, before any run (Gabe: "run #1 and #2 together").

WHY NEW. The certified sleeve has been varied on lookback, skip, bucket size, book size, buffer, vol scaling,
residual/frog, trend filter, entry timing and vehicle. It has never been ranked on proximity to the 52-week high, nor
combined with an earnings signal. Earnings priors: PEAD event study NULL (2026-09-20), CAN SLIM "C" growth filter
NULL (2026-09-30) -> the prior on #2 is LOW; it is run because a COMBINED price+earnings rank on the monthly sleeve is an
untouched axis (CJL/Novy-Marx argue each subsumes part of the other).

DATA  identical to the certified PRIMARY unless stated: silver.chain_spot_daily closes incl. delisted
      (run_dip_survivorship pull/adjust_and_clean), eligibility = 50-session mean option volume >= 1,000 and price >= $5
      at formation, month-end formations 2011-01 -> 2026-01, top decile, equal weight, hold one month, 10 bp/side on
      turnover (run_momentum_portfolio.portfolio mechanics, delisted -> last close).
  PTH   close(t) / max(close over the last 252 sessions incl. t). Closes only (GH use the daily high; ours is the
        close-only analogue). Needs 252 sessions.
  SUE   data/cache/earnings_yf.parquet (yfinance eps_act, adjusted basis, point-in-time report dates; ~1,300 CURRENT
        names -> survivor-biased coverage). Per ticker, reports sorted: d_q = eps_q - eps_{q-4}, only if the q-4 report
        is 300-430 days earlier. SUE_q = d_q / std(d over the last 8 quarters incl. q), needing >= 4 values and std > 0.
        Known from the session AFTER the report session (conservative for BMO), held until the next report, expired
        after 100 sessions.

CELLS
  #1  H1  [REPLICATION PRIMARY] top decile by PTH, full eligible universe. Premium published 2004 on 1963-2001 data;
          our sample is post-publication. Statistic: monthly excess over the EW universe, NW t (lag 3).
          Replication bar: t >= 2 (own Sidak over ONE replication cell = 1.96 -> 2 governs), both halves (2018-01) > 0,
          majority of years > 0. Survivorship-free universe. -> CERTIFIED (replication) if it passes.
      H1v [discovery] H1 - BASE (12-1 top decile), paired monthly: does PTH beat 12-1?
      H2  [discovery] composite: mean of the cross-sectional percentile ranks of 12-1 and PTH, top decile, vs BASE.
  #2  (all on the SUE-COVERED eligible universe; BASE-cov = 12-1 top decile of covered names, and every cell is
       differenced against BASE-cov so coverage/survivorship is shared by both arms)
      E1  [discovery PRIMARY for #2] composite: mean percentile rank of 12-1 and SUE, top decile, vs BASE-cov.
      E2  [discovery] BASE-cov names with SUE above the covered-universe median that month, vs BASE-cov.
      E3  [discovery, exploratory] SUE alone top decile vs BASE-cov.
BAR (discovery cells) M = 5 (H1v, H2, E1, E2, E3) -> Sidak |t| >= 2.57; the house |t| >= 3 governs, both halves the
      same sign as the mean, majority of years. Primaries named in advance: H1 (replication), E1 (#2).
REPORTED  each arm's %/mo, excess over its EW universe, paired diff, t, halves, years +, maxDD, turnover, names held;
      covered-universe size; correlation of H1 and BASE monthly returns.
KNOWN BIASES
  - PTH on closes, not highs (slightly lower max -> PTH a bit higher; ranking barely affected).
  - SUE coverage is today's names -> covered universe is survivor-biased; compare arms (shared bias), not levels.
  - yfinance eps_act is adjusted/consensus-basis EPS, not GAAP; ~3% of reports have no prior-year match.
READ  H1 CERTIFIED -> a second certified sleeve; if H1v/H2 also pass, PTH replaces/joins 12-1 in the screener.
      E1 PASS -> add an earnings sort to the screener. NULL -> stay on plain 12-1.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_momentum_52wk_sue.py
       (log -> data/studies/logs/momentum_52wk_sue.log; table data/studies/momentum_52wk_sue_2026-10-02.csv)
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

import run_momentum_portfolio as M

warnings.filterwarnings("ignore")
REPO = M.REPO
LOG = REPO / "data/studies/logs/momentum_52wk_sue.log"
COST, SPLIT = M.COST, M.SPLIT


def pct_rank(x: np.ndarray, ok: np.ndarray) -> np.ndarray:
    r = np.full(x.shape, np.nan)
    r[ok] = pd.Series(x[ok]).rank(pct=True).values
    return r


def port(C: pd.DataFrame, elig: np.ndarray, score_at, top: float = 0.10, keep_at=None) -> pd.DataFrame:
    """M.portfolio mechanics with a pluggable score. score_at(a) -> score vector over columns (nan = not rankable).
    keep_at(a, mom_idx, names) optionally filters the selected names. EW universe = all rankable eligible names."""
    idx = C.index; Cv = C.values
    last_valid = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                           for j in range(Cv.shape[1])])
    me = [i for i in M.month_ends(idx) if pd.Timestamp(M.START) <= idx[i] <= pd.Timestamp(M.END)]
    rows, prev_m, prev_e = [], set(), set()
    for a, b in zip(me[:-1], me[1:]):
        if a - 252 < 0:
            continue
        s = score_at(a)
        ok = elig[a] & np.isfinite(s) & np.isfinite(Cv[a])
        if ok.sum() < 50:
            continue
        names = np.flatnonzero(ok)
        cut = np.nanquantile(s[names], 1 - top)
        mom = names[s[names] >= cut]
        if keep_at is not None:
            mom = keep_at(a, mom, names)
        if len(mom) == 0:
            continue
        exit_i = np.minimum(b, last_valid[names])
        r = pd.Series(Cv[exit_i, names] / Cv[a, names] - 1, index=names).replace([np.inf, -np.inf], np.nan)
        sm, se = set(mom), set(names)
        to_m = 1 - len(sm & prev_m) / max(len(sm), 1); to_e = 1 - len(se & prev_e) / max(len(se), 1)
        rows.append(dict(month=idx[b].to_period("M"), mom=r.reindex(mom).mean() - 2 * COST * to_m,
                         ew=r.mean() - 2 * COST * to_e, n_mom=len(mom), n_univ=len(names), turnover=to_m))
        prev_m, prev_e = sm, se
    return pd.DataFrame(rows).set_index("month")


def stats_x(x: pd.Series) -> dict:
    h = x.index < pd.Period(SPLIT, "M"); yr = x.groupby(x.index.year).sum()
    return dict(mean=x.mean(), t=M.nw_t(x), h1=x[h].mean(), h2=x[~h].mean(), yp=(yr > 0).sum(), yn=len(yr), yr=yr)


def report(P: pd.DataFrame, B: pd.DataFrame | None, label: str, out: list[str], bar: str) -> dict:
    exc = stats_x((P.mom - P.ew) * 100)
    cum = (1 + P.mom).cumprod(); dd = (1 - cum / cum.cummax()).max() * 100
    res = dict(cell=label, months=len(P), arm_mo=100 * P.mom.mean(), ew_mo=100 * P.ew.mean(), excess_ew=exc["mean"],
               t_excess=exc["t"], ex_h1=exc["h1"], ex_h2=exc["h2"], ex_yrs=f"{exc['yp']}/{exc['yn']}", maxDD=dd,
               turnover=P.turnover.mean(), n_mom=P.n_mom.mean(), n_univ=P.n_univ.mean())
    out.append(f"\n## {label}  ({len(P)} months, ~{P.n_mom.mean():.0f} of {P.n_univ.mean():.0f} names, turnover {P.turnover.mean():.0%}/mo)")
    out.append(f"  arm {res['arm_mo']:+.2f}%/mo vs its EW {res['ew_mo']:+.2f}% | excess {exc['mean']:+.2f}pp t_NW {exc['t']:+.2f} | "
               f"halves {exc['h1']:+.2f} / {exc['h2']:+.2f} | years + {exc['yp']}/{exc['yn']} | maxDD {dd:.1f}%")
    if bar == "replication":
        ok = exc["t"] >= 2 and exc["h1"] > 0 and exc["h2"] > 0 and exc["yp"] > exc["yn"] / 2
        res["verdict"] = "CERTIFIED (replication)" if ok else "fail (replication)"
        out.append("  excess by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in exc["yr"].items()) + f"  -> {res['verdict']}")
    if B is not None:
        j = P.join(B, rsuffix="_b", how="inner")
        d = stats_x((j.mom - j.mom_b) * 100); sg = np.sign(d["mean"])
        ok = abs(d["t"]) >= 3 and np.sign(d["h1"]) == sg and np.sign(d["h2"]) == sg and \
            ((d["yp"] if sg > 0 else d["yn"] - d["yp"]) > d["yn"] / 2)
        res.update(diff=d["mean"], t_diff=d["t"], d_h1=d["h1"], d_h2=d["h2"], d_yrs=f"{d['yp']}/{d['yn']}",
                   corr_base=j.mom.corr(j.mom_b))
        if bar == "discovery":
            res["verdict"] = "PASS" if ok else "fail"
        out.append(f"  vs base: {d['mean']:+.2f}pp/mo t_NW {d['t']:+.2f} | halves {d['h1']:+.2f} / {d['h2']:+.2f} | "
                   f"years + {d['yp']}/{d['yn']} | corr {res['corr_base']:.2f}")
        out.append("  diff by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in d["yr"].items())
                   + (f"  -> {res['verdict']}" if bar == "discovery" else ""))
    return res


def build_sue(C: pd.DataFrame) -> pd.DataFrame:
    e = pd.read_parquet(REPO / "data/cache/earnings_yf.parquet", columns=["ticker", "eps_act", "session"])
    e = e.dropna(subset=["eps_act", "session"]); e["session"] = pd.to_datetime(e.session)
    e = e[e.ticker.isin(C.columns)].sort_values(["ticker", "session"]).drop_duplicates(["ticker", "session"])
    idx = C.index; S = pd.DataFrame(np.nan, index=idx, columns=C.columns)
    for t, g in e.groupby("ticker"):
        dts = g.session.values; eps = g.eps_act.values; d = np.full(len(g), np.nan)
        for q in range(4, len(g)):
            gap = (dts[q] - dts[q - 4]) / np.timedelta64(1, "D")
            if 300 <= gap <= 430:
                d[q] = eps[q] - eps[q - 4]
        sue = np.full(len(g), np.nan)
        for q in range(len(g)):
            w = d[max(0, q - 7): q + 1]; w = w[np.isfinite(w)]
            if np.isfinite(d[q]) and len(w) >= 4 and w.std(ddof=1) > 0:
                sue[q] = d[q] / w.std(ddof=1)
        col = pd.Series(np.nan, index=idx)
        for dt, v in zip(dts, sue):
            if not np.isfinite(v):
                continue
            pos = idx.searchsorted(pd.Timestamp(dt), side="right")          # first session AFTER the report session
            if pos < len(idx):
                col.iloc[pos] = v
        S[t] = col.ffill(limit=100)
    return S


def main():
    import run_dip_survivorship as DS
    out = ["# 12-1 momentum vs/with 52-week high (George-Hwang) and SUE (pre-registration in the docstring)"]
    d = DS.pull(); C, V = DS.adjust_and_clean(d)
    elig = ((V.rolling(50, min_periods=30).mean() >= M.OPTVOL_MIN) & (C >= M.PX_MIN)).fillna(False).values
    Cv = C.values
    hi = C.rolling(252, min_periods=252).max().values
    pth = Cv / hi
    mom = lambda a: Cv[a - 21] / Cv[a - 252] - 1
    S = build_sue(C).values
    out.append(f"\nSUE: {np.isfinite(S).any(axis=0).sum():,} chain_spot names ever covered")

    B = port(C, elig, mom)
    out.append(f"BASE 12-1 (this engine): {100*B.mom.mean():+.2f}%/mo, excess {100*(B.mom-B.ew).mean():+.2f}pp (certified +1.65 / +0.67)")
    R = []
    R.append(report(port(C, elig, lambda a: pth[a]), None, "H1 [REPLICATION PRIMARY] top decile by 52-week-high proximity", out, "replication"))
    R.append(report(port(C, elig, lambda a: pth[a]), B, "H1v [discovery] PTH decile vs 12-1 decile", out, "discovery"))

    def comp_pth(a):
        m, p = mom(a), pth[a]; ok = elig[a] & np.isfinite(m) & np.isfinite(p)
        return (pct_rank(m, ok) + pct_rank(p, ok)) / 2
    R.append(report(port(C, elig, comp_pth), B, "H2 [discovery] composite rank 12-1 + PTH vs 12-1", out, "discovery"))

    # earnings: covered universe only
    cov = lambda a: np.where(np.isfinite(S[a]), 1.0, np.nan)
    Bc = port(C, elig, lambda a: mom(a) * cov(a))
    out.append(f"\nBASE-cov 12-1 on SUE-covered names: {100*Bc.mom.mean():+.2f}%/mo, excess {100*(Bc.mom-Bc.ew).mean():+.2f}pp, "
               f"universe ~{Bc.n_univ.mean():.0f} names")

    def comp_sue(a):
        m, s = mom(a), S[a]; ok = elig[a] & np.isfinite(m) & np.isfinite(s)
        return (pct_rank(m, ok) + pct_rank(s, ok)) / 2
    R.append(report(port(C, elig, comp_sue), Bc, "E1 [discovery PRIMARY #2] composite rank 12-1 + SUE vs BASE-cov", out, "discovery"))

    def keep_hi_sue(a, sel, names):
        med = np.nanmedian(S[a, names]); return sel[S[a, sel] > med]
    R.append(report(port(C, elig, lambda a: mom(a) * cov(a), keep_at=keep_hi_sue), Bc,
                    "E2 [discovery] BASE-cov names with SUE above median vs BASE-cov", out, "discovery"))
    R.append(report(port(C, elig, lambda a: S[a]), Bc, "E3 [discovery, exploratory] SUE alone top decile vs BASE-cov", out, "discovery"))

    D = pd.DataFrame(R)
    out.append("\n" + D.round(3).to_string(index=False))
    out.append("\nReplication bar (H1): t >= 2, both halves, majority of years. Discovery: Sidak(5) 2.57, house |t| >= 3 governs.")
    D.to_csv(REPO / "data/studies/momentum_52wk_sue_2026-10-02.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
