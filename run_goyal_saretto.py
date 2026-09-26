#!/usr/bin/env python3
"""
GOYAL-SARETTO: does the gap between a stock's historical and implied volatility predict delta-hedged straddle
returns, after real costs? (pre-registered 2026-09-26, before any data pull; Gabe: "let's register all three and
run 1". Siblings, pre-registered the same day and NOT run: run_cao_han_idiovol.py, run_har_vol_mispricing.py.)

CLAIM. Goyal & Saretto (JFE 2009), US stocks 1996-2006: sort each month on HV - IV (12-month historical vol minus
at-the-money implied vol). Long straddles where IV is cheap (top decile) minus straddles where IV is rich (bottom
decile) earned ~22%/month on delta-hedged straddles, at mid prices; they note much of it survives half-spread costs.

WHY NEW. The ledger measures the vol premium's LEVEL (VRP panel: single names +4.13vp at 10 days, t 8.7) and tested
IV rank / percentile, skew, the Cremers-Weinbaum spread and the 10/30 term-structure ratio. None of those is a
cross-sectional sort of IV against the stock's own realised vol. Every single-name vol trade here died on costs, so
the test is priced at real fills from the start.

DATA   silver.options_daily_v3 (RAW strikes, bid/ask, bid_iv/ask_iv, delta), bid/ask through ~2026-03.
       silver.chain_spot_daily (cached): RAW spot (for moneyness, the hedge and settlement, consistent with raw strikes)
       and split-adjusted closes (for HV). Includes delisted names.
FORMATION  the last trading day t of each month, 2011-01 -> 2026-01.
UNIVERSE at t (declared now): 50-session mean option volume >= 1,000 contracts; raw spot >= $10; >= 200 daily returns
       in the trailing 252; an ATM straddle at the expiry nearest 30 DTE (20-50) with both legs quoted (bid > 0),
       straddle mid >= $0.50 and quoted straddle spread <= 10% of mid (the liquidity rule, applied BEFORE sorting);
       no split between t and expiry (pit/splits). Months with < 100 eligible names are skipped.
SIGNAL   HV_t = std of daily log returns (split-adjusted) over the trailing 252 sessions x sqrt(252).
         IV_t = mean of the ATM call and put mid IVs ((bid_iv + ask_iv)/2) at the chosen expiry.
         ATM strike = the strike whose call delta is nearest 0.50 with both legs quoted.
         Sort on HV - IV into deciles within the month.
TRADE    ATM straddle bought at t, held to expiry, settled at intrinsic on the raw spot (last close <= expiry).
         DELTA-HEDGED daily at the close: hold -(delta_call + delta_put) shares (v3 deltas; carried forward over a
         missing day); stock hedge cost 2 bp of traded notional, including the unwind.
COSTS    house model: 25% of each leg's quoted spread + $0.0065/share/leg at entry; settlement at expiry costs nothing.
         Long legs pay mid + cost, short legs receive mid - cost. Returns are per $ of straddle MID at entry.
PRIMARY  the monthly NET spread = mean hedged return of the decile-10 LONG straddles (IV cheapest vs HV) + mean hedged
         return of the decile-1 SHORT straddles (IV richest), equal weight. Newey-West t (lag 3) on ~180 monthly
         values. BAR: t >= 3, both halves (split 2018-01) positive, positive in a majority of years.
REPORTED gross (mid) spread; each leg alone net; the full decile gradient (gross long hedged return by decile: the
         claim predicts it rises with HV - IV); the unhedged straddle spread; per year; n per month.
EXPLORATORY (no bar) HV over 63 sessions instead of 252.
PRIOR    the sort's sign is well replicated; the question is costs. Expect the gross spread positive and large; the net
         spread much smaller, possibly negative on the short side (selling rich IV is the cost-heavy leg here).
Local vs cloud: local orchestration of ~32 Athena queries (formation chains + holding paths, one per year each),
cached to data/cache/goyal_saretto/; the P&L loop is local CPU (minutes). No Fargate needed.

Run: AWS_PROFILE=clarinut-gmerton AWS_DEFAULT_REGION=us-west-2 PYTHONPATH=src:. .venv/bin/python3 run_goyal_saretto.py
     (log -> data/studies/logs/goyal_saretto.log)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from lib.athena_lib import athena

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/goyal_saretto"
LOG = REPO / "data/studies/logs/goyal_saretto.log"
START, END, SPLIT = "2011-01-01", "2026-01-31", "2018-01-01"
SLIP, COMM, HEDGE_BP = 0.25, 0.0065, 0.0002
OPTVOL_MIN, PX_MIN, MID_MIN, SPR_MAX, N_MIN = 1000, 10.0, 0.50, 0.10, 100


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def nw_t(x: pd.Series, lag: int = 3) -> float:
    x = x.dropna().values; n = len(x)
    if n < 10:
        return np.nan
    e = x - x.mean(); g0 = (e @ e) / n
    s = g0 + 2 * sum((1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n for k in range(1, lag + 1))
    return float(x.mean() / np.sqrt(s / n))


# ---------------------------------------------------------------- spot, HV, liquidity
def spot_panels():
    import run_dip_survivorship as DS
    d = DS.pull()
    raw = d.pivot_table(index="trade_date", columns="ticker", values="spot").sort_index()
    C, V = DS.adjust_and_clean(d)
    lr = np.log(C / C.shift(1))
    hv252 = lr.rolling(252, min_periods=200).std() * np.sqrt(252)
    hv63 = lr.rolling(63, min_periods=50).std() * np.sqrt(252)
    ov = V.rolling(50, min_periods=30).mean()
    return raw, hv252, hv63, ov


def formation_dates(idx: pd.DatetimeIndex) -> list[pd.Timestamp]:
    s = pd.Series(idx, index=idx)
    me = s.groupby(idx.to_period("M")).max()
    return [d for d in me if pd.Timestamp(START) <= d <= pd.Timestamp(END)]


# ---------------------------------------------------------------- stage 1: formation chains
def pull_formation(dates: list[pd.Timestamp]) -> pd.DataFrame:
    out = []
    for y in sorted({d.year for d in dates}):
        f = CACHE / f"formation_{y}.parquet"
        if not f.exists():
            ds = [d for d in dates if d.year == y]
            dl = ",".join(f"DATE '{d.date()}'" for d in ds)
            lo, hi = (min(ds) + pd.Timedelta(days=15)).date(), (max(ds) + pd.Timedelta(days=55)).date()
            log(f"  formation pull {y} ({len(ds)} dates)")
            q = athena(f"""SELECT ticker, trade_date, expiry, strike, cp, bid, ask, bid_iv, ask_iv, delta
                           FROM options_daily_v3
                           WHERE trade_date IN ({dl}) AND expiry BETWEEN DATE '{lo}' AND DATE '{hi}'
                             AND bid > 0 AND ask > 0 AND abs(delta) BETWEEN 0.25 AND 0.75""")
            q.to_parquet(f, index=False)
        out.append(pd.read_parquet(f))
    d = pd.concat(out, ignore_index=True)
    for c in ("trade_date", "expiry"):
        d[c] = pd.to_datetime(d[c])
    return d


def pick_straddles(ch: pd.DataFrame) -> pd.DataFrame:
    ch = ch.copy()
    ch["dte"] = (ch.expiry - ch.trade_date).dt.days
    ch = ch[(ch.dte >= 20) & (ch.dte <= 50)]
    ch["gap"] = (ch.dte - 30).abs()
    best = ch.groupby(["ticker", "trade_date"]).gap.transform("min")
    ch = ch[ch.gap == best]
    ch = ch[ch.expiry == ch.groupby(["ticker", "trade_date"]).expiry.transform("min")]   # tie -> nearer expiry
    c = ch[ch.cp == "C"].drop_duplicates(["ticker", "trade_date", "strike"])
    p = ch[ch.cp == "P"].drop_duplicates(["ticker", "trade_date", "strike"])
    m = c.merge(p, on=["ticker", "trade_date", "expiry", "strike"], suffixes=("_c", "_p"))
    m["dd"] = (m.delta_c - 0.5).abs()
    m = m.sort_values("dd").drop_duplicates(["ticker", "trade_date"])
    m["mid_c"], m["mid_p"] = (m.bid_c + m.ask_c) / 2, (m.bid_p + m.ask_p) / 2
    m["sp_c"], m["sp_p"] = m.ask_c - m.bid_c, m.ask_p - m.bid_p
    m["mid"] = m.mid_c + m.mid_p
    m["spr"] = (m.sp_c + m.sp_p) / m.mid
    m["iv_c"], m["iv_p"] = (m.bid_iv_c + m.ask_iv_c) / 2, (m.bid_iv_p + m.ask_iv_p) / 2
    m = m[(m.iv_c > 0) & (m.iv_p > 0)]
    m["iv"] = (m.iv_c + m.iv_p) / 2
    return m[["ticker", "trade_date", "expiry", "strike", "mid", "mid_c", "mid_p", "sp_c", "sp_p", "spr", "iv"]]


# ---------------------------------------------------------------- stage 2: holding paths
def pull_paths(S: pd.DataFrame) -> pd.DataFrame:
    out = []
    S = S.assign(y=S.trade_date.dt.year)
    for y, g in S.groupby("y"):
        f = CACHE / f"paths_{y}.parquet"
        if not f.exists():
            tl = ",".join(f"'{t}'" for t in sorted(g.ticker.unique()))
            el = ",".join(f"DATE '{e.date()}'" for e in sorted(g.expiry.unique()))
            kl = ",".join(f"{k:g}" for k in sorted(g.strike.unique()))
            lo, hi = g.trade_date.min().date(), g.expiry.max().date()
            log(f"  path pull {y} ({g.ticker.nunique()} tickers, {len(g)} straddles)")
            q = athena(f"""SELECT ticker, trade_date, expiry, strike, cp, delta
                           FROM options_daily_v3
                           WHERE ticker IN ({tl}) AND expiry IN ({el}) AND strike IN ({kl})
                             AND trade_date BETWEEN DATE '{lo}' AND DATE '{hi}'""")
            keys = g[["ticker", "expiry", "strike"]].drop_duplicates()
            q["expiry"] = pd.to_datetime(q.expiry); q["trade_date"] = pd.to_datetime(q.trade_date)
            q = q.merge(keys, on=["ticker", "expiry", "strike"])
            q.to_parquet(f, index=False)
        out.append(pd.read_parquet(f))
    d = pd.concat(out, ignore_index=True)
    for c in ("trade_date", "expiry"):
        d[c] = pd.to_datetime(d[c])
    return d


def straddle_pnl(S: pd.DataFrame, P: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    dl = (P.pivot_table(index=["ticker", "expiry", "strike", "trade_date"], columns="cp", values="delta", aggfunc="mean"))
    dl["d"] = dl.get("C", np.nan) + dl.get("P", np.nan)
    dl = dl["d"]
    days = raw.index
    rows = []
    for r in S.itertuples():
        if r.ticker not in raw.columns:
            continue
        sp = raw[r.ticker]
        i0 = days.get_indexer([r.trade_date])[0]
        iT = days.searchsorted(r.expiry, side="right") - 1
        if i0 < 0 or iT <= i0:
            continue
        path = sp.iloc[i0:iT + 1].ffill()
        if path.isna().iloc[0] or path.isna().iloc[-1]:
            continue
        try:
            dd = dl.loc[(r.ticker, r.expiry, r.strike)]
        except KeyError:
            dd = pd.Series(dtype=float)
        dd = dd.reindex(path.index).ffill()
        dd.iloc[0] = dd.iloc[0] if np.isfinite(dd.iloc[0]) else np.nan
        h = -dd.fillna(0.0).values[:-1]                                   # shares held over (d, d+1]
        s = path.values
        hedge = float(np.sum(h * np.diff(s)))
        trades = np.abs(np.diff(np.concatenate([[0.0], h, [0.0]])))
        hcost = float(HEDGE_BP * np.sum(trades * np.concatenate([s[:-1], [s[-1]]])))
        unh_pay = abs(s[-1] - r.strike)
        cost = SLIP * (r.sp_c + r.sp_p) + 2 * COMM
        long_gross = (unh_pay + hedge - r.mid) / r.mid
        long_net = (unh_pay + hedge - hcost - r.mid - cost) / r.mid
        short_net = (r.mid - cost - unh_pay - hedge - hcost) / r.mid
        rows.append(dict(ticker=r.ticker, trade_date=r.trade_date, long_gross=long_gross, long_net=long_net,
                         short_net=short_net, unhedged_gross=(unh_pay - r.mid) / r.mid,
                         delta_missing=int(dd.isna().sum())))
    return pd.DataFrame(rows)


def run_sort(E: pd.DataFrame, sig: str, out: list[str], label: str, primary: bool) -> pd.Series:
    E = E.dropna(subset=[sig]).copy()
    E["dec"] = E.groupby("trade_date")[sig].transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=False) + 1)
    M = E.groupby(["trade_date", "dec"]).agg(lg=("long_gross", "mean"), ln=("long_net", "mean"), sn=("short_net", "mean"),
                                             ug=("unhedged_gross", "mean"), n=("ticker", "size")).reset_index()
    top, bot = M[M.dec == 10].set_index("trade_date"), M[M.dec == 1].set_index("trade_date")
    net = 100 * (top.ln + bot.sn)
    gross = 100 * (top.lg - bot.lg)
    unh = 100 * (top.ug - bot.ug)
    h = net.index < pd.Timestamp(SPLIT)
    yr = net.groupby(net.index.year).mean()
    ok = nw_t(net) >= 3 and net[h].mean() > 0 and net[~h].mean() > 0 and (yr > 0).sum() > len(yr) / 2
    out.append(f"\n## {label}: {len(net)} months, ~{E.groupby('trade_date').size().mean():.0f} names/month, "
               f"~{top.n.mean():.0f} per decile")
    out.append(f"  NET spread (D10 long + D1 short, hedged): {net.mean():+.2f}%/mo  t_NW {nw_t(net):+.2f}  halves "
               f"{net[h].mean():+.2f} / {net[~h].mean():+.2f}  years + {(yr > 0).sum()}/{len(yr)}"
               + ("  *PRIMARY*" if primary else ""))
    out.append(f"  gross (mid) spread {gross.mean():+.2f}%/mo t {nw_t(gross):+.2f} | legs net: D10 long "
               f"{100*top.ln.mean():+.2f}% (t {nw_t(100*top.ln):+.2f}), D1 short {100*bot.sn.mean():+.2f}% "
               f"(t {nw_t(100*bot.sn):+.2f}) | unhedged gross spread {unh.mean():+.2f}%")
    g = M.groupby("dec").lg.mean() * 100
    out.append("  decile gradient, gross hedged LONG return %: " + " ".join(f"D{int(k)}:{v:+.1f}" for k, v in g.items()))
    out.append("  net spread by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in yr.items())
               + (f"  -> {'PASS' if ok else 'NOT MET'}" if primary else ""))
    return net


def main():
    out = ["# Goyal-Saretto HV - IV sort on delta-hedged ATM straddles (pre-registration in the docstring)"]
    CACHE.mkdir(parents=True, exist_ok=True)
    raw, hv252, hv63, ov = spot_panels()
    dates = formation_dates(raw.index)
    ch = pull_formation(dates)
    S = pick_straddles(ch)
    log(f"  straddles picked: {len(S):,}")
    S["hv"] = [hv252.at[d, t] if t in hv252.columns else np.nan for t, d in zip(S.ticker, S.trade_date)]
    S["hv63"] = [hv63.at[d, t] if t in hv63.columns else np.nan for t, d in zip(S.ticker, S.trade_date)]
    S["ov"] = [ov.at[d, t] if t in ov.columns else np.nan for t, d in zip(S.ticker, S.trade_date)]
    S["px"] = [raw.at[d, t] if t in raw.columns else np.nan for t, d in zip(S.ticker, S.trade_date)]
    sp = pd.read_parquet(REPO / "data/cache/pit/splits.parquet"); sp["execution_date"] = pd.to_datetime(sp.execution_date)
    spl = sp.groupby("ticker").execution_date.apply(list).to_dict()
    S["split"] = [any(d < x <= e for x in spl.get(t, [])) for t, d, e in zip(S.ticker, S.trade_date, S.expiry)]
    E = S[(S.ov >= OPTVOL_MIN) & (S.px >= PX_MIN) & S.hv.notna() & (S.mid >= MID_MIN) & (S.spr <= SPR_MAX) & ~S.split].copy()
    cnt = E.groupby("trade_date").size()
    E = E[E.trade_date.isin(cnt[cnt >= N_MIN].index)]
    log(f"  eligible: {len(E):,} straddles over {E.trade_date.nunique()} months")
    P = pull_paths(E)
    R = straddle_pnl(E, P, raw)
    E = E.merge(R, on=["ticker", "trade_date"])
    E["sig"], E["sig63"] = E.hv - E.iv, E.hv63 - E.iv
    out.append(f"eligible straddles with P&L: {len(E):,}; months {E.trade_date.nunique()}; "
               f"median spread/mid {E.spr.median():.3f}; delta days missing (share) {E.delta_missing.sum() / max(len(E), 1):.2f}/straddle")
    net = run_sort(E, "sig", out, "PRIMARY HV252 - IV", True)
    run_sort(E, "sig63", out, "EXPLORATORY HV63 - IV", False)
    E.to_parquet(REPO / "data/studies/logs/goyal_saretto_straddles.parquet", index=False)
    net.to_frame("net_spread_pct").to_csv(REPO / "data/studies/goyal_saretto_2026-09-26.csv")
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
