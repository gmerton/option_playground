#!/usr/bin/env python3
"""IV efficiency by liquidity: horizon / earnings check (2026-09-29). PRE-REGISTERED as the addendum in
data/studies/iv_efficiency_by_liquidity_2026-09-29.md (committed 3896c68 before this ran). Re-runs the PRIMARY on
ticker-months with IV expiry 21-40 DTE and no earnings date inside max(DTE, 31) calendar days after the month-end.
Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_iv_efficiency_horizon_check.py > data/studies/iv_efficiency_horizon_check_2026-09-29.log
"""
import numpy as np
import pandas as pd

import run_iv_efficiency_by_liquidity as m

D = pd.read_parquet(m.CACHE / "panel.parquet")
fd = m.CACHE / "dte_month_end.parquet"
if not fd.exists():
    tl = ",".join(f"'{t}'" for t in sorted(D.ticker.unique()))
    dl = ",".join(f"DATE '{d.date()}'" for d in sorted(D.date.unique()))
    x = m.q(f"SELECT ticker, trade_date, skew_dte FROM silver.options_iv_daily WHERE ticker IN ({tl}) AND trade_date IN ({dl})")
    x.to_parquet(fd, index=False)
x = pd.read_parquet(fd); x["trade_date"] = pd.to_datetime(x.trade_date)
D = D.merge(x.rename(columns={"trade_date": "date"}), on=["ticker", "date"], how="left")

e1 = pd.read_parquet(m.REPO / "data/cache/earnings_yf.parquet")[["ticker", "session"]].rename(columns={"session": "ed"})
from lib.mysql_lib import _get_engine
e2 = pd.read_sql("SELECT ticker, raw_date AS ed FROM earnings_report", _get_engine())
E = pd.concat([e1, e2]); E["ed"] = pd.to_datetime(E.ed, errors="coerce"); E = E.dropna().drop_duplicates()
Eg = {t: np.sort(g.ed.values) for t, g in E.groupby("ticker")}

def classify(t, d, dte):
    a = Eg.get(t)
    if a is None:
        return "no_cover"
    d64 = np.datetime64(d)
    if not ((a >= d64 - np.timedelta64(400, "D")) & (a <= d64 + np.timedelta64(400, "D"))).any():
        return "no_cover"
    hi = d64 + np.timedelta64(int(max(dte if np.isfinite(dte) else 31, 31)), "D")
    return "earn" if ((a > d64) & (a <= hi)).any() else "clean"

D["ecls"] = [classify(t, d, k) for t, d, k in zip(D.ticker, D.date, D.skew_dte)]
print(f"rows {len(D):,}; skew_dte known {D.skew_dte.notna().mean():.1%}; DTE 21-40 {D.skew_dte.between(21, 40).mean():.1%}; "
      f"earnings class {D.ecls.value_counts(normalize=True).round(3).to_dict()}")
print("share of rows with DTE 21-40 by decile:", D.groupby("dec").skew_dte.apply(lambda s: s.between(21, 40).mean()).round(2).tolist())
print("share 'earn' by decile:", D.groupby("dec").ecls.apply(lambda s: (s == "earn").mean()).round(2).tolist())
S = D[D.skew_dte.between(21, 40) & (D.ecls == "clean")].copy()
S = S[S.groupby("date").ticker.transform("size") >= 50]      # months need enough rows for deciles (mechanical)
S["dec"] = S.groupby("date").vol21.transform(lambda s: pd.qcut(s.rank(method="first"), 10, labels=False))
lines = m.analyse(S, "HORIZON/EARNINGS-CLEAN SUBSET: IV expiry 21-40 DTE, no earnings in the window, covered tickers")
print("\n".join(lines))
