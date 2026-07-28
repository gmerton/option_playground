#!/usr/bin/env python3
"""
Portfolio simulation of the risk-architecture grid. Run run_arch_test.py first.

WHY THIS EXISTS
    Per-trade means are not comparable across holding periods. A 60-day hold commits capital
    30x longer than a 2-day hold, so "mean return per trade" flatters wide stops by
    construction. The only honest comparison is a capital-constrained portfolio: fixed
    equity, a finite number of concurrent slots, positions competing for the same money.

    A tight-stop architecture recycles capital fast and can take many more trades. That is
    precisely the argument for it, and Table A of run_arch_test.py cannot see it.

RULES
    - Chronological. Each signal is taken only if a slot is free at its entry date.
    - Position notional = min(30%, 0.3% / stop%) x current equity, compounding.
    - Total exposure capped at 100% of equity (no leverage).
    - Equity is marked only on realized exits (no intramonth marking) -> the reported max
      drawdown is on the REALIZED equity curve and therefore UNDERSTATES true drawdown,
      especially for the no-stop and wide-stop variants that carry open losers for months.
      That bias favors the wide-stop cells, which are the ones already winning. Noted, not fixed.

⚠ SURVIVORSHIP
    The universe is the 299 most liquid names as of TODAY. They all survived. The inflation
    this causes GROWS WITH HOLDING PERIOD — a 60-day hold in a guaranteed survivor is worth far
    more than a 2-day one. So the bias does NOT cancel between cells here; it points directly
    at "longer holds win." Any conclusion favoring wide stops / long holds must be discounted
    accordingly. The tight-stop findings (stop-out rates) are unaffected by it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

HERE = "data/carter_mastering_the_trade/backtests/risk_architecture"
SLOTS = 10          # max concurrent positions
MAX_GROSS = 1.00    # no leverage

STOP_ORDER = ["1.0%", "1.5%", "3.0%", "5.0%", "1.0ATR", "2.0ATR", "bar low", "10d low", "20d low", "20EMA"]
EXIT_ORDER = ["close<10EMA", "close<20EMA", "close<50EMA", "hold 20d", "target 2R", "target 4R"]


def simulate(g: pd.DataFrame) -> dict:
    """Event-driven portfolio sim over one architecture cell."""
    g = g.sort_values("entry_date")
    ent = g["entry_date"].to_numpy()
    ext = g["exit_date"].to_numpy()
    ret = g["ret"].to_numpy()
    pos = g["pos"].to_numpy()

    equity = 1.0
    open_pos = []          # (exit_date, notional_dollars, ret)
    curve = []             # (date, equity)
    taken = skipped = 0
    pos_days = []

    for i in range(len(g)):
        now = ent[i]
        # close everything that exited before this entry
        still = []
        for xd, notional, r in open_pos:
            if xd <= now:
                equity += notional * r
                curve.append((xd, equity))
            else:
                still.append((xd, notional, r))
        open_pos = still

        gross = sum(n for _, n, _ in open_pos)
        want = pos[i] * equity
        if len(open_pos) >= SLOTS or gross + want > MAX_GROSS * equity or equity <= 0:
            skipped += 1
            continue
        open_pos.append((ext[i], want, ret[i]))
        pos_days.append(pos[i] * g["hold"].iat[i])
        taken += 1

    for xd, notional, r in sorted(open_pos):
        equity += notional * r
        curve.append((xd, equity))

    if not curve or equity <= 0:
        return {}
    cv = pd.DataFrame(curve, columns=["date", "eq"]).groupby("date")["eq"].last()
    yrs = (cv.index[-1] - cv.index[0]) / np.timedelta64(365, "D")
    peak = cv.cummax()
    dd = (cv / peak - 1.0).min()
    # daily-resampled curve for a comparable volatility figure
    daily = cv.resample("D").ffill().dropna()
    dr = daily.pct_change().dropna()
    sharpe = (dr.mean() / dr.std() * np.sqrt(252)) if dr.std() > 0 else np.nan

    ndays = np.busday_count(ent[0].astype("datetime64[D]"), ext[-1].astype("datetime64[D]"))
    return {"taken": taken, "skipped": skipped, "avg_expo%": 100 * sum(pos_days) / max(1, ndays),
            "fill%": 100 * taken / max(1, taken + skipped),
            "final_x": equity, "CAGR%": 100 * (equity ** (1 / yrs) - 1),
            "maxDD%": 100 * dd, "Sharpe": sharpe,
            "MAR": (100 * (equity ** (1 / yrs) - 1)) / abs(100 * dd) if dd < 0 else np.nan}


def main() -> None:
    df = pd.read_parquet(f"{HERE}/arch_trades.parquet")
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])

    rows = []
    for (st, ex), g in df.groupby(["stop", "exit"], observed=True):
        r = simulate(g)
        if r:
            rows.append({"stop": st, "exit": ex, **r})
    res = pd.DataFrame(rows)

    print("=" * 118)
    print(f"PORTFOLIO SIM — {SLOTS} concurrent slots, 0.3% risk/trade, 30% position cap, "
          f"no leverage, compounding")
    print("=" * 118)

    for metric, label, nd in [("CAGR%", "CAGR %", 2), ("maxDD%", "max drawdown % (realized-only, understated)", 1),
                              ("MAR", "CAGR / |maxDD|", 2), ("Sharpe", "Sharpe (daily, realized curve)", 2),
                              ("taken", "trades actually taken (of 22,774 signals)", 0),
                              ("fill%", "% of signals that got a slot", 1)]:
        print(f"\n  {label}:")
        print(res.pivot(index="stop", columns="exit", values=metric)
              .reindex(STOP_ORDER)[EXIT_ORDER].round(nd).to_string())

    print("\n" + "=" * 118)
    print("RANKED BY CAGR")
    print("=" * 118)
    top = res.sort_values("CAGR%", ascending=False)
    print(top[["stop", "exit", "taken", "fill%", "CAGR%", "maxDD%", "MAR", "Sharpe", "final_x"]]
          .head(12).round(2).to_string(index=False))
    print("\n  worst 6:")
    print(top[["stop", "exit", "taken", "fill%", "CAGR%", "maxDD%", "MAR", "Sharpe", "final_x"]]
          .tail(6).round(2).to_string(index=False))

    # --- is the ranking driven by the tight-stop cells running out of signals, or by edge?
    print("\n" + "=" * 118)
    print("CAPITAL RECYCLING CHECK — do tight stops actually get to take more trades?")
    print("=" * 118)
    print(res.pivot(index="stop", columns="exit", values="taken")
          .reindex(STOP_ORDER)[EXIT_ORDER].astype(int).to_string())
    print("\n  If tight stops take MORE trades but still lose, the recycling argument is dead:")
    print("  the extra turnover does not compensate for the worse per-trade outcome.")

    res.to_csv(f"{HERE}/portfolio_results.csv", index=False)
    print(f"\nwrote {HERE}/portfolio_results.csv")


if __name__ == "__main__":
    main()
