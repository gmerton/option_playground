#!/usr/bin/env python3
"""
[WL-4] Qullamaggie's own partial-then-trail exit vs the house 20-EMA trail (pre-registered 2026-09-23; spec copied from
data/qullamaggie/README.md "The queued partial-then-trail row: does it match his words?" BEFORE running).

His words (Chat With Traders 2021): sell 20-25% ("can vary a lot") into the first burst of strength; then the stop goes
to at least breakeven; trail the rest on the 10-day (fast names) / 20-day (slow) MA, but only ONCE THE MA HAS CAUGHT UP
TO THE STOP; exit on the first close below it, never intraday.

Pools (entry = breakout CLOSE +10 bps, initial stop = breakout-day low judged on the close, risk floor 2%, cap 60):
  PRIMARY  the profit-lock pool (precision-tier house breakouts, 2019-10 -> 2026-09)
  second   the generic house breakout pool (close > prior 20d high, ADR >= 3, eligible) -- the tier is NULL on
           freeze-forward, so don't rely on it alone.
Arms (every arm on the SAME trades; paired arm - BASE, t clustered by entry date):
  BASE              20-EMA close trail from day 1 + initial stop (the house rule)
  Q_DAY{3,5}_P{20,33,50}   sell p at the close of day d (d sessions after entry); stop -> max(LOD, entry);
                    rest: SMA-n close exit, ACTIVE only once SMA-n > the current stop; n = 10 if ADR >= 5% else 20
  Q_BURST_P{20,33,50}      same, partial fires on the first close >= entry + 2 ADR
  Q_NOPARTIAL       the delayed-activation SMA-n trail alone (no partial, no BE) -- isolates the untested mechanism
  SELLALL_D3 / D5   sell 100% at the day-3 / day-5 close (his alternative momentum-burst style)
State updates (partial, BE) take effect from the next close; exits are checked first.
PRIMARY CELL: Q_DAY5_P33 - BASE on the precision pool, in % return (stop widths move under BE, so judge in percent;
  R reported alongside). 13 arms -> Sidak |t| ~ 2.9; the house bar |t| >= 3 governs the primary.
Also: max drawdown / give-back (share of trades that closed >= +1R and still ended <= 0), per-year arm - BASE.
Prior: mean -0.1 to -0.3R vs BASE for partial arms (trims already cost -0.25..-0.33R, BE at +1R -0.08R), smaller DD;
Q_NOPARTIAL is the only arm with a real chance of >= 0.

Run: PYTHONPATH=src .venv/bin/python3 run_qullamaggie_exit.py   (log -> data/studies/logs/qullamaggie_exit.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from run_precision_tier_control import build

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/qullamaggie_exit.log"
SLIP, HOLD, FLOOR, START, SPLIT = pt.SLIP, 60, 0.02, "2019-10-01", "2023-01-01"
ARMS = (["BASE"] + [f"Q_DAY{d}_P{p}" for d in (3, 5) for p in (20, 33, 50)] + [f"Q_BURST_P{p}" for p in (20, 33, 50)]
        + ["Q_NOPARTIAL", "SELLALL_D3", "SELLALL_D5"])


def simulate(C, E20, S10, S20, ADR, L, i, j, arm):
    """Returns (R, pct, peak close R)."""
    entry = C[i, j] * (1 + SLIP)
    stop = L[i, j]
    risk = entry - stop
    adr_px = ADR[i, j] / 100 * C[i, j]
    sma = S10 if ADR[i, j] >= 5 else S20
    q = arm.startswith("Q_")
    p = 0.0
    if "_P" in arm:
        p = int(arm.split("_P")[1]) / 100
    import re
    mday = re.match(r"(?:Q_DAY|SELLALL_D)(\d+)", arm)
    day = int(mday.group(1)) if mday else None
    burst = arm.startswith("Q_BURST")
    part_px, partial_done, peak = None, False, 0.0
    end = min(i + HOLD, len(C) - 1)
    k = i
    for k in range(i + 1, end + 1):
        c = C[k, j]
        if not np.isfinite(c):
            continue
        peak = max(peak, (c - entry) / risk)
        if arm.startswith("SELLALL") and k - i == day:
            break
        if c < stop:
            break
        if arm == "BASE":
            if np.isfinite(E20[k, j]) and c < E20[k, j]:
                break
        elif q:
            m = sma[k, j]
            if np.isfinite(m) and m > stop and c < m:          # trail active only once the MA is above the stop
                break
        # state updates, effective from the next close
        if q and p > 0 and not partial_done and ((day is not None and k - i == day) or (burst and c >= entry + 2 * adr_px)):
            part_px, partial_done = c * (1 - SLIP), True
            stop = max(stop, entry)
    exit_px = C[k, j] * (1 - SLIP)
    if part_px is not None:
        avg = p * part_px + (1 - p) * exit_px
    else:
        avg = exit_px
    return (avg - entry) / risk, 100 * (avg / entry - 1), peak


def tstat_by_date(d: pd.Series, dates: pd.Series) -> float:
    g = d.groupby(dates).mean()
    return float(g.mean() / g.std(ddof=1) * np.sqrt(len(g))) if len(g) > 2 else np.nan


def run_pool(label, mask, P, lines, primary: bool):
    C, L, E20, ADR = P.close.values, P.low.values, P.ema20.values, P.adr.values
    S10 = P.close.rolling(10).mean().values
    S20 = P.close.rolling(20).mean().values
    m = mask[mask.index >= START]
    off = len(mask) - len(m)
    ii, jj = np.where(m.values)
    rows = []
    for i, j in zip(ii + off, jj):
        entry = C[i, j] * (1 + SLIP)
        risk = entry - L[i, j]
        if not np.isfinite(risk) or risk / entry < FLOOR or risk / entry > 0.25 or i + 1 >= len(C) \
                or not np.isfinite(ADR[i, j]):
            continue
        rec = dict(date=P.close.index[i], sym=P.close.columns[j])
        for a in ARMS:
            r, pc, peak = simulate(C, E20, S10, S20, ADR, L, i, j, a)
            rec[a], rec[a + "_pct"] = r, pc
            if a == "BASE":
                rec["peakR"] = peak
        rows.append(rec)
    T = pd.DataFrame(rows)
    T["date"] = pd.to_datetime(T.date)
    lines.append(f"\n## {label}: {len(T):,} trades, {T.sym.nunique()} names, {T.date.nunique()} dates "
                 f"({T.date.min().date()} -> {T.date.max().date()})")
    reached1 = T.peakR >= 1
    out = []
    h1 = T.date < SPLIT
    for a in ARMS:
        dp = T[a + "_pct"] - T["BASE_pct"]
        dr = T[a] - T["BASE"]
        out.append(dict(arm=a, pct=T[a + "_pct"].mean(), R=T[a].mean(), R_cap20=T[a].clip(-20, 20).mean(),
                        d_pct=dp.mean(), t_pct=tstat_by_date(dp, T.date), h1_pct=dp[h1].mean(), h2_pct=dp[~h1].mean(),
                        d_R=dr.mean(), t_R=tstat_by_date(dr, T.date),
                        giveback=100 * ((T[a] <= 0) & reached1).sum() / max(reached1.sum(), 1)))
    S = pd.DataFrame(out)
    lines.append("arm - BASE, paired, t clustered by entry date; % = per-trade return, R uncapped (R_cap20 shown)")
    lines.append(S.round(3).to_string(index=False))
    Y = pd.DataFrame({a: (T[a + "_pct"] - T.BASE_pct).groupby(T.date.dt.year).mean() for a in ARMS[1:]})
    Y["n"] = T.groupby(T.date.dt.year).size()
    lines.append("per year, arm - BASE (% per trade):\n" + Y.round(2).T.to_string())
    eq = []
    for a in ARMS:
        s = T.sort_values("date")[a + "_pct"].values
        cum = np.cumsum(s)
        eq.append(dict(arm=a, total_pct=cum[-1], maxDD_pct=(np.maximum.accumulate(cum) - cum).max()))
    lines.append("fixed-size equity curve (% summed, trades in date order):\n" + pd.DataFrame(eq).round(1).to_string(index=False))
    T.to_parquet(REPO / f"data/studies/logs/qullamaggie_exit_{'precision' if primary else 'generic'}_trades.parquet",
                 index=False)
    return S


def main():
    P, brk, prec = build()
    lines = ["# Qullamaggie partial-then-trail [WL-4] (pre-registration in the docstring)"]
    Sp = run_pool("PRIMARY pool: precision-tier house breakouts", prec, P, lines, True)
    Sg = run_pool("second pool: generic house breakouts (ADR >= 3)", brk, P, lines, False)
    print("\n".join(lines))
    r = Sp.set_index("arm").loc["Q_DAY5_P33"]
    print(f"\nPRIMARY CELL Q_DAY5_P33 - BASE (precision, %): {r.d_pct:+.3f}pp t {r.t_pct:+.2f} halves "
          f"{r.h1_pct:+.3f}/{r.h2_pct:+.3f} | R {r.d_R:+.3f} t {r.t_R:+.2f}")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
