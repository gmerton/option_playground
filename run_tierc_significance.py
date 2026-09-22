#!/usr/bin/env python3
"""
Cost + test-statistic check for every remaining non-regime credit spread in the Friday screener (2026-09-22;
after UVXY and UVIX both turned net-negative once the spread cost was charged).

Each strategy is run EXACTLY as the screener entry defines it (ticker, put/call, short/long delta, DTE target,
VIX condition, profit take, 25% short-leg bid-ask gate, Friday entries, no stop), through the house engines
(put_spread_study / call_spread_study), with the 2026-09-08 cost model ($0.0065/share/leg/side + 25% of each leg's
entry bid-ask on entry and on any traded exit; expiry settles free). Option history ends 2026-02-20.
ROC on max loss. t on MONTHLY means (weekly entries overlap), Newey-West lag 2 alongside; halves split at the
sample's middle date. k = the sweep the cell was picked from in ticker_config.py (side deltas x wings x VIX
levels), for the ledger correction. Not covered: the screener's vrp_min gate on TLT / GEV (live-only input), and
the UUP ATM short straddle (different engine).

Usage: AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src:. .venv/bin/python3 run_tierc_significance.py
"""
from __future__ import annotations
from datetime import date, timedelta
from math import sqrt
import numpy as np, pandas as pd
import run_friday_screener as F
from lib.mysql_lib import fetch_options_cache
from lib.studies.ticker_config import TICKER_CONFIG
from lib.studies.put_study import fetch_vix_data
from lib.studies.put_spread_study import build_put_spread_trades, find_put_spread_exits, compute_spread_metrics as put_metrics
from lib.studies.call_spread_study import build_call_spread_trades, find_spread_exits, compute_spread_metrics as call_metrics
from lib.studies.costs import leg_cost

END = date(2026, 2, 20)
VIX = fetch_vix_data(date(2015, 12, 1), END).set_index("trade_date")["vix_close"]


def run(st: dict) -> pd.DataFrame:
    tk = st["ticker"]; cfg = TICKER_CONFIG.get(tk, {})
    start = cfg.get("start", date(2018, 1, 1)); splits = cfg.get("split_dates", []) or []
    dte = st.get("dte_target", F.DTE_TARGET); tol = max(F.DTE_TOL, dte // 4)
    opts = fetch_options_cache(tk, start, END + timedelta(days=dte + tol + 5))
    if opts is None or opts.empty: return pd.DataFrame()
    wing = round(st["short_delta"] - st["long_delta"], 2)
    kw = dict(short_delta_target=st["short_delta"], wing_delta_width=wing, dte_target=dte, dte_tol=tol,
              entry_weekday=4, split_dates=splits, max_spread_pct=F.MAX_SPREAD_PCT)
    if st["cp"] == "put":
        pos = build_put_spread_trades(opts, max_delta_err=F.MAX_DELTA_ERR, **kw)
        if pos.empty: return pos
        pos = put_metrics(find_put_spread_exits(pos, opts, profit_take_pct=st.get("profit_take", 0.5), stop_multiple=None))
    else:
        pos = build_call_spread_trades(opts, **kw)
        if pos.empty: return pos
        pos = call_metrics(find_spread_exits(pos, opts, profit_take_pct=st.get("profit_take", 0.5)))
        traded = ~pos.exit_type.isin(("expiry", "missing"))
        cost = (leg_cost(pos.short_ask - pos.short_bid, traded) + leg_cost(pos.long_ask - pos.long_bid, traded)) * 100
        pos["roc_net"] = (pos.net_pnl - cost) / pos.max_loss.clip(lower=0.01)
        pos["cost_per_share"] = cost / 100
    pos = pos[~pos.split_flag & ~pos.is_open].copy()
    pos["entry"] = pd.to_datetime(pos.entry_date)
    pos = pos[pos.entry <= pd.Timestamp(END)]
    vc = st.get("vix_cond")
    if vc:
        v = pos.entry_date.map(VIX)
        pos = pos[(v < vc[1]) if vc[0] == "lt" else (v >= vc[1])]
    return pos


def stats(d: pd.DataFrame) -> dict:
    mm = d.groupby(d.entry.dt.to_period("M")).roc_net.mean(); n = len(mm); mu = mm.mean()
    t = mu / (mm.std(ddof=1) / sqrt(n)) if n > 2 else np.nan
    x = (mm - mu).values; g0 = x @ x / n
    nw = g0 + sum(2 * (1 - L / 3) * (x[L:] @ x[:-L]) / n for L in (1, 2) if n > L)
    mid = d.entry.min() + (d.entry.max() - d.entry.min()) / 2
    yr = d.groupby(d.entry.dt.year).roc_net.mean()
    credit = d.net_credit_mid if "net_credit_mid" in d else pd.Series(np.nan, index=d.index)
    return dict(trades=len(d), months=n, first=d.entry.min().date(), gross=100 * d.roc.mean(), net=100 * d.roc_net.mean(),
                month_net=100 * mu, t=t, t_nw=mu / sqrt(nw / n) if nw > 0 else np.nan,
                win_gross=100 * (d.roc > 0).mean(), win_net=100 * (d.roc_net > 0).mean(),
                h1=100 * d[d.entry < mid].roc_net.mean(), h2=100 * d[d.entry >= mid].roc_net.mean(),
                yrs_pos=f"{(yr > 0).sum()}/{len(yr)}", credit_med=credit.median(),
                cost_med=d.cost_per_share.median() if "cost_per_share" in d else np.nan)


def k_of(st: dict) -> int:
    c = TICKER_CONFIG.get(st["ticker"], {})
    deltas = c.get("put_deltas" if st["cp"] == "put" else "short_deltas") or [0] * 5
    return len(deltas) * len(c.get("wing_widths") or [0] * 3) * len(c.get("vix_thresholds") or [None])


rows, trades = {}, []
for st in F.STRATEGIES:
    if st["type"] != "spread": continue
    print(f"... {st['name']}", flush=True)
    try:
        d = run(st)
    except Exception as e:
        print(f"    failed: {type(e).__name__}: {e}"); continue
    if len(d) < 10:
        print(f"    only {len(d)} trades"); continue
    r = stats(d); r["k"] = k_of(st); r["tier_was"] = F.TIER_MAP.get(st["name"]); rows[st["name"]] = r
    trades.append(d[["entry", "roc", "roc_net"]].assign(strategy=st["name"]))
T = pd.DataFrame(rows).T
pd.set_option("display.width", 260)
print(T.to_string(float_format=lambda x: f"{x:+.2f}"))
T.to_csv("data/studies/tierc_significance_2026-09-22.csv")
pd.concat(trades).to_csv("data/studies/tierc_trades_2026-09-22.csv", index=False)
