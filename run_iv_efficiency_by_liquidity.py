#!/usr/bin/env python3
"""Is mid IV mispriced in illiquid options? HAR-gap efficiency beta by option-liquidity decile (2026-09-29).

PRE-REGISTERED: data/studies/iv_efficiency_by_liquidity_2026-09-29.md (committed e4149be before any pull).
Unit ticker x month-end 2010-01 -> 2026-02. gap = log IV - log F (out-of-sample HAR forecast of next-21-session RV);
outcome = log RV_fwd - log F; beta per option-volume decile (within month). PRIMARY: beta(D10) - beta(D1) > 0, |t| >= 3,
month-clustered, both halves (2012-2018 / 2019-2026). RV from REAL closes (liquid + small-cap panels); chain-spot RV
is a robustness row only.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_iv_efficiency_by_liquidity.py \
         > data/studies/iv_efficiency_by_liquidity_2026-09-29.log
"""
from __future__ import annotations

from pathlib import Path

import awswrangler as wr
import numpy as np
import pandas as pd
import statsmodels.api as sm

from lib.constants import S3_OUTPUT, WORKGROUP

REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/iv_efficiency"
CACHE.mkdir(parents=True, exist_ok=True)
START, END, H, SPLIT = "2010-01-01", "2026-02-27", 21, "2019-01-01"
pd.set_option("display.width", 220)


def q(sql):
    return wr.athena.read_sql_query(sql, database="silver", workgroup=WORKGROUP, data_source="AwsDataCatalog",
                                    s3_output=S3_OUTPUT, ctas_approach=False)


def closes() -> pd.DataFrame:
    frames = []
    for f in ("liquid_panel_2009", "smallcap_panel_2009"):
        r = pd.read_parquet(REPO / f"data/cache/{f}.parquet", columns=["date", "ticker", "close"])
        frames.append(r)
    r = pd.concat(frames).drop_duplicates(["ticker", "date"], keep="first")
    r["date"] = pd.to_datetime(r.date)
    r = r[~r.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    return r.pivot(index="date", columns="ticker", values="close").sort_index()


def pull(tickers, month_ends):
    fi, ff = CACHE / "iv_month_end.parquet", CACHE / "flow_month_end.parquet"
    tl = ",".join(f"'{t}'" for t in tickers)
    dl = ",".join(f"DATE '{d.date()}'" for d in month_ends)
    if not fi.exists():
        iv = q(f"SELECT ticker, trade_date, call50_iv FROM silver.options_iv_daily WHERE ticker IN ({tl}) "
               f"AND trade_date IN ({dl}) AND call50_iv IS NOT NULL")
        iv.to_parquet(fi, index=False)
    if not ff.exists():
        fl = q(f"""WITH x AS (
                 SELECT ticker, trade_date,
                        AVG(COALESCE(call_vol, 0) + COALESCE(put_vol, 0)) OVER (PARTITION BY ticker ORDER BY trade_date
                            ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) AS vol21
                 FROM silver.options_flow_daily WHERE ticker IN ({tl})
                   AND trade_date BETWEEN DATE '2009-11-01' AND DATE '{END}')
               SELECT ticker, trade_date, vol21 FROM x WHERE trade_date IN ({dl})""")
        fl.to_parquet(ff, index=False)
    iv, fl = pd.read_parquet(fi), pd.read_parquet(ff)
    for d in (iv, fl):
        d["trade_date"] = pd.to_datetime(d.trade_date)
    return iv, fl


def rv_frame(C: pd.DataFrame, month_ends) -> pd.DataFrame:
    lr = np.log(C / C.shift(1))
    sq = lr ** 2
    ann = lambda s: np.sqrt(252 * s)
    past = {k: ann(sq.rolling(k, min_periods=max(1, int(k * .8))).mean()) for k in (1, 5, 21, 63)}
    fwd = ann(sq[::-1].rolling(H, min_periods=18).mean()[::-1].shift(-1))       # sessions t+1 .. t+21
    rows = []
    idx = C.index
    for d in month_ends:
        if d not in idx:
            continue
        rec = pd.DataFrame({"rv_fwd": fwd.loc[d], **{f"rv{k}": past[k].loc[d] for k in past}, "px": C.loc[d]})
        rec["date"] = d; rec["ticker"] = rec.index
        rows.append(rec.reset_index(drop=True))
    return pd.concat(rows, ignore_index=True)


def har_oos(D: pd.DataFrame) -> pd.Series:
    X = np.log(D[["rv1", "rv5", "rv21", "rv63"]].clip(lower=1e-3))
    y = np.log(D.rv_fwd.clip(lower=1e-3))
    F = pd.Series(np.nan, index=D.index)
    for yr in range(2012, 2027):
        tr = D.date < pd.Timestamp(f"{yr - 1}-12-01")                # target windows end before the year starts
        te = D.date.dt.year == yr
        if tr.sum() < 1000 or te.sum() == 0:
            continue
        f = sm.OLS(y[tr], sm.add_constant(X[tr])).fit()
        F[te] = f.predict(sm.add_constant(X[te], has_constant="add"))
    return F


def analyse(D: pd.DataFrame, label: str) -> list[str]:
    out = [f"\n=== {label} ===", f"rows {len(D):,}, tickers {D.ticker.nunique():,}, months {D.date.nunique()}"]
    D = D.copy()
    D["gap"] = np.log(D.iv) - D.F
    D["outc"] = np.log(D.rv_fwd) - D.F
    D["mcode"] = pd.factorize(D.date)[0]
    rows = []
    for dec, g in D.groupby("dec"):
        f = sm.OLS(g.outc, sm.add_constant(g.gap)).fit(cov_type="cluster", cov_kwds={"groups": g.mcode})
        r2f = np.corrcoef(g.F, np.log(g.rv_fwd))[0, 1] ** 2
        f2 = sm.OLS(np.log(g.rv_fwd), sm.add_constant(pd.DataFrame({"F": g.F, "iv": np.log(g.iv)}))).fit()
        qg = pd.qcut(g.gap.rank(method="first"), 5, labels=False)
        rmi = 100 * (g.rv_fwd - g.iv)
        rows.append(dict(decile=dec + 1, n=len(g), names=g.ticker.nunique(), med_optvol=g.vol21.median(),
                         beta=f.params.gap, beta_se=f.bse.gap, bias_log_iv_rv=np.log(g.iv / g.rv_fwd).mean(),
                         r2_F=r2f, r2_F_iv=f2.rsquared, rv_minus_iv_Q5_Q1=rmi[qg == 4].mean() - rmi[qg == 0].mean()))
    T = pd.DataFrame(rows)
    out.append(T.round(3).to_string(index=False))
    P = D[D.dec.isin([0, 9])].copy()
    P["D1"] = (P.dec == 0).astype(float); P["D1gap"] = P.D1 * P.gap

    def prim(x):
        f = sm.OLS(x.outc, sm.add_constant(x[["gap", "D1", "D1gap"]])).fit(cov_type="cluster", cov_kwds={"groups": x.mcode})
        return -f.params.D1gap, -f.tvalues.D1gap
    d, t = prim(P)
    h1, t1 = prim(P[P.date < SPLIT]); h2, t2 = prim(P[P.date >= SPLIT])
    ok = d > 0 and abs(t) >= 3 and h1 > 0 and h2 > 0
    out.append(f"PRIMARY beta(D10) - beta(D1) = {d:+.3f} (t {t:+.2f}); halves {h1:+.3f} (t {t1:+.2f}) / {h2:+.3f} (t {t2:+.2f}) "
               f"-> {'PASS: IV less efficient in illiquid options' if ok else 'FAIL'}")
    return out


def main():
    C = closes()
    days = pd.Series(C.index[(C.index >= START) & (C.index <= END)])
    me = days.groupby(days.dt.to_period("M")).max()
    month_ends = pd.DatetimeIndex(me.values)
    iv, fl = pull(sorted(C.columns), month_ends)
    R = rv_frame(C, month_ends)
    D = R.merge(iv.rename(columns={"trade_date": "date", "call50_iv": "iv"}), on=["ticker", "date"]) \
         .merge(fl.rename(columns={"trade_date": "date"}), on=["ticker", "date"])
    D = D[(D.px >= 5) & D.iv.between(0.03, 5) & (D.rv_fwd > 0) & (D.vol21 > 0)].dropna(subset=["rv_fwd", "rv5", "rv21", "rv63"])
    D["F"] = har_oos(D)
    D = D.dropna(subset=["F"])
    D["dec"] = D.groupby("date").vol21.transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=False))
    lines = [f"# IV efficiency by option liquidity (pre-registration in the md). month-ends {len(month_ends)}"]
    lines += analyse(D, "PRIMARY: RV from real closes (liquid + small-cap panels)")
    # robustness: chain-spot RV, same ticker-months
    import run_dip_survivorship as ds
    Cc, _ = ds.adjust_and_clean(ds.pull())
    Rc = rv_frame(Cc, month_ends)
    Dc = Rc.merge(D[["ticker", "date", "iv", "vol21", "dec"]], on=["ticker", "date"])
    Dc = Dc[(Dc.rv_fwd > 0)].dropna(subset=["rv_fwd", "rv5", "rv21", "rv63"])
    Dc["F"] = har_oos(Dc); Dc = Dc.dropna(subset=["F"])
    lines += analyse(Dc, "ROBUSTNESS: RV from chain-spot closes (noisier for illiquid options)")
    D.to_parquet(CACHE / "panel.parquet", index=False)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
