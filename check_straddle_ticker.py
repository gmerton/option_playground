#!/usr/bin/env python3
"""Structural eligibility check for the long-straddle pool (data/studies/long_straddle_playbook.md).

A name is eligible when it (1) carries weekly expirations, (2) has >= 60 daily IV
observations for the own-IV percentile gate (run_straddle_iv_gate.py), and (3) quotes a
liquid ATM straddle at 6-17 DTE (both legs bid > 0, worst leg bid-ask <= MAX_BA % of mid,
min open interest >= MIN_OI). No performance screen -- ticker qualification was tested and
rejected (playbook, Approved-List Rebuild).

Usage:
  PYTHONPATH=src .venv/bin/python3 check_straddle_ticker.py KNSA WDC CF
  PYTHONPATH=src .venv/bin/python3 check_straddle_ticker.py --file data/watchlist/universe_latest.txt
  ... --add      append the names that pass to data/watchlist/straddle_pool_323.txt
Requires TRADIER_API_KEY; the IV-history check also needs AWS (Athena prints).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from lib.tradier.tradier_client_wrapper import TradierClient

POOL = Path("data/watchlist/straddle_pool_323.txt")
MAX_BA = 25.0      # worst-leg bid-ask as % of mid
MIN_OI = 100
MIN_WEEKLIES = 4   # distinct expirations inside the next 42 days


async def chain_check(sym: str, client: TradierClient) -> dict:
    out = dict(ticker=sym, weeklies=0, dte=None, strike=None, cost=None, worst_ba=None, min_oi=None, chain_ok=False, note="")
    try:
        exps = (await client.get_json("/markets/options/expirations", params={"symbol": sym}))["expirations"]["date"]
    except Exception as exc:  # noqa: BLE001
        out["note"] = f"no expirations ({exc.__class__.__name__})"; return out
    if isinstance(exps, str): exps = [exps]
    today = date.today()
    dtes = {e: (date.fromisoformat(e) - today).days for e in exps}
    out["weeklies"] = sum(1 for d in dtes.values() if 0 < d <= 42)
    cands = [e for e, d in dtes.items() if 6 <= d <= 17]
    if not cands:
        out["note"] = "no 6-17 DTE expiry"; return out
    exp = min(cands, key=lambda e: abs(dtes[e] - 9))
    out["dte"] = dtes[exp]
    q = (await client.get_json("/markets/quotes", params={"symbols": sym}))["quotes"]["quote"]
    spot = q["last"]
    ch = (await client.get_json("/markets/options/chains", params={"symbol": sym, "expiration": exp}))["options"]["option"]
    strikes = sorted({o["strike"] for o in ch})
    if not strikes:
        out["note"] = "empty chain"; return out
    k = min(strikes, key=lambda s: abs(s - spot)); out["strike"] = k
    legs = {o["option_type"]: o for o in ch if o["strike"] == k}
    if "call" not in legs or "put" not in legs:
        out["note"] = "missing leg"; return out
    bas, ois, mids = [], [], []
    for leg in (legs["call"], legs["put"]):
        b, a = leg["bid"] or 0.0, leg["ask"] or 0.0
        if b <= 0 or a <= 0:
            out["note"] = "zero bid/ask on a leg"; return out
        mid = (a + b) / 2; mids.append(mid); bas.append((a - b) / mid * 100); ois.append(leg["open_interest"] or 0)
    out.update(cost=round(sum(mids), 2), worst_ba=round(max(bas)), min_oi=min(ois))
    out["chain_ok"] = max(bas) <= MAX_BA and min(ois) >= MIN_OI
    return out


def iv_history(tickers: list[str]) -> dict[str, tuple[int, str]]:
    """n_days per ticker from run_straddle_iv_gate.py (needs AWS)."""
    r = subprocess.run([sys.executable, "run_straddle_iv_gate.py", "--tickers", ",".join(tickers)],
                       capture_output=True, text=True, env=os.environ)
    res = {}
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] in tickers:
            try:
                res[parts[0]] = (int(parts[2]), " ".join(parts[7:]) if len(parts) > 7 else "")
            except ValueError:
                pass
    return res


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tickers", nargs="*"); ap.add_argument("--file", action="append", default=[]); ap.add_argument("--add", action="store_true")
    ap.add_argument("--skip-iv", action="store_true", help="skip the Athena IV-history check")
    a = ap.parse_args()
    syms = [t.upper() for t in a.tickers]
    for f in a.file:
        syms += [l.split("#")[0].strip().upper() for l in Path(f).read_text().splitlines() if l.split("#")[0].strip()]
    pool = set(l.strip() for l in POOL.read_text().splitlines() if l.strip())
    syms = sorted(set(syms))
    already = [s for s in syms if s in pool]; todo = [s for s in syms if s not in pool]
    if already: print(f"already in pool ({len(already)}): {' '.join(already)}")
    if not todo: print("nothing to check"); return 0
    print(f"checking {len(todo)}: {' '.join(todo)}")
    sem = asyncio.Semaphore(2)
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
        async def one(s):
            async with sem: return await chain_check(s, c)
        rows = await asyncio.gather(*(one(s) for s in todo))
    hist = {} if a.skip_iv else iv_history(todo)
    df = pd.DataFrame(rows)
    df["iv_days"] = df["ticker"].map(lambda t: hist.get(t, (None, ""))[0])
    df["weeklies_ok"] = df["weeklies"] >= MIN_WEEKLIES
    df["iv_ok"] = df["iv_days"].map(lambda n: (n is not None) and n >= 60) if not a.skip_iv else None
    df["eligible"] = df["weeklies_ok"] & df["chain_ok"] & (df["iv_ok"] if not a.skip_iv else True)
    pd.set_option("display.width", 200)
    print(df[["ticker", "weeklies", "weeklies_ok", "dte", "strike", "cost", "worst_ba", "min_oi", "chain_ok", "iv_days", "iv_ok", "eligible", "note"]].to_string(index=False))
    passing = df.loc[df["eligible"], "ticker"].tolist()
    print(f"\neligible: {' '.join(passing) or 'none'}")
    if a.add and passing:
        with POOL.open("a") as fh:
            fh.write("".join(f"{t}\n" for t in passing))
        print(f"appended {len(passing)} to {POOL}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
