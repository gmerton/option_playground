#!/usr/bin/env python3
"""
"QUIET FALLING KNIFE" LEAPs: cheap LEAP calls on a large cap whose volatility has gone to sleep while price sits LOW
in its multi-year range (pre-registered 2026-09-27, before any run; Gabe: "pre-register it and run it", prompted by
his Aug-Sep 2026 IBIT LEAP buys, which he saw as Tito's Sleeping Giants).

WHY NEW. Our Sleeping Giants detector (src/lib/sleeping_giants/detector.py; MARGINAL: 47% win, median -9%, mean +59%)
requires COILING = price in the TOP 20% of its multi-year range, and was built to EXCLUDE the "quiet falling knife"
(long base, price near the bottom). Gabe's IBIT entries passed the sleeping gate (ATR at a multi-year low) and failed
coiling (29-49% of range). The ledger's nulls on deep drawdowns (crash-leader veto, capitulation longs) were STOCK
returns; nothing has tested the convex version, a cheap LEAP bought when the drawdown has gone quiet.

UNIVERSE  the Sleeping Giants universe (77 large caps + sector ETFs + GLD/SLV; scripts/archive/run_sleeping_giants_
          backtest.py UNIVERSE). ⚠ survivor-biased large caps (conservative for a long-call test? no: survivors
          recovered, which FLATTERS buying low -- stated, and the same-date control shares the bias).
DETECTOR  analyze() on yfinance adjusted daily OHLC, point-in-time, weekly (every 5th session), 1,500-bar window,
          2014-01 -> 2025-06 (so a 180-day exit lands inside v3 bid/ask, which ends ~2026-03).
          LOW  (the tested arm) = sleeping AND can_wake AND base_len_ok AND pos_in_base <= 40   <- only coiling flipped
          TOP  (reference)      = the original is_sleeping_giant (pos_in_base >= 80)
          Consecutive firing weeks collapse into one EPISODE (gap > 60 calendar days = new episode); entry on the first
          firing date (arm A, "buy the setup").
VEHICLE   the call nearest 0.40 delta, expiry nearest 315 DTE within 200-450 (the SG pipeline's LEAP), from v3.
FILLS     buy at mid + 25% of the quoted spread + $0.0065/share; sell at mid - 25% of that day's spread + $0.0065.
EXIT      the first quote on/after +180 calendar days (the SG headline horizon). If quotes stop earlier: a contract whose
          quotes end > 45 days before expiry with a last mid > $0.10 is a split artefact -> excluded (counted);
          otherwise the last quote. Return = net P&L / net entry cost (ROC %).
CONTROL   (declared now) SAME-DATE: for each LOW episode, 3 other universe names drawn at random (seed 20260927) from
          those NOT in the LOW state that week, same LEAP rule and exit. excess = LOW ROC - mean(control ROC). Holds the
          date (market move, IV level) fixed; varies only "quiet and low in its base" vs a random large cap.
PRIMARY   mean excess ROC per LOW episode, t on signal-date cluster means (episodes sharing a date share controls).
          BAR: t >= 3, both halves (split 2020-01-01) positive, positive in a majority of years with episodes.
          The LEAP payoff is convex: report the MEDIAN excess and the win rate alongside; a mean carried by 1-2
          episodes is flagged, not certified.
REPORTED  LOW vs TOP on the same pipeline (does "low in the base" beat the original giant?); LOW's underlying stock
          return over the same 180 days vs control stock (is it the stock or the convexity?); per year; the top 3
          episodes' share of total; mid-priced (gross) numbers next to net.
PRIOR     low. Deep drawdowns didn't pay as stock in a healthy tape; a cheap LEAP adds convexity but also time decay.
Local vs cloud: yfinance + the detector sweep are local CPU (minutes); two Athena queries (LEAP pick, forward marks).

Run: AWS_PROFILE=clarinut-gmerton AWS_DEFAULT_REGION=us-west-2 PYTHONPATH=src:. .venv/bin/python3 run_quiet_knife_leaps.py
     (log -> data/studies/logs/quiet_knife_leaps.log)
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import awswrangler as wr
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts/archive"))
from lib.athena_lib import athena, _ensure_glue_db
from lib.constants import DB, TABLE, S3TABLES_CATALOG, GLUE_CATALOG, TMP_S3_PREFIX
from lib.sleeping_giants.detector import analyze
from run_sleeping_giants_backtest import UNIVERSE

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/quiet_knife_leaps.log"
OUT = REPO / "data/studies/quiet_knife_leaps_2026-09-27.csv"
T = f'"{S3TABLES_CATALOG}"."{DB}"."{TABLE}"'
START, END, SPLIT = "2014-01-01", "2025-06-30", "2020-01-01"
WINDOW, STEP, GAP_DAYS, LOW_MAX = 1500, 5, 60, 40.0
TARGET_DELTA, TARGET_DTE, DTE_MIN, DTE_MAX, HORIZON = 0.40, 315, 200, 450, 180
SLIP, COMM, N_CTRL = 0.25, 0.0065, 3


def log(m):
    print(m, file=sys.stderr, flush=True)


def sweep() -> pd.DataFrame:
    px = yf.download(UNIVERSE, start="2008-01-01", end="2025-07-15", auto_adjust=True, progress=False, group_by="ticker")
    rows = []
    for tk in UNIVERSE:
        try:
            d = px[tk].dropna()
        except KeyError:
            continue
        H, L, C, idx = d.High.values, d.Low.values, d.Close.values, d.index
        ev = [i for i in range(len(d)) if idx[i] >= pd.Timestamp(START) and idx[i] <= pd.Timestamp(END)][::STEP]
        for i in ev:
            lo = max(0, i - WINDOW + 1)
            r = analyze(list(H[lo:i + 1]), list(L[lo:i + 1]), list(C[lo:i + 1]))
            if r is None:
                continue
            base = r["sleeping"] and r["can_wake"] and r["base_len_ok"]
            rows.append(dict(ticker=tk, date=idx[i], low=bool(base and r["pos_in_base"] <= LOW_MAX),
                             top=bool(r["is_sleeping_giant"]), pos=r["pos_in_base"], close=C[i]))
        log(f"  swept {tk}")
    return pd.DataFrame(rows)


def episodes(S: pd.DataFrame, col: str) -> pd.DataFrame:
    f = S[S[col]].sort_values(["ticker", "date"])
    out = []
    for tk, g in f.groupby("ticker"):
        last = None
        for r in g.itertuples():
            if last is None or (r.date - last).days > GAP_DAYS:
                out.append(dict(ticker=tk, signal_date=r.date, pos=r.pos))
            last = r.date
    return pd.DataFrame(out)


def _tmp(df: pd.DataFrame, cols: list[str]) -> tuple[str, str]:
    name = f"tmp_qk_{uuid.uuid4().hex}"
    path = TMP_S3_PREFIX.rstrip("/") + f"/{name}/"
    w = df[cols].copy()
    for c in cols:
        if c in ("entry_date", "expiry"):
            w[c] = pd.to_datetime(w[c]).dt.date
    wr.s3.to_parquet(w, path=path, dataset=True, database=DB, table=name, mode="overwrite")
    return name, path


def pick_leaps(req: pd.DataFrame) -> pd.DataFrame:
    _ensure_glue_db(DB)
    name, path = _tmp(req, ["row_id", "ticker", "entry_date"])
    try:
        df = athena(f"""
        WITH cand AS (
          SELECT t.row_id, o.trade_date AS entry_date, o.expiry, o.ticker, o.strike, o.delta, o.bid, o.ask,
                 ABS(date_diff('day', o.expiry, date_add('day', {TARGET_DTE}, o.trade_date))) AS dte_err
          FROM {T} o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" t ON o.ticker = t.ticker AND o.trade_date = t.entry_date
          WHERE o.cp = 'C' AND o.bid > 0 AND o.ask > 0 AND o.delta IS NOT NULL
            AND date_diff('day', o.trade_date, o.expiry) BETWEEN {DTE_MIN} AND {DTE_MAX}),
        ranked AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY row_id ORDER BY ABS(delta - {TARGET_DELTA}), dte_err) rn FROM cand)
        SELECT row_id, entry_date, expiry, ticker, strike, delta, bid, ask FROM ranked WHERE rn = 1""")
    finally:
        wr.catalog.delete_table_if_exists(database=DB, table=name); wr.s3.delete_objects(path)
    for c in ("entry_date", "expiry"):
        df[c] = pd.to_datetime(df[c])
    return df


def marks(con: pd.DataFrame) -> pd.DataFrame:
    _ensure_glue_db(DB)
    name, path = _tmp(con, ["row_id", "ticker", "expiry", "strike", "entry_date"])
    try:
        df = athena(f"""
        SELECT c.row_id, o.trade_date, o.bid, o.ask
        FROM {T} o JOIN "{GLUE_CATALOG}"."{DB}"."{name}" c
          ON o.ticker = c.ticker AND o.expiry = c.expiry AND o.strike = c.strike AND o.cp = 'C'
        WHERE o.trade_date > c.entry_date AND o.trade_date <= c.expiry AND o.bid >= 0 AND o.ask > 0""")
    finally:
        wr.catalog.delete_table_if_exists(database=DB, table=name); wr.s3.delete_objects(path)
    df["trade_date"] = pd.to_datetime(df.trade_date)
    return df


def payoff(e, m: pd.DataFrame) -> dict | None:
    if m.empty:
        return None
    m = m.sort_values("trade_date")
    mid0, spr0 = (e.bid + e.ask) / 2, e.ask - e.bid
    cost_net, cost_gross = mid0 + SLIP * spr0 + COMM, mid0
    tgt = e.entry_date + pd.Timedelta(days=HORIZON)
    after = m[m.trade_date >= tgt]
    x = after.iloc[0] if len(after) else m.iloc[-1]
    mid1, spr1 = (x.bid + x.ask) / 2, x.ask - x.bid
    short = (e.expiry - m.trade_date.max()).days
    incomplete = bool(len(after) == 0 and short > 45 and mid1 > 0.10)
    return dict(exit_date=x.trade_date, roc_net=100 * ((max(mid1 - SLIP * spr1 - COMM, 0)) - cost_net) / cost_net,
                roc_gross=100 * (mid1 - cost_gross) / cost_gross, incomplete=incomplete, spr_pct=spr0 / mid0)


def main():
    log("sweeping detector...")
    S = sweep()
    E_low, E_top = episodes(S, "low"), episodes(S, "top")
    rng = np.random.default_rng(20260927)
    req = []
    for k, r in E_low.iterrows():
        req.append(dict(row_id=f"L{k}", arm="LOW", ep=f"L{k}", ticker=r.ticker, entry_date=r.signal_date))
        wk = S[(S.date == r.signal_date) & ~S.low & (S.ticker != r.ticker)].ticker.unique()
        for j, c in enumerate(rng.choice(wk, size=min(N_CTRL, len(wk)), replace=False)):
            req.append(dict(row_id=f"L{k}c{j}", arm="CTRL", ep=f"L{k}", ticker=c, entry_date=r.signal_date))
    for k, r in E_top.iterrows():
        req.append(dict(row_id=f"T{k}", arm="TOP", ep=f"T{k}", ticker=r.ticker, entry_date=r.signal_date))
    R = pd.DataFrame(req)
    log(f"episodes LOW {len(E_low)}, TOP {len(E_top)}; LEAP requests {len(R)}")
    Lp = pick_leaps(R)
    M = marks(Lp)
    rows = []
    for e in Lp.itertuples():
        p = payoff(e, M[M.row_id == e.row_id])
        if p:
            rows.append(dict(row_id=e.row_id, ticker=e.ticker, entry_date=e.entry_date, strike=e.strike, delta=e.delta, **p))
    P = R.merge(pd.DataFrame(rows), on=["row_id", "ticker"], how="inner", suffixes=("", "_x"))
    n_inc = int(P.incomplete.sum()); P = P[~P.incomplete]
    # stock returns over the same window (adjusted)
    px = yf.download(sorted(P.ticker.unique()), start="2013-06-01", end="2026-04-30", auto_adjust=True, progress=False)["Close"]
    P["stock"] = [100 * (px[t].asof(x) / px[t].asof(d) - 1) if t in px else np.nan
                  for t, d, x in zip(P.ticker, P.entry_date, P.exit_date)]
    P.to_csv(OUT, index=False)
    out = [f"# Quiet-falling-knife LEAPs (pre-registration in the docstring)",
           f"sweep evals {len(S):,}; episodes LOW {len(E_low)} ({E_low.ticker.nunique()} names), TOP {len(E_top)}; "
           f"priced LEAPs {len(P)} (split-artefact exclusions {n_inc}); median entry spread {100 * P.spr_pct.median():.1f}% of mid"]
    for arm in ("LOW", "TOP", "CTRL"):
        x = P[P.arm == arm]
        out.append(f"  {arm:4s} n {len(x):3d}  net ROC mean {x.roc_net.mean():+.1f}% median {x.roc_net.median():+.1f}% "
                   f"win {100 * (x.roc_net > 0).mean():.0f}% | gross mean {x.roc_gross.mean():+.1f}% | stock {x.stock.mean():+.1f}%")
    lo = P[P.arm == "LOW"].set_index("ep"); ct = P[P.arm == "CTRL"].groupby("ep")[["roc_net", "stock"]].mean()
    J = lo.join(ct, rsuffix="_c", how="inner")
    J["ex"] = J.roc_net - J.roc_net_c; J["ex_stock"] = J.stock - J.stock_c
    g = J.groupby("entry_date").ex.mean()
    t = g.mean() / g.std(ddof=1) * np.sqrt(len(g)) if len(g) > 2 else np.nan
    h = J.entry_date < SPLIT
    yr = J.groupby(J.entry_date.dt.year).ex.mean()
    top3 = J.ex.nlargest(3).sum() / J.ex.sum() if J.ex.sum() > 0 else np.nan
    out.append(f"\nPRIMARY LOW - same-date control: n {len(J)} episodes / {len(g)} dates  mean {J.ex.mean():+.1f}pp  "
               f"median {J.ex.median():+.1f}pp  win {100 * (J.ex > 0).mean():.0f}%  t {t:+.2f}  halves "
               f"{J[h].ex.mean():+.1f} / {J[~h].ex.mean():+.1f}  yrs+ {(yr > 0).sum()}/{len(yr)}  top-3 share {top3:.2f}")
    out.append(f"  stock excess over the same window: mean {J.ex_stock.mean():+.1f}pp median {J.ex_stock.median():+.1f}pp")
    out.append("  per year excess: " + " ".join(f"{y}:{v:+.0f}" for y, v in yr.items()))
    out.append("  LOW episodes: " + ", ".join(f"{r.ticker} {r.entry_date.date()} {r.roc_net:+.0f}% (ctrl {r.roc_net_c:+.0f})"
                                              for r in J.sort_values("entry_date").itertuples()))
    ok = t >= 3 and J[h].ex.mean() > 0 and J[~h].ex.mean() > 0 and (yr > 0).sum() > len(yr) / 2
    out.append(f"\nBAR: {'PASS' if ok else 'NOT MET'}")
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
