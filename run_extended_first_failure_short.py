#!/usr/bin/env python3
"""
MECHANICAL "VERY EXTENDED NAME, FIRST FAILURE" SHORT (pre-registered 2026-10-01, before any scoring; Gabe: "yes...
I think Qullamaggie has a similar strategy on shorts"). Creator method -> DISCOVERY track (|t| >= 3).

WHY. Ariel's broker-logged shorts beat same-date ADR-matched names by +7.66pp over 10 sessions, t 3.39
(ariel_broker_picks_2026-10-01.md). His short slides describe one recurring spot: a name 10-13x ATR above its 50-day,
shorted at the first sign of failure ("first red day", "rejection of the 20sma", "break of prior day low").
Qullamaggie's parabolic short is the same idea (data/qullamaggie/README.md, Setup 3; codable proxy: big extension,
>= 3 up closes, short the first daily close below the prior day's low). The control in Ariel's test did not hold
EXTENSION fixed, so the question is whether the mechanical property carries the edge without his discretion.
PRIOR (negative, stated up front): single-name capitulation / exhaustion fades are 0 for 4 here (Breitstein scorecard
short every bucket negative; Tito honest fade t -0.59; bouncy ball FAIL), and no short-selectable universe was found
(0/10 cells, weak names still drift up). WHAT IS NEW: extension measured as distance above the 50-day SMA in ATR
units (his metric), the first-failure trigger on DAILY closes, a 10-session hold, and the house % excess vs
same-date names; plus an extension-without-trigger arm that isolates the trigger.

DATA   data/cache/liquid_panel_2009.parquet (1,728 liquid names, 2009-01 -> 2026-09). Eligible on day t: close >= $5,
       20-day mean dollar volume >= $50M (known at t-1). ⚠ Survivor-biased universe (today's liquid list): delisted
       names are absent, and they are a short's best outcome, so this flatters the shorts' CONTROLS less than it
       hurts the shorts. Read a null as "not proven on survivors".
DEFINITIONS (all from data known at the close of day t)
  ATR14  Wilder-style 14-day mean true range;  SMA50 of closes;  E_t = (close_t - SMA50_t) / ATR14_t.
  EXTENDED at t-1: max(E over t-5 .. t-1) >= K.
  FAILURE TRIGGER at t: close_t < low_(t-1) (first daily close below the prior day's low), the name EXTENDED at t-1,
         and no trigger for the same name in the previous 20 sessions (first failure only).
  ENTRY  short at the close of t. EXIT after h sessions at the close (h = 10 primary; 5, 20 secondary/reported).
  COSTS  10 bp per side; borrow not charged (stated; these are liquid names but borrow can be dear on parabolics).
CONTROLS
  C1  same-date eligible names in the trigger name's ADR(20) tercile, shorted the same way (Ariel test's control).
  C2  EXTENSION WITHOUT TRIGGER: the same name on its other EXTENDED days (E-max >= K) in t-10 .. t-1 that were not
      triggers, shorted at that close -- does the failure day matter, or just being extended?
PRIMARY  K = 8, h = 10: trigger short minus C1, net; t on entry-date cluster means.
         BAR: t >= 3; both halves (2010-2017 / 2018-2026) positive; a majority of calendar years positive; AND the
         absolute short return net of costs > 0 (a short must make money outright, not just beat its control).
         MDE at 80% power reported first; below it the verdict is UNDERPOWERED. POWER GATE: if the primary has
         < 200 events or < 150 dates, report UNDERPOWERED and do not loosen K.
SECONDARY (4; 5 cells in all, Sidak 5% two-sided |t| >= 2.57; the discovery bar of 3 governs adoption)
  S1 K = 10 (his stated 10-13x)  S2 K = 6  S3 K = 8, h = 20  S4 K = 8, h = 10, trigger minus C2 (does the trigger matter?)
REPORTED (no claim): h = 5; event counts by year; the 2025-10 -> 2026-03 window (Ariel's sample) separately.
Local: daily panel, minutes of CPU.
"""
from __future__ import annotations

from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd

PANEL = Path("data/cache/liquid_panel_2009.parquet")
LOG = Path("data/studies/logs/extended_first_failure_short.log")
EV = Path("data/studies/logs/extended_first_failure_short_events.csv")
COST = 0.002
SPLIT = pd.Timestamp("2018-01-01")


def wide(p: pd.DataFrame, col: str) -> pd.DataFrame:
    return p.pivot(index="date", columns="ticker", values=col).sort_index()


def main() -> None:
    p = pd.read_parquet(PANEL)
    O, H, L, C, DV = (wide(p, c) for c in ("open", "high", "low", "close", "dolvol"))
    prevC = C.shift(1)
    tr = np.maximum(H - L, np.maximum((H - prevC).abs(), (L - prevC).abs()))
    atr = tr.rolling(14).mean()
    sma50 = C.rolling(50).mean()
    E = (C - sma50) / atr
    adr = ((H / L - 1).rolling(20).mean() * 100).shift(1)
    elig = (C.shift(1) >= 5) & (DV.rolling(20).mean().shift(1) >= 50e6)
    Emax5 = E.shift(1).rolling(5).max()                      # max E over t-5 .. t-1
    fail = (C < L.shift(1)) & elig
    idx, cols = C.index, C.columns
    fwd = {h: C.shift(-h) / C - 1 for h in (5, 10, 20)}       # forward close-to-close

    out = ["# Extended name, first failure short (pre-registered 2026-10-01); see docstring",
           f"panel {idx.min().date()} -> {idx.max().date()}, {len(cols)} names"]
    rows = []
    for K in (6, 8, 10):
        trig = fail & (Emax5 >= K)
        tv = trig.values.copy()
        # first failure only: no trigger for the same name in the previous 20 sessions
        last = np.full(tv.shape[1], -10_000)
        for i in range(tv.shape[0]):
            hit = tv[i]
            ok = hit & (i - last > 20)
            last[hit] = np.where(ok[hit], i, last[hit])
            tv[i] = ok
        ext = (E >= K) & elig                                  # extended days (for C2)
        for i, j in zip(*np.nonzero(tv)):
            d, tk = idx[i], cols[j]
            rec = dict(K=K, date=d, ticker=tk, E=float(Emax5.iat[i, j]), adr=float(adr.iat[i, j]))
            a_el = adr.iloc[i][elig.iloc[i].values].dropna()
            for h in (5, 10, 20):
                if i + h >= len(idx) or pd.isna(fwd[h].iat[i, j]):
                    continue
                rec[f"s{h}"] = -fwd[h].iat[i, j] - COST
                if len(a_el) > 30 and pd.notna(rec["adr"]):
                    q1, q2 = a_el.quantile([1 / 3, 2 / 3])
                    a = rec["adr"]
                    peers = a_el[a_el <= q1] if a <= q1 else a_el[(a_el > q1) & (a_el <= q2)] if a <= q2 else a_el[a_el > q2]
                    rec[f"c1_{h}"] = -fwd[h].iloc[i][peers.index.difference([tk])].dropna().mean() - COST
                if h == 10:
                    js = [k for k in range(max(0, i - 10), i) if ext.iat[k, j] and not tv[k, j] and pd.notna(fwd[10].iat[k, j])]
                    if js:
                        rec["c2_10"] = float(np.mean([-fwd[10].iat[k, j] for k in js])) - COST
            rows.append(rec)
    R = pd.DataFrame(rows)
    R.to_csv(EV, index=False)

    def cell(K: int, x: str, c: str | None, label: str, primary: bool = False) -> None:
        g = R[R.K == K].copy()
        g["x"] = g[x] - (g[c] if c else 0)
        g = g.dropna(subset=["x"])
        if len(g) < 5:
            out.append(f"  {label:42s} n {len(g)} -- too few")
            return
        dm = g.groupby("date").x.mean()
        se = dm.std(ddof=1) / sqrt(len(dm))
        t = dm.mean() / se
        h1, h2 = dm[dm.index < SPLIT].mean(), dm[dm.index >= SPLIT].mean()
        yr = dm.groupby(dm.index.year).mean()
        absr = g[x].mean()
        line = (f"  {label:42s} n {len(g):5d} / {len(dm):4d} dates | mean {100*g.x.mean():+6.2f}pp | date-cluster t {t:+.2f} | "
                f"MDE(80%) {100*2.8*se:.2f}pp | halves {100*h1:+.2f} / {100*h2:+.2f} | years + {int((yr>0).sum())}/{len(yr)} | "
                f"abs short {100*absr:+.2f}% | win {100*(g.x>0).mean():.0f}%")
        out.append(line)
        if primary:
            gate = len(g) >= 200 and len(dm) >= 150
            ok = gate and t >= 3 and h1 > 0 and h2 > 0 and (yr > 0).mean() > 0.5 and absr > 0
            out.append(f"  -> power gate {'met' if gate else 'NOT met (UNDERPOWERED)'}; PRIMARY bar: {'PASS' if ok else 'NOT MET'}")

    out.append("\n## event counts: " + ", ".join(f"K={k}: {int((R.K==k).sum())} events / {R[R.K==k].date.nunique()} dates" for k in (6, 8, 10)))
    out.append("## PRIMARY: K=8, h=10, trigger short - C1 (bar t>=3, halves +, years majority +, absolute > 0)")
    cell(8, "s10", "c1_10", "K=8 h=10 vs C1", primary=True)
    out.append("## SECONDARY (Sidak |t| >= 2.57)")
    cell(10, "s10", "c1_10", "S1 K=10 h=10 vs C1")
    cell(6, "s10", "c1_10", "S2 K=6 h=10 vs C1")
    cell(8, "s20", "c1_20", "S3 K=8 h=20 vs C1")
    cell(8, "s10", "c2_10", "S4 K=8 h=10 vs C2 extension w/o trigger")
    out.append("## reported")
    cell(8, "s5", "c1_5", "K=8 h=5 vs C1")
    cell(8, "s10", None, "K=8 h=10 absolute short (no control)")
    w = R[(R.date >= "2025-10-01") & (R.date <= "2026-03-31")]
    R_bak, R = R, w
    cell(8, "s10", "c1_10", "Ariel window 2025-10..2026-03, K=8")
    cell(10, "s10", "c1_10", "Ariel window 2025-10..2026-03, K=10")
    R = R_bak
    yr = R[R.K == 8].groupby(R[R.K == 8].date.dt.year).size()
    out.append("  K=8 events by year: " + ", ".join(f"{y}:{n}" for y, n in yr.items()))
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
