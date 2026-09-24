#!/usr/bin/env python3
"""
Volatility-managed sizing of the book (Moreira & Muir 2017) -- pre-registered 2026-09-24, before the first run.
Gabe's "other ideas" list, #1. The ledger has NO vol-targeting row; the size-lever study (2026-09-18) sized by trade
GRADE (exclusion won), never by market volatility.

IDEA: scale each trade's risk budget by 1 / sigma^2 of the market at entry (SPY 20-day realized variance, prior close):
smaller when the market is volatile, larger when it is calm. MM find this raises Sharpe for most factors because
volatility clusters while expected returns don't rise with it. It changes RISK-ADJUSTED return, not selection.

DESIGN
  sleeves   BRK  precision-tier breakouts (run_precision_tier_control.build + the house process, R capped 20), 2019-10 ->
            PUT  certified bearish-high-IV SPY/QQQ bull puts (data/studies/cw_on_certified_2026-09-22.csv, roc_net)
            ETF  the ETF put roster, Friday entries, live 50%-take rule (putspread_exit_capital_time trades, net ROC)
            (the 7-DTE long straddle is omitted: no trade file with an unambiguous identity was found.)
  weight    w = (1 / RV20^2) / expanding mean of (1 / RV20^2) over PRIOR dates  -> no look-ahead, mean ~1; cap 3x.
            variant: 1 / RV20 (linear).
  book      monthly series: sum of w x trade return by ENTRY month (unmanaged = sum of trade returns, w = 1).
  PRIMARY   BRK: regress managed on unmanaged monthly (MM's test), alpha > 0 with t >= 3, both halves' alpha > 0;
            report Sharpe (annualised) both ways and the worst month.
  SECONDARY PUT and ETF (⚠ the PUT cell is conditioned on HIGH IV, so vol-managing it downsizes the very entries that
            define it -- expect it to hurt); the 1/RV variant; VIX instead of RV20.

Usage: PYTHONPATH=src:. .venv/bin/python3 run_vol_managed_book.py   (log -> data/studies/logs/vol_managed_book.log)
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/vol_managed_book.log"
CAP = 3.0


def spy_rv() -> pd.Series:
    raw = pd.read_parquet(REPO / "data/cache/liquid_panel_2009.parquet")
    s = raw[raw.ticker == "SPY"].set_index("date").close.sort_index()
    s.index = pd.to_datetime(s.index)
    rv = s.pct_change().rolling(20).std() * sqrt(252) * 100
    return rv.shift(1).dropna()                          # known at the prior close


def weights(dates: pd.Series, sig: pd.Series, power: int) -> np.ndarray:
    x = (1.0 / sig ** power)
    norm = x.expanding(min_periods=60).mean().shift(1)    # prior dates only
    w = (x / norm).clip(upper=CAP)
    return w.reindex(pd.to_datetime(dates), method="ffill").values


def evaluate(name: str, df: pd.DataFrame, sig: pd.Series, out: list, primary: bool = False):
    df = df.copy()
    df["date"] = pd.to_datetime(df.date)
    for p, lab in ((2, "1/var"), (1, "1/vol")):
        df[f"w_{lab}"] = weights(df.date, sig, p)
    df = df.dropna(subset=["w_1/var", "ret"])
    m = df.assign(month=df.date.dt.to_period("M"))
    base = m.groupby("month").ret.sum()
    out.append(f"\n## {name}: {len(df):,} trades, {base.size} months, mean weight {df['w_1/var'].mean():.2f} (1/var)")
    sh = lambda x: x.mean() / x.std() * sqrt(12)
    out.append(f"  unmanaged: mean/month {base.mean():+.3f}  Sharpe {sh(base):.2f}  worst month {base.min():+.2f}")
    res = {}
    for lab in ("1/var", "1/vol"):
        man = (m.ret * m[f"w_{lab}"]).groupby(m.month).sum().reindex(base.index)
        X = sm.add_constant(base.values)
        fit = sm.OLS(man.values, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        half = base.index < base.index[len(base) // 2]
        a_h = [sm.OLS(man.values[h], sm.add_constant(base.values[h])).fit().params[0] for h in (half, ~half)]
        res[lab] = (fit.params[0], fit.tvalues[0], a_h)
        out.append(f"  managed {lab:5s}: mean/month {man.mean():+.3f}  Sharpe {sh(man):.2f}  worst month {man.min():+.2f}  "
                   f"| alpha {fit.params[0]:+.3f}/month (t {fit.tvalues[0]:+.2f}), beta {fit.params[1]:.2f}, "
                   f"halves alpha {a_h[0]:+.3f} / {a_h[1]:+.3f}")
    if primary:
        a, t, h = res["1/var"]
        ok = a > 0 and t >= 3 and h[0] > 0 and h[1] > 0
        out.append(f"  PRIMARY bar (1/var alpha > 0, t >= 3, both halves > 0): {'PASS' if ok else 'FAIL'}")
    # where the weight comes from: return per trade by market-vol tercile
    q = pd.qcut(df["w_1/var"], 3, labels=["high vol (small w)", "mid", "low vol (large w)"])
    out.append("  per-trade return by market-vol tercile: " +
               "  ".join(f"{k} {v:+.3f}" for k, v in df.groupby(q, observed=True).ret.mean().items()))


def main() -> None:
    sig = spy_rv()
    out = ["# Volatility-managed sizing of the book (pre-registration in the docstring)"]

    # BRK: precision-tier breakouts, house process, R capped at 20
    from run_precision_tier_control import build
    from run_adr_floor_test import house
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        P, brk, prec = build()
        T = house(P, prec)
    evaluate("BRK precision-tier breakouts (R)", pd.DataFrame(dict(date=T.date, ret=T.R)), sig, out, primary=True)

    c = pd.read_csv(REPO / "data/studies/cw_on_certified_2026-09-22.csv")
    evaluate("PUT certified bearish-high-IV SPY/QQQ bull puts (net ROC)", pd.DataFrame(dict(date=c.entry_date, ret=c.roc_net)), sig, out)

    e = pd.read_parquet(REPO / "data/studies/logs/putspread_exit_capital_time_trades.parquet")
    e = e[(e.arm == "T50") & (pd.to_datetime(e.entry_date).dt.weekday == 4)]
    evaluate("ETF put roster, Friday, 50% take (net ROC)", pd.DataFrame(dict(date=e.entry_date, ret=e.roc)), sig, out)

    vix = pd.read_parquet(REPO / "data/cache/vix_daily_long.parquet")
    vix = vix.set_index(pd.to_datetime(vix.trade_date)).vix_close.shift(1).dropna()
    evaluate("BRK with VIX instead of RV20 (secondary)", pd.DataFrame(dict(date=T.date, ret=T.R)), vix, out)
    print("\n".join(out))


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
