#!/usr/bin/env python3
"""Short interest (days to cover) as a standalone single-name SHORT (2026-09-29).

PRE-REGISTERED: data/studies/short_interest_short_2026-09-29.md (committed 9304781 before this ran).
Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_short_interest_short.py \
         > data/studies/short_interest_short_2026-09-29.log
"""
from __future__ import annotations

from math import ceil

import numpy as np
import pandas as pd
import statsmodels.api as sm

from lib.regime.trailing import Panel, liquidity_mask

REPO_SI = "data/cache/short_interest.parquet"
LAG_BD, COST, SPLIT = 8, 0.0010, pd.Timestamp("2022-01-01")
HS = (10, 20, 60)


def nw_t(x: pd.Series, lags: int) -> float:
    x = x.dropna()
    if len(x) < 10:
        return np.nan
    f = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(f.tvalues[0])


def load_si() -> pd.DataFrame:
    si = pd.read_parquet(REPO_SI)
    si = si[(si.days_to_cover > 0) & (si.days_to_cover < 999) & (si.avg_daily_volume > 0)].copy()
    si["settlement_date"] = pd.to_datetime(si.settlement_date)
    si = si.sort_values(["ticker", "settlement_date"])
    si["ratio"] = si.days_to_cover / si.groupby("ticker").days_to_cover.shift(1)
    si["pub"] = si.settlement_date + pd.offsets.BDay(LAG_BD)
    return si


def build(C: pd.DataFrame, elig: pd.DataFrame, vol_proxy: pd.DataFrame, si: pd.DataFrame) -> pd.DataFrame:
    """One row per (formation, name) for eligible names with an SI record: fwd returns, cell, signal flags."""
    idx = C.index
    Cf = C.ffill()                                             # a series that ends exits at its last close
    r20 = C / C.shift(20) - 1
    rows = []
    for sd, g in si.groupby("settlement_date"):
        if sd < pd.Timestamp("2017-12-01") or sd > pd.Timestamp("2026-07-15"):
            continue
        pos = idx.searchsorted(g.pub.iloc[0])
        if pos + 60 >= len(idx) and pos + 20 >= len(idx):
            continue
        t0 = idx[pos]
        if t0 > pd.Timestamp("2026-07-31"):
            continue
        g = g[g.ticker.isin(C.columns)]
        g = g[elig.loc[t0, g.ticker].fillna(False).values & np.isfinite(C.loc[t0, g.ticker].values)]
        if len(g) < 100:
            continue
        d = pd.DataFrame({"ticker": g.ticker.values, "dtc": g.days_to_cover.values, "ratio": g.ratio.values})
        d["date"] = t0
        d["high"] = d.dtc >= d.dtc.quantile(0.9)
        d["rising"] = d.ratio >= d.ratio.quantile(0.9)
        e = C.loc[t0, d.ticker].values
        for h in HS:
            j = min(pos + h, len(idx) - 1)
            d[f"f{h}"] = Cf.iloc[j][d.ticker].values / e - 1 if pos + h < len(idx) else np.nan
        d["r20"] = r20.loc[t0, d.ticker].values
        d["vp"] = vol_proxy.loc[t0, d.ticker].values
        d["cell"] = (pd.qcut(d.r20.rank(method="first"), 5, labels=False).astype(str) + "_" +
                     pd.qcut(d.vp.rank(method="first"), 3, labels=False).astype(str))
        rows.append(d)
    return pd.concat(rows, ignore_index=True)


def score(D: pd.DataFrame, flag: str, h: int, borrow: float) -> dict:
    col = f"f{h}"
    X = D.dropna(subset=[col]).copy()
    ctl = X[~X[flag]].groupby(["date", "cell"])[col].mean().rename("ctl")
    S = X[X[flag]].join(ctl, on=["date", "cell"]).dropna(subset=["ctl"])
    S["ex"] = S[col] - S.ctl
    S["short_pnl"] = -S[col] - 2 * COST - borrow * h / 252
    g = S.groupby("date")[["ex", "short_pnl"]].mean()
    lags = max(1, ceil(h / 10))
    hmask = g.index < SPLIT
    yr = g.ex.groupby(g.index.year).mean()
    return dict(signal=flag, h=h, borrow=borrow, n=len(S), formations=len(g), excess_pct=100 * g.ex.mean(), t=nw_t(g.ex, lags),
                h1=100 * g.ex[hmask].mean(), h2=100 * g.ex[~hmask].mean(), yrs_neg=f"{int((yr < 0).sum())}/{len(yr)}",
                yrs_neg_share=(yr < 0).mean(), short_pnl_pct=100 * g.short_pnl.mean(), t_short=nw_t(g.short_pnl, lags))


def main():
    si = load_si()
    raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    C, H, L = p.close, p.high, p.low
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    adr = (H / L - 1).shift(1).rolling(20).mean()
    D = build(C, elig, adr, si)
    D["high_rising"] = D.high & D.rising
    out = [f"# Short interest short (pre-registration in the md). formations {D.date.nunique()}, name-dates {len(D):,}"]
    R = pd.DataFrame([score(D, f, h, b) for f in ("high", "rising", "high_rising") for h in HS for b in ((0.05, 0.01) if f == "high" and h == 20 else (0.05,))])
    out.append(R.round(3).to_string(index=False))
    p0 = R[(R.signal == "high") & (R.h == 20) & (R.borrow == 0.05)].iloc[0]
    core = p0.excess_pct < 0 and abs(p0.t) >= 3 and p0.h1 < 0 and p0.h2 < 0 and p0.yrs_neg_share > 0.5
    verdict = "PASS (short)" if core and p0.short_pnl_pct > 0 else ("VETO candidate (lags but does not fall)" if core else "FAIL")
    out.append(f"\nPRIMARY HIGH +20, 5% borrow: excess {p0.excess_pct:+.2f}% t {p0.t:+.2f}, halves {p0.h1:+.2f}/{p0.h2:+.2f}, "
               f"yrs neg {p0.yrs_neg}, short P&L {p0.short_pnl_pct:+.2f}% -> {verdict}")
    # survivorship check on chain-spot closes (incl. delisted)
    import run_dip_survivorship as ds
    Cc, V = ds.adjust_and_clean(ds.pull())
    k = ds.k_scale()
    adrp = Cc.pct_change(fill_method=None).abs().shift(1).rolling(20, min_periods=15).mean() * k
    liq = (V.rolling(50, min_periods=30).mean() >= 1000) & (Cc >= 5)
    Dc = build(Cc, liq, adrp, si)
    surv = set(raw.ticker.unique())
    Dc["surv"] = Dc.ticker.isin(surv)
    rows = []
    for lab, sub in (("chain ALL", Dc), ("chain SURV", Dc[Dc.surv]), ("chain NONSURV", Dc[~Dc.surv])):
        r = score(sub, "high", 20, 0.05); r["signal"] = lab; rows.append(r)
    out.append("\n== survivorship check: HIGH +20, 5% borrow, chain-spot closes (DTC decile re-ranked within each group universe: no) ==")
    out.append(pd.DataFrame(rows).round(3).to_string(index=False))
    D.to_csv("data/studies/logs/short_interest_short_names.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    main()
