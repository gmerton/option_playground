#!/usr/bin/env python3
"""
XSP put credit spread v2 — DELTA-parameterised width (scale-free).

Rebuild of run_xsp_put_spread_study.py, which sized the long leg at a fixed
percent of spot. That is not scale-free: 1.3% of spot spans 7-9 strikes at
XSP 690 but only 1-3 strikes at XSP 130, so the 2010-2017 and 2018-2026 halves
were not testing the same structure (credit/max-loss came out at 3-4% vs 10-11%).
That confound made the out-of-sample test uninformative.

v2 picks BOTH legs by delta (house convention: 0.10Δ wings), which is comparable
across index levels and across eras.

Inference is date-clustered from the start: Friday entries across many configs
are the same weeks replicated, so bootstrap resamples DATES, not trades.

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 \\
      run_xsp_spread_v2.py --start 2010-01-01 --csv
"""

from __future__ import annotations

import argparse
from datetime import date

import numpy as np
import pandas as pd

from run_davis_condor_study import fetch, spot_by_date, SLIP

DTES        = [7, 14, 21, 28, 35, 42]
SHORT_DELTAS = [0.10, 0.15, 0.20, 0.30]
WINGS        = [0.05, 0.10]          # long delta = short - wing
MIN_LONG_D   = 0.03
RNG = np.random.default_rng(53)


def build(chain: pd.DataFrame, sd: float, wing: float):
    ld = sd - wing
    if ld < MIN_LONG_D:
        return None
    puts = chain[chain["cp"] == "P"].dropna(subset=["delta"])
    puts = puts[puts["delta"] < 0]
    if len(puts) < 6:
        return None
    C = puts.loc[(puts["delta"] + sd).abs().idxmin()]
    D = puts.loc[(puts["delta"] + ld).abs().idxmin()]
    if D["strike"] >= C["strike"]:
        return None
    # reject if the chain can't actually hit the targets
    if abs(abs(C["delta"]) - sd) > 0.04 or abs(abs(D["delta"]) - ld) > 0.04:
        return None

    def px(r, sign, slip):
        return r["mid"] + sign * (r["ask"] - r["bid"]) / 2.0 * slip

    o = {"C": C["strike"], "D": D["strike"], "width": C["strike"] - D["strike"],
         "cd": C["delta"], "dd": D["delta"]}
    for tag, slip in (("mid", 0.0), ("cost", SLIP)):
        cr = (px(C, -1, slip) - px(D, +1, slip)) * 100
        o[f"credit_{tag}"] = cr
        o[f"maxloss_{tag}"] = o["width"] * 100 - cr
    return o if o["maxloss_mid"] > 0 and o["credit_mid"] > 0 else None


def run_cfg(df, spots, dte, sd, wing):
    rows = []
    for (td, exp), chain in df[df["dte"] == dte].groupby(["trade_date", "expiry"]):
        S0, S1 = spots.get(td), spots.get(exp)
        if S0 is None or S1 is None:
            continue
        s = build(chain, sd, wing)
        if s is None:
            continue
        term = (-max(s["C"] - S1, 0.0) + max(s["D"] - S1, 0.0)) * 100
        r = dict(entry=td, expiry=exp, spot0=S0, spot1=S1, dte=dte,
                 short_d=sd, wing=wing, move_pct=(S1 / S0 - 1) * 100, **s)
        for tag in ("mid", "cost"):
            r[f"pnl_{tag}"] = s[f"credit_{tag}"] + term
        rows.append(r)
    return pd.DataFrame(rows)


def roc(g):
    return g.pnl_cost.sum() / g.maxloss_cost.sum() * 100


def ci_dates(g, n=3000):
    """Date-clustered bootstrap. Aggregate per date first, then resample the
    per-date sums as numpy arrays — the frame-concat version was O(dates) pandas
    ops per draw and took minutes per config."""
    agg = g.groupby("entry")[["pnl_cost", "maxloss_cost"]].sum()
    p = agg["pnl_cost"].to_numpy()
    m = agg["maxloss_cost"].to_numpy()
    k = len(p)
    if k < 15:
        return (np.nan, np.nan)
    idx = RNG.integers(0, k, size=(n, k))
    boots = p[idx].sum(axis=1) / m[idx].sum(axis=1) * 100
    return np.percentile(boots, [2.5, 97.5])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2010-01-01")
    ap.add_argument("--end", default="2026-02-20")
    ap.add_argument("--csv", action="store_true")
    a = ap.parse_args()

    df = fetch(date.fromisoformat(a.start), date.fromisoformat(a.end))
    spots = spot_by_date(df)
    print(f"{len(df):,} rows, {df.trade_date.nunique()} Fridays, parity spot on {len(spots)} dates")

    frames = []
    print(f"\n{'DTE':>4}{'shortΔ':>8}{'wing':>6}{'|':>2}{'n':>5}{'win%':>7}"
          f"{'ROC mid':>9}{'ROC cost':>10}{'95% CI (date-clustered)':>26}{'cr/ML%':>8}{'worst$':>9}")
    print("-" * 104)
    for dte in DTES:
        for sd in SHORT_DELTAS:
            for wing in WINGS:
                if sd - wing < MIN_LONG_D:
                    continue
                t = run_cfg(df, spots, dte, sd, wing)
                if len(t) < 40:
                    continue
                frames.append(t)
                lo, hi = ci_dates(t)
                star = " *" if (lo == lo and lo * hi > 0) else "  "
                print(f"{dte:>4}{sd:>8.2f}{wing:>6.2f}{'|':>2}{len(t):>5}"
                      f"{(t.pnl_cost>0).mean()*100:>6.1f}%"
                      f"{t.pnl_mid.sum()/t.maxloss_mid.sum()*100:>+9.2f}{roc(t):>+10.2f}"
                      f"   [{lo:>+6.2f},{hi:>+6.2f}]{star}"
                      f"{(t.credit_cost/t.maxloss_cost*100).mean():>8.2f}{t.pnl_cost.min():>9,.0f}")

    if not frames:
        print("no configs")
        return
    allt = pd.concat(frames, ignore_index=True)
    allt["era"] = np.where(pd.to_datetime(allt.entry) < "2018-01-01", "2010-2017", "2018-2026")

    print("\n=== ERA COMPARABILITY (the check the v1 parameterisation failed) ===")
    print(f"  {'era':<12}{'dates':>7}{'cr/ML%':>9}{'width/spot%':>13}{'ROC cost%':>11}")
    for era, g in allt.groupby("era"):
        print(f"  {era:<12}{g.entry.nunique():>7}{(g.credit_cost/g.maxloss_cost*100).mean():>9.2f}"
              f"{(g.width/g.spot0*100).mean():>13.2f}{roc(g):>+11.2f}")

    print("\n=== SAME CONFIG, BOTH ERAS (0.20Δ / 0.10 wing) ===")
    print(f"  {'DTE':>4}{'era':>12}{'dates':>7}{'ROC cost%':>11}{'95% CI':>22}")
    for dte in DTES:
        for era, g in allt[(allt.short_d == 0.20) & (allt.wing == 0.10)
                           & (allt.dte == dte)].groupby("era"):
            lo, hi = ci_dates(g)
            cis = f"[{lo:>+6.2f},{hi:>+6.2f}]" if lo == lo else "         (thin)"
            print(f"  {dte:>4}{era:>12}{g.entry.nunique():>7}{roc(g):>+11.2f}   {cis}")

    if a.csv:
        allt.to_csv("xsp_spread_v2.csv", index=False)
        print(f"\nsaved -> xsp_spread_v2.csv ({len(allt):,} rows)")


if __name__ == "__main__":
    main()
