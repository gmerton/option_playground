#!/usr/bin/env python3
"""
STRESS BUCKET HEAD-TO-HEAD: the book's 20-DTE 0.25/0.15 SPY bull put vs the 45-DTE 12-delta naked SPY put, on the SAME
certified-regime entries (pre-registered 2026-09-28, before the run; Gabe: "run 10, the stress bucket head-to-head").

WHY. The index put sale in the bearish-high-IV regime is the book's one certified trade (20-DTE spread t 6.07). On
2026-09-26 the always-on test showed the same regime edge in a 45-DTE 12Δ naked put (+3.38% of Reg-T margin per trade,
t 11.3, 32/32 stress episodes positive). Same bet, two structures: which one to trade when the regime fires?

ENTRIES  the 122 regime Fridays from always_on_index_put_2026-09-26.csv (cert == True: SPY close < its 50-day MA AND
         VIX close >= 20; weekly last session; 2010-01 -> 2026-01).
ARM B    45-DTE put nearest -0.12Δ; 50% take at the real closing cost, else close at the first session with DTE <= 21;
         settle at intrinsic if no quote. Results taken as-is from that CSV (pnlA column), nothing re-fit.
ARM A    the book's spec (run_tierab_significance.py / the SPY Bearish_HighIV cell): expiry nearest 20 DTE (14-28), short
         put nearest -0.25Δ, long put nearest -0.15Δ below it; 50% take at the real closing cost; NO stop; else hold to
         expiry, settled at intrinsic on the raw spot (chain_spot_daily). Pulled fresh from silver.options_daily_v3.
FILLS    house model on every leg: open at mid -/+ 25% of the quoted spread -/+ $0.0065/share; close at mid +/- 25%.
CAPITAL  (declared) what the broker ties up: A = max loss = (width - credit) x 100; B = Reg-T naked margin
         (0.20 x spot - OTM amount, floored at 0.10 x strike, + premium) x 100. SPAN on /ES is ~5x smaller for B:
         reported as a sensitivity, never as the primary.
PRIMARY  paired by entry date: ROC_A - ROC_B (net P&L / capital, % per trade), t on entry-month cluster means.
         BAR: a structure is PREFERRED only if |t| >= 3 with both halves (split 2018-01) the same sign. Otherwise the
         two are EQUIVALENT on return and the choice is a risk/capital preference, reported via the secondaries.
SECONDARY  return per capital-day (capital x days held, annualised), win rate, worst trade (% of capital and $ per
         1 contract), CVaR 5%, the 2020-02/03 and 2022 entries explicitly, per year, episode-level paired t
         (32 episodes, as in the parent).
PRIOR    B earns more per Reg-T dollar but carries an uncapped tail; A's tail is capped at the width. Expect
         EQUIVALENT on return after capital normalisation, with the choice made on tail and capital efficiency.
Local orchestration of ~16 small Athena queries (entry chains + paths for the 122 dates), cached to
data/cache/stress_h2h/.

Run: AWS_PROFILE=clarinut-gmerton AWS_DEFAULT_REGION=us-west-2 PYTHONPATH=src:. .venv/bin/python3 run_stress_bucket_h2h.py
     (log -> data/studies/logs/stress_bucket_h2h.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.athena_lib import athena
from run_always_on_index_put import spy_raw

REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/stress_h2h"
LOG = REPO / "data/studies/logs/stress_bucket_h2h.log"
SLIP, COMM, TAKE, SPLIT = 0.25, 0.0065, 0.50, "2018-01-01"


def log(m):
    print(m, file=sys.stderr, flush=True)


def pull_entries(days) -> pd.DataFrame:
    out = []
    for y in sorted({d.year for d in days}):
        f = CACHE / f"entry_{y}.parquet"
        if not f.exists():
            dl = ",".join(f"DATE '{d.date()}'" for d in days if d.year == y)
            log(f"  entry chains {y}")
            athena(f"""SELECT trade_date, expiry, strike, bid, ask, delta FROM options_daily_v3
                       WHERE ticker = 'SPY' AND upper(substr(cp,1,1)) = 'P' AND trade_date IN ({dl})
                         AND date_diff('day', trade_date, expiry) BETWEEN 14 AND 28
                         AND delta BETWEEN -0.40 AND -0.05 AND bid > 0""").to_parquet(f, index=False)
        out.append(pd.read_parquet(f))
    d = pd.concat(out, ignore_index=True)
    d["trade_date"], d["expiry"] = pd.to_datetime(d.trade_date), pd.to_datetime(d.expiry)
    return d


def choose(ch: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for d, g in ch.groupby("trade_date"):
        g = g.assign(gap=((g.expiry - g.trade_date).dt.days - 20).abs())
        g = g[g.gap == g.gap.min()]; g = g[g.expiry == g.expiry.min()]
        s = g.iloc[(g.delta + 0.25).abs().argsort()[:1]].iloc[0]
        lg = g[g.strike < s.strike]
        if lg.empty:
            continue
        l = lg.iloc[(lg.delta + 0.15).abs().argsort()[:1]].iloc[0]
        rows.append(dict(trade_date=d, expiry=s.expiry, ks=s.strike, kl=l.strike, sb=s.bid, sa=s.ask, lb=l.bid, la=l.ask,
                         ds=s.delta, dl=l.delta))
    return pd.DataFrame(rows)


def pull_paths(T: pd.DataFrame) -> pd.DataFrame:
    out = []
    T = T.assign(y=T.trade_date.dt.year)
    for y, g in T.groupby("y"):
        f = CACHE / f"paths_{y}.parquet"
        if not f.exists():
            el = ",".join(f"DATE '{e.date()}'" for e in sorted(g.expiry.unique()))
            kl = ",".join(f"{k:g}" for k in sorted(set(g.ks) | set(g.kl)))
            log(f"  paths {y} ({len(g)} spreads)")
            athena(f"""SELECT trade_date, expiry, strike, bid, ask FROM options_daily_v3
                       WHERE ticker = 'SPY' AND upper(substr(cp,1,1)) = 'P' AND expiry IN ({el}) AND strike IN ({kl})
                         AND trade_date BETWEEN DATE '{g.trade_date.min().date()}' AND DATE '{g.expiry.max().date()}'""").to_parquet(f, index=False)
        out.append(pd.read_parquet(f))
    d = pd.concat(out, ignore_index=True)
    d["trade_date"], d["expiry"] = pd.to_datetime(d.trade_date), pd.to_datetime(d.expiry)
    return d.drop_duplicates(["trade_date", "expiry", "strike"])


def sim_A(T, Q, spot) -> pd.DataFrame:
    Q = Q.set_index(["expiry", "strike"]).sort_index()
    rows = []
    for r in T.itertuples():
        smid, lmid = (r.sb + r.sa) / 2, (r.lb + r.la) / 2
        credit = (smid - SLIP * (r.sa - r.sb) - COMM) - (lmid + SLIP * (r.la - r.lb) + COMM)
        width = r.ks - r.kl
        if credit <= 0 or width <= credit:
            continue
        sT = spot.loc[:r.expiry]
        if len(sT) == 0 or sT.index[-1] < r.expiry - pd.Timedelta(days=4):
            continue
        S_T = float(sT.iloc[-1])
        settle = max(r.ks - S_T, 0) - max(r.kl - S_T, 0)
        try:
            ps = Q.loc[(r.expiry, r.ks)].set_index("trade_date"); pl = Q.loc[(r.expiry, r.kl)].set_index("trade_date")
        except KeyError:
            ps = pl = pd.DataFrame(columns=["bid", "ask"])
        j = ps.join(pl, lsuffix="_s", rsuffix="_l", how="inner")
        j = j[(j.index > r.trade_date) & (j.index < r.expiry) & (j.ask_s > 0)]
        cost = ((j.bid_s + j.ask_s) / 2 + SLIP * (j.ask_s - j.bid_s) + COMM) - ((j.bid_l + j.ask_l) / 2 - SLIP * (j.ask_l - j.bid_l) - COMM)
        hit = cost[cost <= TAKE * credit]
        if len(hit):
            pnl, exit_d, why = credit - float(hit.iloc[0]), hit.index[0], "take"
        else:
            pnl, exit_d, why = credit - settle, r.expiry, "expiry"
        cap = width - credit
        rows.append(dict(trade_date=r.trade_date, A_pnl=100 * pnl, A_cap=100 * cap, A_days=max((exit_d - r.trade_date).days, 1),
                         A_why=why, A_width=width, A_credit=credit))
    return pd.DataFrame(rows)


def mclu(x: pd.Series, d: pd.Series):
    g = x.groupby(d.dt.to_period("M")).mean(); return g.mean(), g.mean() / g.std(ddof=1) * np.sqrt(len(g)), len(g)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    B = pd.read_csv(REPO / "data/studies/always_on_index_put_2026-09-26.csv", parse_dates=["trade_date", "expiry"])
    B = B[B.cert].copy()
    B["B_pnl"], B["B_cap"] = 100 * B.pnlA, 100 * B.margin
    spot = spy_raw()
    T = choose(pull_entries(list(B.trade_date)))
    log(f"  {len(T)} spreads chosen")
    A = sim_A(T, pull_paths(T), spot)
    M = B.merge(A, on="trade_date")
    M["roc_A"], M["roc_B"] = 100 * M.A_pnl / M.A_cap, 100 * M.B_pnl / M.B_cap
    M["roc_B_span"] = 100 * M.B_pnl / (M.B_cap / 5)
    M["d"] = M.roc_A - M.roc_B
    h = M.trade_date < SPLIT
    m, t, nm = mclu(M.d, M.trade_date)
    out = ["# Stress bucket head-to-head (pre-registration in the docstring)",
           f"paired regime entries: {len(M)} of {len(B)} ({nm} months), {M.trade_date.min().date()} -> {M.trade_date.max().date()}; "
           f"A median width ${M.A_width.median():.0f}, credit ${M.A_credit.median():.2f}, exits {M.A_why.value_counts().to_dict()}"]
    for lab, col, capcol, pnlcol in (("A 20-DTE 0.25/0.15 spread", "roc_A", "A_cap", "A_pnl"),
                                    ("B 45-DTE 12Δ naked (Reg-T)", "roc_B", "B_cap", "B_pnl")):
        x = M[col]; mm, tt, _ = mclu(x, M.trade_date)
        cv = x[x <= x.quantile(0.05)].mean()
        out.append(f"  {lab:28s} ROC {x.mean():+.2f}%/trade (median {x.median():+.2f}, t {tt:+.2f}) win {100 * (M[pnlcol] > 0).mean():.0f}% "
                   f"| worst {x.min():+.1f}% of capital (${M[pnlcol].min():+.0f}/contract) | CVaR5 {cv:+.1f}% | "
                   f"median capital ${M[capcol].median():,.0f}/contract | mean $ P&L {M[pnlcol].mean():+.0f}")
    out.append(f"  (B on a SPAN-like capital ≈ Reg-T/5: ROC {M.roc_B_span.mean():+.2f}%/trade — sensitivity only)")
    out.append(f"\nPRIMARY paired ROC_A - ROC_B: {m:+.2f}pp  t {t:+.2f}  halves {M[h].d.mean():+.2f} / {M[~h].d.mean():+.2f}")
    M["A_rocd"] = M.roc_A / M.A_days * 365
    out.append(f"  A annualised ROC per capital-day {M.A_rocd.mean():+.0f}%/yr (mean hold {M.A_days.mean():.0f} d); B held ≤ 24 d by rule")
    c = M.sort_values("trade_date"); ep = (c.trade_date.diff().dt.days > 21).cumsum()
    E = c.groupby(ep).agg(start=("trade_date", "min"), A=("roc_A", "mean"), B=("roc_B", "mean"))
    de = E.A - E.B
    out.append(f"  episode-level ({len(E)} episodes): A {E.A.mean():+.2f}% vs B {E.B.mean():+.2f}% -> {de.mean():+.2f}pp t {de.mean() / de.std(ddof=1) * np.sqrt(len(de)):+.2f}; "
               f"A positive in {(E.A > 0).sum()}/{len(E)}, B in {(E.B > 0).sum()}/{len(E)}")
    for k, (a, b) in {"2020-02/03": ("2020-02-01", "2020-04-30"), "2022": ("2022-01-01", "2022-12-31"), "2018-Q4": ("2018-10-01", "2018-12-31")}.items():
        w = M[(M.trade_date >= a) & (M.trade_date <= b)]
        out.append(f"  {k:10s} n {len(w):2d}: A {w.roc_A.mean():+.2f}% (worst {w.roc_A.min():+.1f}) | B {w.roc_B.mean():+.2f}% (worst {w.roc_B.min():+.1f})")
    Y = M.groupby(M.trade_date.dt.year)[["roc_A", "roc_B"]].mean().round(2)
    out.append("\nper year ROC %/trade:\n" + Y.T.to_string())
    ok = abs(t) >= 3 and np.sign(M[h].d.mean()) == np.sign(M[~h].d.mean()) == np.sign(m)
    out.append(f"\nVERDICT: {'PREFERRED: ' + ('A (spread)' if m > 0 else 'B (naked 45-DTE)') if ok else 'EQUIVALENT on return (choose on tail / capital)'}")
    M.to_csv(REPO / "data/studies/stress_bucket_h2h_2026-09-28.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
