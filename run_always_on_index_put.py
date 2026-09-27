#!/usr/bin/env python3
"""
ALWAYS-ON 45-DTE 12-DELTA INDEX PUT (Sosnoff's "one trade", via Freedom Income 0f2kr2iOXzg) vs the certified regime
(pre-registered 2026-09-26, before the data pull; Gabe: "go").

CLAIM. "Sell a put on the ES 45 days out at a 12 delta and take off at 50%", closing at 21 DTE regardless, every
week, forever. The ledger certifies an index put sale only in the BEARISH-HIGH-IV regime (SPY 20-DTE 0.25/0.15 bull
put t 6.07; SPX condor t 5.21 -- one bet). The question: does selling ALWAYS add anything beyond the regime that
already certifies, or is the regime the whole edge?

INSTRUMENT  SPY puts as the /ES proxy (same index, penny-wide quotes; v3 bid/ask). Naked short put, 1 contract.
DATA        silver.options_daily_v3, pulled fresh (entry chains, then the chosen contracts' daily paths);
            SPY raw spot from chain_spot_daily for settlement; VIX from data/cache/vix_daily_long.parquet +
            vix_daily.parquet; SPY 50-day MA from adjusted closes (ratio only).
ENTRY       the last trading day of every week, 2010-01 -> the last entry whose expiry has quotes (bid/ask ~2026-03).
            Expiry nearest 45 DTE within 38-52; the put with delta nearest -0.12 and bid > 0.
FILLS       house model: sell at mid - 25% of the quoted spread - $0.0065/share; buy back at mid + 25% + $0.0065.
            Settlement at expiry costs nothing.
ARM A (PRIMARY, his rule)  close the first day the cost to close <= 50% of the entry credit; else close at the first
            session with DTE <= 21; a missing quote on a day is skipped (never treated as a fill); if no quote exists
            from the 21-DTE day to expiry, settle at intrinsic on the raw spot. The share of trades affected is reported.
ARM B       hold to expiry, settle at intrinsic max(K - S_T, 0) on the raw spot.
RETURN      net P&L per share / Reg-T naked margin at entry (0.20 x strike - OTM amount, floored at 0.10 x strike,
            + premium). SPAN on /ES is ~5x lower -- report $ per contract too, since return on margin is mostly leverage.
REGIME      at entry, the ledger's classifier: Bearish_HighIV = SPY close < its 50-day MA AND VIX close >= 20.
PRIMARY     ARM A, ALWAYS-ON: mean net return per trade, t on ENTRY-MONTH cluster means (weekly entries overlap).
            BAR: t >= 3, both halves (split 2018-01) positive, positive in a majority of years.
KEY SECONDARY (declared, the actual question): ARM A on entries OUTSIDE Bearish_HighIV (the complement). If the
            complement is ~0 or negative, always-on adds nothing beyond the regime; report the Bearish_HighIV subset
            alongside and the difference (Welch t on month means).
REPORTED    ARM B the same three ways; win rate, mean vs median, worst 10 trades with dates; crash windows explicitly:
            2011-08, 2015-08, 2018-02, 2018-12, 2020-02/03, 2022; per year; exit-reason shares; $ per contract.
            Crash-week rule (house): settle at intrinsic, never at a stale mark.
PRIOR       positive gross on average (the VRP), negative skew. The ledger's 21-DTE close cost return on 45-DTE
            strangles (t -2.42) and cut the tail; expect ARM A below ARM B on mean, better on tail; expect the
            complement to be thin after costs.
Local vs cloud: local orchestration of ~34 small Athena queries (one entry-chain + one path query per year), cached
to data/cache/always_on_put/; minutes of CPU.

Run: AWS_PROFILE=clarinut-gmerton AWS_DEFAULT_REGION=us-west-2 PYTHONPATH=src:. .venv/bin/python3 run_always_on_index_put.py
     (log -> data/studies/logs/always_on_index_put.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.athena_lib import athena

REPO = Path(__file__).resolve().parent
CACHE = REPO / "data/cache/always_on_put"
LOG = REPO / "data/studies/logs/always_on_index_put.log"
SLIP, COMM, SPLIT, TAKE, MGMT_DTE = 0.25, 0.0065, "2018-01-01", 0.50, 21
CRASH = {"2011-08": ("2011-07-01", "2011-09-30"), "2015-08": ("2015-07-15", "2015-09-30"),
         "2018-02": ("2018-01-01", "2018-02-28"), "2018-Q4": ("2018-10-01", "2018-12-31"),
         "2020-02/03": ("2020-01-15", "2020-03-31"), "2022": ("2022-01-01", "2022-12-31")}


def log(m):
    print(m, file=sys.stderr, flush=True)


def spy_raw() -> pd.Series:
    d = pd.read_parquet(REPO / "data/cache/chain_spot/chain_spot_daily.parquet")
    s = d[d.ticker == "SPY"].set_index("trade_date").spot.sort_index()
    s.index = pd.to_datetime(s.index)
    return s


def entry_days(idx: pd.DatetimeIndex) -> list[pd.Timestamp]:
    s = pd.Series(idx, index=idx)
    return list(s.groupby(idx.to_period("W")).max())


def pull_entries(days) -> pd.DataFrame:
    out = []
    for y in sorted({d.year for d in days}):
        f = CACHE / f"entry_{y}.parquet"
        if not f.exists():
            dl = ",".join(f"DATE '{d.date()}'" for d in days if d.year == y)
            log(f"  entry chains {y}")
            q = athena(f"""SELECT trade_date, expiry, strike, bid, ask, delta FROM options_daily_v3
                           WHERE ticker = 'SPY' AND upper(substr(cp,1,1)) = 'P' AND trade_date IN ({dl})
                             AND date_diff('day', trade_date, expiry) BETWEEN 38 AND 52
                             AND delta BETWEEN -0.25 AND -0.05 AND bid > 0""")
            q.to_parquet(f, index=False)
        out.append(pd.read_parquet(f))
    d = pd.concat(out, ignore_index=True)
    d["trade_date"], d["expiry"] = pd.to_datetime(d.trade_date), pd.to_datetime(d.expiry)
    return d


def choose(ch: pd.DataFrame) -> pd.DataFrame:
    ch = ch.copy()
    ch["gap"] = ((ch.expiry - ch.trade_date).dt.days - 45).abs()
    ch = ch[ch.gap == ch.groupby("trade_date").gap.transform("min")]
    ch = ch[ch.expiry == ch.groupby("trade_date").expiry.transform("min")]
    ch["dd"] = (ch.delta + 0.12).abs()
    return ch.sort_values("dd").drop_duplicates("trade_date")[["trade_date", "expiry", "strike", "bid", "ask", "delta"]]


def pull_paths(T: pd.DataFrame) -> pd.DataFrame:
    out = []
    T = T.assign(y=T.trade_date.dt.year)
    for y, g in T.groupby("y"):
        f = CACHE / f"paths_{y}.parquet"
        if not f.exists():
            el = ",".join(f"DATE '{e.date()}'" for e in sorted(g.expiry.unique()))
            kl = ",".join(f"{k:g}" for k in sorted(g.strike.unique()))
            log(f"  paths {y} ({len(g)} trades)")
            q = athena(f"""SELECT trade_date, expiry, strike, bid, ask FROM options_daily_v3
                           WHERE ticker = 'SPY' AND upper(substr(cp,1,1)) = 'P'
                             AND expiry IN ({el}) AND strike IN ({kl})
                             AND trade_date BETWEEN DATE '{g.trade_date.min().date()}' AND DATE '{g.expiry.max().date()}'""")
            q.to_parquet(f, index=False)
        out.append(pd.read_parquet(f))
    d = pd.concat(out, ignore_index=True)
    d["trade_date"], d["expiry"] = pd.to_datetime(d.trade_date), pd.to_datetime(d.expiry)
    return d.drop_duplicates(["trade_date", "expiry", "strike"])


def simulate(T: pd.DataFrame, Q: pd.DataFrame, spot: pd.Series) -> pd.DataFrame:
    Q = Q.set_index(["expiry", "strike"]).sort_index()
    rows = []
    for r in T.itertuples():
        mid, spr = (r.bid + r.ask) / 2, r.ask - r.bid
        credit = mid - SLIP * spr - COMM
        sT = spot.loc[:r.expiry]
        if len(sT) == 0 or sT.index[-1] < r.expiry - pd.Timedelta(days=4):
            continue                                     # no settlement spot
        S_T = float(sT.iloc[-1])
        intrinsic = max(r.strike - S_T, 0.0)
        try:
            p = Q.loc[(r.expiry, r.strike)].set_index("trade_date").sort_index()
        except KeyError:
            p = pd.DataFrame(columns=["bid", "ask"])
        p = p[(p.index > r.trade_date) & (p.index <= r.expiry) & (p.ask > 0)]
        close_cost = (p.bid + p.ask) / 2 + SLIP * (p.ask - p.bid) + COMM
        dte = (r.expiry - p.index.to_series()).dt.days
        exitA, whyA, gap = None, None, False
        for d, c in close_cost.items():
            if c <= TAKE * credit:
                exitA, whyA = c, "take"; break
            if dte[d] <= MGMT_DTE:
                exitA, whyA = c, "21dte"; break
        if exitA is None:
            exitA, whyA, gap = intrinsic, "expiry", True
        s0 = spot.loc[:r.trade_date]
        S0 = float(s0.iloc[-1]) if len(s0) else np.nan
        otm = max(S0 - r.strike, 0.0)
        margin = max(0.20 * S0 - otm, 0.10 * r.strike) + mid
        rows.append(dict(trade_date=r.trade_date, expiry=r.expiry, strike=r.strike, delta=r.delta, S0=S0, credit=credit,
                         pnlA=credit - exitA, whyA=whyA, pnlB=credit - intrinsic, margin=margin, gapA=gap,
                         spr_pct=spr / mid))
    return pd.DataFrame(rows)


def mclu(x: pd.Series, dates: pd.Series) -> tuple[float, float, int]:
    g = x.groupby(dates.dt.to_period("M")).mean()
    return float(g.mean()), float(g.mean() / g.std(ddof=1) * np.sqrt(len(g))) if len(g) > 2 else np.nan, len(g)


def welch_m(a, da, b, db):
    ga, gb = a.groupby(da.dt.to_period("M")).mean(), b.groupby(db.dt.to_period("M")).mean()
    return float((ga.mean() - gb.mean()) / np.sqrt(ga.var(ddof=1) / len(ga) + gb.var(ddof=1) / len(gb)))


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    spot = spy_raw()
    days = [d for d in entry_days(spot.index) if d >= pd.Timestamp("2010-01-01")]
    T = choose(pull_entries(days))
    Q = pull_paths(T)
    R = simulate(T, Q, spot)
    last_q = Q.trade_date.max()
    R = R[R.expiry <= last_q]                                   # expiry must lie inside the quoted data
    vix = pd.concat([pd.read_parquet(REPO / "data/cache/vix_daily_long.parquet"),
                     pd.read_parquet(REPO / "data/cache/vix_daily.parquet").reset_index().rename(
                         columns=lambda c: {"date": "trade_date", "close": "vix_close"}.get(c, c))], ignore_index=True)
    vix["trade_date"] = pd.to_datetime(vix.trade_date)
    vix = vix.drop_duplicates("trade_date", keep="last").set_index("trade_date").vix_close.sort_index()
    adj = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "close"])
    adj = adj[adj.ticker == "SPY"].assign(date=lambda d: pd.to_datetime(d.date)).set_index("date").close.sort_index()
    ma = adj / adj.rolling(50).mean()
    R["vix"] = vix.reindex(R.trade_date, method="ffill").values
    R["ma"] = ma.reindex(R.trade_date, method="ffill").values
    R["cert"] = (R.ma < 1.0) & (R.vix >= 20)
    for a in ("A", "B"):
        R[f"ret{a}"] = 100 * R[f"pnl{a}"] / R.margin
    out = [f"# Always-on 45-DTE 12-delta SPY put (pre-registration in the docstring)",
           f"trades {len(R):,} weekly entries {R.trade_date.min().date()} -> {R.trade_date.max().date()} "
           f"(quotes through {last_q.date()}); median delta {R.delta.median():.3f}, median DTE "
           f"{(R.expiry - R.trade_date).dt.days.median():.0f}, median spread {100 * R.spr_pct.median():.1f}% of mid; "
           f"certified-regime entries {R.cert.sum()} ({100 * R.cert.mean():.0f}%)",
           f"ARM A exits: {R.whyA.value_counts(normalize=True).round(3).to_dict()} (expiry = no quote from 21 DTE on -> intrinsic)"]
    h = R.trade_date < SPLIT

    def line(lab, d, col):
        m, t, nm = mclu(d[col], d.trade_date)
        yr = d.groupby(d.trade_date.dt.year)[col].mean()
        hh = d.trade_date < SPLIT
        pnl = d[col.replace("ret", "pnl")]
        out.append(f"  {lab:34s} n {len(d):4d} months {nm:3d}  {m:+.3f}% of margin t {t:+.2f}  halves "
                   f"{d[hh][col].mean():+.3f}/{d[~hh][col].mean():+.3f}  yrs+ {(yr > 0).sum()}/{len(yr)}  win "
                   f"{100 * (pnl > 0).mean():.0f}%  median {d[col].median():+.2f}  ${100 * pnl.mean():+.0f}/contract")
        return m, t, d[hh][col].mean(), d[~hh][col].mean(), (yr > 0).sum(), len(yr)

    res = {}
    for a, nm in (("A", "ARM A (50% take / 21 DTE) *PRIMARY*"), ("B", "ARM B (hold to expiry)")):
        out.append(f"\n## {nm}")
        res[a] = line("ALWAYS-ON", R, f"ret{a}")
        line("certified Bearish_HighIV subset", R[R.cert], f"ret{a}")
        line("COMPLEMENT (key secondary)", R[~R.cert], f"ret{a}")
        out.append(f"  certified - complement: Welch t on month means {welch_m(R[R.cert][f'ret{a}'], R[R.cert].trade_date, R[~R.cert][f'ret{a}'], R[~R.cert].trade_date):+.2f}")
    out.append("\nworst 10 trades (ARM A, % of margin / $ per contract):")
    for r in R.nsmallest(10, "retA").itertuples():
        out.append(f"  {r.trade_date.date()} K {r.strike:g} exp {r.expiry.date()} {r.retA:+.1f}% ${100 * r.pnlA:+.0f} ({r.whyA}); hold {r.retB:+.1f}%")
    out.append("\ncrash windows (sum of per-trade % of margin, entries in window): A / B")
    for k, (a, b) in CRASH.items():
        w = R[(R.trade_date >= a) & (R.trade_date <= b)]
        out.append(f"  {k:10s} n {len(w):3d}  A {w.retA.sum():+.1f}  B {w.retB.sum():+.1f}  worst A {w.retA.min() if len(w) else np.nan:+.1f}")
    Y = R.groupby(R.trade_date.dt.year)[["retA", "retB"]].mean().round(2)
    out.append("\nper year mean % of margin:\n" + Y.T.to_string())
    m, t, h1, h2, yp, ny = res["A"]
    ok = t >= 3 and h1 > 0 and h2 > 0 and yp > ny / 2
    out.append(f"\nBAR (PRIMARY ARM A always-on): {'PASS' if ok else 'NOT MET'}")
    R.to_csv(REPO / "data/studies/always_on_index_put_2026-09-26.csv", index=False)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
