"""
Honest inference for the VRP panel.

The panel breaks BOTH assumptions behind a plain t-test:

  1. Serial overlap.  A 30-day forward window observed daily shares 29 of its 30
     days with the next day's window.  Consecutive rows are nearly the same
     observation, so the naive standard error is too small by roughly sqrt(tenor).
  2. Cross-sectional correlation.  Pool 10 ETFs and you have nothing like 10
     independent draws per date — they all load on the same market factor.

Both inflate t-stats, and they compound.  A naive t of 20 on this panel can be a
real t of 2.  Everything here exists to stop that.

Method
------
Collapse first, then correct.  For each date take the cross-sectional mean across
tickers, which handles (2) exactly the way Fama-MacBeth does: whatever the
correlation structure within a date, the date's mean is one observation.  Then
treat the resulting daily series as the sample and correct for (1) with either
Newey-West or a moving-block bootstrap, both using a lag/block length equal to the
overlap horizon.

`summarize` reports the naive t alongside the corrected ones on purpose.  The gap
between them is the thing worth looking at, and printing it keeps anyone (including
a future me) from quoting the wrong number.

Multiple testing
----------------
`haircut_t` applies the Harvey-Liu-Zhu style Bonferroni adjustment.  Pass the number
of hypotheses the SEARCH has actually consumed, not the number in the current table.
The trial count is a property of the research program, not of one script.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

TRADING_DAYS = 252.0


# ══════════════════════════════════════════════════════════════════════════════
# Building blocks
# ══════════════════════════════════════════════════════════════════════════════

def daily_mean_series(
    df: pd.DataFrame,
    value_col: str = "vrp",
    date_col: str = "trade_date",
    min_names: int = 1,
) -> pd.Series:
    """
    Collapse a panel to one observation per date (the cross-sectional mean).

    This is the step that handles cross-sectional correlation.  Dates with fewer
    than `min_names` tickers are dropped so a single thin name cannot swing a date.
    """
    g = df.dropna(subset=[value_col]).groupby(date_col)[value_col]
    s = g.mean()
    counts = g.size()
    s = s[counts >= min_names]
    return s.sort_index()


def newey_west_se(x: np.ndarray, lag: int) -> float:
    """
    Newey-West standard error of the MEAN of a serially correlated series.

    var = gamma_0 + 2 * sum_l (1 - l/(L+1)) * gamma_l ,  se = sqrt(var / T)

    Bartlett weights keep the estimate positive semi-definite.  Clamped at zero
    because a heavily negatively autocorrelated sample can drive the sum negative.
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = x.size
    if n < 3:
        return float("nan")
    lag = int(min(max(lag, 0), n - 1))
    dm = x - x.mean()
    var = float(dm @ dm) / n
    for l in range(1, lag + 1):
        cov = float(dm[l:] @ dm[:-l]) / n
        var += 2.0 * (1.0 - l / (lag + 1.0)) * cov
    if var <= 0:
        return float("nan")
    return float(np.sqrt(var / n))


def block_bootstrap_ci(
    x: np.ndarray,
    block: int,
    n_boot: int = 4000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float, float]:
    """
    Moving-block bootstrap CI for the mean of an overlapping series.

    Resampling contiguous blocks of length `block` preserves the serial dependence
    that the overlap creates, which a plain i.i.d. bootstrap would destroy (and so
    would reproduce the naive, too-narrow interval).

    Returns (lo, hi, p_two_sided) where p is the bootstrap probability that the
    mean is on the opposite side of zero, doubled.
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = x.size
    if n < 3:
        return (float("nan"), float("nan"), float("nan"))
    block = int(min(max(block, 1), n))
    n_blocks = int(np.ceil(n / block))
    n_starts = n - block + 1

    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n_starts, size=(n_boot, n_blocks))
    idx = starts[:, :, None] + np.arange(block)[None, None, :]
    means = x[idx.reshape(n_boot, -1)[:, :n]].mean(axis=1)

    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    frac_le0 = float((means <= 0).mean())
    p = 2.0 * min(frac_le0, 1.0 - frac_le0)
    return (float(lo), float(hi), float(min(p, 1.0)))


def nonoverlap_t(x: np.ndarray, stride: int) -> tuple[float, int]:
    """
    t-stat on a strided, genuinely non-overlapping subsample.

    Wasteful (keeps 1 of every `stride` observations) but assumption-free, so it is
    the sanity check on the two corrected estimates above.  Averaged over all
    `stride` possible phases so the answer does not depend on where the sample
    happens to start.
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    stride = int(max(stride, 1))
    ts, ns = [], []
    for phase in range(stride):
        sub = x[phase::stride]
        if sub.size < 5:
            continue
        sd = sub.std(ddof=1)
        if sd <= 0:
            continue
        ts.append(sub.mean() / (sd / np.sqrt(sub.size)))
        ns.append(sub.size)
    if not ts:
        return (float("nan"), 0)
    return (float(np.mean(ts)), int(np.mean(ns)))


def haircut_t(n_trials: int, alpha: float = 0.05) -> float:
    """
    Bonferroni t-hurdle for `n_trials` tested hypotheses.

    Ten trials needs ~2.8, fifty needs ~3.3, two hundred needs ~3.7.  This is the
    number a candidate must clear, not the number it produced.
    """
    n_trials = max(int(n_trials), 1)
    return float(stats.norm.ppf(1.0 - alpha / (2.0 * n_trials)))


# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class VrpSummary:
    label: str
    n_obs: int              # panel rows
    n_dates: int            # independent-ish date observations after collapsing
    n_tickers: int
    mean: float             # mean premium, vol points (iv - rv_fwd)
    median: float           # median premium — for short vol this sits well ABOVE the mean
    frac_pos: float         # share of dates with a positive premium
    sd_daily: float         # sd of the daily cross-sectional mean series
    t_naive: float          # WRONG on purpose — the number a plain t-test would print
    t_nw: float             # Newey-West, lag = overlap horizon
    t_nonoverlap: float     # strided non-overlapping subsample
    n_nonoverlap: int
    boot_lo: float
    boot_hi: float
    boot_p: float
    hurdle: float           # Bonferroni t-hurdle for the declared trial count
    passes: bool            # |t_nw| >= hurdle AND bootstrap CI excludes zero

    def as_row(self) -> dict:
        return asdict(self)


def summarize(
    df: pd.DataFrame,
    tenor: int,
    label: str = "",
    value_col: str = "vrp",
    date_col: str = "trade_date",
    n_trials: int = 1,
    n_boot: int = 4000,
    seed: int = 0,
    min_names: int = 1,
) -> Optional[VrpSummary]:
    """
    Full inference for one cell of the panel.

    `tenor` sets the overlap horizon: a tenor-calendar-day forward window overlaps
    for about tenor * 252/365 trading days, which becomes the Newey-West lag, the
    bootstrap block length, and the non-overlap stride.
    """
    sub = df.dropna(subset=[value_col])
    if sub.empty:
        return None

    overlap = max(2, int(round(tenor * TRADING_DAYS / 365.0)))
    s = daily_mean_series(sub, value_col=value_col, date_col=date_col, min_names=min_names)
    x = s.to_numpy(dtype=float)
    if x.size < 10:
        return None

    mean = float(np.mean(x))
    median = float(np.median(x))
    frac_pos = float((x > 0).mean())
    sd = float(np.std(x, ddof=1))
    t_naive = mean / (sd / np.sqrt(x.size)) if sd > 0 else float("nan")

    se_nw = newey_west_se(x, lag=overlap)
    t_nw = mean / se_nw if se_nw and np.isfinite(se_nw) and se_nw > 0 else float("nan")

    t_no, n_no = nonoverlap_t(x, stride=overlap)
    lo, hi, p = block_bootstrap_ci(x, block=overlap, n_boot=n_boot, seed=seed)

    hurdle = haircut_t(n_trials)
    passes = bool(
        np.isfinite(t_nw) and abs(t_nw) >= hurdle
        and np.isfinite(lo) and np.isfinite(hi) and (lo > 0 or hi < 0)
    )

    return VrpSummary(
        label=label,
        n_obs=int(len(sub)),
        n_dates=int(x.size),
        n_tickers=int(sub["ticker"].nunique()) if "ticker" in sub.columns else 0,
        mean=mean,
        median=median,
        frac_pos=frac_pos,
        sd_daily=sd,
        t_naive=float(t_naive),
        t_nw=float(t_nw),
        t_nonoverlap=float(t_no),
        n_nonoverlap=int(n_no),
        boot_lo=lo,
        boot_hi=hi,
        boot_p=p,
        hurdle=hurdle,
        passes=passes,
    )


def summarize_by(
    panel: pd.DataFrame,
    by: str | list[str],
    tenor: int,
    value_col: str = "vrp",
    n_trials: int = 1,
    n_boot: int = 2000,
    min_rows: int = 200,
    seed: int = 0,
) -> pd.DataFrame:
    """Run `summarize` for each group of `by` within one tenor. Returns a tidy frame."""
    keys = [by] if isinstance(by, str) else list(by)
    rows = []
    for gkey, grp in panel.groupby(keys, sort=True, dropna=True, observed=True):
        if len(grp.dropna(subset=[value_col])) < min_rows:
            continue
        label = " / ".join(str(k) for k in (gkey if isinstance(gkey, tuple) else (gkey,)))
        res = summarize(
            grp, tenor=tenor, label=label, value_col=value_col,
            n_trials=n_trials, n_boot=n_boot, seed=seed,
        )
        if res is not None:
            rows.append(res.as_row())
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("mean", ascending=False).reset_index(drop=True)


def format_table(df: pd.DataFrame, pct: bool = True) -> str:
    """Render a summary frame as a fixed-width table, vol points as percentages."""
    if df.empty:
        return "  (no cells met the minimum row count)"
    d = df.copy()
    scale = 100.0 if pct else 1.0
    for c in ("mean", "median", "boot_lo", "boot_hi"):
        if c in d.columns:
            d[c] = d[c] * scale

    head = (f"  {'cell':<22} {'n_obs':>8} {'dates':>7} {'mean':>8} {'med':>7} {'pos':>6} "
            f"{'t_naive':>8} {'t_NW':>7} {'t_nolap':>8} {'boot 95% CI':>18} {'hurdle':>7}  ok")
    lines = [head, "  " + "-" * (len(head) - 2)]
    for r in d.itertuples(index=False):
        ci = f"[{r.boot_lo:+6.2f},{r.boot_hi:+6.2f}]"
        lines.append(
            f"  {str(r.label)[:22]:<22} {r.n_obs:>8,} {r.n_dates:>7,} {r.mean:>7.2f}% "
            f"{r.median:>6.2f}% {100*r.frac_pos:>5.0f}% "
            f"{r.t_naive:>8.1f} {r.t_nw:>7.2f} {r.t_nonoverlap:>8.2f} {ci:>18} "
            f"{r.hurdle:>7.2f}  {'YES' if r.passes else '-'}"
        )
    return "\n".join(lines)
