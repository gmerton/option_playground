#!/usr/bin/env python3
"""
Davis XSP Put Condor vs matched Put Credit Spread — equal-max-risk backtest.

Tests the central claim of data/options_with_davis/strategies/xsp_put_condor.md:
that a 4-leg put condor (wide OTM put credit spread financing a narrow ATM put
debit spread) beats a plain put credit spread at the same max risk.

STRUCTURE (all puts, one expiry)
  A  long  put  ~ATM            (delta nearest -0.50)
  B  short put  A - debit_w     (debit spread, narrow)
  C  short put  at target delta (credit spread short)
  D  long  put  C - credit_w    (credit spread long)
  max profit = debit_w*100 + net_credit      (index between C and B at expiry)
  max loss   = (credit_w - debit_w)*100 - net_credit   (index below D)

MATCHED COMPARISON
  Same short strike C. Long strike D' chosen from the live chain so the credit
  spread's max loss is as close as possible to the condor's. This is Davis's own
  comparison method (equalise max risk, then compare), applied out of sample.

ASSUMPTIONS (he specifies none of these; all are swept or stated)
  - Entry Fridays; expiry Fridays. Hold to expiry, no management (he gives no exits).
  - DTE swept: he never states one. This is the single biggest gap in the source.
  - Widths as % of spot, so they scale across XSP 110 (2010) -> 770 (2026).
    His example: credit_w 1.3% of spot, debit_w 0.13% (narrow) / 0.42% (wide).
  - Settlement from put-call parity on the expiry chain (median over near-ATM
    strikes) — avoids the stale-`last` problem flagged in reference_infra.
  - Pricing at mid, AND with per-leg slippage. The condor has 4 legs vs the
    spread's 2, so mid-pricing structurally flatters it; the cost run is the
    honest comparison.

Usage
-----
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 \\
      run_davis_condor_study.py --start 2010-01-01 --dte 30 --delta 0.15
  ... --sweep            # all DTE x delta x debit-width combinations
"""

from __future__ import annotations

import argparse
from datetime import date

import numpy as np
import pandas as pd

from lib.athena_lib import athena
from lib.constants import DB, TABLE

TICKER = "XSP"
CREDIT_W_PCT = 0.013     # credit-spread width as fraction of spot (his ~10pts/770)
DEBIT_WS     = [1, 3, 5]   # debit spread width in STRIKES below ATM
DTES         = [7, 14, 30, 45]
DELTAS       = [0.10, 0.15, 0.20]
DTE_TOL      = 3
SLIP         = 0.50      # fraction of each leg's bid-ask crossed on entry


# ── Data ──────────────────────────────────────────────────────────────────────

def fetch(start: date, end: date) -> pd.DataFrame:
    """Friday XSP option rows (both cp) with usable quotes, DTE 0..50."""
    sql = f"""
    SELECT trade_date, expiry, strike, cp, bid, ask, delta,
           date_diff('day', trade_date, expiry) AS dte
    FROM "{DB}"."{TABLE}"
    WHERE ticker = '{TICKER}'
      AND trade_date >= TIMESTAMP '{start.isoformat()} 00:00:00'
      AND trade_date <= TIMESTAMP '{end.isoformat()} 00:00:00'
      AND day_of_week(trade_date) = 5
      AND day_of_week(expiry)     = 5
      AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 50
      AND bid > 0 AND ask > 0 AND ask >= bid
    """
    df = athena(sql)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    for c in ("strike", "bid", "ask", "delta"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["mid"] = (df["bid"] + df["ask"]) / 2.0
    return df


def spot_by_date(df: pd.DataFrame) -> dict:
    """Underlying via put-call parity S ~= K + C - P, median over near-ATM strikes."""
    piv = df.pivot_table(index=["trade_date", "expiry", "strike"],
                         columns="cp", values="mid", aggfunc="first")
    if not {"C", "P"}.issubset(piv.columns):
        return {}
    piv = piv.dropna(subset=["C", "P"]).reset_index()
    piv["implied_s"] = piv["strike"] + piv["C"] - piv["P"]
    piv["gap"] = (piv["C"] - piv["P"]).abs()
    out = {}
    for d, g in piv.groupby("trade_date"):
        near = g.nsmallest(12, "gap")
        if len(near) >= 3:
            out[d] = float(near["implied_s"].median())
    return out


# ── Structure construction ────────────────────────────────────────────────────

def _pick(chain: pd.DataFrame, target_strike: float):
    i = (chain["strike"] - target_strike).abs().idxmin()
    return chain.loc[i]


def build(chain: pd.DataFrame, spot: float, dlt: float, debit_w_pct: float):
    """Return (condor, spread) dicts or None."""
    puts = chain[chain["cp"] == "P"].dropna(subset=["delta"]).sort_values("strike")
    if len(puts) < 8:
        return None
    credit_w = spot * CREDIT_W_PCT

    # A: ATM long put; B: short put n_strikes below A (XSP grid is $1/$5, so a
    # percent-of-spot width rounds onto the same strike — count strikes instead).
    A = _pick(puts, spot)
    below = puts[puts["strike"] < A["strike"]]
    n_strikes = int(debit_w_pct)          # reused arg: number of strikes below ATM
    if len(below) < n_strikes:
        return None
    B = below.iloc[-n_strikes]
    # C: short put at target delta; D: long put credit_w below
    ci = (puts["delta"] - (-abs(dlt))).abs().idxmin()
    C = puts.loc[ci]
    D = _pick(puts, C["strike"] - credit_w)
    if not (D["strike"] < C["strike"] < B["strike"]):
        return None

    def px(row, sign, slip):
        """sign +1 = we buy (pay ask-ward), -1 = we sell (receive bid-ward)."""
        half = (row["ask"] - row["bid"]) / 2.0 * slip
        return row["mid"] + sign * half

    out = {}
    for tag, slip in (("mid", 0.0), ("cost", SLIP)):
        # condor: buy A, sell B, sell C, buy D
        net_c = (-px(A, +1, slip) + px(B, -1, slip)
                 + px(C, -1, slip) - px(D, +1, slip)) * 100
        dw = A["strike"] - B["strike"]
        cw = C["strike"] - D["strike"]
        out[f"condor_credit_{tag}"] = net_c
        out[f"condor_maxloss_{tag}"] = (cw - dw) * 100 - net_c

    # Davis's hard rule: the structure must go on for a NET CREDIT, which is the
    # entire basis of the "no risk to the upside" claim. Reject anything else.
    if out["condor_credit_mid"] <= 0:
        return "no_credit"
    out.update(dict(A=A["strike"], B=B["strike"], C=C["strike"], D=D["strike"],
                    debit_w=A["strike"] - B["strike"], credit_w=C["strike"] - D["strike"]))

    # matched credit spread: same short C, pick D' so max loss ~= condor's
    target_ml = out["condor_maxloss_mid"]
    cands = puts[puts["strike"] < C["strike"]].copy()
    if cands.empty:
        return None
    cands["cr_mid"] = (px(C, -1, 0.0) - cands["mid"]) * 100
    cands["ml_mid"] = (C["strike"] - cands["strike"]) * 100 - cands["cr_mid"]
    Dp = cands.loc[(cands["ml_mid"] - target_ml).abs().idxmin()]
    for tag, slip in (("mid", 0.0), ("cost", SLIP)):
        cr = (px(C, -1, slip) - px(Dp, +1, slip)) * 100
        out[f"spread_credit_{tag}"] = cr
        out[f"spread_maxloss_{tag}"] = (C["strike"] - Dp["strike"]) * 100 - cr
    out["Dp"] = Dp["strike"]
    return out


def pnl(s: dict, S: float, tag: str):
    """Expiry P&L for both structures at settlement S."""
    iv = lambda k: max(k - S, 0.0)
    cond_term = (iv(s["A"]) - iv(s["B"]) - iv(s["C"]) + iv(s["Dp"] * 0 + s["D"])) * 100
    cond = s[f"condor_credit_{tag}"] + cond_term
    spr  = s[f"spread_credit_{tag}"] + (-iv(s["C"]) + iv(s["Dp"])) * 100
    return cond, spr


# ── Runner ────────────────────────────────────────────────────────────────────

def run(df: pd.DataFrame, spots: dict, dte: int, dlt: float, debit_w_pct: float):
    rows = []; n_nocredit = 0; n_try = 0
    sub = df[(df["dte"] >= dte - DTE_TOL) & (df["dte"] <= dte + DTE_TOL)]
    for (td, exp), chain in sub.groupby(["trade_date", "expiry"]):
        S0, S1 = spots.get(td), spots.get(exp)
        if S0 is None or S1 is None:
            continue
        n_try += 1
        s = build(chain, S0, dlt, debit_w_pct)
        if s == "no_credit":
            n_nocredit += 1
            continue
        if s is None:
            continue
        r = dict(entry=td, expiry=exp, spot0=S0, spot1=S1,
                 ret_pct=(S1 / S0 - 1) * 100, **{k: v for k, v in s.items()})
        for tag in ("mid", "cost"):
            c, p = pnl(s, S1, tag)
            r[f"condor_pnl_{tag}"], r[f"spread_pnl_{tag}"] = c, p
        rows.append(r)
    out = pd.DataFrame(rows)
    out.attrs["n_nocredit"] = n_nocredit
    out.attrs["n_try"] = n_try
    return out


def summarise(t: pd.DataFrame, label: str):
    if t.empty:
        print(f"  {label:<34} (no trades)")
        return None
    o = {}
    for name, pcol, mcol in (("condor", "condor_pnl", "condor_maxloss"),
                             ("spread", "spread_pnl", "spread_maxloss")):
        for tag in ("mid", "cost"):
            p, m = t[f"{pcol}_{tag}"], t[f"{mcol}_{tag}"]
            o[f"{name}_{tag}"] = dict(
                n=len(t), win=(p > 0).mean() * 100,
                roc=p.sum() / m.sum() * 100,
                mean=p.mean(), med=p.median(),
                worst=p.min(), ml=m.mean())
    return o


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2010-01-01")
    ap.add_argument("--end", default="2026-02-20")
    ap.add_argument("--dte", type=int, default=30)
    ap.add_argument("--delta", type=float, default=0.15)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--csv", action="store_true")
    a = ap.parse_args()
    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)

    print(f"Fetching {TICKER} Friday chains {start} -> {end} ...")
    df = fetch(start, end)
    print(f"  {len(df):,} rows, {df.trade_date.nunique()} Fridays")
    spots = spot_by_date(df)
    print(f"  parity spot on {len(spots)} dates "
          f"(e.g. {sorted(spots)[0]} = {spots[sorted(spots)[0]]:.2f}, "
          f"{sorted(spots)[-1]} = {spots[sorted(spots)[-1]]:.2f})")

    combos = ([(d, k, w) for d in DTES for k in DELTAS for w in DEBIT_WS]
              if a.sweep else [(a.dte, a.delta, w) for w in DEBIT_WS])

    print(f"\n{'DTE':>4} {'Δ':>5} {'debitW':>8} | {'n':>4} "
          f"{'CONDOR roc% (mid/cost)':>24} {'SPREAD roc% (mid/cost)':>24} "
          f"{'cond win%':>10} {'spr win%':>9} {'cond worst$':>12} {'spr worst$':>11}")
    print("-" * 132)
    allrows = []
    for dte, dlt, w in combos:
        t = run(df, spots, dte, dlt, w)
        if t.empty:
            print(f"{dte:>4} {dlt:>5.2f} {w:>6d}st | (none)")
            continue
        t["dte_target"], t["delta_target"], t["debit_w_pct"] = dte, dlt, w
        allrows.append(t)
        o = summarise(t, "")
        print(f"{dte:>4} {dlt:>5.2f} {w:>6d}st | {len(t):>4} "
              f"{o['condor_mid']['roc']:>+11.2f}/{o['condor_cost']['roc']:>+11.2f} "
              f"{o['spread_mid']['roc']:>+11.2f}/{o['spread_cost']['roc']:>+11.2f} "
              f"{o['condor_mid']['win']:>9.1f}% {o['spread_mid']['win']:>8.1f}% "
              f"{o['condor_mid']['worst']:>12,.0f} {o['spread_mid']['worst']:>11,.0f}"
              f"   [rejected no-credit: {t.attrs.get('n_nocredit',0)}/{t.attrs.get('n_try',0)}]")

    if allrows and a.csv:
        out = pd.concat(allrows, ignore_index=True)
        out.to_csv("davis_condor_study.csv", index=False)
        print(f"\nsaved -> davis_condor_study.csv ({len(out):,} rows)")


if __name__ == "__main__":
    main()
