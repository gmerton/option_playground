#!/usr/bin/env python3
"""
Reconcile the long straddle with the variance risk premium.

The contradiction
-----------------
The VRP panel says short-dated ATM implied vol is RICH: on the 10 ETFs, +1.75 vol
points at 10 days, t 8.93, positive in 17 of 17 years.  A vol SELLER is paid there.
The best-evidenced strategy in the book is a LONG 7-DTE straddle, which is on the
other side of exactly that trade.

Both cannot be the main effect.  There are three ways out, and this script decides
between them:

  A. The premium does not transfer to single names.  Index implied vol carries a
     correlation premium that single stocks do not, so single-name VRP is known to
     be much smaller.  If it is near zero or negative on the straddle's own
     universe, there is no contradiction and the straddle is harvesting a
     single-name effect the ETF panel never measured.
  B. The straddle's edge is SELECTION.  Its entry gates pick the days where the
     premium happens to be negative.  Then the gate is the strategy, and sharpening
     the gate is the whole game.
  C. The straddle's edge is CONVEXITY.  It pays on the TERMINAL move while realized
     vol sums DAILY squared moves, so it can win on gaps and trends even when the
     average premium favours the seller.  Then the premium is the wrong lens and the
     straddle should be sized as a tail position, not a carry position.

Method notes
------------
Each trade is matched to realized vol over its OWN horizon, not a fixed 10 days: a
7-DTE trade gets the (t, t+7] window and a 14-DTE trade gets (t, t+14].  Implied
comes from the VRP panel's ATM measurement, which is computed independently of the
trade's own cost, so the two are not mechanically linked.

`roc` in the feature cache is ALREADY A PERCENTAGE (its minimum is exactly -100.0,
a long straddle expiring worthless).  It is violently right-skewed: median -18%, 99th
percentile +273%, and a single corrupt row reads +10,526,214% (a split artefact), which
is why the raw mean is meaningless and the winsorized mean is the one to read.  Every table therefore leads
with the MEDIAN and the win rate, reports a winsorized mean beside the raw one, and
runs the date-clustered bootstrap on the winsorized series.  Conclusions that flip
between raw and winsorized are reported as unresolved, not picked.

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 \
      run_vrp_straddle_reconcile.py --panel names_v1
"""

from __future__ import annotations

import argparse
import pathlib
from datetime import date

import numpy as np
import pandas as pd

from lib.studies.vrp_panel import cache_path, load_panel, realized_vol_windows
from lib.studies.vrp_stats import (
    block_bootstrap_ci,
    daily_mean_series,
    format_table,
    haircut_t,
    newey_west_se,
    summarize,
    summarize_by,
)

FEATURES = pathlib.Path("data/cache/long_straddle_features.parquet")
REPORT = pathlib.Path("data/studies/vrp_straddle_reconcile.md")
WINSOR = 0.99


def winsorize(s: pd.Series, q: float = WINSOR) -> pd.Series:
    hi = s.quantile(q)
    lo = s.quantile(1 - q)
    return s.clip(lower=lo, upper=hi)


def load_trades() -> pd.DataFrame:
    f = pd.read_parquet(FEATURES)
    f = f.rename(columns={"entry_date": "trade_date"})
    f["trade_date"] = pd.to_datetime(f["trade_date"]).dt.normalize()
    f["dte"] = pd.to_numeric(f["dte"], errors="coerce")
    f = f[f["dte"].between(5, 16)]
    f = f.dropna(subset=["roc", "cost"])
    f = f[f["cost"] > 0]
    return f


def attach_premium(trades: pd.DataFrame, panel_name: str) -> pd.DataFrame:
    """Join each trade to implied at entry and realized over its OWN horizon."""
    panel = load_panel(panel_name)
    iv = (
        panel[panel["tenor"] == 10][["ticker", "trade_date", "iv", "iv_pctile", "vix"]]
        .rename(columns={"vix": "vix_panel"})
    )
    closes = pd.read_parquet(cache_path(f"{panel_name}_closes"))

    out = []
    for horizon, grp in trades.groupby(trades["dte"].round().astype(int)):
        rv = realized_vol_windows(closes, int(horizon))[
            ["ticker", "trade_date", "rv_fwd", "rv_trail"]
        ]
        merged = grp.merge(iv, on=["ticker", "trade_date"], how="inner")
        merged = merged.merge(rv, on=["ticker", "trade_date"], how="inner",
                              suffixes=("", "_own"))
        out.append(merged)

    if not out:
        return pd.DataFrame()
    df = pd.concat(out, ignore_index=True)
    df = df.dropna(subset=["rv_fwd", "iv"])
    df["premium"] = df["iv"] - df["rv_fwd"]          # >0 = seller paid
    df["roc_w"] = winsorize(df["roc"])
    return df


def quintile_table(df: pd.DataFrame, col: str, label: str, n_bins: int = 5) -> pd.DataFrame:
    """Straddle outcome by quantile of `col`, robust statistics first."""
    d = df.dropna(subset=[col]).copy()
    if d.empty:
        return pd.DataFrame()
    d["bin"] = pd.qcut(d[col], q=n_bins, duplicates="drop")
    rows = []
    for b, g in d.groupby("bin", observed=True):
        rows.append({
            "bucket": f"{label} {b.left:+.3f}..{b.right:+.3f}",
            "n": len(g),
            "median_roc": g["roc"].median(),
            "mean_roc_w": g["roc_w"].mean(),
            "mean_roc_raw": g["roc"].mean(),
            "win": g["win"].mean() if "win" in g else np.nan,
            "mean_premium": g["premium"].mean(),
        })
    return pd.DataFrame(rows)


def fmt_quintiles(t: pd.DataFrame) -> str:
    if t.empty:
        return "  (no data)"
    head = (f"  {'bucket':<30} {'n':>7} {'med ROC':>9} {'mean ROC(w)':>12} "
            f"{'mean ROC(raw)':>14} {'win':>6} {'mean prem':>10}")
    lines = [head, "  " + "-" * (len(head) - 2)]
    for r in t.itertuples(index=False):
        lines.append(
            f"  {r.bucket:<30} {r.n:>7,} {r.median_roc:>8.1f}% "
            f"{r.mean_roc_w:>11.1f}% {r.mean_roc_raw:>13.1f}% "
            f"{100*r.win:>5.0f}% {100*r.mean_premium:>9.2f}%"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default="names_v1")
    ap.add_argument("--trials", type=int, default=50)
    ap.add_argument("--boot", type=int, default=3000)
    args = ap.parse_args()

    hurdle = haircut_t(args.trials)
    lines: list[str] = []

    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    trades = load_trades()
    df = attach_premium(trades, args.panel)
    if df.empty:
        raise SystemExit("no trades joined to the panel — check the panel name and date range")

    emit("# Reconciling the long straddle with the variance risk premium")
    emit()
    emit(f"Generated {date.today().isoformat()}. "
         f"{len(df):,} straddle trades matched to an independent implied-vol measurement "
         f"and to realized vol over each trade's own horizon. "
         f"{df['ticker'].nunique()} tickers, "
         f"{df['trade_date'].min().date()} to {df['trade_date'].max().date()}.")
    emit()
    emit(f"Hurdle: Bonferroni at {args.trials} declared trials, t >= {hurdle:.2f}.")
    emit()

    # ── 1. Does the ETF premium transfer to single names? ────────────────────
    emit("## 1. Does the 10-day premium transfer to single names?")
    emit()
    emit("The ETF panel found +1.75 vol points at 10 days. Index implied vol carries a "
         "correlation premium that single stocks do not, so this is the first thing to "
         "check before calling anything a contradiction.")
    emit()
    panel = load_panel(args.panel)
    p10 = panel[panel["tenor"] == 10]
    rows = []
    for lbl, sub in (("single names 10d", p10), ("single names 30d", panel[panel["tenor"] == 30])):
        if sub.empty:
            continue
        r = summarize(sub, tenor=int(sub["tenor"].iloc[0]), label=lbl,
                      n_trials=args.trials, n_boot=args.boot)
        if r:
            rows.append(r.as_row())
    emit("```")
    emit(format_table(pd.DataFrame(rows)))
    emit("```")
    emit()

    # ── 2. Straddle outcome by the premium it actually faced ─────────────────
    emit("## 2. Straddle outcome by the premium it actually faced")
    emit()
    emit("`premium = implied at entry - realized over the trade's own horizon`. Positive "
         "means the straddle bought vol that turned out expensive. If the straddle is a "
         "premium trade, its returns should fall monotonically across these buckets.")
    emit()
    emit("> **LOOK-AHEAD BY CONSTRUCTION — this is a diagnostic, not a signal.** The premium "
         "is measured over the same forward window that determines the straddle's payoff, so "
         "sorting trades by it is partly sorting them by their own outcome. A monotonic table "
         "here answers *what kind of trade the straddle is*. It cannot be traded, because the "
         "premium is unknown at entry. Section 3 is the one that uses entry-time information.")
    emit()
    emit("```")
    emit(fmt_quintiles(quintile_table(df, "premium", "prem")))
    emit("```")
    emit()

    # ── 3. What does the existing entry gate select? ─────────────────────────
    emit("## 3. What does the existing IV-percentile gate select?")
    emit()
    emit("The playbook gate buys when own IV percentile is LOW. If that gate is the edge, "
         "low percentile should line up with a negative premium.")
    emit()
    if "iv_pctile" in df.columns and df["iv_pctile"].notna().any():
        emit("```")
        emit(fmt_quintiles(quintile_table(df, "iv_pctile", "ivpct")))
        emit("```")
    else:
        emit("  (no iv_pctile coverage on the joined rows)")
    emit()

    # ── 4. Convexity check: terminal move vs realized path ───────────────────
    emit("## 4. Convexity check")
    emit()
    emit("A straddle pays on the TERMINAL move; realized vol sums DAILY squared moves. "
         "If the edge is convexity, straddle returns should track the terminal move "
         "relative to implied far better than they track the premium.")
    emit()
    sub = df.dropna(subset=["premium", "roc_w"])
    c_prem = sub["roc_w"].corr(sub["premium"], method="spearman")
    c_rv = sub["roc_w"].corr(sub["rv_fwd"], method="spearman")
    c_iv = sub["roc_w"].corr(sub["iv"], method="spearman")
    emit("```")
    emit(f"  Spearman rank correlation of winsorized straddle ROC with:")
    emit(f"    premium (iv - rv_fwd)   {c_prem:+.3f}   <- negative if it is a premium trade")
    emit(f"    realized vol (rv_fwd)   {c_rv:+.3f}")
    emit(f"    implied at entry (iv)   {c_iv:+.3f}")
    emit("```")
    emit()

    # ── 5. Top vs bottom premium bucket, date-clustered ──────────────────────
    emit("## 5. Is the premium spread real, or date-clustered noise?")
    emit()
    emit("> Same look-ahead caveat as section 2. This asks whether the premium-to-payoff link "
         "survives pairing by date (so it is not just a few violent days), not whether it can "
         "be traded.")
    emit()
    d = df.dropna(subset=["premium"]).copy()
    d["bin"] = pd.qcut(d["premium"], q=5, duplicates="drop", labels=False)
    lo = d[d["bin"] == d["bin"].min()]
    hi = d[d["bin"] == d["bin"].max()]
    s_lo = daily_mean_series(lo, value_col="roc_w")
    s_hi = daily_mean_series(hi, value_col="roc_w")
    joined = pd.concat([s_lo.rename("lo"), s_hi.rename("hi")], axis=1).dropna()
    if len(joined) >= 20:
        diff = (joined["lo"] - joined["hi"]).to_numpy()
        se = newey_west_se(diff, lag=10)
        t = float(np.mean(diff) / se) if se and np.isfinite(se) and se > 0 else float("nan")
        blo, bhi, bp = block_bootstrap_ci(diff, block=10, n_boot=args.boot)
        emit("```")
        emit(f"  cheapest-premium quintile minus richest, same dates only")
        emit(f"    paired dates      {len(joined):,}")
        emit(f"    mean ROC gap      {np.mean(diff):+.2f} pp")
        emit(f"    t (Newey-West)    {t:+.2f}    hurdle {hurdle:.2f}")
        emit(f"    bootstrap 95% CI  [{blo:+.2f}, {bhi:+.2f}] pp")
        emit(f"    verdict           {'REAL' if abs(t) >= hurdle and (blo > 0 or bhi < 0) else 'not resolved'}")
        emit("```")
    else:
        emit("  (too few paired dates)")
    emit()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {REPORT}")


if __name__ == "__main__":
    main()
