#!/usr/bin/env python3
"""
VASQUEZ (JFQA 2017): does the slope of a stock's implied-vol TERM STRUCTURE predict its straddle returns, after real
costs? (pre-registered 2026-09-28, before the long-tenor pull; cited in Euan Sinclair, "Positional Option Trading";
Gabe: "yes, pre-register it and run it".)

CLAIM (abstract only -- the paper's exact tenors, sample and magnitudes are NOT verified here): "The slope of the
implied volatility term structure is positively related to future option returns ... Straddle portfolios with high
slopes ... outperform straddle portfolios with low slopes by an economically and statistically significant amount."
Trade: buy straddles on the most upward-sloping names, sell straddles on the most inverted.

WHY NEW. The ledger tested the 10/30 term ratio on the ETF-roster short straddle (FVR regression, FAIL) and the
pre-earnings ts_slope gate (NULL), plus the index VIX/VIX3M curve today (NULL). None is a monthly CROSS-SECTIONAL
sort of single-name IV slope. The sibling cross-sectional sort (Goyal-Saretto, 2026-09-26) failed on costs:
net -4.73%/mo, t -4.99, gross +0.71%/mo, costs ~2.6-2.9pp per leg-month. So the bar that matters is the gross spread
clearing that friction.

REUSE (declared). The 55,067 eligible straddles and their P&L from run_goyal_saretto.py
(data/studies/logs/goyal_saretto_straddles.parquet): same universe (option volume >= 1k, spot >= $10, straddle mid >=
$0.50, quoted spread <= 10% of mid, no split in the hold), month-end formation 2011-01 -> 2026-01, ATM straddle nearest
30 DTE (20-50) bought at t and held to expiry, settled at intrinsic on raw spot; house costs (25% of each leg's quoted
spread + $0.0065/share/leg; hedge 2 bp). Nothing about the trade changes; only the SIGNAL is new.
NEW DATA  a long-tenor ATM IV at each formation date: silver.options_daily_v3, expiry nearest 91 DTE within 60-130,
         strike with call delta nearest 0.50 and both legs quoted (bid > 0), IV_long = mean of call/put mid IVs.
         Cached to data/cache/vasquez/.
SIGNAL   SLOPE = IV_long - IV_30 (IV_30 = the traded straddle's own IV). Deciles within the month.
PRIMARY  (the paper's vehicle) UNHEDGED straddles: monthly NET spread = D10 (steepest) long net + D1 (most inverted)
         short net, equal weight; Newey-West t (lag 3). BAR: t >= 3, both halves (split 2018-01) > 0, positive in a
         majority of years.
SECONDARY the same spread delta-hedged daily (the Goyal-Saretto vehicle); gross (mid) spreads for both; each leg
         alone net; the full decile gradient (the claim predicts gross long returns RISING with the slope); per year.
EXPLORATORY (no bar) SLOPE as a ratio IV_long / IV_30; the slope sort within the top HV-IV tercile.
PRIOR    the sort's sign may replicate gross; after Goyal-Saretto's ~5-6pp round-trip friction per month, expect the
         net spread negative. A gross spread < ~5%/mo is decisive against the trade regardless of its t.
Local: ~16 Athena queries (one per year, restricted to that year's eligible names) + CPU for minutes.

Run: AWS_PROFILE=clarinut-gmerton AWS_DEFAULT_REGION=us-west-2 PYTHONPATH=src:. .venv/bin/python3 run_vasquez_ts_slope.py
     (log -> data/studies/logs/vasquez_ts_slope.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from lib.athena_lib import athena
from run_goyal_saretto import COMM, SLIP, nw_t

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/vasquez"
LOG = REPO / "data/studies/logs/vasquez_ts_slope.log"
SPLIT = "2018-01-01"


def log(m):
    print(m, file=sys.stderr, flush=True)


def pull_long(E: pd.DataFrame) -> pd.DataFrame:
    out = []
    for y, g in E.groupby(E.trade_date.dt.year):
        f = CACHE / f"long_{y}.parquet"
        if not f.exists():
            tl = ",".join(f"'{t}'" for t in sorted(g.ticker.unique()))
            dl = ",".join(f"DATE '{d.date()}'" for d in sorted(g.trade_date.unique()))
            log(f"  long-tenor pull {y} ({g.ticker.nunique()} names, {g.trade_date.nunique()} dates)")
            athena(f"""SELECT ticker, trade_date, expiry, strike, cp, bid_iv, ask_iv, delta FROM options_daily_v3
                       WHERE ticker IN ({tl}) AND trade_date IN ({dl})
                         AND date_diff('day', trade_date, expiry) BETWEEN 60 AND 130
                         AND bid > 0 AND ask > 0 AND abs(delta) BETWEEN 0.35 AND 0.65""").to_parquet(f, index=False)
        out.append(pd.read_parquet(f))
    d = pd.concat(out, ignore_index=True)
    for c in ("trade_date", "expiry"):
        d[c] = pd.to_datetime(d[c])
    d["dte"] = (d.expiry - d.trade_date).dt.days
    d["gap"] = (d.dte - 91).abs()
    d = d[d.gap == d.groupby(["ticker", "trade_date"]).gap.transform("min")]
    d = d[d.expiry == d.groupby(["ticker", "trade_date"]).expiry.transform("min")]
    c = d[d.cp == "C"].drop_duplicates(["ticker", "trade_date", "strike"])
    p = d[d.cp == "P"].drop_duplicates(["ticker", "trade_date", "strike"])
    m = c.merge(p, on=["ticker", "trade_date", "expiry", "strike"], suffixes=("_c", "_p"))
    m["dd"] = (m.delta_c - 0.5).abs()
    m = m.sort_values("dd").drop_duplicates(["ticker", "trade_date"])
    m["iv_long"] = ((m.bid_iv_c + m.ask_iv_c) / 2 + (m.bid_iv_p + m.ask_iv_p) / 2) / 2
    m = m[m.iv_long > 0]
    return m[["ticker", "trade_date", "iv_long", "dte"]].rename(columns={"dte": "dte_long"})


def sort(E, sig, out, label, primary):
    E = E.dropna(subset=[sig]).copy()
    E["dec"] = E.groupby("trade_date")[sig].transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=False) + 1)
    M = E.groupby(["trade_date", "dec"]).agg(ug=("unhedged_gross", "mean"), ul=("u_long_net", "mean"), us=("u_short_net", "mean"),
                                             hg=("long_gross", "mean"), hl=("long_net", "mean"), hs=("short_net", "mean"),
                                             n=("ticker", "size")).reset_index()
    T, B = M[M.dec == 10].set_index("trade_date"), M[M.dec == 1].set_index("trade_date")
    res = {}
    out.append(f"\n## {label}: {len(T)} months, ~{T.n.mean():.0f} names per decile")
    for veh, g, l, s in (("UNHEDGED", "ug", "ul", "us"), ("HEDGED", "hg", "hl", "hs")):
        net = 100 * (T[l] + B[s]); gross = 100 * (T[g] - B[g])
        h = net.index < pd.Timestamp(SPLIT); yr = net.groupby(net.index.year).mean()
        tag = "  *PRIMARY*" if (primary and veh == "UNHEDGED") else ""
        out.append(f"  {veh:8s} NET D10 long + D1 short {net.mean():+.2f}%/mo t_NW {nw_t(net):+.2f} halves {net[h].mean():+.2f} / "
                   f"{net[~h].mean():+.2f} yrs+ {(yr > 0).sum()}/{len(yr)} | GROSS {gross.mean():+.2f}%/mo t {nw_t(gross):+.2f} | "
                   f"legs net: long {100 * T[l].mean():+.2f}% short {100 * B[s].mean():+.2f}%{tag}")
        grad = M.groupby("dec")[g].mean() * 100
        out.append(f"           gross LONG by decile: " + " ".join(f"D{int(k)}:{v:+.1f}" for k, v in grad.items()))
        if primary and veh == "UNHEDGED":
            out.append("           net by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in yr.items()))
            res = dict(m=net.mean(), t=nw_t(net), h1=net[h].mean(), h2=net[~h].mean(), yp=(yr > 0).sum(), ny=len(yr))
    return res


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    E = pd.read_parquet(REPO / "data/studies/logs/goyal_saretto_straddles.parquet")
    E["trade_date"] = pd.to_datetime(E.trade_date)
    L = pull_long(E)
    E = E.merge(L, on=["ticker", "trade_date"], how="inner")
    cost = (SLIP * (E.sp_c + E.sp_p) + 2 * COMM) / E["mid"]
    E["u_long_net"] = E.unhedged_gross - cost
    E["u_short_net"] = -E.unhedged_gross - cost
    E["slope"] = E.iv_long - E.iv
    E["ratio"] = E.iv_long / E.iv
    out = ["# Vasquez IV term-structure slope sort (pre-registration in the docstring)",
           f"straddles with a long-tenor IV: {len(E):,} ({E.trade_date.nunique()} months); median long DTE {E.dte_long.median():.0f}; "
           f"slope median {E.slope.median():+.3f}, share inverted {100 * (E.slope < 0).mean():.0f}%; median cost {100 * cost.median():.1f}% of mid per side"]
    r = sort(E, "slope", out, "PRIMARY slope = IV91 - IV30", True)
    sort(E, "ratio", out, "EXPLORATORY ratio IV91 / IV30", False)
    E["gs_ter"] = E.groupby("trade_date").sig.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False))
    sort(E[E.gs_ter == 2], "slope", out, "EXPLORATORY slope inside the top HV-IV tercile", False)
    ok = r["t"] >= 3 and r["h1"] > 0 and r["h2"] > 0 and r["yp"] > r["ny"] / 2
    out.append(f"\nVERDICT (PRIMARY unhedged net): {'PASS' if ok else 'NOT MET'} ({r['m']:+.2f}%/mo, t {r['t']:+.2f})")
    E.to_parquet(REPO / "data/studies/logs/vasquez_straddles.parquet", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
