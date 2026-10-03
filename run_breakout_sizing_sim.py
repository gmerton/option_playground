#!/usr/bin/env python3
"""
HOUSE BREAKOUT: WHAT DOES SIZING DO? (pre-registered 2026-10-03, before the run)

WHY. Gabe 2026-10-03: focus on sizing, selection and entry. The triple-digit traders (Luk, Ariel, Qullamaggie) run
20-30% positions on 1-2.5% stops (Luk: 0.3% account risk, up to ~200% long); the house book has only ever been
simulated at a flat 10% notional (adaptive_trader_2026-09-27.md: +5.1% CAGR, 54% max DD, 2009-26). The edge is
regime-dependent: the same rule lost ~-1.2%/trade in 2010-19 and made ~+1.3% in 2019-26 (self-regime holdout, §4).
Sizing cannot create edge -- it multiplies whatever is there, losing decade included. This is a DESCRIPTIVE
simulation with no pass bar; its job is to show what the existing edge supports at their sizing, and how wide the
luck band is.

TRADES. data/studies/logs/self_regime_trades.csv: the 2,226 house breakouts 2009-06 -> 2026-09 (precision-tier rule
on liquid_panel_2009 -- 2026 SURVIVORS, which flatters every arm equally), close entry, day-low stop judged on the
close, 20-EMA exit. stop% = pct / R at entry. Costs: 10 bp per side on top of the file's return.

MARK-TO-MARKET. Every open position is marked at each session's close from liquid_panel_2009 (adjusted), so drawdowns
are real, not realised-only. A position's value on its exit date is its realised return (so the per-trade P&L matches
the file); days it lacks a panel close carry the last mark.

ARMS (all event-ordered; a signal is taken only if the caps allow, else SKIPPED and counted):
  FIX10        10% of equity per trade, gross cap 100%                      (reproduces the 10%-notional baseline)
  R025 / R050 / R100   risk 0.25 / 0.5 / 1.0% of equity: notional = risk / stop%, position cap 30%, gross cap 200%
  R050_G100    risk 0.5%, position cap 30%, gross cap 100% (no margin)
  Sizing uses equity at the prior close. Margin cost on gross > 100%: 6%/yr on the borrowed part.
  Stop floor 1% (a tighter stop is sized as 1%), so a near-zero stop cannot make a position explode.

REPORTED for each arm: CAGR and max drawdown for the full period, 2010-2018 and 2019-2026; worst month; share of
positive months; mean gross exposure; share of signals skipped by the caps; and a month-block bootstrap (2,000
resamples of calendar months with their trades' monthly P&L, re-compounded) giving the 5th / 50th / 95th percentile
CAGR and max DD for 2019-26 alone and for the full period. Plus full-Kelly and half-Kelly risk per trade from the
R distribution (f* = mean R / var R, per unit of risk), 2010-18 and 2019-26 separately.
The question it answers: at what risk per trade would the 2019-26 book have compounded >= 100%/yr, and what does that
same rule do in 2010-18 and in the bootstrap's bad tail.

  PYTHONPATH=src .venv/bin/python3 run_breakout_sizing_sim.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADES = "data/studies/logs/self_regime_trades.csv"
PANEL = "data/cache/liquid_panel_2009.parquet"
OUT = "data/studies/breakout_sizing_sim_2026-10-03"
COST = 0.0010
MARGIN = 0.06
STOP_FLOOR = 0.01
RNG = np.random.default_rng(20261003)
ARMS = {
    "FIX10": dict(kind="fix", f=0.10, pos_cap=0.10, gross=1.0),
    "R025": dict(kind="risk", r=0.0025, pos_cap=0.30, gross=2.0),
    "R050": dict(kind="risk", r=0.005, pos_cap=0.30, gross=2.0),
    "R100": dict(kind="risk", r=0.010, pos_cap=0.30, gross=2.0),
    "R050_G100": dict(kind="risk", r=0.005, pos_cap=0.30, gross=1.0),
}


def load():
    T = pd.read_csv(TRADES, parse_dates=["entry", "exit"]).sort_values(["entry", "sym"]).reset_index(drop=True)
    T["ret"] = T.pct / 100 - 2 * COST
    T["stop"] = (T.pct.abs() / T.R.abs()).where(T.R.abs() > 1e-9) / 100
    T["stop"] = T["stop"].fillna(T["stop"].median()).clip(lower=STOP_FLOOR)
    P = pd.read_parquet(PANEL, columns=["date", "ticker", "close"])
    C = P.pivot(index="date", columns="ticker", values="close").sort_index()
    C.index = pd.to_datetime(C.index)
    return T, C


def simulate(T: pd.DataFrame, C: pd.DataFrame, a: dict) -> tuple[pd.Series, pd.DataFrame, float]:
    days = C.index[(C.index >= T.entry.min()) & (C.index <= T.exit.max())]
    by_entry = {d: g for d, g in T.groupby("entry")}
    eq = 1.0; open_ = []            # dicts: sym, notional0, px0, exit, ret, last_mark
    curve, gross_hist, skipped, taken = [], [], 0, 0
    prev_mark_total = 0.0
    for d in days:
        # mark open positions; close those exiting today at their realised return
        still, pnl_today = [], 0.0
        for p in open_:
            if d >= p["exit"]:
                val = p["notional0"] * (1 + p["ret"])
                pnl_today += val - p["mark"]
                eq_add = val
                p["closed_val"] = eq_add
            else:
                px = C.at[d, p["sym"]] if p["sym"] in C.columns else np.nan
                val = p["notional0"] * px / p["px0"] if np.isfinite(px) and p["px0"] > 0 else p["mark"]
                pnl_today += val - p["mark"]
                p["mark"] = val
                still.append(p)
        gross_val = sum(p["mark"] for p in still)
        borrowed = max(0.0, gross_val - eq)
        eq += pnl_today - borrowed * MARGIN / 252
        open_ = still
        # new entries at today's close, sized off equity at that close
        for r in (by_entry.get(d, pd.DataFrame()).itertuples() if d in by_entry else []):
            if a["kind"] == "fix":
                n = a["f"] * eq
            else:
                n = min(a["r"] / r.stop, a["pos_cap"]) * eq
            if sum(p["mark"] for p in open_) + n > a["gross"] * eq + 1e-9:
                skipped += 1
                continue
            px0 = C.at[d, r.sym] if r.sym in C.columns else np.nan
            open_.append(dict(sym=r.sym, notional0=n, px0=px0 if np.isfinite(px0) else np.nan, exit=r.exit, ret=r.ret, mark=n))
            taken += 1
        curve.append(eq); gross_hist.append(sum(p["mark"] for p in open_) / eq if eq > 0 else np.nan)
        if eq <= 0:
            break
    E = pd.Series(curve, index=days[:len(curve)])
    G = pd.Series(gross_hist, index=E.index)
    return E, G, skipped / max(1, skipped + taken)


def cagr(E: pd.Series) -> float:
    if len(E) < 2 or E.iloc[0] <= 0:
        return np.nan
    yrs = (E.index[-1] - E.index[0]).days / 365.25
    return (max(E.iloc[-1], 1e-12) / E.iloc[0]) ** (1 / yrs) - 1


def mdd(E: pd.Series) -> float:
    return float((E / E.cummax() - 1).min())


def boot(E: pd.Series, n=2000) -> tuple:
    m = E.resample("ME").last().pct_change().dropna().values
    if len(m) < 12:
        return (np.nan,) * 6
    C, D = [], []
    for _ in range(n):
        x = RNG.choice(m, len(m), replace=True)
        w = np.cumprod(1 + x)
        C.append(w[-1] ** (12 / len(m)) - 1); D.append((w / np.maximum.accumulate(w) - 1).min())
    return tuple(np.percentile(C, [5, 50, 95])) + tuple(np.percentile(D, [5, 50, 95]))


def main() -> None:
    T, C = load()
    lines = [f"# House breakout sizing simulation ({pd.Timestamp.now():%Y-%m-%d %H:%M})", "",
             f"{len(T)} trades {T.entry.min().date()} -> {T.exit.max().date()}; median stop {T.stop.median():.1%}; "
             f"costs 10 bp/side; margin 6%/yr on gross > 100%.", ""]
    for era, sel in (("2010-18", (T.entry >= "2010-01-01") & (T.entry < "2019-01-01")), ("2019-26", T.entry >= "2019-01-01")):
        Rr = (T.ret[sel] / T.stop[sel])
        f = Rr.mean() / Rr.var()
        lines.append(f"Kelly {era}: mean R {Rr.mean():+.3f}, sd {Rr.std():.2f}, n {sel.sum()} -> full Kelly risk/trade {f:+.2%}, half {f / 2:+.2%}")
    lines += ["", "| arm | CAGR full | max DD full | CAGR 2010-18 | DD 2010-18 | CAGR 2019-26 | DD 2019-26 | worst month | months + | mean gross | skipped |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    bl = ["", "Bootstrap (month blocks): CAGR p5 / p50 / p95 · max DD p5 / p50 / p95", ""]
    for name, a in ARMS.items():
        E, G, sk = simulate(T, C, a)
        E.to_frame("equity").to_csv(f"{OUT}_{name}_equity.csv")
        e1, e2 = E[(E.index >= "2010-01-01") & (E.index < "2019-01-01")], E[E.index >= "2019-01-01"]
        mo = E.resample("ME").last().pct_change().dropna()
        lines.append(f"| {name} | {cagr(E):+.1%} | {mdd(E):.0%} | {cagr(e1):+.1%} | {mdd(e1):.0%} | {cagr(e2):+.1%} | {mdd(e2):.0%} | "
                     f"{mo.min():+.1%} | {(mo > 0).mean():.0%} | {G.mean():.0%} | {sk:.0%} |")
        b2, bf = boot(e2), boot(E)
        bl.append(f"- {name}: 2019-26 CAGR {b2[0]:+.0%} / {b2[1]:+.0%} / {b2[2]:+.0%} · DD {b2[3]:.0%} / {b2[4]:.0%} / {b2[5]:.0%}; "
                  f"full CAGR {bf[0]:+.0%} / {bf[1]:+.0%} / {bf[2]:+.0%} · DD {bf[3]:.0%} / {bf[4]:.0%} / {bf[5]:.0%}")
        print(lines[-1], flush=True)
    open(f"{OUT}_results.md", "w").write("\n".join(lines + bl) + "\n")
    print("\n".join(lines[:6] + bl))


if __name__ == "__main__":
    main()
