#!/usr/bin/env python3
"""
Position monitor — the open book, grouped into structures, with broker basis and live marks.

Source is `journal_open_positions`: the IBKR Flex open-position snapshot written by
run_daily_journal.py, one row per leg with the broker's own `open_price` (true cost basis),
`mark_price` and `unrealized_pnl`.

Why not journal_campaigns: its `net_premium` is CUMULATIVE cash for the campaign including rolls,
so it is not an entry price -- on 2026-09-18 it implied a 3.90 credit on a 2.00-wide SLS spread,
which would make any "max risk" figure nonsense. The Flex snapshot has no such problem.
(It also replaced `strategy_positions`, a March-2026 experiment dropped 2026-09-20 whose last
8 "open" rows had all expired by May.)

The snapshot lands one session late, so `--live` re-marks every option leg against Tradier for a
current read; without it you get the broker's marks as of the snapshot date.

Structures are inferred from the legs (same underlying + expiry, sign of `position` = direction),
so straddles, verticals, calendars and singles all come out without a stored position_type.

Usage:
    MYSQL_PASSWORD=... PYTHONPATH=src .venv/bin/python3 run_position_monitor.py
    ... run_position_monitor.py --live          # re-mark against Tradier (needs TRADIER_API_KEY)
    ... run_position_monitor.py --expiring 7    # only structures inside 7 DTE
"""
from __future__ import annotations

import argparse, asyncio, os, sys, warnings
from datetime import date
warnings.filterwarnings("ignore")

import pandas as pd
from lib.mysql_lib import _get_conn

MULT = {"OPT": 100, "STK": 1}


def latest_snapshot() -> tuple[date, pd.DataFrame]:
    c = _get_conn()
    d = pd.read_sql("SELECT MAX(report_date) d FROM journal_open_positions", c).d[0]
    df = pd.read_sql(f"SELECT * FROM journal_open_positions WHERE report_date = '{d}'", c)
    return d, df


def classify(g: pd.DataFrame) -> str:
    if (g.asset_category == "STK").all():
        return "stock"
    pcs = set(g.put_call.dropna()); longs = (g.position > 0).sum(); shorts = (g.position < 0).sum()
    ks = g.strike.dropna().nunique()
    if pcs == {"C", "P"}:
        if not shorts: return "long straddle/strangle"
        if not longs:  return "short straddle/strangle"
        return "iron condor/fly"
    pc = "call" if pcs == {"C"} else "put"
    if len(g) == 1 or ks == 1:
        return f"{'long' if g.position.iloc[0] > 0 else 'short'} {pc}"
    # (position x open_price) is the position's VALUE, so a spread opened for a CREDIT is
    # negative -- you owe it back. Credit put spread = bull put; credit call spread = bear call.
    val = (g.position * g.open_price).sum()
    if pc == "put":  return "bull put spread" if val < 0 else "bear put spread"
    return "bear call spread" if val < 0 else "bull call spread"


async def live_marks(df: pd.DataFrame) -> dict:
    from lib.tradier.tradier_client_wrapper import TradierClient
    from lib.commons.list_contracts import list_contracts_for_expiry
    key = os.environ.get("TRADIER_API_KEY")
    if not key:
        print("  (--live needs TRADIER_API_KEY; falling back to broker marks)", file=sys.stderr)
        return {}
    o = df[df.asset_category == "OPT"]
    want = {(r.underlying_symbol, str(r.expiry)[:10]) for r in o.itertuples()}
    out = {}
    async with TradierClient(api_key=key) as cl:
        for tk, ex in sorted(want):
            try:
                for c in await list_contracts_for_expiry(tk, ex, client=cl):
                    b, a = c.get("bid") or 0, c.get("ask") or 0
                    m = (b + a) / 2 if b > 0 and a > 0 else (c.get("last") or 0)
                    if m:
                        out[(tk, ex, float(c["strike"]), c["option_type"][0].upper())] = float(m)
            except Exception as e:
                print(f"  WARN {tk}/{ex}: {type(e).__name__}", file=sys.stderr)
    return out


async def main(argv) -> int:
    ap = argparse.ArgumentParser(description="Open book by structure, broker basis + live marks")
    ap.add_argument("--live", action="store_true", help="re-mark options against Tradier")
    ap.add_argument("--expiring", type=int, default=None)
    a = ap.parse_args(argv)

    snap, df = latest_snapshot()
    today = date.today()
    lag = (today - snap).days
    print(f"Flex snapshot {snap} ({lag}d old) | {len(df)} legs: "
          + ", ".join(f"{k} {v}" for k, v in df.asset_category.value_counts().items()))
    marks = await live_marks(df) if a.live else {}
    if a.live:
        print(f"live marks: {len(marks)} contracts re-quoted\n")
    else:
        print()

    df["expiry_s"] = df.expiry.astype(str).str[:10]
    rows = []
    for (u, ex), g in df.groupby(["underlying_symbol", "expiry_s"], dropna=False):
        kind = classify(g)
        m = MULT.get(g.asset_category.iloc[0], 100)
        basis = (g.position * g.open_price * m).sum()
        bmark = (g.position * g.mark_price * m).sum()
        lmark = bmark
        if marks and (g.asset_category == "OPT").all():
            v, ok = 0.0, True
            for r in g.itertuples():
                k = (r.underlying_symbol, r.expiry_s, float(r.strike), str(r.put_call)[:1].upper())
                if k not in marks: ok = False; break
                v += r.position * marks[k] * m
            if ok: lmark = v
        dte = (pd.Timestamp(ex).date() - today).days if ex and ex != "None" else None
        if a.expiring is not None and (dte is None or dte > a.expiring):
            continue
        # NB: one (underlying, expiry) cell can hold two unrelated positions -- a bull put and a
        # long call on the same name and expiry merge into one row and read as an odd structure.
        rows.append(dict(u=u, kind=kind, dte=dte, legs=len(g),
                         qty=int(g.position.abs().max()), basis=basis, mark=lmark,
                         pnl=lmark - basis, broker_pnl=g.unrealized_pnl.sum()))

    D = pd.DataFrame(rows).sort_values(["dte", "u"], na_position="last")
    col = "P&L(live)" if marks else "P&L"
    print(f"{'ticker':<7}{'structure':<24}{'DTE':>5}{'legs':>5}{'basis$':>10}{'mark$':>10}{col:>11}   note")
    for r in D.itertuples():
        dte = "  --" if r.dte is None or pd.isna(r.dte) else f"{r.dte:>4.0f}"
        note = ""
        if r.dte is not None and not pd.isna(r.dte):
            if r.dte < 0: note = "EXPIRED, reconcile"
            elif r.dte <= 2: note = "<<< EXPIRES"
        print(f"{r.u:<7}{r.kind:<24}{dte:>5}{r.legs:>5}{r.basis:>10,.0f}{r.mark:>10,.0f}{r.pnl:>11,.0f}   {note}")

    print(f"\nnet: basis ${D.basis.sum():,.0f} -> mark ${D.mark.sum():,.0f} = ${D.pnl.sum():+,.0f}")
    if not marks:
        print(f"broker unrealized (snapshot): ${D.broker_pnl.sum():+,.0f}")
    print(f"\nstructure mix:\n{D.groupby('kind').agg(n=('u','size'), legs=('legs','sum')).to_string()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
