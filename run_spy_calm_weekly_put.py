#!/usr/bin/env python3
"""
CALM-REGIME SPY WEEKLY PUT SALE as a strategy: short 7-DTE far-OTM SPY puts on calm Fridays, skipping negative
dealer-gamma days (pre-registered 2026-09-28, committed before any run).

WHY. Gabe's goal (2026-09-28): what to run NOW. The environment is calm (VIX ~16, SPY above its 50-day, so the stress
bucket cannot fire -- and it is PARKED). The leg surface's strongest UNCONDITIONAL cells are 7-DTE far-OTM puts
(5-delta +3.8 bp t 5.24, 10-delta +6.0 bp t 4.46, one entry per expiry). The GEX regime is the book's one certified
MECHANISM (negative dealer gamma -> realised vol +8% beyond VIX). This asks whether the combination certifies as a
strategy, and whether its premium survives the delta-matched beta control that sank the stress bucket.

PRE-REGISTRATION
  Data      data/cache/spy_leg_surface_entries.parquet (v3 EOD quotes, 2010-01 -> 2026-02): the 7-DTE cells (expiry nearest
            7 DTE in [5, 9]; |delta| nearest 0.10 +/- 0.025 or 0.05 +/- 0.015); FRIDAY entries only (weekly, so trades do
            not overlap); hold to expiry; settle on SPY's close; house fills (mid - 25% bid-ask - $0.0065/share).
  Regime    CALM = NOT (SPY close < 50 SMA AND VIX >= 20).  GAMMA+ = SPY net dealer GEX > 0 at the entry close
            (run_gex_regime_pin.gex_series; data ends 2026-02).
  PRIMARY   arm N10-CG: short 7-DTE 10-delta put, CALM & GAMMA+ Fridays.
            Statistic: EXCESS over beta per trade = net P&L - |delta| x SPY return entry->expiry (carry-adjusted,
            q 1.8% - T-bill), bp of notional; month-clustered t.
            CERTIFIED-CANDIDATE iff: excess t >= 3, both halves (2010-2017 / 2018-2026) positive, >= 70% of years
            positive. Candidate status means a forward paper trade before any size, never size on this alone.
  Secondary (exploratory; Sidak over the 5 extra cells ~ |t| 2.8): N10 CALM without the gamma gate (does the gate earn
            its place?); N05 CALM & GAMMA+; the 10/5 VERTICAL (short 10-delta, long 5-delta, same expiry) CALM & GAMMA+
            (defined risk); N10 on CALM & GAMMA- Fridays (the skipped cell -- the gate's mirror); N10 ALL Fridays.
  Also      raw net bp and return on Reg-T margin (naked: premium + max(20% S - OTM, 10% K); vertical: max loss);
            worst trade, worst 4-week window, the 2020-02 path, the 2018-02 'Volmageddon' week, per-year table.
  Caveats   2010-2026 only -- short-tenor synthetic pricing failed validation (+15% rich), so there is NO 2008 test for
            this strategy; weekly SPY expiries are thin before ~2012-16; survivorship does not apply (index).

Usage: PYTHONPATH=src:. .venv/bin/python3 run_spy_calm_weekly_put.py > data/studies/logs/spy_calm_weekly_put.log
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
Q = 0.018
SPLIT = pd.Timestamp("2018-01-01")


def irx():
    import yfinance as yf
    s = yf.download("^IRX", start="2009-12-01", end="2026-04-01", progress=False, auto_adjust=False)["Close"].squeeze() / 100
    s.index = pd.to_datetime(s.index).normalize()
    return s


def mclust(x: pd.Series, d: pd.Series):
    df = pd.DataFrame(dict(x=x.values, m=pd.to_datetime(d.values).to_period("M"))).dropna()
    mu = df.x.mean(); s = df.groupby("m").x.sum(); n = df.groupby("m").size()
    se = np.sqrt(((s - n * mu) ** 2).sum()) / n.sum()
    return mu, (mu / se if se > 0 else np.nan)


def main():
    E = pd.read_parquet("data/cache/spy_leg_surface_entries.parquet")
    E = E[(E.cp == "P") & (E.dtgt == 7) & (E.trade_date.dt.dayofweek == 4)].copy()
    r = irx(); E["r"] = r.reindex(E.trade_date, method="ffill").values
    T = E.dte / 365
    E["beta_bp"] = E.ad * ((E.S_T - E.S_0) / E.S_0 + (Q - E.r) * T) * 1e4
    E["excess"] = E.bp_n - E.beta_bp
    E["regt"] = E.mid + np.maximum(0.20 * E.S_0 - np.maximum(E.S_0 - E.strike, 0), 0.10 * E.strike)
    E["roc"] = (E.bp_n * E.S_0 / 1e4) / E.regt * 100
    E["calm"] = ~E.stress
    N10 = E[E.dcen == 0.10].set_index("trade_date"); N05 = E[E.dcen == 0.05].set_index("trade_date")
    # vertical: short 10d, long 5d, same expiry
    V = N10.join(N05[["expiry", "strike", "mid", "ba", "pay", "delta"]], rsuffix="_l", how="inner")
    V = V[V.expiry == V.expiry_l]
    V["long_net"] = (V.pay_l - V.mid_l - 0.25 * V.ba_l - 0.0065)
    V["pnl"] = V.bp_n * V.S_0 / 1e4 + V.long_net
    V["bp_n"] = V.pnl / V.S_0 * 1e4
    V["ad"] = V.ad - V.delta_l.abs()
    V["beta_bp"] = V.ad * ((V.S_T - V.S_0) / V.S_0 + (Q - V.r) * (V.dte / 365)) * 1e4
    V["excess"] = V.bp_n - V.beta_bp
    width = V.strike - V.strike_l; credit = V.bp_n * 0 + (V.mid - 0.25 * V.ba - 0.0065) - (V.mid_l + 0.25 * V.ba_l + 0.0065)
    V["roc"] = V.pnl / (width - credit).where(width - credit > 0) * 100
    cells = {
        "PRIMARY N10 CALM&G+": N10[N10.calm & (N10.gamma > 0)],
        "N10 CALM (no gate)": N10[N10.calm],
        "N05 CALM&G+": N05[N05.calm & (N05.gamma > 0)],
        "VERT 10/5 CALM&G+": V[V.calm & (V.gamma > 0)],
        "N10 CALM&G- (skipped)": N10[N10.calm & (N10.gamma < 0)],
        "N10 ALL": N10,
    }
    rows = []
    for k, g in cells.items():
        g = g.reset_index().sort_values("trade_date").drop_duplicates("trade_date")
        mu, t = mclust(g.bp_n, g.trade_date); ex, tx = mclust(g.excess, g.trade_date)
        be, _ = mclust(g.beta_bp, g.trade_date)
        yr = g.groupby(g.trade_date.dt.year).excess.mean()
        h1, h2 = g[g.trade_date < SPLIT].excess.mean(), g[g.trade_date >= SPLIT].excess.mean()
        wk = g.set_index("trade_date").bp_n.rolling("28D").sum()
        rows.append(dict(cell=k, n=len(g), years=f"{g.trade_date.dt.year.min()}-{g.trade_date.dt.year.max() % 100}",
                         net_bp=mu, t_net=t, beta_bp=be, excess_bp=ex, t_excess=tx, h1=h1, h2=h2,
                         yrs_pos=(yr > 0).mean(), win=100 * (g.bp_n > 0).mean(), roc_pct=g.roc.mean(),
                         worst_bp=g.bp_n.min(), worst_4wk=wk.min()))
    R = pd.DataFrame(rows)
    print(R.round(2).to_string(index=False))
    p = R.iloc[0]
    ok = p.t_excess >= 3 and p.h1 > 0 and p.h2 > 0 and p.yrs_pos >= 0.70
    print(f"\nPRIMARY: excess {p.excess_bp:+.2f} bp/trade, t {p.t_excess:+.2f}, halves {p.h1:+.2f}/{p.h2:+.2f}, years + {p.yrs_pos:.0%} "
          f"-> {'CERTIFIED-CANDIDATE (paper trade first)' if ok else 'NOT CERTIFIED'}")
    g = cells["PRIMARY N10 CALM&G+"].reset_index()
    print("\nper year (primary): excess bp mean, n, raw net bp mean, worst")
    print(g.groupby(g.trade_date.dt.year).agg(excess=("excess", "mean"), n=("excess", "size"), net=("bp_n", "mean"),
                                              worst=("bp_n", "min")).round(2).T.to_string())
    allf = N10.reset_index()
    for lab, a, b in (("2018-02 Volmageddon", "2018-01-26", "2018-02-16"), ("2020-02/03 COVID", "2020-02-14", "2020-03-20"),
                      ("2025-03/04 tariffs", "2025-03-21", "2025-04-18")):
        w = allf[(allf.trade_date >= a) & (allf.trade_date <= b)]
        print(f"\n{lab} (all 10-delta Fridays, with regime flags):")
        print(w[["trade_date", "expiry", "strike", "S_0", "S_T", "bp_n", "calm", "gamma"]].round(2).to_string(index=False))
    E.to_csv("data/studies/logs/spy_calm_weekly_put_entries.csv", index=False)


if __name__ == "__main__":
    main()
