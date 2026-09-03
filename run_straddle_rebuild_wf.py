#!/usr/bin/env python3
"""
Honest rebuild of the long-straddle approved list — qualify under the rule you trade.

The published list qualifies tickers on FVR-filtered in-sample trades, then trades
them under FVR. Today's IV-percentile gate was bolted on afterwards, so the list was
selected under one rule and traded under another. This rebuilds it: qualification
statistics are computed on trades passing BOTH gates.

Fold structure matches the published design exactly so results are comparable:
  for test year N in 2021..2025:
      IS  = entries with year < N   (qualification only ever sees the past)
      OOS = entries with year == N
  qualify: n >= 15, avg_roc > 0, sharpe > 0   (unchanged)
  trade  : approved list, both gates, stop -50%

Baselines, in increasing order of how much they'd hurt:
  1. published 140-name list, FVR gate only        <- the published result
  2. published 140-name list, both gates           <- today's +18.79%, now OOS
  3. REBUILT list, both gates                      <- the honest number
  4. full 323 pool, both gates, NO qualification   <- does ticker selection do anything?

Baseline 4 is the one to watch. If the rebuilt list does not beat the ungated pool
out of sample, ticker qualification is not doing real work.

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_straddle_rebuild_wf.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import awswrangler as wr

IN = "straddle_pool_data.csv"
APPROVED = "data/watchlist/long_straddle_approved.txt"
SENTINEL, MIN_COST, STOP = 99_999.0, 0.50, -50.0
FVR_GATE, IVPCT_GATE = 1.20, 30.0
MIN_N = 15
FOLDS = [2021, 2022, 2023, 2024, 2025]


def load() -> pd.DataFrame:
    d = pd.read_csv(IN, parse_dates=["entry_date"])
    d["entry_date"] = d["entry_date"].dt.date
    n0 = len(d)
    d = d[~((d.call_last_exp >= SENTINEL) | (d.put_last_exp >= SENTINEL))]
    d = d.dropna(subset=["ret_pct_long", "fvr_put_30_90"])
    d = d[d.entry_premium >= MIN_COST]
    print(f"  {n0:,} -> {len(d):,} after sentinel + ${MIN_COST} min-cost")

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
    d["yr"] = pd.to_datetime(d.entry_date).dt.year
    d["roc"] = d.ret_pct_long.clip(lower=STOP)          # stop applied
    d["pass_fvr"] = d.fvr_put_30_90 >= FVR_GATE
    d["pass_iv"] = d.iv_pct <= IVPCT_GATE
    d["pass_both"] = d.pass_fvr & d.pass_iv
    return d


def qualify(df: pd.DataFrame) -> list[str]:
    """Published criteria, unchanged: n>=MIN_N, avg_roc>0, sharpe>0."""
    out = []
    for t, g in df.groupby("ticker"):
        if len(g) < MIN_N:
            continue
        a, s = g.roc.mean(), g.roc.std()
        if a > 0 and (a / s if s > 0 else 0) > 0:
            out.append(t)
    return sorted(out)


def stats(g: pd.DataFrame) -> dict:
    if len(g) < 5:
        return dict(n=len(g), win=np.nan, roc=np.nan, sh=np.nan)
    return dict(n=len(g), win=(g.roc > 0).mean() * 100, roc=g.roc.mean(),
                sh=g.roc.mean() / g.roc.std() if g.roc.std() > 0 else np.nan)


def main() -> None:
    print("loading + backward-only IV percentile ...")
    d = load()
    pub = [l.strip() for l in open(APPROVED) if l.strip()]
    print(f"  {len(d):,} trades, {d.ticker.nunique()} tickers, "
          f"{d.entry_date.min()} -> {d.entry_date.max()}")
    print(f"  published list: {len(pub)} names ({len(set(pub)&set(d.ticker))} present in pool)")

    rows, churn = [], []
    prev = None
    for N in FOLDS:
        IS, OOS = d[d.yr < N], d[d.yr == N]
        if IS.empty or OOS.empty:
            continue
        rebuilt = qualify(IS[IS.pass_both])
        arms = {
            "1 published + FVR only":  OOS[OOS.ticker.isin(pub) & OOS.pass_fvr],
            "2 published + both":      OOS[OOS.ticker.isin(pub) & OOS.pass_both],
            "3 REBUILT + both":        OOS[OOS.ticker.isin(rebuilt) & OOS.pass_both],
            "4 full pool + both":      OOS[OOS.pass_both],
        }
        for k, g in arms.items():
            rows.append(dict(fold=N, arm=k, **stats(g)))
        churn.append(dict(fold=N, n_qual=len(rebuilt),
                          kept_from_pub=len(set(rebuilt) & set(pub)),
                          new_vs_prev=len(set(rebuilt) - set(prev)) if prev else np.nan,
                          overlap_prev=(len(set(rebuilt) & set(prev)) / len(set(rebuilt) | set(prev)) * 100)
                                        if prev else np.nan))
        prev = rebuilt

    r = pd.DataFrame(rows)
    print(f"\n{'='*94}\n  OUT-OF-SAMPLE BY FOLD (stop -50%)\n{'='*94}")
    print(f"  {'arm':<26}" + "".join(f"{y:>12}" for y in FOLDS) + f"{'MEAN':>12}")
    for arm in ["1 published + FVR only", "2 published + both", "3 REBUILT + both", "4 full pool + both"]:
        s = r[r.arm == arm].set_index("fold")
        line = f"  {arm:<26}" + "".join(f"{s.roc.get(y, np.nan):>+12.2f}" for y in FOLDS)
        print(line + f"{s.roc.mean():>+12.2f}")
    print(f"\n  {'arm':<26}{'n (total)':>12}{'win%':>10}{'mean ROC%':>12}{'Sharpe':>10}")
    for arm in ["1 published + FVR only", "2 published + both", "3 REBUILT + both", "4 full pool + both"]:
        s = r[r.arm == arm]
        print(f"  {arm:<26}{int(s.n.sum()):>12,}{s.win.mean():>9.1f}%"
              f"{s.roc.mean():>+12.2f}{s.sh.mean():>+10.3f}")

    c = pd.DataFrame(churn)
    print(f"\n{'='*94}\n  LIST STABILITY — heavy churn = fitting noise\n{'='*94}")
    print(f"  {'fold':<7}{'qualified':>11}{'kept from published 140':>26}{'new vs prev':>13}{'overlap prev %':>16}")
    for x in c.itertuples(index=False):
        print(f"  {x.fold:<7}{x.n_qual:>11}{x.kept_from_pub:>26}"
              f"{(x.new_vs_prev if x.new_vs_prev == x.new_vs_prev else 0):>13.0f}"
              f"{(x.overlap_prev if x.overlap_prev == x.overlap_prev else float('nan')):>16.1f}")

    final = qualify(d[(d.yr < 2026) & d.pass_both])
    pd.Series(final).to_csv("straddle_approved_rebuilt.csv", index=False, header=["ticker"])
    print(f"\n  full-sample rebuilt list: {len(final)} names -> straddle_approved_rebuilt.csv")
    print(f"  (for reference only — the OOS numbers above are what matters)")


if __name__ == "__main__":
    main()
