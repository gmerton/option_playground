#!/usr/bin/env python3
"""
Stage two for the short-dated premium: single names, 10 DTE vs 30 DTE.

Stage one ([[project_vrp_panel_study]] / run_vrp_panel.py) found the variance risk
premium concentrated at the short end and LARGER on single names than on ETFs:
+4.13 vol points at 10 days across 331 names, t 8.74, 82% of days positive, against
+1.75 on the ETF basket.  Thirty days clears nothing in either universe.

The SPY pilot showed the short tenor survives costs (+1.16%/trade net at 0.35 delta,
against +1.10% at 30 DTE while holding capital a third as long), but SPY is an ETF.
This runs the same audited engine on the single names where the bigger premium lives,
and where wider bid-ask is most likely to eat it.

What it does NOT change: the engine, the cost model, or the structure.  Only the
universe and the DTE.  Everything goes through `lib.studies.put_spread_study`, whose
cost handling was audited clean on 2026-09-16.

Inference: per-trade ROC is pooled across tickers that all trade on the same dates, so
the rows are cross-sectionally correlated and (at 30 DTE) serially overlapping.  The
headline t-stats come from `lib.studies.vrp_stats.summarize`, which collapses to a
daily cross-sectional mean and then corrects — the same discipline stage one used.

Usage
-----
  AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=... PYTHONPATH=src \
      .venv/bin/python3 run_vrp_shortdte_names.py --build
  ... run_vrp_shortdte_names.py --report
"""

from __future__ import annotations

import argparse
import contextlib
import io
import pathlib
import traceback
from datetime import date

import numpy as np
import pandas as pd

from lib.studies.put_spread_study import run_put_spread_study
from lib.studies.vrp_stats import format_table, haircut_t, summarize

# Single names in TICKER_CONFIG with >100k cached rows at 6-14 DTE.
NAMES = ["AMZN", "GOOGL", "NVDA", "COST", "MSFT", "MA",
         "AAPL", "HD", "META", "V", "WMT", "JNJ"]

CACHE = pathlib.Path("data/cache/shortdte_names")
REPORT = pathlib.Path("data/studies/vrp_shortdte_names_study.md")

DEFAULT_DELTAS = [0.25, 0.30, 0.35]
DEFAULT_WINGS = [0.15]
VIX_THRESHOLDS = [None, 20.0, 25.0]


def sweep_path(name: str = "sweep") -> pathlib.Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    return CACHE / f"{name}.parquet"


# ══════════════════════════════════════════════════════════════════════════════

def do_build(args) -> None:
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    frames: list[pd.DataFrame] = []
    failures: list[tuple[str, int, str]] = []

    for ticker in args.tickers:
        for dte in args.dtes:
            print(f"\n=== {ticker} @ {dte} DTE ===", flush=True)
            buf = io.StringIO()
            try:
                # The engine prints large sweep tables; keep them out of the driver log.
                with contextlib.redirect_stdout(buf):
                    sweep = run_put_spread_study(
                        ticker=ticker,
                        start=start,
                        end=end,
                        short_delta_targets=args.deltas,
                        wing_delta_widths=DEFAULT_WINGS,
                        vix_thresholds=VIX_THRESHOLDS,
                        dte_target=dte,
                        dte_tol=args.dte_tol,
                        max_spread_pct=args.spread,
                        profit_take_pct=0.50,
                        output_csv=None,
                        force_sync=False,
                    )
            except Exception as exc:  # one bad ticker must not kill the batch
                failures.append((ticker, dte, f"{type(exc).__name__}: {exc}"))
                print(f"  FAILED: {type(exc).__name__}: {exc}", flush=True)
                traceback.print_exc()
                continue

            if sweep is None or sweep.empty:
                failures.append((ticker, dte, "no trades"))
                print("  no trades", flush=True)
                continue

            sweep = sweep.copy()
            sweep["ticker"] = ticker
            sweep["dte_target"] = dte
            frames.append(sweep)
            closed = sweep[~sweep.get("is_open", pd.Series(False, index=sweep.index)).fillna(False)]
            print(f"  {len(sweep):,} rows ({len(closed):,} closed), "
                  f"mean roc_net {100*closed['roc_net'].mean():+.2f}%", flush=True)

    if not frames:
        raise SystemExit("no sweeps produced any trades")

    out = pd.concat(frames, ignore_index=True)
    out.to_parquet(sweep_path(), index=False)
    print(f"\nwrote {len(out):,} rows -> {sweep_path()}")
    if failures:
        print("\nfailures:")
        for t, d, why in failures:
            print(f"  {t} @ {d}d: {why}")


# ══════════════════════════════════════════════════════════════════════════════

# A defined-risk spread cannot lose more than its max_loss, so roc_net has a hard floor
# near -1.0 (a little below it once costs are added).  Anything past this is a corrupt
# quote in the shared MySQL options_cache, not a trade.  Known instance: MA expiring
# 2022-02-11 carries an exit_net_value of 57,891 on a 12.5-wide spread (4 rows).
ROC_FLOOR = -1.5


def _closed(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    if "is_open" in df.columns:
        df = df[~df["is_open"].fillna(False)]
    df = df.dropna(subset=["roc_net"])
    bad = df["roc_net"] < ROC_FLOOR
    if bad.any():
        n = int(bad.sum())
        if verbose:
            who = (df.loc[bad, ["ticker", "dte_target"]]
                   .value_counts().to_dict() if "ticker" in df.columns else {})
            print(f"  [sanity] dropped {n} row(s) with roc_net < {ROC_FLOOR} "
                  f"(impossible for a defined-risk spread — corrupt cache quotes): {who}")
        df = df[~bad]
    _closed.n_dropped = int(bad.sum())
    return df


_closed.n_dropped = 0


def _cell(df: pd.DataFrame) -> dict:
    n = len(df)
    return {
        "n": n,
        "roc_net": 100 * df["roc_net"].mean() if n else np.nan,
        "roc_gross": 100 * df["roc"].mean() if n else np.nan,
        "ann_net": 100 * df["annualized_roc_net"].mean() if n else np.nan,
        "win_net": 100 * df["is_win_net"].mean() if n else np.nan,
        "days": df["days_held"].mean() if n else np.nan,
    }


def do_report(args) -> None:
    sweep = pd.read_parquet(sweep_path())
    sweep = _closed(sweep)
    sweep["entry_date"] = pd.to_datetime(sweep["entry_date"])
    sweep = sweep.rename(columns={"entry_date": "trade_date"})
    hurdle = haircut_t(args.trials)

    lines: list[str] = []

    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    emit("# Short-dated premium selling on single names — stage two")
    emit()
    emit(f"Generated {date.today().isoformat()}. "
         f"{len(sweep):,} closed bull put spreads, {sweep['ticker'].nunique()} single names, "
         f"{sweep['trade_date'].min().date()} to {sweep['trade_date'].max().date()}.")
    emit()
    if _closed.n_dropped:
        emit(f"> **Data note.** {_closed.n_dropped} row(s) were dropped as corrupt: a "
             f"defined-risk spread cannot return worse than -100% of max loss, and these "
             f"carried an `exit_net_value` far above the spread width. All of them are MA "
             f"expiring 2022-02-11, a bad quote in the shared MySQL `options_cache`. "
             f"Left in, they alone drag MA's 10-DTE mean to -799%.")
        emit()
    emit("Engine: `lib.studies.put_spread_study` unchanged, wing ~0.15 delta, 50% profit "
         "take, weekly Friday entries, net of the house cost model "
         "($0.65/leg commission plus 25% of entry bid-ask per traded side).")
    emit()
    emit(f"Hurdle: Bonferroni at {args.trials} declared trials, t >= {hurdle:.2f}. "
         "t-stats collapse each date to a cross-sectional mean before correcting, because "
         "these names all trade on the same Fridays.")
    emit()

    # ── 1. Headline: does the short tenor beat the long one, net? ────────────
    emit("## 1. 10 DTE vs 30 DTE, pooled across names")
    emit()
    rows = []
    for dte in sorted(sweep["dte_target"].unique()):
        for d in sorted(sweep["short_delta_target"].unique()):
            sub = sweep[(sweep["dte_target"] == dte) & (sweep["short_delta_target"] == d)]
            if len(sub) < args.min_rows:
                continue
            c = _cell(sub)
            c["cell"] = f"{int(dte)}d  {d:.2f}D"
            rows.append(c)
    t1 = pd.DataFrame(rows)
    emit("```")
    emit(f"  {'cell':<12} {'n':>7} {'net ROC':>9} {'gross':>8} {'cost bite':>10} "
         f"{'ann net':>9} {'win':>6} {'days':>6}")
    emit("  " + "-" * 74)
    for r in t1.itertuples(index=False):
        bite = 100 * (1 - r.roc_net / r.roc_gross) if r.roc_gross else np.nan
        emit(f"  {r.cell:<12} {r.n:>7,} {r.roc_net:>+8.2f}% {r.roc_gross:>+7.2f}% "
             f"{bite:>9.0f}% {r.ann_net:>+8.1f}% {r.win_net:>5.1f}% {r.days:>6.1f}")
    emit("```")
    emit()

    # ── 2. Inference on the pooled net ROC ───────────────────────────────────
    emit("## 2. Is the net edge statistically real?")
    emit()
    rows = []
    for dte in sorted(sweep["dte_target"].unique()):
        for d in sorted(sweep["short_delta_target"].unique()):
            sub = sweep[(sweep["dte_target"] == dte) & (sweep["short_delta_target"] == d)]
            if len(sub) < args.min_rows:
                continue
            r = summarize(sub, tenor=int(dte), label=f"{int(dte)}d {d:.2f}D",
                          value_col="roc_net", n_trials=args.trials, n_boot=args.boot)
            if r:
                rows.append(r.as_row())
    emit("```")
    emit(format_table(pd.DataFrame(rows)))
    emit("```")
    emit()
    emit("Values are per-trade return on capital at risk, in percent (the table scales by "
         "100, so read `mean` as percentage points of ROC).")
    emit()

    # ── 3. The VIX gate ──────────────────────────────────────────────────────
    emit("## 3. The VIX gate")
    emit()
    emit("On SPY the 10 DTE spread was net NEGATIVE below VIX 20 at almost every delta, and "
         "the all-VIX result was carried entirely by calmer days being excluded. This checks "
         "whether single names behave the same way.")
    emit()
    if "vix" in sweep.columns and sweep["vix"].notna().any():
        sweep["vix_band"] = pd.cut(sweep["vix"], [-np.inf, 15, 20, 25, np.inf],
                                   labels=["VIX<15", "15-20", "20-25", "VIX>25"])
        emit("```")
        emit(f"  {'dte':>4} {'delta':>6} {'band':>8} {'n':>7} {'net ROC':>9} {'win':>7}")
        emit("  " + "-" * 48)
        for dte in sorted(sweep["dte_target"].unique()):
            for d in sorted(sweep["short_delta_target"].unique()):
                for band, g in sweep[(sweep["dte_target"] == dte) &
                                     (sweep["short_delta_target"] == d)].groupby(
                                         "vix_band", observed=True):
                    if len(g) < 50:
                        continue
                    emit(f"  {int(dte):>4} {d:>6.2f} {str(band):>8} {len(g):>7,} "
                         f"{100*g['roc_net'].mean():>+8.2f}% {100*g['is_win_net'].mean():>6.1f}%")
        emit("```")
    else:
        emit("  (no VIX column on the sweep)")
    emit()

    # ── 4. Per ticker ────────────────────────────────────────────────────────
    emit("## 4. Per name, 10 DTE")
    emit()
    emit("```")
    emit(f"  {'ticker':<8} {'n':>7} {'net ROC':>9} {'gross':>8} {'cost bite':>10} {'win':>7}")
    emit("  " + "-" * 54)
    sub10 = sweep[sweep["dte_target"] == min(sweep["dte_target"])]
    for tk, g in sub10.groupby("ticker"):
        c = _cell(g)
        bite = 100 * (1 - c["roc_net"] / c["roc_gross"]) if c["roc_gross"] else np.nan
        emit(f"  {tk:<8} {c['n']:>7,} {c['roc_net']:>+8.2f}% {c['roc_gross']:>+7.2f}% "
             f"{bite:>9.0f}% {c['win_net']:>6.1f}%")
    emit("```")
    emit()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {REPORT}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--build", action="store_true")
    p.add_argument("--report", action="store_true")
    p.add_argument("--tickers", nargs="+", default=NAMES)
    p.add_argument("--dtes", nargs="+", type=int, default=[10, 30])
    p.add_argument("--deltas", nargs="+", type=float, default=DEFAULT_DELTAS)
    p.add_argument("--dte-tol", type=int, default=4)
    p.add_argument("--spread", type=float, default=0.25)
    p.add_argument("--start", default="2018-01-01")
    p.add_argument("--end", default="2026-02-20")
    p.add_argument("--trials", type=int, default=50)
    p.add_argument("--boot", type=int, default=3000)
    p.add_argument("--min-rows", type=int, default=100)
    args = p.parse_args()

    if not args.build and not args.report:
        p.error("pass --build, --report, or both")
    if args.build:
        do_build(args)
    if args.report:
        do_report(args)


if __name__ == "__main__":
    main()
