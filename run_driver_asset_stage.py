#!/usr/bin/env python3
"""
STAGE SIGNALS ON DRIVER ASSETS (pre-registered 2026-10-04, before any data pull)

WHY. The Weinstein test (run_weinstein_stage.py, 2026-10-04): on single STOCKS the "4B-minus" reclaim (H2) is INVERTED
(-1.94pp, t -3.51) and the Stage 1->2 breakout (H1) is NULL -- yet H2 fired on BTC and IBIT on 2026-08-21, the week Gabe,
Luk and Ariel all bought crypto proxies, and its 3 BTC signals were large wins (2019-04 +63% / 2023-01 +52% at 26 weeks).
Hypothesis: stage reversals carry information for the ASSETS THAT DRIVE GROUPS (crypto, commodities, currencies, rates,
countries, sectors), not for single names. Three BTC signals are the reason to look, not evidence; this test freezes the
Weinstein-test definitions unchanged and applies them to a pre-declared list of ~50 driver assets.

UNIVERSE (frozen now; yfinance adjusted weekly closes, W-FRI; an asset enters once it has 82 weeks of history):
  crypto       BTC-USD, ETH-USD
  metals       GLD, SLV, PPLT, PALL, CPER, DBB
  energy       USO, UNG, BNO
  ags          DBA, CORN, WEAT, SOYB, CANE
  currencies   UUP, FXE, FXY, FXB, FXA, FXC, FXF, CYB
  rates/credit TLT, IEF, SHY, TIP, HYG, LQD, EMB
  countries    EWZ, EWJ, FXI, EWG, EWW, INDA, EWY, EWT, EWA, EWC, EWU, RSX(where listed), EZA, TUR
  sectors      XLE, XLF, XLK, XLU, XLV, XLP, XLY, XLB, XLI, SMH, XBI, KRE, XHB, IYR, XOP, GDX, URA, TAN
  (Assets missing from yfinance are dropped and listed; nothing is substituted.)
SIGNALS (identical to run_weinstein_stage.py; weekly; MA30 = 30-week SMA, SLOPE = MA30 / MA30 4 weeks earlier - 1,
  STAGE4 = close < MA30 & SLOPE < 0; RS is NOT used here -- a currency or a bond has no meaningful RS vs SPY):
  H2 4B-MINUS   >= 20 consecutive STAGE4 weeks ending within the prior 4 weeks; close > MA30 while SLOPE < 0 (first such
                week); prior 12 weekly closes span <= 40%.
  H1 2A         close > the highest weekly close of the prior 20 weeks (fresh); close > MA30; SLOPE >= -0.5%; a STAGE4
                week in the prior 52; 16 of the prior 20 closes within +/-15% of MA30.
  One signal per asset per 26 weeks per hypothesis. Signal weeks 2007-01 -> 2026-03 (26 weeks of follow-up).
OUTCOME, comparable across asset classes: the 26-week forward return divided by the asset's trailing 52-week st. dev.
  of weekly returns x sqrt(26) (a 26-week "z"), MINUS the same asset's mean z over all its weeks (removes each asset's
  drift). Also the raw % return.
PRIMARY: H2 demeaned 26-week z, pooled over assets, t clustered by signal week.
BAR (discovery): t >= 3, both halves (split 2017-01-01) > 0, a majority of years positive, and positive in at least 4 of
  the 7 asset classes with >= 3 signals.
SECONDARY (reported): H1 same metric; 13 weeks; per asset class; per asset; payoff with the base-low stop (lowest weekly
  close of the prior 20 weeks; exit at the first weekly close below it, else week 26; R, stop-out share, R >= 3 share);
  the expression check for drivers with a group proxy (BTC -> crypto proxies IBIT / MSTR where they exist; GLD -> GDX;
  SLV -> SIL; USO -> XOP; CPER -> COPX; URA as its own), raw 26-week return of the proxy from the same signal week;
  the live list (assets whose latest week fires H1 or H2).
PRIOR ~25%: trend-following on futures (time-series momentum) is well documented, but this is a reversal-entry
  condition after long declines, which the stock test inverted; the three BTC wins sit in one asset.

  PYTHONPATH=src:. .venv/bin/python3 run_driver_asset_stage.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf

OUT = "data/studies/driver_asset_stage_2026-10-04"
CLASSES = {
    "crypto": ["BTC-USD", "ETH-USD"],
    "metals": ["GLD", "SLV", "PPLT", "PALL", "CPER", "DBB"],
    "energy": ["USO", "UNG", "BNO"],
    "ags": ["DBA", "CORN", "WEAT", "SOYB", "CANE"],
    "currencies": ["UUP", "FXE", "FXY", "FXB", "FXA", "FXC", "FXF", "CYB"],
    "rates_credit": ["TLT", "IEF", "SHY", "TIP", "HYG", "LQD", "EMB"],
    "countries": ["EWZ", "EWJ", "FXI", "EWG", "EWW", "INDA", "EWY", "EWT", "EWA", "EWC", "EWU", "RSX", "EZA", "TUR"],
    "sectors": ["XLE", "XLF", "XLK", "XLU", "XLV", "XLP", "XLY", "XLB", "XLI", "SMH", "XBI", "KRE", "XHB", "IYR", "XOP", "GDX", "URA", "TAN"],
}
PROXY = {"BTC-USD": ["IBIT", "MSTR"], "GLD": ["GDX"], "SLV": ["SIL"], "USO": ["XOP"], "CPER": ["COPX"]}
S0, S1, SPLIT = pd.Timestamp("2007-01-01"), pd.Timestamp("2026-03-31"), pd.Timestamp("2017-01-01")


def stage(W: pd.DataFrame):
    ma = W.rolling(30, min_periods=30).mean(); slope = ma / ma.shift(4) - 1
    st4 = (W < ma) & (slope < 0)
    runlen = st4.astype(int).copy()
    for c in st4.columns:
        k = 0; r = []
        for v in st4[c].values:
            k = k + 1 if v else 0; r.append(k)
        runlen[c] = r
    long4 = runlen.shift(1).rolling(4, min_periods=1).max() >= 20
    span12 = W.shift(1).rolling(12, min_periods=12).max() / W.shift(1).rolling(12, min_periods=12).min() - 1
    h2 = long4 & (W > ma) & (slope < 0) & ~((W.shift(1) > ma.shift(1)) & (slope.shift(1) < 0)) & (span12 <= 0.40)
    res = W.shift(1).rolling(20, min_periods=20).max()
    base = ((W / ma - 1).abs() <= 0.15).astype(float).shift(1).rolling(20, min_periods=20).sum() >= 16
    had4 = st4.astype(float).shift(1).rolling(52, min_periods=30).max() >= 1
    h1 = (W > res) & ~(W.shift(1) > res.shift(1)) & (W > ma) & (slope >= -0.005) & had4 & base
    return h1.fillna(False), h2.fillna(False)


def thin(m: pd.DataFrame, gap=26) -> pd.DataFrame:
    out = m & False
    for c in m.columns:
        last = -10 ** 9
        for i in np.flatnonzero(m[c].values):
            if i - last >= gap:
                out.iat[i, out.columns.get_loc(c)] = True; last = i
    return out


def main() -> None:
    allt = sorted({t for v in CLASSES.values() for t in v} | {p for v in PROXY.values() for p in v})
    px = yf.download(allt, start="2004-01-01", auto_adjust=True, progress=False)["Close"]
    px.index = pd.to_datetime(px.index).tz_localize(None)
    W = px.resample("W-FRI").last()
    drivers = [t for v in CLASSES.values() for t in v if t in W.columns and W[t].notna().sum() >= 82]
    missing = [t for v in CLASSES.values() for t in v if t not in drivers]
    cls = {t: c for c, v in CLASSES.items() for t in v}
    Wd = W[drivers]
    r = Wd.pct_change(fill_method=None)
    sig = r.rolling(52, min_periods=40).std() * np.sqrt(26)
    rows = []
    for h in (13, 26):
        f = Wd.shift(-h) / Wd - 1
        z = f / (sig * np.sqrt(h / 26))
        zmean = z.mean()
        for lab, M in zip(("H1", "H2"), map(thin, stage(Wd))):
            for i, j in zip(*np.where(M.values)):
                d = Wd.index[i]; t = Wd.columns[j]
                if not (S0 <= d <= S1) or not np.isfinite(z.iat[i, j]):
                    continue
                rows.append(dict(h=h, hyp=lab, week=d, asset=t, cls=cls[t], ret=f.iat[i, j] * 100, zx=z.iat[i, j] - zmean[t]))
    R = pd.DataFrame(rows); R.to_csv(f"{OUT}_signals.csv", index=False)

    def ct(x, d):
        n = len(x); mu = x.mean(); g = (x - mu).groupby(d).sum(); G = len(g)
        return mu, mu / (np.sqrt((g ** 2).sum()) / n * np.sqrt(G / max(G - 1, 1))), n

    L = [f"# Stage signals on driver assets ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         f"{len(drivers)} assets; missing / too short: {missing}", ""]
    for hyp in ("H2", "H1"):
        X = R[(R.hyp == hyp) & (R.h == 26)]
        m, t, n = ct(X.zx, X.week)
        a, b = X[X.week < SPLIT].zx.mean(), X[X.week >= SPLIT].zx.mean()
        yr = X.groupby(X.week.dt.year).zx.mean()
        bycls = X.groupby("cls").zx.agg(["mean", "count"])
        ok_cls = ((bycls["count"] >= 3) & (bycls["mean"] > 0)).sum()
        ok = t >= 3 and a > 0 and b > 0 and (yr > 0).mean() > 0.5 and ok_cls >= 4
        v = ("PASS" if ok else ("INVERTED" if (t <= -3 and a < 0 and b < 0) else ("NULL" if abs(t) < 2 else "UNDERPOWERED / LEAN")))
        X13 = R[(R.hyp == hyp) & (R.h == 13)]; m13, t13, _ = ct(X13.zx, X13.week)
        L += [f"## {hyp}{' (PRIMARY)' if hyp == 'H2' else ''}", "",
              f"**{v}** — 26-week demeaned z {m:+.3f}, t {t:.2f}, n {n}; halves {a:+.3f} / {b:+.3f}; years + {(yr > 0).sum()}/{len(yr)}; "
              f"classes positive (>= 3 signals) {ok_cls}; raw 26-week return mean {X.ret.mean():+.1f}% / median {X.ret.median():+.1f}%",
              f"- 13 weeks: z {m13:+.3f} t {t13:.2f}", "", "By class:", "", bycls.round(3).to_string(), ""]
    # payoff with base-low stop (H2, 26w)
    h1m, h2m = map(thin, stage(Wd)); out = []
    for i, j in zip(*np.where(h2m.values)):
        if not (S0 <= Wd.index[i] <= S1) or i + 26 >= len(Wd):
            continue
        e = Wd.iat[i, j]; stop = Wd.iloc[max(0, i - 20):i, j].min()
        if not (np.isfinite(e) and np.isfinite(stop) and e > stop):
            continue
        risk = (e - stop) / e; res = None
        for k in range(i + 1, i + 27):
            c = Wd.iat[k, j]
            if np.isfinite(c):
                res = (c / e - 1) / risk
                if c < stop:
                    out.append((res, True)); break
        else:
            if res is not None:
                out.append((res, False))
    P = pd.DataFrame(out, columns=["R", "stopped"])
    L += [f"H2 payoff with the base-low stop: mean R {P.R.mean():+.2f}, median {P.R.median():+.2f}, win {(P.R > 0).mean():.0%}, "
          f"stopped {P.stopped.mean():.0%}, R >= 3 {(P.R >= 3).mean():.0%} (n {len(P)})", ""]
    # proxy expression
    L += ["## Proxy expression (raw 26-week return from the same signal week, %)", ""]
    for d_, ps in PROXY.items():
        X = R[(R.asset == d_) & (R.h == 26)]
        for x in X.itertuples():
            k = W.index.get_loc(x.week)
            vals = []
            for p in ps:
                if p in W.columns and k + 26 < len(W) and np.isfinite(W[p].iat[k]) and np.isfinite(W[p].iat[k + 26]):
                    vals.append(f"{p} {(W[p].iat[k + 26] / W[p].iat[k] - 1) * 100:+.1f}")
            L.append(f"- {x.hyp} {d_} {x.week.date()}: driver {x.ret:+.1f} | " + (", ".join(vals) or "no proxy data"))
    last = Wd.index[-1]
    L += ["", f"## Live (week of {last.date()})", "", "H1: " + " ".join(Wd.columns[stage(Wd)[0].loc[last].values]),
          "H2: " + " ".join(Wd.columns[stage(Wd)[1].loc[last].values]), "", "## All signals (26 weeks)", "",
          R[R.h == 26].sort_values(["hyp", "week"]).assign(week=lambda z: z.week.dt.date).round(2).to_string(index=False)]
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
