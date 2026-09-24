"""
Kell Wedge Pop -- base vs no base, and vs the house breakout (queue [WL-1], 2026-09-23).

PRE-REGISTRATION (from data/traderlion/setups/kell_wedge_pop.md s7-8, written before this script ran)
-------------------------------------------------------------------------------------------------
Claim (Oliver Kell, TraderLion 2025-12-21 [01:01, 05:27]): after a correction below the 10/20 EMAs, the buy is
the break of a TIGHT MINI-BASE's swing high after a HIGHER LOW -- "not the move back above the averages".

Wedge pop at day t (liquid panel, 2019-10 on; every window ends at t-1 or t, nothing reads past t):
  1 close >= EMA100 (~20-week EMA)
  2 not extended on the weekly: (close / EMA50 - 1) / ADR <= 3
  3 ADR20 >= 3%, liquidity-eligible
  4 correction: >= 5 closes below EMA20 in sessions t-40 .. t-1
  5 reversal extension: some session in t-40 .. t-8 had low <= EMA20 - 1.5 ADR (operationalised as "at some
    session", not only at the min-low session)
  6 higher low: min low over t-7 .. t-1 (the 5-session base plus the 2 sessions before it) > min low over
    t-40 .. t-8, so the correction low is >= 3 sessions before the base starts
  7 mini base t-5 .. t-1: high-to-low span <= 2.0 ADR
  8 volatility contraction: mean (high-low)/close over the base <= 0.8 x ADR20
  9 base low within 1.0 ADR of EMA20 (at t-1)
  T trigger: close > base high AND close > EMA10 AND close > EMA20. One signal per correction (>= 5 sub-EMA20
    closes since the previous accepted signal in that name).
Entry = trigger close, 0.10% slippage a side. Stop = base low judged on the close, floored at 0.5 ADR below the
entry (widen). Exit = first close < EMA20 (primary) / < EMA10 (secondary), cap 120 sessions. Metric = % return.

Questions and controls (all DATE-MATCHED, cross-name: the 2026-09-23 VCP test showed a same-name window is
outcome-selected)
  Q1 PRIMARY  wedge pop vs the house breakouts in OTHER names on the SAME date (close > prior 20d high,
              ADR >= 3, eligible; stop = that day's low, same exit). Paired per signal, date-clustered t.
  Q2          wedge pop vs the "MA-cross only" STRUCTURE CONTROL on the same date: other names meeting 1-5 whose
              close is the first back above both EMAs (prior close not above both) but which FAIL 6-9. Same
              entry/exit; stop = 5-session low with the same floor. This is Kell's own claim.
  Also: ext_above_level (entry vs prior 20d high, in ADR) for every group; harness rows via
  lib.studies.pattern_test (control=post, ledger; xname report only).
Cells: 2 questions x 2 exits = 4 -> Sidak |t| >= 2.49; the house bar |t| >= 3 governs the PRIMARY cell.
PASS = Q1-EMA20 |t| >= 3 with both halves (split 2023-01-01) positive, per-year signs shown, AND Q2-EMA20 the
same sign. Neighbourhood (robustness only, no verdict of its own): rule 5 depth 1.0/3.0, rule 7 span 1.5/3.0,
rule 9 1.0 -> 0.5/1.5, each moved alone.
Prior ~65% NULL. A win on Q1 alone that comes from buying lower restates the entry-extension finding; Q2 is what
separates Kell's structure from that.

Run: PYTHONPATH=src .venv/bin/python3 run_kell_wedge_pop.py   (log -> data/studies/logs/kell_wedge_pop.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lib.studies.pattern_test import SLIP, daily_signals, load_panel, run_daily

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/kell_wedge_pop.log"
START = "2019-10-01"
SPLIT = "2023-01-01"
CAP = 120
BASE = dict(depth=1.5, span=2.0, contr=0.8, near=1.0)


def frames(P):
    C, H, L = P.close, P.high, P.low
    adr = P.adr                                   # % (prior-shifted 20d mean of H/L-1)
    adrpx = adr / 100 * C
    e10 = C.ewm(span=10, adjust=False).mean()
    e20 = P.ema20
    e50 = C.ewm(span=50, adjust=False).mean()
    e100 = C.ewm(span=100, adjust=False).mean()
    return C, H, L, adr, adrpx, e10, e20, e50, e100


def masks(P, depth=1.5, span=2.0, contr=0.8, near=1.0):
    C, H, L, adr, adrpx, e10, e20, e50, e100 = frames(P)
    r1 = C >= e100
    r2 = ((C / e50 - 1) * 100 / adr) <= 3
    r3 = (adr >= 3) & P.elig
    below = (C < e20).astype(float)
    r4 = below.shift(1).rolling(40).sum() >= 5
    deep = (L <= e20 - depth * adrpx).astype(float)
    r5 = deep.shift(8).rolling(33).max() > 0                      # sessions t-40 .. t-8
    r5_any = deep.shift(1).rolling(40).max() > 0                  # structure control: anywhere in t-40 .. t-1
    corr_low = L.shift(8).rolling(33).min()
    recent_low = L.shift(1).rolling(7).min()
    r6 = recent_low > corr_low
    bh = H.shift(1).rolling(5).max()
    bl = L.shift(1).rolling(5).min()
    c1 = C.shift(1)
    r7 = (bh - bl) / c1 * 100 <= span * adr
    r8 = ((H - L) / C).shift(1).rolling(5).mean() * 100 <= contr * adr
    r9 = (bl - e20.shift(1)).abs() / c1 * 100 <= near * adr
    ctx = r1 & r2 & r3 & r4
    wp = ctx & r5 & r6 & r7 & r8 & r9 & (C > bh) & (C > e10) & (C > e20)
    cross = (C > e10) & (C > e20) & ~((c1 > e10.shift(1)) & (c1 > e20.shift(1)))
    struct = ctx & r5_any & cross & ~(r5 & r6 & r7 & r8 & r9)
    for m in (wp, struct):
        m[m.index < START] = False
    return one_per_correction(wp.fillna(False), below), one_per_correction(struct.fillna(False), below), bl


def one_per_correction(m: pd.DataFrame, below: pd.DataFrame) -> pd.DataFrame:
    out = np.zeros(m.shape, dtype=bool)
    cb = below.fillna(0).values.cumsum(axis=0)
    mv = m.values
    for j in range(mv.shape[1]):
        last = None
        for i in np.flatnonzero(mv[:, j]):
            if last is None or cb[i - 1, j] - cb[last, j] >= 5:
                out[i, j] = True
                last = i
    return pd.DataFrame(out, index=m.index, columns=m.columns)


def house_breakout(P):
    lvl = P.high.shift(1).rolling(20).max()
    m = ((P.close > lvl) & (P.adr >= 3) & P.elig).fillna(False)
    m[m.index < START] = False
    return m, lvl


def trade(C, E, adrpx, j, i, stop) -> float:
    """% return: enter at close i, exit on first close < E or through the stop, cap CAP sessions."""
    if i + 1 >= len(C) or not np.isfinite(C[i, j]):
        return np.nan
    entry = C[i, j] * (1 + SLIP)
    floor = C[i, j] - 0.5 * adrpx[i, j]
    stop = min(stop, floor) if np.isfinite(stop) else floor
    px = np.nan
    for k in range(i + 1, min(i + 1 + CAP, len(C))):
        c = C[k, j]
        if not np.isfinite(c):
            continue
        if c < stop or (np.isfinite(E[k, j]) and c < E[k, j]):
            px = c
            break
    if not np.isfinite(px):
        px = C[min(i + CAP, len(C) - 1), j]
    return 100 * (px * (1 - SLIP) / entry - 1) if np.isfinite(px) else np.nan


def tstat(x: pd.Series, by: pd.Series) -> float:
    d = x.groupby(by).mean()
    return float(d.mean() / d.std() * np.sqrt(len(d))) if len(d) > 2 and d.std() > 0 else np.nan


def book(P, m: pd.DataFrame, stop: pd.DataFrame, lvl: pd.DataFrame, E, tag: str) -> pd.DataFrame:
    C, adrpx = P.close.values, (P.adr / 100 * P.close).values
    rows = []
    for i, j in zip(*np.where(m.values)):
        r = trade(C, E, adrpx, j, i, stop.values[i, j])
        if np.isfinite(r):
            ext = (C[i, j] - lvl.values[i, j]) / adrpx[i, j] if np.isfinite(lvl.values[i, j]) else np.nan
            rows.append(dict(date=m.index[i], i=i, sym=m.columns[j], ret=r, ext=ext, grp=tag))
    return pd.DataFrame(rows)


def paired(W: pd.DataFrame, K: pd.DataFrame) -> dict:
    ctl = K.groupby("date").ret.mean()
    D = W.assign(ctl=W.date.map(ctl)).dropna(subset=["ctl"])
    D["diff"] = D.ret - D.ctl
    return dict(n=len(D), wp=D.ret.mean(), ctl=D.ctl.mean(), diff=D["diff"].mean(), t=tstat(D["diff"], D.date),
                h1=D[D.date < SPLIT]["diff"].mean(), h2=D[D.date >= SPLIT]["diff"].mean(),
                n1=int((D.date < SPLIT).sum()), n2=int((D.date >= SPLIT).sum()), _D=D)


def fmt(r: dict) -> str:
    return (f"n {r['n']:5d} | wedge pop {r['wp']:+.2f}% vs control {r['ctl']:+.2f}% | diff {r['diff']:+.2f}pp "
            f"t {r['t']:+.2f} | halves {r['h1']:+.2f}/{r['h2']:+.2f} (n {r['n1']}/{r['n2']})")


def run_cells(P, params: dict, hb, hlvl, lines: list[str], full: bool) -> dict:
    wp, st, bl = masks(P, **params)
    out = {}
    for ename, E in (("EMA20", P.ema20.values), ("EMA10", P.close.ewm(span=10, adjust=False).mean().values)):
        W = book(P, wp, bl, hlvl, E, "wedge")
        HB = book(P, hb & ~wp, P.low, hlvl, E, "house")
        S = book(P, st, bl, hlvl, E, "struct")
        q1, q2 = paired(W, HB), paired(W, S)
        out[ename] = (q1, q2, W, HB, S)
        if full:
            lines.append(f"\n## exit {ename}")
            lines.append(f"groups: wedge pops {len(W)} ({W.sym.nunique()} names), mean {W.ret.mean():+.2f}% "
                         f"(t vs 0 {tstat(W.ret, W.date):+.2f}), win {100 * (W.ret > 0).mean():.0f}%, "
                         f"median ext {W.ext.median():+.2f} ADR | house bo {len(HB)} mean {HB.ret.mean():+.2f}% "
                         f"ext {HB.ext.median():+.2f} | structure ctl {len(S)} mean {S.ret.mean():+.2f}% "
                         f"ext {S.ext.median():+.2f}")
            lines.append("Q1 vs same-date house breakouts : " + fmt(q1))
            lines.append("Q2 vs same-date MA-cross-only   : " + fmt(q2))
            for lab, q in (("Q1", q1), ("Q2", q2)):
                D = q["_D"]
                yr = D.groupby(D.date.dt.year).agg(n=("diff", "size"), wp=("ret", "mean"), ctl=("ctl", "mean"),
                                                   diff=("diff", "mean"))
                lines.append(f"{lab} per year:\n" + yr.round(2).to_string())
            W.to_csv(REPO / f"data/studies/logs/kell_wedge_pop_{ename}_trades.csv", index=False)
    return out


def main() -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    P = load_panel()
    hb, hlvl = house_breakout(P)
    lines: list[str] = ["# Kell Wedge Pop -- pre-registered run (see docstring)"]
    R = run_cells(P, BASE, hb, hlvl, lines, full=True)
    lines.append("\n## neighbourhood (primary cell Q1-EMA20 and Q2-EMA20; robustness only)")
    neigh = {}
    for k, vals in (("depth", (1.0, 3.0)), ("span", (1.5, 3.0)), ("near", (0.5, 1.5))):
        for v in vals:
            prm = {**BASE, k: v}
            o = run_cells(P, prm, hb, hlvl, lines, full=False)["EMA20"]
            neigh[f"{k}={v}"] = (o[0], o[1])
            lines.append(f"{k}={v}: Q1 {fmt(o[0])}\n{'':>10}Q2 {fmt(o[1])}")
    print("\n".join(lines))

    def pattern(P):
        wp, _, bl = masks(P, **BASE)
        floor = P.close - 0.5 * P.adr / 100 * P.close
        return daily_signals(wp, stop=np.minimum(bl, floor), side="long", since=START)
    print("\n\n# harness rows (entry at close, hold 120; R-based)")
    run_daily("kell wedge pop", pattern, hold=CAP, entry_at="close", control="post",
              note="Kell wedge pop per kell_wedge_pop.md s7, stop = base low (floor 0.5 ADR)")
    run_daily("kell wedge pop xname", pattern, hold=CAP, entry_at="close", control="xname", ledger=False)
    sys.stdout.close()
    sys.stdout = real
    for e in ("EMA20", "EMA10"):
        q1, q2, W, HB, S = R[e]
        print(f"[{e}] wedge pops {len(W)} ({W.sym.nunique()} names) mean {W.ret.mean():+.2f}% win "
              f"{100 * (W.ret > 0).mean():.0f}% ext {W.ext.median():+.2f} ADR | house {HB.ret.mean():+.2f}% "
              f"ext {HB.ext.median():+.2f} | struct {S.ret.mean():+.2f}% ext {S.ext.median():+.2f}")
        print(f"   Q1 {fmt(q1)}\n   Q2 {fmt(q2)}")
    for k, (a, b) in neigh.items():
        print(f"   {k:10s} Q1 diff {a['diff']:+.2f} t {a['t']:+.2f} (n {a['n']}) | Q2 diff {b['diff']:+.2f} "
              f"t {b['t']:+.2f} (n {b['n']})")
    print(f"log: {LOG}")


if __name__ == "__main__":
    main()
