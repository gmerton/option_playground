#!/usr/bin/env python3
"""
Rates regime x rate sensitivity: which breakouts to take when yields are RISING or STEADY-HIGH
(pre-registered 2026-09-28, committed before any run).

WHY. Gabe 2026-09-28: the 10-year hit 5.24% and the book is concentrated in long-duration tech. Question: when rates are
rising fast, or sitting high and steady, does the house breakout's expectancy depend on how rate-sensitive the stock is?
Nothing in the ledger tests rates as a conditioning variable (TLT/XLF regime switches died on costs; rotation / group
strength NULL; FOMC noise).

PRE-REGISTRATION
  Panel     liquid_panel_2009 (2009 -> 2026-09), eligible = ADDV50 >= $50M, px >= $5, not a split artefact; ETFs out.
  Events    HOUSE breakout pool: close > prior 20-session high, ADR >= 3, eligible (the 44k-event pool of
            entry_vs_stop). Secondary: the precision tier (run_oneil_pyramid_8wk.py definition).
  Trade     buy the close; stop = min(entry-day low, close x 0.98) judged on the close; exit on the first close < stop or
            < 20 EMA; 60-session cap; outcome in % of entry.
  Rate beta per name-day, PARTIAL beta of daily returns on the daily change in the 10-year yield (^TNX, in percentage
            points) controlling for SPY's return, over the prior 252 sessions (min 180), lagged one session. Terciles
            across ALL eligible names on each date: T1 = most negative (falls when yields rise: long duration),
            T3 = most positive (beneficiaries).
  Regimes   (from ^TNX at the entry close)
            RISING       20-session change >= +0.30 pp
            FALLING      20-session change <= -0.30 pp          (reported, not tested)
            HIGH-STEADY  level >= 4.00% AND |20-session change| < 0.15 pp
            NORMAL       everything else (the reference)
  Statistic per date: gap = mean %(T3 breakouts) - mean %(T1 breakouts), dates with >= 1 of each. Regress the gap on
            RISING / FALLING / HIGH-STEADY dummies (NORMAL = intercept), weights = number of events that date,
            SE clustered by calendar month.
  PRIMARY   H1 = RISING coefficient (does the beneficiary-minus-victim gap widen when yields rise fast?)
            H2 = HIGH-STEADY coefficient.
            Bar: |t| >= 3.2 (Sidak for 2 on the house |t| 3) AND the sign holds in a majority of regime EPISODES
            (runs of regime days, gaps > 20 sessions start a new episode) -- time halves are not used because
            HIGH-STEADY exists only from 2023 (the level >= 4% is era-confounded; stated caveat).
  Secondary (exploratory) same on the precision tier; RELATIVE-high version of H2 (level in the top quintile of its
            trailing 5-year range and |20d change| < 0.15) to separate "high" from "2023-26"; per-regime means of T1 / T2
            / T3 in absolute %.
  Caveats   survivorship (today's liquid names; the within-date gap is what is tested); one high-rate era.

Usage: PYTHONPATH=src .venv/bin/python3 run_rates_regime_breakouts.py > data/studies/logs/rates_regime_breakouts.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
ETF = {"SPY", "QQQ", "IWM", "RSP", "DIA"}


def tnx():
    import yfinance as yf
    s = yf.download("^TNX", start="2007-01-01", end="2026-10-01", progress=False, auto_adjust=False)["Close"].squeeze()
    s.index = pd.to_datetime(s.index).normalize()
    return s.dropna()


def main():
    raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet")
    p = Panel.from_long(raw)
    spy = p.close["SPY"]
    keep = [c for c in p.close.columns if c not in ETF]
    C, H, L = p.close[keep], p.high[keep], p.low[keep]
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index().reindex_like(p.close)[keep]
    V = (p.dolvol / p.close)[keep]
    elig = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect())[keep].fillna(False)
    y = tnx().reindex(C.index).ffill()
    dy = y.diff()
    # ---- partial rate beta, rolling 252 (min 180), lagged
    r = C.pct_change(fill_method=None); m = spy.pct_change(fill_method=None).reindex(C.index)
    W, MP = 252, 180
    E = lambda x: x.rolling(W, min_periods=MP).mean()
    Em, Ey, Er = E(m), E(dy), E(r)
    vm = E(m * m) - Em ** 2; vy = E(dy * dy) - Ey ** 2; cmy = E(m * dy) - Em * Ey
    crm = E(r.mul(m, axis=0)).sub(Er.mul(Em, axis=0)); cry = E(r.mul(dy, axis=0)).sub(Er.mul(Ey, axis=0))
    den = vy * vm - cmy ** 2
    by = (cry.mul(vm, axis=0) - crm.mul(cmy, axis=0)).div(den, axis=0).shift(1)
    terc = by.where(elig).rank(axis=1, pct=True)
    tcls = np.select([terc <= 1 / 3, terc > 2 / 3], [1, 3], default=2).astype(float)
    tcls = pd.DataFrame(tcls, index=C.index, columns=C.columns).where(terc.notna())
    # ---- regimes
    ch20 = y - y.shift(20)
    lvl_pct5 = y.rolling(1260, min_periods=750).rank(pct=True)
    reg = pd.Series("NORMAL", index=C.index)
    reg[ch20 >= 0.30] = "RISING"; reg[ch20 <= -0.30] = "FALLING"
    reg[(y >= 4.0) & (ch20.abs() < 0.15)] = "HIGH-STEADY"
    relhigh = (lvl_pct5 >= 0.8) & (ch20.abs() < 0.15)
    print("regime share of sessions 2010-2026:", reg[reg.index >= "2010"].value_counts(normalize=True).round(3).to_dict())
    print("HIGH-STEADY years:", sorted(reg[reg == "HIGH-STEADY"].index.year.unique().tolist()))
    # ---- events
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    house = ((C > H.shift(1).rolling(20).max()) & (adr >= 3) & elig).fillna(False)
    e20 = C.ewm(span=20, adjust=False).mean()
    hi52 = H.shift(1).rolling(252, min_periods=120).max(); lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100; piv = H.shift(1).rolling(15).max(); rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan); gap = O / C.shift(1) - 1; chg = C.pct_change(fill_method=None)
    stk = stack_run(C, adr=adr); off52 = (C / hi52 - 1) * 100
    brk = ((adr >= 3) & (range52 >= 17) & elig & (C >= piv) & (rvol >= 1.1) & (pos >= 0.5) & (stk >= 5) & (gap < 0.05)
           & (chg < 0.08) & (C.shift(1) < piv))
    prec = (brk & (adr >= 4) & (adr <= 7) & (off52 > -15) & (stk <= 40)).fillna(False)
    Cv, Lv, Ev = C.values, L.values, e20.values; N = len(Cv)

    def trade(i, j):
        entry = Cv[i, j]; stop = min(Lv[i, j], entry * 0.98)
        for k in range(i + 1, min(i + 61, N)):
            c = Cv[k, j]
            if not np.isfinite(c):
                continue
            if c < stop or c < Ev[k, j]:
                return (c / entry - 1) * 100
        k = min(i + 60, N - 1)
        return (Cv[k, j] / entry - 1) * 100 if k > i else np.nan

    def events(mask):
        ii, jj = np.where(mask.values)
        ok = (C.index[ii] >= "2010-01-01") & (ii < N - 2)
        ii, jj = ii[ok], jj[ok]
        out = pd.DataFrame(dict(date=C.index[ii], sym=np.array(keep)[jj], i=ii, j=jj, t=tcls.values[ii, jj]))
        out = out.dropna(subset=["t"])
        out["ret"] = [trade(i, j) for i, j in zip(out.i, out.j)]
        out["reg"] = reg.reindex(out.date).values
        out["relhigh"] = relhigh.reindex(out.date).values
        return out.dropna(subset=["ret"])

    def analyse(Ev_, label, regcol="reg"):
        d = Ev_[Ev_.t.isin([1, 3])].groupby(["date", "t"]).ret.agg(["mean", "size"]).unstack()
        d = d.dropna()
        g = pd.DataFrame(dict(gap=d[("mean", 3)] - d[("mean", 1)], w=d[("size", 1)] + d[("size", 3)]))
        g["reg"] = reg.reindex(g.index).values if regcol == "reg" else np.where(relhigh.reindex(g.index).values, "REL-HIGH", "OTHER")
        levels = ["RISING", "FALLING", "HIGH-STEADY"] if regcol == "reg" else ["REL-HIGH"]
        X = pd.DataFrame({k: (g.reg == k).astype(float) for k in levels}, index=g.index)
        X = sm.add_constant(X)
        fit = sm.WLS(g.gap, X, weights=g.w).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(g.index.to_period("M"))[0]})
        print(f"\n== {label}: dates with T1 & T3 breakouts {len(g)} ==")
        print(pd.DataFrame(dict(coef_pp=fit.params, t=fit.tvalues)).round(3).to_string())
        # episodes per regime: sign of the mean gap per episode
        res = {}
        for k in levels:
            gi = g[g.reg == k].sort_index()
            if gi.empty:
                continue
            pos_idx = C.index.get_indexer(gi.index)
            ep = np.concatenate([[0], np.cumsum(np.diff(pos_idx) > 20)])
            em = gi.gap.groupby(ep).mean() - fit.params["const"]
            res[k] = (len(em), (np.sign(em) == np.sign(fit.params[k])).mean())
            print(f"  {k}: {len(em)} episodes, share with the coefficient's sign {res[k][1]:.0%}")
        return fit, res

    HE = events(house)
    print(f"\nHOUSE breakouts 2010-26 with a rate-beta tercile: {len(HE):,}")
    tab = HE.groupby(["reg", "t"]).ret.agg(["mean", "size"]).unstack()
    print("mean % per trade by regime x rate-beta tercile (T1 long-duration / T3 beneficiaries):")
    print(tab.round(2).to_string())
    fit, res = analyse(HE, "PRIMARY: house pool, gap T3 - T1 on regime dummies")
    for k, name in (("RISING", "H1"), ("HIGH-STEADY", "H2")):
        t = fit.tvalues[k]; share = res.get(k, (0, 0))[1]
        ok = abs(t) >= 3.2 and share > 0.5
        print(f"{name} {k}: coef {fit.params[k]:+.2f}pp t {t:+.2f}, episode sign share {share:.0%} -> {'PASS' if ok else 'FAIL'}")
    analyse(HE, "SECONDARY: relative-high (top quintile of 5y range, steady) vs other", regcol="rel")
    PE = events(prec)
    print(f"\nPRECISION tier events: {len(PE):,}")
    print(PE.groupby(["reg", "t"]).ret.agg(["mean", "size"]).unstack().round(2).to_string())
    analyse(PE, "SECONDARY: precision tier")
    HE.drop(columns=["i", "j"]).to_csv("data/studies/logs/rates_regime_breakouts_events.csv", index=False)


if __name__ == "__main__":
    main()
