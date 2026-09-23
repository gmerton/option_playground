"""
VCP as a damped sine wave (Gabe's definition, 2026-09-23) -- does a contracting base add anything to the house
breakout?

PRE-REGISTRATION (written before any run)
----------------------------------------
Definition (Gabe): on the daily chart, look at the swings between local maxima and minima; if the vertical
size of successive swings shrinks, that is a VCP -- a damped sine wave.

Mechanised:
  * Swing points = 3-bar fractals on HIGH / LOW (a pivot high at p is the max of H[p-3 .. p+3]); a pivot is only
    KNOWN at p+3, so no look-ahead. Consecutive same-type pivots collapse to the more extreme one.
  * Contraction i = peak_i high -> next trough_i low, depth_i = 1 - trough_i / peak_i.
  * VCP state at day t: the last N contractions have STRICTLY decreasing depth, the first of them starts no more
    than 65 sessions before t, and the last trough is confirmed.
  * Context: close > SMA50 > SMA200 on the trigger day (minimal uptrend -- a damped sine inside a downtrend is a
    different animal), ADR20 >= 3%, liquidity-eligible (the house breakout universe).
  * Trigger: FIRST close above the last peak's high (the pivot) while the VCP state holds. Entry at that CLOSE
    (house process). Tight stop = the last trough's low, judged on the close.

Cells
  PRIMARY  N = 3 contractions (two consecutive decreases -- the least that is a damping, not one lucky pair).
  secondary (exploratory): N = 2.

Tests (primary governs; secondaries are exploratory and carry no verdict of their own)
  1. PRIMARY -- VCP vs the house breakout IN THE SAME NAME: each VCP signal is paired with the non-VCP house
     breakouts (close > prior 20d high, ADR >= 3, eligible) in the same name within +/-60 sessions. Metric =
     % return per trade (NOT R: the stops differ), both entered at the close, exit = first close below the
     20 EMA or through the setup's own stop, max 60 sessions, 0.10% slippage per side. Paired difference
     (VCP - mean of its matched breakouts), date-clustered t.
     Also: "held the level" share = low never touches the pivot again within 20 sessions (house breakout pool
     measured at 23.6% on 2026-09-20 -- recomputed here on the same exit window for both groups).
  2. Harness rows (`lib.studies.pattern_test.run_daily`, entry_at="close", hold 60): control="post" (ledger row)
     and control="xname" (report only).
Bar: |t| >= 3 on the paired difference, both halves (split 2023-01-01) the same sign, per-year table shown.
Multiple-testing charge: 2 cells x (paired + 2 harness controls) = 6 looks; the PRIMARY cell's paired t is the
one registered test, so the raw |t| >= 3 bar applies to it alone.
What it must show to add anything: beat the same-name house breakout on % return AND raise the held-the-level
share -- i.e. make the bimodal breakout's good cohort callable at entry.

Run: PYTHONPATH=src .venv/bin/python3 run_vcp_damped_sine.py   (log -> data/studies/logs/vcp_damped_sine.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.pattern_test import SLIP, daily_signals, load_panel, run_daily

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/vcp_damped_sine.log"
OUT = REPO / "data/studies/vcp_damped_sine_2026-09-23.md"
START = "2019-10-01"
K = 3            # fractal half-width
WINDOW = 65      # max sessions from the first contraction's peak to the trigger
HOLD = 60
PAIR_WIN = 60
SPLIT = "2023-01-01"


def pivots(h: np.ndarray, l: np.ndarray) -> list[tuple[int, str, float]]:
    """Alternating confirmed swing points (index, 'H'|'L', price), each known at index + K."""
    n, raw = len(h), []
    for p in range(K, n - K):
        wh, wl = h[p - K:p + K + 1], l[p - K:p + K + 1]
        if np.isfinite(h[p]) and h[p] == np.nanmax(wh):
            raw.append((p, "H", h[p]))
        if np.isfinite(l[p]) and l[p] == np.nanmin(wl):
            raw.append((p, "L", l[p]))
    out: list[tuple[int, str, float]] = []
    for pv in raw:
        if out and out[-1][1] == pv[1]:
            better = pv[2] > out[-1][2] if pv[1] == "H" else pv[2] < out[-1][2]
            if better:
                out[-1] = pv
        else:
            out.append(pv)
    return out


def vcp_signals(P, n_contr: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Boolean trigger mask + stop frame for the damped-sine VCP."""
    C, H, L = P.close.values, P.high.values, P.low.values
    sma50 = P.close.rolling(50).mean().values
    sma200 = P.close.rolling(200).mean().values
    ok = (P.adr.values >= 3) & P.elig.values
    hit = np.zeros_like(C, dtype=bool)
    stop = np.full_like(C, np.nan, dtype=float)
    pivot_lvl = np.full_like(C, np.nan, dtype=float)
    n, m = C.shape
    for j in range(m):
        pv = pivots(H[:, j], L[:, j])
        if len(pv) < 2 * n_contr:
            continue
        known = np.array([p[0] + K for p in pv])
        for t in range(1, n):
            if not ok[t, j] or not (C[t, j] > sma50[t, j] > sma200[t, j]):
                continue
            q = np.searchsorted(known, t, side="right")      # pivots known by t
            seq = pv[:q]
            if len(seq) < 2 * n_contr or seq[-1][1] != "L":
                continue
            pairs = seq[-2 * n_contr:]
            if pairs[0][1] != "H":
                continue
            peaks, troughs = pairs[0::2], pairs[1::2]
            if t - peaks[0][0] > WINDOW:
                continue
            depth = [1 - tr[2] / pk[2] for pk, tr in zip(peaks, troughs)]
            if not all(depth[i + 1] < depth[i] for i in range(len(depth) - 1)):
                continue
            lvl = peaks[-1][2]
            if C[t, j] > lvl and C[t - 1, j] <= lvl:
                hit[t, j] = True
                stop[t, j] = troughs[-1][2]
                pivot_lvl[t, j] = lvl
    idx, cols = P.close.index, P.close.columns
    return (pd.DataFrame(hit, index=idx, columns=cols), pd.DataFrame(stop, index=idx, columns=cols),
            pd.DataFrame(pivot_lvl, index=idx, columns=cols))


def house_breakout(P) -> tuple[pd.DataFrame, pd.DataFrame]:
    lvl = P.high.shift(1).rolling(20).max()
    m = ((P.close > lvl) & (P.adr >= 3) & P.elig).fillna(False)
    m[m.index < START] = False
    return m, lvl


def pct_trade(P, j: int, i: int, stop: float, level: float) -> tuple[float, bool] | None:
    """Enter at close i; exit on first close below EMA20 or through the stop, max HOLD. % return, held-level."""
    C, L, E = P.close.values, P.low.values, P.ema20.values
    if i + 1 >= len(C) or not np.isfinite(C[i, j]):
        return None
    entry = C[i, j] * (1 + SLIP)
    exit_px = np.nan
    for k in range(i + 1, min(i + 1 + HOLD, len(C))):
        c = C[k, j]
        if not np.isfinite(c):
            continue
        if (np.isfinite(stop) and c < stop) or (np.isfinite(E[k, j]) and c < E[k, j]):
            exit_px = c
            break
    if not np.isfinite(exit_px):
        k = min(i + HOLD, len(C) - 1)
        exit_px = C[k, j]
    if not np.isfinite(exit_px):
        return None
    lows = L[i + 1:min(i + 21, len(C)), j]
    held = bool(np.all(lows[np.isfinite(lows)] > level)) if np.isfinite(level) and len(lows) else False
    return 100 * (exit_px * (1 - SLIP) / entry - 1), held


def tstat(x: pd.Series, by: pd.Series) -> float:
    d = x.groupby(by).mean()
    return float(d.mean() / d.std() * np.sqrt(len(d))) if len(d) > 2 and d.std() > 0 else np.nan


def paired(P, n_contr: int, lines: list[str]) -> dict:
    hit, stop, plvl = vcp_signals(P, n_contr)
    hit[hit.index < START] = False
    hb, hlvl = house_breakout(P)
    hbv, hlv = hb.values, hlvl.values
    rows = []
    for i, j in zip(*np.where(hit.values)):
        v = pct_trade(P, j, i, stop.values[i, j], plvl.values[i, j])
        if v is None:
            continue
        lo, hi = max(0, i - PAIR_WIN), min(len(hbv), i + PAIR_WIN + 1)
        ctl = []
        for k in range(lo, hi):
            if k == i or not hbv[k, j] or hit.values[k, j]:
                continue
            c = pct_trade(P, j, k, P.low.values[k, j], hlv[k, j])      # house tight stop = the day's low
            if c is not None:
                ctl.append(c)
        rows.append(dict(date=hit.index[i], sym=hit.columns[j], vcp=v[0], vcp_held=v[1],
                         stop_pct=100 * (1 - stop.values[i, j] / P.close.values[i, j]),
                         n_ctl=len(ctl), ctl=np.mean([c[0] for c in ctl]) if ctl else np.nan,
                         ctl_held=np.mean([c[1] for c in ctl]) if ctl else np.nan))
    D = pd.DataFrame(rows)
    # the whole house-breakout pool, same exit, for the held-level base rate
    pool = []
    for i, j in zip(*np.where(hbv)):
        c = pct_trade(P, j, i, P.low.values[i, j], hlv[i, j])
        if c is not None:
            pool.append(dict(date=hb.index[i], ret=c[0], held=c[1]))
    Pool = pd.DataFrame(pool)
    Dp = D.dropna(subset=["ctl"]).copy()
    Dp["diff"] = Dp.vcp - Dp.ctl
    res = dict(N=n_contr, signals=len(D), names=D.sym.nunique() if len(D) else 0, paired=len(Dp),
               vcp_mean=D.vcp.mean(), vcp_med=D.vcp.median(), vcp_win=100 * (D.vcp > 0).mean(),
               vcp_held=100 * D.vcp_held.mean(), stop_med=D.stop_pct.median(),
               pool_n=len(Pool), pool_mean=Pool.ret.mean(), pool_held=100 * Pool.held.mean(),
               pool_t=tstat(Pool.ret, Pool.date),
               vcp_t=tstat(D.vcp, D.date), diff=Dp["diff"].mean(), diff_t=tstat(Dp["diff"], Dp.date),
               ctl_mean=Dp.ctl.mean(), ctl_held=100 * Dp.ctl_held.mean(),
               h1=Dp[Dp.date < SPLIT]["diff"].mean(), h2=Dp[Dp.date >= SPLIT]["diff"].mean(),
               n1=int((Dp.date < SPLIT).sum()), n2=int((Dp.date >= SPLIT).sum()))
    yr = Dp.groupby(Dp.date.dt.year).agg(n=("diff", "size"), vcp=("vcp", "mean"), ctl=("ctl", "mean"),
                                         diff=("diff", "mean"))
    lines.append(f"\n## N = {n_contr} contractions {'(PRIMARY)' if n_contr == 3 else '(exploratory)'}\n")
    lines.append(pd.Series(res).round(3).to_string())
    lines.append("\nper year (paired):\n" + yr.round(2).to_string())
    D.to_csv(REPO / f"data/studies/logs/vcp_damped_sine_N{n_contr}_trades.csv", index=False)
    return {**res, "_yr": yr}


def main() -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    real_stdout = sys.stdout
    sys.stdout = open(LOG, "w")
    P = load_panel()
    lines: list[str] = []
    R = {n: paired(P, n, lines) for n in (3, 2)}
    print("\n".join(lines))

    def pattern(n):
        def f(P):
            hit, stop, _ = vcp_signals(P, n)
            return daily_signals(hit, stop=stop, side="long", since=START)
        return f
    print("\n\n# harness rows (entry at close, hold 60)")
    run_daily("vcp damped sine N3", pattern(3), hold=HOLD, entry_at="close", control="post",
              note="Gabe damped-sine VCP, 3 decreasing contractions, close>pivot, stop=last trough")
    run_daily("vcp damped sine N3 xname", pattern(3), hold=HOLD, entry_at="close", control="xname", ledger=False)
    run_daily("vcp damped sine N2", pattern(2), hold=HOLD, entry_at="close", control="post", ledger=False)
    sys.stdout.close()
    sys.stdout = real_stdout
    for n, r in R.items():
        print(f"N={n}: signals {r['signals']} ({r['names']} names), paired {r['paired']} | VCP {r['vcp_mean']:.2f}% "
              f"(t {r['vcp_t']:.2f}, win {r['vcp_win']:.0f}%, held {r['vcp_held']:.1f}%, med stop {r['stop_med']:.1f}%) "
              f"| same-name house bo {r['ctl_mean']:.2f}% (held {r['ctl_held']:.1f}%) | diff {r['diff']:+.2f}pp "
              f"t {r['diff_t']:.2f} halves {r['h1']:+.2f}/{r['h2']:+.2f} (n {r['n1']}/{r['n2']}) "
              f"| pool {r['pool_n']} bo {r['pool_mean']:.2f}% held {r['pool_held']:.1f}%")
        print(r["_yr"].round(2).to_string())
    print(f"log: {LOG}")


if __name__ == "__main__":
    main()
