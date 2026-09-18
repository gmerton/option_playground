#!/usr/bin/env python3
"""
Step 2 of the long-call project: expiry x strike grid on real quotes (2026-09-16).

Every Friday, for each ticker, buy one call at each (DTE target, delta target) cell and hold to expiry.
  entry  = mid + 25% of that leg's bid-ask + $0.0065/sh (house model)
  settle = max(S_T - K, 0), with S_T from put-call PARITY on the expiry date, on the same unadjusted basis as the
           strikes. Parity is computed from near-ATM strikes quoted on BOTH sides -- it needs no expiry-day chain
           row, which is what makes the delta-filtered pull safe here (see calendar_path_study.md erratum).

Usage: PYTHONPATH=src .venv/bin/python3 run_call_grid_sim.py [--out data/cache/call_grid/results.parquet]
"""
from __future__ import annotations
import argparse, glob, sys
from pathlib import Path
import numpy as np, pandas as pd

C = Path("data/cache/call_grid"); SLIP, COMM = 0.25, 0.0065
DTES = [7, 14, 21, 30, 45]; DTOL = {7: 3, 14: 3, 21: 3, 30: 4, 45: 5}
DELTAS = [0.65, 0.50, 0.40, 0.30, 0.20]


def parity_spot(d: pd.DataFrame) -> pd.Series:
    """S = K + C - P at the strike where |C-P| is smallest, per ticker-day. One value per trading day."""
    c = d[d.cp == "C"][["ticker", "trade_date", "expiry", "strike", "mid"]]
    p = d[d.cp == "P"][["ticker", "trade_date", "expiry", "strike", "mid"]]
    m = c.merge(p, on=["ticker", "trade_date", "expiry", "strike"], suffixes=("_c", "_p"))
    if m.empty: return pd.Series(dtype=float)
    m["gap"] = (m.mid_c - m.mid_p).abs()
    b = m.sort_values("gap").drop_duplicates(["ticker", "trade_date"])
    return (b.strike + b.mid_c - b.mid_p).set_axis(pd.MultiIndex.from_arrays([b.ticker, b.trade_date]))


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(C / "results.parquet")); a = ap.parse_args()
    files = sorted(glob.glob(str(C / "grid_*.parquet")))
    spots, entries = [], []
    for f in files:
        d = pd.read_parquet(f)
        d["trade_date"] = pd.to_datetime(d.trade_date); d["expiry"] = pd.to_datetime(d.expiry)
        d["mid"] = (d.bid + d.ask) / 2; d["ba"] = d.ask - d.bid
        d["dte"] = (d.expiry - d.trade_date).dt.days
        spots.append(parity_spot(d))
        # entries: Fridays only, calls only
        e = d[(d.trade_date.dt.weekday == 4) & (d.cp == "C") & (d.dte > 0)]
        for td in DTES:
            tol = DTOL[td]
            x = e[(e.dte - td).abs() <= tol].copy()
            if x.empty: continue
            # one expiry per ticker-Friday: the closest to the DTE target
            x["derr"] = (x.dte - td).abs()
            best = x.sort_values("derr").drop_duplicates(["ticker", "trade_date"])[["ticker", "trade_date", "expiry"]]
            x = x.merge(best, on=["ticker", "trade_date", "expiry"])
            for dl in DELTAS:
                y = x.assign(e=(x.delta - dl).abs()).sort_values("e").drop_duplicates(["ticker", "trade_date"])
                y = y[y.e <= 0.08]
                if y.empty: continue
                entries.append(y.assign(dte_target=td, delta_target=dl)[
                    ["ticker", "trade_date", "expiry", "strike", "mid", "ba", "delta", "dte", "bid_iv", "ask_iv",
                     "open_interest", "dte_target", "delta_target"]])
        print(f"  {Path(f).name}: {sum(len(z) for z in entries):,} entries so far", flush=True)
        del d
    S = pd.concat(spots); S = S[~S.index.duplicated()]
    E = pd.concat(entries, ignore_index=True)
    E["cost"] = E.mid + SLIP * E.ba + COMM
    E["spot"] = S.reindex(pd.MultiIndex.from_arrays([E.ticker, E.trade_date])).values
    E["ST"] = S.reindex(pd.MultiIndex.from_arrays([E.ticker, E.expiry])).values
    E = E.dropna(subset=["ST", "spot"])
    E = E[E.cost > 0.05]
    E["payoff"] = (E.ST - E.strike).clip(lower=0)
    E["roc"] = 100 * (E.payoff - E.cost) / E.cost
    E["move_pct"] = 100 * (E.ST / E.spot - 1)
    E.to_parquet(a.out, index=False)
    print(f"wrote {a.out}: {len(E):,} call entries, {E.ticker.nunique()} tickers, "
          f"{E.trade_date.min().date()} -> {E.trade_date.max().date()}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
