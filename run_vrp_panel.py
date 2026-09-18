#!/usr/bin/env python3
"""
Stage-one variance-risk-premium screen.

Measures  iv - rv_fwd  directly instead of simulating a structure and reading its
P&L.  Same economic question as the path studies, far more statistical power,
because it uses every daily return in the window rather than one terminal price.

This does NOT decide whether a trade is capturable — costs, fills, strike drift and
gamma weighting all live in the stage-two path backtests.  It decides whether there
is anything there to capture, which is the cheap question to answer first.

Usage
-----
  # Build + cache the panel (Athena + yfinance; ~10 ETFs x 3 tenors ~ a few minutes)
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_vrp_panel.py \
      --build --universe etf --start 2010-01-01

  # Re-run the analysis off the cache (instant)
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_vrp_panel.py --report

  # Declare how many hypotheses the research program has consumed
  ... run_vrp_panel.py --report --trials 50

Universes
---------
  etf      the 10 names the calendar path study ran on — deliberately the set where
           we already know the stage-two answer, so this run doubles as a check on
           whether the cheap estimator predicts the expensive one
  index    SPY QQQ IWM only
  <list>   comma-separated tickers
"""

from __future__ import annotations

import argparse
import pathlib
from datetime import date

import numpy as np
import pandas as pd

from lib.studies.vrp_panel import (
    TENORS,
    build_forward_premium,
    build_panel,
    fetch_closes,
    load_panel,
    save_panel,
    cache_path,
)
from lib.studies.vrp_stats import (
    format_table,
    haircut_t,
    summarize,
    summarize_by,
)

# The calendar path study universe.  Same names, so the two estimators are directly
# comparable on the same tape.
ETF_UNIVERSE = ["SPY", "QQQ", "IWM", "XLU", "XLV", "XLP", "XLE", "XLF", "GLD", "TLT"]
INDEX_UNIVERSE = ["SPY", "QQQ", "IWM"]

REPORT_PATH = pathlib.Path("data/studies/vrp_panel_study.md")


def resolve_universe(spec: str, ticker_file: str | None = None) -> list[str]:
    if ticker_file:
        raw = pathlib.Path(ticker_file).read_text().split()
        return list(dict.fromkeys(t.strip().upper() for t in raw if t.strip()))
    key = spec.strip().lower()
    if key == "etf":
        return ETF_UNIVERSE
    if key == "index":
        return INDEX_UNIVERSE
    return [t.strip().upper() for t in spec.split(",") if t.strip()]


# ══════════════════════════════════════════════════════════════════════════════

def do_build(args) -> None:
    tickers = resolve_universe(args.universe, args.ticker_file)
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else date.today()
    tenors = [int(t) for t in args.tenors]

    print(f"\nBuilding VRP panel")
    print(f"  universe : {len(tickers)} tickers"
          f"{'' if len(tickers) > 15 else ' ' + str(tickers)}")
    print(f"  dates    : {start} -> {end}")
    print(f"  tenors   : {tenors}")
    print(f"  ATM IV   : {'calls+puts' if not args.cp else args.cp} averaged, |delta| 0.45-0.55\n")

    pad = max(tenors) + 40
    closes = fetch_closes(
        tickers,
        (pd.Timestamp(start) - pd.Timedelta(days=pad + 400)).date(),
        (pd.Timestamp(end) + pd.Timedelta(days=pad)).date(),
    )
    print(f"  closes: {len(closes):,} rows, {closes['ticker'].nunique()} tickers, "
          f"{closes['trade_date'].min().date()} -> {closes['trade_date'].max().date()}\n")

    panel = build_panel(tickers, start, end, tenors=tenors, cp=args.cp, closes=closes)
    save_panel(panel, args.name)

    closes.to_parquet(cache_path(f"{args.name}_closes"), index=False)
    print(f"  wrote {len(closes):,} close rows -> {cache_path(f'{args.name}_closes')}")

    print("\nPanel coverage by tenor:")
    for tenor, g in panel.groupby("tenor"):
        ok = g.dropna(subset=["vrp"])
        print(f"  {tenor:>3}d: {len(g):>8,} rows  {len(ok):>8,} with complete forward window  "
              f"{ok['trade_date'].min().date()} -> {ok['trade_date'].max().date()}")


# ══════════════════════════════════════════════════════════════════════════════

def _regime_col(df: pd.DataFrame) -> pd.Series:
    """Coarse VIX regime, observable at entry."""
    v = df.get("vix")
    if v is None:
        return pd.Series("all", index=df.index)
    return pd.cut(
        v, bins=[-np.inf, 15, 20, 25, np.inf],
        labels=["VIX<15", "VIX 15-20", "VIX 20-25", "VIX>25"],
    )


def do_report(args) -> None:
    panel = load_panel(args.name)
    closes = pd.read_parquet(cache_path(f"{args.name}_closes"))
    trials = args.trials
    hurdle = haircut_t(trials)

    lines: list[str] = []

    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    ok = panel.dropna(subset=["vrp"])
    emit(f"# Variance risk premium panel — stage-one screen")
    emit()
    emit(f"Generated {date.today().isoformat()}. "
         f"Universe: {', '.join(sorted(panel['ticker'].unique()))}.")
    emit(f"Sample {ok['trade_date'].min().date()} to {ok['trade_date'].max().date()}, "
         f"{len(ok):,} ticker-days with a complete forward window.")
    emit()
    emit("`vrp = ATM implied vol - realized vol over the matching forward window`, in "
         "annualized vol points. Positive means implied was rich and a vol SELLER was "
         "paid. Negative means implied was cheap and a vol BUYER was paid.")
    emit()
    emit(f"**Inference.** Rows overlap (a 30-day window observed daily repeats 29/30 of "
         f"itself) and tickers are cross-sectionally correlated, so a plain t-test is "
         f"badly wrong here. Each cell is collapsed to a daily cross-sectional mean, then "
         f"corrected with Newey-West at the overlap lag and a moving-block bootstrap. "
         f"`t_naive` is printed only to show the size of the error. The hurdle is "
         f"Bonferroni at {trials} declared trials: **t >= {hurdle:.2f}**, not 2.0.")
    emit()

    # ── 1. Headline: is there a premium at each tenor ────────────────────────
    emit("## 1. Premium by tenor (pooled)")
    emit()
    emit("```")
    rows = []
    for tenor in sorted(panel["tenor"].unique()):
        sub = panel[panel["tenor"] == tenor]
        res = summarize(sub, tenor=int(tenor), label=f"{int(tenor)}d pooled",
                        n_trials=trials, n_boot=args.boot)
        if res:
            rows.append(res.as_row())
    pooled = pd.DataFrame(rows)
    emit(format_table(pooled))
    emit("```")
    emit()

    # ── 2. Per ticker, per tenor ─────────────────────────────────────────────
    for tenor in sorted(panel["tenor"].unique()):
        sub = panel[panel["tenor"] == tenor]
        tbl = summarize_by(sub, "ticker", tenor=int(tenor), n_trials=trials,
                           n_boot=args.boot, min_rows=args.min_rows)
        if tbl.empty:
            continue
        emit(f"## 2.{int(tenor)} Premium by ticker — {int(tenor)}d")
        emit()
        emit("```")
        emit(format_table(tbl))
        emit("```")
        emit()

    # ── 3. Conditioning on observable state ──────────────────────────────────
    emit("## 3. Conditioning on state observable at entry")
    emit()
    emit("Every column used here is known at t. `iv_pctile` is own-IV rank vs its "
         "trailing 252 observations, the gate that works on the paid-to-wait put "
         "spreads. `vrp_trail` is implied minus TRAILING realized, the naive richness "
         "proxy a desk can see without forecasting anything.")
    emit()
    for tenor in sorted(panel["tenor"].unique()):
        sub = panel[panel["tenor"] == tenor].copy()
        sub["iv_pctile_bucket"] = pd.cut(
            sub["iv_pctile"], bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
            labels=["IVpct 0-20", "IVpct 20-40", "IVpct 40-60", "IVpct 60-80", "IVpct 80-100"],
        )
        sub["vix_regime"] = _regime_col(sub)
        sub["vrp_trail_bucket"] = pd.qcut(
            sub["vrp_trail"], q=4,
            labels=["trail Q1 (cheap)", "trail Q2", "trail Q3", "trail Q4 (rich)"],
            duplicates="drop",
        )
        for col, title in (
            ("iv_pctile_bucket", "own IV percentile"),
            ("vix_regime", "VIX regime"),
            ("vrp_trail_bucket", "implied vs trailing realized"),
        ):
            tbl = summarize_by(sub, col, tenor=int(tenor), n_trials=trials,
                               n_boot=args.boot, min_rows=args.min_rows)
            if tbl.empty:
                continue
            emit(f"### {int(tenor)}d by {title}")
            emit()
            emit("```")
            emit(format_table(tbl))
            emit("```")
            emit()

    # ── 4. By year — the halves / stability check ────────────────────────────
    emit("## 4. Stability by year")
    emit()
    for tenor in sorted(panel["tenor"].unique()):
        sub = panel[panel["tenor"] == tenor].copy()
        sub["yr"] = sub["trade_date"].dt.year
        tbl = summarize_by(sub, "yr", tenor=int(tenor), n_trials=trials,
                           n_boot=args.boot, min_rows=args.min_rows)
        if tbl.empty:
            continue
        tbl = tbl.sort_values("label")
        emit(f"### {int(tenor)}d by year")
        emit()
        emit("```")
        emit(format_table(tbl))
        emit("```")
        emit()

    # ── 5. Term-structure premium — the calendar question ────────────────────
    if {30, 90}.issubset(set(panel["tenor"].unique())):
        emit("## 5. Term-structure premium (the calendar question)")
        emit()
        emit("Forward implied vol between day 30 and day 90, minus the realized vol that "
             "then shows up in exactly that window. This is what a 30/90 calendar or a "
             "forward-factor trade is reaching for. The calendar path study found no "
             "capturable edge on these same names; this says whether the premium was "
             "absent in the first place or present but uncapturable.")
        emit()
        fwd = build_forward_premium(panel, closes, near=30, far=90)
        if fwd.empty:
            emit("  (no overlapping 30d and 90d IV — cannot compute)")
        else:
            fwd["fvr_bucket"] = pd.qcut(
                fwd["fvr"], q=4,
                labels=["FVR Q1 (flat/inv)", "FVR Q2", "FVR Q3", "FVR Q4 (steep)"],
                duplicates="drop",
            )
            res = summarize(fwd, tenor=60, label="fwd 30->90 pooled", value_col="fwd_vrp",
                            n_trials=trials, n_boot=args.boot)
            emit("```")
            emit(format_table(pd.DataFrame([res.as_row()]) if res else pd.DataFrame()))
            emit("```")
            emit()
            for col, title in (("ticker", "ticker"), ("fvr_bucket", "forward vol ratio")):
                tbl = summarize_by(fwd, col, tenor=60, value_col="fwd_vrp",
                                   n_trials=trials, n_boot=args.boot, min_rows=args.min_rows)
                if tbl.empty:
                    continue
                emit(f"### forward 30->90 premium by {title}")
                emit()
                emit("```")
                emit(format_table(tbl))
                emit("```")
                emit()

    emit("## How to read this")
    emit()
    emit("- A cell only counts as a finding when `t_NW` clears the hurdle AND the "
         "bootstrap interval excludes zero. The `ok` column marks those.")
    emit("- The gap between `t_naive` and `t_NW` is the overlap correction. Where it is "
         "large, any past study that ran a plain t-test on daily rows was reading noise.")
    emit("- A positive premium is a screen result, not a trade. It says a vol seller was "
         "paid gross. Whether a real structure keeps any of it after spreads, commissions, "
         "gamma weighting and direction risk is the stage-two path backtest's job.")
    emit("- A premium near zero is the informative null: no structure over those names and "
         "that tenor can manufacture an edge, so stop building them.")
    emit()
    emit("## What this estimator is not")
    emit()
    emit("- **Vol, not variance.** It compares ATM implied vol to realized vol. An option "
         "position's P&L is linear in variance, not vol, so the mapping to dollars is not "
         "one to one. Fine for ranking and for sign, wrong for sizing.")
    emit("- **ATM, not the whole smile.** A variance swap rate integrates every strike and "
         "sits above ATM implied because of the smile. The true premium is therefore a bit "
         "LARGER than what is printed here, which makes this a conservative screen.")
    emit("- **No costs.** Gross of spreads, commissions and assignment. The put-spread and "
         "straddle engines already carry `lib.studies.costs`; nothing here does, by design.")
    emit("- **Realized vol is close-to-close.** It ignores intraday range and overnight gaps "
         "priced separately, so it slightly understates what a gamma position actually "
         "experiences.")
    emit("- **Split adjustment is correct here.** Closes are yfinance auto-adjusted, which is "
         "right for returns. The usual split-vs-strike caveat does not apply because this "
         "panel never touches a strike.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n")
    print(f"\nWrote report -> {REPORT_PATH}")


# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--build", action="store_true", help="build and cache the panel")
    p.add_argument("--report", action="store_true", help="analyze the cached panel")
    p.add_argument("--universe", default="etf", help="etf | index | comma-separated tickers")
    p.add_argument("--ticker-file", default=None,
                   help="file with one ticker per line; overrides --universe")
    p.add_argument("--name", default="etf_v1", help="cache name (default: etf_v1)")
    p.add_argument("--start", default="2010-01-01")
    p.add_argument("--end", default=None)
    p.add_argument("--tenors", nargs="+", default=[10, 30, 90], help=f"from {sorted(TENORS)}")
    p.add_argument("--cp", default=None, choices=[None, "C", "P"],
                   help="restrict ATM IV to one side (default: average calls and puts)")
    p.add_argument("--trials", type=int, default=50,
                   help="hypotheses the research program has consumed, for the Bonferroni "
                        "hurdle (default 50)")
    p.add_argument("--boot", type=int, default=2000, help="bootstrap resamples")
    p.add_argument("--min-rows", type=int, default=200, help="min rows for a reported cell")
    args = p.parse_args()

    if not args.build and not args.report:
        p.error("pass --build, --report, or both")
    if args.build:
        do_build(args)
    if args.report:
        do_report(args)


if __name__ == "__main__":
    main()
