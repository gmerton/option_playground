"""
Regime-gated confirmation: does borrowing the Theta-Profits *tighter strikes* (0.25Δ -> 0.35Δ)
on the user's EXISTING SPY double-calendar (+7 gap) survive inside the regimes the user actually
trades — Bearish_HighIV (hold) and Bullish_LowIV (50% PT) — or was it an ungated-sample artifact?

Regime (same as run_tlt_regime_switch.py / spy_double_calendar_playbook.md):
  direction = Bullish if SPY close > 50-day MA else Bearish
  iv_label  = HighIV  if VIX >= 20 else LowIV
Traded regimes only:  BHI (asym 0.25P/0.10C, hold)  ·  BuLO (sym 0.25/0.25, 50%PT)

Same cost model as run_backtest.py: $0.052/share commission (8 legs) + 25% of each leg's bid-ask,
entry and exit. Metric = capital-weighted ROC = sum(pnl)/sum(debit), after costs (outlier-robust).

Run:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 \
      data/theta_profits/backtests/dc_time_machine/run_gated_confirm.py
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

CACHE      = "data/cache/SPY_options.parquet"
STOCK      = "data/cache/SPY_stock.parquet"
VIX        = "data/cache/vix_daily.parquet"
COMMISSION_PER_LEG = 0.0065
SLIPPAGE_FRAC      = 0.25
SHORT_DTE, SHORT_TOL, GAP, GAP_TOL = 12, 3, 7, 2   # user's structure: +7 gap
MA_WINDOW, VIX_HIGH = 50, 20


def build_regime_map() -> pd.DataFrame:
    spy = pd.read_parquet(STOCK).copy()
    spy["trade_date"] = pd.to_datetime(spy["trade_date"]).dt.date
    spy = spy.sort_values("trade_date").reset_index(drop=True)
    spy["ma50"] = spy["close"].rolling(MA_WINDOW, min_periods=MA_WINDOW).mean()
    vix = pd.read_parquet(VIX).copy()
    vix["trade_date"] = pd.to_datetime(vix["trade_date"]).dt.date
    m = spy.merge(vix, on="trade_date", how="left")
    m["direction"] = np.where(m["close"] > m["ma50"], "Bullish", "Bearish")
    m["iv"]        = np.where(m["vix_close"] >= VIX_HIGH, "HighIV", "LowIV")
    m["regime"]    = m["direction"] + "_" + m["iv"]
    return m[["trade_date", "regime"]]


def add_costs(m: pd.DataFrame) -> pd.DataFrame:
    m = m.copy()
    spreads = sum((m[f"{lg}_ask"] - m[f"{lg}_bid"]).clip(lower=0)
                  for lg in ("sp", "sc", "lp", "lc"))
    m["cost"]        = COMMISSION_PER_LEG * 8 + SLIPPAGE_FRAC * spreads * 2
    m["net_pnl_net"] = m["net_pnl"] - m["cost"]
    m["roc_net"]     = m["net_pnl_net"] / m["net_debit"].clip(lower=0.001)
    m["is_win_net"]  = m["net_pnl_net"] > 0
    return m


def run(df, regimes, *, put_d, call_d, pt):
    trades = build_double_calendar_trades(
        df, delta_target=put_d, put_delta_target=put_d, call_delta_target=call_d,
        short_dte_target=SHORT_DTE, short_dte_tol=SHORT_TOL, gap_days=GAP, gap_tol=GAP_TOL,
        max_delta_err=0.10, max_spread_pct=0.25)
    if trades.empty:
        return None
    m = compute_double_calendar_metrics(find_double_calendar_exits(trades, df, profit_target_roc=pt))
    m = m[~m["is_open"]]
    if m.empty:
        return None
    m = add_costs(m)
    m["trade_date"] = pd.to_datetime(m["entry_date"]).dt.date
    return m.merge(regimes, on="trade_date", how="left")


def summarize(m, regime):
    g = m[m["regime"] == regime]
    if g.empty:
        return None
    return {
        "n": len(g), "win_net": round(g["is_win_net"].mean() * 100, 1),
        "rocCW_mid": round(g["net_pnl"].sum()     / g["net_debit"].sum() * 100, 2),
        "rocCW_net": round(g["net_pnl_net"].sum() / g["net_debit"].sum() * 100, 2),
        "med_net":  round(g["roc_net"].median() * 100, 2),
        "sumPnL_net": round(g["net_pnl_net"].sum(), 2),
        "debit": round(g["net_debit"].mean(), 2),
    }


def main():
    print(f"Loading {CACHE} ...")
    df = pd.read_parquet(CACHE)
    print(f"  {len(df):,} rows  ({df['trade_date'].min()} -> {df['trade_date'].max()})")
    regimes = build_regime_map()

    # Each matchup: (label, put_d, call_d, pt, regime-to-report)
    matchups = {
        "Bullish_LowIV": [
            ("INCUMBENT 0.25/0.25 50%PT", 0.25, 0.25, 0.50),
            ("CHALLENGER 0.35/0.35 50%PT", 0.35, 0.35, 0.50),
            ("CHALLENGER 0.35/0.35 25%PT", 0.35, 0.35, 0.25),
            ("CHALLENGER 0.30/0.30 25%PT", 0.30, 0.30, 0.25),
        ],
        "Bearish_HighIV": [
            ("INCUMBENT 0.25P/0.10C hold", 0.25, 0.10, None),
            ("CHALLENGER 0.35P/0.10C hold", 0.35, 0.10, None),
            ("CHALLENGER 0.35/0.35 hold", 0.35, 0.35, None),
            ("CHALLENGER 0.35/0.35 25%PT", 0.35, 0.35, 0.25),
        ],
    }

    # Cache built trades per (put,call,pt) to avoid rebuilds
    cache = {}
    def get(put_d, call_d, pt):
        key = (put_d, call_d, pt)
        if key not in cache:
            cache[key] = run(df, regimes, put_d=put_d, call_d=call_d, pt=pt)
        return cache[key]

    for regime, variants in matchups.items():
        print("\n" + "=" * 110)
        print(f"REGIME-GATED CONFIRMATION — {regime}  (+7 gap, after costs; rocCW = sum pnl / sum debit)")
        print("=" * 110)
        rows = []
        for label, put_d, call_d, pt in variants:
            m = get(put_d, call_d, pt)
            s = summarize(m, regime) if m is not None else None
            if s:
                rows.append({"variant": label, **s})
        out = pd.DataFrame(rows)
        pd.set_option("display.width", 200)
        print(out.to_string(index=False))

        # Year-by-year for incumbent vs the headline challenger (0.35/0.35 25%PT)
        inc = get(*( (0.25,0.25,0.50) if regime=="Bullish_LowIV" else (0.25,0.10,None) ))
        chl = get(0.35, 0.35, 0.25)
        print(f"\n  Year-by-year (sumPnL_net, after costs) in {regime}:")
        print(f"  {'year':>6} {'INC n':>6} {'INC $':>9} {'CHL n':>6} {'CHL $':>9}")
        for yr in range(2018, 2027):
            ig = inc[(inc['regime']==regime) & (pd.to_datetime(inc['entry_date']).dt.year==yr)] if inc is not None else pd.DataFrame()
            cg = chl[(chl['regime']==regime) & (pd.to_datetime(chl['entry_date']).dt.year==yr)] if chl is not None else pd.DataFrame()
            if len(ig)==0 and len(cg)==0:
                continue
            print(f"  {yr:>6} {len(ig):>6} {ig['net_pnl_net'].sum() if len(ig) else 0:>9.2f} "
                  f"{len(cg):>6} {cg['net_pnl_net'].sum() if len(cg) else 0:>9.2f}")


if __name__ == "__main__":
    main()
