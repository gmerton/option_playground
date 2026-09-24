#!/usr/bin/env python3
"""
[WL-5f] Deep-OTM SPY put overlay on the certified bearish-high-IV bull put bucket (pre-registered 2026-09-23; spec
from data/tail_hedging/videos/2026-01-15_HC6GKtqNZHc/notes.md "Not tested, could be", written before any pull).

Bucket (A): SPY 0.25/0.15-delta bull put, ~20 DTE, Friday entry, 50% take, no stop, SPY < 50MA and VIX >= 20 -- rebuilt
  from silver.options_daily_v3 through the SAME engine (lib.studies.put_spread_study); reproduces the 75 recorded
  trades exactly (mean net ROC +6.70% vs +6.76%, per-trade corr 1.000).
Overlays (premium budget = 10% of the spread's credit; secondary 5% / 20%):
  B  PRIMARY  SPY put at the nearest 5-delta, SAME expiry as the spread, bought at the ask, held to expiry, settled at
              intrinsic (raw SPY close; v3 strikes are raw)
  B' variant  same put, sold at the bid on the spread's exit date if that is before expiry
  C           3-delta put at ~60 DTE (nearest to 60 in 50-70), sold at the bid after 20 sessions or at the spread's exit,
              whichever is first
Commission $0.0065/sh per overlay leg per side. Combined ROC = (spread net P&L + overlay P&L) / (spread max loss +
  overlay premium), per share of spread.
Measures: month-clustered paired delta in net ROC (entry month); delta CVaR-5% and worst month of the monthly ROC series;
  per-year signs; LEAVE-ONE-EPISODE-OUT (2018-Q4, 2020-02/04, 2022-H1).
Control: the same overlay (B, 10% of a notional credit = the bucket's median credit per $ of width) bought on
  NON-bucket Fridays with VIX >= 20 (holds the vol state fixed, moves the bucket signal): overlay return on premium,
  bucket vs control. Descriptive carry table: 5-delta same-expiry and 3-delta ~60-DTE puts on all Fridays, VIX >= 20
  vs < 20.
BAR (stated in advance): a delta-mean t >= 3 is unreachable -- the effective n is the ~3 stress episodes, not 75. The
  best achievable verdicts are UNDERPOWERED-helps-the-tail or NULL / negative carry. Accept as a risk tool only if it
  improves worst-month / CVaR by more than it costs in mean ROC AND the improvement survives leave-one-episode-out.
Prior: NULL, leaning negative on mean (bought at the richest skew of the cycle).

Run: PYTHONPATH=src:. .venv/bin/python3 run_spy_tail_overlay.py   (log -> data/studies/logs/spy_tail_overlay.log)
"""
from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import run_qqq_regime_put_sweep as S
from lib.studies.put_study import fetch_vix_data
from lib.studies.put_spread_study import (add_ma_column, build_put_spread_trades, compute_spread_metrics,
                                          find_put_spread_exits)

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/spy_tail_overlay.log"
COMM = 0.0065
EPISODES = {"2018-Q4": ("2018-10-01", "2018-12-31"), "2020-03": ("2020-02-15", "2020-04-30"),
            "2022-H1": ("2022-01-01", "2022-06-30")}


def load_quotes():
    a = pd.read_parquet(REPO / "data/cache/SPY_puts_v3_2018_2026.parquet")
    b = pd.read_parquet(REPO / "data/cache/SPY_puts_v3_2018_2026_dte36_49.parquet")
    q = pd.concat([a, b], ignore_index=True).drop_duplicates(["trade_date", "expiry", "strike"])
    q["dte"] = (q.expiry - q.trade_date).dt.days
    return q


def stock_close():
    """Raw SPY close. ⚠ data/cache/SPY_stock.parquet was overwritten outside this study (65 rows, other schema); the
    committed version is read from git so the working copy is left alone."""
    import subprocess, io
    raw = subprocess.run(["git", "show", "HEAD:data/cache/SPY_stock.parquet"], cwd=REPO, capture_output=True).stdout
    s = pd.read_parquet(io.BytesIO(raw))
    s["trade_date"] = pd.to_datetime(s.trade_date).dt.date
    return s


def engine_input(q):
    e = q[q.dte <= 35].copy()
    e["trade_date"] = e.trade_date.dt.date; e["expiry"] = e.expiry.dt.date
    e["mid"] = (e.bid + e.ask) / 2
    for c in ("last", "open_interest", "volume"):
        e[c] = np.nan
    return e


def spreads(q, stock):
    S.TICKER = "SPY"; S.SPLIT_DATES = []; S.DTE_TARGET = 20; S.DTE_TOL = 5
    vix = fetch_vix_data(S.START - timedelta(days=5), S.END)
    e = engine_input(q)
    pos = build_put_spread_trades(e, short_delta_target=0.25, wing_delta_width=0.10, dte_target=20, dte_tol=5,
                                  entry_weekday=4, split_dates=[], max_delta_err=0.08, max_spread_pct=None)
    pos["vix_on_entry"] = pos["entry_date"].map(vix.set_index("trade_date")["vix_close"])
    pos = add_ma_column(pos, stock, S.MA_DAYS)
    pos = find_put_spread_exits(pos, e, profit_take_pct=0.50, stop_multiple=None)
    pos = compute_spread_metrics(pos)
    pos["regime"] = pos.apply(S.assign_regime, axis=1)
    return pos[~pos.is_open & ~pos.split_flag].copy()


def pick(qd: pd.DataFrame, expiry, target_delta: float):
    c = qd[(qd.expiry == expiry) & (qd.ask > 0) & qd.delta.notna()]
    if c.empty:
        return None
    return c.loc[(c.delta + target_delta).abs().idxmin()]


def quote_on(qidx, d, expiry, strike):
    try:
        return qidx.loc[(d, expiry, strike)]
    except KeyError:
        return None


def sell_price(qidx, dates_after, expiry, strike):
    """Bid on the first available date in dates_after (the intended exit date first)."""
    for d in dates_after:
        r = quote_on(qidx, d, expiry, strike)
        if r is not None and np.isfinite(r.bid):
            return float(r.bid), d
    return None, None


def overlay_pnl(row, q, qidx, by_date, close, budget, arm, days):
    """Overlay P&L and premium in $ PER SPREAD CONTRACT (x100), matching the engine's net_pnl_net / max_loss units
    (the engine's credit is per share). 2026-09-23 fix: the first run mixed per-share and per-contract units."""
    p, pr = _overlay_pnl_ps(row, q, qidx, by_date, close, budget, arm, days)
    return p * 100, pr * 100


def _overlay_pnl_ps(row, q, qidx, by_date, close, budget, arm, days):
    """P&L per share of spread for the overlay; returns (pnl, premium) or (nan, nan)."""
    ed = pd.Timestamp(row.entry_date)
    if ed not in by_date:
        return np.nan, np.nan
    qd = by_date[ed]
    if arm in ("B", "B'"):
        ex = pd.Timestamp(row.expiry)
        opt = pick(qd, ex, 0.05)
    else:
        cand = qd[(qd.dte >= 50) & (qd.dte <= 70)]
        if cand.empty:
            return np.nan, np.nan
        ex = cand.expiry.iloc[(cand.dte - 60).abs().argmin()]
        opt = pick(qd, ex, 0.03)
    if opt is None or not np.isfinite(opt.ask) or opt.ask <= 0:
        return np.nan, np.nan
    credit = float(row.net_credit_worst)
    k = budget * credit / (opt.ask + COMM)                        # contracts (per share of spread)
    premium = k * (opt.ask + COMM)
    K = float(opt.strike)
    if arm == "B":
        sx = close.get(ex.date(), np.nan)
        if not np.isfinite(sx):
            return np.nan, np.nan
        return k * max(K - sx, 0.0) - premium, premium
    xd = pd.Timestamp(row.exit_date)
    if arm == "B'":
        if xd >= ex:
            sx = close.get(ex.date(), np.nan)
            return (k * max(K - sx, 0.0) - premium, premium) if np.isfinite(sx) else (np.nan, np.nan)
        target = xd
    else:
        i0 = days.searchsorted(ed)
        d20 = days[min(i0 + 20, len(days) - 1)]
        target = min(xd, d20)
    after = [d for d in days[days.searchsorted(target):days.searchsorted(target) + 5]]
    bid, _ = sell_price(qidx, after, ex, K)
    if bid is None:
        return np.nan, np.nan
    return k * (bid - COMM) - premium, premium


def main():
    q = load_quotes()
    stock = stock_close()
    close = dict(zip(stock.trade_date, stock.close))
    pos = spreads(q, stock)
    A = pos[pos.regime == "Bearish_HighIV"].copy()
    print(f"# SPY tail overlay [WL-5f] -- bucket rebuilt from v3: {len(A)} trades, mean net ROC {A.roc_net.astype(float).mean():+.4f} "
          f"(recorded +0.0676)")
    by_date = {d: g for d, g in q.groupby("trade_date")}
    qidx = q.set_index(["trade_date", "expiry", "strike"]).sort_index()
    days = pd.DatetimeIndex(sorted(q.trade_date.unique()))
    A["spnl"] = A.net_pnl_net.astype(float)
    A["risk"] = A.max_loss.astype(float)
    A["rocA"] = A.spnl / A.risk
    A["month"] = pd.to_datetime(A.entry_date).dt.to_period("M")
    res = {}
    for arm in ("B", "B'", "C"):
        for bud in (0.05, 0.10, 0.20):
            v = [overlay_pnl(r, q, qidx, by_date, close, bud, arm, days) for r in A.itertuples()]
            op = np.array([x[0] for x in v]); pr = np.array([x[1] for x in v])
            A[f"roc_{arm}_{bud}"] = (A.spnl + op) / (A.risk + pr)
            A[f"ovr_{arm}_{bud}"] = op / pr                         # overlay return on its own premium
            res[(arm, bud)] = int(np.isfinite(op).sum())
    print("overlays priced (of 75):", {f"{a}@{int(b * 100)}%": n for (a, b), n in res.items()})

    def monthly(col):
        return A.groupby("month")[col].mean()

    def cvar(m, p=0.05):
        k = max(1, int(np.ceil(p * len(m))))
        return m.sort_values().head(k).mean()

    mA = monthly("rocA")
    print(f"\nA (bucket alone): trades {len(A)} | mean ROC {A.rocA.mean():+.4f} | months {len(mA)} | worst month "
          f"{mA.min():+.4f} | CVaR5% {cvar(mA):+.4f} | worst trade {A.rocA.min():+.4f}")
    rows = []
    for arm in ("B", "B'", "C"):
        for bud in (0.05, 0.10, 0.20):
            col = f"roc_{arm}_{bud}"
            ok = A[col].notna()
            d = (A[col] - A.rocA)[ok]
            dm = d.groupby(A.month[ok]).mean()
            m = monthly(col)
            loo = {}
            for ep, (a, b) in EPISODES.items():
                keep = ~pd.to_datetime(A.entry_date).between(a, b)
                mm = A[keep & ok].groupby("month")[col].mean(); ma = A[keep & ok].groupby("month").rocA.mean()
                loo[ep] = (mm.min() - ma.min(), cvar(mm) - cvar(ma))
            rows.append(dict(arm=arm, budget=bud, n=int(ok.sum()), d_mean=d.mean(),
                             t_month=dm.mean() / dm.std(ddof=1) * np.sqrt(len(dm)) if len(dm) > 2 else np.nan,
                             # same-sample comparison: C prices only 61/75 trades, so compare on the common trades
                             d_worst_month=m.min() - A[ok].groupby("month").rocA.mean().min(),
                             d_cvar5=cvar(m) - cvar(A[ok].groupby("month").rocA.mean()),
                             ovr_mean=A[f"ovr_{arm}_{bud}"].mean(), ovr_win=(A[f"ovr_{arm}_{bud}"] > 0).mean(),
                             **{f"LOO {ep} d_worst": v[0] for ep, v in loo.items()},
                             **{f"LOO {ep} d_cvar": v[1] for ep, v in loo.items()}))
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 260)
    print("\n## overlays vs A (delta = overlay arm minus bucket alone; ROC on spread risk + overlay premium)")
    print(R.round(4).to_string(index=False))
    b = R[(R.arm == "B") & (R.budget == 0.10)].iloc[0]
    print(f"\nPRIMARY B @ 10%: d_mean {b.d_mean:+.4f} (month-clustered t {b.t_month:+.2f}) | d_worst_month {b.d_worst_month:+.4f} "
          f"| d_CVaR5 {b.d_cvar5:+.4f} | overlay return on premium {b.ovr_mean:+.2%} (win {b.ovr_win:.0%})")
    yr = pd.DataFrame({"n": A.groupby(pd.to_datetime(A.entry_date).dt.year).size(),
                       "A": A.groupby(pd.to_datetime(A.entry_date).dt.year).rocA.mean(),
                       "B10": A.groupby(pd.to_datetime(A.entry_date).dt.year)["roc_B_0.1"].mean()})
    yr["delta"] = yr.B10 - yr.A
    print("per year (mean ROC):\n" + yr.round(4).T.to_string())
    print("\nthe tail trades (A <= -50%):")
    print(A[A.rocA <= -0.5][["entry_date", "expiry", "exit_date", "rocA", "roc_B_0.1", "roc_C_0.1", "ovr_B_0.1"]].round(4).to_string(index=False))

    # control: the same 5-delta same-expiry overlay on NON-bucket Fridays with VIX >= 20; carry table
    allf = pos.copy()
    allf["bucket"] = allf.regime == "Bearish_HighIV"
    out = []
    for r in allf.itertuples():
        v5 = overlay_pnl(r, q, qidx, by_date, close, 0.10, "B", days)
        v3 = overlay_pnl(r, q, qidx, by_date, close, 0.10, "C", days)
        out.append(dict(date=r.entry_date, bucket=r.bucket, vix=r.vix_on_entry,
                        r5=v5[0] / v5[1] if v5[1] else np.nan, r3=v3[0] / v3[1] if v3[1] else np.nan))
    O = pd.DataFrame(out)
    hi = O.vix >= 20
    print("\n## control: overlay return on its own premium (5-delta same expiry, held; 3-delta ~60 DTE, 20 sessions)")
    for lab, m in (("bucket Fridays", O.bucket), ("NON-bucket, VIX >= 20", ~O.bucket & hi), ("all VIX >= 20", hi),
                   ("all VIX < 20", ~hi)):
        x = O[m]
        print(f"{lab:24s} n {len(x):4d} | 5-delta {x.r5.mean():+.2%} (win {(x.r5 > 0).mean():.0%}) | "
              f"3-delta 60d {x.r3.mean():+.2%} (win {(x.r3 > 0).mean():.0%})")
    A.to_csv(REPO / "data/studies/logs/spy_tail_overlay_trades.csv", index=False)


if __name__ == "__main__":
    real = sys.stdout
    sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(open(LOG).read())
