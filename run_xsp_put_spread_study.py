#!/usr/bin/env python3
"""
XSP put credit spread — UNCONDITIONAL study across DTE, with a robustness battery.

Follow-up to run_davis_condor_study.py, which found a strong 7-DTE effect but
computed it on a biased subsample: every spread there was conditioned on the
Davis condor being constructible at a net credit, and that constraint fails when
IV is elevated — i.e. exactly the weeks that produce losses. This script drops
the condor entirely and builds the spread on every Friday it can.

Friday entry + Friday expiry means DTE is always a multiple of 7, so the buckets
are exact (7, 14, 21, 28, 35, 42) rather than tolerance bands.

Robustness battery, because a clean monotonic gradient is exactly what noise
looks like:
  - bootstrap 95% CI on capital-weighted ROC (net of costs)
  - drop-worst-N sensitivity (is one trade carrying the result?)
  - per-year breakdown (is it one regime?)
  - mid vs cost, to size the slippage dependence

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 \\
      run_xsp_put_spread_study.py --start 2010-01-01 --csv
"""

from __future__ import annotations

import argparse
from datetime import date

import numpy as np
import pandas as pd

from run_davis_condor_study import fetch, spot_by_date, CREDIT_W_PCT, SLIP

DTES   = [7, 14, 21, 28, 35, 42]
DELTAS = [0.10, 0.15, 0.20, 0.30]
RNG    = np.random.default_rng(11)


def build_spread(chain: pd.DataFrame, spot: float, dlt: float):
    """Short put at target delta, long put CREDIT_W_PCT of spot below. Mid + cost."""
    puts = chain[chain["cp"] == "P"].dropna(subset=["delta"]).sort_values("strike")
    if len(puts) < 6:
        return None
    ci = (puts["delta"] - (-abs(dlt))).abs().idxmin()
    C = puts.loc[ci]
    tgt = C["strike"] - spot * CREDIT_W_PCT
    lower = puts[puts["strike"] < C["strike"]]
    if lower.empty:
        return None
    D = lower.loc[(lower["strike"] - tgt).abs().idxmin()]

    def px(row, sign, slip):
        return row["mid"] + sign * (row["ask"] - row["bid"]) / 2.0 * slip

    out = {"C": C["strike"], "D": D["strike"],
           "width": C["strike"] - D["strike"], "short_delta": C["delta"]}
    for tag, slip in (("mid", 0.0), ("cost", SLIP)):
        cr = (px(C, -1, slip) - px(D, +1, slip)) * 100
        out[f"credit_{tag}"] = cr
        out[f"maxloss_{tag}"] = out["width"] * 100 - cr
    return out


def run(df: pd.DataFrame, spots: dict, dte: int, dlt: float) -> pd.DataFrame:
    rows = []
    sub = df[df["dte"] == dte]
    for (td, exp), chain in sub.groupby(["trade_date", "expiry"]):
        S0, S1 = spots.get(td), spots.get(exp)
        if S0 is None or S1 is None:
            continue
        s = build_spread(chain, S0, dlt)
        if s is None or s["maxloss_mid"] <= 0:
            continue
        iv = lambda k: max(k - S1, 0.0)
        term = (-iv(s["C"]) + iv(s["D"])) * 100
        r = dict(entry=td, expiry=exp, spot0=S0, spot1=S1,
                 move_pct=(S1 / S0 - 1) * 100, dte=dte, delta_target=dlt, **s)
        for tag in ("mid", "cost"):
            r[f"pnl_{tag}"] = s[f"credit_{tag}"] + term
        rows.append(r)
    return pd.DataFrame(rows)


def boot_ci(pnl: pd.Series, ml: pd.Series, n=4000):
    idx = np.arange(len(pnl))
    b = [pnl.iloc[s].sum() / ml.iloc[s].sum() * 100
         for s in (RNG.choice(idx, len(idx), replace=True) for _ in range(n))]
    return np.percentile(b, [2.5, 97.5])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2010-01-01")
    ap.add_argument("--end", default="2026-02-20")
    ap.add_argument("--csv", action="store_true")
    a = ap.parse_args()

    print(f"Fetching XSP Friday chains {a.start} -> {a.end} ...")
    df = fetch(date.fromisoformat(a.start), date.fromisoformat(a.end))
    print(f"  {len(df):,} rows, {df.trade_date.nunique()} Fridays")
    spots = spot_by_date(df)
    print(f"  parity spot on {len(spots)} dates")
    n_fridays = df.trade_date.nunique()

    frames = []
    print(f"\n{'DTE':>4} {'Δ':>5} | {'n':>4} {'cov%':>5} {'win%':>6} "
          f"{'ROC mid':>9} {'ROC cost':>9} {'95% CI (cost)':>20} {'mean$':>8} "
          f"{'worst$':>9} {'drop-3':>8}")
    print("-" * 106)
    for dte in DTES:
        for dlt in DELTAS:
            t = run(df, spots, dte, dlt)
            if len(t) < 20:
                print(f"{dte:>4} {dlt:>5.2f} | {len(t):>4}  (thin)")
                continue
            frames.append(t)
            p, m = t["pnl_cost"], t["maxloss_cost"]
            roc_mid = t["pnl_mid"].sum() / t["maxloss_mid"].sum() * 100
            roc_cst = p.sum() / m.sum() * 100
            lo, hi = boot_ci(p, m)
            keep = t.drop(t.nsmallest(3, "pnl_cost").index)
            d3 = keep["pnl_cost"].sum() / keep["maxloss_cost"].sum() * 100
            star = " *" if lo * hi > 0 else ""
            print(f"{dte:>4} {dlt:>5.2f} | {len(t):>4} {len(t)/n_fridays*100:>4.0f}% "
                  f"{(p>0).mean()*100:>5.1f}% {roc_mid:>+9.2f} {roc_cst:>+9.2f} "
                  f"[{lo:>+7.2f},{hi:>+7.2f}]{star:<2} {p.mean():>8,.0f} "
                  f"{p.min():>9,.0f} {d3:>+8.2f}")

    if not frames:
        return
    allt = pd.concat(frames, ignore_index=True)

    # per-year for the headline config
    best = (allt.groupby(["dte", "delta_target"])
                .apply(lambda g: g["pnl_cost"].sum() / g["maxloss_cost"].sum() * 100,
                       include_groups=False)
                .idxmax())
    b = allt[(allt.dte == best[0]) & (allt.delta_target == best[1])].copy()
    b["yr"] = pd.to_datetime(b.entry).dt.year
    print(f"\n=== PER-YEAR: DTE {best[0]}, Δ {best[1]:.2f} (best cost-adj ROC) ===")
    print(f"  {'yr':<6}{'n':>5}{'win%':>7}{'ROC%':>9}{'P&L$':>10}{'worst$':>9}")
    for yr, g in b.groupby("yr"):
        print(f"  {yr:<6}{len(g):>5}{(g.pnl_cost>0).mean()*100:>6.1f}%"
              f"{g.pnl_cost.sum()/g.maxloss_cost.sum()*100:>+9.2f}"
              f"{g.pnl_cost.sum():>10,.0f}{g.pnl_cost.min():>9,.0f}")

    print(f"\n=== DTE gradient at Δ0.20 (is it monotonic and does it survive?) ===")
    for dte in DTES:
        g = allt[(allt.dte == dte) & (allt.delta_target == 0.20)]
        if len(g) < 20:
            continue
        lo, hi = boot_ci(g["pnl_cost"], g["maxloss_cost"])
        print(f"  DTE {dte:>2}: n={len(g):>4}  ROC={g.pnl_cost.sum()/g.maxloss_cost.sum()*100:>+7.2f}%"
              f"  CI[{lo:>+7.2f},{hi:>+7.2f}]  worst=${g.pnl_cost.min():>7,.0f}"
              f"  maxloss_hit={(g.pnl_cost <= -g.maxloss_cost*0.99).sum()}")

    if a.csv:
        allt.to_csv("xsp_put_spread_study.csv", index=False)
        print(f"\nsaved -> xsp_put_spread_study.csv ({len(allt):,} rows)")


if __name__ == "__main__":
    main()
