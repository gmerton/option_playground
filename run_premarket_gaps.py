#!/usr/bin/env python3
"""Pre-market gap check against the plan (run 08:35-09:25 ET; start_alerts.sh runs it first).

For every name in the long universe, the short list, and SPY/QQQ: pre-market mid (Tradier
extended-hours bid/ask; `last` is stale pre-open), gap vs the prior close in % and in ADR,
and what that does to the plan:
  DEAD      a buy-stop the stock is already gapping ABOVE  -> not a fill (gap rule)
  GAP>1ADR  opening more than 1 ADR away                    -> no hour-one buys on that name
  STOP      a held position gapping through its stop        -> decide before the bell
  INDEX     SPY/QQQ gap, which sets the tone for the index gate
Levels come from data/watchlist/trade_plan_<latest>.md: every "buy-stop X" cell and the
"Holds:" line's "NAME (stop / ...)" entries. Nothing here is a trade; it is the 9:25 read.

  PYTHONPATH=src .venv/bin/python3 run_premarket_gaps.py [--min-gap-adr 0.5]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from lib.alerts.context import load_context
from lib.alerts.universe import build_universe, latest_plan
from lib.tradier.tradier_client_wrapper import TradierClient

ET = ZoneInfo("America/New_York")
SHORT = Path("data/watchlist/universe_short.txt")


def session_date() -> date:
    """The session being prepared for: today in ET, or the next weekday after the close."""
    now = datetime.now(ET); d = now.date()
    if now.time() >= time(16, 5):
        d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def plan_levels(p: Path | None) -> tuple[dict[str, float], dict[str, float]]:
    """buy-stops and hold-stops from the plan file. If the file has '## For <date>' sections,
    only the LAST one counts (earlier tables are the previous session's levels). Buy-stops come
    from a 'buy-stop' table column or an inline 'buy-stop X'; hold stops from the last 'Holds:' line
    as 'NAME (STOP / ...)'."""
    buys, holds = {}, {}
    if p is None or not p.exists():
        return buys, holds
    text = p.read_text()
    parts = re.split(r"^## For ", text, flags=re.M)
    text = ("## For " + parts[-1]) if len(parts) > 1 else text
    col = None
    for line in text.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            low = [c.lower() for c in cells]
            if "buy-stop" in low:
                col = low.index("buy-stop"); continue
            if set("".join(cells)) <= set("-: "):
                continue
            tok = cells[0].split()[0] if cells[0] else ""
            if not re.match(r"^[A-Z][A-Z0-9.\-]{0,5}$", tok):
                continue
            m = re.search(r"buy-stop\s+([\d.]+)", line)
            if m:
                buys[tok] = float(m.group(1))
            elif col is not None and col < len(cells):
                for part in re.split(r"\s*/\s*", cells[col]):
                    mm = re.match(r"([\d.]+)", part)
                    if mm:
                        names = [t for t in re.split(r"\s*/\s*", cells[0]) if re.match(r"^[A-Z]", t)]
                        # "INTC / AMD | 106.75 / 526.80" -> pair positionally
                        i = re.split(r"\s*/\s*", cells[col]).index(part)
                        if i < len(names):
                            buys[names[i].split()[0]] = float(mm.group(1))
        elif line.startswith("Holds:"):
            holds = {m.group(1): float(m.group(2)) for m in re.finditer(r"\b([A-Z]{2,6})\b[^()]*?\(([\d.]+)\s*/", line)}
    return buys, holds


async def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--min-gap-adr", type=float, default=0.5); a = ap.parse_args()
    now = datetime.now(ET)
    universe, _ = build_universe(write=False)
    shorts = [l.split("#")[0].strip().upper() for l in SHORT.read_text().splitlines() if l.split("#")[0].strip()] if SHORT.exists() else []
    syms = sorted(set(universe) | set(shorts) | {"SPY", "QQQ"})
    plan = latest_plan(); buys, holds = plan_levels(plan)
    ctx = await load_context(syms, session_date())
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
        q = (await c.get_json("/markets/quotes", params={"symbols": ",".join(syms)}))["quotes"]["quote"]
    rows = []
    for x in (q if isinstance(q, list) else [q]):
        s = x["symbol"]; k = ctx.get(s)
        if k is None:
            continue
        bid, ask = x.get("bid") or 0, x.get("ask") or 0
        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else None
        # freshness: Tradier stamps bid/ask in ms; stale quotes are yesterday's close
        ts = max(x.get("bid_date") or 0, x.get("ask_date") or 0) / 1000
        fresh = ts > 0 and (session_date() - datetime.fromtimestamp(ts, ET).date()).days <= 1
        px = mid if (mid and fresh) else None
        gap = (px / k.prev_close - 1) * 100 if px else None
        gap_adr = gap / k.adr_pct if gap is not None and k.adr_pct else None
        flags = []
        if px is not None:
            if s in buys and px > buys[s]:
                flags.append(f"DEAD buy-stop {buys[s]:.2f}")
            if s in holds and px < holds[s]:
                flags.append(f"STOP {holds[s]:.2f} gapped through")
            if gap_adr is not None and abs(gap_adr) >= 1.0:
                flags.append("GAP>1ADR")
            if s in ("SPY", "QQQ"):
                flags.append("INDEX")
        rows.append(dict(sym=s, prev=round(k.prev_close, 2), pm_mid=round(px, 2) if px else None, gap_pct=round(gap, 2) if gap is not None else None,
                         gap_adr=round(gap_adr, 2) if gap_adr is not None else None, spread_pct=round((ask / bid - 1) * 100, 2) if px else None,
                         buy_stop=buys.get(s), hold_stop=holds.get(s), flags=" ".join(flags), side="short" if s in shorts and s not in universe else "long"))
    df = pd.DataFrame(rows)
    live = df[df.pm_mid.notna()]
    print(f"[{now:%H:%M} ET] pre-market check | plan {plan.name if plan else 'none'} | {len(live)} of {len(df)} names have a fresh pre-market quote")
    if live.empty:
        print("  no fresh extended-hours quotes yet (before ~04:00 ET, or Tradier not returning pre-market bid/ask)")
        return 0
    pd.set_option("display.width", 220)
    idx = live[live.sym.isin(["SPY", "QQQ"])]
    print("index: " + " | ".join(f"{r.sym} {r.gap_pct:+.2f}%" for r in idx.itertuples()))
    show = live[(live.flags != "") | (live.gap_adr.abs() >= a.min_gap_adr)].sort_values("gap_adr", ascending=False)
    print(show[["sym", "side", "prev", "pm_mid", "gap_pct", "gap_adr", "spread_pct", "buy_stop", "hold_stop", "flags"]].to_string(index=False) if len(show) else "  nothing flagged")
    out = Path("data/watchlist/logs") / f"premarket_{now.date().isoformat()}.csv"; out.parent.mkdir(parents=True, exist_ok=True); df.to_csv(out, index=False)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
