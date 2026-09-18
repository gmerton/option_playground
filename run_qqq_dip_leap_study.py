#!/usr/bin/env python3
"""
"Buy a QQQ LEAP every time QQQ closes down >= 1%" -- tested against buying the same LEAP on any day.

Set before running:
  Entry     at the close of the signal day. Contract: expiry nearest 450 DTE (360-600), delta nearest 0.50 / 0.70 /
            0.80. Buy at mid + 25% of spread + $0.0065/share.
  Exit      after 63 / 126 / 252 trading days at mid - 25% of spread (zero if the bid is zero), quote from the exit
            date or the last one within the 5 prior trading days. Entries whose exit falls after 2026-02-27 (end
            of bid/ask) are dropped; unpriceable exits are counted and reported, never assumed.
  Arms      every trading day (benchmark) · down >= 1% (the rule) · down >= 2% · all other days.
  Compare   QQQ shares (total return) over the same window, and "delta-levered shares": delta x S / premium
            times QQQ's price move, floored at -100%. LEAP minus levered shares = what the option structure
            itself (theta, vol paid, convexity) added.
  Stats     t clustered by entry month (entries overlap heavily). Pooled lift = the rule as traded.
            Within-month lift = buying on the down day instead of another day the same month (timing only).
            Bar |t| >= 3; 2022 entries must not be worse than the benchmark.

Usage:
  PYTHONPATH=src .venv/bin/python3 run_qqq_dip_leap_study.py > data/studies/qqq_dip_leap_study_2026-09-17.log
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yfinance as yf

pd.set_option("display.width", 250)
COST = 0.0065
QUOTE_END = pd.Timestamp("2026-02-27")
HOLDS = (63, 126, 252)

raw = yf.download("QQQ", start="2010-06-01", end="2026-09-17", auto_adjust=False, progress=False)
raw.index = pd.to_datetime(raw.index).tz_localize(None)
S = raw["Close"].squeeze()               # QQQ has not split since 2000: split-adjusted close = raw price
TR = raw["Adj Close"].squeeze()          # total return for the share benchmark
days = S.index
ret1 = S.pct_change() * 100

E = pd.read_parquet("data/cache/qqq_dip_leap/entries.parquet")
Pth = pd.read_parquet("data/cache/qqq_dip_leap/paths.parquet")
for d in (E, Pth):
    d["trade_date"] = pd.to_datetime(d.trade_date)
    d["expiry"] = pd.to_datetime(d.expiry)
Pth = Pth.sort_values("trade_date")
quotes = {k: g.set_index("trade_date")[["bid", "ask"]] for k, g in Pth.groupby(["expiry", "strike"])}


def exit_px(expiry, strike, when):
    q = quotes.get((expiry, strike))
    if q is None:
        return np.nan
    pos = days.get_loc(when)
    window = days[max(0, pos - 5):pos + 1]
    q = q.loc[q.index.isin(window)]
    if q.empty:
        return np.nan
    b, a = q.iloc[-1].bid, q.iloc[-1].ask
    if not (b > 0):
        return 0.0
    return max((b + a) / 2 - 0.25 * (a - b) - COST, 0.0)


rows = []
for dcol, dlab in (("d50", 0.50), ("d70", 0.70), ("d80", 0.80)):
    ent = E[E[dcol]].drop_duplicates("trade_date")
    for r in ent.itertuples(index=False):
        if r.trade_date not in days:
            continue
        pos = days.get_loc(r.trade_date)
        entry = (r.bid + r.ask) / 2 + 0.25 * (r.ask - r.bid) + COST
        for h in HOLDS:
            if pos + h >= len(days):
                continue
            xd = days[pos + h]
            if xd > QUOTE_END or xd >= r.expiry:
                continue
            xp = exit_px(r.expiry, r.strike, xd)
            s0, s1 = S.iloc[pos], S.iloc[pos + h]
            lev = r.delta * s0 / entry
            rows.append(dict(trade_date=r.trade_date, delta_t=dlab, hold=h, delta=r.delta, dte=r.dte, iv=r.iv,
                             entry=entry, exit=xp, ret=100 * (xp / entry - 1) if pd.notna(xp) else np.nan,
                             qqq_tr=100 * (TR.iloc[pos + h] / TR.iloc[pos] - 1),
                             lev_shares=max(100 * lev * (s1 / s0 - 1), -100.0), day_ret=ret1.iloc[pos]))
T = pd.DataFrame(rows)
T["down1"] = (T.day_ret <= -1).astype(int)
T["down2"] = (T.day_ret <= -2).astype(int)
T["month"] = T.trade_date.dt.to_period("M").astype(str)
T["year"] = T.trade_date.dt.year
missing = T.ret.isna()
print(f"entries x holds: {len(T):,}; exits unpriceable: {int(missing.sum())} ({100*missing.mean():.2f}%) -> dropped")
print("   unpriceable share by arm:", T.groupby("down1").ret.apply(lambda s: round(100 * s.isna().mean(), 2)).to_dict())
T = T[~missing].copy()
T["vs_lev"] = T.ret - T.lev_shares
T.to_parquet("data/cache/qqq_dip_leap/trades.parquet", index=False)


def tstat(x, col):
    s = x.groupby("month")[col].mean()
    return s.mean() / s.std() * np.sqrt(len(s)) if len(s) > 2 else np.nan


def arm_stats(x):
    return dict(n=len(x), months=x.month.nunique(), mean=x.ret.mean(), median=x.ret.median(),
                win=100 * (x.ret > 0).mean(), worst=x.ret.min(), t=tstat(x, "ret"),
                qqq_tr=x.qqq_tr.mean(), lev_shares=x.lev_shares.mean(), leap_minus_lev=x.vs_lev.mean(),
                iv=100 * x.iv.mean(), y2022=x[x.year == 2022].ret.mean())


def lift(x, var, y="ret"):
    z = x[[y, var, "month"]].copy()
    z["g"] = pd.factorize(z.month)[0]
    m = smf.ols(f"{y} ~ {var}", z).fit(cov_type="cluster", cov_kwds={"groups": z.g})
    z["y_dm"] = z[y] - z.groupby("month")[y].transform("mean")
    z["v_dm"] = z[var] - z.groupby("month")[var].transform("mean")
    m2 = smf.ols("y_dm ~ v_dm - 1", z).fit(cov_type="cluster", cov_kwds={"groups": z.g})
    return (f"pooled {m.params[var]:+.2f} (t {m.tvalues[var]:+.2f}) | "
            f"within-month {m2.params['v_dm']:+.2f} (t {m2.tvalues['v_dm']:+.2f})")


for (dl, h), x in T.groupby(["delta_t", "hold"]):
    print(f"\n{'#'*96}\n# {dl:.2f}-delta LEAP (~450 DTE), hold {h} trading days | entries "
          f"{x.trade_date.min().date()} -> {x.trade_date.max().date()}\n{'#'*96}")
    arms = {"every day (benchmark)": x, "down >= 1% (the rule)": x[x.down1 == 1],
            "down >= 2%": x[x.down2 == 1], "all other days": x[x.down1 == 0]}
    print(pd.DataFrame({k: arm_stats(v) for k, v in arms.items()}).T.round(2).to_string())
    print(f"  rule vs other days, LEAP return:        {lift(x, 'down1')}")
    print(f"  rule vs other days, LEAP minus levered: {lift(x, 'down1', 'vs_lev')}")
    print(f"  rule vs other days, entry IV:           {lift(x.assign(ivp=100 * x.iv), 'down1', 'ivp')}")
    yr = pd.DataFrame({"every day": x.groupby("year").ret.mean(), "rule": x[x.down1 == 1].groupby("year").ret.mean(),
                       "rule n": x[x.down1 == 1].groupby("year").size(), "qqq_tr": x.groupby("year").qqq_tr.mean()})
    print("  by entry year (mean LEAP return %):")
    print(yr.round(1).to_string())
