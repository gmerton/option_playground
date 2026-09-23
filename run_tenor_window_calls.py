#!/usr/bin/env python3
"""
TENOR-WINDOW LONG CALL: buy ~90 DTE and exit with ~60 left vs buy ~60 exit ~30 vs buy ~30 hold to expiry
(pre-registered 2026-09-23; Cashflow Academy claim 5a, `data/cashflow_academy/2026-06-03_brutal_options_advice_review.md`).

THE CLAIM [16:05]: "Buying a 3-month option and selling it when it has 2 months left is much, much better than buying
a 2-month option and selling it with 1 month left, which is still better than buying a 1-month option and holding it
to expiration." Mechanism offered: theta is steepest in the last 30 days.

DESIGN: hold the CALENDAR WINDOW fixed and move only the tenor.
  universe  data/watchlist/straddle_pool_323.txt, Friday entries 2018-01 -> 2026-01 (bid/ask ends ~Mar 2026)
  C (control, "the beginner")   ATM call, expiry 21-35 DTE (closest to 28), held to expiry, settled at intrinsic
                                against the CHAIN-implied raw spot on the expiry date (never an adjusted panel)
  B                             ATM call with ~30 DTE REMAINING on C's expiry date (20-44), sold that day
  A (the claim)                 ATM call with ~60 DTE REMAINING on C's expiry date (45-80), sold that day
  All three enter the same Friday and exit the same day (C's expiry) -> identical underlying path; the arms differ
  only in tenor. ATM = call delta closest to 0.50 within [0.40, 0.60]. Paired: a (ticker, Friday) enters only if all
  three legs exist and each leg's entry spread <= 20% of mid (one common, tradeable population).

FILLS: house model (`costs.py`): mid +/- 25% of the leg's quoted bid-ask + $0.0065/share each traded side. The EXIT
uses the exit day's real bid-ask (we have it), not the entry proxy. C pays no exit cost (settles). Also reported:
gross at mid, and full cross (ask in, bid out).

METRIC: P&L per share as % of entry spot. The three legs carry ~equal delta (~0.50), so this is P&L per unit of
directional exposure and the theta/vega difference shows up directly. Return on premium is reported but is NOT the
comparison: a 30-DTE ATM call costs ~half a 90-DTE one, so % of premium mostly measures leverage.
Secondary: delta-adjusted P&L = pnl - delta_entry * (S_exit - S_entry), the non-directional bleed.

PRIMARY: A - C, house fills, % of spot, paired, Newey-West t on the weekly entry-date series (lag 4: the 4-week holds
overlap). PASS = |t| >= 3, both chronological halves the same sign, and no single year carrying it.
Comparisons: A-C (primary), B-C, A-B -> Sidak for 3 at 5% two-sided |t| >= 2.39; the house 3.0 governs.

PRIOR: the claim is mechanically right about theta per share (ATM theta ~ 1/sqrt(T)), but theta is the price of
gamma, and the net bleed of a long option is ~vega-weighted (implied - realised). The VRP panel finds the premium at
10d (+1.75vp) and NOTHING at 30d/90d -> A should bleed less than C per unit delta. Against it: A pays an exit spread C
does not, and carries ~1.7x the vega through 4 weeks of IV noise. Guess: A beats C at MID by a small amount;
at house fills ~55/45 that A still wins, t < 3. No prior on B.

Usage: AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 -u run_tenor_window_calls.py \
         2>&1 | tee data/studies/logs/tenor_window_calls.log
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from lib.athena_lib import athena
from lib.constants import S3TABLES_CATALOG, DB, TABLE
from lib.studies.chain_spot import implied_spot
from lib.studies.costs import COMMISSION_PER_LEG, SLIPPAGE_FRAC

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
CACHE = Path("data/cache/tenor_window"); CACHE.mkdir(parents=True, exist_ok=True)
FQ = f'"{S3TABLES_CATALOG}"."{DB}"."{TABLE}"'
END = "2026-02-27"
YEARS = range(2018, 2027)
MAX_SPREAD = 0.20
ARMS = {"C": (21, 35, 28), "B": (20, 44, 30), "A": (45, 80, 60)}   # C: entry DTE; A/B: DTE remaining at exit
SPLIT_NOTE = "halves = median entry date"


def tickers() -> list[str]:
    return [l.strip().upper() for l in open("data/watchlist/straddle_pool_323.txt") if l.strip()]


def pull_entries() -> pd.DataFrame:
    tsql = ",".join(f"'{t}'" for t in tickers())
    out = []
    for yr in YEARS:
        p = CACHE / f"entry_{yr}.parquet"
        if not p.exists():
            lo, hi = f"{yr}-01-01", min(f"{yr}-12-31", "2026-01-30")
            if lo > hi: break
            t0 = time.time()
            d = athena(f"""
                SELECT ticker, trade_date, expiry, cp, strike, bid, ask, bid_iv, ask_iv, delta
                FROM {FQ}
                WHERE ticker IN ({tsql})
                  AND trade_date BETWEEN DATE '{lo}' AND DATE '{hi}'
                  AND day_of_week(trade_date) = 5
                  AND date_diff('day', trade_date, expiry) BETWEEN 14 AND 125
                  AND bid > 0 AND ask > 0
                  AND ((cp = 'C' AND delta BETWEEN 0.35 AND 0.65) OR (cp = 'P' AND delta BETWEEN -0.65 AND -0.35))""")
            d.to_parquet(p, index=False)
            print(f"  entry {yr}: {len(d):,} rows {time.time() - t0:.0f}s", flush=True)
        out.append(pd.read_parquet(p))
    d = pd.concat(out, ignore_index=True)
    for c in ("trade_date", "expiry"): d[c] = pd.to_datetime(d[c])
    return d.drop_duplicates(["ticker", "trade_date", "expiry", "cp", "strike"])


def select(E: pd.DataFrame) -> pd.DataFrame:
    E = E.copy()
    E["dte"] = (E.expiry - E.trade_date).dt.days
    E["iv"] = (E.bid_iv + E.ask_iv) / 2
    E["mid"] = (E.bid + E.ask) / 2
    spot = E[E.iv > 0].assign(s=lambda x: implied_spot(x.strike, x.delta, x.iv, x.dte, x.cp)) \
        .groupby(["ticker", "trade_date"]).s.median().rename("s0")
    C = E[(E.cp == "C") & E.delta.between(0.40, 0.60)].copy()
    C["dd"] = (C.delta - 0.50).abs()
    atm = C.sort_values("dd").drop_duplicates(["ticker", "trade_date", "expiry"])     # ATM strike per expiry
    lo, hi, tgt = ARMS["C"]
    c = atm[atm.dte.between(lo, hi)].assign(k=lambda x: (x.dte - tgt).abs()).sort_values(["k", "dd"]) \
        .drop_duplicates(["ticker", "trade_date"]).drop(columns="k")
    c = c.assign(x_date=c.expiry)
    legs = {"C": c}
    base = c[["ticker", "trade_date", "x_date"]]
    for arm in ("B", "A"):
        lo, hi, tgt = ARMS[arm]
        m = atm.merge(base, on=["ticker", "trade_date"])
        m["rem"] = (m.expiry - m.x_date).dt.days
        m = m[m.rem.between(lo, hi)].assign(k=lambda x: (x.rem - tgt).abs()).sort_values(["k", "dd"]) \
            .drop_duplicates(["ticker", "trade_date"]).drop(columns=["k", "rem"])
        legs[arm] = m
    keep = ["ticker", "trade_date", "x_date", "expiry", "strike", "bid", "ask", "mid", "delta", "iv", "dte"]
    W = None
    for arm, L in legs.items():
        L = L[keep].rename(columns={c_: f"{c_}_{arm}" for c_ in keep[3:]})
        W = L if W is None else W.merge(L, on=["ticker", "trade_date", "x_date"])
    W = W.merge(spot, left_on=["ticker", "trade_date"], right_index=True)
    n0 = len(W)
    for arm in ARMS:
        W = W[(W[f"ask_{arm}"] - W[f"bid_{arm}"]) / W[f"mid_{arm}"] <= MAX_SPREAD]
    print(f"paired (ticker, Friday) with all 3 legs: {n0:,}; after <= {MAX_SPREAD:.0%} spread gate: {len(W):,}", flush=True)
    return W.reset_index(drop=True)


def pull_exits(W: pd.DataFrame) -> pd.DataFrame:
    out = []
    W = W.assign(yr=W.x_date.dt.year)
    for yr, g in W.groupby("yr"):
        p = CACHE / f"exit_{yr}.parquet"
        if not p.exists():
            t0 = time.time()
            tsql = ",".join(f"'{t}'" for t in sorted(g.ticker.unique()))
            dsql = ",".join(f"DATE '{d:%Y-%m-%d}'" for d in sorted(g.x_date.unique()))
            exps = pd.concat([g[f"expiry_{a}"] for a in ARMS]).unique()
            esql = ",".join(f"DATE '{pd.Timestamp(d):%Y-%m-%d}'" for d in sorted(exps))
            d = athena(f"""
                SELECT ticker, trade_date, expiry, cp, strike, bid, ask, bid_iv, ask_iv, delta
                FROM {FQ}
                WHERE ticker IN ({tsql}) AND trade_date IN ({dsql})
                  AND ( (cp = 'C' AND expiry IN ({esql}))
                     OR (date_diff('day', trade_date, expiry) BETWEEN 5 AND 125
                         AND abs(delta) BETWEEN 0.25 AND 0.75 AND bid > 0 AND ask > 0) )""")
            d.to_parquet(p, index=False)
            print(f"  exit {yr}: {len(d):,} rows {time.time() - t0:.0f}s", flush=True)
        out.append(pd.read_parquet(p))
    d = pd.concat(out, ignore_index=True)
    for c in ("trade_date", "expiry"): d[c] = pd.to_datetime(d[c])
    return d.drop_duplicates(["ticker", "trade_date", "expiry", "cp", "strike"])


def score(W: pd.DataFrame, X: pd.DataFrame) -> pd.DataFrame:
    X = X.copy()
    X["dte"] = (X.expiry - X.trade_date).dt.days
    X["iv"] = (X.bid_iv + X.ask_iv) / 2
    sp = X[(X.iv > 0) & (X.dte >= 5) & X.delta.abs().between(0.25, 0.75) & (X.bid > 0)]
    s1 = sp.assign(s=lambda x: implied_spot(x.strike, x.delta, x.iv, x.dte, x.cp)) \
        .groupby(["ticker", "trade_date"]).s.median().rename("s1")
    W = W.merge(s1, left_on=["ticker", "x_date"], right_index=True, how="left")
    q = X[X.cp == "C"][["ticker", "trade_date", "expiry", "strike", "bid", "ask"]]
    for arm in ("A", "B", "C"):
        W = W.merge(q.rename(columns={"trade_date": "x_date", "expiry": f"expiry_{arm}", "strike": f"strike_{arm}",
                                      "bid": f"xbid_{arm}", "ask": f"xask_{arm}"}),
                    on=["ticker", "x_date", f"expiry_{arm}", f"strike_{arm}"], how="left")
    print(f"exit spot recovered: {W.s1.notna().mean():.1%}; exit quote found A {W.xbid_A.notna().mean():.1%} "
          f"B {W.xbid_B.notna().mean():.1%}", flush=True)
    # sanity: C's own expiry-day quote vs our intrinsic
    chk = W.dropna(subset=["xbid_C", "s1"])
    chk = chk[chk.xask_C > 0]
    if len(chk):
        intr = (chk.s1 - chk.strike_C).clip(lower=0)
        xm = (chk.xbid_C + chk.xask_C) / 2
        print(f"settlement sanity (C expiry-day mid vs chain-intrinsic, n={len(chk):,}): corr "
              f"{np.corrcoef(intr, xm)[0, 1]:.4f}, median |diff|/spot {((intr - xm).abs() / chk.s0).median():.4%}", flush=True)
    W = W.dropna(subset=["s1", "xbid_A", "xbid_B"])
    W = W[(W.xask_A > 0) & (W.xask_B > 0)]
    # guard: a split between entry and exit breaks the raw-strike comparison
    W = W[(W.s1 / W.s0).between(0.55, 1.8)]
    print(f"scored trades: {len(W):,} ({W.ticker.nunique()} names, {W.trade_date.nunique()} Fridays)", flush=True)
    comm = COMMISSION_PER_LEG
    for arm in ("A", "B", "C"):
        ba = W[f"ask_{arm}"] - W[f"bid_{arm}"]
        W[f"in_mid_{arm}"] = W[f"mid_{arm}"]
        W[f"in_house_{arm}"] = W[f"mid_{arm}"] + SLIPPAGE_FRAC * ba + comm
        W[f"in_cross_{arm}"] = W[f"ask_{arm}"] + comm
        if arm == "C":
            v = (W.s1 - W.strike_C).clip(lower=0)
            W["out_mid_C"] = W["out_house_C"] = W["out_cross_C"] = v
        else:
            xb, xa = W[f"xbid_{arm}"], W[f"xask_{arm}"]
            xm = (xb + xa) / 2
            W[f"out_mid_{arm}"] = xm
            W[f"out_house_{arm}"] = xm - SLIPPAGE_FRAC * (xa - xb) - comm
            W[f"out_cross_{arm}"] = xb - comm
        for f in ("mid", "house", "cross"):
            pnl = W[f"out_{f}_{arm}"] - W[f"in_{f}_{arm}"]
            W[f"sp_{f}_{arm}"] = 100 * pnl / W.s0                              # % of spot
            W[f"rop_{f}_{arm}"] = 100 * pnl / W[f"in_{f}_{arm}"]              # % of premium
            W[f"dadj_{f}_{arm}"] = 100 * (pnl - W[f"delta_{arm}"] * (W.s1 - W.s0)) / W.s0
    return W


def nw_t(x: pd.Series, lag: int = 4) -> float:
    x = x.dropna().to_numpy(); n = len(x)
    if n < 10: return np.nan
    e = x - x.mean(); v = e @ e / n
    for L in range(1, lag + 1):
        v += 2 * (1 - L / (lag + 1)) * (e[L:] @ e[:-L]) / n
    return x.mean() / np.sqrt(v / n)


def summarize(W: pd.DataFrame, col: str) -> dict:
    wk = W.groupby("trade_date")[col].mean()
    med = wk.index[len(wk) // 2]
    yr = W.groupby(W.trade_date.dt.year)[col].mean()
    return {"n": int(W[col].notna().sum()), "mean": W[col].mean(), "median": W[col].median(), "win%": 100 * (W[col] > 0).mean(),
            "nw_t": nw_t(wk), "h1": wk[wk.index < med].mean(), "h2": wk[wk.index >= med].mean(),
            "yrs+": f"{(yr > 0).sum()}/{len(yr)}", "2022": yr.get(2022, np.nan)}


def main() -> int:
    t0 = time.time()
    print("stage 1: entry chains", flush=True)
    W = select(pull_entries())
    print("stage 2: exit marks", flush=True)
    W = score(W, pull_exits(W))
    for f in ("mid", "house", "cross"):
        W[f"AmC_{f}"] = W[f"sp_{f}_A"] - W[f"sp_{f}_C"]
        W[f"BmC_{f}"] = W[f"sp_{f}_B"] - W[f"sp_{f}_C"]
        W[f"AmB_{f}"] = W[f"sp_{f}_A"] - W[f"sp_{f}_B"]
        W[f"dAmC_{f}"] = W[f"dadj_{f}_A"] - W[f"dadj_{f}_C"]
    print(f"\nentry DTE medians: A {W.dte_A.median():.0f}  B {W.dte_B.median():.0f}  C {W.dte_C.median():.0f};  "
          f"remaining at exit: A {(W.expiry_A - W.x_date).dt.days.median():.0f}  B {(W.expiry_B - W.x_date).dt.days.median():.0f};  "
          f"entry delta medians A {W.delta_A.median():.3f} B {W.delta_B.median():.3f} C {W.delta_C.median():.3f}")
    print(f"entry premium % of spot (median): A {100 * (W.mid_A / W.s0).median():.2f}  B {100 * (W.mid_B / W.s0).median():.2f}  "
          f"C {100 * (W.mid_C / W.s0).median():.2f};  entry spread % of mid: A {100 * ((W.ask_A - W.bid_A) / W.mid_A).median():.1f}  "
          f"B {100 * ((W.ask_B - W.bid_B) / W.mid_B).median():.1f}  C {100 * ((W.ask_C - W.bid_C) / W.mid_C).median():.1f}")

    rows = []
    for f in ("mid", "house", "cross"):
        for arm in ("A", "B", "C"):
            rows.append({"fill": f, "series": f"arm {arm} P&L %spot", **summarize(W, f"sp_{f}_{arm}")})
        for d in ("AmC", "BmC", "AmB"):
            rows.append({"fill": f, "series": f"{d[0]} - {d[2]} %spot" + ("  <- PRIMARY" if (d == "AmC" and f == "house") else ""),
                         **summarize(W, f"{d}_{f}")})
        rows.append({"fill": f, "series": "A - C delta-adjusted", **summarize(W, f"dAmC_{f}")})
        for arm in ("A", "B", "C"):
            rows.append({"fill": f, "series": f"arm {arm} % of premium", **summarize(W, f"rop_{f}_{arm}")})
    R = pd.DataFrame(rows)
    print("\n" + "#" * 118 + "\nRESULTS (per share; %spot = P&L / entry spot x 100; NW t on the weekly entry-date series, lag 4; "
          + SPLIT_NOTE + ")\n" + "#" * 118)
    print(R.round(3).to_string(index=False))

    print("\nPER YEAR — A - C and B - C, house fills, %spot")
    py = W.groupby(W.trade_date.dt.year).agg(n=("AmC_house", "size"), AmC=("AmC_house", "mean"), BmC=("BmC_house", "mean"),
                                             A=("sp_house_A", "mean"), B=("sp_house_B", "mean"), C=("sp_house_C", "mean"))
    print(py.round(3).to_string())

    print("\nEXPLORATORY — by entry-spread tercile of the A leg (house, %spot)")
    W["liq"] = pd.qcut((W.ask_A - W.bid_A) / W.mid_A, 3, labels=["tight", "mid", "wide"])
    print(W.groupby("liq", observed=True).agg(n=("AmC_house", "size"), AmC=("AmC_house", "mean"),
                                              AmC_mid=("AmC_mid", "mean"), BmC=("BmC_house", "mean")).round(3).to_string())
    print("\nEXPLORATORY — by the underlying's move over the window (S1/S0 - 1), house, %spot")
    W["mv"] = pd.cut(100 * (W.s1 / W.s0 - 1), [-100, -10, -3, 3, 10, 100], labels=["<-10%", "-10..-3", "flat", "+3..+10", ">+10%"])
    print(W.groupby("mv", observed=True).agg(n=("AmC_house", "size"), A=("sp_house_A", "mean"), B=("sp_house_B", "mean"),
                                             C=("sp_house_C", "mean"), AmC=("AmC_house", "mean")).round(3).to_string())

    out = Path("data/studies/tenor_window_calls_2026-09-23.csv")
    W.drop(columns=["liq", "mv"]).to_csv(out, index=False)
    R.to_csv(out.with_name("tenor_window_calls_summary_2026-09-23.csv"), index=False)
    print(f"\nwrote {out}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
