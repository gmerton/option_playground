#!/usr/bin/env python3
"""
DISCRETIONARY SELECTION ALPHA — measuring the thing every backtest here has been unable to see.

Every result so far tests a MECHANICAL entry. Luk, Minervini and Qullamaggie all describe the
same workflow: a screen throws up 20-50 qualifying names, and they take one to three. If the
edge lives in that choice, no mechanical backtest can find it — it is precisely the step that
gets averaged away when a sim takes every qualifying signal.

`data/martin_luk/trades/observed_trades.jsonl` is 386 dated, directional trades extracted from
64 livestreams (Nov 2025 - Jul 2026). The Minervini day-cache covers 2025-05-19 to 2026-07-22
across 5,302 names — the same window, the full universe. So for once the comparison is
available: how did his ACTUAL picks do against the universe he picked them from, on the same
days, over the same horizons?

Baselines, weakest to strongest:
  UNIVERSE   every name in the cache that day. The "throw a dart" control.
  LIQUID     names with 50d dollar volume >= $10M — his tradeable pool.
  STAGE2     liquid + SMA50>SMA150>SMA200 & close>SMA50 — roughly his screen output.
             (For SHORTS the mirror is used: liquid + close<SMA50 & SMA50<SMA150<SMA200.)

Excess vs STAGE2 is the number that matters: it isolates the CHOICE, holding the screen fixed.

⚠ Interpretation limits, stated up front:
  - 9 months, one trader, one (strong) market period. This is an observation, not a track record.
  - Extracted from video narration, so entry timing is coarse (fill_date at best) and exits are
    mostly unrecorded — this measures SELECTION, not his realized P&L. His actual results depend
    on sizing and exits that are not in this data.
  - `confidence: inferred` rows are the extractor's reading, not his stated words; reported
    separately.
  - Entry is modelled at the fill_date CLOSE, so any intraday edge on the entry day is excluded.
"""
from __future__ import annotations

import json
import sys
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from lib.minervini.scan import load_cache  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)

TRADES = "data/martin_luk/trades/observed_trades.jsonl"
CACHE = "data/cache/minervini_matrix.parquet"
HORIZONS = [1, 3, 5, 10, 20]


def main() -> None:
    close, high, low, dolvol = load_cache(CACHE)
    close = close.sort_index()
    idx = close.index
    dv50 = dolvol.rolling(50, min_periods=20).mean()
    sma = {n: close.rolling(n, min_periods=n).mean() for n in (50, 150, 200)}

    liquid = dv50 >= 10e6
    up = liquid & (close > sma[50]) & (sma[50] > sma[150]) & (sma[150] > sma[200])
    dn = liquid & (close < sma[50]) & (sma[50] < sma[150]) & (sma[150] < sma[200])

    fwd = {h: close.shift(-h) / close - 1.0 for h in HORIZONS}

    rows = [json.loads(l) for l in open(TRADES)]
    recs, skipped = [], {"no_ticker": 0, "no_date": 0}
    for r in rows:
        tkr = r["ticker"]
        d = r.get("fill_date") or r.get("date")
        if tkr not in close.columns:
            skipped["no_ticker"] += 1
            continue
        ts = pd.Timestamp(d)
        pos = idx.searchsorted(ts)
        if pos >= len(idx):
            skipped["no_date"] += 1
            continue
        dt = idx[pos]
        sign = -1.0 if r.get("direction") == "short" else 1.0
        rec = {"date": dt, "ticker": tkr, "dir": r.get("direction"),
               "conf": r.get("confidence"), "action": r.get("action")}
        ok = False
        for h in HORIZONS:
            v = fwd[h].at[dt, tkr]
            if pd.notna(v):
                ok = True
            rec[f"r{h}"] = sign * v
            # baselines, sign-matched to the direction he took
            pool_all = fwd[h].loc[dt]
            rec[f"b_uni{h}"] = sign * pool_all.mean()
            liq = pool_all[liquid.loc[dt].reindex(pool_all.index).fillna(False)]
            rec[f"b_liq{h}"] = sign * liq.mean()
            scr = up.loc[dt] if sign > 0 else dn.loc[dt]
            s = pool_all[scr.reindex(pool_all.index).fillna(False)]
            rec[f"b_scr{h}"] = sign * s.mean()
            rec[f"n_scr{h}"] = int(s.notna().sum())
        if ok:
            recs.append(rec)
        else:
            skipped["no_date"] += 1

    df = pd.DataFrame(recs)
    print(f"observed trades: {len(rows)}   usable: {len(df)}   "
          f"skipped: {skipped['no_ticker']} unknown ticker, {skipped['no_date']} no fwd data")
    print(f"window: {df.date.min().date()} -> {df.date.max().date()}")
    print(f"direction: {df['dir'].value_counts().to_dict()}")
    print(f"confidence: {df['conf'].value_counts().to_dict()}")
    print(f"screen pool on his trade days: median {df.n_scr10.median():.0f} qualifying names")

    def block(sub: pd.DataFrame, label: str) -> None:
        if len(sub) < 15:
            return
        out = {}
        for h in HORIZONS:
            r, bu, bl, bs = (sub[f"r{h}"], sub[f"b_uni{h}"],
                             sub[f"b_liq{h}"], sub[f"b_scr{h}"])
            m = r.notna() & bs.notna()
            ex = (r - bs)[m]
            out[f"{h}d"] = {
                "n": int(m.sum()),
                "his %": 100 * r[m].mean(),
                "universe %": 100 * bu[m].mean(),
                "liquid %": 100 * bl[m].mean(),
                "screen %": 100 * bs[m].mean(),
                "EXCESS vs screen": 100 * ex.mean(),
                "t": ex.mean() / (ex.std(ddof=1) / np.sqrt(len(ex))) if len(ex) > 2 else np.nan,
                "beat screen %": 100 * (ex > 0).mean(),
            }
        print(f"\n  {label}  (n={len(sub)})")
        print(pd.DataFrame(out).T.round(2).to_string())

    print("\n" + "=" * 110)
    print("A.  ALL OBSERVED TRADES")
    print("=" * 110)
    block(df, "all")

    print("\n" + "=" * 110)
    print("B.  BY DIRECTION")
    print("=" * 110)
    for d in ("long", "short"):
        block(df[df["dir"] == d], d)

    print("\n" + "=" * 110)
    print("C.  BY EXTRACTION CONFIDENCE — 'stated' is what he actually said")
    print("=" * 110)
    for c in ("stated", "inferred"):
        block(df[df["conf"] == c], c)

    print("\n" + "=" * 110)
    print("D.  HIGHEST-CONFIDENCE SUBSET: stated + long")
    print("=" * 110)
    block(df[(df["conf"] == "stated") & (df["dir"] == "long")], "stated longs")

    df.to_csv("data/carter_mastering_the_trade/backtests/risk_architecture/luk_alpha.csv",
              index=False)
    print("\nwrote luk_alpha.csv")


if __name__ == "__main__":
    main()
