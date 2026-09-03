#!/usr/bin/env python3
"""
Track 2 — does an IV-LEVEL gate beat / complement the FVR gate on the long straddle?

Arms (all on the same 140-ticker approved list, so the comparison is fair even
though the list itself was selected on 2021-25 data):
  0  no gate                      (baseline)
  A  FVR >= 1.20                  (current playbook gate)
  A+ FVR >= 1.40                  (current full-size tier)
  B  IV percentile <= X           (new: iv_put_10 low vs the ticker's OWN history)
  C  A and B                      (expected to matter most — the two are near-orthogonal)

Why iv_put_10: the traded straddle is ~7-10 DTE, and the tenor-matched IV tested
strongest (R^2 0.098 vs 0.085 at 30d, 0.061 at 90d) in the 2026-08-05 work.

BACKWARD-ONLY PERCENTILE. The rank is computed over each ticker's own trailing
252 *daily* observations, shifted one day, so no entry can see its own or any
future IV. An earlier within-ticker test used a full-sample mean and was
look-ahead contaminated; that is the mistake this avoids.

Inference is date-clustered throughout: Friday entries across 140 correlated
names are not independent observations.

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_track2_gates.py
"""
from __future__ import annotations

import argparse
import numpy as np
import pandas as pd
import awswrangler as wr

IN_CSV = "track2_straddle_data.csv"
RNG = np.random.default_rng(97)
WIN = 252          # trailing daily obs for the percentile
PCT_CUTS = [20, 30, 40]


def iv_percentile(tickers: list[str]) -> pd.DataFrame:
    """Per-ticker trailing percentile rank of iv_put_10, strictly backward-looking."""
    sql = f"""
    SELECT ticker, trade_date, iv_put_10
    FROM silver.fwd_vol_daily
    WHERE ticker IN ({",".join(f"'{t}'" for t in tickers)})
      AND iv_put_10 IS NOT NULL AND iv_put_10 > 0
    """
    d = wr.athena.read_sql_query(sql=sql, database="silver", workgroup="dev-v3",
                                 s3_output="s3://athena-919061006621/")
    d["trade_date"] = pd.to_datetime(d["trade_date"]).dt.date
    d = d.sort_values(["ticker", "trade_date"]).reset_index(drop=True)
    # shift(1) => the rank window ends the day BEFORE the entry
    d["iv_pct"] = (d.groupby("ticker")["iv_put_10"]
                     .transform(lambda s: s.shift(1)
                                           .rolling(WIN, min_periods=60)
                                           .rank(pct=True) * 100))
    return d[["ticker", "trade_date", "iv_pct"]]


def roc_stats(g: pd.DataFrame) -> dict:
    r = g["ret_pct_long"]
    return dict(n=len(g), dates=g["entry_date"].nunique(),
                mean=r.mean(), med=r.median(), win=(r > 0).mean() * 100,
                sharpe=r.mean() / r.std() if r.std() > 0 else np.nan)


def ci_dates(g: pd.DataFrame, n=3000):
    """Date-clustered bootstrap on the MEAN return."""
    agg = g.groupby("entry_date")["ret_pct_long"].agg(["sum", "count"])
    s, c = agg["sum"].to_numpy(), agg["count"].to_numpy()
    k = len(s)
    if k < 15:
        return (np.nan, np.nan)
    idx = RNG.integers(0, k, size=(n, k))
    return np.percentile(s[idx].sum(1) / c[idx].sum(1), [2.5, 97.5])


def show(g: pd.DataFrame, label: str, base: float | None = None):
    if len(g) < 30:
        print(f"  {label:<34} (thin, n={len(g)})")
        return None
    st = roc_stats(g)
    lo, hi = ci_dates(g)
    star = "*" if (lo == lo and lo * hi > 0) else " "
    lift = f"{st['mean']-base:>+7.2f}" if base is not None else "      -"
    print(f"  {label:<34}{st['n']:>6}{st['dates']:>7}{st['win']:>7.1f}%"
          f"{st['mean']:>+8.2f}{st['med']:>+8.2f}{st['sharpe']:>+8.3f}"
          f"  [{lo:>+6.2f},{hi:>+6.2f}]{star}{lift}")
    return st["mean"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=IN_CSV)
    a = ap.parse_args()

    df = pd.read_csv(a.csv, parse_dates=["entry_date"])
    df["entry_date"] = df["entry_date"].dt.date
    df = df.dropna(subset=["ret_pct_long", "fvr_put_30_90"])

    # options_daily_v3 uses 99999.99 as a sentinel in `last`. Only ~10 rows in 27k,
    # but they produce returns up to +7,272,627% and swamp every mean. Filter on the
    # sentinel itself, NOT on payout>strike — a straddle's payout legitimately exceeds
    # the strike on a large upside move, and that filter would delete real winners.
    SENTINEL = 99_999.0
    bad = (df["call_last_exp"] >= SENTINEL) | (df["put_last_exp"] >= SENTINEL)
    if bad.any():
        print(f"  dropped {bad.sum()} rows with {SENTINEL:,.0f} sentinel in last "
              f"(mean before {df.ret_pct_long.mean():+.1f}%, after {df[~bad].ret_pct_long.mean():+.2f}%)")
        df = df[~bad]
    tickers = sorted(df["ticker"].unique())
    print(f"{len(df):,} straddles, {len(tickers)} tickers, "
          f"{df.entry_date.min()} -> {df.entry_date.max()}, mean DTE {df.dte.mean():.1f}")

    print("computing backward-only trailing IV percentile ...")
    pct = iv_percentile(tickers)
    df = df.merge(pct.rename(columns={"trade_date": "entry_date"}),
                  on=["ticker", "entry_date"], how="left")
    print(f"  iv_pct present on {df.iv_pct.notna().mean()*100:.0f}% of entries")
    df = df.dropna(subset=["iv_pct"])

    hdr = (f"  {'arm':<34}{'n':>6}{'dates':>7}{'win%':>8}{'mean%':>8}"
           f"{'med%':>8}{'sharpe':>8}{'  95% CI (date-clustered)':>26}{'  lift':>8}")
    print(f"\n{'='*118}\n  POOLED\n{'='*118}")
    print(hdr); print("  " + "-" * 116)
    base = show(df, "0  no gate")
    show(df[df.fvr_put_30_90 >= 1.20], "A  FVR>=1.20 (current)", base)
    show(df[df.fvr_put_30_90 >= 1.40], "A+ FVR>=1.40 (full size)", base)
    for c in PCT_CUTS:
        show(df[df.iv_pct <= c], f"B  IV pct<={c}", base)
    for c in PCT_CUTS:
        show(df[(df.iv_pct <= c) & (df.fvr_put_30_90 >= 1.20)],
             f"C  IV pct<={c} AND FVR>=1.20", base)

    print(f"\n{'='*118}\n  WALK-FORWARD BY YEAR (playbook folds 2021-2025)\n{'='*118}")
    df["yr"] = pd.to_datetime(df.entry_date).dt.year
    arms = {
        "0 none":      lambda d: d,
        "A FVR>=1.20": lambda d: d[d.fvr_put_30_90 >= 1.20],
        "B IVpct<=30": lambda d: d[d.iv_pct <= 30],
        "C both":      lambda d: d[(d.iv_pct <= 30) & (d.fvr_put_30_90 >= 1.20)],
    }
    print(f"  {'year':<7}" + "".join(f"{k:>16}" for k in arms))
    for yr in sorted(y for y in df.yr.unique() if 2021 <= y <= 2025):
        g = df[df.yr == yr]
        row = f"  {yr:<7}"
        for _, f in arms.items():
            s = f(g)
            row += f"{(s.ret_pct_long.mean() if len(s) >= 20 else float('nan')):>+16.2f}"
        print(row)
    print(f"  {'-'*7}" + "".join(f"{'-'*16}" for _ in arms))
    row = f"  {'ALL':<7}"
    for _, f in arms.items():
        s = f(df[(df.yr >= 2021) & (df.yr <= 2025)])
        row += f"{s.ret_pct_long.mean():>+16.2f}"
    print(row)

    print(f"\n  note: 140-name list was itself selected on 2021-25 data, so absolute")
    print(f"  levels carry look-ahead. The ARM COMPARISON is unaffected — same list, "
          f"same trades, only the gate differs.")


if __name__ == "__main__":
    main()
