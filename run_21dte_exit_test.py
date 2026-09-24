#!/usr/bin/env python3
"""
Does the 21-DTE exit beat holding to expiry on a short strangle? (pre-registered 2026-09-23)

THE CLAIM. Sosnoff (OptionsPlay interview 2024-10-14, reviewed 3/5): sell a ~45 DTE / ~20-delta strangle
in liquid high-IV-rank names and **manage it at 21 DTE** -- roll or close, regardless of P&L. He introduces
it as "basically a theoretical discussion"; no sample, distribution or statistic is offered anywhere.

WHY IT IS WORTH TESTING AT ALL, when our exit ledger is a graveyard. Every exit rule we have killed removes
LOSERS -- breakeven stops, profit locks, trims, "extended -> tighten", the 10-EMA trail, all negative. This
one removes **gamma symmetrically at a fixed date**, independent of whether the trade is up or down. That
is a different object, and "don't manage" may not generalise to it. It is also the one rule the audited
TSLA trade vindicated: it rolled out clean on 2024-10-25 at 269.19, two weeks before that position printed
a 358.64 high and closed EXACTLY on the 350 short strike with 4 DTE.

⛔ WHY THIS WAS BLOCKED UNTIL NOW. A fixed-date exit is a PATH question, and path questions in short
premium are how this book got burned: run_iv_condor_study.py reported 94-99% win / 86-100% ROC at 14.3%
median mark coverage, because days without marks silently skipped the trigger and fell through to a
win-biased expiry settlement. Running this test before the guard existed would have manufactured a
confirmation of the claim under test. `lib.studies.path_coverage` now exists; this study uses it.

⚠ THE TRAP SPECIFIC TO THIS DATA, and it points the same way. `options_cache` is a synced subset of
options_daily_v3 whose filter drops every zero-bid row EXCEPT on expiry day (measured 2026-09-22: SPY has
0 zero-bid rows at DTE>0 out of 7.49M, but 44.6% of expiry-day rows are zero-bid). A short strangle's legs
decay toward a zero bid precisely when the trade is WINNING -- so the missing 21-DTE marks are concentrated
in winners. Defaulting them to the expiry outcome over-counts wins (the condor bug); dropping them
under-counts wins. Both are biased. **This reports BOTH conventions and lets the guard's sensitivity table
show whether the answer depends on the choice.** If it does, there is no answer here.

DESIGN
  Universe: every ticker in options_cache with enough history (liquid ETFs + mega caps).
  Entry:    each Friday, the expiry nearest 45 DTE; sell the ~20-delta put and the ~20-delta call.
  Fills:    REAL -- sell the bid on entry, buy back the ask on exit, house commissions. No mid.
  ARM A:    hold to expiry, settled at intrinsic against the expiry-day mark.
  ARM B:    close the whole strangle at the first session with DTE <= 21, at the ask.
  Paired:   A and B are the SAME trades, so the comparison is within-trade and the market is held fixed.

PRE-REGISTERED PASS: ARM B minus ARM A, on the trades where BOTH arms resolve honestly, positive with
month-clustered t >= 3 and both halves of the sample the same sign (split 2022-07). Anything else = the
21-DTE rule does not beat holding, on this data.

PRIOR: no edge. Our exit ledger is 0-for-many and the mark gap flatters whichever arm keeps the winners.
The most likely true outcome is that B reduces variance (it removes the gamma tail) without improving the
mean -- which is a RISK claim, not a return claim, and would be worth saying plainly.

Usage: MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 -u run_21dte_exit_test.py
"""
from __future__ import annotations

import warnings
from datetime import date
from math import sqrt

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)

from lib.mysql_lib import fetch_options_cache
from lib.studies.path_coverage import report as coverage_report

COMM = 0.0065
DTE_TARGET, DTE_TOL = 45, 5
EXIT_DTE = 21
DELTA, DELTA_TOL = 0.20, 0.07
SPLIT = pd.Timestamp("2022-07-01")
START, END = date(2018, 1, 1), date(2026, 2, 20)


def pick(g: pd.DataFrame, target: float) -> pd.Series | None:
    if g.empty:
        return None
    r = g.iloc[(g["delta"].abs() - target).abs().argsort()[:1]].iloc[0]
    return r if abs(abs(r["delta"]) - target) <= DELTA_TOL else None


def build(ticker: str) -> pd.DataFrame:
    df = fetch_options_cache(ticker, START, END)
    if df.empty:
        return pd.DataFrame()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["expiry"] = pd.to_datetime(df["expiry"])
    # ⚠ FIXED 2026-09-23: expiry-day rows must survive the zero-bid filter. A leg that expires worthless has
    # bid 0; filtering it out made every both-legs-worthless strangle (the best outcome) disappear from ARM A.
    # Found by the tastylive review; SPY hold-to-expiry flipped from -$1.77 to about +$1.13/share when restored.
    df = df[((df["bid"] > 0) & (df["ask"] > 0)) | (df["trade_date"] == df["expiry"])]
    rows = []
    by_day = dict(tuple(df.groupby("trade_date")))            # index once: the per-Friday rescans were O(Fridays x rows)
    by_exp = dict(tuple(df.groupby("expiry")))
    fridays = sorted(d for d in by_day if pd.Timestamp(d).weekday() == 4)
    for d in fridays:
        day = by_day[d]
        cand = day[(day["dte"] >= DTE_TARGET - DTE_TOL) & (day["dte"] <= DTE_TARGET + DTE_TOL)]
        if cand.empty:
            continue
        exp = cand.iloc[(cand["dte"] - DTE_TARGET).abs().argsort()[:1]]["expiry"].iloc[0]
        chain = day[day["expiry"] == exp]
        sp = pick(chain[chain["cp"] == "P"], DELTA)
        sc = pick(chain[chain["cp"] == "C"], DELTA)
        if sp is None or sc is None:
            continue
        credit = (sp["bid"] + sc["bid"]) - 2 * COMM          # sell the BID
        if credit <= 0:
            continue

        life = by_exp[exp]; life = life[life["trade_date"] > d]
        legs = life[((life["cp"] == "P") & (life["strike"] == sp["strike"]))
                    | ((life["cp"] == "C") & (life["strike"] == sc["strike"]))]
        both = legs.groupby("trade_date")["cp"].nunique()
        full = set(both[both == 2].index)                     # sessions where BOTH legs are quoted
        horizon = legs["trade_date"].nunique() or 1

        # ARM B: first session at or inside 21 DTE with both legs quoted
        # ⚠ FIXED 2026-09-24: expiry-day rows now always survive the filter, so without "t < exp" a trade with no
        # both-legs-quoted session inside 21 DTE fell through to an "exit" at the expiry-day ASK (1,311 of 14,367
        # trades). Those are UNRESOLVED per the pre-registration, not 21-DTE exits.
        exitable = sorted(t for t in full if (exp - t).days <= EXIT_DTE and t < exp)
        b_cost, b_date = np.nan, pd.NaT
        if exitable:
            t0 = exitable[0]
            leg = legs[legs["trade_date"] == t0]
            b_cost = float(leg["ask"].sum()) + 2 * COMM       # buy back at the ASK
            b_date = t0

        # ARM A: settle at expiry intrinsic (expiry-day rows are exempt from the zero-bid filter)
        fin = legs[legs["trade_date"] == exp]
        if fin.empty:
            continue
        if fin["cp"].nunique() < 2:                              # a leg with no expiry row at all: cannot settle
            continue
        px = fin["last"].fillna(fin["mid"]).clip(lower=0)
        a_cost = float(px.where(fin["bid"] > 0, 0.0).sum())        # zero bid at expiry = worthless = 0

        rows.append(dict(
            sym=ticker, entry=pd.Timestamp(d), expiry=exp, credit=credit,
            a_pnl=credit - a_cost,
            b_pnl=(credit - b_cost) if np.isfinite(b_cost) else np.nan,
            b_date=b_date, b_resolved=bool(np.isfinite(b_cost)),
            mark_cov=len(full) / horizon,
        ))
    return pd.DataFrame(rows)


def mt(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / (x.std(ddof=1) / sqrt(len(x)))) if len(x) > 2 else np.nan


def main() -> None:
    import lib.mysql_lib as ml
    conn = ml._get_conn(); cur = conn.cursor()
    cur.execute("SELECT ticker FROM options_cache GROUP BY ticker HAVING COUNT(*) > 200000")
    tickers = [r[0] for r in cur.fetchall()]
    print(f"{len(tickers)} tickers with deep chains: {', '.join(sorted(tickers)[:14])}...\n")

    T = pd.concat([build(t) for t in tickers], ignore_index=True)
    T["month"] = T.entry.dt.to_period("M")
    T["roc_a"] = T.a_pnl / T.credit
    T["roc_b"] = T.b_pnl / T.credit
    print(f"{len(T):,} strangles · {T.sym.nunique()} names · {T.entry.dt.year.nunique()} years\n")

    coverage_report(T, cov_col="mark_cov", pnl_col="a_pnl", floor=0.60,
                    label="45 DTE short strangle, 21-DTE exit test")

    print(f"\nARM B resolved honestly on {T.b_resolved.mean():.1%} of trades "
          f"({int((~T.b_resolved).sum()):,} had no session with BOTH legs quoted inside {EXIT_DTE} DTE)")
    print("⚠ unresolved B trades are concentrated in WINNERS (legs decay to a zero bid, which the cache drops)")

    paired = T[T.b_resolved].copy()
    d = paired.b_pnl - paired.a_pnl
    md = d.groupby(paired["month"]).mean()
    h1, h2 = md[md.index < SPLIT.to_period("M")], md[md.index >= SPLIT.to_period("M")]
    print("\n" + "=" * 96)
    print("PRIMARY — ARM B (exit at 21 DTE) minus ARM A (hold to expiry), same trades, paired")
    print("=" * 96)
    print(f"  n {len(paired):,}   mean diff ${d.mean():+.2f}/strangle   month-clustered t {mt(md):+.2f}   "
          f"halves {h1.mean():+.2f} / {h2.mean():+.2f}")
    print(f"  ARM A  mean ${paired.a_pnl.mean():+.2f}  ROC {100*paired.roc_a.mean():+.1f}%  "
          f"win {100*(paired.a_pnl > 0).mean():.1f}%  sd ${paired.a_pnl.std():.2f}  worst ${paired.a_pnl.min():,.0f}")
    print(f"  ARM B  mean ${paired.b_pnl.mean():+.2f}  ROC {100*paired.roc_b.mean():+.1f}%  "
          f"win {100*(paired.b_pnl > 0).mean():.1f}%  sd ${paired.b_pnl.std():.2f}  worst ${paired.b_pnl.min():,.0f}")
    passed = bool(d.mean() > 0 and abs(mt(md)) >= 3 and np.sign(h1.mean()) == np.sign(h2.mean()))
    print(f"\n  PRE-REGISTERED PASS: {'YES' if passed else 'NO'}")

    print("\n  ⚠ convention sensitivity — does the answer depend on how unresolved B trades are treated?")
    alt = T.copy(); alt["b_alt"] = alt.b_pnl.fillna(alt.a_pnl)   # the condor bug's convention
    da = (alt.b_alt - alt.a_pnl)
    print(f"     drop unresolved (used above): {d.mean():+.2f}   |   default them to the expiry outcome: {da.mean():+.2f}")
    print(f"     tail: ARM A worst 1% ${paired.a_pnl.quantile(0.01):,.0f} vs ARM B worst 1% ${paired.b_pnl.quantile(0.01):,.0f}")
    T.to_csv("data/studies/exit_21dte_2026-09-23_fixed.csv", index=False)
    print("\nwrote data/studies/exit_21dte_2026-09-23_fixed.csv")


if __name__ == "__main__":
    main()
