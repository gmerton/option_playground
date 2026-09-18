#!/usr/bin/env python3
"""
BCI (Alan Ellman) cash-secured puts, tested against holding the stock at the same delta.

Question (data/traderlion/setups/bci_covered_calls_cash_secured_puts.md §7): does selling OTM puts on names that
pass his PUBLIC filters beat (a) the same put with no filter and (b) holding the stock at the put's entry
delta on the same collateral? An ITM covered call is the same payoff (put-call parity), so this covers both.

Set before running:
  Universe   straddle pool (331 weekly-optionable names), Fridays 2018-01 -> 2026-02.
  Tenors     W = nearest 7 DTE (4-10), M = nearest 28 DTE (21-38). Hold to expiry, no management.
  Strikes    y  = his rule: OTM put whose yield premium/(K - premium) is nearest 0.75%/week or 3%/30 days
             30 = nearest 0.30 delta (house comparator)
  Fill       sell at mid - 25% of spread, $0.0065/share commission. Settle at intrinsic from the RAW underlying
             close on (or before) expiry. Assignment modelled as cash settlement.
  Return     on collateral K - premium:  csp = (premium - cost - max(K - S_T, 0)) / (K - premium)
  Benchmark  stock_d = |delta| x (S_T - S_0) / (K - premium): the stock held at the put's delta, same capital.
             excess  = csp - stock_d  -> the part that is premium, not direction.
  His filters (public ones only; industry rank / analyst rating / the BCI list are not reconstructable):
    trend  EMA20 > EMA100, EMA100 rising (vs 5 days ago), close >= EMA20
    macd   MACD(12,26,9) histogram > 0
    stoch  slow stochastic %K(14,3) > 80
    volume 10-day avg volume >= 80% of the prior 50-day avg ("holding up")
    rs     63-day return > SPY's
    ivband ATM (0.50 delta, M tenor) IV between 30% and 60%
    earn   no earnings date from entry through expiry (names without earnings coverage excluded from this arm)
  BCI = trend & macd & stoch & volume & rs & ivband & earn.
  Also: RSI(14) >= 70 (the seller's side of rsi_conditioning_study_2026-09-16.md section F).
  Stats: week-clustered t (entry week) for W; month-clustered for M (overlapping entries). Bar: |t| >= 3.

Usage:
  PYTHONPATH=src .venv/bin/python3 run_bci_csp_study.py > data/studies/bci_csp_study_2026-09-17.log
"""
from __future__ import annotations

import glob

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from lib.commons.rsi import wilder_rsi
from lib.mysql_lib import _get_engine

pd.set_option("display.width", 250)
COST = 0.0065

# ---------------------------------------------------------------- prices & filters
P = pd.read_parquet("data/cache/bci_csp/prices.parquet").sort_values(["ticker", "date"])
spy = P[P.ticker == "SPY"].set_index("date").close


def feats(g: pd.DataFrame) -> pd.DataFrame:
    c, h, l, v = g.close, g.high, g.low, g.volume
    e20, e100 = c.ewm(span=20, adjust=False).mean(), c.ewm(span=100, adjust=False).mean()
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    hist = macd - macd.ewm(span=9, adjust=False).mean()
    kfast = 100 * (c - l.rolling(14).min()) / (h.rolling(14).max() - l.rolling(14).min())
    kslow = kfast.rolling(3).mean()
    out = pd.DataFrame({
        "date": g.date, "raw_close": g.raw_close,
        "trend": (e20 > e100) & (e100 > e100.shift(5)) & (c >= e20),
        "macd": hist > 0,
        "stoch": kslow > 80,
        "volume": v.rolling(10).mean() >= 0.8 * v.shift(10).rolling(50).mean(),
        "ret63": c / c.shift(63) - 1,
        "rsi": wilder_rsi(c),
    })
    for k in ("trend", "macd", "stoch", "volume"):                            # warm-up -> unknown
        out[k] = out[k].astype("boolean")
        out.loc[out.index[:120], k] = pd.NA
    return out


F = pd.concat([feats(g).assign(ticker=t) for t, g in P.groupby("ticker")], ignore_index=True)
spy63 = (spy / spy.shift(63) - 1).rename("spy63")
F = F.merge(spy63, left_on="date", right_index=True, how="left")
F["rs"] = F.ret63 > F.spy63

# ---------------------------------------------------------------- chains
C = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob("data/cache/bci_csp/chain_*.parquet"))], ignore_index=True)
for col in ("trade_date", "expiry"):
    C[col] = pd.to_datetime(C[col])
atm = (C[C.is50 & (C.tenor == "M")][["ticker", "trade_date", "iv"]].rename(columns={"iv": "atm_iv"})
       .drop_duplicates(["ticker", "trade_date"]))
# price-series sanity: the ~0.50-delta weekly strike must sit within 10% of the raw close. Drops ticker-dates where
# the yfinance history belongs to a different company (COHR pre-2022 = old Coherent; HUT pre-2023) and $2-5 names
# whose strike grid is too coarse to check (0.55% of rows).
atmk = (C[C.is50 & (C.tenor == "W")][["ticker", "trade_date", "strike"]].rename(columns={"strike": "atm_k"})
        .drop_duplicates(["ticker", "trade_date"]))

ent = F.rename(columns={"date": "trade_date", "raw_close": "S0"})
# settlement: last raw close on or before expiry (handles holiday Thursdays)
settle = P[["ticker", "date", "raw_close"]].rename(columns={"raw_close": "ST"}).sort_values("date")

E = pd.read_sql("SELECT ticker, raw_date FROM earnings_report", _get_engine())
E["raw_date"] = pd.to_datetime(E.raw_date)
earn_names = set(E.ticker)


def build(tenor: str, rule: str) -> pd.DataFrame:
    flag = {"y": "isy", "30": "is30"}[rule]
    d = C[(C.tenor == tenor) & C[flag]].drop_duplicates(["ticker", "trade_date"]).copy()
    d = d.merge(ent, on=["ticker", "trade_date"], how="inner")
    d = pd.merge_asof(d.sort_values("expiry"), settle, left_on="expiry", right_on="date", by="ticker",
                      direction="backward").drop(columns="date")
    d = d.merge(atm, on=["ticker", "trade_date"], how="left").merge(atmk, on=["ticker", "trade_date"], how="left")
    d = d.dropna(subset=["S0", "ST"])
    d = d[(d.atm_k / d.S0 - 1).abs() <= 0.10]
    d = d[d.strike < d.S0]                                       # OTM puts only (his rule)
    d = d[(d.strike / d.S0).between(0.5, 1.0)]                    # guards against a mis-scaled price series
    coll = d.strike - d.sellpx
    d["csp"] = 100 * (d.sellpx - COST - np.maximum(d.strike - d.ST, 0)) / coll
    d["stock_d"] = 100 * d.delta.abs() * (d.ST - d.S0) / coll
    d["excess"] = d.csp - d.stock_d
    d["stock"] = 100 * (d.ST / d.S0 - 1)
    d["assigned"] = d.ST < d.strike
    d["ivband"] = d.atm_iv.between(0.30, 0.60)
    # earnings from entry through expiry
    w = d[["ticker", "trade_date", "expiry"]].merge(E, on="ticker")
    hit = w[(w.raw_date >= w.trade_date) & (w.raw_date <= w.expiry)][["ticker", "trade_date"]].drop_duplicates()
    d = d.merge(hit.assign(earn_in=True), on=["ticker", "trade_date"], how="left")
    d["earn_in"] = d.earn_in.fillna(False).astype(bool)
    d.loc[~d.ticker.isin(earn_names), "earn_in"] = np.nan
    d["earn_clear"] = d.earn_in == False                         # noqa: E712 (NaN -> False: unknown excluded)
    for k in ("trend", "macd", "stoch", "volume", "rs"):
        d[k] = d[k].astype("boolean")
    d["tech4"] = (d.trend & d.macd & d.stoch & d.volume).fillna(False).astype(bool)
    d["bci"] = (d.tech4 & d.rs.fillna(False) & d.ivband & d.earn_clear).astype(bool)
    d["rsi70"] = d.rsi >= 70
    d["week"] = d.trade_date.dt.to_period("W-FRI").astype(str)
    d["month"] = d.trade_date.dt.to_period("M").astype(str)
    d["tenor"], d["rule"] = tenor, rule
    return d


def stats(x: pd.DataFrame, cl: str) -> dict:
    if len(x) < 30:
        return dict(n=len(x))
    g = x.groupby(cl)
    def t(col):
        s = g[col].mean()
        return s.mean() / s.std() * np.sqrt(len(s)) if len(s) > 2 else np.nan
    q01 = x.csp.quantile(0.01)
    return dict(n=len(x), csp=x.csp.mean(), med=x.csp.median(), win=100 * (x.csp > 0).mean(),
                worst1pct=x.csp[x.csp <= q01].mean(), t_csp=t("csp"), stock_d=x.stock_d.mean(),
                excess=x.excess.mean(), t_excess=t("excess"), assigned=100 * x.assigned.mean(),
                delta=x.delta.abs().mean(), yld=100 * (x.sellpx / (x.strike - x.sellpx)).mean())


def contrast(x: pd.DataFrame, var: str, y: str, cl: str) -> str:
    z = x[list(dict.fromkeys([y, var, cl, "week"]))].copy()
    z[var] = z[var].map({True: 1.0, False: 0.0, 1: 1.0, 0: 0.0})
    z = z.dropna()
    z["g"] = pd.factorize(z[cl])[0]
    if z[var].nunique() < 2:
        return "n/a"
    m = smf.ols(f"{y} ~ {var}", z).fit(cov_type="cluster", cov_kwds={"groups": z["g"]})
    z["y_dm"] = z[y] - z.groupby("week")[y].transform("mean")
    z["v_dm"] = z[var] - z.groupby("week")[var].transform("mean")
    m2 = smf.ols("y_dm ~ v_dm - 1", z).fit(cov_type="cluster", cov_kwds={"groups": z["g"]})
    return (f"pooled {m.params[var]:+.2f} (t {m.tvalues[var]:+.2f}) | "
            f"within-week {m2.params['v_dm']:+.2f} (t {m2.tvalues['v_dm']:+.2f})")


CRASH = {"2020-02-14..03-20": ("2020-02-14", "2020-03-20"), "2022 (all)": ("2022-01-01", "2022-12-31"),
         "2025-03-28..04-11": ("2025-03-28", "2025-04-11")}

all_frames = []
for tenor in ("W", "M"):
    cl = "week" if tenor == "W" else "month"
    for rule in ("y", "30"):
        d = build(tenor, rule)
        all_frames.append(d)
        print(f"\n{'#'*100}\n# tenor {tenor} ({'~7' if tenor=='W' else '~28'} DTE)  strike rule {rule}  "
              f"| {len(d):,} trades, {d.ticker.nunique()} names, {d.trade_date.min().date()} -> {d.trade_date.max().date()}"
              f"  | t clustered by {cl}\n{'#'*100}")
        arms = {
            "ALL": d,
            "earnings in window": d[d.earn_in == True],                 # noqa: E712
            "earnings clear": d[d.earn_clear],
            "tech4 (trend+macd+stoch+vol)": d[d.tech4],
            "tech4 + rs": d[d.tech4 & d.rs.fillna(False).astype(bool)],
            "IV 30-60%": d[d.ivband],
            "BCI full (tech4+rs+IV+earn clear)": d[d.bci],
            "RSI >= 70": d[d.rsi70],
            "RSI >= 70 & earnings clear": d[d.rsi70 & d.earn_clear],
            "not BCI, earnings clear": d[~d.bci & d.earn_clear],
        }
        print(pd.DataFrame({k: stats(v, cl) for k, v in arms.items()}).T.round(2).to_string())
        print("\ncontrasts (y = csp return / y = excess over delta-matched stock):")
        for var, sub in [("earn_in", d[d.earn_in.notna()]), ("bci", d[d.earn_in.notna()]), ("rsi70", d),
                         ("tech4", d)]:
            print(f"  {var:8s} csp:    {contrast(sub, var, 'csp', cl)}")
            print(f"  {var:8s} excess: {contrast(sub, var, 'excess', cl)}")
        print("\nby year (mean csp %, mean excess %):")
        yr = d.assign(y=d.trade_date.dt.year)
        tab = pd.DataFrame({
            "ALL csp": yr.groupby("y").csp.mean(), "ALL excess": yr.groupby("y").excess.mean(),
            "BCI n": yr[yr.bci].groupby("y").size(), "BCI csp": yr[yr.bci].groupby("y").csp.mean(),
            "BCI excess": yr[yr.bci].groupby("y").excess.mean(),
            "clear csp": yr[yr.earn_clear].groupby("y").csp.mean(),
            "earn-in csp": yr[yr.earn_in == True].groupby("y").csp.mean()})   # noqa: E712
        print(tab.round(2).to_string())
        print("\ncrash windows (entries inside):")
        rows = {}
        for lab, (a, b) in CRASH.items():
            z = d[(d.trade_date >= a) & (d.trade_date <= b)]
            for arm, zz in (("ALL", z), ("BCI", z[z.bci])):
                rows[f"{lab} {arm}"] = dict(n=len(zz), csp=zz.csp.mean(), worst=zz.csp.min(),
                                            stock_d=zz.stock_d.mean(), excess=zz.excess.mean())
        print(pd.DataFrame(rows).T.round(2).to_string())
        # equal-weight weekly book (W only): what one week of 100% collateral looked like
        if tenor == "W":
            book = pd.DataFrame({arm: x.groupby("trade_date").csp.mean() for arm, x in
                                 (("ALL", d), ("BCI", d[d.bci]))})
            spyw = (spy.resample("W-FRI").last().pct_change() * 100).shift(-1).rename("SPY next wk")
            book = book.join(spyw, how="left")
            desc = {}
            for col in book:
                s = book[col].dropna() / 100
                s = s[s.index <= "2026-02-27"]
                eq = (1 + s).cumprod()
                desc[col] = dict(weeks=len(s), mean_wk=100 * s.mean(), sd_wk=100 * s.std(),
                                 worst_wk=100 * s.min(), cagr=100 * (eq.iloc[-1] ** (52 / len(s)) - 1),
                                 max_dd=100 * (eq / eq.cummax() - 1).min())
            print("\nequal-weight weekly book, 100% of collateral each week, compounded (W, this rule):")
            print(pd.DataFrame(desc).T.round(2).to_string())

pd.concat(all_frames, ignore_index=True).to_parquet("data/cache/bci_csp/trades.parquet", index=False)
