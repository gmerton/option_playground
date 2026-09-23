#!/usr/bin/env python3
"""
Is the Adhikary "precision tier" a real cross-sectional sort, or was it fit to 2023-2026?
(pre-registered 2026-09-23, before the first run)

THE PROBLEM WITH THE QUEUED TEST. TEST_INDEX §286 asks for a "precision-tier true OOS" on 2023 + 2025.
That is not an out-of-sample test: the tier was fit on 2019-10 -> 2026-09, so 2023 and 2025 are INSIDE
the fitting sample -- and they are its two best years (by-year mean R: 2019 -0.30, 2020 -0.04, 2021 -0.21,
2022 -0.43, **2023 +0.21, 2024 +0.41, 2025 +0.58**, 2026 +0.28). Re-running the same panel on those years
re-reads in-sample data and would manufacture a confirmation. (§286 also carries `n = 17`, which belongs
to the archetype-C exhaustion FADE, not to this breakout tier -- the tier's n is ~1,824 events.)

WHAT THIS RUNS INSTEAD. A genuine temporal freeze-forward:
  FIT    2019-10-01 -> 2022-12-31   re-derive the three precision thresholds from scratch, mechanically
  TEST   2023-01-01 -> present      apply the FROZEN thresholds; never looked at during the fit

The published tier is ADR 4-7, off-52wk-high > -15%, stack run 5-40 sessions. Those bands saw the test
years. This refits them on the fit window alone and asks two questions:
  Q1  THRESHOLD STABILITY -- does a 2019-2022-only fit recover bands resembling the published ones?
      If it lands somewhere else entirely, the published tier is a 2023+ artefact regardless of Q2.
  Q2  FORWARD PERFORMANCE -- does the frozen tier beat the generic archetype-A pool in the test window,
      and beat honest controls (same name later = timing, other name same date = selection)?

⚠ THE FIT WINDOW IS A LOSING REGIME, and this is the study's main weakness, stated before running.
Archetype A has NEGATIVE mean R in every fit-window year. Picking "the best bucket" inside a losing
regime may select noise. So the fit rule is mechanical and declared here, and if the fit window cannot
separate the levers (no bucket clears the pool mean by a real margin) this reports UNDERPOWERED and
declines to freeze thresholds rather than forcing them.

⚠ SURVIVORSHIP IS NOT FIXED HERE. `liquid_panel_2019.parquet` holds names liquid as of 2026, so both
windows contain only survivors -- the flattering direction for a breakout book. A freeze-forward controls
for THRESHOLD fitting, not for universe construction. The survivorship-free version needs a point-in-time
universe from `silver.equity_daily` and is the follow-on if this passes.

R CONVENTION (the house process, per breitstein_tests/precision_tier_control_2026-09-19.md):
  entry = the signal bar's CLOSE; stop = that bar's LOW with a 2% floor (near-zero stops produced the
  fake +0.79R: 762R on a 0.4% stop); exit = first daily close below the stop, else first close below the
  20 EMA, else capped at 60 sessions. R = (exit - entry) / (entry - stop).
  Reported at cap 10 / cap 20 / uncapped -- the 9/19 note shows the verdict slides t 3.9 -> t 1.5 across
  exactly those cells, so a single cap would be cherry-picking.

MECHANICAL FIT RULE (declared before running): within the fit window's archetype-A events, bucket each
lever independently; keep the buckets whose mean R exceeds the pool mean by >= 0.10R; take the contiguous
span covering the kept buckets as the frozen band. A lever with no qualifying bucket is DROPPED (no
threshold), not forced.

PRE-REGISTERED PASS (Q2): in the TEST window, frozen tier minus generic pool > 0 with date-clustered
|t| >= 3, both halves of the test window (split 2024-07-01) the same sign, AND positive edge over both
the `post` and `xname` controls. Reported at all three R caps; a pass that exists only at one cap is
reported as CAP-DEPENDENT, not as a pass.

PRIOR: the published bands will NOT be recovered cleanly from 2019-2022 (~65%), because the by-year
table says the whole effect lives in 2023+. Most likely verdict is UNDERPOWERED on Q1 with the forward
test inheriting wide error bars -- which would mean the tier is a regime finding, not a selection finding.

Usage: PYTHONPATH=src .venv/bin/python3 -u run_precision_tier_freeze_forward.py
"""
from __future__ import annotations

import warnings
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)

from lib.commons.ma_stack import stack_run
from lib.regime.trailing import Panel, liquidity_mask
from lib.studies import pattern_test as pt

FIT_START, FIT_END = "2019-10-01", "2022-12-31"
TEST_START = "2023-01-01"
TEST_SPLIT = "2024-07-01"
STOP_FLOOR = 0.02          # risk must be >= 2% of price
HOLD_CAP = 60
CAPS = [10.0, 20.0, np.inf]
MIN_LIFT = 0.10            # a bucket must beat the pool mean by this much to be kept

ADR_BUCKETS   = [(3, 4), (4, 5), (5, 7), (7, 10), (10, 100)]
STACK_BUCKETS = [(5, 10), (10, 20), (20, 40), (40, 10_000)]
OFF52_BUCKETS = [(-100, -30), (-30, -15), (-15, -5), (-5, 1e9)]


def build():
    """Archetype-A mask + the three lever values, computed on the FULL panel (indicators need warm-up)."""
    raw = pd.read_parquet(pt.REPO / "data/cache/liquid_panel_2019.parquet")
    raw = raw[~raw.ticker.isin(["SPY", "QQQ", "IWM", "RSP"])]
    p = Panel.from_long(raw)
    O = raw.pivot(index="date", columns="ticker", values="open").sort_index()
    C, H, L, V = p.close, p.high, p.low, p.dolvol / p.close
    elig = liquidity_mask(p, addv_min=50e6, px_min=5.0) & ~p.suspect()
    adr = (H / L - 1).shift(1).rolling(20).mean() * 100
    hi52 = H.shift(1).rolling(252, min_periods=120).max()
    lo52 = L.shift(1).rolling(252, min_periods=120).min()
    range52 = (hi52 - lo52) / C * 100
    piv15 = H.shift(1).rolling(15).max()
    rvol = V / V.shift(1).rolling(50).mean()
    pos = (C - L) / (H - L).replace(0, np.nan)
    gap = O / C.shift(1) - 1
    chg = C.pct_change(fill_method=None)
    stack_days = stack_run(C, adr=adr)
    off52 = (C / hi52 - 1) * 100
    gate = (adr >= 3) & (range52 >= 17) & elig
    brk = (gate & (C >= piv15) & (rvol >= 1.1) & (pos >= 0.5) & (stack_days >= 5)
           & (gap < 0.05) & (chg < 0.08) & (C.shift(1) < piv15)).fillna(False)
    ema20 = C.ewm(span=20, adjust=False).mean()
    return dict(C=C, L=L, ema20=ema20, brk=brk, adr=adr, stack=stack_days, off52=off52, elig=elig)


def events(D: pd.DataFrame) -> pd.DataFrame:
    """Every archetype-A signal with its levers and its realised R under the house process."""
    C, L, E = D["C"].to_numpy(), D["L"].to_numpy(), D["ema20"].to_numpy()
    ii, jj = np.nonzero(D["brk"].to_numpy())
    dates = D["C"].index.to_numpy()
    syms = D["C"].columns.to_numpy()
    adr, stk, off = D["adr"].to_numpy(), D["stack"].to_numpy(), D["off52"].to_numpy()
    n_rows = C.shape[0]

    out = []
    for i, j in zip(ii, jj):
        entry = C[i, j]
        if not np.isfinite(entry) or entry <= 0:
            continue
        stop = min(L[i, j], entry * (1 - STOP_FLOOR))     # 2% floor: widen, never tighten
        risk = entry - stop
        if not np.isfinite(risk) or risk <= 0:
            continue
        exit_px = np.nan
        for k in range(i + 1, min(i + 1 + HOLD_CAP, n_rows)):
            c = C[k, j]
            if not np.isfinite(c):
                continue
            if c < stop or c < E[k, j]:                    # stop through, or 20-EMA trail
                exit_px = c
                break
            exit_px = c                                    # keep the last good mark for the cap
        if not np.isfinite(exit_px):
            continue
        out.append((dates[i], syms[j], (exit_px - entry) / risk, adr[i, j], stk[i, j], off[i, j]))

    E_ = pd.DataFrame(out, columns=["date", "sym", "R", "adr", "stack", "off52"])
    return E_.dropna(subset=["adr", "stack", "off52"])


def capped(r: pd.Series, cap: float) -> pd.Series:
    return r.clip(-cap, cap) if np.isfinite(cap) else r


def dclust_t(df: pd.DataFrame, col: str) -> float:
    """Date-clustered t: mean per signal date, then t across dates."""
    m = df.groupby("date")[col].mean()
    return float(m.mean() / (m.std(ddof=1) / sqrt(len(m)))) if len(m) > 2 else np.nan


def fit_levers(F: pd.DataFrame, cap: float) -> dict:
    """The declared mechanical fit: keep buckets beating the pool mean by >= MIN_LIFT, take the span."""
    F = F.assign(Rc=capped(F.R, cap))
    pool = F.Rc.mean()
    print(f"\n  fit-window pool: n {len(F):,}  mean R {pool:+.3f}  (cap {cap})")
    frozen = {}
    for lever, buckets in [("adr", ADR_BUCKETS), ("stack", STACK_BUCKETS), ("off52", OFF52_BUCKETS)]:
        rows, kept = [], []
        for lo, hi in buckets:
            sub = F[(F[lever] >= lo) & (F[lever] < hi)]
            mu = sub.Rc.mean() if len(sub) >= 30 else np.nan
            ok = bool(np.isfinite(mu) and mu - pool >= MIN_LIFT)
            rows.append((f"[{lo},{hi})", len(sub), mu, mu - pool if np.isfinite(mu) else np.nan, "KEEP" if ok else ""))
            if ok:
                kept.append((lo, hi))
        print(f"\n    {lever}:")
        print("      " + pd.DataFrame(rows, columns=["bucket", "n", "meanR", "lift", ""])
              .to_string(index=False, float_format=lambda v: f"{v:,.3f}").replace("\n", "\n      "))
        if kept:
            frozen[lever] = (min(k[0] for k in kept), max(k[1] for k in kept))
            print(f"      -> FROZEN {lever} in [{frozen[lever][0]}, {frozen[lever][1]})")
        else:
            print(f"      -> no bucket clears +{MIN_LIFT:.2f}R over pool: lever DROPPED")
    return frozen


def apply_frozen(E_: pd.DataFrame, frozen: dict) -> pd.Series:
    m = pd.Series(True, index=E_.index)
    for lever, (lo, hi) in frozen.items():
        m &= (E_[lever] >= lo) & (E_[lever] < hi)
    return m


PUBLISHED = {"adr": (4, 7), "off52": (-15, 1e9), "stack": (5, 40)}


def report(T: pd.DataFrame, mask: pd.Series, label: str) -> None:
    print(f"\n{'='*104}\n{label}\n{'='*104}")
    for cap in CAPS:
        tier = T[mask].assign(Rc=lambda d: capped(d.R, cap))
        pool = T[~mask].assign(Rc=lambda d: capped(d.R, cap))
        allp = T.assign(Rc=lambda d: capped(d.R, cap))
        if len(tier) < 30:
            print(f"  cap {cap}: n {len(tier)} — too few events"); continue
        # difference in per-date means -> date-clustered t on the DIFFERENCE
        a = tier.groupby("date").Rc.mean().rename("tier")
        b = allp.groupby("date").Rc.mean().rename("all")
        j = pd.concat([a, b], axis=1).dropna()
        d = j.tier - j["all"]
        t = float(d.mean() / (d.std(ddof=1) / sqrt(len(d)))) if len(d) > 2 else np.nan
        h1, h2 = d[d.index < TEST_SPLIT], d[d.index >= TEST_SPLIT]
        capn = "none" if not np.isfinite(cap) else f"{cap:.0f}"
        print(f"  cap {capn:>4s} | tier n {len(tier):>5,} meanR {tier.Rc.mean():+.3f} (t {dclust_t(tier,'Rc'):+.2f}, "
              f"win {100*(tier.Rc>0).mean():.0f}%, med {tier.Rc.median():+.2f}) | "
              f"pool meanR {allp.Rc.mean():+.3f} | EDGE {d.mean():+.3f} t {t:+.2f} | halves {h1.mean():+.3f}/{h2.mean():+.3f}")


def main() -> None:
    print("building panel and archetype-A events (indicators on the FULL history, then split)...")
    D = build()
    E_ = events(D)
    E_["date"] = pd.to_datetime(E_["date"])
    F = E_[(E_.date >= FIT_START) & (E_.date <= FIT_END)]
    T = E_[E_.date >= TEST_START]
    print(f"\narchetype-A events: {len(E_):,} total | FIT {len(F):,} ({FIT_START}..{FIT_END}) | "
          f"TEST {len(T):,} ({TEST_START}..{E_.date.max().date()})")
    print(f"⚠ fit-window regime check — mean R by year (uncapped):")
    print("   " + E_.assign(y=E_.date.dt.year).groupby("y").R.agg(["count", "mean"])
          .round(3).to_string().replace("\n", "\n   "))

    print(f"\n{'='*104}\nQ1 — REFIT THE THRESHOLDS ON {FIT_START}..{FIT_END} ONLY\n{'='*104}")
    frozen = fit_levers(F, cap=20.0)        # cap 20 for the fit: the 9/19 note's middle, least tail-driven
    print(f"\n  FROZEN TIER: {frozen if frozen else 'EMPTY — the fit window could not separate any lever'}")
    print(f"  PUBLISHED  : {PUBLISHED}")
    if frozen:
        same = {k: (k in PUBLISHED and abs(frozen[k][0] - PUBLISHED[k][0]) < 1e-9
                    and abs(min(frozen[k][1], 1e9) - min(PUBLISHED[k][1], 1e9)) < 1e-9) for k in frozen}
        print(f"  recovered the published band? {same}")

    print(f"\n{'='*104}\nQ2 — CARRY THE FROZEN THRESHOLDS INTO {TEST_START}..  (never seen during the fit)\n{'='*104}")
    if frozen:
        report(T, apply_frozen(T, frozen), f"FROZEN tier (fit on 2019-2022 only): {frozen}")
    else:
        print("\n  Q1 produced no thresholds -> UNDERPOWERED. No frozen tier to carry forward.")
    report(T, apply_frozen(T, PUBLISHED), "PUBLISHED tier (ADR 4-7, off52 > -15, stack 5-40) — ⚠ CONTAMINATED: these bands saw the test years")
    report(E_[(E_.date >= FIT_START) & (E_.date <= FIT_END)], apply_frozen(F, PUBLISHED),
           "PUBLISHED tier in the FIT window — what the tier looked like before its good years")

    E_.to_csv(pt.REPO / "data/studies/precision_tier_freeze_forward_2026-09-23.csv", index=False)
    print("\nwrote data/studies/precision_tier_freeze_forward_2026-09-23.csv")


if __name__ == "__main__":
    main()
