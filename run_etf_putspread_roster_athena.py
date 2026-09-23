#!/usr/bin/env python3
"""
Second pass on the 20-ETF bull put roster: rebuild it from Athena v3 with the LOSSY SYNC FILTER RELAXED.

This is the follow-up `etf_put_spread_exit_rule_2026-09-16.md` asked for and never got ("Before sizing this,
confirm on a more complete source"), and it is also the way to settle the missing-exit question instead of
arguing about it.

THE PROBLEM. `options_cache` (MySQL) is a synced mirror of `silver.options_daily_v3`, but `sync_options_cache`
filters with `bid > 0 AND ask > 0 AND delta IS NOT NULL`, exempting expiry-day rows so settlement survives.
Measured on SPY 2026-09-22: DTE>0 has **0 zero-bid rows out of 7.49M**, while expiry day has **191,578 of
430,014 (44.6%)**. So every quote that decays to a 0.00 bid vanishes from the cache on every day except expiry.

WHY IT MATTERS HERE. `find_put_spread_exits` drops any mark date where EITHER leg is missing. On a bull put
spread the long 0.25d leg reaches a zero bid first, and it does so on the trades that are winning hardest --
so those days are invisible to the 50%-take scan and the trade either takes profit later than it really did
or runs to expiry. 7.7% of trades end up labelled 'missing' and the study then DROPS them.

TWO BIASES, OPPOSITE SIGNS, NET UNKNOWN:
  (a) zero-bid filtering hides marks on WINNERS (this script's target);
  (b) an 'expiry' exit requires a mark on the exact expiry date, and with a 50% take the trades that reach
      expiry are the LOSERS -- so a gap there deletes losers.
The 9/16 doc defends the exclusion by noting the gap rate FALLS as VIX rises. That addresses neither mechanism.

WHAT THIS DOES. Pulls puts for the same 20 ETFs, DTE 0-65, from v3 with NO bid/ask/delta restriction, then runs
the IDENTICAL committed engine and the IDENTICAL filters as run_etf_putspread_roster.py. Same code, same params,
only data completeness differs -- so any change in the headline is attributable to the sync filter alone.

⚠ Dedup ordering matters. The sync breaks ties on (open_interest DESC, bid DESC). Admitting zero-bid rows would
let a high-OI zero-bid row WIN that tie and displace a quoted row, which would silently change ENTRIES too.
This query therefore sorts quoted rows first, so the original winner is preserved wherever one exists and a
zero-bid row is used only when nothing else is available.

⚠ v3 carries bid/ask only through ~Mar 2026 (verified 2026-09-16); the study window ends Feb 2026 entries /
Mar 2026 expiries, so it just fits. Anything later would be prints-only and must not be added.

Run AFTER run_etf_putspread_roster.py, which is the provenance test against the original source.

Usage:
  AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 -u run_etf_putspread_roster_athena.py \
      > data/studies/etf_putspread_roster_athena.log 2>&1
"""
from __future__ import annotations

import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)

REPO = Path(__file__).resolve().parent
OUT = REPO / "data/cache/etf_putspread_roster_athena.parquet"
CHAIN_CACHE = REPO / "data/cache/etf_putspread_chains_v3"      # one parquet per ticker, so a re-run is free
MYSQL_BUILD = REPO / "data/cache/etf_putspread_roster.parquet"  # pass 1, for the A/B

from run_etf_putspread_roster import (  # noqa: E402  - reuse the SAME spec, do not restate it
    ROSTER, SHORT_DELTA, WING_WIDTH, DTE_TARGET, DTE_TOL, TAKE,
    ENTRY_START, ENTRY_END, apply_filters, wtstat,
)

YEARS = list(range(ENTRY_START.year, ENTRY_END.year + 1))


def pull_chains(ticker: str) -> pd.DataFrame:
    """All put rows for one ticker, DTE 0-65, NO quote filter. Chunked by year (v3 is partitioned
    bucket[5](ticker) + year(trade_date), so a ticker-year is the natural unit, ~6s each)."""
    from lib.athena_lib import athena
    from lib.constants import DB, TABLE

    CHAIN_CACHE.mkdir(parents=True, exist_ok=True)
    dest = CHAIN_CACHE / f"{ticker}.parquet"
    if dest.exists():
        df = pd.read_parquet(dest)
        print(f"  {ticker}: {len(df):,} put rows (cached)")
        return df

    parts = []
    for yr in YEARS:
        sql = f"""
        SELECT trade_date, expiry, cp,
               CAST(strike AS DOUBLE) AS strike,
               CAST(bid    AS DOUBLE) AS bid,
               CAST(ask    AS DOUBLE) AS ask,
               CAST(last   AS DOUBLE) AS last,
               (CAST(bid AS DOUBLE) + CAST(ask AS DOUBLE)) / 2.0 AS mid,
               CAST(delta  AS DOUBLE) AS delta,
               CAST(open_interest AS BIGINT) AS open_interest,
               CAST(volume AS BIGINT) AS volume
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY ticker, trade_date, expiry, cp, strike
                    ORDER BY
                        CASE WHEN bid > 0 AND ask > 0 AND delta IS NOT NULL THEN 0 ELSE 1 END,
                        open_interest DESC NULLS LAST,
                        bid DESC
                ) AS rn
            FROM "{DB}"."{TABLE}"
            WHERE ticker = '{ticker}'
              AND cp = 'P'
              AND trade_date >= TIMESTAMP '{yr}-01-01 00:00:00'
              AND trade_date <= TIMESTAMP '{yr}-12-31 00:00:00'
              AND date_diff('day', trade_date, expiry) BETWEEN 0 AND 65
        ) d
        WHERE rn = 1
        """
        part = athena(sql)
        if not part.empty:
            parts.append(part)
        print(f"    {ticker} {yr}: {len(part):,} rows")

    if not parts:
        return pd.DataFrame()
    df = pd.concat(parts, ignore_index=True)
    for c in ("trade_date", "expiry"):
        df[c] = pd.to_datetime(df[c]).dt.date
    df["dte"] = [(e - t).days for t, e in zip(df.trade_date, df.expiry)]
    df.to_parquet(dest)
    zero = (df.bid == 0) & (df.dte > 0)
    print(f"  {ticker}: {len(df):,} put rows, {int(zero.sum()):,} zero-bid at DTE>0 "
          f"({zero.mean():.1%}) that the MySQL cache does not have")
    return df


def build_one(ticker: str) -> pd.DataFrame:
    from lib.studies.put_spread_study import (
        build_put_spread_trades, compute_spread_metrics, find_put_spread_exits,
    )
    df = pull_chains(ticker)
    if df.empty:
        return pd.DataFrame()

    # Entries: the builder's own mask already demands bid>0/ask>0/delta, so the entry pool is unchanged.
    pos = build_put_spread_trades(
        df, short_delta_target=SHORT_DELTA, wing_delta_width=WING_WIDTH,
        dte_target=DTE_TARGET, dte_tol=DTE_TOL, entry_weekday=4,
    )
    if pos.empty:
        return pd.DataFrame()
    pos = pos[pd.to_datetime(pos["entry_date"]) <= pd.Timestamp(ENTRY_END)].reset_index(drop=True)

    # Exits: THIS is what changes -- the scanner now sees the zero-bid days.
    ex = find_put_spread_exits(pos, df, profit_take_pct=TAKE, stop_multiple=None)
    m = compute_spread_metrics(ex)
    m.insert(0, "ticker", ticker)
    print(f"  {ticker}: {len(m):,} trades, {(m.exit_type == 'missing').mean():.1%} missing exit")
    return m


def main() -> None:
    print(f"20-ETF bull put roster from Athena v3, sync quote-filter RELAXED ({date.today()})\n")
    raw = pd.concat([build_one(t) for t in ROSTER], ignore_index=True)
    raw.to_parquet(REPO / "data/cache/etf_putspread_roster_athena_raw.parquet")
    kept = apply_filters(raw)
    kept.to_parquet(OUT)

    print(f"\nraw {len(raw):,} -> {len(kept):,} after filters; "
          f"missing-exit rate {(raw.exit_type == 'missing').mean():.2%}")

    hdr = f"\n{'':26s} {'n':>7s} {'mean %':>9s} {'median %':>9s} {'win %':>7s} {'week t':>8s} {'month t':>8s}"
    print(hdr)

    def line(label, r, d):
        print(f"{label:26s} {len(r):>7,} {r.mean():>9.3f} {r.median():>9.3f} "
              f"{100 * (r > 0).mean():>7.1f} {wtstat(r, d, 'W-FRI'):>8.2f} {wtstat(r, d, 'M'):>8.2f}")

    line("ATHENA gross", kept["roc_pct"], kept["entry_date"])
    line("ATHENA after costs", kept["roc_net"] * 100, kept["entry_date"])

    if MYSQL_BUILD.exists():
        mb = pd.read_parquet(MYSQL_BUILD)
        line("MySQL pass gross", mb["roc_pct"], mb["entry_date"])
        line("MySQL pass after costs", mb["roc_net"] * 100, mb["entry_date"])
        print(f"\ndelta from relaxing the sync filter: "
              f"{kept['roc_pct'].mean() - mb['roc_pct'].mean():+.3f}pp gross, "
              f"{100 * (kept['roc_net'].mean() - mb['roc_net'].mean()):+.3f}pp net, "
              f"n {len(kept) - len(mb):+,}")

    ref = pd.read_parquet(REPO / "data/cache/rsi_putspread.parquet")
    line("REFERENCE cache", ref["roc"], ref["entry_date"])

    # Did the recovered marks resolve the trades that used to be 'missing', and which way did they cut?
    print("\nresolved-vs-missing: where the previously-invisible days land")
    print(raw.groupby("exit_type").agg(n=("roc", "size"), mean_roc_pct=("roc", lambda s: 100 * s.mean())).round(2).to_string())

    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
