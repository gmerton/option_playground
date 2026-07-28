"""
Double-Calendar head-to-head: Theta-Profits skeleton (Bernich "DC Time Machine" /
Ravish "range tent") vs the user's existing SPY double-calendar.

What's testable on EOD data, and what is NOT
--------------------------------------------
Bernich's distinguishing move — the intraday TRANSFORM of a winning double calendar into
an all-front-month credit iron condor — is an *intraday* action triggered by a 1-minute
IV-ratio tool ("Flux"). It CANNOT be replayed on daily (EOD) data. What IS testable is the
*skeleton* both Theta-Profits traders share, which differs from the user's SPY dcal only in
parameters the engine already exposes:

  axis            user SPY dcal          Theta-Profits skeleton
  --------------  ---------------------  ------------------------------------
  gap (S->L)      +7 days (Fri/Fri)      +3 days (Fri-short / Mon-long)   [Bernich/Ravish]
  short strikes   0.25Δ (BuLO) /         Bernich ~0.35-0.40Δ (closer in)
                  0.25P+0.10C (BHI)      Ravish ~expected-move (wider)
  profit target   50% (BuLO) / hold(BHI) Ravish 15-30% of debit; out before expiry
  entry day       Friday                 Tue/Wed (NOT replicated — see caveat)

We hold entry day = Friday for ALL configs so the only thing varying is structure
(gap / delta / PT). That isolates the parameter effect and keeps the user's own dcal
faithful (it is Friday-entry). Ravish's "exit 2-3 days before short expiry" is approximated
by the engine's hold-to-short-expiry (short legs settle at intrinsic there) + the early
profit-take scan.

Cost model (the decisive part)
------------------------------
The engine prices legs at MID. A double calendar is 4 legs at entry + 4 at exit across two
expiries; both Ravish and Bernich flag fills as the soft spot, and the TP edge is a thin
15-30% target. So we report ROC at mid AND after a realistic cost haircut:

  cost/share = commission_legs + slippage_frac * (sum of the 4 entry leg bid-ask spreads) * 2
               (x2 = pay the haircut on entry AND exit; spreads proxied by entry quotes)
  roc_net    = (net_pnl_mid - cost) / net_debit

Run:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 \
      data/theta_profits/backtests/dc_time_machine/run_backtest.py
"""
from __future__ import annotations

import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from lib.studies.double_calendar_study import (
    build_double_calendar_trades,
    find_double_calendar_exits,
    compute_double_calendar_metrics,
)

CACHE = "data/cache/SPY_options.parquet"
COMMISSION_PER_LEG = 0.0065   # $0.65/contract = $0.0065/share
SLIPPAGE_FRAC      = 0.25     # pay 1/4 of the quoted spread per leg, per side

SHORT_DTE, SHORT_TOL = 12, 3
GAP_TOL = 2


def add_costs(m: pd.DataFrame, slip: float = SLIPPAGE_FRAC) -> pd.DataFrame:
    m = m.copy()
    spreads = (
        (m["sp_ask"] - m["sp_bid"]).clip(lower=0)
        + (m["sc_ask"] - m["sc_bid"]).clip(lower=0)
        + (m["lp_ask"] - m["lp_bid"]).clip(lower=0)
        + (m["lc_ask"] - m["lc_bid"]).clip(lower=0)
    )
    commission = COMMISSION_PER_LEG * 8          # 4 legs in + 4 legs out
    m["cost"]    = commission + slip * spreads * 2
    m["net_pnl_net"] = m["net_pnl"] - m["cost"]
    m["roc_net"]     = m["net_pnl_net"] / m["net_debit"].clip(lower=0.001)
    m["is_win_net"]  = m["net_pnl_net"] > 0
    return m


def run_config(df, label, *, gap, pt, put_d, call_d):
    trades = build_double_calendar_trades(
        df, delta_target=put_d,
        put_delta_target=put_d, call_delta_target=call_d,
        short_dte_target=SHORT_DTE, short_dte_tol=SHORT_TOL,
        gap_days=gap, gap_tol=GAP_TOL,
        max_delta_err=0.10, max_spread_pct=0.25,
    )
    if trades.empty:
        return None, None
    exits   = find_double_calendar_exits(trades, df, profit_target_roc=pt)
    metrics = compute_double_calendar_metrics(exits)
    metrics = metrics[~metrics["is_open"]]
    if metrics.empty:
        return None, None
    metrics = add_costs(metrics)

    early = (metrics["exit_type"] == "profit_take").mean() if "exit_type" in metrics else 0.0

    def summarize(m):
        # capital-weighted ROC = sum(pnl)/sum(debit) — robust to tiny-debit outliers
        cw_mid = m["net_pnl"].sum()     / m["net_debit"].sum()
        cw_net = m["net_pnl_net"].sum() / m["net_debit"].sum()
        return {
            "n":        len(m),
            "win_net":  round(m["is_win_net"].mean() * 100, 1),
            "rocCW_mid":round(cw_mid * 100, 2),
            "rocCW_net":round(cw_net * 100, 2),
            "med_net":  round(m["roc_net"].median() * 100, 2),
            "sumPnL_net": round(m["net_pnl_net"].sum(), 2),
            "debit":    round(m["net_debit"].mean(), 2),
        }

    row = {"config": label, "gap": gap, "putD": put_d, "callD": call_d,
           "pt": "hold" if pt is None else f"{int(pt*100)}%",
           **summarize(metrics), "hold": round(metrics["days_held"].mean(), 1),
           "early%": round(early * 100, 0)}

    # 2022+ subset (Fri/Mon tight-gap expiries only really exist post-2022)
    m22 = metrics[pd.to_datetime(metrics["entry_date"]).dt.year >= 2022]
    row22 = {"config": label, **summarize(m22)} if len(m22) else None
    return row, metrics, row22


def main():
    print(f"Loading {CACHE} ...")
    df = pd.read_parquet(CACHE)
    print(f"  {len(df):,} rows  ({df['trade_date'].min()} -> {df['trade_date'].max()})")
    print(f"\nCost model: ${COMMISSION_PER_LEG*8:.3f}/share commission (8 legs) "
          f"+ {int(SLIPPAGE_FRAC*100)}% of bid-ask per leg per side\n")

    configs = [
        # ---- user's SPY dcal baselines (gap +7) ----
        ("USER BuLO (0.25/0.25, 50%PT)",      dict(gap=7, pt=0.50, put_d=0.25, call_d=0.25)),
        ("USER BHI  (0.25P/0.10C, hold)",     dict(gap=7, pt=None, put_d=0.25, call_d=0.10)),
        ("USER sym  (0.25/0.25, hold)",       dict(gap=7, pt=None, put_d=0.25, call_d=0.25)),
        # ---- Theta-Profits skeleton: tight gap +3 (Fri/Mon), Ravish 15-30% PT ----
        ("TP-Ravish (0.25/0.25, g3, 25%PT)",  dict(gap=3, pt=0.25, put_d=0.25, call_d=0.25)),
        ("TP-Ravish (0.25/0.25, g3, 20%PT)",  dict(gap=3, pt=0.20, put_d=0.25, call_d=0.25)),
        # ---- Theta-Profits skeleton: Bernich tighter strikes 0.35-0.40Δ ----
        ("TP-Bernich(0.35/0.35, g3, 25%PT)",  dict(gap=3, pt=0.25, put_d=0.35, call_d=0.35)),
        ("TP-Bernich(0.40/0.40, g3, hold)",   dict(gap=3, pt=None, put_d=0.40, call_d=0.40)),
        ("TP-Bernich(0.35/0.35, g3, hold)",   dict(gap=3, pt=None, put_d=0.35, call_d=0.35)),
        # ---- controls: TP strikes/PT but USER's gap +7, to isolate the gap effect ----
        ("CTRL tight-strike g7 (0.35, 25%PT)",dict(gap=7, pt=0.25, put_d=0.35, call_d=0.35)),
        ("CTRL low-PT g7 (0.25/0.25, 25%PT)", dict(gap=7, pt=0.25, put_d=0.25, call_d=0.25)),
    ]

    rows, rows22, detail = [], [], {}
    for label, kw in configs:
        row, m, row22 = run_config(df, label, **kw)
        if row is None:
            print(f"  [skip] {label}: no trades")
            continue
        rows.append(row)
        if row22:
            rows22.append(row22)
        detail[label] = m

    out = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    print("=" * 150)
    print("HEAD-TO-HEAD — FULL SAMPLE 2018-2026  (rocCW = capital-weighted sum(pnl)/sum(debit);")
    print("  _mid = mid fills, _net = after costs; med_net = median per-trade ROC after costs)")
    print("=" * 150)
    print(out.to_string(index=False))

    print("\n" + "=" * 150)
    print("HEAD-TO-HEAD — 2022+ ONLY  (clean window: Fri/Mon tight-gap expiries exist; removes pre-2022 EOM-matching artifact)")
    print("=" * 150)
    print(pd.DataFrame(rows22).to_string(index=False))

    # Year-by-year for the two protagonists: user BuLO vs the best TP challenger
    print("\n" + "=" * 80)
    print("YEAR-BY-YEAR  (avg ROC % of debit, AFTER costs)")
    print("=" * 80)
    for label in ["USER BuLO (0.25/0.25, 50%PT)",
                  "TP-Ravish (0.25/0.25, g3, 25%PT)",
                  "TP-Bernich(0.35/0.35, g3, hold)"]:
        m = detail.get(label)
        if m is None:
            continue
        m = m.copy()
        m["year"] = pd.to_datetime(m["entry_date"]).dt.year
        print(f"\n{label}")
        print(f"{'year':>6} {'n':>4} {'win%':>6} {'rocNet%':>8} {'sumPnLnet':>10}")
        for yr, g in m.groupby("year"):
            print(f"{yr:>6} {len(g):>4} {g['is_win_net'].mean()*100:>5.0f}% "
                  f"{g['roc_net'].mean()*100:>7.1f}% {g['net_pnl_net'].sum():>10.2f}")

    out.to_csv("data/theta_profits/backtests/dc_time_machine/results.csv", index=False)
    print("\nWrote results.csv")


if __name__ == "__main__":
    main()
