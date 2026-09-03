#!/usr/bin/env python3
"""
Analyse the controlled DTE sweep. Tests the pre-registered hypothesis that
results IMPROVE with DTE, because the FVR gate is a 30->90d signal while the
trade currently lives only 7 days.

Reports, per DTE target: no gate / arm A (FVR) / arm C (FVR + IV pct), each with
a date-clustered bootstrap CI, then an era split as the falsification check.

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_track2_dte_analysis.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import awswrangler as wr

RNG = np.random.default_rng(131)
STOP, MIN_COST, SENTINEL = -50.0, 0.50, 99_999.0
IN = "track2_dte_sweep.csv"


def load() -> pd.DataFrame:
    d = pd.read_csv(IN, parse_dates=["entry_date"])
    d["entry_date"] = d["entry_date"].dt.date
    n0 = len(d)
    d = d[~((d.call_last_exp >= SENTINEL) | (d.put_last_exp >= SENTINEL))]
    d = d.dropna(subset=["ret_pct_long", "fvr_put_30_90"])
    d = d[d.entry_premium >= MIN_COST]
    print(f"  {n0:,} -> {len(d):,} after sentinel + ${MIN_COST} min-cost filters")

    tk = sorted(d.ticker.unique())
    p = wr.athena.read_sql_query(
        sql=f"""SELECT ticker, trade_date, iv_put_10 FROM silver.fwd_vol_daily
                WHERE ticker IN ({",".join(f"'{t}'" for t in tk)}) AND iv_put_10 > 0""",
        database="silver", workgroup="dev-v3", s3_output="s3://athena-919061006621/")
    p["trade_date"] = pd.to_datetime(p.trade_date).dt.date
    p = p.sort_values(["ticker", "trade_date"])
    p["iv_pct"] = (p.groupby("ticker").iv_put_10
                     .transform(lambda s: s.shift(1).rolling(252, min_periods=60)
                                           .rank(pct=True) * 100))
    d = d.merge(p.rename(columns={"trade_date": "entry_date"})[["ticker", "entry_date", "iv_pct"]],
                on=["ticker", "entry_date"], how="left").dropna(subset=["iv_pct"])
    d["stp"] = d.ret_pct_long.clip(lower=STOP)
    d["era"] = np.where(pd.to_datetime(d.entry_date) < "2022-01-01", "2018-2021", "2022-2026")
    return d


def ci(g, col="stp", n=3000):
    a = g.groupby("entry_date")[col].agg(["sum", "count"])
    s, c = a["sum"].to_numpy(), a["count"].to_numpy()
    if len(s) < 15:
        return (np.nan, np.nan)
    i = RNG.integers(0, len(s), size=(n, len(s)))
    return np.percentile(s[i].sum(1) / c[i].sum(1), [2.5, 97.5])


ARMS = {
    "no gate":      lambda d: d,
    "A FVR>=1.20":  lambda d: d[d.fvr_put_30_90 >= 1.20],
    "C FVR+IVpct":  lambda d: d[(d.fvr_put_30_90 >= 1.20) & (d.iv_pct <= 30)],
}


def main() -> None:
    print("loading + computing backward-only IV percentile ...")
    d = load()
    print(f"  {len(d):,} trades, {d.ticker.nunique()} tickers, "
          f"{d.entry_date.min()} -> {d.entry_date.max()}")

    print(f"\n{'='*100}\n  BY DTE (straddle, stop -50%)  — hypothesis: results improve with DTE"
          f"\n{'='*100}")
    print(f"  {'arm':<14}{'DTE':>5}{'n':>7}{'actual':>8}{'win%':>7}{'mean%':>9}"
          f"{'med%':>8}{'sharpe':>8}{'  95% CI':>20}{'  cost$':>9}")
    for arm, f in ARMS.items():
        print("  " + "-" * 96)
        for dte in sorted(d.dte_target.unique()):
            g = f(d[d.dte_target == dte])
            if len(g) < 50:
                print(f"  {arm:<14}{dte:>5}{len(g):>7}  (thin)"); continue
            lo, hi = ci(g)
            st = "*" if (lo == lo and lo * hi > 0) else " "
            print(f"  {arm:<14}{dte:>5}{len(g):>7}{g.dte.mean():>8.1f}"
                  f"{(g.stp>0).mean()*100:>6.1f}%{g.stp.mean():>+9.2f}{g.stp.median():>+8.2f}"
                  f"{g.stp.mean()/g.stp.std():>+8.3f}  [{lo:>+6.2f},{hi:>+6.2f}]{st}"
                  f"{g.entry_premium.mean():>9.2f}")

    print(f"\n{'='*100}\n  ERA SPLIT — arm C. A real DTE effect must appear in BOTH."
          f"\n{'='*100}")
    print(f"  {'era':<12}" + "".join(f"{f'DTE {x}':>14}" for x in sorted(d.dte_target.unique())))
    for era in ["2018-2021", "2022-2026"]:
        row = f"  {era:<12}"
        for dte in sorted(d.dte_target.unique()):
            g = ARMS["C FVR+IVpct"](d[(d.dte_target == dte) & (d.era == era)])
            row += f"{(g.stp.mean() if len(g) >= 50 else float('nan')):>+14.2f}"
        print(row)

    print(f"\n{'='*100}\n  HOLD-TO-EXPIRY (no stop) — is any DTE effect just the stop?"
          f"\n{'='*100}")
    print(f"  {'arm':<14}" + "".join(f"{f'DTE {x}':>14}" for x in sorted(d.dte_target.unique())))
    for arm, f in ARMS.items():
        row = f"  {arm:<14}"
        for dte in sorted(d.dte_target.unique()):
            g = f(d[d.dte_target == dte])
            row += f"{(g.ret_pct_long.mean() if len(g) >= 50 else float('nan')):>+14.2f}"
        print(row)

    print("\n  note: longer-DTE straddles cost more, so the $0.50 min-cost filter binds")
    print("  less at high DTE — check the cost$ column when reading the gradient.")


if __name__ == "__main__":
    main()
