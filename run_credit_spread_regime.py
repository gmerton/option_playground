#!/usr/bin/env python3
"""Credit-spread widening (FRED BAA10Y) vs S&P forward return / vol beyond VIX (2026-09-29).
PRE-REGISTERED: data/studies/credit_spread_regime_2026-09-29.md (committed f9f3b17 before this ran).
Usage: PYTHONPATH=src:. .venv/bin/python3 run_credit_spread_regime.py > data/studies/credit_spread_regime_2026-09-29.log
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf

H, BAR, SPLIT = 21, 3.2, "2008-01-01"


def nw(y, X, lags=21):
    d = pd.concat([y, X], axis=1).dropna()
    return sm.OLS(d.iloc[:, 0], sm.add_constant(d.iloc[:, 1:])).fit(cov_type="HAC", cov_kwds={"maxlags": lags}), len(d)


cs = pd.read_csv("data/cache/fred/BAA10Y.csv", parse_dates=["observation_date"], na_values=".").set_index("observation_date").BAA10Y
px = yf.download(["^GSPC", "^VIX", "HYG", "IEF"], start="1986-01-01", end="2026-09-26", auto_adjust=True, progress=False)["Close"]
s, vix = px["^GSPC"].dropna(), px["^VIX"]
D = pd.DataFrame({"s": s}).join(vix.rename("vix")).join(cs.rename("cs"))
D["cs"] = D.cs.ffill(limit=3)
lr = np.log(D.s / D.s.shift(1))
D["fwd"] = np.log(D.s.shift(-H) / D.s)
D["rv_fwd"] = np.sqrt(252 * (lr ** 2)[::-1].rolling(H).mean()[::-1].shift(-1))
D["rv_past"] = np.sqrt(252 * (lr ** 2).rolling(H).mean())
D["past"] = np.log(D.s / D.s.shift(H))
D["dcs"] = D.cs - D.cs.shift(20)
D["cs_pct"] = D.cs.rolling(252, min_periods=200).rank(pct=True)
hy, ief = px["HYG"], px["IEF"]
D["hy_rel"] = (np.log(hy / hy.shift(20)) - np.log(ief / ief.shift(20))).reindex(D.index)
dd = np.array([D.s.values[i + 1:i + 64].min() / D.s.values[i] - 1 if i + 63 < len(D) else np.nan for i in range(len(D))])
D["dd10"] = dd <= -0.10
D.loc[np.isnan(dd), "dd10"] = np.nan
D = D[(D.index >= "1990-01-01") & (D.index <= "2026-08-31")]

out = [f"# Credit spread regime (pre-registration in the md). {D.index.min().date()} -> {D.index.max().date()}, {len(D):,} sessions"]


def run(label, sig, lo_ok):
    res = {}
    for nm, y, X, sign in (("P1 returns", D.fwd, pd.DataFrame({"sig": sig, "vix": D.vix, "past": D.past}), -1),
                           ("P2 vol", np.log(D.rv_fwd), pd.DataFrame({"sig": sig, "lvix": np.log(D.vix), "lrv": np.log(D.rv_past)}), +1)):
        f, n = nw(y, X)
        h = []
        for a, b in (("1990-01-01", SPLIT), (SPLIT, "2027-01-01")):
            m = (y.index >= a) & (y.index < b)
            fh, _ = nw(y[m], X[m]); h.append((fh.params.sig, fh.tvalues.sig))
        ok = np.sign(f.params.sig) == sign and abs(f.tvalues.sig) >= BAR and all(np.sign(c) == sign for c, _ in h)
        out.append(f"  {label} | {nm}: coef {f.params.sig:+.4f} t {f.tvalues.sig:+.2f} (n {n:,}); halves {h[0][0]:+.4f} (t {h[0][1]:+.2f}) / "
                   f"{h[1][0]:+.4f} (t {h[1][1]:+.2f})" + (f" -> {'PASS' if ok else 'FAIL'}" if lo_ok else ""))
        res[nm] = ok
    return res


out.append("\n== PRIMARY: dCS = 20-session change in BAA10Y (pp) ==")
r = run("dCS", D.dcs, True)
out.append("\n== reported ==")
run("BAA10Y level pct", D.cs_pct, False)
run("HYG - IEF 20d rel (sign flipped: weakness = +)", -D.hy_rel, False)
fl = D.dcs >= 0.30
out.append(f"  flag dCS >= +0.30pp: {fl.mean():.1%} of sessions; P(>=10% dd in 63d) {D.dd10[fl].mean():.1%} vs {D.dd10[~fl & D.dcs.notna()].mean():.1%}; "
           f"fwd21 {100 * D.fwd[fl].mean():+.2f}% vs {100 * D.fwd[~fl & D.dcs.notna()].mean():+.2f}%")
try:
    import run_gex_regime_pin as g
    _, net, _ = g.gex_series("SPY", g.daily_bars("SPY"))
    neg = (net.sort_index().reindex(D.index) < 0).astype(float)
    sub = D.index >= "2010-01-01"
    for nm, y, X in (("P2 vol + GEX", np.log(D.rv_fwd), pd.DataFrame({"sig": D.dcs, "lvix": np.log(D.vix), "lrv": np.log(D.rv_past), "neg": neg})),
                     ("P1 returns + GEX", D.fwd, pd.DataFrame({"sig": D.dcs, "vix": D.vix, "past": D.past, "neg": neg}))):
        f, n = nw(y[sub], X[sub])
        out.append(f"  2010+ {nm}: dCS coef {f.params.sig:+.4f} t {f.tvalues.sig:+.2f} (n {n:,}); GEX-neg coef {f.params.neg:+.4f} t {f.tvalues.neg:+.2f}")
except Exception as e:
    out.append(f"  GEX control skipped: {e}")
last = D.dropna(subset=["cs"]).iloc[-1]
out.append(f"\nTODAY ({last.name.date()}): BAA10Y {last.cs:.2f}, dCS20 {last.dcs:+.2f}pp, level pct {last.cs_pct:.0%}, VIX {last.vix:.1f}")
out.append(f"VERDICT: P1 {'PASS' if r['P1 returns'] else 'FAIL'}, P2 {'PASS' if r['P2 vol'] else 'FAIL'}")
print("\n".join(out))
