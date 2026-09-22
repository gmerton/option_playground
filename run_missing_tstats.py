#!/usr/bin/env python3
"""
Test statistics for the claims we ACT ON that had none (2026-09-22; item 1 of the post-correction queue).

The ledger-wide multiple-testing correction found 7 acted-on claims with no t on file. Two (the Tier A/B regime
playbooks, UVXY/UVIX) were computed the same day and both partly failed. This script does the remaining five plus
the straddle-stop removal, each from its own trade-level output, with the clustering the data demands:

  1. SIZE LEVER -- "trade A+B grades only" (+0.29R OOS)      data/cache/size_lever_trades.parquet
     t on the OOS window (2023+) for (A+B mean R) - (all-grades mean R), month-clustered.
  2. EVENT CONVEXITY -- OTM calls before FOMC/elections beat random dates   data/cache/event_convexity/trades.parquet
     t on (event - control) per arm, clustered by event date (the events are the unit; ~1 per month at most).
  3. PAID-TO-WAIT IV GATE -- "sell the put spread only when IV pct >= 60" (+5.7% net)  paid_to_wait_events.csv
     t on the gated cohort's net ROC, and on (gated - ungated), month-clustered.
  4. SLEEPING GIANTS -- cheap LEAP on a multi-year base, "convex edge holds OOS"  sleeping_giants_trades.csv
     t per arm on the primary ROC, by regime split (the file carries pre2022_OOS / post tags).
  5. STRADDLE STOP REMOVAL -- "0 of 20 stop variants beat no stop"   straddle_recenter/recenter_results.parquet
     paired t on (hold - path-stop) per trade, month-clustered -- the removal is a claim about a DIFFERENCE.
  6. (context) STRADDLE ITSELF -- hold, net of costs, month-clustered, for comparison.

No new rules are proposed here; this only attaches a statistic to what is already in the book, so the ledger
correction can be re-run over a complete table.

Usage: PYTHONPATH=src .venv/bin/python3 run_missing_tstats.py
"""
from __future__ import annotations
import warnings
from math import sqrt
import numpy as np, pandas as pd

warnings.filterwarnings("ignore"); pd.set_option("display.width", 240)
OUT = []


def t_of(x) -> float:
    x = pd.Series(x).dropna()
    return x.mean() / (x.std(ddof=1) / sqrt(len(x))) if len(x) > 2 else np.nan


def clustered(df: pd.DataFrame, col: str, by: str):
    m = df.groupby(by)[col].mean()
    return m.mean(), t_of(m), len(m)


def rec(claim, stat, t, n, units, note=""):
    OUT.append(dict(claim=claim, stat=round(stat, 3) if stat == stat else np.nan,
                    t=round(t, 2) if t == t else np.nan, n=n, units=units, note=note))
    print(f"  {claim:52} {stat:+8.3f} {units:14} t {t:+5.2f}  (n {n})  {note}")


print("\n1. SIZE LEVER -- A+B only vs all grades")
S = pd.read_parquet("data/cache/size_lever_trades.parquet")
S["date"] = pd.to_datetime(S.date); S["month"] = S.date.dt.to_period("M")
oos = S[S.date >= "2023-01-01"]
ab = oos[oos.grade.isin(["A", "B"])]; c = oos[oos.grade == "C"]
# NB A+B is exactly the precision tier in this file (A+B OOS mean R = precision-only mean R = +0.286), so the
# "exclusion lever" is the precision-tier selection already in the book, not an independent lever on top of it.
m_ab = ab.groupby("month").R.mean(); m_c = c.groupby("month").R.mean()
diff = (m_ab - m_c).dropna()
rec("size lever: A+B (= precision tier), OOS", *clustered(ab, "R", "month")[:2], len(ab), "R/trade")
rec("size lever: C (the excluded rest), OOS", *clustered(c, "R", "month")[:2], len(c), "R/trade")
rec("size lever: (A+B) - C, OOS", diff.mean(), t_of(diff), len(diff), "R/trade", "what exclusion buys; the +0.29R claim was A+B vs the whole pool")

print("\n2. EVENT CONVEXITY -- calls before FOMC/elections vs control dates")
E = pd.read_parquet("data/cache/event_convexity/trades.parquet")
E["date"] = pd.to_datetime(E.date)
print(f"   kinds: {E.kind.value_counts().to_dict()}   deltas: {sorted(E.delta.unique())}")
# controls sit on DIFFERENT (random) dates by design, so this is unpaired: Welch on date-level means
for arm in ("sell_5d", "sell_10d", "hold_expiry"):
    ge = E[E.kind == "event"].groupby("date")[arm].mean().dropna()
    gc = E[E.kind == "control"].groupby("date")[arm].mean().dropna()
    se = np.sqrt(ge.var(ddof=1) / len(ge) + gc.var(ddof=1) / len(gc))
    rec(f"event calls {arm} vs control (Welch)", 100 * (ge.mean() - gc.mean()), (ge.mean() - gc.mean()) / se,
        len(ge), "pp of premium", f"{len(ge)} event vs {len(gc)} control dates")

print("\n3. PAID-TO-WAIT -- the IV>=60th-percentile gate")
P = pd.read_csv("data/studies/paid_to_wait_events.csv", parse_dates=["entry_date"])
P["month"] = P.entry_date.dt.to_period("M")
gated = P[P.iv_pct >= 0.60]; ungated = P[P.iv_pct < 0.60]
rec("paid-to-wait: gated (IV pct >= 60), net ROC", *clustered(gated, "roc_hold_net", "month")[:2], len(gated), "ROC", "the +5.7% claim")
rec("paid-to-wait: ungated, net ROC", *clustered(ungated, "roc_hold_net", "month")[:2], len(ungated), "ROC")
mg = gated.groupby("month").roc_hold_net.mean(); mu = ungated.groupby("month").roc_hold_net.mean()
d = (mg - mu).dropna()
rec("paid-to-wait: gated - ungated", d.mean(), t_of(d), len(d), "ROC", "months where both fire")

print("\n4. SLEEPING GIANTS -- cheap LEAP on a multi-year base")
G = pd.read_csv("data/studies/Adhikary/sleeping_giants_trades.csv", parse_dates=["entry_date"])
G["month"] = G.entry_date.dt.to_period("M")
col = "roc_primary"
for arm, g in G.groupby("arm"):
    rec(f"sleeping giants arm {arm}", *clustered(g, col, "month")[:2], len(g), "ROC %")
for reg, g in G.groupby("regime"):
    rec(f"sleeping giants {reg}", *clustered(g, col, "month")[:2], len(g), "ROC %")

print("\n5. STRADDLE -- the stop removal (paired) and the strategy itself")
R = pd.read_parquet("data/cache/straddle_recenter/recenter_results.parquet")
R = R[(R.arm == 7) & R.both].copy()
R["entry_date"] = pd.to_datetime(R.entry_date); R["month"] = R.entry_date.dt.to_period("M")
R["gain_from_no_stop"] = R.hold - R.stop
rec("straddle: hold, net of costs", *clustered(R, "hold", "month")[:2], len(R), "%/trade", "the in-book strategy")
rec("straddle: no-stop minus path stop", *clustered(R, "gain_from_no_stop", "month")[:2], len(R), "%/trade",
    "the 'drop the stop' claim")
rec("straddle: with the -50% path stop", *clustered(R, "stop", "month")[:2], len(R), "%/trade")

T = pd.DataFrame(OUT)
T.to_csv("data/studies/missing_tstats_2026-09-22.csv", index=False)
print(f"\nwrote data/studies/missing_tstats_2026-09-22.csv ({len(T)} rows)")
