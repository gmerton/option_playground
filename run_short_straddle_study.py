#!/usr/bin/env python3
"""
Short straddle — when is SELLING the 7-DTE ATM straddle profitable?

Mirror of the long-straddle work. Same trades, same pool (323 weekly-optionable
names), opposite side.

PRE-REGISTERED HYPOTHESES (stated before looking):
  H1  Sellers want BACKWARDATION.  FVR <= 0.90 should beat FVR >= 1.20.
      (Prior: fvr_straddle_regression_playbook.md found exactly this on 987 names —
       FVR<0.80 +4.6% vs FVR>=1.20 -0.8%. This is a replication on a cleaner pool.)
  H2  Sellers want HIGH IV.  IV percentile >= 70 should beat <= 30.
      (Mirror of this week's finding that high IV predicts poor LONG returns.
       This is the genuinely new test.)
  H3  The two stack, as they did on the long side.

WHY THE PAYOFF IS NOT A MIRROR IMAGE
  Long straddle: floored at -100%, unbounded upside.
  Short straddle: capped at +100% of credit, UNBOUNDED downside.
  So the seller has a high win rate, a positive median, and a mean dragged down by
  a thin left tail. Mean and median disagree by design — report both, and never
  quote win rate alone.

RETURN BASES (both reported)
  profit_pct_seller = (premium - payout)/premium * 100     <- house convention
  roc_margin        = (premium - payout)*100 / reg_t       <- real capital at risk
  reg_t ~= 0.20*strike*100 + premium*100  (naked-option approximation)

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src:. .venv/bin/python3 run_short_straddle_study.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import awswrangler as wr

IN = "straddle_pool_data.csv"
SENTINEL, MIN_COST = 99_999.0, 0.50
RNG = np.random.default_rng(211)


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

    d["seller"] = -d.ret_pct_long                      # capped at +100 by construction
    d["reg_t"] = 0.20 * d.strike * 100 + d.entry_premium * 100
    d["roc_margin"] = (d.entry_premium - d.payout) * 100 / d.reg_t * 100
    d["yr"] = pd.to_datetime(d.entry_date).dt.year
    return d


def ci(g, col, n=3000):
    a = g.groupby("entry_date")[col].agg(["sum", "count"])
    s, c = a["sum"].to_numpy(), a["count"].to_numpy()
    if len(s) < 15:
        return (np.nan, np.nan)
    i = RNG.integers(0, len(s), size=(n, len(s)))
    return np.percentile(s[i].sum(1) / c[i].sum(1), [2.5, 97.5])


def line(g, lab, col="seller"):
    if len(g) < 50:
        print(f"  {lab:<28}{len(g):>7}  (thin)"); return
    r = g[col]
    lo, hi = ci(g, col)
    st = "*" if (lo == lo and lo * hi > 0) else " "
    print(f"  {lab:<28}{len(g):>7}{(r > 0).mean()*100:>7.1f}%{r.mean():>+9.2f}{r.median():>+9.2f}"
          f"{r.mean()/r.std():>+8.3f}  [{lo:>+6.2f},{hi:>+6.2f}]{st}"
          f"{g.roc_margin.mean():>+9.2f}{r.min():>9.0f}")


def main() -> None:
    print("loading + backward-only IV percentile ...")
    d = load()
    print(f"  {len(d):,} trades, {d.ticker.nunique()} tickers, "
          f"{d.entry_date.min()} -> {d.entry_date.max()}")

    hdr = (f"  {'arm':<28}{'n':>7}{'win%':>8}{'mean%':>9}{'med%':>9}{'sharpe':>8}"
           f"{'  95% CI':>20}{'ROCmargin':>9}{'worst%':>9}")
    print(f"\n{'='*108}\n  BASELINE + H1 (FVR bands)   — seller wants BACKWARDATION\n{'='*108}")
    print(hdr); print("  " + "-" * 106)
    line(d, "all trades (no gate)")
    for lab, m in [("FVR <= 0.80", d.fvr_put_30_90 <= 0.80),
                   ("FVR <= 0.90", d.fvr_put_30_90 <= 0.90),
                   ("FVR 0.90-1.20", (d.fvr_put_30_90 > 0.90) & (d.fvr_put_30_90 < 1.20)),
                   ("FVR >= 1.20", d.fvr_put_30_90 >= 1.20)]:
        line(d[m], lab)

    print(f"\n{'='*108}\n  H2 (IV percentile)   — seller wants HIGH IV  [the new test]\n{'='*108}")
    print(hdr); print("  " + "-" * 106)
    for lab, m in [("IV pct <= 30 (low)", d.iv_pct <= 30),
                   ("IV pct 30-70", (d.iv_pct > 30) & (d.iv_pct < 70)),
                   ("IV pct >= 70 (high)", d.iv_pct >= 70),
                   ("IV pct >= 85", d.iv_pct >= 85)]:
        line(d[m], lab)

    print(f"\n{'='*108}\n  H3 (stacked)\n{'='*108}")
    print(hdr); print("  " + "-" * 106)
    line(d[(d.fvr_put_30_90 <= 0.90) & (d.iv_pct >= 70)], "FVR<=0.90 AND IVpct>=70")
    line(d[(d.fvr_put_30_90 <= 0.80) & (d.iv_pct >= 70)], "FVR<=0.80 AND IVpct>=70")
    line(d[(d.fvr_put_30_90 >= 1.20) & (d.iv_pct <= 30)], "worst cell (buyer's setup)")

    print(f"\n{'='*108}\n  WALK-FORWARD BY YEAR (mean seller %)\n{'='*108}")
    arms = {"no gate": d,
            "FVR<=0.90": d[d.fvr_put_30_90 <= 0.90],
            "IVpct>=70": d[d.iv_pct >= 70],
            "both": d[(d.fvr_put_30_90 <= 0.90) & (d.iv_pct >= 70)]}
    print(f"  {'year':<7}" + "".join(f"{k:>14}" for k in arms))
    for y in range(2021, 2026):
        row = f"  {y:<7}"
        for _, g in arms.items():
            s = g[g.yr == y]
            row += f"{(s.seller.mean() if len(s) >= 20 else float('nan')):>+14.2f}"
        print(row)
    print(f"  {'-'*7}" + "".join("-" * 14 for _ in arms))
    row = f"  {'ALL':<7}"
    for _, g in arms.items():
        s = g[g.yr.between(2021, 2025)]
        row += f"{s.seller.mean():>+14.2f}"
    print(row)

    print(f"\n  ⚠ short straddles carry UNBOUNDED loss. 'worst%' above is the single")
    print(f"  worst trade as a multiple of credit — read it before sizing anything.")


if __name__ == "__main__":
    main()
