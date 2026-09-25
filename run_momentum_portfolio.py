#!/usr/bin/env python3
"""
Cross-sectional 12-1 MOMENTUM as a stand-alone stock-buying strategy (pre-registered 2026-09-25, before any run;
Gabe: "a bread-and-butter strategy for buying stocks" -- option C, the durable academic baseline).

WHY NEW. The ledger tested momentum only as a FILTER inside the precision tier (Novy-Marx 12->7, NULL, 2026-09-24) and
as a SECTOR spread (12-1 K3, NULL on return, 2026-09-24). A long-only portfolio of the strongest STOCKS has never been
run. Jegadeesh-Titman (1993) and a century of out-of-sample replications make it the honest baseline every setup
should beat; the known risk is the momentum CRASH after a bear-market low (2009, 2020-04).

DATA
  PRIMARY  silver.chain_spot_daily via run_dip_survivorship.pull()/adjust_and_clean(): closes for 10.8k optionable
           tickers INCLUDING DELISTED, split-adjusted, series cut at unexplained >45% jumps. Momentum needs only
           closes, so this is the survivorship-free test. Liquidity: 50-session mean option volume >= 1,000 contracts
           and price >= $5 at formation. A name whose series ends inside the holding month exits at its last close.
  SECONDARY liquid_panel_2009 (adjusted OHLCV, today's liquid names = survivor-biased), harness eligibility
           (ADDV >= $50M, px >= $5).
  METHOD CHECK (declared now, not bar-bearing): chain-spot top-decile monthly returns restricted to panel names vs the
           panel's own top-decile returns -- correlation should be >= 0.8, else the chain-spot run is uninterpretable.
DESIGN   formation at each month-end t: score = close(t - 21 sessions) / close(t - 252 sessions) - 1 (12-1: skip the
           most recent month, the short-term reversal window). Needs 252 sessions of history. Long the TOP DECILE
           of eligible names, equal weight, hold one month (close t -> close of the next month-end), rebalance
           monthly. Costs: 10 bp per side on the turnover (share of the portfolio replaced).
BENCHMARK (declared now) the equal-weight portfolio of ALL eligible names that month (same universe, same costs on
           its own turnover) -- momentum must beat owning everything, not zero. Also reported: SPY, and the
           regression alpha / beta of the top decile on the EW universe.
CELLS    PRIMARY = top decile, 12-1, on chain_spot. Plus top quintile 12-1 and top decile 6-1. M = 3 -> Sidak |t| >= 2.39;
           the house |t| >= 3 GOVERNS (Newey-West lag 3 on monthly excess), both halves (2018-01) positive, a majority
           of years positive.
REPORTED descriptive: max drawdown of the portfolio and of the excess, the worst 5 months (the crash check), per-year
           excess, and an exploratory "momentum + trend" cell (top decile only while SPY > its 200-day, else cash) --
           exploratory because the trend filter has already been tested elsewhere (index_filter NULL for breakouts).
READ     a PASS makes this the baseline stock sleeve: boring, monthly, low decision load. A NULL on the survivorship-free
           series with a pass on the panel means the panel result is survivorship.
Window   2011-01 -> 2026-01 formations (chain_spot starts 2010; 12 months of history needed; ends 2026-02).

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_momentum_portfolio.py
       (log -> data/studies/logs/momentum_portfolio.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/momentum_portfolio.log"
START, END, SPLIT = "2011-01-01", "2026-01-31", "2018-01-01"
COST = 0.0010
OPTVOL_MIN, PX_MIN = 1000, 5.0


def nw_t(x: pd.Series, lag: int = 3) -> float:
    x = x.dropna().values; n = len(x)
    if n < 10:
        return np.nan
    e = x - x.mean(); g0 = (e @ e) / n
    s = g0 + 2 * sum((1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n for k in range(1, lag + 1))
    return float(x.mean() / np.sqrt(s / n))


def month_ends(idx: pd.DatetimeIndex) -> list[int]:
    s = pd.Series(np.arange(len(idx)), index=idx)
    return list(s.groupby(idx.to_period("M")).max().values)


def portfolio(C: pd.DataFrame, elig: pd.DataFrame, lookback: int, skip: int, top: float) -> pd.DataFrame:
    """Monthly returns of the top-`top` momentum bucket and of the EW universe, net of turnover costs."""
    idx = C.index; Cv = C.values; E = elig.values
    last_valid = np.array([np.flatnonzero(np.isfinite(Cv[:, j])).max() if np.isfinite(Cv[:, j]).any() else -1
                           for j in range(Cv.shape[1])])
    me = [i for i in month_ends(idx) if pd.Timestamp(START) <= idx[i] <= pd.Timestamp(END)]
    rows, prev_mom, prev_ew = [], set(), set()
    for a, b in zip(me[:-1], me[1:]):
        if a - lookback < 0:
            continue
        score = Cv[a - skip] / Cv[a - lookback] - 1
        ok = E[a] & np.isfinite(score) & np.isfinite(Cv[a])
        if ok.sum() < 50:
            continue
        names = np.flatnonzero(ok)
        cut = np.nanquantile(score[names], 1 - top)
        mom = names[score[names] >= cut]
        exit_i = np.minimum(b, last_valid[names])                     # delisted inside the month -> last close
        r_all = Cv[exit_i, names] / Cv[a, names] - 1
        r = pd.Series(r_all, index=names).replace([np.inf, -np.inf], np.nan)
        rm, rew = r.reindex(mom).mean(), r.mean()
        smom, sew = set(C.columns[mom]), set(C.columns[names])
        to_m = 1 - len(smom & prev_mom) / max(len(smom), 1)
        to_e = 1 - len(sew & prev_ew) / max(len(sew), 1)
        rows.append(dict(month=idx[b].to_period("M"), mom=rm - 2 * COST * to_m, ew=rew - 2 * COST * to_e,
                         n_mom=len(mom), n_univ=len(names), turnover=to_m))
        prev_mom, prev_ew = smom, sew
    return pd.DataFrame(rows).set_index("month")


def describe(P: pd.DataFrame, label: str, spy_m: pd.Series, out: list[str]) -> dict:
    x = (P.mom - P.ew) * 100
    h = x.index < pd.Period(SPLIT, "M")
    yr = x.groupby(x.index.year).sum()
    beta = np.cov(P.mom, P.ew)[0, 1] / P.ew.var()
    alpha = (P.mom - beta * P.ew) * 100
    cum = (1 + P.mom).cumprod(); dd = (1 - cum / cum.cummax()).max() * 100
    cx = x.cumsum(); ddx = (cx.cummax() - cx).max()
    s = spy_m.reindex(P.index) * 100
    res = dict(cell=label, months=len(x), mom_mo=100 * P.mom.mean(), ew_mo=100 * P.ew.mean(), spy_mo=s.mean(),
               excess=x.mean(), t_nw=nw_t(x), h1=x[h].mean(), h2=x[~h].mean(), yrs_pos=f"{(yr > 0).sum()}/{len(yr)}",
               beta_ew=beta, alpha_mo=alpha.mean(), t_alpha=nw_t(alpha), maxDD=dd, excess_maxDD=ddx,
               turnover=P.turnover.mean(), n_mom=P.n_mom.mean(), n_univ=P.n_univ.mean())
    res["PASS"] = bool(abs(res["t_nw"]) >= 3 and res["excess"] > 0 and res["h1"] > 0 and res["h2"] > 0
                       and (yr > 0).sum() > len(yr) / 2)
    out.append(f"\n## {label}: {len(x)} months, ~{P.n_mom.mean():.0f} of {P.n_univ.mean():.0f} names, turnover {P.turnover.mean():.0%}/mo")
    out.append(f"  momentum {100*P.mom.mean():+.2f}%/mo vs EW universe {100*P.ew.mean():+.2f}% vs SPY {s.mean():+.2f}% | "
               f"excess {x.mean():+.2f}pp t_NW {res['t_nw']:+.2f} | halves {res['h1']:+.2f} / {res['h2']:+.2f} | "
               f"years + {res['yrs_pos']} | beta on EW {beta:.2f}, alpha {alpha.mean():+.2f}pp t {res['t_alpha']:+.2f}")
    out.append(f"  max drawdown: portfolio {dd:.1f}%, excess {ddx:.1f}pp | worst 5 excess months: "
               + ", ".join(f"{m}: {v:+.1f}" for m, v in x.nsmallest(5).items()))
    out.append("  excess by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in yr.items()) + f"  -> {'PASS' if res['PASS'] else 'fail'}")
    return res


def main():
    import run_dip_survivorship as DS
    out = ["# 12-1 momentum portfolio (pre-registration in the docstring)"]
    d = DS.pull()
    C, V = DS.adjust_and_clean(d)
    liq = ((V.rolling(50, min_periods=30).mean() >= OPTVOL_MIN) & (C >= PX_MIN)).fillna(False)
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet"); raw["date"] = pd.to_datetime(raw.date)
    spy = raw[raw.ticker == "SPY"].set_index("date").close.sort_index()
    spy_m = spy.groupby(spy.index.to_period("M")).last().pct_change()
    surv = set(raw.ticker.unique())
    R = []
    R.append(describe(portfolio(C, liq, 252, 21, 0.10), "PRIMARY chain_spot (incl. delisted) top decile 12-1", spy_m, out))
    R.append(describe(portfolio(C, liq, 252, 21, 0.20), "chain_spot top quintile 12-1", spy_m, out))
    R.append(describe(portfolio(C, liq, 126, 21, 0.10), "chain_spot top decile 6-1", spy_m, out))
    # secondary: survivor panel
    from lib.regime.trailing import Panel, liquidity_mask
    pr = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(pr)
    elig_p = (liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()).fillna(False)
    Pp = portfolio(p.close, elig_p, 252, 21, 0.10)
    R.append(describe(Pp, "SECONDARY survivor panel top decile 12-1", spy_m, out))
    # method check: chain_spot restricted to panel names vs the panel run
    cs_surv = C.loc[:, [c for c in C.columns if c in surv]]
    Pc = portfolio(cs_surv, liq.loc[:, cs_surv.columns], 252, 21, 0.10)
    j = Pc.join(Pp, lsuffix="_cs", rsuffix="_panel", how="inner")
    rho = j.mom_cs.corr(j.mom_panel)
    out.append(f"\n## METHOD CHECK: chain_spot top decile on panel names vs the panel's own: monthly corr {rho:.2f} over {len(j)} months "
               f"({'OK' if rho >= 0.8 else 'FAILED -> the chain_spot run is uninterpretable'})")
    # exploratory: momentum + SPY 200d trend
    P0 = portfolio(C, liq, 252, 21, 0.10)
    tr = (spy > spy.rolling(200).mean()).groupby(spy.index.to_period("M")).last().shift(1)
    on = tr.reindex(P0.index).fillna(False).astype(bool)
    P1 = P0.copy(); P1.loc[~on, "mom"] = 0.0
    out.append(f"\n## [exploratory] momentum only while SPY > 200d at formation: invested {on.mean():.0%} of months")
    describe(P1, "EXPLORATORY chain_spot top decile 12-1 + SPY 200d trend", spy_m, out)
    D = pd.DataFrame(R)
    out.append("\n" + D.round(3).to_string(index=False))
    prim = D.iloc[0]
    out.append(f"\nVERDICT (PRIMARY): {'PASS' if prim.PASS and rho >= 0.8 else 'fail'} -- excess {prim.excess:+.2f}pp/mo t_NW {prim.t_nw:+.2f}")
    D.to_csv(REPO / "data/studies/momentum_portfolio_2026-09-25.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
