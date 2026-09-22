#!/usr/bin/env python3
"""Long-straddle tenor study (2026-09-21): does the 7-DTE edge survive at 8, 9, 10 and 11 DTE?

With weekly (Friday) expiries, the tenor IS the entry weekday: Fri -> next Friday = 7 DTE, Thu = 8, Wed = 9,
Tue = 10, Mon = 11. Every arm buys the ATM straddle (call delta nearest 0.50 on the entry day) on the
Friday expiry of the FOLLOWING week and holds it to expiry (no stop: the stop studies of 2026-09-20 showed
every stop costs money).

Gates are computed on each arm's OWN entry day, exactly as the playbook does on Friday:
  FVR   fvr_put_30_90 >= 1.20                        (silver.fwd_vol_daily)
  IVpct iv_put_10 ranked vs the name's own prior 252 readings <= 30 (shifted one row: no look-ahead)
Universe = the 317 tickers of the Friday study file (data/cache/straddle_recenter/straddle_gated.parquet).
Min entry mid $0.50 (same as the Friday study).

Pricing = house cost model (run_straddle_recenter_sim.py): buy at mid + 25% of the bid-ask on each leg +
$0.0065/sh/leg; expiry settles at |S_T - K|, S_T from expiry-day put-call parity at the strike with the
smallest |C - P| mid. Also reported at mid (gross) and at the full ask.

Stages (each cached under data/cache/straddle_dte/):
  gates    fwd_vol_daily -> gates.parquet (every ticker-day, both gates)
  pull     options_daily_v3 entry-day + expiry-day chains for every gate-passing candidate, by year
  sim      -> trades.parquet
  report   -> tables (printed; paste into data/studies/straddle_dte_study_2026-09-21.md)
Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_straddle_dte_study.py [gates|pull|sim|report|all]
"""
from __future__ import annotations

import glob
import os
import sys
import time
import uuid
from datetime import timedelta

import numpy as np
import pandas as pd

sys.path.insert(0, "src")

DIR = "data/cache/straddle_dte"
FRIDAY_FILE = "data/cache/straddle_recenter/straddle_gated.parquet"
FVR_GATE, IVPCT_GATE, MIN_MID = 1.20, 30.0, 0.50
SLIP, COMM = 0.25, 0.0065
DTE_BY_DOW = {4: 7, 3: 8, 2: 9, 1: 10, 0: 11}          # pandas dayofweek: Mon=0 .. Fri=4
os.makedirs(DIR, exist_ok=True)


def _q(sql: str) -> pd.DataFrame:
    import awswrangler as wr
    return wr.athena.read_sql_query(sql=sql, database="silver", workgroup="dev-v3", s3_output="s3://athena-919061006621/")


# ---------------------------------------------------------------- gates
def gates() -> pd.DataFrame:
    out = f"{DIR}/gates.parquet"
    if os.path.exists(out):
        return pd.read_parquet(out)
    tk = sorted(pd.read_parquet(FRIDAY_FILE).ticker.unique())
    p = _q(f"""SELECT ticker, trade_date, fvr_put_30_90, iv_put_10 FROM silver.fwd_vol_daily
               WHERE ticker IN ({",".join(f"'{t}'" for t in tk)}) AND iv_put_10 > 0""")
    p["trade_date"] = pd.to_datetime(p.trade_date)
    p = p.sort_values(["ticker", "trade_date"]).drop_duplicates(["ticker", "trade_date"])
    # identical to run_straddle_rebuild_wf.load(): rank vs the prior 252 readings, min 60
    p["iv_pct"] = p.groupby("ticker").iv_put_10.transform(lambda s: s.shift(1).rolling(252, min_periods=60).rank(pct=True) * 100)
    p = p.dropna(subset=["iv_pct", "fvr_put_30_90"])
    p["pass_fvr"] = p.fvr_put_30_90 >= FVR_GATE
    p["pass_iv"] = p.iv_pct <= IVPCT_GATE
    p["dow"] = p.trade_date.dt.dayofweek
    p.to_parquet(out, index=False)
    return p


def candidates() -> pd.DataFrame:
    g = gates()
    c = g[g.pass_fvr & g.pass_iv & g.dow.isin(DTE_BY_DOW)].copy()
    c["dte"] = c.dow.map(DTE_BY_DOW)
    c["exp_hi"] = c.trade_date + pd.to_timedelta(c.dte, unit="D")          # the Friday of next week
    c["exp_lo"] = c.exp_hi - timedelta(days=1)                               # holiday Friday -> Thursday expiry
    c = c.reset_index(drop=True)
    c["row_id"] = c.index.astype("int64")
    return c


# ---------------------------------------------------------------- pull
def pull() -> None:
    import awswrangler as wr
    from lib.athena_lib import _drop_temp_targets_table, _ensure_glue_db, athena
    from lib.constants import DB, GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX
    c = candidates()
    print("gate-passing candidates by DTE:", c.dte.value_counts().sort_index().to_dict(), flush=True)
    tg = c[["row_id", "ticker", "trade_date", "exp_lo", "exp_hi"]].rename(columns={"trade_date": "entry_date"})
    for col in ("entry_date", "exp_lo", "exp_hi"):
        tg[col] = tg[col].dt.date
    tg["yr"] = pd.to_datetime(tg.entry_date).dt.year
    os.makedirs(f"{DIR}/chains", exist_ok=True)
    _ensure_glue_db(DB)
    for yr, t in tg.groupby("yr"):
        out = f"{DIR}/chains/chains_{yr}.parquet"
        if os.path.exists(out):
            print(yr, "cached", flush=True)
            continue
        t0 = time.time()
        name = f"tmp_targets_{uuid.uuid4().hex}"
        path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
        wr.s3.to_parquet(df=t.drop(columns="yr"), path=path, dataset=True, database=DB, table=name, compression="snappy",
                         mode="overwrite", dtype={"row_id": "bigint", "ticker": "string", "entry_date": "date",
                                                  "exp_lo": "date", "exp_hi": "date"})
        try:
            # entry day: the whole chain of that expiry (ATM is picked by delta locally)
            # expiry day: the whole chain (parity settle); strikes are trimmed locally
            d = athena(f"""
            SELECT t.row_id, o.trade_date, o.expiry, o.cp, o.strike, o.bid, o.ask, o.delta
            FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t
              ON o.ticker = t.ticker AND o.expiry BETWEEN t.exp_lo AND t.exp_hi
             AND (o.trade_date = t.entry_date OR o.trade_date = o.expiry)
            WHERE o.trade_date BETWEEN DATE '{yr}-01-01' AND DATE '{yr + 1}-01-31'""")
        finally:
            _drop_temp_targets_table(DB, name, path)
        d.to_parquet(out, index=False)
        print(f"{yr}: {len(d):,} rows, {d.row_id.nunique():,} of {len(t):,} trades, {time.time() - t0:.0f}s", flush=True)


# ---------------------------------------------------------------- sim
def sim() -> pd.DataFrame:
    c = candidates().set_index("row_id")
    P = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{DIR}/chains/chains_*.parquet"))], ignore_index=True)
    P["trade_date"] = pd.to_datetime(P.trade_date)
    P["expiry"] = pd.to_datetime(P.expiry)
    P = P[(P.ask > 0) & (P.bid >= 0) & (P.ask >= P.bid) & (P.ask < 9999)]
    P["mid"] = (P.bid + P.ask) / 2
    P["ba"] = P.ask - P.bid
    P = P.sort_values("ba").drop_duplicates(["row_id", "trade_date", "expiry", "cp", "strike"], keep="first")
    rows, skip = [], {}
    for rid, d in P.groupby("row_id", sort=False):
        m = c.loc[rid]
        exp = d.expiry.max()                                   # Friday if listed, else the Thursday holiday expiry
        d = d[d.expiry == exp]
        e, x = d[d.trade_date == m.trade_date], d[d.trade_date == exp]
        why = None
        ce, pe = e[e.cp == "C"].set_index("strike"), e[e.cp == "P"].set_index("strike")
        ks = ce.index.intersection(pe.index)
        if not len(ks) or ce.loc[ks].delta.isna().all():
            why = "no entry chain"
        cx, px = x[x.cp == "C"].set_index("strike"), x[x.cp == "P"].set_index("strike")
        kx = cx.index.intersection(px.index)
        if why is None and not len(kx):
            why = "no expiry chain"
        if why:
            skip[why] = skip.get(why, 0) + 1
            continue
        ce, pe = ce.loc[ks], pe.loc[ks]
        K = (ce.delta - 0.5).abs().idxmin()
        mid = ce.loc[K, "mid"] + pe.loc[K, "mid"]
        if mid < MIN_MID:
            skip["mid < 0.50"] = skip.get("mid < 0.50", 0) + 1
            continue
        ba = ce.loc[K, "ba"] + pe.loc[K, "ba"]
        cost = mid + SLIP * ba + 2 * COMM
        ask = ce.loc[K, "ask"] + pe.loc[K, "ask"] + 2 * COMM
        cx, px = cx.loc[kx], px.loc[kx]
        k0 = (cx.mid - px.mid).abs().idxmin()
        ST = k0 + cx.loc[k0, "mid"] - px.loc[k0, "mid"]
        pay = abs(ST - K)
        rows.append(dict(row_id=rid, ticker=m.ticker, entry_date=m.trade_date, expiry=exp, dte=int(m.dte),
                         real_dte=(exp - m.trade_date).days, strike=K, spot_exp=ST, entry_mid=mid, ba_pct=ba / mid,
                         ret_mid=(pay - mid) / mid, ret=(pay - cost) / cost, ret_ask=(pay - ask) / ask,
                         fvr=m.fvr_put_30_90, iv_pct=m.iv_pct))
    R = pd.DataFrame(rows)
    R.to_parquet(f"{DIR}/trades.parquet", index=False)
    print(f"simulated {len(R):,} trades; skipped {skip}")
    return R


# ---------------------------------------------------------------- report
def _clus_t(x: pd.Series, by: pd.Series) -> float:
    """t on per-DATE means (trades on one date share the market move): the honest effective n."""
    m = x.groupby(by).mean()
    return m.mean() / (m.std(ddof=1) / np.sqrt(len(m))) if len(m) > 2 and m.std() > 0 else np.nan


def report() -> None:
    R = pd.read_parquet(f"{DIR}/trades.parquet")
    R["yr"] = R.entry_date.dt.year
    R["pct"] = R.ret * 100
    pd.set_option("display.width", 220)
    print(f"\ntrades {len(R):,}, {R.entry_date.min():%Y-%m-%d} -> {R.entry_date.max():%Y-%m-%d}")
    print("\n== A. Each arm gated on its own entry day, hold to expiry (returns in % of premium) ==")
    rows = []
    for dte, g in R.groupby("dte"):
        cap = g.pct.clip(upper=g.pct.quantile(0.999))
        rows.append(dict(dte=dte, n=len(g), dates=g.entry_date.nunique(), names=g.ticker.nunique(),
                         mid=g.ret_mid.mean() * 100, real_fill=g.pct.mean(), full_ask=g.ret_ask.mean() * 100,
                         t_dates=_clus_t(g.pct, g.entry_date), trim_0_1pct=cap.mean(), median=g.pct.median(),
                         win=(g.ret > 0).mean() * 100, ba_med=g.ba_pct.median() * 100))
    print(pd.DataFrame(rows).round(2).to_string(index=False))

    print("\n== B. By year, real fill (mean %; n) ==")
    y = R.pivot_table(index="yr", columns="dte", values="pct", aggfunc="mean").round(1)
    yn = R.pivot_table(index="yr", columns="dte", values="pct", aggfunc="size")
    print(y.to_string()); print("years positive:", (y > 0).sum().to_dict())
    print("n by year:\n" + yn.to_string())

    print("\n== C. Paired vs Friday: same ticker, same expiry, both days passed the gates ==")
    f = R[R.dte == 7].set_index(["ticker", "expiry"])
    rows = []
    for dte in (8, 9, 10, 11):
        o = R[R.dte == dte].set_index(["ticker", "expiry"])
        j = o[["pct", "entry_date"]].join(f[["pct"]], rsuffix="_fri", how="inner")
        dif = j.pct - j.pct_fri
        rows.append(dict(dte=dte, pairs=len(j), expiries=j.index.get_level_values(1).nunique(),
                         early=j.pct.mean(), friday=j.pct_fri.mean(), diff=dif.mean(),
                         t_expiry=_clus_t(dif.reset_index(drop=True), pd.Series(j.index.get_level_values(1))),
                         diff_median=dif.median(), share_of_other_arm=len(j) / len(o) * 100))
    print(pd.DataFrame(rows).round(2).to_string(index=False))

    print("\n== D. Right tail: share of the arm's total P&L from its top 1% of trades ==")
    for dte, g in R.groupby("dte"):
        s = g.pct.sort_values(ascending=False)
        top = s.head(max(1, len(s) // 100)).sum()
        print(f"  {dte:2d} DTE  total {s.sum():,.0f}pp  top-1% {top:,.0f}pp  = {top / s.sum() * 100 if s.sum() else float('nan'):.0f}%  "
              f"without top 1%: {s.iloc[len(s) // 100:].mean():+.2f}%/trade")

    print("\n== E. Halves by date (stability) ==")
    days = sorted(R.entry_date.unique()); cut = days[len(days) // 2]
    R["half"] = np.where(R.entry_date < cut, "A", "B")
    print(R.pivot_table(index="dte", columns="half", values="pct", aggfunc="mean").round(2).to_string())


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("gates", "all"):
        g = gates(); print(f"gates: {len(g):,} ticker-days")
    if step in ("pull", "all"):
        pull()
    if step in ("sim", "all"):
        sim()
    if step in ("report", "all"):
        report()
