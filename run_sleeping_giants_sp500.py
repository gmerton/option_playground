#!/usr/bin/env python3
"""
SLEEPING GIANTS on a POINT-IN-TIME S&P 500 universe, vs same-date random S&P LEAPs, + a cheap-IV gate
(pre-registered 2026-09-29, before any run; audit List A #10, audit_top_down_2026-09-25.md; Gabe: "do sleeping giants").

WHY. The original SG backtest (src/lib/sleeping_giants/, MARGINAL) ran on 77 HAND-PICKED large caps; arm B (wait for
the breakout) +94% mean ROC, t 2.76 -- but vs ZERO. Thirteen exits were tried in-sample, the cheap-IV condition was
only a realised-vol proxy, and on 2026-09-27 the same pipeline showed the original TOP arm (+47%) barely beating
random large-cap LEAPs bought the same day (+39%): SG's "edge" may be LEAP beta in a bull market. This fixes the
universe, charges the control, and adds the real IV gate.

UNIVERSE  point-in-time S&P 500: data/sp500_constituents.txt (502 names, 2026-06-21) with the Wikipedia change log
          (data/cache/sp500_changes_wikipedia.csv) reverse-applied for changes effective on/before 2026-06-21. A name
          is eligible on a date only if it was a member that day. Prices: yfinance adjusted OHLC 2008 -> 2025-07 by
          today's/removed ticker; names yfinance cannot return are missing (coverage of member-weeks REPORTED; the
          removed-and-delisted gap is survivorship, shared by the same-date control). Renamed tickers are not mapped
          for v3 (e.g. META was FB before 2022): their LEAP lookups fail symmetrically; failures reported.
DETECTOR  lib.sleeping_giants.detector.analyze, unchanged, point-in-time, weekly (every 5th session), 1,500-bar
          window, 2014-01 -> 2025-06. SG = is_sleeping_giant (all five gates). Episodes: consecutive firings with
          gaps <= 60 calendar days collapse; signal = first firing date.
ARMS      B (PRIMARY, the arm the original t 2.76 came from): entry = first close > the signal-time resistance with
          volume >= its 50-day average, within 180 sessions of the signal (stage-2 rule); no breakout = no trade
          (counted). A (reported): entry on the signal date.
VEHICLE   call nearest 0.40 delta, expiry nearest 315 DTE within 200-450, v3; buy at mid + 25% of spread + $0.0065,
          sell at mid - 25% + $0.0065; EXIT = first quote on/after +180 calendar days (the pre-specified horizon,
          NOT the in-sample arm-then-trail cell); split-artefact rule as in run_quiet_knife_leaps.py.
CONTROL   SAME-DATE: for each SG entry, 3 other S&P members on that date (seed 20260929), not in the SG state that
          week, same LEAP rule and exit. excess = SG ROC - mean(control ROC).
PRIMARY   arm B mean excess ROC; t on entry-date cluster means >= 3, both halves (split 2020-01-01) positive,
          positive in a majority of years. Report median excess, win rate, and the TOP-5 episodes' share of total
          excess (a mean carried by <= 5 episodes is flagged, not certified).
IV GATE   (secondary, not bar-bearing) silver.options_iv_daily call50_iv percentile within the ticker's trailing 252
          sessions at the SIGNAL date; "cheap" = <= 0.25. Report arm-B excess for cheap vs not.
REPORTED  arm A excess; arm B raw ROC vs the original's +94%; underlying stock excess over the same windows;
          ARM+50 / TRAIL-30 (the in-sample best exit) on SG and control from daily marks -- exploratory only.
PRIOR     low-moderate: 9/27 showed TOP ~ random LEAP (+47 vs +39).
Local CPU for the sweep; three Athena queries (LEAP pick, marks, IV), approved by Gabe 2026-09-29.

Run: AWS_PROFILE=clarinut-gmerton AWS_DEFAULT_REGION=us-west-2 PYTHONPATH=src:. .venv/bin/python3 run_sleeping_giants_sp500.py
     (log -> data/studies/logs/sleeping_giants_sp500.log; summary -> data/studies/sleeping_giants_sp500_2026-09-29.log)
"""
from __future__ import annotations

import sys
from pathlib import Path

import awswrangler as wr
import numpy as np
import pandas as pd
import yfinance as yf

import run_quiet_knife_leaps as qk
from lib.constants import S3_OUTPUT, WORKGROUP
from lib.sleeping_giants.detector import analyze

REPO = Path(__file__).resolve().parent
LOG = REPO / "data/studies/logs/sleeping_giants_sp500.log"
SUMMARY = REPO / "data/studies/sleeping_giants_sp500_2026-09-29.log"
OUT = REPO / "data/studies/sleeping_giants_sp500_2026-09-29.csv"
PX_CACHE = REPO / "data/cache/sp500_pit_ohlc_2008_2025.parquet"
START, END, SPLIT, LIST_DATE = "2014-01-01", "2025-06-30", "2020-01-01", pd.Timestamp("2026-06-21")
WINDOW, STEP, GAP_DAYS, BO_WINDOW, N_CTRL, CHEAP = 1500, 5, 60, 180, 3, 0.25


def log(m):
    print(m, file=sys.stderr, flush=True)


def membership() -> tuple[set, list]:
    cur = set(open(REPO / "data/sp500_constituents.txt").read().strip().split(","))
    ch = pd.read_csv(REPO / "data/cache/sp500_changes_wikipedia.csv", header=[0, 1])
    ch.columns = ["date", "add", "add_name", "rem", "rem_name", "reason"]
    ch["date"] = pd.to_datetime(ch.date)
    ch = ch[ch.date <= LIST_DATE].sort_values("date", ascending=False)
    return cur, [(r.date, r.add if isinstance(r.add, str) else None, r.rem if isinstance(r.rem, str) else None)
                 for r in ch.itertuples()]


def members_on(cur: set, changes: list, d: pd.Timestamp) -> set:
    s = set(cur)
    for dt, add, rem in changes:                  # newest first; undo every change effective after d
        if dt <= d:
            break
        if add: s.discard(add)
        if rem: s.add(rem)
    return s


def prices(tickers: list[str]) -> pd.DataFrame:
    if PX_CACHE.exists():
        return pd.read_parquet(PX_CACHE)
    yft = {t: t.replace(".", "-") for t in tickers}
    frames = []
    for k in range(0, len(tickers), 100):
        chunk = tickers[k:k + 100]
        px = yf.download([yft[t] for t in chunk], start="2008-01-01", end="2025-07-15", auto_adjust=True,
                         progress=False, group_by="ticker", threads=True)
        for t in chunk:
            try:
                d = px[yft[t]].dropna(subset=["Close"])
            except KeyError:
                continue
            if len(d):
                frames.append(d[["High", "Low", "Close", "Volume"]].assign(ticker=t).reset_index())
        log(f"  prices {k + len(chunk)}/{len(tickers)}")
    P = pd.concat(frames, ignore_index=True).rename(columns={"Date": "date"})
    P.to_parquet(PX_CACHE, index=False)
    return P


def main():
    cur, changes = membership()
    y13 = pd.Timestamp("2013-01-01")
    ever = sorted(cur | {a for d, a, r in changes if a and d >= y13} | {r for d, a, r in changes if r and d >= y13})
    P = prices(ever)
    have = set(P.ticker.unique())
    log(f"tickers ever-member 2013+: {len(ever)}, with prices: {len(have)}")
    SW = REPO / "data/cache/sleeping_giants_sp500_sweep.parquet"
    rows = []
    for tk, d in ([] if SW.exists() else P.groupby("ticker")):
        d = d.sort_values("date").reset_index(drop=True)
        H, L, C, V, idx = d.High.values, d.Low.values, d.Close.values, d.Volume.values, pd.DatetimeIndex(d.date)
        ev = np.flatnonzero((idx >= START) & (idx <= END))[::STEP]
        for i in ev:
            lo = max(0, i - WINDOW + 1)
            r = analyze(list(H[lo:i + 1]), list(L[lo:i + 1]), list(C[lo:i + 1]))
            if r is None:
                continue
            rows.append(dict(ticker=tk, date=idx[i], sg=bool(r["is_sleeping_giant"]), R=r["resistance"]))
    S = pd.read_parquet(SW) if SW.exists() else pd.DataFrame(rows)
    if not SW.exists():
        S.to_parquet(SW, index=False)
    S["date"] = pd.to_datetime(S.date)
    # point-in-time membership filter (weekly dates)
    mem = {d: members_on(cur, changes, d) for d in pd.DatetimeIndex(sorted(S.date.unique()))}
    S["member"] = [t in mem[d] for t, d in zip(S.ticker, S.date)]
    wk_cov = np.mean([len(mem[d] & have) / max(len(mem[d]), 1) for d in list(mem)[::20]])
    S = S[S.member]
    log(f"detector evals (members only) {len(S):,}; SG weeks {int(S.sg.sum())}; member coverage with prices {wk_cov:.1%}")

    # episodes
    eps = []
    for tk, g in S[S.sg].sort_values("date").groupby("ticker"):
        last = None
        for r in g.itertuples():
            if last is None or (r.date - last).days > GAP_DAYS:
                eps.append(dict(ticker=tk, signal_date=r.date, R=r.R))
            last = r.date
    E = pd.DataFrame(eps)
    # arm B breakout dates
    Pi = {tk: d.set_index("date").sort_index() for tk, d in P.groupby("ticker")}
    bo = []
    for e in E.itertuples():
        d = Pi[e.ticker]; va = d.Volume.rolling(50).mean()
        fwd = d[d.index > e.signal_date].head(BO_WINDOW)
        hit = fwd[(fwd.Close > e.R) & (fwd.Volume >= va.reindex(fwd.index))]
        bo.append(hit.index[0] if len(hit) else pd.NaT)
    E["bo_date"] = bo
    log(f"SG episodes {len(E)} on {E.ticker.nunique()} names; broke out within {BO_WINDOW} sessions: {E.bo_date.notna().mean():.0%}")

    # entry requests with same-date controls
    rng = np.random.default_rng(20260929)
    sg_week = S[S.sg].groupby("date").ticker.apply(set).to_dict()
    wk_dates = pd.DatetimeIndex(sorted(S.date.unique()))
    req = []
    for k, e in E.iterrows():
        for arm, dt in (("A", e.signal_date), ("B", e.bo_date)):
            if pd.isna(dt):
                continue
            wk = wk_dates[wk_dates <= dt][-1]
            pool = sorted((mem[wk] & have) - sg_week.get(wk, set()) - {e.ticker})
            ep = f"{arm}{k}"
            req.append(dict(row_id=ep, arm=arm, role="SG", ep=ep, ticker=e.ticker, entry_date=dt, signal_date=e.signal_date))
            for j, c in enumerate(rng.choice(pool, size=min(N_CTRL, len(pool)), replace=False)):
                req.append(dict(row_id=f"{ep}c{j}", arm=arm, role="CTRL", ep=ep, ticker=c, entry_date=dt, signal_date=e.signal_date))
    R = pd.DataFrame(req)
    # entry dates must be trading days with chains: snap to the actual date (already trading days from prices)
    log(f"LEAP requests {len(R)}")
    Lp = qk.pick_leaps(R)
    M = qk.marks(Lp)
    out = []
    for e in Lp.itertuples():
        m = M[M.row_id == e.row_id]
        p = qk.payoff(e, m)
        if not p:
            continue
        # exploratory ARM+50 / TRAIL-30 on daily mids
        mm = m.sort_values("trade_date"); mid = ((mm.bid + mm.ask) / 2).values
        cost = (e.bid + e.ask) / 2 + qk.SLIP * (e.ask - e.bid) + qk.COMM
        armed, peak, tr = False, 0.0, None
        for k_, x in enumerate(mid):
            if not armed and x >= 1.5 * cost:
                armed = True
            if armed:
                peak = max(peak, x)
                if x <= 0.7 * peak:
                    tr = k_; break
        xi = tr if tr is not None else len(mid) - 1
        spr = (mm.ask - mm.bid).values[xi]
        roc_trail = 100 * (max(mid[xi] - qk.SLIP * spr - qk.COMM, 0) - cost) / cost if len(mid) else np.nan
        out.append(dict(row_id=e.row_id, **p, roc_trail=roc_trail))
    X = R.merge(pd.DataFrame(out), on="row_id", how="inner")
    n_inc = int(X.incomplete.sum()); X = X[~X.incomplete]
    # stock returns
    X["stock"] = [100 * (Pi[t].Close.asof(x) / Pi[t].Close.asof(d) - 1) if t in Pi else np.nan
                  for t, d, x in zip(X.ticker, X.entry_date, X.exit_date)]
    # IV gate at the signal date
    tl = ",".join(f"'{t}'" for t in sorted(X[X.role == "SG"].ticker.unique()))
    iv = wr.athena.read_sql_query(
        f"SELECT ticker, trade_date, call50_iv FROM silver.options_iv_daily WHERE ticker IN ({tl}) "
        f"AND trade_date BETWEEN DATE '2012-06-01' AND DATE '2025-07-31' AND call50_iv IS NOT NULL",
        database="silver", workgroup=WORKGROUP, data_source="AwsDataCatalog", s3_output=S3_OUTPUT, ctas_approach=False)
    iv["trade_date"] = pd.to_datetime(iv.trade_date)
    ivs = {t: g.set_index("trade_date").call50_iv.sort_index() for t, g in iv.groupby("ticker")}

    def ivpct(t, d):
        s = ivs.get(t)
        if s is None: return np.nan
        w = s.loc[:d].iloc[-252:]
        return (w.iloc[:-1] < w.iloc[-1]).mean() if len(w) >= 126 else np.nan
    X["iv_pct"] = [ivpct(t, d) if r == "SG" else np.nan for t, d, r in zip(X.ticker, X.signal_date, X.role)]
    X.to_csv(OUT, index=False)

    lines = ["# Sleeping Giants on a point-in-time S&P 500 (pre-registration in the docstring)",
             f"ever-members 2013+ {len(ever)}; with yfinance prices {len(have)}; member coverage with prices ~{wk_cov:.1%}",
             f"SG episodes {len(E)} / {E.ticker.nunique()} names; arm-B breakouts {int(E.bo_date.notna().sum())}; "
             f"priced LEAPs {len(X)} of {len(R)} requests (split exclusions {n_inc})"]

    def excess(arm, mask=None):
        sg = X[(X.arm == arm) & (X.role == "SG")].set_index("ep")
        if mask is not None:
            sg = sg[mask(sg)]
        ct = X[(X.arm == arm) & (X.role == "CTRL")].groupby("ep")[["roc_net", "stock", "roc_trail"]].mean()
        J = sg.join(ct, rsuffix="_c", how="inner")
        J["ex"] = J.roc_net - J.roc_net_c
        return J

    def report(lab, J, primary=False):
        if len(J) < 5:
            lines.append(f"{lab}: n {len(J)} -- too few"); return None
        g = J.groupby("entry_date").ex.mean()
        t = g.mean() / g.std(ddof=1) * np.sqrt(len(g)) if len(g) > 2 else np.nan
        h = J.entry_date < SPLIT; yr = J.groupby(J.entry_date.dt.year).ex.mean()
        top5 = J.ex.nlargest(5).sum() / J.ex.sum() if J.ex.sum() > 0 else np.nan
        lines.append(f"{lab}: n {len(J)} / {len(g)} dates | SG ROC mean {J.roc_net.mean():+.1f}% median {J.roc_net.median():+.1f}% | "
                     f"ctrl mean {J.roc_net_c.mean():+.1f}% | EXCESS mean {J.ex.mean():+.1f}pp median {J.ex.median():+.1f}pp "
                     f"win {100 * (J.ex > 0).mean():.0f}% t {t:+.2f} halves {J[h].ex.mean():+.1f}/{J[~h].ex.mean():+.1f} "
                     f"yrs+ {(yr > 0).sum()}/{len(yr)} top-5 share {top5:.2f} | stock ex {(J.stock - J.stock_c).mean():+.1f}pp")
        if primary:
            ok = t >= 3 and J[h].ex.mean() > 0 and J[~h].ex.mean() > 0 and (yr > 0).sum() > len(yr) / 2
            lines.append(f"  per year: " + " ".join(f"{y}:{v:+.0f}" for y, v in yr.items()))
            lines.append(f"  PRIMARY BAR: {'PASS' if ok else 'NOT MET'}")
        return J

    JB = report("ARM B (PRIMARY) SG - same-date random S&P LEAP", excess("B"), primary=True)
    report("ARM A SG - control", excess("A"))
    report("ARM B, cheap IV (pct <= 0.25) [secondary]", excess("B", lambda s: s.iv_pct <= CHEAP))
    report("ARM B, not cheap IV", excess("B", lambda s: s.iv_pct > CHEAP))
    if JB is not None:
        lines.append(f"exploratory ARM+50/TRAIL-30: SG {JB.roc_trail.mean():+.1f}% vs ctrl {JB.roc_trail_c.mean():+.1f}% "
                     f"(diff {(JB.roc_trail - JB.roc_trail_c).mean():+.1f}pp)")
        lines.append(f"IV pct known for {JB.iv_pct.notna().mean():.0%} of arm-B SG entries")
    txt = "\n".join(lines)
    print(txt)
    SUMMARY.write_text(txt + "\n")


if __name__ == "__main__":
    real = sys.stdout; sys.stdout = open(LOG, "w")
    try:
        main()
    finally:
        sys.stdout.close(); sys.stdout = real
    print(SUMMARY.read_text() if SUMMARY.exists() else open(LOG).read())
