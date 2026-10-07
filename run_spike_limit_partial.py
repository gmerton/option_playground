#!/usr/bin/env python3
"""
Resting-limit partial into an intraday spike, and the same-day "sell the spike, rebuy the close" harvest
(pre-registered 2026-10-06, NOT YET RUN; written after the 2026-10-06 fade review, where CRWD/PANW/MRVL spiked
before 10:00 and gave the spike back by the close).

WHAT IS ALREADY SETTLED (do not re-test): selling a partial at the CLOSE of a +2-ADR day is INVERTED
(WL-4 Q_BURST_P20/33/50 -1.42..-1.76pp, t -3.8..-4.1); Tito's single-day >=2-ADR spike override on calls is NULL
(t +0.18) and only caps the right tail; trims and "extended -> tighten" cost on daily bars.
WHAT IS NEW (the only axis tested here): the FILL MECHANISM. A resting LIMIT order fills INTRADAY at the level the
moment the spike reaches it; the daily-bar tests sold at the close, after the spike had already faded. Daily OHLC
tests this cleanly: the limit fills on any day whose HIGH exceeds it (fill at max(limit, open) less slippage),
no intraday bars needed. CLAUDE.md: a daily-bar null does not refute an intraday pattern -- this is that case.

Pools (identical to run_qullamaggie_exit.py: entry = breakout CLOSE +10 bps, initial stop = breakout-day low judged on
the close, risk floor 2%, cap 25%, hold cap 60 sessions, liquid_panel_2019, 2019-10 -> 2026-09):
  PRIMARY  precision-tier house breakouts     second  generic house breakouts (ADR >= 3)
Arms (every arm on the SAME trades; paired arm - BASE; t clustered by entry date; judged in % return, R alongside):
  BASE               20-EMA close trail + initial stop (house rule). Every arm below keeps BASE for the rest.
  LIM_E{k}_P{p}      one resting limit at entry + k*ADR_entry (k in 2,3), sells p% (25, 50) on the first day whose
                     high > limit; fill = max(limit, open)*(1-SLIP). No BE move, no trail change -- isolates the partial.
  CLOSE_E2_P{p}      twin of LIM_E2: same level, but sells at the CLOSE of the first day closing >= the level
                     (= WL-4's burst mechanism without its BE/SMA changes). Mechanism control for LIM_E2.
  LIM_D{k}_P{p}      the resting limit re-set every day at prev_close*(1 + k*ADR_t/100), k in 1.5, 2.0; fires once.
  HARV_D{k}_P{p}     Gabe's question: EVERY day whose high > prev_close*(1 + k*ADR_t/100), sell p% (25, 100) at
                     max(limit, open)*(1-SLIP) and REBUY p% at the close*(1+SLIP), paying $0.0065/share each way
                     (lib.studies.costs). Position unchanged into the next day. If the exit also fires that day the
                     sold piece stays sold (no rebuy). Reported per trade AND per fire-day after costs.
PRIMARY CELL: LIM_E2_P25 - BASE on the precision pool, in % per trade.
SECONDARY (pre-registered): mechanism LIM_E2_P25 - CLOSE_E2_P25; Gabe's cell HARV_D2_P100 - BASE (= harvest income).
Bar: |t| >= 3 with both halves (split 2023-01-01) the same sign and a majority of years positive; 14 non-BASE arms
-> Sidak |t| 2.91 at alpha 0.05, so the house 3.0 governs. Everything else exploratory.
Prior: LIM - BASE NEGATIVE (the book's edge is the right tail; WL-4 -1.4..-1.8pp); LIM - CLOSE twin small POSITIVE
(spike days close off the high); HARV ~ 0 after costs -- the open cell. INVERTED on HARV = a veto on same-day
sell/rebuy with a number attached; PASS would be the first same-day round trip the ledger supports.
Outcome-conditioning check: the limit level is known before the open; the fill uses the same day's high and the
rebuy the same day's close -- nothing after the decision enters the selection.
Decision: local (same engine as WL-4, minutes of CPU).

Run: PYTHONPATH=src .venv/bin/python3 run_spike_limit_partial.py   (log -> data/studies/logs/spike_limit_partial.log)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies import pattern_test as pt
from lib.studies.costs import COMMISSION_PER_LEG
from run_precision_tier_control import build

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/spike_limit_partial.log"
SLIP, HOLD, FLOOR, START, SPLIT = pt.SLIP, 60, 0.02, "2019-10-01", "2023-01-01"
ARMS = (["BASE"]
        + [f"LIM_E{k}_P{p}" for k in (2, 3) for p in (25, 50)]
        + [f"CLOSE_E2_P{p}" for p in (25, 50)]
        + [f"LIM_D{k}_P{p}" for k in ("1.5", "2.0") for p in (25, 50)]
        + [f"HARV_D{k}_P{p}" for k in ("1.5", "2.0") for p in (25, 100)])
PRIMARY = "LIM_E2_P25"


def _parse(arm):
    m = re.match(r"(LIM_E|CLOSE_E|LIM_D|HARV_D)([\d.]+)_P(\d+)", arm)
    return m.group(1), float(m.group(2)), int(m.group(3)) / 100


def simulate(O, H, C, E20, ADR, L, i, j, arm):
    """Returns (R, pct, peak close R, fires)."""
    entry = C[i, j] * (1 + SLIP)
    stop = L[i, j]
    risk = entry - stop
    adr_px0 = ADR[i, j] / 100 * C[i, j]
    kind, k, p = (None, 0.0, 0.0) if arm == "BASE" else _parse(arm)
    sold_px, sold_frac, harvest, fires, peak = None, 0.0, 0.0, 0, 0.0
    end = min(i + HOLD, len(C) - 1)
    kk = i
    for kk in range(i + 1, end + 1):
        c = C[kk, j]
        if not np.isfinite(c):
            continue
        peak = max(peak, (c - entry) / risk)
        exiting = c < stop or (np.isfinite(E20[kk, j]) and c < E20[kk, j])
        if kind in ("LIM_E", "CLOSE_E") and sold_px is None:
            level = entry + k * adr_px0
            if kind == "LIM_E" and H[kk, j] > level:
                sold_px, sold_frac = max(level, O[kk, j]) * (1 - SLIP), p
            elif kind == "CLOSE_E" and c >= level:
                sold_px, sold_frac = c * (1 - SLIP), p
        elif kind in ("LIM_D", "HARV_D"):
            prev = C[kk - 1, j]
            adr_t = ADR[kk, j]
            if np.isfinite(prev) and np.isfinite(adr_t):
                level = prev * (1 + k * adr_t / 100)
                if H[kk, j] > level:
                    fill = max(level, O[kk, j]) * (1 - SLIP)
                    if kind == "LIM_D" and sold_px is None:
                        sold_px, sold_frac = fill, p
                    elif kind == "HARV_D":
                        fires += 1
                        if exiting:                       # exit day: the sold piece stays sold
                            sold_px, sold_frac = fill, p
                        else:                             # rebuy at the close, pay both commissions
                            harvest += p * (fill - c * (1 + SLIP) - 2 * COMMISSION_PER_LEG)
        if exiting:
            break
    exit_px = C[kk, j] * (1 - SLIP)
    avg = sold_frac * sold_px + (1 - sold_frac) * exit_px if sold_px is not None else exit_px
    avg += harvest
    return (avg - entry) / risk, 100 * (avg / entry - 1), peak, fires


def tstat_by_date(d: pd.Series, dates: pd.Series) -> float:
    g = d.groupby(dates).mean()
    return float(g.mean() / g.std(ddof=1) * np.sqrt(len(g))) if len(g) > 2 else np.nan


def run_pool(label, mask, P, lines, primary: bool):
    O, H, C, L, E20, ADR = P.open.values, P.high.values, P.close.values, P.low.values, P.ema20.values, P.adr.values
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
            r, pc, peak, fires = simulate(O, H, C, E20, ADR, L, i, j, a)
            rec[a], rec[a + "_pct"] = r, pc
            if a.startswith("HARV"):
                rec[a + "_fires"] = fires
            if a == "BASE":
                rec["peakR"] = peak
        rows.append(rec)
    T = pd.DataFrame(rows)
    T["date"] = pd.to_datetime(T.date)
    lines.append(f"\n## {label}: {len(T):,} trades, {T.sym.nunique()} names, {T.date.nunique()} dates "
                 f"({T.date.min().date()} -> {T.date.max().date()})")
    reached1 = T.peakR >= 1
    h1 = T.date < SPLIT
    out = []
    for a in ARMS:
        dp = T[a + "_pct"] - T["BASE_pct"]
        dr = T[a] - T["BASE"]
        yrs = dp.groupby(T.date.dt.year).mean()
        row = dict(arm=a, pct=T[a + "_pct"].mean(), R=T[a].mean(), R_cap20=T[a].clip(-20, 20).mean(),
                   d_pct=dp.mean(), t_pct=tstat_by_date(dp, T.date), h1_pct=dp[h1].mean(), h2_pct=dp[~h1].mean(),
                   yrs_pos=f"{int((yrs > 0).sum())}/{len(yrs)}", d_R=dr.mean(), t_R=tstat_by_date(dr, T.date),
                   fired=100 * (dp != 0).mean(),
                   giveback=100 * ((T[a] <= 0) & reached1).sum() / max(reached1.sum(), 1))
        if a.startswith("HARV"):
            f = T[a + "_fires"]
            row["fires_per_trade"] = f.mean()
            row["pp_per_fire"] = dp.sum() / max(f.sum(), 1)
        out.append(row)
    S = pd.DataFrame(out)
    lines.append("arm - BASE, paired, t clustered by entry date; % = per-trade return, R uncapped (R_cap20 shown); "
                 "fired = % of trades where the arm differs from BASE")
    lines.append(S.round(3).to_string(index=False))
    tw = T[PRIMARY + "_pct"] - T["CLOSE_E2_P25_pct"]
    lines.append(f"mechanism: {PRIMARY} - CLOSE_E2_P25 = {tw.mean():+.3f}pp t {tstat_by_date(tw, T.date):+.2f} "
                 f"halves {tw[h1].mean():+.3f}/{tw[~h1].mean():+.3f}")
    Y = pd.DataFrame({a: (T[a + "_pct"] - T.BASE_pct).groupby(T.date.dt.year).mean() for a in ARMS[1:]})
    Y["n"] = T.groupby(T.date.dt.year).size()
    lines.append("per year, arm - BASE (% per trade):\n" + Y.round(2).T.to_string())
    eq = []
    for a in ARMS:
        s = T.sort_values("date")[a + "_pct"].values
        cum = np.cumsum(s)
        eq.append(dict(arm=a, total_pct=cum[-1], maxDD_pct=(np.maximum.accumulate(cum) - cum).max()))
    lines.append("fixed-size equity curve (% summed, trades in date order):\n" + pd.DataFrame(eq).round(1).to_string(index=False))
    T.to_parquet(REPO / f"data/studies/logs/spike_limit_partial_{'precision' if primary else 'generic'}_trades.parquet",
                 index=False)
    return S


def main():
    P, brk, prec = build()
    lines = ["# Resting-limit spike partial + same-day harvest (pre-registration in the docstring)"]
    Sp = run_pool("PRIMARY pool: precision-tier house breakouts", prec, P, lines, True)
    run_pool("second pool: generic house breakouts (ADR >= 3)", brk, P, lines, False)
    print("\n".join(lines))
    r = Sp.set_index("arm").loc[PRIMARY]
    print(f"\nPRIMARY CELL {PRIMARY} - BASE (precision, %): {r.d_pct:+.3f}pp t {r.t_pct:+.2f} halves "
          f"{r.h1_pct:+.3f}/{r.h2_pct:+.3f} yrs+ {r.yrs_pos} | R {r.d_R:+.3f} t {r.t_R:+.2f}")
    g = Sp.set_index("arm").loc["HARV_D2.0_P100"]
    print(f"GABE'S CELL HARV_D2.0_P100 - BASE (precision, %): {g.d_pct:+.3f}pp t {g.t_pct:+.2f} halves "
          f"{g.h1_pct:+.3f}/{g.h2_pct:+.3f} yrs+ {g.yrs_pos} | {g.fires_per_trade:.2f} fires/trade, "
          f"{g.pp_per_fire:+.3f}pp per fire after costs")


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
