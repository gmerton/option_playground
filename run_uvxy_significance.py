#!/usr/bin/env python3
"""
UVXY combined strategy with costs + a test statistic (2026-09-22; follow-up to the ledger-wide correction, where
UVXY had no t on file yet carried the largest registry allocation, $10,000).

Playbook config (uvxy_strategy_playbook.md): Friday entry, ~20 DTE (+/-5), bear call spread 0.50/0.40 always,
naked short put 0.40 when VIX < 20, 50% profit take, no stop, short-leg bid-ask <= 25% of mid, 2018-01-12 on,
trades spanning a UVXY reverse split excluded. Same engines as run_uvxy_combined_sweep.py.
Costs (lib.studies.costs, the 2026-09-08 model): $0.0065/share/leg/side + 25% of each leg's entry bid-ask, entry
and any traded exit (expiry settles free).
Per-entry combined ROC = 0.5 x spread ROC + 0.5 x put ROC when the put fires, else the spread ROC (the playbook's
equal-capital blend). Spread ROC on max loss, put ROC on Reg-T margin (0.20 x strike + premium).
t on MONTHLY means (weekly entries overlap), Newey-West lag 2 alongside. Search: the playbook cell was picked from
the 5 x 4 x 7 = 140-triplet sweep in run_uvxy_combined_sweep.py -> k = 140 in the ledger correction.

Usage: AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 run_uvxy_significance.py
"""
from __future__ import annotations
from datetime import date
from math import sqrt
import numpy as np, pandas as pd
from run_uvxy_combined_sweep import load_data, UVXY_START, DTE_TARGET, DTE_TOL, PUT_VIX_MAX
from lib.studies.straddle_study import UVXY_SPLIT_DATES
from lib.studies.call_spread_study import build_call_spread_trades, find_spread_exits, compute_spread_metrics
from lib.studies.put_study import build_put_trades, find_exits as find_put_exits, compute_put_metrics
from lib.studies.costs import leg_cost

END = date(2026, 2, 20)   # option history (bid/ask) ends here
opts, vix = load_data(UVXY_START, END, refresh=False)
vlk = vix.set_index("trade_date")["vix_close"]

sp = build_call_spread_trades(opts, short_delta_target=0.50, wing_delta_width=0.10, dte_target=DTE_TARGET, dte_tol=DTE_TOL,
                              entry_weekday=4, split_dates=UVXY_SPLIT_DATES, max_spread_pct=0.25)
sp = compute_spread_metrics(find_spread_exits(sp, opts))
sp = sp[~sp.split_flag & ~sp.is_open & (pd.to_datetime(sp.entry_date) <= pd.Timestamp(END))].copy()
traded = ~sp.exit_type.isin(("expiry", "missing"))
sp_cost = (leg_cost(sp.short_ask - sp.short_bid, traded) + leg_cost(sp.long_ask - sp.long_bid, traded)) * 100
sp["roc_net"] = (sp.net_pnl - sp_cost) / sp.max_loss.clip(lower=0.01)

pu = build_put_trades(opts, delta_target=0.40, dte_target=DTE_TARGET, dte_tol=DTE_TOL, entry_weekday=4,
                      split_dates=UVXY_SPLIT_DATES, max_spread_pct=0.25)
pu["vix_on_entry"] = pu.entry_date.map(vlk)
pu = compute_put_metrics(find_put_exits(pu, opts))
pu = pu[~pu.split_flag & ~pu.is_open & (pu.vix_on_entry.isna() | (pu.vix_on_entry < PUT_VIX_MAX))].copy()
ptraded = ~pu.exit_type.isin(("expiry", "missing"))
pu_cost = leg_cost(pu.put_entry_ask - pu.put_entry_bid, ptraded) * 100
pu["roc_net"] = (pu.short_pnl - pu_cost) / pu.margin_reg_t

m = sp[["entry_date", "roc", "roc_net"]].rename(columns={"roc": "sp_gross", "roc_net": "sp_net"}).merge(
    pu[["entry_date", "roc", "roc_net"]].rename(columns={"roc": "pu_gross", "roc_net": "pu_net"}), on="entry_date", how="left")
m["entry"] = pd.to_datetime(m.entry_date)
has = m.pu_net.notna()
m["comb_net"] = np.where(has, 0.5 * m.sp_net + 0.5 * m.pu_net, m.sp_net)
m["comb_gross"] = np.where(has, 0.5 * m.sp_gross + 0.5 * m.pu_gross, m.sp_gross)


def stats(d: pd.DataFrame, col: str) -> dict:
    d = d.dropna(subset=[col])
    mm = d.groupby(d.entry.dt.to_period("M"))[col].mean(); n = len(mm); mu = mm.mean()
    t = mu / (mm.std(ddof=1) / sqrt(n))
    x = (mm - mu).values; g0 = x @ x / n
    nw = g0 + sum(2 * (1 - L / 3) * (x[L:] @ x[:-L]) / n for L in (1, 2))
    yr = d.groupby(d.entry.dt.year)[col].mean()
    return dict(trades=len(d), months=n, mean=100 * d[col].mean(), month_mean=100 * mu, t_month=t, t_nw=mu / sqrt(nw / n),
                win=100 * (d[col] > 0).mean(), h1=100 * d[d.entry < "2022-01-01"][col].mean(), h2=100 * d[d.entry >= "2022-01-01"][col].mean(),
                yrs_pos=f"{(yr > 0).sum()}/{len(yr)}", worst=100 * d[col].min(), by_year={y: round(100 * v, 1) for y, v in yr.items()})


pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
sp_d = m.rename(columns={"sp_net": "x"}); pu_d = m[has].rename(columns={"pu_net": "x"})
T = pd.DataFrame({
    "combined (net)": stats(m, "comb_net"), "combined (gross)": stats(m, "comb_gross"),
    "call spread leg (net)": stats(m, "sp_net"), "short put leg (net, VIX<20)": stats(m[has], "pu_net"),
}).T
print(T.drop(columns="by_year").to_string(float_format=lambda x: f"{x:+.2f}"))
print("\nby year, combined net %:", T.loc["combined (net)", "by_year"])
print("by year, put leg net %:", T.loc["short put leg (net, VIX<20)", "by_year"])
print(f"cost per trade: spread {sp_cost.mean():.1f}$/ct on max loss {sp.max_loss.mean():.0f}$; put {pu_cost.mean():.1f}$/ct on margin {pu.margin_reg_t.mean():.0f}$")
m.to_csv("data/studies/uvxy_significance_trades_2026-09-22.csv", index=False)
T.drop(columns="by_year").to_csv("data/studies/uvxy_significance_2026-09-22.csv")
