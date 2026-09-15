#!/usr/bin/env python3
"""
Pre-market HOT INDUSTRIES (2026-09-14, Gabe: "add something to the premarket routine that identifies hot industries"
-- that morning cyber gapped up and semis gapped down before the bell and nothing named it).

For every sector / industry ETF (market_conditions.SECTORS + INDUSTRIES + data/watchlist/group_etfs.csv) and for the
alert universe's own groups (data/watchlist/universe_groups.csv): the PRE-MARKET move vs the prior close (yfinance
pre-market print; falls back to the last regular print and says so), in % and in ADR units, the ETF's daily in-play
state at the prior close, its 1-day / 5-day return, and for tracked groups the members' pre-market breadth.
Ranked by |gap in ADR|; HOT = the ETF is >= HOT_ADR from the prior close or >= 2/3 of >= 3 members are moving the
same way by >= 0.5 ADR. Descriptive only -- industry strength is context, never a gate (rotation study, 2026-08);
what it changes intraday: ORB9 is not index-gated on a LEADING group; names gapping >= 1 ADR get re-classified at
the first bar; reclaims on a gapped-down group are the +0.22R cell only after 09:40 (gap study 2026-09-14).

Run 08:00-09:25 ET:  TRADIER_API_KEY=... PYTHONPATH=src .venv/bin/python3 run_premarket_industries.py [--no-members]
Writes data/watchlist/premarket_industries_<date>.csv. start_alerts.sh runs it before the bell.
"""
from __future__ import annotations
import argparse, asyncio, os, sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd

REPO = Path(__file__).resolve().parent; WL = REPO / "data" / "watchlist"
sys.path.insert(0, str(REPO))
HOT_ADR = 1.5; MEMBER_ADR = 0.5; MEMBERS_MIN = 3; MEMBERS_FRAC = 0.67   # 1.0 lit 16 groups on the 9/14 dry run; 1.5 keeps the real movers


def etf_list() -> list[tuple[str, str]]:
    from market_conditions import SECTORS, INDUSTRIES
    out = list(SECTORS) + list(INDUSTRIES); seen = {s for s, _ in out}
    p = WL / "group_etfs.csv"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip() and not line.startswith("#") and not line.startswith("group,") and "," in line:
                g, e = [x.strip() for x in line.split(",", 1)]
                if e.upper() not in seen:
                    out.append((e.upper(), g)); seen.add(e.upper())
    return out


def groups_map() -> dict[str, str]:
    m = {}
    p = WL / "universe_groups.csv"
    if p.exists():
        for line in p.read_text().splitlines()[1:]:
            if "," in line:
                t, g = line.split(",", 1); m[t.strip().upper()] = g.strip()
    return m


def etf_for_group() -> dict[str, str]:
    m = {}
    for line in (WL / "group_etfs.csv").read_text().splitlines():
        if line.strip() and not line.startswith("#") and not line.startswith("group,") and "," in line:
            g, e = [x.strip() for x in line.split(",", 1)]; m[g] = e.upper()
    return m


async def premarket_prices(symbols: list[str]) -> dict[str, tuple[float | None, str]]:
    """{sym: (price, source)}. Tradier's quote carries no pre-market LAST, but its bid/ask are live in the
    pre-market (bid_date = now), so the mid is the price -- one batched call for everything. Missing ones fall
    back to yfinance 1-min bars with extended hours (the fast_info preMarketPrice field is empty, 9/15/2026)."""
    import time as _time
    from lib.tradier.tradier_client_wrapper import TradierClient
    out: dict[str, tuple[float | None, str]] = {}
    now_ms = _time.time() * 1000
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as t:
        for i in range(0, len(symbols), 50):
            chunk = symbols[i:i + 50]
            try:
                q = (await t.get_json("/markets/quotes", params={"symbols": ",".join(chunk), "greeks": "false"}))["quotes"].get("quote", [])
            except Exception:  # noqa: BLE001
                q = []
            if isinstance(q, dict): q = [q]
            for x in q:
                bid, ask, bd = x.get("bid") or 0, x.get("ask") or 0, x.get("bid_date") or 0
                fresh = bd and (now_ms - bd) < 30 * 60 * 1000          # a quote refreshed in the last 30 minutes
                if bid > 0 and ask > 0 and fresh and (ask / bid - 1) < 0.03:
                    out[x["symbol"]] = ((bid + ask) / 2, "pre-mid")
    missing = [s for s in symbols if s not in out]
    if missing:
        try:
            import yfinance as yf
            d = yf.download(missing, period="1d", interval="1m", prepost=True, progress=False, auto_adjust=True, group_by="ticker", threads=True)
            for s in missing:
                try:
                    x = (d[s] if len(missing) > 1 else d).dropna(subset=["Close"])
                    if len(x): out[s] = (float(x.Close.iloc[-1]), "pre-bar")
                except Exception:  # noqa: BLE001
                    pass
        except Exception:  # noqa: BLE001
            pass
    for s in symbols:
        out.setdefault(s, (None, "none"))
    return out


async def daily(symbols: list[str], session: date):
    from lib.alerts.context import load_context
    from lib.tradier.tradier_client_wrapper import TradierClient
    from lib.tradier.get_daily_history import get_daily_history
    ctx = await load_context(symbols, session)
    rets = {}
    async with TradierClient(api_key=os.environ["TRADIER_API_KEY"]) as c:
        sem = asyncio.Semaphore(2)
        async def one(s):
            async with sem:
                try:
                    d = await get_daily_history(s, session - timedelta(days=30), session - timedelta(days=1), client=c)
                    cl = d.close.astype(float)
                    rets[s] = (100 * (cl.iloc[-1] / cl.iloc[-2] - 1), 100 * (cl.iloc[-1] / cl.iloc[-6] - 1)) if len(cl) >= 6 else (None, None)
                except Exception:  # noqa: BLE001
                    rets[s] = (None, None)
        await asyncio.gather(*(one(s) for s in symbols))
    return ctx, rets


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--no-members", action="store_true"); ap.add_argument("--date", default=None); a = ap.parse_args()
    now = datetime.now(ZoneInfo("America/New_York")); session = date.fromisoformat(a.date) if a.date else now.date()
    etfs = etf_list(); gmap = groups_map(); g2e = etf_for_group()
    members = {} if a.no_members else {g: [t for t, gg in gmap.items() if gg == g] for g in set(gmap.values())}
    syms = [e for e, _ in etfs] + [t for ts in members.values() for t in ts]
    ctx, rets = asyncio.run(daily(sorted(set(syms)), session))
    px = asyncio.run(premarket_prices(sorted(set(syms))))
    def move(s):
        c = ctx.get(s); p, src = px.get(s, (None, "none"))
        if c is None or p is None or not c.prev_close or not c.adr_pct:
            return None, None, src
        g = 100 * (p / c.prev_close - 1); return g, g / c.adr_pct, src
    rows = []
    for e, label in etfs:
        g, gadr, src = move(e); c = ctx.get(e)
        grp = next((gg for gg, ee in g2e.items() if ee == e), None)
        mem = members.get(grp, []) if grp else []
        mm = [move(t) for t in mem]; mm = [(x[0], x[1]) for x in mm if x[0] is not None]
        up = sum(1 for _, ad in mm if ad >= MEMBER_ADR); dn = sum(1 for _, ad in mm if ad <= -MEMBER_ADR); n = len(mm)
        avg = sum(x for x, _ in mm) / n if n else None
        hot = ""
        if gadr is not None and gadr >= HOT_ADR: hot = "HOT UP"
        elif gadr is not None and gadr <= -HOT_ADR: hot = "HOT DOWN"
        elif n >= MEMBERS_MIN and up / n >= MEMBERS_FRAC: hot = "HOT UP (members)"
        elif n >= MEMBERS_MIN and dn / n >= MEMBERS_FRAC: hot = "HOT DOWN (members)"
        rows.append(dict(etf=e, label=label if not grp else f"{label} [{grp}]", gap_pct=g, gap_adr=gadr, src=src, adr=getattr(c, "adr_pct", None),
                         day=getattr(c, "day_state", ""), ext21=getattr(c, "ext21_close_adr", None), ret1d=rets.get(e, (None, None))[0], ret5d=rets.get(e, (None, None))[1],
                         members=n, up=up, down=dn, mem_avg=avg, hot=hot))
    df = pd.DataFrame(rows); df["absadr"] = df.gap_adr.abs(); df = df.sort_values("absadr", ascending=False).drop(columns="absadr")
    src = df.src.value_counts().to_dict()
    print(f"PRE-MARKET INDUSTRIES  {session}  {now:%H:%M} ET  | price source: {src}  (pre-mid = live Tradier bid/ask mid; pre-bar = yfinance extended-hours bar; none = no quote)")
    print(f"HOT = ETF >= {HOT_ADR:.1f} ADR from the prior close, or >= {int(100*MEMBERS_FRAC)}% of >= {MEMBERS_MIN} tracked members moving >= {MEMBER_ADR} ADR the same way")
    pd.set_option("display.width", 220)
    show = df.copy()
    for col in ("gap_pct", "ret1d", "ret5d", "mem_avg"): show[col] = show[col].map(lambda v: "" if v is None or pd.isna(v) else f"{v:+.1f}%")
    show["gap_adr"] = show.gap_adr.map(lambda v: "" if v is None or pd.isna(v) else f"{v:+.1f}"); show["ext21"] = show.ext21.map(lambda v: "" if v is None or pd.isna(v) else f"{v:+.1f}")
    show["breadth"] = [f"{u}↑ {d}↓ of {n}" if n else "" for u, d, n in zip(df.up, df.down, df.members)]
    print(show[["etf", "label", "gap_pct", "gap_adr", "day", "ext21", "ret1d", "ret5d", "breadth", "mem_avg", "hot"]].to_string(index=False))
    hot = df[df.hot != ""]
    print("\nHOT groups:", ", ".join(f"{r.etf} {r.hot} ({r.gap_pct:+.1f}%)" for r in hot.itertuples()) if len(hot) else "none")
    print("Read: a LEADING group un-gates ORB9 on its names; names gapping >= 1 ADR are re-classified at the first bar; on a gapped-DOWN group the")
    print("      reclaim that pays is after 09:40 (+0.22R), the 09:30-09:40 one is the worst cell (-0.31R). Industry strength is context, not a gate.")
    out = WL / f"premarket_industries_{session}.csv"; df.to_csv(out, index=False); print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
