#!/usr/bin/env python3
"""
LUK-STYLE WHOLE-BOOK TIMING: GO FLAT WHEN THE TAPE TURNS (pre-registered 2026-10-03, before the run)

WHY. Gabe 2026-10-03: Luk spends long stretches short or flat; what was he watching? Over his 37 labelled weeks
(stance_weeks_2026-10-01.json, Nov 2025 -> Sep 2026) his LONG weeks vs SHORT/EMPTY weeks: QQQ > SMA50 91% vs 47%,
QQQ EMA9 > EMA21 86% vs 40%, net new 20-day highs - lows (5-day mean) +70 vs -17; the share of names above their
50-day barely differs (59% vs 53%). Earlier tests gated single LONG ENTRIES on index trend and found nothing (Q index
10/20 filter t -1.68; QQQ gate in the tight-stop test t 0.95). Not tested: switching the WHOLE BOOK -- closing every
open position when the tape turns and buying nothing until it turns back, as he does ("closed the entire long book
proactively", 2026-07-22).

REGIME (frozen from that comparison; evaluated at each session's close, acted on at that close):
  ON  = QQQ close > QQQ SMA50  AND  QQQ EMA9 > QQQ EMA21  AND  the 5-session mean of (names at a 20-day closing high
        minus names at a 20-day closing low) > 0, over the eligible universe (ADDV50 >= $50M, price >= $5).
  OFF = anything else.
  ⚠ The three conditions were picked by looking at 2025-11 -> 2026-09, so the PRIMARY window ends before it:
    2010-01-04 -> 2025-10-31. 2025-11 -> 2026-09 is reported separately as the in-sample window.

BOOKS
  1. HOUSE BREAKOUT, the sizing simulation's R030 arm (run_breakout_sizing_sim.py: 0.3% risk per trade, 30%
     position cap, 200% gross, daily mark-to-market, 10 bp/side, 6% margin), 2,226 house breakouts:
     BASE        as simulated.
     ENTRY_GATE  new entries only on ON days; open positions run their own rule.
     FLAT_GATE   on the first OFF close, sell every open position at that close (10 bp); no entries while OFF.
  2. 12-1 MOMENTUM SLEEVE, top decile (momentum_monthly_2026-10-02.csv, survivorship-free, 2011-02 -> 2026-01):
     BASE        top_decile monthly return.
     GATED       a month's return is 0 (cash) when the regime is OFF at the last close of the prior month.

PRIMARY (two, each judged alone; Šidák(2) is 2.24, the house 3 governs): monthly log-return difference GATED minus
  BASE (breakout: FLAT_GATE - BASE; momentum: GATED - BASE) over the primary window, Newey-West t (3 lags).
  PASS: t >= 3 and both halves (split 2018-01-01) > 0. Negative t <= -3 with both halves < 0 -> INVERTED.
  Otherwise NULL / UNDERPOWERED.
REPORTED, not a pass: CAGR, max drawdown and worst month for every arm; share of days ON; the in-sample window
  (2025-11 -> 2026-09); per year; ENTRY_GATE - BASE; a SHORT_QQQ variant of FLAT_GATE that holds -50% notional QQQ
  while OFF (his "short side" in index form, since his single-name shorts are not codable).
PRIOR ~25%: trend gates usually cut drawdown and give back return; the earlier entry-gate nulls point the same way.
  A drawdown-only improvement is reported as such (REFRAME), not as a pass.

  PYTHONPATH=src:. .venv/bin/python3 run_luk_regime_book_switch.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import run_breakout_sizing_sim as S

OUT = "data/studies/luk_regime_book_switch_2026-10-03"
P0, P1 = pd.Timestamp("2010-01-04"), pd.Timestamp("2025-10-31")
SPLIT = pd.Timestamp("2018-01-01")
R030 = dict(kind="risk", r=0.003, pos_cap=0.30, gross=2.0)


def regime() -> pd.Series:
    raw = pd.read_parquet(S.PANEL, columns=["date", "ticker", "close", "dolvol"])
    C = raw.pivot(index="date", columns="ticker", values="close").sort_index(); C.index = pd.to_datetime(C.index)
    D = raw.pivot(index="date", columns="ticker", values="dolvol").reindex_like(C)
    q = C["QQQ"] if "QQQ" in C.columns else C["SPY"]
    elig = (D.rolling(50, min_periods=30).mean() >= 50e6) & (C >= 5)
    nh = ((C >= C.rolling(20).max()) & elig).sum(1) - ((C <= C.rolling(20).min()) & elig).sum(1)
    on = (q > q.rolling(50).mean()) & (q.ewm(span=9, adjust=False).mean() > q.ewm(span=21, adjust=False).mean()) & (nh.rolling(5).mean() > 0)
    return on.astype(bool), q


def simulate(T, C, a, on, mode, q=None):
    days = C.index[(C.index >= T.entry.min()) & (C.index <= T.exit.max())]
    by_entry = {d: g for d, g in T.groupby("entry")}
    eq, open_, curve = 1.0, [], []
    short_n, short_px = 0.0, None
    for d in days:
        pnl = 0.0; still = []
        for p in open_:
            if d >= p["exit"]:
                pnl += p["notional0"] * (1 + p["ret"]) - p["mark"]
            else:
                px = C.at[d, p["sym"]] if p["sym"] in C.columns else np.nan
                val = p["notional0"] * px / p["px0"] if np.isfinite(px) and p["px0"] > 0 else p["mark"]
                pnl += val - p["mark"]; p["mark"] = val; still.append(p)
        if short_n and short_px:
            qp = q.get(d, np.nan)
            if np.isfinite(qp):
                pnl += short_n * (short_px - qp) / short_px   # fixed notional, re-marked daily
                short_px = qp
        gross = sum(p["mark"] for p in still)
        eq += pnl - max(0.0, gross - eq) * S.MARGIN / 252
        open_ = still
        is_on = bool(on.get(d, True))
        if mode in ("flat", "flat_short") and not is_on and open_:
            eq -= sum(p["mark"] for p in open_) * S.COST          # sell everything at this close
            open_ = []
        if mode == "flat_short":
            if not is_on and not short_n:
                short_n, short_px = 0.5 * eq, q.get(d, np.nan); eq -= short_n * S.COST
            elif is_on and short_n:
                eq -= short_n * S.COST; short_n, short_px = 0.0, None
        allow = is_on or mode == "base"
        for r in (by_entry[d].itertuples() if d in by_entry else []):
            if not allow:
                continue
            n = min(a["r"] / r.stop, a["pos_cap"]) * eq
            if sum(p["mark"] for p in open_) + n > a["gross"] * eq + 1e-9:
                continue
            px0 = C.at[d, r.sym] if r.sym in C.columns else np.nan
            open_.append(dict(sym=r.sym, notional0=n, px0=px0 if np.isfinite(px0) else np.nan, exit=r.exit, ret=r.ret, mark=n))
        curve.append(eq)
        if eq <= 0:
            break
    return pd.Series(curve, index=days[:len(curve)])


def nw_t(x: np.ndarray, lags=3) -> float:
    x = x[np.isfinite(x)]; n = len(x); mu = x.mean(); e = x - mu
    v = (e @ e) / n
    for l in range(1, lags + 1):
        v += 2 * (1 - l / (lags + 1)) * (e[l:] @ e[:-l]) / n
    return mu / np.sqrt(v / n)


def judge(diff: pd.Series) -> tuple[str, float, float, float, float]:
    d = diff[(diff.index >= P0) & (diff.index <= P1)]
    t = nw_t(d.values); h1, h2 = d[d.index < SPLIT].mean(), d[d.index >= SPLIT].mean()
    v = "PASS" if t >= 3 and h1 > 0 and h2 > 0 else "INVERTED" if t <= -3 and h1 < 0 and h2 < 0 else ("NULL" if abs(t) < 2 else "UNDERPOWERED")
    return v, d.mean() * 100, t, h1 * 100, h2 * 100


def stats(m: pd.Series, lab: str) -> str:
    w = np.exp(np.log1p(m).cumsum()); yrs = len(m) / 12
    return f"| {lab} | {w.iloc[-1] ** (1 / yrs) - 1:+.1%} | {(w / w.cummax() - 1).min():.0%} | {m.min():+.1%} |"


def main() -> None:
    on, q = regime()
    T, C = S.load()
    L = [f"# Luk-style whole-book timing ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
         f"Regime ON share of sessions, primary window: {on[(on.index >= P0) & (on.index <= P1)].mean():.0%}.", "",
         "## 1. House breakout book (R030)", ""]
    M = {}
    for name, mode in (("BASE", "base"), ("ENTRY_GATE", "entry"), ("FLAT_GATE", "flat"), ("SHORT_QQQ", "flat_short")):
        E = S.simulate(T, C, R030)[0] if mode == "base" else simulate(T, C, R030, on, mode, q)
        M[name] = E.resample("ME").last().pct_change().dropna()
    v, mu, t, h1, h2 = judge(np.log1p(M["FLAT_GATE"]) - np.log1p(M["BASE"]))
    L += [f"**PRIMARY FLAT_GATE − BASE: {v}** — {mu:+.2f}pp/month (log), NW t {t:.2f}, halves {h1:+.2f} / {h2:+.2f}", "",
          "| arm, primary window | CAGR | max DD | worst month |", "|---|---|---|---|"]
    for k, m in M.items():
        L.append(stats(m[(m.index >= P0) & (m.index <= P1)], k))
    v2 = judge(np.log1p(M["ENTRY_GATE"]) - np.log1p(M["BASE"]))
    L += ["", f"- ENTRY_GATE − BASE: {v2[1]:+.2f}pp/month, t {v2[2]:.2f}", "", "In-sample window 2025-11 → 2026-09:", "",
          "| arm | CAGR | max DD | worst month |", "|---|---|---|---|"]
    for k, m in M.items():
        L.append(stats(m[m.index >= "2025-11-01"], k))
    # momentum
    mo = pd.read_csv("data/studies/momentum_monthly_2026-10-02.csv")
    mo.index = pd.to_datetime(mo.month) + pd.offsets.MonthEnd(0)
    prev_on = on.resample("ME").last().shift(1).reindex(mo.index).fillna(True).astype(bool)
    base = mo.top_decile; gated = base.where(prev_on, 0.0)
    v3, mu3, t3, a3, b3 = judge(np.log1p(gated) - np.log1p(base))
    L += ["", "## 2. 12-1 momentum sleeve (top decile)", "",
          f"**PRIMARY GATED − BASE: {v3}** — {mu3:+.2f}pp/month (log), NW t {t3:.2f}, halves {a3:+.2f} / {b3:+.2f}; "
          f"months in cash {(~prev_on[(prev_on.index >= P0) & (prev_on.index <= P1)]).mean():.0%}", "",
          "| arm, primary window | CAGR | max DD | worst month |", "|---|---|---|---|",
          stats(base[(base.index >= P0) & (base.index <= P1)], "BASE"), stats(gated[(gated.index >= P0) & (gated.index <= P1)], "GATED"),
          "", "Per year, breakout FLAT_GATE − BASE and momentum GATED − BASE (sum of monthly log diffs, pp):", ""]
    yb = ((np.log1p(M["FLAT_GATE"]) - np.log1p(M["BASE"])).groupby(lambda d: d.year).sum() * 100).round(1)
    ym = ((np.log1p(gated) - np.log1p(base)).groupby(lambda d: d.year).sum() * 100).round(1)
    L.append(pd.DataFrame({"breakout": yb, "momentum": ym}).to_string())
    open(f"{OUT}_results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
