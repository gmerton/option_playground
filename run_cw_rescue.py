#!/usr/bin/env python3
"""
Does PREMIUM-TO-WIDTH rescue the screener spreads we tagged Tier U / retired? (2026-09-22, pre-registered.)

2026-09-22 found (run_premium_to_width.py) that credit/width sorts bull put spreads ACROSS names at a fixed
structure: +7.64pp net ROC within-date, t 4.15, in both VIX terciles. Every spread retired that day was a
low-credit/width name (ASHR collected $0.12 against $0.07 of cost). So: if we keep only the entries whose
credit/width is high, does any of them come back?

NAMES + STRUCTURES = exactly what the screener defined before today's retirements:
  bull puts  GLD .30/.20 · USO .25/.15 (30 DTE) · SOXX .35/.25 · INDA .25/.15 · BJ .20/.10 (45 DTE) ·
             GEV .25/.15 · CLS .25/.15 · ASHR .25/.15 (retired) · XOP .35/.25 (60 DTE, retired)
  bear calls TLT .35/.25 · SQQQ .50/.40 (retired) · TMF .35/.25 (retired) · ASHR .20/.10 (retired) ·
             UVXY .50/.40 (retired) · UVIX .50/.40 (retired)
Friday entries, expiry closest to the strategy's DTE, real fills (sell the bid / buy the ask + $0.0065/leg/side),
held to expiry, settled on the RAW spot from the chain (lib.studies.chain_spot). ROC on (width - credit).

TEST: per name, net ROC in the TOP half vs the BOTTOM half of its own credit/width history, and for the pooled
book, quintiles of credit/width. PRE-REGISTERED PASS for a rescue: the name's top-half net ROC > 0 with
month-clustered t >= 2 AND positive in both halves of the sample. A name that only turns positive in one period,
or on fewer than ~20 trades, is not rescued.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 run_cw_rescue.py
"""
from __future__ import annotations
import os, warnings
from math import sqrt
import numpy as np, pandas as pd
from lib.athena_lib import athena
from lib.studies.chain_spot import spot_from_chain

warnings.filterwarnings("ignore"); pd.set_option("display.width", 250)
CACHE = "data/cache/cw_rescue_chains.parquet"
COMM = 0.0065
SPECS = [  # name, cp, short delta, long delta, dte, status
    ("GLD", "P", .30, .20, 20, "Tier U"), ("USO", "P", .25, .15, 30, "Tier U"), ("SOXX", "P", .35, .25, 20, "Tier U"),
    ("INDA", "P", .25, .15, 20, "Tier U"), ("BJ", "P", .20, .10, 45, "Tier U"), ("GEV", "P", .25, .15, 20, "Tier U"),
    ("CLS", "P", .25, .15, 20, "Tier U"), ("TLT", "C", .35, .25, 20, "Tier U"),
    ("ASHR", "P", .25, .15, 20, "retired"), ("XOP", "P", .35, .25, 60, "retired"), ("ASHR", "C", .20, .10, 20, "retired"),
    ("SQQQ", "C", .50, .40, 20, "retired"), ("TMF", "C", .35, .25, 20, "retired"),
    ("UVXY", "C", .50, .40, 20, "retired"), ("UVIX", "C", .50, .40, 20, "retired"),
]
NAMES = sorted({s[0] for s in SPECS})


def pull() -> pd.DataFrame:
    if os.path.exists(CACHE): return pd.read_parquet(CACHE)
    lst = ", ".join(f"'{t}'" for t in NAMES)
    sql = f"""
    SELECT ticker, trade_date, expiry, cp, strike, CAST(bid AS DOUBLE) bid, CAST(ask AS DOUBLE) ask,
           CAST(delta AS DOUBLE) d, CAST((bid_iv+ask_iv)/2.0 AS DOUBLE) iv,
           date_diff('day', trade_date, expiry) dte
    FROM "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"
    WHERE ticker IN ({lst})
      AND trade_date >= TIMESTAMP '2018-01-01 00:00:00' AND trade_date <= TIMESTAMP '2026-02-27 23:59:59'
      AND day_of_week(trade_date) = 5
      AND bid > 0 AND delta IS NOT NULL
      AND date_diff('day', trade_date, expiry) BETWEEN 12 AND 70
      AND ABS(delta) BETWEEN 0.05 AND 0.60
    """
    df = athena(sql); df.to_parquet(CACHE, index=False); return df


raw = pull()
raw["trade_date"] = pd.to_datetime(raw.trade_date).dt.normalize(); raw["expiry"] = pd.to_datetime(raw.expiry).dt.normalize()
SPOT = spot_from_chain(raw, delta="d")


def pick(g, target):
    if g.empty: return None
    r = g.iloc[(g.d.abs() - target).abs().argsort()[:1]].iloc[0]
    return r if abs(abs(r.d) - target) <= 0.08 else None


rows = []
for tk, cp, sd, ld, dte, status in SPECS:
    sub = raw[(raw.ticker == tk) & (raw.cp == cp)]
    for d, g in sub.groupby("trade_date"):
        g = g.copy(); g["gap"] = (g.dte - dte).abs()
        exp = g.sort_values("gap").expiry.iloc[0]
        if abs((exp - d).days - dte) > max(10, dte // 3): continue
        g = g[g.expiry == exp]
        s_, l_ = pick(g, sd), pick(g, ld)
        if s_ is None or l_ is None: continue
        width = (l_.strike - s_.strike) if cp == "C" else (s_.strike - l_.strike)
        credit = (s_.bid - l_.ask) - 2 * COMM
        if width <= 0 or credit <= 0 or credit >= width: continue
        ST = SPOT.get((tk, exp), np.nan)
        if not np.isfinite(ST): continue
        loss = min(max(ST - s_.strike, 0.0), width) if cp == "C" else min(max(s_.strike - ST, 0.0), width)
        rows.append(dict(name=f"{tk} {'bear call' if cp=='C' else 'bull put'}", status=status, date=d, expiry=exp,
                         credit=credit, width=width, cw=credit / width, roc=(credit - loss) / (width - credit),
                         win=(credit - loss) > 0, iv=float(s_.iv)))
T = pd.DataFrame(rows)
T["month"] = T.date.dt.to_period("M")
print(f"{len(T):,} spreads across {T.name.nunique()} screener strategies, {T.date.min().date()}..{T.date.max().date()}")


def mt(x):
    x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


print(f"\n{'strategy':22} {'status':8} {'n':>4} {'all ROC%':>9} {'LOW cw':>8} {'HIGH cw':>8} {'t(HIGH)':>8} {'H1':>7} {'H2':>7} {'cw med':>7} rescued")
res = []
for (nm, st), g in T.groupby(["name", "status"]):
    if len(g) < 20: continue
    med = g.cw.median()
    hi = g[g.cw > med]; lo = g[g.cw <= med]
    m = hi.groupby("month").roc.mean(); t = mt(m)
    mid = g.date.min() + (g.date.max() - g.date.min()) / 2
    h1 = hi[hi.date < mid].roc.mean() * 100; h2 = hi[hi.date >= mid].roc.mean() * 100
    ok = (t >= 2) and (h1 > 0) and (h2 > 0)
    res.append(dict(name=nm, status=st, n=len(g), all_roc=100 * g.roc.mean(), lo=100 * lo.roc.mean(),
                    hi=100 * hi.roc.mean(), t=t, h1=h1, h2=h2, cw=med, rescued=ok))
    print(f"{nm:22} {st:8} {len(g):>4} {100*g.roc.mean():>+9.2f} {100*lo.roc.mean():>+8.2f} {100*hi.roc.mean():>+8.2f} "
          f"{t:>+8.2f} {h1:>+7.2f} {h2:>+7.2f} {med:>7.2f} {'YES' if ok else ''}")
R = pd.DataFrame(res)
print("\nRESCUED:", R[R.rescued].name.tolist() or "NONE")

print("\npooled across all of these strategies, by credit/width quintile:")
T["q"] = pd.qcut(T.cw, 5, labels=False, duplicates="drop")
print(T.groupby("q").agg(n=("roc", "size"), cw=("cw", "mean"), iv=("iv", "mean"),
                         net_roc=("roc", lambda x: 100 * x.mean()), win=("win", lambda x: 100 * x.mean())).round(2).to_string())
T.to_csv("data/studies/cw_rescue_2026-09-22.csv", index=False)
