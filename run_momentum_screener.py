#!/usr/bin/env python3
"""
Monthly 12-1 MOMENTUM screener -- the live list for the momentum sleeve, and its forward lockbox.

WHAT IT IS. The rule tested in run_momentum_portfolio.py (2026-09-25: top decile 12-1 on the survivorship-free
chain_spot series, excess +0.67pp/mo vs the equal-weight universe, t_NW 2.93, halves +0.38/+0.92, 12/16 years --
SUPPORTED near-miss, not certified). This script applies that rule, unchanged, to today's data so the
forward record starts with the 2026-09-30 formation.

RULE (same as the study; do not tune it here)
  formation  the last session of the month, t.  score = close(t-21) / close(t-252) - 1  (12-1, skipping the last month)
  eligible   price >= $5 at t, 252 sessions of history, and no >45% single-day move inside the formation window
             (the study cut series at unexplained >45% jumps, which dropped those names from ranking)
  buy        TOP DECILE by score, equal weight, hold to the next month-end close, then rebalance.
             The top QUINTILE is also written (study: +0.42pp/mo, t 2.64, 14/16 years), and the fixed-count books
             T20 / T30 = ranks 1-20 / 1-30 (run_momentum_topn.py: +1.22 / +1.08pp/mo, ACCEPTABLE vs the decile but
             tail-driven, 9/16 and 11/16 years, maxDD 35% / 30%). Flagged in_t20 / in_t30 in the list and lockbox.
             T20-B = the BUFFER book (run_momentum_buffer.py: same return as T20, turnover 38% -> 13%/mo): keep last
             formation's T20-B names while they stay in the top quintile, refill from the top ranks to 20. Flagged in_t20b;
             the lockbox is its memory, so a missed month-end breaks the chain (it restarts as plain T20).
  benchmark  the equal-weight portfolio of every eligible name (the lockbox logs its size so it can be rebuilt).

LIVE DIFFERENCES (declared, not tuned)
  data       data/cache/minervini_matrix.parquet (the nightly S3 matrix; ~5.3k names, mostly split-adjusted closes, and 297
             sessions). This script refreshes it from S3 first. ⚠ Recent splits are sometimes left unadjusted there (MNST, APH), so
             adjust_missed_splits() repairs them from pit/splits.parquet before scoring. It has survivorship, but that is harmless going forward.
  liquidity  the study gated on 50-day mean OPTION volume >= 1,000 contracts, which isn't available live at no cost. Here
             the gate is 50-day stock ADDV >= $50M (the survivor-panel run: +0.54pp/mo, t 2.34). This proxy is a live
             difference, and the forward record is what will judge it.
  no SPY 200-day filter (the study's exploratory trend cell HURT).

LOCKBOX. On a month-end formation it writes data/momentum/lists/<YYYY-MM-DD>.csv and appends one row per pick
to data/momentum/lockbox.csv. Formations already logged are never overwritten. A non-month-end run is a PREVIEW
and logs nothing. The grader that scores each closed month against the EW universe is a separate step, not built yet.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_momentum_screener.py [--asof YYYY-MM-DD]
       [--no-refresh] [--preview]
       Run after the month's last close is in the matrix (the matrix refreshes Tue-Sat 07:30 UTC), e.g. on the
       morning of 2026-10-01 for the 2026-09-30 formation.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent
MATRIX = REPO / "data/cache/minervini_matrix.parquet"
S3_MATRIX = "s3://gmerton-stock-data/breakouts/minervini_matrix.parquet"
OUT_DIR = REPO / "data/momentum"
LOOKBACK, SKIP, ADDV_MIN, PX_MIN, JUMP = 252, 21, 50e6, 5.0, 0.45


def adjust_missed_splits(C: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """The matrix leaves some recent splits unadjusted (MNST 2026-08, APH 2026-09 show a raw 2:1 step). For each split in
    pit/splits.parquet, find the session within -3..+1 of the execution date whose close ratio matches from/to within 15%;
    if one exists, the split was missed, so divide every earlier close by to/from. Already-adjusted splits show no step
    and are left alone."""
    sp = pd.read_parquet(REPO / "data/cache/pit/splits.parquet")
    sp["execution_date"] = pd.to_datetime(sp.execution_date)
    sp = sp[sp.ticker.isin(C.columns) & (sp.split_from > 0) & (sp.split_to > 0)
            & (sp.execution_date >= C.index[0]) & (sp.execution_date <= C.index[-1] + pd.Timedelta(days=3))]
    C = C.copy(); fixed = []
    for r in sp.itertuples():
        expect = r.split_from / r.split_to                     # post/pre close ratio of an unadjusted split
        if abs(expect - 1) < 0.2:
            continue
        s = C[r.ticker]
        k = C.index.searchsorted(r.execution_date)
        best = None
        for i in range(max(k - 3, 1), min(k + 2, len(C))):
            if np.isfinite(s.iloc[i]) and np.isfinite(s.iloc[i - 1]) and s.iloc[i - 1] > 0:
                err = abs(s.iloc[i] / s.iloc[i - 1] / expect - 1)
                if err < 0.15 and (best is None or err < best[1]):
                    best = (i, err)
        if best:
            C.iloc[:best[0], C.columns.get_loc(r.ticker)] *= expect
            fixed.append(f"{r.ticker} {C.index[best[0]].date()} {r.split_to:g}:{r.split_from:g}")
    return C, fixed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=None, help="formation date (default: the last session in the matrix)")
    ap.add_argument("--no-refresh", action="store_true", help="skip the S3 pull of the matrix")
    ap.add_argument("--preview", action="store_true", help="never write to the lockbox")
    a = ap.parse_args()

    if not a.no_refresh:
        r = subprocess.run(["aws", "s3", "cp", S3_MATRIX, str(MATRIX), "--only-show-errors"],
                           env={**os.environ, "AWS_PROFILE": os.environ.get("AWS_PROFILE") or "clarinut-gmerton"})
        if r.returncode:
            print("WARN: S3 refresh failed; using the local matrix")
    d = pd.read_parquet(MATRIX)
    d["date"] = pd.to_datetime(d.date)
    C = d.pivot(index="date", columns="ticker", values="close").sort_index()
    DV = d.pivot(index="date", columns="ticker", values="dolvol").sort_index()
    idx = C.index
    asof = pd.Timestamp(a.asof) if a.asof else idx[-1]
    if asof not in idx:
        raise SystemExit(f"{asof.date()} is not a session in the matrix (last {idx[-1].date()})")
    t = idx.get_loc(asof)
    if t < LOOKBACK:
        raise SystemExit(f"only {t + 1} sessions before {asof.date()}; need {LOOKBACK + 1}")
    # month-end = the last session of asof's month is in the data and equals asof
    same_month = idx[(idx.year == asof.year) & (idx.month == asof.month)]
    is_month_end = asof == same_month[-1] and (t < len(idx) - 1 or pd.Timestamp.today().normalize() > asof + pd.offsets.MonthEnd(0))

    C, fixed = adjust_missed_splits(C)
    win = C.iloc[t - LOOKBACK:t + 1]
    score = C.iloc[t - SKIP] / C.iloc[t - LOOKBACK] - 1
    addv = DV.iloc[t - 49:t + 1].mean()
    px = C.iloc[t]
    jump = (win.pct_change(fill_method=None).abs() > JUMP).any()
    full = win.notna().all()
    elig = full & (px >= PX_MIN) & (addv >= ADDV_MIN) & ~jump & score.notna()
    jumped = sorted(score.index[full & (px >= PX_MIN) & (addv >= ADDV_MIN) & jump])

    E = pd.DataFrame({"score": score[elig], "close": px[elig], "addv_m": addv[elig] / 1e6}).sort_values("score", ascending=False)
    n = len(E)
    E["rank"] = np.arange(1, n + 1)
    n10, n20 = int(np.ceil(n * 0.10)), int(np.ceil(n * 0.20))
    E["bucket"] = np.where(E["rank"] <= n10, "D1", np.where(E["rank"] <= n20, "Q1", ""))
    E["in_t20"], E["in_t30"] = E["rank"] <= 20, E["rank"] <= 30        # fixed-count books (run_momentum_topn.py: ACCEPTABLE)
    top = E[E.bucket != ""].reset_index().rename(columns={"index": "ticker"})
    top.insert(0, "formation", asof.date().isoformat())
    top["universe_n"] = n
    # T20-B buffer book (run_momentum_buffer.py, 2026-09-25: same return as T20, turnover 38% -> 13%/mo): keep last
    # formation's T20-B names that are still in the top quintile, refill from the top ranks back to 20.
    prev, prev_date = set(), None
    box = OUT_DIR / "lockbox.csv"
    if box.exists():
        L = pd.read_csv(box)
        if "in_t20b" in L.columns:
            L = L[L.formation < asof.date().isoformat()]
            if len(L):
                prev_date = L.formation.max()
                prev = set(L[(L.formation == prev_date) & L.in_t20b.astype(bool)].ticker)
    keep = [t for t in top.ticker if t in prev]                      # top = the top quintile, in rank order
    fill = [t for t in top.ticker if t not in prev][:max(20 - len(keep), 0)]
    top["in_t20b"] = top.ticker.isin(set(keep) | set(fill))
    t20b_sell = sorted(prev - set(keep))

    tag = "MONTH-END FORMATION" if is_month_end else "PREVIEW (not a completed month-end; nothing logged)"
    print(f"# 12-1 momentum screener -- {asof.date()} -- {tag}")
    print(f"universe {n} eligible (px >= ${PX_MIN:.0f}, ADDV >= ${ADDV_MIN / 1e6:.0f}M, 252 sessions); "
          f"top decile {n10}, top quintile {n20}; excluded for a >45% day: {len(jumped)}")
    print(f"{'rank':>4} {'ticker':<7} {'12-1':>8} {'close':>9} {'ADDV $M':>8}  bucket")
    for r in top.itertuples():
        print(f"{r.rank:4d} {r.ticker:<7} {r.score:+8.1%} {r.close:9.2f} {r.addv_m:8.0f}  {r.bucket}"
              + ("  T20" if r.in_t20 else ("  T30" if r.in_t30 else "")) + ("  T20-B" if r.in_t20b else ""))
    if fixed:
        print(f"split-adjusted here (missed in the matrix): {len(fixed)} -- " + ", ".join(fixed))
    if jumped:
        print("excluded (>45% day in window): " + ", ".join(jumped))
    print("T20 (5% each): " + " ".join(top[top.in_t20].ticker))
    print("T30 (3.3% each; T20 + these): " + " ".join(top[top.in_t30 & ~top.in_t20].ticker))
    print(f"T20-B buffer book (5% each; keep while in the top quintile) vs {prev_date or 'no prior formation -> = T20'}:")
    print("  HOLD: " + (" ".join(keep) or "-"))
    print("  BUY:  " + (" ".join(fill) or "-"))
    print("  SELL: " + (" ".join(t20b_sell) or "-") + "   (fell out of the top quintile or no longer eligible)")
    print(f"equal weight across the top decile: 1/{n10} = {1 / n10:.2%} of the sleeve per name")

    if is_month_end and not a.preview:
        OUT_DIR.joinpath("lists").mkdir(parents=True, exist_ok=True)
        f = OUT_DIR / "lists" / f"{asof.date()}.csv"
        if f.exists():
            print(f"lockbox: {asof.date()} already logged -> {f} (not overwritten)")
            return
        top.to_csv(f, index=False)
        top.to_csv(box, mode="a", header=not box.exists(), index=False)
        print(f"lockbox: wrote {f} and appended {len(top)} rows to {box}")


if __name__ == "__main__":
    main()
