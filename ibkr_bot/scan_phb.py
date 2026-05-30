#!/usr/bin/env python3
"""
Batch-scan a list of symbols through the Power Hour Breakout (PHB) lens.

Fetches today's 1-min bars for each symbol (reusing a cached CSV in data/ if one
exists for the date), runs the PHB card quietly, and prints one ranked row per
symbol labelled STRONG / weak / COUNTER. Counter-examples (coiled midday but
faded or no volume surge) are exactly what we need to measure the false-positive
rate -- they sort to the bottom.

Usage:
  .venv/bin/python3 ibkr_bot/scan_phb.py CIEN CRDO AVGO NVDA TSLA
  .venv/bin/python3 ibkr_bot/scan_phb.py "CIEN, CRDO, AVGO, NVDA"
"""

from __future__ import annotations

import os
import sys

import pandas as pd
from ib_async import Stock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from characterize import phb_card  # noqa: E402
from conn import connect_ib  # noqa: E402
from fetch_intraday import DATA_DIR, _bars_to_df  # noqa: E402


def _parse_symbols(argv: list[str]) -> list[str]:
    raw = " ".join(argv).replace(",", " ")
    return [s.upper() for s in raw.split() if s.strip()]


def _get_bars(ib, sym: str) -> pd.DataFrame | None:
    """Latest cached CSV for the symbol, else fetch 1 day from IBKR and cache it."""
    cached = sorted(
        f for f in os.listdir(DATA_DIR)
        if f.startswith(f"{sym}_") and f.endswith("_1min.csv")
    ) if os.path.isdir(DATA_DIR) else []
    if cached:
        return pd.read_csv(os.path.join(DATA_DIR, cached[-1]), parse_dates=["time"])
    contract = Stock(sym, "SMART", "USD")
    if not ib.qualifyContracts(contract):
        return None
    bars = ib.reqHistoricalData(
        contract, endDateTime="", durationStr="1 D", barSizeSetting="1 min",
        whatToShow="TRADES", useRTH=True, keepUpToDate=False,
    )
    if not bars:
        return None
    df = _bars_to_df(bars)
    day = df["time"].dt.date.iloc[-1]
    df.to_csv(os.path.join(DATA_DIR, f"{sym}_{day}_1min.csv"), index=False)
    return df


def main() -> int:
    symbols = _parse_symbols(sys.argv[1:])
    if not symbols:
        print("usage: scan_phb.py SYM [SYM ...]")
        return 1

    os.makedirs(DATA_DIR, exist_ok=True)
    ib = connect_ib(client_id=int(os.environ.get("IB_CLIENT_ID", "14")))
    print(f"OK Connected (paper {ib.managedAccounts()}). Scanning {len(symbols)} symbols.\n")

    rows = []
    for sym in symbols:
        try:
            df = _get_bars(ib, sym)
        except Exception as e:
            print(f"  x {sym}: {e}")
            continue
        if df is None or df.empty:
            print(f"  x {sym}: no data")
            continue
        rows.append(phb_card(sym, df, verbose=False))
    ib.disconnect()

    if not rows:
        return 1
    order = {"STRONG": 0, "weak": 1, "COUNTER": 2}
    rows.sort(key=lambda m: (order[m["label"]], -m["close_pos_in_range_pct"]))

    hdr = (f"\n{'sym':<6}{'label':>8}{'base_w%':>8}{'vsVWAP':>8}{'pwr_volx':>9}"
           f"{'breakout':>10}{'%ahead':>8}{'clo%rng':>8}{'offHOD%':>8}")
    print(hdr); print("-" * len(hdr))
    for m in rows:
        bt = m["breakout_time"] or "--"
        ah = "--" if m["ahead_to_late_high_pct"] is None else f"{m['ahead_to_late_high_pct']}"
        print(f"{m['symbol']:<6}{m['label']:>8}{m['base_width_pct']:>8.1f}{m['coil_vs_vwap_pct']:>+8.1f}"
              f"{m['power_vol_x']:>9.1f}{bt:>10}{ah:>8}{m['close_pos_in_range_pct']:>8}{m['close_off_hod_pct']:>+8.1f}")

    n = {k: sum(r["label"] == k for r in rows) for k in order}
    print(f"\n{n['STRONG']} STRONG, {n['weak']} weak, {n['COUNTER']} counter-example(s). "
          f"Run characterize.py <SYM> --phb for any one's full card.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
