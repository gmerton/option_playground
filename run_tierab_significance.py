#!/usr/bin/env python3
"""
Test statistics for the IN-BOOK Tier A/B regime playbooks (2026-09-22; follow-up to the ledger-wide
multiple-testing correction, which found these in the book with NO t on file).

Configs = what the playbooks / strategy_registry / Friday screener actually trade, run through the SAME engines
with the 2026-09-08 cost model (net ROC on max loss):
  QQQ bull put, 20 DTE, 50% take, Friday entry (run_qqq_regime_put_sweep engine):
    Bearish_HighIV 0.25/0.15 no stop · Bullish_HighIV 0.45/0.35 2x stop · Bullish_LowIV 0.45/0.35 no stop
    (+ Bearish_LowIV 0.35/0.15 no stop, reported, not tiered)
  SPY bull put Bearish_HighIV 0.25/0.15 no stop, 20 DTE (same engine)
  SPX iron condor 45 DTE, 0.10-delta wings, 50% take / 2x stop (run_spx_strangle engine, --dump):
    Bullish_HighIV + above 200MA: call 0.20 / put 0.40 · Bearish_HighIV: call 0.20 / put 0.30
Statistic: trades overlap (weekly entries, 2-6 week holds), so t is on MONTHLY means of net ROC (entry month),
with a Newey-West (lag 2) variant for the adjacent-month overlap. Search size k for each cell = the sweep it was
picked from (QQQ/SPY: 7 short deltas x 4 wings x stop/no-stop ~= 52; SPX: 7x7 call/put deltas ~= 49), charged in
the ledger correction with Sidak.

Usage: AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src:. .venv/bin/python3 run_tierab_significance.py
"""
from __future__ import annotations
import subprocess, sys
from datetime import timedelta
from math import sqrt
import numpy as np, pandas as pd
import run_qqq_regime_put_sweep as S
from lib.studies.put_study import fetch_vix_data
from lib.studies.put_spread_study import build_put_spread_trades, find_put_spread_exits, compute_spread_metrics, add_ma_column

PUT_CELLS = [  # ticker, regime, short, wing, stop
    ("QQQ", "Bearish_HighIV", 0.25, 0.10, None),
    ("QQQ", "Bullish_HighIV", 0.45, 0.10, 2.0),
    ("QQQ", "Bullish_LowIV", 0.45, 0.10, None),
    ("QQQ", "Bearish_LowIV", 0.35, 0.20, None),
    ("SPY", "Bearish_HighIV", 0.25, 0.10, None),
]


def put_trades(ticker: str) -> dict:
    S.TICKER = ticker; S.SPLIT_DATES = S._SPLIT_DATES.get(ticker, []); S.DTE_TARGET = 20; S.DTE_TOL = 5
    vix = fetch_vix_data(S.START - timedelta(days=5), S.END)
    opts = S._load_options_cache(ticker, S.START, S.END + timedelta(days=30))
    stock = S._load_stock_cache(ticker)
    vlk = vix.set_index("trade_date")["vix_close"]
    out = {}
    for tk, reg, sd, ww, stop in PUT_CELLS:
        if tk != ticker: continue
        pos = build_put_spread_trades(opts, short_delta_target=sd, wing_delta_width=ww, dte_target=20, dte_tol=5,
                                      entry_weekday=4, split_dates=S.SPLIT_DATES, max_delta_err=0.08, max_spread_pct=None)
        pos["vix_on_entry"] = pos["entry_date"].map(vlk)
        pos = add_ma_column(pos, stock, S.MA_DAYS)
        pos = find_put_spread_exits(pos, opts, profit_take_pct=0.50, stop_multiple=stop)
        pos = compute_spread_metrics(pos)
        pos["regime"] = pos.apply(S.assign_regime, axis=1)
        c = pos[~pos.is_open & ~pos.split_flag & (pos.regime == reg)].copy()
        out[(tk, reg)] = pd.DataFrame({"entry": pd.to_datetime(c.entry_date), "roc_net": c.roc_net.astype(float),
                                       "roc_gross": c.roc.astype(float)})
    return out


def spx_trades(regime: str, call_d: float, put_d: float, ma200: bool) -> pd.DataFrame:
    cmd = [sys.executable, "run_spx_strangle.py", "--dte", "45", "--regime", regime, "--wing-delta", "0.10",
           "--dump", f"data/studies/_spx_{regime}.csv"] + (["--require-200ma"] if ma200 else [])
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    d = pd.read_csv(f"data/studies/_spx_{regime}.csv", parse_dates=["edate"])
    d = d[(d.call_delta.round(2) == call_d) & (d.put_delta.round(2) == put_d)]
    return pd.DataFrame({"entry": d.edate, "roc_net": d.roc_net.astype(float), "roc_gross": d.roc_gross.astype(float)})


def stats(d: pd.DataFrame) -> dict:
    m = d.groupby(d.entry.dt.to_period("M")).roc_net.mean()
    n = len(m); mu = m.mean(); sd = m.std(ddof=1)
    t_iid = mu / (sd / sqrt(n)) if n > 2 else np.nan
    # Newey-West lag 2 on the monthly series
    x = (m - mu).values; g0 = (x @ x) / n
    nw = g0 + sum(2 * (1 - L / 3) * (x[L:] @ x[:-L]) / n for L in (1, 2) if n > L)
    t_nw = mu / sqrt(nw / n) if nw > 0 else np.nan
    yr = d.groupby(d.entry.dt.year).roc_net.mean()
    top = d.groupby(d.entry.dt.year).size().max() / len(d)
    h1 = d[d.entry < "2022-07-01"].roc_net.mean(); h2 = d[d.entry >= "2022-07-01"].roc_net.mean()
    return dict(trades=len(d), months=n, mean_trade=100 * d.roc_net.mean(), gross=100 * d.roc_gross.mean(),
                win=100 * (d.roc_net > 0).mean(), month_mean=100 * mu, t_month=t_iid, t_nw=t_nw,
                h1=100 * h1, h2=100 * h2, yrs_pos=f"{(yr > 0).sum()}/{len(yr)}", top_year_share=100 * top,
                worst_trade=100 * d.roc_net.min())


rows = {}
for tk in ("QQQ", "SPY"):
    for key, d in put_trades(tk).items(): rows[f"{key[0]} bull put {key[1]}"] = d
rows["SPX condor Bullish_HighIV+200MA 0.20c/0.40p"] = spx_trades("Bullish_HighIV", 0.20, 0.40, True)
rows["SPX condor Bearish_HighIV 0.20c/0.30p"] = spx_trades("Bearish_HighIV", 0.20, 0.30, False)
T = pd.DataFrame({k: stats(v) for k, v in rows.items() if len(v) > 5}).T
pd.set_option("display.width", 250)
print(T.to_string(float_format=lambda x: f"{x:+.2f}"))
pd.concat([v.assign(cell=k) for k, v in rows.items()]).to_csv("data/studies/tierab_trades_2026-09-22.csv", index=False)
T.to_csv("data/studies/tierab_significance_2026-09-22.csv")
