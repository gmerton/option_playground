#!/usr/bin/env python3
"""
Vehicle benchmark: is the call debit spread's edge just leveraged beta? (2026-09-22, steps 1-3 of the follow-up to
run_ivrank_vehicle.py; pre-registered here before the first run.)

Same 4,742 paired entries as run_ivrank_vehicle.py (18 liquid names, every Friday, expiry closest to 30 DTE,
2019-10 -> 2026-01, real fills: pay the ask / sell the bid + $0.0065/leg, held to expiry, RAW spot from the chain
via lib.studies.chain_spot).

Q1 (decisive) -- DELTA-MATCHED STOCK. Each structure's entry delta is known (call debit: d(c30) - d(c15);
  put credit: |d(p30)| - |d(p20)|, long delta). Benchmark = holding that many shares of the same name over the same
  30 days. Report the option P&L minus the stock P&L per contract. A vehicle "edge" must beat its own delta.
Q2 -- FRAMING. Per $1,000 of capital at risk (= the ROC table) vs per contract in dollars vs per $1,000 of NOTIONAL
  delta exposure. The first flatters whichever leg has the small denominator; all three are reported.
Q3 -- REGIME. Same tables split by calendar year, by entry-VIX tercile, and by SPY above/below its 200 SMA, plus
  down-months only. If the call spread's lead is beta, it should vanish or invert when the market falls.
PRE-REGISTERED READ: the call debit spread has a vehicle edge only if (Q1) it beats delta-matched stock with
month-clustered t >= 2 AND (Q3) that holds with SPY below its 200 SMA. Otherwise the 2026-09-22 result is exposure,
not selection, and neither vehicle is adopted.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_vehicle_benchmark.py
"""
from __future__ import annotations
import warnings
from math import sqrt
import numpy as np, pandas as pd
from lib.athena_lib import athena  # noqa: F401  (cache is on disk; import kept so the pull path still works)
from lib.studies.chain_spot import spot_from_chain

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250)
COMM = 0.0065
raw = pd.read_parquet("data/cache/ivrank_vehicle_chains.parquet")
raw["trade_date"] = pd.to_datetime(raw.trade_date).dt.normalize()
raw["expiry"] = pd.to_datetime(raw.expiry).dt.normalize()
SPOT = spot_from_chain(raw, delta="d")
panel = pd.read_parquet("data/cache/liquid_panel_2019.parquet"); panel["date"] = pd.to_datetime(panel.date)
C = panel.pivot(index="date", columns="ticker", values="close").sort_index()
spy = C["SPY"]; spy200 = spy.rolling(200).mean()
vix = pd.read_parquet("data/cache/vix_daily.parquet"); vix["date"] = pd.to_datetime(vix.trade_date).dt.normalize()
VIX = vix.set_index("date").vix_close


def pick(g, target):
    if g.empty: return None
    r = g.iloc[(g.d.abs() - target).abs().argsort()[:1]].iloc[0]
    return r if abs(abs(r.d) - target) <= 0.07 else None


rows = []
for (tk, d), g in raw.groupby(["ticker", "trade_date"]):
    g = g.copy(); g["gap"] = (g.dte - 30).abs()
    exp = g.sort_values("gap").expiry.iloc[0]; g = g[g.expiry == exp]
    c30, c15 = pick(g[g.cp == "C"], 0.30), pick(g[g.cp == "C"], 0.15)
    p30, p20 = pick(g[g.cp == "P"], 0.30), pick(g[g.cp == "P"], 0.20)
    if any(x is None for x in (c30, c15, p30, p20)) or tk not in C.columns or d not in C.index: continue
    S, ST = SPOT.get((tk, d), np.nan), SPOT.get((tk, exp), np.nan)
    if not (np.isfinite(S) and np.isfinite(ST)): continue
    debit = (c30.ask - c15.bid) + 2 * COMM; wc = c15.strike - c30.strike
    credit = (p30.bid - p20.ask) - 2 * COMM; wp = p30.strike - p20.strike
    if debit <= 0 or wc <= 0 or credit <= 0 or wp <= 0 or credit >= wp: continue
    pnl_call = (min(max(ST - c30.strike, 0.0), wc) - debit) * 100          # $ per contract
    pnl_put = (credit - min(max(p30.strike - ST, 0.0), wp)) * 100
    risk_call, risk_put = debit * 100, (wp - credit) * 100
    dlt_call = float(c30.d - c15.d); dlt_put = float(abs(p30.d) - abs(p20.d))
    move = ST - S
    rows.append(dict(sym=tk, date=d, expiry=exp, iv=float(c30.iv), S=S, ST=ST, ret=(ST / S - 1) * 100,
                     pnl_call=pnl_call, pnl_put=pnl_put, risk_call=risk_call, risk_put=risk_put,
                     dlt_call=dlt_call, dlt_put=dlt_put,
                     stock_call=100 * dlt_call * move,      # delta-matched stock, same contract count
                     stock_put=100 * dlt_put * move,
                     bull=bool(np.isfinite(C.at[d, tk]) and C.at[d, tk] > C[tk].rolling(50).mean().at[d]),
                     vix=float(VIX.get(d, np.nan)),
                     spy_up=bool(np.isfinite(spy200.get(d, np.nan)) and spy.get(d, np.nan) > spy200.get(d, np.nan))))
T = pd.DataFrame(rows).sort_values(["sym", "date"])
T["ivrank"] = T.groupby("sym").iv.transform(lambda s: s.rolling(52, min_periods=40).apply(lambda w: (w[-1] > w[:-1]).mean(), raw=True) * 100)
T = T.dropna(subset=["ivrank"]); T["month"] = T.date.dt.to_period("M")
T["terc"] = np.where(T.ivrank <= 33, "LOW", np.where(T.ivrank >= 67, "HIGH", "MID"))
T["vs_stock_call"] = T.pnl_call - T.stock_call
T["vs_stock_put"] = T.pnl_put - T.stock_put
T["roc_call"] = 100 * T.pnl_call / T.risk_call
T["roc_put"] = 100 * T.pnl_put / T.risk_put
T["per1k_call"] = 1000 * T.pnl_call / T.risk_call          # $ per $1k at risk
T["per1k_put"] = 1000 * T.pnl_put / T.risk_put
print(f"{len(T):,} paired entries · {T.sym.nunique()} names · {T.date.min().date()}..{T.date.max().date()} · {T.month.nunique()} months")


def mt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def clustered(df, col):
    m = df.groupby("month")[col].mean(); return m.mean(), mt(m)


print("\n== Q1. DELTA-MATCHED STOCK (option P&L minus the same delta in shares, $ per contract) ==")
print(f"{'cut':28} {'n':>5} {'call $':>8} {'stock $':>8} {'diff':>8} {'t':>6} | {'put $':>8} {'stock $':>8} {'diff':>8} {'t':>6}")
def q1(lab, df):
    if len(df) < 30: return
    a, ta = clustered(df, "vs_stock_call"); b, tb = clustered(df, "vs_stock_put")
    print(f"{lab:28} {len(df):>5} {df.pnl_call.mean():>8.0f} {df.stock_call.mean():>8.0f} {a:>8.0f} {ta:>+6.2f} | "
          f"{df.pnl_put.mean():>8.0f} {df.stock_put.mean():>8.0f} {b:>8.0f} {tb:>+6.2f}")
q1("ALL", T)
for k in ("LOW", "MID", "HIGH"): q1(f"IV rank {k}", T[T.terc == k])
q1("bullish (above 50 SMA)", T[T.bull])

print("\n== Q2. THREE FRAMINGS (means) ==")
fr = pd.DataFrame({
    "$ per contract": [T.pnl_call.mean(), T.pnl_put.mean()],
    "$ per $1k at risk": [T.per1k_call.mean(), T.per1k_put.mean()],
    "capital at risk $": [T.risk_call.mean(), T.risk_put.mean()],
    "entry delta": [T.dlt_call.mean(), T.dlt_put.mean()],
    "$ per 1.0 delta": [T.pnl_call.mean() / T.dlt_call.mean() / 100, T.pnl_put.mean() / T.dlt_put.mean() / 100],
}, index=["call debit 30/15", "put credit 30/20"])
print(fr.round(2).to_string())

print("\n== Q3. REGIME ==")
print(f"{'cut':28} {'n':>5} {'call ROC%':>10} {'put ROC%':>9} {'call vs stock $':>16} {'t':>6} {'put vs stock $':>15} {'t':>6}")
def q3(lab, df):
    if len(df) < 30: return
    a, ta = clustered(df, "vs_stock_call"); b, tb = clustered(df, "vs_stock_put")
    print(f"{lab:28} {len(df):>5} {df.roc_call.mean():>10.1f} {df.roc_put.mean():>9.1f} {a:>16.0f} {ta:>+6.2f} {b:>15.0f} {tb:>+6.2f}")
for y, g in T.groupby(T.date.dt.year): q3(f"year {y}", g)
vt = pd.qcut(T.vix, 3, labels=["VIX low", "VIX mid", "VIX high"])
for k in vt.cat.categories: q3(str(k), T[vt == k])
q3("SPY > 200 SMA", T[T.spy_up]); q3("SPY < 200 SMA", T[~T.spy_up])
dn = T.groupby("month").ret.mean() < 0
q3("down months (name-avg < 0)", T[T.month.map(dn)])
T.to_csv("data/studies/vehicle_benchmark_2026-09-22.csv", index=False)
