#!/usr/bin/env python3
"""
Momentum-skew vertical backtest (oquants strategy #3) — 2026-09-16.

Their rule: skew z <= -1.5 in the momentum direction -> buy the 45-60 delta option, sell the 10-25 delta wing,
same expiry, 7-21 DTE, hold to expiry, close before earnings. Claim: +23% mean return on debit at a ~32% win rate
(from a GBM simulation, which assumes the lognormal distribution their own thesis says is wrong -- see
data/oquants/posts/momentum-skew-strategy.md).

This prices it on real quotes:
  signal expiry = the one nearest 14 DTE; skew = (ATM IV - 25 delta IV)/ATM IV per wing, z-scored against that
  ticker's own trailing 252 days (min 120 obs); momentum from data/cache/liquid_panel_2019.parquet -- 126-day
  return, its cross-sectional decile that day, its sign, and the ratio to SPY's.
  Entry cost = mid + 25% of the bid-ask + $0.0065/share on each leg (the house model).
  Settlement = intrinsic at expiry from a put-call-parity spot on the SAME unadjusted basis as the strikes.
Every gated cell is reported against the ungated control on the same universe and dates.

Usage: PYTHONPATH=src .venv/bin/python3 run_skew_vertical_sim.py [--z -1.5] [--out ...]
"""
from __future__ import annotations
import argparse, glob, sys
from pathlib import Path
import numpy as np, pandas as pd

C = Path("data/cache/skew_vertical"); SLIP, COMM = 0.25, 0.0065
SIG_DTE = 14; LONG_D, SHORT_D = 0.525, 0.175
MOM_LB = 126; Z_WIN, Z_MIN = 252, 120


def daily_features() -> pd.DataFrame:
    """One row per ticker-day: parity spot, ATM/25d IVs, both skews, and the signal expiry."""
    fs = sorted(glob.glob(str(C / "skew_*.parquet")))
    out = []
    for f in fs:
        d = pd.read_parquet(f)
        d["trade_date"] = pd.to_datetime(d.trade_date); d["expiry"] = pd.to_datetime(d.expiry)
        d["mid"] = (d.bid + d.ask) / 2; d["ba"] = d.ask - d.bid; d["iv"] = (d.bid_iv + d.ask_iv) / 2
        d["dte"] = (d.expiry - d.trade_date).dt.days
        # signal expiry per ticker-day = nearest SIG_DTE
        pick = (d.assign(err=(d.dte - SIG_DTE).abs())
                  .sort_values("err").drop_duplicates(["ticker", "trade_date"])[["ticker", "trade_date", "expiry"]])
        g = d.merge(pick, on=["ticker", "trade_date", "expiry"])
        cal = g[g.cp == "C"]; put = g[g.cp == "P"]
        # parity spot: strike where |C-P| is smallest
        m = cal.merge(put, on=["ticker", "trade_date", "expiry", "strike"], suffixes=("_c", "_p"))
        if m.empty: continue
        m["gap"] = (m.mid_c - m.mid_p).abs()
        sp = m.sort_values("gap").drop_duplicates(["ticker", "trade_date"])
        sp = sp.assign(spot=sp.strike + sp.mid_c - sp.mid_p)[["ticker", "trade_date", "expiry", "spot"]]
        def near(df, target, col):
            x = df.assign(e=(df.delta - target).abs()).sort_values("e").drop_duplicates(["ticker", "trade_date"])
            return x[["ticker", "trade_date", "iv"]].rename(columns={"iv": col})
        atm = pd.concat([near(cal, 0.50, "iv_atm_c"), near(put, -0.50, "iv_atm_p")], axis=0)
        atm = (atm.groupby(["ticker", "trade_date"])[["iv_atm_c", "iv_atm_p"]].mean()
                  .mean(axis=1).rename("iv_atm").reset_index())
        f_ = (sp.merge(atm, on=["ticker", "trade_date"])
                .merge(near(cal, 0.25, "iv_c25"), on=["ticker", "trade_date"], how="left")
                .merge(near(put, -0.25, "iv_p25"), on=["ticker", "trade_date"], how="left"))
        out.append(f_)
        print(f"  {Path(f).name}: {len(f_):,} ticker-days", flush=True)
    F = pd.concat(out, ignore_index=True)
    F["skew_c"] = (F.iv_atm - F.iv_c25) / F.iv_atm
    F["skew_p"] = (F.iv_atm - F.iv_p25) / F.iv_atm
    F = F.sort_values(["ticker", "trade_date"])
    for s in ("skew_c", "skew_p"):
        g = F.groupby("ticker")[s]
        F[f"z_{s[-1]}"] = (F[s] - g.transform(lambda x: x.rolling(Z_WIN, min_periods=Z_MIN).mean())) / \
                          g.transform(lambda x: x.rolling(Z_WIN, min_periods=Z_MIN).std())
    return F


def momentum() -> pd.DataFrame:
    p = pd.read_parquet("data/cache/liquid_panel_2019.parquet")
    p["date"] = pd.to_datetime(p.date)
    cl = p.pivot_table(index="date", columns="ticker", values="close")
    ret = cl / cl.shift(MOM_LB) - 1
    spy = ret["SPY"] if "SPY" in ret else ret.mean(axis=1)
    dec = ret.rank(axis=1, pct=True).mul(10).apply(np.ceil).clip(1, 10)
    M = (ret.stack().rename("ret126").to_frame()
           .join(dec.stack().rename("decile"))
           .join(ret.div(spy, axis=0).stack().rename("relmom")).reset_index())
    M.columns = ["trade_date", "ticker", "ret126", "decile", "relmom"]
    return M


def build(F: pd.DataFrame, z_gate: float) -> pd.DataFrame:
    """Price both wings' verticals on every ticker-day that can form them (gating happens afterwards)."""
    fs = sorted(glob.glob(str(C / "skew_*.parquet")))
    spot = F.set_index(["ticker", "trade_date"]).spot
    rows = []
    for f in fs:
        d = pd.read_parquet(f)
        d["trade_date"] = pd.to_datetime(d.trade_date); d["expiry"] = pd.to_datetime(d.expiry)
        d["mid"] = (d.bid + d.ask) / 2; d["ba"] = d.ask - d.bid
        d = d.merge(F[["ticker", "trade_date", "expiry"]], on=["ticker", "trade_date", "expiry"])
        for cp, sgn in (("C", 1), ("P", -1)):
            x = d[d.cp == cp]
            lo = x.assign(e=(x.delta - sgn * LONG_D).abs()).sort_values("e").drop_duplicates(["ticker", "trade_date"])
            sh = x.assign(e=(x.delta - sgn * SHORT_D).abs()).sort_values("e").drop_duplicates(["ticker", "trade_date"])
            j = lo.merge(sh, on=["ticker", "trade_date", "expiry"], suffixes=("_l", "_s"))
            j = j[(j.strike_l - j.strike_s) * sgn < 0]                       # long is the nearer-the-money strike
            debit = (j.mid_l + SLIP * j.ba_l + COMM) - (j.mid_s - SLIP * j.ba_s - COMM)
            width = (j.strike_s - j.strike_l) * sgn
            k = j.assign(cp=cp, debit=debit, width=width)
            k = k[(k.debit > 0.01) & (k.width > 0) & (k.debit < k.width)]
            rows.append(k[["ticker", "trade_date", "expiry", "cp", "strike_l", "strike_s", "debit", "width",
                           "delta_l", "delta_s", "ba_l", "ba_s"]])
    T = pd.concat(rows, ignore_index=True)
    T["S_exp"] = [spot.get((t, e), np.nan) for t, e in zip(T.ticker, T.expiry)]
    T = T.dropna(subset=["S_exp"])
    itm = np.where(T.cp == "C", T.S_exp - T.strike_l, T.strike_l - T.S_exp)
    T["payoff"] = np.clip(itm, 0, T.width)
    T["pnl"] = T.payoff - T.debit
    T["roc"] = 100 * T.pnl / T.debit
    return T


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--z", type=float, default=-1.5)
    ap.add_argument("--out", default=str(C / "results.parquet")); a = ap.parse_args()
    print("daily features...", flush=True); F = daily_features()
    print(f"  {len(F):,} ticker-days, {F.ticker.nunique()} tickers, "
          f"{F.trade_date.min().date()} -> {F.trade_date.max().date()}", flush=True)
    print("building spreads...", flush=True); T = build(F, a.z)
    T = T.merge(F[["ticker", "trade_date", "z_c", "z_p", "iv_atm", "spot"]], on=["ticker", "trade_date"], how="left")
    T = T.merge(momentum(), on=["ticker", "trade_date"], how="left")
    E = pd.read_parquet("data/cache/calendar_path/earnings.parquet"); E["edate"] = pd.to_datetime(E.edate)
    by = {t: g.edate.values for t, g in E.groupby("ticker")}
    T["earn_before_exp"] = [bool(((by.get(t, np.array([], dtype="datetime64[ns]")) > np.datetime64(d)) &
                                  (by.get(t, np.array([], dtype="datetime64[ns]")) <= np.datetime64(e))).any())
                            for t, d, e in zip(T.ticker, T.trade_date, T.expiry)]
    T["z"] = np.where(T.cp == "C", T.z_c, T.z_p)
    T["gate_skew"] = T.z <= a.z
    T["gate_mom"] = np.where(T.cp == "C", (T.decile >= 8) & (T.ret126 > 0) & (T.relmom > 1),
                                          (T.decile <= 3) & (T.ret126 < 0) & (T.relmom < 1))
    T["gate_all"] = T.gate_skew & T.gate_mom & ~T.earn_before_exp
    T.to_parquet(a.out, index=False)
    print(f"wrote {a.out}: {len(T):,} priced verticals", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
