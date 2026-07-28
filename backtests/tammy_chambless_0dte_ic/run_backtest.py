#!/usr/bin/env python3
"""
Tammy Chambless MEIC — SKELETON backtest (honest floor, NOT the real strategy).

WHY THIS IS A SKELETON, NOT MEIC
--------------------------------
Her strategy is 0DTE, 6 intraday entries/day, with intraday PER-SIDE stops at ~1x net
(≈2x credit). Our data (silver.options_daily_v3) is EOD-only: a 0DTE option's sole row is
its price at the close = expiration ≈ intrinsic, so the intraday ENTRY CREDIT and intraday
STOP-OUTS are both unobservable. A faithful MEIC backtest is therefore impossible here.

What we CAN test: the raw volatility-risk-premium (VRP) edge of the same SHORT-DATED SPX
iron-condor family, using a 1DTE proxy with REAL EOD entry prices:
  - Enter at trade_date close on a contract expiring the NEXT trading day (dte==1).
  - Settle at expiry SPX close (cash-settled; winners expire, no closing fill).
This transfers the structure (a 0.12Δ / 50-wide 1DTE net credit ≈ $1.5/side ≈ her $1-1.75)
but differs from MEIC in ways to keep in mind:
  * 1DTE overnight hold vs her 0DTE intraday  → proxy carries gap risk MEIC avoids.
  * single entry/day vs her 6 staggered       → proxy has HIGHER variance (no averaging).
  * held-to-expiry vs her intraday per-side stops → see the two scenarios below.

TWO SCENARIOS BRACKET THE TRUTH
-------------------------------
  A. HELD-TO-EXPIRY, NO STOP  → each side can lose up to (width - credit). Pessimistic
     lower bound: a "naked" short IC with no protection. If A is deeply negative, MEIC's
     edge IS the stop, not the premium.
  B. LOSS CAPPED AT 2x CREDIT/side → crude proxy for the per-side stop's effect on the tail.
     OPTIMISTIC upper bound: it caps bad days but does NOT charge for the whipsaw stop-outs
     on days that would have reverted to a win (which MEIC does suffer). MEIC's true result
     sits between A and B; her live ~20.7% CAR is the ground truth to sanity-check against.

Costs: winners cash-settle (no exit fill); only the 4 opening legs pay slippage. Modeled as
`--slip` per leg (default $0.075) + negligible commission. (MEIC pays MORE — it also pays exit
slippage on every stopped side — so this UNDERSTATES MEIC costs, which is fine: it's a floor.)

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 \
    backtests/tammy_chambless_0dte_ic/run_backtest.py [--refresh] [--width 50] [--slip 0.075]
"""
from __future__ import annotations

import argparse
import pathlib
from datetime import date, timedelta

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).parent
CACHE = HERE / "spx_dte2.parquet"

START = date(2016, 1, 1)
END   = date(2025, 9, 5)          # matches Tammy's backtest window end
SHORT_DELTAS = [0.10, 0.12, 0.15, 0.20]
DEFAULT_WIDTH = 50                 # her "50-60 wide typical"
HER_WINDOW = (date(2023, 1, 1), date(2025, 9, 5))


def pull() -> pd.DataFrame:
    from lib.athena_lib import athena
    sql = f"""
    SELECT trade_date, expiry, strike,
           CAST((bid + ask)/2.0 AS DOUBLE) AS mid,
           CAST(delta AS DOUBLE) AS delta, cp,
           date_diff('day', trade_date, expiry) AS dte
    FROM "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"."silver"."options_daily_v3"
    WHERE ticker = 'SPX'
      AND trade_date >= TIMESTAMP '{START} 00:00:00'
      AND trade_date <= TIMESTAMP '{END} 23:59:59'
      AND bid > 0 AND delta IS NOT NULL
      AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 2
    ORDER BY trade_date, expiry, cp, strike
    """
    print("Querying Athena for SPX dte 0-2 (all deltas, bid>0) ...")
    df = athena(sql)
    print(f"  {len(df):,} rows")
    return df


def load(refresh: bool) -> pd.DataFrame:
    if CACHE.exists() and not refresh:
        df = pd.read_parquet(CACHE)
        print(f"Loaded cache {CACHE}  ({len(df):,} rows)")
    else:
        df = pull()
        df.to_parquet(CACHE, index=False)
        print(f"  cached -> {CACHE}")
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    df["strike"]     = df["strike"].astype(float)
    df["mid"]        = df["mid"].astype(float)
    df["delta"]      = df["delta"].astype(float)
    df["dte"]        = df["dte"].astype(int)
    return df


def load_spot() -> dict:
    import yfinance as yf
    raw = yf.download("^GSPC", start=str(START), end=str(END + timedelta(days=5)),
                      progress=False, auto_adjust=True)
    raw.index = pd.to_datetime(raw.index).date
    return dict(zip(raw.index, raw["Close"].squeeze().astype(float).values))


def nearest_by_delta(chain: pd.DataFrame, cp: str, target: float):
    sub = chain[chain["cp"] == cp].copy()
    if sub.empty:
        return None
    sub["_e"] = (sub["delta"].abs() - target).abs()
    r = sub.loc[sub["_e"].idxmin()]
    if r["_e"] > 0.06:      # no strike near the target delta
        return None
    return r


def strike_at_or_beyond(chain: pd.DataFrame, cp: str, target_strike: float):
    """Wing: the option at the strike closest to target (short_strike -/+ width)."""
    sub = chain[chain["cp"] == cp].copy()
    if sub.empty:
        return None
    sub["_e"] = (sub["strike"] - target_strike).abs()
    r = sub.loc[sub["_e"].idxmin()]
    if r["_e"] > 15:        # no strike within 15pts of the desired wing
        return None
    return r


def run(df: pd.DataFrame, spot: dict, width: int, slip: float):
    # 1DTE entries: contract expiring the next trading day
    entries = df[df["dte"] == 1]
    rows = []
    for (td, exp), chain in entries.groupby(["trade_date", "expiry"]):
        settle = spot.get(exp)
        if settle is None:
            continue
        cost = 4 * slip                       # 4 opening legs
        for d in SHORT_DELTAS:
            sp = nearest_by_delta(chain, "P", d)   # short put
            sc = nearest_by_delta(chain, "C", d)   # short call
            if sp is None or sc is None:
                continue
            lp = strike_at_or_beyond(chain, "P", sp["strike"] - width)  # long put wing
            lc = strike_at_or_beyond(chain, "C", sc["strike"] + width)  # long call wing
            if lp is None or lc is None:
                continue
            put_w  = sp["strike"] - lp["strike"]
            call_w = lc["strike"] - sc["strike"]
            if put_w <= 0 or call_w <= 0:
                continue
            put_cr  = sp["mid"] - lp["mid"]       # per-side net credit
            call_cr = sc["mid"] - lc["mid"]
            net_cr  = put_cr + call_cr
            if put_cr <= 0 or call_cr <= 0:
                continue

            # intrinsic loss at settlement, capped at wing width
            put_loss  = min(max(0.0, sp["strike"] - settle), put_w)
            call_loss = min(max(0.0, settle - sc["strike"]), call_w)

            # Scenario A: held to expiry, no stop
            pnl_A = net_cr - put_loss - call_loss - cost
            max_loss_A = max(put_w, call_w) - net_cr

            # Scenario B: per-side loss capped at 2x that side's credit (stop proxy)
            put_loss_B  = min(put_loss,  2 * put_cr)
            call_loss_B = min(call_loss, 2 * call_cr)
            pnl_B = net_cr - put_loss_B - call_loss_B - cost

            rows.append(dict(
                trade_date=td, expiry=exp, year=td.year, short_delta=d,
                settle=settle, sp=sp["strike"], sc=sc["strike"],
                put_cr=put_cr, call_cr=call_cr, net_cr=net_cr,
                put_w=put_w, call_w=call_w,
                pnl_A=pnl_A, max_loss_A=max_loss_A, win_A=pnl_A > 0,
                pnl_B=pnl_B, win_B=pnl_B > 0,
                roc_A=pnl_A / max_loss_A if max_loss_A > 0 else np.nan,
            ))
    return pd.DataFrame(rows)


def report(res: pd.DataFrame, width: int, slip: float):
    def block(sub, label):
        n = len(sub)
        if n == 0:
            print(f"  {label}: no trades"); return
        wa, wb = sub["win_A"].mean()*100, sub["win_B"].mean()*100
        pa, pb = sub["pnl_A"].mean(), sub["pnl_B"].mean()
        sa, sb = sub["pnl_A"].sum(), sub["pnl_B"].sum()
        cr = sub["net_cr"].mean()
        print(f"  {label:>16}  n={n:>4}  cr=${cr:4.2f}  "
              f"|A no-stop:  win={wa:4.1f}% avgPnL=${pa:+5.2f} sum=${sa:+8.1f}  "
              f"|B 2x-cap:  win={wb:4.1f}% avgPnL=${pb:+5.2f} sum=${sb:+8.1f}")

    print("\n" + "="*140)
    print(f"  SPX 1DTE IRON CONDOR — MEIC SKELETON (held-to-expiry floor)   width={width}  slip=${slip}/leg (4 legs)")
    print(f"  A = no stop (pessimistic) | B = per-side loss capped at 2x credit (optimistic stop proxy)")
    print(f"  PnL in SPX points/1-lot ($ = points x100). NOT MEIC: 1DTE overnight, single daily entry, no intraday stops.")
    print("="*140)

    for d in SHORT_DELTAS:
        print(f"\n  ── Short Δ ≈ {d:.2f} ──────────────────────────────────────────")
        sub = res[res["short_delta"] == d]
        for yr, g in sub.groupby("year"):
            block(g, str(yr))
        block(sub, "ALL 2016-2025")
        block(sub[(sub["trade_date"] >= HER_WINDOW[0])], "HER 2023-25")

    print("\n" + "="*140)
    print("  READ: Scenario A tests whether raw premium beats the held-to-expiry tail (is there ANY VRP edge).")
    print("        Scenario B shows what per-side loss-capping (the MEIC stop) does to that same book.")
    print("        MEIC's true EV sits BETWEEN A and B; her live ~20.7% CAR is the external check.")
    print("="*140)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    ap.add_argument("--slip", type=float, default=0.075)
    a = ap.parse_args()
    df = load(a.refresh)
    print("Downloading SPX spot (^GSPC) ...")
    spot = load_spot()
    res = run(df, spot, a.width, a.slip)
    if res.empty:
        print("No trades produced."); return
    res.to_csv(HERE / "results.csv", index=False)
    report(res, a.width, a.slip)
    print(f"\n  wrote {HERE/'results.csv'}  ({len(res)} trades)")


if __name__ == "__main__":
    main()
