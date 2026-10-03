#!/usr/bin/env python3
"""
WEAK-MARKET ENTRY TACTICS: are Drendel's "buy weakness" entries relatively better when the market is weak?
(pre-registered 2026-10-02, before any run; Gabe after the Drendel review: "I would be interested if these
strategies are relatively better than others in weak markets")

THE CLAIM (Nick Drendel, video xYLU6Ep2U1M): in a downtrending or choppy market breakouts stop following
through, so buy WEAKNESS instead -- undercut & reclaim, oops reversal, ugly close -> gap-up -- on leaders.
Every earlier test of these entries (UR t -0.31 vs a random minute; reclaim vs pullback-low best t 2.69;
confirmation ladder) pooled ALL regimes. The regime-conditional claim is the untested axis.

DATA. liquid_panel_2009 (yfinance adjusted daily, 2009-01 -> 2026-09, 1,728 names; ⚠ 2026 survivors, which
flatters dip-buying -- the same-date control is drawn from the same survivor panel, which offsets some of it).
Signals 2010-01 -> 2026-08 (room for the hold). VWAP recovery is NOT testable here (single-name 1-min bars
start 2024-10) and is out of scope.

UNIVERSE ("leaders", Drendel: "always focus on the leading stocks"): eligible (ADDV >= $50M, px >= $5, not
suspect), ADR >= 3, and 63-session return at t-1 in the top 30% of eligible names that date.

TACTICS (daily proxies; all level/context values known at t-1; day t = the event day):
  context (T1, T2)  pullback underway: close[t-1] <= max(close[t-10..t-1]) - 1 ADR (in price)
  T1 UR      L in {min low[t-10..t-1], EMA20[t-1], EMA50[t-1]}: open[t] >= L, low[t] < L, close[t] > L.
             Entry = close[t] (the house's best entry; a buy-stop at L cannot be scored on daily bars
             without knowing whether the reclaim came after the low).
  T2 OOPS    L in {low[t-1], EMA20[t-1], EMA50[t-1]}: open[t] < L, close[t] > L. Entry = close[t].
  T3 UGLY    L in {EMA20, EMA50} at t-1: close[t-1] < L and in the bottom third of day t-1's range;
             open[t] > max(L, close[t-1]). Entry = open[t] (the closest daily proxy for his ORB trigger).
  BO (the "others")  house breakout: close[t] > max(high[t-20..t-1]), close > EMA50. Entry = close[t].
  Levels are pooled within a tactic (one event per name-day).

OUTCOME. % return from entry to close[t+10] (10 sessions), minus the mean of 3 random OTHER leaders on the
same date entered the same way (open or close). Excess return, not R: the stops differ by tactic and R would
move the denominator (CLAUDE.md: judge in percent). Slippage cancels (same fill type both sides).

REGIME at t-1 (ex-ante). WEAK = SPY in a downtrend (close < EMA20 and EMA10 < EMA20 -- Drendel's own
"trends under declining 10 and 20-day EMAs") OR breadth damage (< 40% of eligible names above their 50-SMA --
his "choppy" tape where the index hides damage under the hood). STRONG = everything else.

PRIMARY (3 cells, one per tactic): in WEAK regimes, tactic excess minus BO excess. "Relatively better than
others in weak markets" = this > 0. Month-clustered SE; difference SE = sqrt(se1^2 + se2^2).
SECONDARY (reported, not a pass): the interaction (tactic excess WEAK - STRONG) and each tactic's raw WEAK
excess vs its control.
BAR (discovery track): |t| >= 3 (Sidak over 3 is 2.39; the house 3 governs), both chronological halves
(split 2018-01-01) the same sign, and a majority of WEAK years the same sign.
PRIOR: ~25%. The entry-extension mechanism says buying lower helps in every regime, so a gap vs the breakout is
plausible; but survivorship flatters exactly these dips, so a pass needs the per-year check to hold.
EXPLORATORY: per-level cells; Drendel's volume spike (event-day volume >= 1.5x 20-day avg); hold 5.

  PYTHONPATH=src .venv/bin/python3 run_weak_market_entries.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from lib.studies.pattern_test import load_panel

HOLD = 10
N_CTL = 3
SPLIT = pd.Timestamp("2018-01-01")
OUT = "data/studies/weak_market_entries_2026-10-02"
RNG = np.random.default_rng(20261002)


def main() -> None:
    P = load_panel("data/cache/liquid_panel_2009.parquet")
    raw = pd.read_parquet("data/cache/liquid_panel_2009.parquet")
    V = raw.pivot(index="date", columns="ticker", values="volume").reindex_like(P.close)
    O, H, L, C = P.open.reindex_like(P.close), P.high, P.low, P.close
    dates = C.index
    adr_px = P.adr / 100 * C.shift(1)
    e10 = C.ewm(span=10, adjust=False).mean(); e20 = P.ema20; e50 = C.ewm(span=50, adjust=False).mean()
    sma50 = C.rolling(50).mean()

    elig = P.elig & (P.adr >= 3)
    r63 = C.shift(1) / C.shift(64) - 1
    rk = r63.where(P.elig.shift(1, fill_value=False)).rank(axis=1, pct=True)
    leader = elig & (rk >= 0.70)

    # regime at t-1
    spy = C["SPY"]
    down = (spy < e20["SPY"]) & (e10["SPY"] < e20["SPY"])
    breadth = (C > sma50).where(P.elig).sum(axis=1) / P.elig.sum(axis=1)
    weak = (down | (breadth < 0.40)).shift(1, fill_value=False)
    comp = pd.DataFrame({"down": down.shift(1, fill_value=False), "breadth_lt40": (breadth < 0.40).shift(1, fill_value=False)})

    pb = C.shift(1) <= C.rolling(10).max().shift(1) - adr_px
    lo10 = L.rolling(10).min().shift(1)
    lv1 = {"lo10": lo10, "ema20": e20.shift(1), "ema50": e50.shift(1)}
    lv2 = {"pdl": L.shift(1), "ema20": e20.shift(1), "ema50": e50.shift(1)}
    T = {}
    T["UR"] = {k: pb & (O >= x) & (L < x) & (C > x) for k, x in lv1.items()}
    T["OOPS"] = {k: pb & (O < x) & (C > x) for k, x in lv2.items()}
    rng1 = (H - L).shift(1)
    ugly = (C.shift(1) - L.shift(1)) <= rng1 / 3
    T["UGLY"] = {k: (C.shift(1) < x) & ugly & (O > np.maximum(x, C.shift(1))) for k, x in {"ema20": e20.shift(1), "ema50": e50.shift(1)}.items()}
    T["BO"] = {"20dh": (C > H.rolling(20).max().shift(1)) & (C > e50)}
    entry_kind = {"UR": "close", "OOPS": "close", "UGLY": "open", "BO": "close"}
    volspike = V >= 1.5 * V.rolling(20).mean().shift(1)

    fwd = {}
    for kind, src in (("close", C), ("open", O)):
        fwd[kind] = (C.shift(-HOLD) / src - 1) * 100

    lo, hi = dates.searchsorted(pd.Timestamp("2010-01-01")), len(dates) - HOLD - 1
    L_arr = leader.values
    rows = []
    for tac, cells in T.items():
        F = fwd[entry_kind[tac]].values
        for lvl, m in cells.items():
            M = (m & leader).values
            for i in range(lo, hi):
                js = np.flatnonzero(M[i])
                if not len(js):
                    continue
                pool = np.flatnonzero(L_arr[i] & np.isfinite(F[i]))
                for j in js:
                    if not np.isfinite(F[i, j]):
                        continue
                    cp = pool[pool != j]
                    if len(cp) < N_CTL:
                        continue
                    ctl = F[i, RNG.choice(cp, N_CTL, replace=False)].mean()
                    rows.append((tac, lvl, dates[i], C.columns[j], F[i, j], F[i, j] - ctl, bool(volspike.values[i, j])))
    E = pd.DataFrame(rows, columns=["tactic", "level", "date", "sym", "ret", "excess", "volspike"])
    E["weak"] = weak.reindex(E.date).values
    E["down"] = comp.down.reindex(E.date).values; E["breadth_lt40"] = comp.breadth_lt40.reindex(E.date).values
    E["month"] = E.date.dt.to_period("M")
    E.to_csv(f"{OUT}_events.csv", index=False)

    def ms(x: pd.DataFrame) -> tuple[float, float, int]:
        g = x.groupby("month").excess.agg(["sum", "count"])
        n = g["count"].sum()
        if n < 30 or len(g) < 6:
            return np.nan, np.nan, int(n)
        mu = g["sum"].sum() / n
        resid = (x.excess - mu).groupby(x.month).sum()
        se = np.sqrt((resid ** 2).sum()) / n * np.sqrt(len(g) / (len(g) - 1))
        return mu, se, int(n)

    pooled = E.sort_values("level").drop_duplicates(["tactic", "date", "sym"])
    out = []
    bo = pooled[pooled.tactic == "BO"]
    for tac in ("UR", "OOPS", "UGLY"):
        x = pooled[pooled.tactic == tac]
        r = {"tactic": tac}
        for reg, f in (("weak", True), ("strong", False)):
            mu, se, n = ms(x[x.weak == f]); r[f"{reg}_ex"], r[f"{reg}_t"], r[f"{reg}_n"] = mu, mu / se, n
        bmu, bse, bn = ms(bo[bo.weak])
        tmu, tse, _ = ms(x[x.weak])
        r["bo_weak_ex"], r["bo_weak_n"] = bmu, bn
        r["PRIMARY_diff"] = tmu - bmu; r["PRIMARY_t"] = (tmu - bmu) / np.sqrt(tse ** 2 + bse ** 2)
        smu, sse, _ = ms(x[~x.weak])
        r["interact"] = tmu - smu; r["interact_t"] = (tmu - smu) / np.sqrt(tse ** 2 + sse ** 2)
        for half, sel in (("h1", x.date < SPLIT), ("h2", x.date >= SPLIT)):
            bsel = bo.date < SPLIT if half == "h1" else bo.date >= SPLIT
            r[f"{half}_diff"] = ms(x[sel & x.weak])[0] - ms(bo[bsel & bo.weak])[0]
        yrs = []
        for y, g in x[x.weak].groupby(x.date.dt.year):
            b = bo[bo.weak & (bo.date.dt.year == y)]
            if len(g) >= 10 and len(b) >= 10:
                yrs.append(g.excess.mean() - b.excess.mean())
        r["yrs_pos"] = f"{sum(v > 0 for v in yrs)}/{len(yrs)}"
        out.append(r)
    R = pd.DataFrame(out)
    bw, bs = ms(bo[bo.weak]), ms(bo[~bo.weak])
    R.to_csv(f"{OUT}_primary.csv", index=False)

    lines = [f"# Weak-market entry tactics — results ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
             f"Excess = 10-session % return minus 3 same-date random leaders, month-clustered t. WEAK share of dates "
             f"(2010+): {weak[dates >= '2010-01-01'].mean():.0%}.", "",
             f"House breakout: WEAK {bw[0]:+.2f}pp (t {bw[0] / bw[1]:.2f}, n {bw[2]}) · STRONG {bs[0]:+.2f}pp (t {bs[0] / bs[1]:.2f}, n {bs[2]})", "",
             "## Primary (tactic − breakout, WEAK regime) + secondary", "", R.round(3).to_markdown(index=False), "",
             "## Exploratory: per level × regime", ""]
    ex = []
    for (tac, lvl), g in E.groupby(["tactic", "level"]):
        for reg, f in (("weak", True), ("strong", False)):
            mu, se, n = ms(g[g.weak == f]); ex.append((tac, lvl, reg, n, mu, mu / se if se else np.nan))
        mu, se, n = ms(g[g.weak & g.volspike]); ex.append((tac, lvl, "weak+volspike", n, mu, mu / se if se else np.nan))
    for comp_name in ("down", "breadth_lt40"):
        for tac, g in pooled.groupby("tactic"):
            mu, se, n = ms(g[g[comp_name]]); ex.append((tac, "pooled", f"{comp_name} only", n, mu, mu / se if se else np.nan))
    lines.append(pd.DataFrame(ex, columns=["tactic", "level", "regime", "n", "excess_pp", "t"]).round(3).to_markdown(index=False))
    open(f"{OUT}_results.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
