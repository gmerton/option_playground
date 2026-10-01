#!/usr/bin/env python3
"""
LEAPs as the leverage vehicle for the CERTIFIED 12-1 momentum sleeve (pre-registered 2026-09-30, BEFORE any run).

QUESTION (an implementation question, not a discovery): momentum certified on 2026-09-30 (replication track). To earn
more on an ~$80k account the sleeve needs more exposure per dollar. Is a deep-ITM ~1-year call on each momentum name
a cheaper way to get that exposure than holding the shares on margin? Options carry spread, time value and IV; margin
carries interest. Measure which costs less on the SAME names and months.

FORMATION exactly the certified PRIMARY (run_momentum_portfolio.portfolio): survivorship-free chain_spot (incl.
          delisted), liquidity = 50d mean option volume >= 1,000 and px >= $5, top decile by close(t-21)/close(t-252),
          monthly, formations 2011-01 -> 2026-01.
LEAP ARM  per name at the month-end it ENTERS the decile: buy the call nearest 0.80 delta with expiry nearest 365 DTE
          in [270, 500] (silver.options_daily_v3, bid > 0, ask > 0) at mid + 25% of spread + $0.0065/sh. Hold while the
          name stays in the decile; ROLL (sell, buy a fresh pick) at a month-end where the held call has < 180 DTE; SELL
          at mid - 25% - $0.0065 when the name leaves. Intermediate month-ends marked at mid. Equal premium dollars per
          name; monthly book return = mean of per-name option returns.
CONTROL   LEVERED STOCK on the same name-months: stock return (adjusted chain_spot) x L, L = delta x raw spot / premium
          at the month's start (the call's dollar delta per premium dollar, same units: raw strikes vs raw spot), minus
          financing (L - 1) x (3-month T-bill + 1.5%) / 12 (~ IBKR margin), minus 10 bp x L per side on entries/exits.
          It holds the names, months and exposure fixed and varies only the vehicle.
PRIMARY   monthly LEAP book - LEVERED-STOCK book (paired months), Newey-West t (lag 3), halves split 2018-01, per year.
          DECISION RULE (declared now): LEAPs are the leverage vehicle iff the gap is >= -0.25pp/month (~3%/yr) AND not
          significantly negative (t > -2). Otherwise margin is the cheaper leverage.
REPORTED  median L; the LEAP book's own return vs the unlevered momentum book and SPY; spread cost as % of premium;
          share of name-months dropped (no month-end quote for the held call: splits / delistings / missing prints --
          dropped from BOTH arms, paired); max drawdown of each book; worst 5 months.
Caveats   v3 bid/ask ends ~2026-03 (window ends 2026-01). Dividends: the call forgoes them, the levered stock earns
          them (adjusted closes) -- part of the vehicle's honest cost. Early exercise ignored.
Local: two batched Athena pulls (picks + month-end marks), then pandas; minutes.

Run: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_momentum_leap_leverage.py
     (log -> data/studies/logs/momentum_leap_leverage.log)
"""
from __future__ import annotations

import sys
import uuid
import warnings
from pathlib import Path

import awswrangler as wr
import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)

import run_dip_survivorship as DS
import run_momentum_portfolio as MP
import run_quiet_knife_leaps as qk
from lib.athena_lib import athena, _ensure_glue_db
from lib.constants import DB, GLUE_CATALOG, TMP_S3_PREFIX

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/momentum_leap_leverage.log"
CACHE = REPO / "data/cache/momentum_leap"
TARGET_DELTA, TARGET_DTE, DTE_MIN, DTE_MAX, ROLL_DTE = 0.80, 365, 270, 500, 180
SLIP, COMM, STOCK_COST, MARGIN_SPREAD = 0.25, 0.0065, 0.0010, 0.015


def log(m):
    print(m, file=sys.stderr, flush=True)


def formations(C, liq):
    """[(a, b, set_of_names)] for the certified PRIMARY."""
    idx = C.index
    Cv, E = C.values, liq.values
    me = [i for i in MP.month_ends(idx) if pd.Timestamp(MP.START) <= idx[i] <= pd.Timestamp(MP.END)]
    out = []
    for a, b in zip(me[:-1], me[1:]):
        if a - 252 < 0:
            continue
        score = Cv[a - 21] / Cv[a - 252] - 1
        ok = E[a] & np.isfinite(score) & np.isfinite(Cv[a])
        if ok.sum() < 50:
            continue
        names = np.flatnonzero(ok)
        cut = np.nanquantile(score[names], 0.9)
        out.append((a, b, set(C.columns[names[score[names] >= cut]])))
    return out


def tmp_table(df: pd.DataFrame) -> tuple[str, str]:
    name = f"tmp_ml_{uuid.uuid4().hex}"
    path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
    w = df.copy()
    for c in w.columns:
        if c in ("entry_date", "expiry", "trade_date"):
            w[c] = pd.to_datetime(w[c]).dt.date
    wr.s3.to_parquet(w, path=path, dataset=True, database=DB, table=name, mode="overwrite")
    return name, path


def pull_picks(req: pd.DataFrame) -> pd.DataFrame:
    f = CACHE / "picks.parquet"
    if f.exists():
        return pd.read_parquet(f)
    qk.TARGET_DELTA, qk.TARGET_DTE, qk.DTE_MIN, qk.DTE_MAX = TARGET_DELTA, TARGET_DTE, DTE_MIN, DTE_MAX
    df = qk.pick_leaps(req)
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_parquet(f, index=False)
    return df


def pull_marks(con: pd.DataFrame, dates: list) -> pd.DataFrame:
    f = CACHE / "marks.parquet"
    if f.exists():
        return pd.read_parquet(f)
    _ensure_glue_db(DB)
    name, path = tmp_table(con[["ticker", "expiry", "strike", "entry_date"]].drop_duplicates())
    dl = ",".join(f"DATE '{pd.Timestamp(d).date()}'" for d in dates)
    try:
        df = athena(f"""
        SELECT o.ticker, o.expiry, o.strike, o.trade_date, o.bid, o.ask, o.delta
        FROM {qk.T} o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" c
          ON o.ticker = c.ticker AND o.expiry = c.expiry AND o.strike = c.strike AND o.cp = 'C'
        WHERE o.trade_date > c.entry_date AND o.trade_date <= c.expiry AND o.trade_date IN ({dl})
          AND o.bid >= 0 AND o.ask > 0""")
    finally:
        wr.catalog.delete_table_if_exists(database=DB, table=name)
        wr.s3.delete_objects(path)
    for c in ("trade_date", "expiry"):
        df[c] = pd.to_datetime(df[c])
    df = df.drop_duplicates(["ticker", "expiry", "strike", "trade_date"])
    df.to_parquet(f, index=False)
    return df


def tbill_monthly(idx) -> pd.Series:
    ir = yf.download("^IRX", start="2010-01-01", end="2026-03-01", progress=False)["Close"].squeeze() / 100
    return ir.groupby(ir.index.to_period("M")).last().reindex(idx).ffill().fillna(0.0)


def main():
    d = DS.pull()
    C, V = DS.adjust_and_clean(d)
    raw = d.pivot_table(index="trade_date", columns="ticker", values="spot").sort_index().reindex_like(C)
    liq = ((V.rolling(50, min_periods=30).mean() >= MP.OPTVOL_MIN) & (C >= MP.PX_MIN)).fillna(False)
    F = formations(C, liq)
    idx = C.index
    log(f"formations {len(F)}")
    req = pd.DataFrame([(i, tk, idx[a]) for i, (a, b, S) in enumerate(F) for tk in sorted(S)],
                       columns=["fi", "ticker", "entry_date"])
    req["row_id"] = np.arange(len(req))
    picks = pull_picks(req[["row_id", "ticker", "entry_date"]])
    picks = picks.merge(req[["row_id", "fi"]], on="row_id")
    log(f"picks {len(picks):,} of {len(req):,} requests")
    mdates = [idx[b] for (_, b, _) in F]
    marks = pull_marks(picks, mdates)
    log(f"marks {len(marks):,}")
    mk = marks.set_index(["ticker", "expiry", "strike", "trade_date"])
    pk = picks.set_index(["fi", "ticker"])
    rf = tbill_monthly(pd.PeriodIndex([idx[b].to_period("M") for (_, b, _) in F]))

    held: dict[str, dict] = {}
    rows, drops, spreads = [], 0, []
    for fi, (a, b, S) in enumerate(F):
        da, db = idx[a], idx[b]
        nxt = F[fi + 1][2] if fi + 1 < len(F) else set()
        lev, stk = [], []
        for tk in sorted(S):
            h = held.get(tk)
            new = h is None or (h["expiry"] - da).days < ROLL_DTE
            if new:
                if (fi, tk) not in pk.index:
                    held.pop(tk, None); drops += 1; continue
                p = pk.loc[(fi, tk)]
                mid, spr = (p.bid + p.ask) / 2, p.ask - p.bid
                v0, delta0 = mid + SLIP * spr + COMM, p.delta
                spreads.append(spr / mid)
                h = dict(expiry=p.expiry, strike=p.strike)
                held[tk] = h
                entry_cost = 0.0                                   # option cost already in v0
            else:
                q = mk.loc[(tk, h["expiry"], h["strike"], da)] if (tk, h["expiry"], h["strike"], da) in mk.index else None
                if q is None:
                    held.pop(tk, None); drops += 1; continue
                v0, delta0 = (q.bid + q.ask) / 2, q.delta
            key = (tk, h["expiry"], h["strike"], db)
            if key not in mk.index or not np.isfinite(C.at[db, tk]) or not np.isfinite(C.at[da, tk]):
                held.pop(tk, None); drops += 1; continue
            q1 = mk.loc[key]
            leaving = tk not in nxt or (h["expiry"] - db).days < ROLL_DTE
            v1 = max((q1.bid + q1.ask) / 2 - SLIP * (q1.ask - q1.bid) - COMM, 0.0) if leaving else (q1.bid + q1.ask) / 2
            if not (np.isfinite(v0) and v0 > 0 and np.isfinite(delta0)):
                held.pop(tk, None); drops += 1; continue
            L = delta0 * raw.at[da, tk] / v0
            r_opt = v1 / v0 - 1
            r_stk = C.at[db, tk] / C.at[da, tk] - 1
            fin = (L - 1) * (rf.iloc[fi] + MARGIN_SPREAD) / 12
            tc = STOCK_COST * L * ((1 if new else 0) + (1 if leaving else 0))
            lev.append(r_opt)
            stk.append(dict(L=L, r=L * r_stk - fin - tc, r1=r_stk))
            if leaving:
                held.pop(tk, None)
        if lev:
            s = pd.DataFrame(stk)
            rows.append(dict(month=db.to_period("M"), leap=np.mean(lev), levstock=s.r.mean(), stock=s.r1.mean(),
                             L=s.L.median(), n=len(lev)))
    R = pd.DataFrame(rows).set_index("month")
    spy = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet", columns=["date", "ticker", "close"])
    spy = spy[spy.ticker == "SPY"].assign(date=lambda x: pd.to_datetime(x.date)).set_index("date").close.sort_index()
    spy_m = spy.groupby(spy.index.to_period("M")).last().pct_change().reindex(R.index)
    gap = (R.leap - R.levstock) * 100
    h1 = gap.index < pd.Period(MP.SPLIT, "M")
    yr = gap.groupby(gap.index.year).sum()

    def dd(r):
        c = (1 + r.clip(lower=-0.99)).cumprod()
        return 100 * (1 - c / c.cummax()).max()
    L = ["# Momentum sleeve: LEAPs vs levered stock (pre-registration in the docstring)",
         f"{len(R)} months; median names/month {R.n.median():.0f}; dropped name-months {drops:,} (both arms); "
         f"median entry spread {100 * np.median(spreads):.1f}% of mid; median L {R.L.median():.2f}",
         f"monthly means: LEAP book {100 * R.leap.mean():+.2f}% | levered stock {100 * R.levstock.mean():+.2f}% | "
         f"unlevered momentum stock {100 * R.stock.mean():+.2f}% | SPY {100 * spy_m.mean():+.2f}%",
         f"max drawdown: LEAP {dd(R.leap):.1f}% | levered stock {dd(R.levstock):.1f}% | stock {dd(R.stock):.1f}%",
         f"\nPRIMARY LEAP - levered stock: {gap.mean():+.2f}pp/mo  t_NW {MP.nw_t(gap):+.2f}  halves {gap[h1].mean():+.2f} / "
         f"{gap[~h1].mean():+.2f}  years + {(yr > 0).sum()}/{len(yr)}",
         "per year (pp, summed): " + " ".join(f"{y}:{v:+.1f}" for y, v in yr.items()),
         "worst 5 months LEAP: " + ", ".join(f"{m}: {100 * v:+.1f}%" for m, v in R.leap.nsmallest(5).items())]
    ok = gap.mean() >= -0.25 and MP.nw_t(gap) > -2
    L.append(f"DECISION: {'LEAPs are an acceptable leverage vehicle' if ok else 'margin is the cheaper leverage'}")
    R.to_csv(REPO / "data/studies/logs/momentum_leap_leverage_months.csv")
    print("\n".join(L))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
