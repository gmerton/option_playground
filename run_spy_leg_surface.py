#!/usr/bin/env python3
"""
SPY LEG-RETURN SURFACE, step 1 of the vol-selling structure search (pre-registered 2026-09-28, before any run).

WHY. Any option structure's P&L is the weighted sum of its legs' P&L, so no structure can carry more expected return
than its legs. Step 1 measures where the premium lives, leg by leg, at real fills; step 2 (a CVaR-constrained
optimiser over these legs) is NOT part of this script and waits on reading the surface.

PRE-REGISTRATION (frozen before the first run)
  Data      data/cache/spy_chain_v3/ (run_spy_chain_v3_pull.py): SPY puts + calls, DTE 0-70, 2010-01 -> 2026-03.
            Settlement = SPY's raw close on the expiry date (last close on or before it; SPY never split).
  Entry     every trading day t, at t's EOD quote. For each leg cell:
              type    put / call
              delta   |delta| centres 0.05 0.10 0.16 0.20 0.25 0.30 0.40 0.50 (tolerance +/-0.015 at 0.05, else +/-0.025)
              DTE     targets 1 [1-2], 7 [5-9], 14 [11-17], 30 [25-35], 45 [40-50]  (0DTE excluded)
            the expiry in the window closest to the target, then the strike with |delta| nearest the centre; bid > 0.
  Trade     SELL one contract, hold to expiry (no management -- keeps legs additive).
            gross credit = mid; net credit = mid - 25% x (ask - bid) - $0.0065/share (house cost model, no exit cost
            at expiry). P&L = credit - intrinsic at settlement. Units: bp of SPY at entry (additive across legs of
            equal notional); also premium kept = P&L / mid.
  States    (known at t's close) ALL; STRESS = SPY close < 50 SMA AND VIX >= 20 (the certified regime); CALM = not
            STRESS; GAMMA+ / GAMMA- = sign of SPY net dealer GEX (run_gex_regime_pin.gex_series, the certified
            mechanism; data ends 2026-02).
  Stats     per cell: n entries, months, mean net and gross bp, EVENT-WEIGHTED mean with MONTH-CLUSTERED SE (daily
            entries overlap), halves (split 2018-01-01), share of years positive, worst month.
  Bar       this is a MAP, not a strategy test. A cell is called "premium after costs" only if net t clears Sidak over
            its family: ALL = 80 cells -> |t| >= 3.42; each conditional state = 80 cells x 4 states -> |t| >= 3.84;
            AND both halves positive. Everything else is descriptive.
  Caveats   ~11 stress episodes carry the tail; short tenors have depth only from ~2016 (reported as years covered);
            SPY is American (early assignment ignored); 2008 is not in v3.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_spy_leg_surface.py > data/studies/logs/spy_leg_surface.log
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
CH = Path("data/cache/spy_chain_v3")
SPLIT = pd.Timestamp("2018-01-01")
DELTAS = [0.05, 0.10, 0.16, 0.20, 0.25, 0.30, 0.40, 0.50]
DTES = {1: (1, 2), 7: (5, 9), 14: (11, 17), 30: (25, 35), 45: (40, 50)}
SLIP, COMM = 0.25, 0.0065
T_ALL, T_COND = 3.42, 3.84


def spy_close() -> pd.Series:
    import yfinance as yf
    s = yf.download("SPY", start="2009-09-01", end="2026-05-01", progress=False, auto_adjust=False)["Close"].squeeze()
    s.index = pd.to_datetime(s.index).normalize()
    return s.dropna()


def vix_close() -> pd.Series:
    v = pd.read_parquet("data/cache/vix_daily_long.parquet")
    v = v.set_index(pd.to_datetime(v.trade_date)).vix_close
    if v.index.max() < pd.Timestamp("2026-03-31"):
        import yfinance as yf
        y = yf.download("^VIX", start="2008-01-01", end="2026-05-01", progress=False, auto_adjust=False)["Close"].squeeze()
        y.index = pd.to_datetime(y.index).normalize()
        v = y.combine_first(v)
    return v.sort_index()


def select(df: pd.DataFrame) -> pd.DataFrame:
    df = df[(df.bid > 0) & (df.ask >= df.bid) & df.delta.notna()].copy()
    df["dte"] = (df.expiry - df.trade_date).dt.days
    df["ad"] = df.delta.abs()
    out = []
    for tgt, (lo, hi) in DTES.items():
        x = df[(df.dte >= lo) & (df.dte <= hi)].copy()
        if x.empty:
            continue
        x["dd"] = (x.dte - tgt).abs()
        best = x.groupby(["trade_date", "cp"]).dd.transform("min")
        x = x[x.dd == best]
        # tie on distance: keep the earlier expiry
        first = x.groupby(["trade_date", "cp"]).expiry.transform("min")
        x = x[x.expiry == first]
        for c in DELTAS:
            tol = 0.015 if c == 0.05 else 0.025
            y = x[(x.ad - c).abs() <= tol].copy()
            if y.empty:
                continue
            y["err"] = (y.ad - c).abs()
            y = y.sort_values("err").drop_duplicates(["trade_date", "cp"])
            y["dcen"], y["dtgt"] = c, tgt
            out.append(y)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def clus(x: pd.Series, m: pd.Series):
    d = pd.DataFrame(dict(x=x.values, m=m.values)).dropna()
    if len(d) < 20:
        return np.nan, np.nan
    mu = d.x.mean(); g = d.groupby("m").x; s, n = g.sum(), g.size()
    se = np.sqrt(((s - n * mu) ** 2).sum()) / n.sum()
    return mu, (mu / se if se > 0 else np.nan)


def main():
    S = spy_close()
    vix = vix_close()
    sma50 = S.rolling(50).mean()
    stress = ((S < sma50) & (vix.reindex(S.index).ffill() >= 20))
    import run_gex_regime_pin as gp
    _, net, _ = gp.gex_series("SPY", pd.DataFrame({"close": S}))
    gsign = np.sign(net)

    frames = []
    for f in sorted(CH.glob("*.parquet")):
        frames.append(select(pd.read_parquet(f)))
        print(f"  selected {f.stem}: {len(frames[-1]):,}", flush=True)
    E = pd.concat(frames, ignore_index=True)
    last = S.index.max()
    E = E[E.expiry <= last]
    settle_idx = S.index.searchsorted(E.expiry.values, side="right") - 1
    E["S_T"] = S.values[settle_idx]
    E["S_0"] = S.reindex(E.trade_date).values
    E = E.dropna(subset=["S_0", "S_T"])
    E["mid"] = (E.bid + E.ask) / 2
    E["ba"] = E.ask - E.bid
    E["pay"] = np.where(E.cp == "P", (E.strike - E.S_T).clip(lower=0), (E.S_T - E.strike).clip(lower=0))
    E["pnl_g"] = E.mid - E.pay
    E["pnl_n"] = E.mid - SLIP * E.ba - COMM - E.pay
    E["bp_g"] = E.pnl_g / E.S_0 * 1e4
    E["bp_n"] = E.pnl_n / E.S_0 * 1e4
    E["kept"] = E.pnl_n / E.mid
    E["m"] = E.trade_date.dt.to_period("M")
    E["stress"] = stress.reindex(E.trade_date).values.astype(bool)
    E["gamma"] = gsign.reindex(E.trade_date).values
    print(f"\nentries {len(E):,}, {E.trade_date.min().date()} -> {E.trade_date.max().date()}, "
          f"stress share of days {E.drop_duplicates('trade_date').stress.mean():.1%}")

    states = {"ALL": E, "STRESS": E[E.stress], "CALM": E[~E.stress],
              "GAMMA+": E[E.gamma > 0], "GAMMA-": E[E.gamma < 0]}
    rows = []
    for st, X in states.items():
        for (cp, dt, dc), g in X.groupby(["cp", "dtgt", "dcen"]):
            mu, t = clus(g.bp_n, g.m)
            mug, tg = clus(g.bp_g, g.m)
            yr = g.groupby(g.trade_date.dt.year).bp_n.mean()
            mo = g.groupby("m").bp_n.mean()
            h1, h2 = g[g.trade_date < SPLIT].bp_n.mean(), g[g.trade_date >= SPLIT].bp_n.mean()
            bar = T_ALL if st == "ALL" else T_COND
            rows.append(dict(state=st, cp=cp, dte=dt, delta=dc, n=len(g), months=g.m.nunique(),
                             yrs=f"{g.trade_date.dt.year.min()}-{g.trade_date.dt.year.max() % 100:02d}",
                             gross_bp=mug, net_bp=mu, t_net=t, t_gross=tg, h1=h1, h2=h2,
                             yrs_pos=(yr > 0).mean(), worst_mo=mo.min(), kept=g.kept.median(),
                             ba_pct_mid=(g.ba / g.mid).median(),
                             PREMIUM=bool(np.isfinite(t) and t >= bar and h1 > 0 and h2 > 0)))
    T = pd.DataFrame(rows)
    T.to_csv("data/studies/spy_leg_surface_2026-09-28.csv", index=False)
    E.drop(columns=["m"]).to_parquet("data/cache/spy_leg_surface_entries.parquet", index=False)

    for st in states:
        X = T[T.state == st]
        print(f"\n===== {st}: net bp of notional per short contract, hold to expiry (t_net in brackets; * = clears the bar) =====")
        for cp in ("P", "C"):
            piv = X[X.cp == cp].pivot(index="delta", columns="dte", values="net_bp")
            tt = X[X.cp == cp].pivot(index="delta", columns="dte", values="t_net")
            ok = X[X.cp == cp].pivot(index="delta", columns="dte", values="PREMIUM")
            cell = piv.round(1).astype(str) + " (" + tt.round(1).astype(str) + ")" + ok.replace({True: "*", False: ""}).astype(str)
            print(f"-- {'PUTS' if cp == 'P' else 'CALLS'} (rows |delta|, cols DTE)")
            print(cell.to_string())
    print("\ncells clearing the pre-registered bar:")
    print(T[T.PREMIUM].sort_values("t_net", ascending=False)[["state", "cp", "dte", "delta", "n", "months", "yrs", "gross_bp",
                                                                "net_bp", "t_net", "h1", "h2", "yrs_pos", "worst_mo"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
