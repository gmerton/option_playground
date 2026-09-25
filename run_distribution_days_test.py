#!/usr/bin/env python3
"""
Do O'Neil distribution-day counts predict SPY? (pre-registered 2026-09-24, before the first run)

WHY. market_conditions.py flags "SPY 9 distribution days (SERIOUS — defend / raise cash)" on 2026-09-24. The ledger
has no row on distribution days; the nearest O'Neil signal (the follow-through day) FAILED as a regime switch, and
every trailing-30d breadth rule failed 2019-26. New axis: the count itself.

DESIGN
  data      SPY daily OHLCV from 1994-01 (yfinance, auto-adjusted closes, raw volume). QQQ from 1999-04 as robustness.
  count     EXACTLY the desk's rule (market_conditions.count_distribution_days): close <= -0.2% vs the prior close AND
            volume > the prior session's, counted over the trailing 25 sessions (inclusive of today).
            Exploratory variants: IBD's expiry (a day drops once the index closes >= 5% above that day's close) and a
            strict-volume rule (volume >= 1.2x the prior session).
  regime    BULL = the report's verdict: close > 50SMA and > 200SMA, 50SMA rising vs 5 sessions ago.
  outcomes  fwd20  = SPY return over the next 20 sessions;
            rv20   = realised vol (annualised) over the next 20 sessions, and xrv20 = rv20 minus the trailing 20d RV;
            dd5    = P(close falls >= 5% below today's close within the next 20 sessions).
  PRIMARY   inside BULL: high count (>= 6) minus low count (<= 3), on fwd20. O'Neil's prediction: negative.
  sampling  non-overlapping: every 20th session (so each forward window is used once); t on the difference of
            bucket means (Welch). Robustness: all 20 phase offsets averaged, and Newey-West on the overlapping daily
            series (lag 20).
  bar       |t| >= 3 on the primary, halves (split 2010-01) the same sign, and the sign holding in >= 3 of 4
            decades-ish blocks (1994-2003, 2004-2012, 2013-2019, 2020-2026). Everything else is exploratory.
  caveat    SPY ETF volume is not the exchange composite volume IBD uses; early-1990s SPY volume is thin.

Usage: PYTHONPATH=src .venv/bin/python3 run_distribution_days_test.py > data/studies/logs/distribution_days_test.log
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore"); pd.set_option("display.width", 200)

H, LOOK, HI, LO, SPLIT = 20, 25, 6, 3, "2010-01-01"
BLOCKS = [("1994", "2003"), ("2004", "2012"), ("2013", "2019"), ("2020", "2026")]


def load(tk: str, start: str) -> pd.DataFrame:
    d = yf.download(tk, start=start, auto_adjust=True, progress=False)
    d.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in d.columns]
    return d[["close", "volume"]].dropna()


def counts(d: pd.DataFrame) -> pd.DataFrame:
    c, v = d.close, d.volume
    chg = c.pct_change()
    ddays = (chg <= -0.002) & (v > v.shift(1))
    strict = (chg <= -0.002) & (v >= 1.2 * v.shift(1))
    out = pd.DataFrame(index=d.index)
    out["n"] = ddays.rolling(LOOK).sum()
    out["n_strict"] = strict.rolling(LOOK).sum()
    # IBD expiry: a distribution day stops counting once any later close is >= 5% above its close
    cv = c.values; dv = ddays.values; n_exp = np.full(len(c), np.nan)
    for t in range(LOOK, len(c)):
        k = 0
        for s in range(t - LOOK + 1, t + 1):
            if dv[s] and cv[s:t + 1].max() < cv[s] * 1.05:
                k += 1
        n_exp[t] = k
    out["n_ibd"] = n_exp
    s50, s200 = c.rolling(50).mean(), c.rolling(200).mean()
    out["bull"] = (c > s50) & (c > s200) & (s50 > s50.shift(5))
    r = np.log(c).diff()
    out["fwd20"] = (c.shift(-H) / c - 1) * 100
    out["rv20"] = r[::-1].rolling(H).std()[::-1].shift(-1) * sqrt(252) * 100
    out["trv20"] = r.rolling(H).std() * sqrt(252) * 100
    out["xrv20"] = out.rv20 - out.trv20
    fmin = pd.concat([c.shift(-k) for k in range(1, H + 1)], axis=1).min(axis=1)
    out["dd5"] = (fmin <= c * 0.95).astype(float).where(fmin.notna())
    return out.dropna(subset=["n", "fwd20"])


def welch(a: pd.Series, b: pd.Series) -> tuple[float, float]:
    a, b = a.dropna(), b.dropna()
    if len(a) < 3 or len(b) < 3:
        return np.nan, np.nan
    d = a.mean() - b.mean()
    return d, d / sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def nw_t(y: np.ndarray, lag: int = H) -> float:
    """Newey-West t of the mean of y (overlapping observations)."""
    y = y[np.isfinite(y)]; n = len(y); e = y - y.mean()
    s = e @ e / n
    for L in range(1, lag + 1):
        s += 2 * (1 - L / (lag + 1)) * (e[L:] @ e[:-L]) / n
    return y.mean() / sqrt(s / n)


def cell(D: pd.DataFrame, col: str, outcome: str, mask: pd.Series, phase: int = 0) -> dict:
    S = D[mask].iloc[phase::H] if phase >= 0 else D[mask]
    hi, lo = S[S[col] >= HI][outcome], S[S[col] <= LO][outcome]
    d, t = welch(hi, lo)
    return dict(n_hi=hi.count(), n_lo=lo.count(), hi=hi.mean(), lo=lo.mean(), diff=d, t=t)


def report(tk: str, D: pd.DataFrame, primary: bool) -> None:
    bull = D.bull
    print(f"\n{'='*100}\n{tk}: {D.index[0].date()} -> {D.index[-1].date()}, {len(D):,} sessions; BULL share "
          f"{bull.mean():.0%}; count >= {HI} on {(D.n >= HI).mean():.0%} of sessions, <= {LO} on {(D.n <= LO).mean():.0%}")
    print(f"current count (desk rule) {int(D.n.iloc[-1])} | strict x1.2 {int(D.n_strict.iloc[-1])} | IBD expiry {int(D.n_ibd.iloc[-1])}")
    # distribution of the count
    print("count distribution (share of sessions):",
          D.n.value_counts(normalize=True).sort_index().round(3).to_dict())
    rows = []
    for col in ("n", "n_ibd", "n_strict"):
        for rname, m in (("BULL", bull), ("ALL", pd.Series(True, index=D.index))):
            for out in ("fwd20", "xrv20", "rv20", "dd5"):
                c0 = cell(D, col, out, m, 0)
                ph = [cell(D, col, out, m, p)["diff"] for p in range(H)]
                sub = D[m]; y = np.where(sub[col] >= HI, 1.0, np.where(sub[col] <= LO, 0.0, np.nan))
                # NW on the overlapping series: regress outcome on the hi dummy (hi vs lo only)
                ok = np.isfinite(y) & sub[out].notna().values
                yy, xx = sub[out].values[ok], y[ok]
                beta = yy[xx == 1].mean() - yy[xx == 0].mean() if (xx == 1).any() and (xx == 0).any() else np.nan
                resid = yy - np.where(xx == 1, yy[xx == 1].mean(), yy[xx == 0].mean())
                t_nw = np.nan
                if np.isfinite(beta):
                    X = np.column_stack([np.ones(len(xx)), xx]); XtX = np.linalg.inv(X.T @ X)
                    u = X * resid[:, None]; S = u.T @ u
                    for L in range(1, H + 1):
                        G = u[L:].T @ u[:-L]; S += (1 - L / (H + 1)) * (G + G.T)
                    V = XtX @ S @ XtX; t_nw = beta / sqrt(V[1, 1])
                rows.append(dict(count=col, regime=rname, outcome=out, n_hi=c0["n_hi"], n_lo=c0["n_lo"],
                                 hi=c0["hi"], lo=c0["lo"], diff=c0["diff"], t_nonoverlap=c0["t"],
                                 diff_phase_avg=np.nanmean(ph), t_nw=t_nw))
    R = pd.DataFrame(rows)
    print(R.round(3).to_string(index=False))
    if primary:
        m = bull
        P = R[(R["count"] == "n") & (R.regime == "BULL") & (R.outcome == "fwd20")].iloc[0]
        halves, blocks = [], []
        for a, b in ((None, SPLIT), (SPLIT, None)):
            mm = m & (D.index >= a if a else True) & (D.index < b if b else True)
            halves.append(cell(D, "n", "fwd20", mm, 0)["diff"])
        for a, b in BLOCKS:
            mm = m & (D.index >= f"{a}-01-01") & (D.index <= f"{b}-12-31")
            c = cell(D, "n", "fwd20", mm, 0); blocks.append(c["diff"])
            print(f"  block {a}-{b}: hi {c['hi']:+.2f}% (n {c['n_hi']}) vs lo {c['lo']:+.2f}% (n {c['n_lo']}) -> diff {c['diff']:+.2f}pp")
        sgn = np.sign(P["diff"])
        ok_blocks = sum(np.sign(x) == sgn for x in blocks if np.isfinite(x))
        passed = bool(abs(P.t_nonoverlap) >= 3 and all(np.sign(h) == sgn for h in halves) and ok_blocks >= 3)
        print(f"\nPRIMARY (BULL, count >= {HI} vs <= {LO}, fwd20): diff {P['diff']:+.2f}pp, t {P.t_nonoverlap:+.2f} "
              f"(non-overlapping), phase-avg diff {P.diff_phase_avg:+.2f}pp, NW t {P.t_nw:+.2f}; halves "
              f"{halves[0]:+.2f} / {halves[1]:+.2f}; blocks same sign {ok_blocks}/4 -> passes: {'YES' if passed else 'no'}")
    return R


if __name__ == "__main__":
    spy = counts(load("SPY", "1993-01-01"))
    R = report("SPY", spy, primary=True)
    R.to_csv("data/studies/distribution_days_test_2026-09-24.csv", index=False)
    qqq = counts(load("QQQ", "1999-03-01"))
    report("QQQ (robustness)", qqq, primary=False)
