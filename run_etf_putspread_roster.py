#!/usr/bin/env python3
"""
Rebuild the 20-ETF bull put spread roster from COMMITTED code (TEST_INDEX §10, queued 2026-09-20).

Why this exists: the in-book half of the certified straddle + bull-put PAIR lives only in a gitignored
cache, `data/cache/rsi_putspread.parquet` (6,739 trades, +5.68%/trade), which was derived by
`run_rsi_conditioning_study.py` §A from `data/cache/etf_condor_recon.parquet` -- and THAT was written by
a session scratchpad (`ps_recon.py`) that was never committed. So a headline book number currently has no
reproducible provenance. This script rebuilds it from `lib.studies.put_spread_study` and diffs.

Spec (etf_put_spread_exit_rule_2026-09-16.md): 20 ETFs, every Friday 2018 -> Feb 2026, sell the 0.35d put
and buy the 0.25d put at the expiry nearest 45 days, take profit at 50% of the credit, NO stop, otherwise
hold to expiry. Return on margin (width - credit). Filters applied downstream by the RSI script:
credit/width <= 0.50, margin >= 0.10, exit_type != 'missing', expiry <= 2026-03-31, and the ROC-ceiling
filter roc <= credit/margin (condor study §0: 2.3% of wings score above the theoretical ceiling, i.e. a
negative exit value = a crossed or stale mark, not a trade).

PASS = reproduces n ~ 6,739 and +5.68%/trade with per-ticker means in line.

This script also reports what the cached roc does NOT: the after-cost number (`roc_net`, the house model:
$0.65/contract/leg/side + 25% of each leg's quoted bid-ask), and the missing-exit diagnostic.

Usage:
  MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 run_etf_putspread_roster.py \
      > data/studies/etf_putspread_roster_rebuild.log 2>&1
"""
from __future__ import annotations

import warnings
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)

REPO = Path(__file__).resolve().parent
OUT = REPO / "data/cache/etf_putspread_roster.parquet"
REF = REPO / "data/cache/rsi_putspread.parquet"

# The 20 names, read off the reference cache's own ticker list.
ROSTER = ["ASHR", "EEM", "FXI", "GDX", "GLD", "INDA", "IWM", "QQQ", "SOXX", "SPY",
          "TLT", "USO", "XBI", "XLE", "XLF", "XLK", "XLP", "XLU", "XLV", "XOP"]

SHORT_DELTA, WING_WIDTH = 0.35, 0.10
DTE_TARGET, DTE_TOL = 45, 5
TAKE = 0.50
ENTRY_START, ENTRY_END = date(2018, 1, 1), date(2026, 2, 28)
EXPIRY_CAP = pd.Timestamp("2026-03-31")


def build_one(ticker: str) -> pd.DataFrame:
    """Every trade for one ticker, unfiltered, with metrics. Per-ticker on purpose: the exit scanner
    joins marks on (expiry, strike) with NO ticker column, so a pooled frame would cross-contaminate."""
    from lib.mysql_lib import fetch_options_cache
    from lib.studies.put_spread_study import (
        build_put_spread_trades, compute_spread_metrics, find_put_spread_exits,
    )

    df = fetch_options_cache(ticker, ENTRY_START, ENTRY_END + timedelta(days=DTE_TARGET + DTE_TOL + 30))
    if df.empty:
        print(f"  {ticker}: no option rows"); return pd.DataFrame()

    pos = build_put_spread_trades(
        df, short_delta_target=SHORT_DELTA, wing_delta_width=WING_WIDTH,
        dte_target=DTE_TARGET, dte_tol=DTE_TOL, entry_weekday=4,
    )
    if pos.empty:
        print(f"  {ticker}: no spreads built"); return pd.DataFrame()
    pos = pos[pd.to_datetime(pos["entry_date"]) <= pd.Timestamp(ENTRY_END)].reset_index(drop=True)

    ex = find_put_spread_exits(pos, df, profit_take_pct=TAKE, stop_multiple=None)
    m = compute_spread_metrics(ex)
    m.insert(0, "ticker", ticker)
    print(f"  {ticker}: {len(m):,} raw trades  "
          f"({(m.exit_type == 'missing').mean():.1%} missing exit)")
    return m


def apply_filters(m: pd.DataFrame) -> pd.DataFrame:
    """The four filters run_rsi_conditioning_study.py §A applies, in the same order."""
    m = m.copy()
    m["cw"] = m["net_credit_mid"] / (m["short_strike"] - m["long_strike"]).abs()
    m["margin"] = m["spread_width"] - m["net_credit_mid"]
    m["roc_pct"] = m["roc"] * 100.0          # the cache stores roc in percent
    keep = (
        (m["cw"] <= 0.50)
        & (m["margin"] >= 0.10)
        & (m["exit_type"] != "missing")
        & (pd.to_datetime(m["expiry"]) <= EXPIRY_CAP)
        & (m["roc_pct"] <= 100.0 * m["net_credit_mid"] / m["margin"] + 1e-6)
    )
    return m[keep].reset_index(drop=True)


def wtstat(x: pd.Series, d: pd.Series, freq: str) -> float:
    g = x.groupby(pd.to_datetime(d).dt.to_period(freq)).mean()
    return float(g.mean() / g.std() * np.sqrt(len(g))) if len(g) > 2 else np.nan


def main() -> None:
    print(f"Rebuilding the 20-ETF bull put roster from committed code ({date.today()})")
    print(f"  {SHORT_DELTA}/{SHORT_DELTA - WING_WIDTH} delta, {DTE_TARGET} DTE +/-{DTE_TOL}, "
          f"Friday entries, {TAKE:.0%} take, no stop, {ENTRY_START} -> {ENTRY_END}\n")

    raw = pd.concat([build_one(t) for t in ROSTER], ignore_index=True)
    raw.to_parquet(REPO / "data/cache/etf_putspread_roster_raw.parquet")
    kept = apply_filters(raw)
    kept.to_parquet(OUT)

    print(f"\nraw {len(raw):,} trades -> {len(kept):,} after filters")
    for name, mask in [
        ("credit/width > 0.50", raw["net_credit_mid"] / (raw["short_strike"] - raw["long_strike"]).abs() > 0.50),
        ("margin < 0.10", (raw["spread_width"] - raw["net_credit_mid"]) < 0.10),
        ("exit_type == missing", raw["exit_type"] == "missing"),
        ("expiry > 2026-03-31", pd.to_datetime(raw["expiry"]) > EXPIRY_CAP),
    ]:
        print(f"  dropped by {name:24s} {int(mask.sum()):>6,}")

    # ── The headline vs the reference cache ───────────────────────────────────
    ref = pd.read_parquet(REF)
    print(f"\n{'':22s} {'n':>7s} {'mean %':>9s} {'median %':>9s} {'win %':>7s} {'week t':>8s} {'month t':>8s}")
    for label, n, r, d in [
        ("REBUILD (this script)", len(kept), kept["roc_pct"], kept["entry_date"]),
        ("REFERENCE (cache)",     len(ref),  ref["roc"],      ref["entry_date"]),
    ]:
        print(f"{label:22s} {n:>7,} {r.mean():>9.3f} {r.median():>9.3f} "
              f"{100 * (r > 0).mean():>7.1f} {wtstat(r, d, 'W-FRI'):>8.2f} {wtstat(r, d, 'M'):>8.2f}")

    # ── After costs: what the cached number leaves out ────────────────────────
    rn = kept["roc_net"] * 100.0
    print(f"\n{'REBUILD after costs':22s} {len(kept):>7,} {rn.mean():>9.3f} {rn.median():>9.3f} "
          f"{100 * (rn > 0).mean():>7.1f} {wtstat(rn, kept.entry_date, 'W-FRI'):>8.2f} "
          f"{wtstat(rn, kept.entry_date, 'M'):>8.2f}")
    print(f"  cost drag {kept['roc_pct'].mean() - rn.mean():+.2f}pp/trade "
          f"= {100 * (kept['roc_pct'].mean() - rn.mean()) / max(kept['roc_pct'].mean(), 1e-9):.0f}% of the gross edge")

    # ── Per ticker ────────────────────────────────────────────────────────────
    a = kept.groupby("ticker").agg(n=("roc_pct", "size"), mean=("roc_pct", "mean"))
    b = ref.groupby("ticker").agg(n_ref=("roc", "size"), mean_ref=("roc", "mean"))
    cmp = a.join(b, how="outer")
    cmp["d_n"] = cmp["n"] - cmp["n_ref"]
    cmp["d_mean"] = cmp["mean"] - cmp["mean_ref"]
    cmp["net"] = kept.groupby("ticker").roc_net.mean() * 100
    print("\nper ticker (rebuild vs reference cache, and the rebuild's after-cost mean):")
    print(cmp.round(2).to_string())

    # ── Missing-exit diagnostic ───────────────────────────────────────────────
    # The engine can only label a trade 'expiry' if a mark exists ON the expiry date. A trade that hits
    # the 50% take needs one good mark out of ~30 days; a trade that must run to expiry needs one
    # specific day. So dropping 'missing' is NOT symmetric across outcomes -- test it.
    print("\nmissing-exit diagnostic (is the exclusion outcome-related?)")
    miss = raw[raw.exit_type == "missing"]
    print(f"  {len(miss):,} missing of {len(raw):,} ({len(miss) / len(raw):.1%})")
    if len(miss):
        near = raw.copy()
        print(f"  their share of entries by year:")
        yr = pd.DataFrame({
            "missing": miss.groupby(pd.to_datetime(miss.entry_date).dt.year).size(),
            "all": near.groupby(pd.to_datetime(near.entry_date).dt.year).size(),
        })
        yr["rate %"] = 100 * yr["missing"] / yr["all"]
        print(yr.fillna(0).round(1).to_string())

    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
