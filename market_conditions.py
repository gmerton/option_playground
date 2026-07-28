#!/usr/bin/env python3
"""
Top-down pre-market market-conditions report.

A daily routine aid that reads, from the top down:
  1. MARKET REGIME  -- bull or bear, off SPY trend + cross-index breadth
  2. INDEX SCOREBOARD -- SPY / QQQ / IWM / DIA / MDY / RSP, ranked by relative strength
  3. SECTOR ROTATION -- the 11 SPDR sectors, ranked by 1-month momentum
  4. INDUSTRY STRENGTH -- ~20 industry ETFs (semis, biotech, banks, energy...),
       ranked, with a risk flag so you can see where strength is *and* where the
       cheap (low-vol) strength is vs. the expensive (high-vol) chase.

Everything is computed from Tradier daily history. No positions, no orders --
read-only situational awareness for the open.

Run:
    AWS_PROFILE=clarinut-gmerton PYTHONPATH=src .venv/bin/python3 market_conditions.py

Requires: TRADIER_API_KEY
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from lib.tradier.tradier_client_wrapper import TradierClient

WATCHLIST_FILE = "data/watchlist/monitor_custom.json"

# Best-effort ticker -> group ETF map, used only to give position flags some
# sector/industry context. Edit freely; unmapped tickers still get flagged on
# their own trend. Group ETFs should exist in SECTORS or INDUSTRIES below.
SECTOR_MAP: Dict[str, str] = {
    # semis / hardware
    "AMD": "SMH", "NVDA": "SMH", "GFS": "SMH", "MU": "SMH", "AVGO": "SMH",
    "ASML": "SMH", "LRCX": "SMH", "AMAT": "SMH", "KLAC": "SMH", "TSM": "SMH",
    "ARM": "SMH", "MRVL": "SMH", "ON": "SMH", "QCOM": "SMH", "INTC": "SMH",
    # software / internet
    "DOCN": "IGV", "PLTR": "IGV", "CRWD": "CIBR", "PANW": "CIBR", "ZS": "CIBR",
    "NET": "IGV", "SNOW": "IGV", "DDOG": "IGV", "MDB": "IGV", "NOW": "IGV",
    "APH": "XLK", "APP": "IGV",
    # industrials / power / aero
    "CMI": "XLI", "GEV": "XLI", "ETN": "XLI", "PWR": "XLI", "VRT": "XLI",
    "FTAI": "JETS", "GE": "XAR", "RTX": "XAR", "LMT": "XAR", "HWM": "XAR",
    "CRS": "XAR", "HEI": "XAR",
    # materials / metals / energy
    "ATI": "XME", "FCX": "XME", "CLF": "XME", "NUE": "XME", "STLD": "XME",
    "XOM": "XLE", "CVX": "XLE", "OXY": "XOP", "FANG": "XOP",
    # financials
    "BAP": "XLF", "JPM": "XLF", "GS": "XLF", "BAC": "XLF", "WFC": "XLF",
    # health / biotech / devices
    "LLY": "XLV", "UNH": "XLV", "ISRG": "IHI", "VRTX": "XBI", "REGN": "XBI",
    # consumer / retail / homebuild
    "DHI": "ITB", "LEN": "ITB", "PHM": "ITB", "AMZN": "XLY", "TSLA": "XLY",
}

# ---- universe -------------------------------------------------------------

BENCHMARK = "SPY"

INDICES = [
    ("SPY", "S&P 500 (large cap)"),
    ("QQQ", "Nasdaq 100 (mega tech)"),
    ("IWM", "Russell 2000 (small cap)"),
    ("DIA", "Dow 30 (old economy)"),
    ("MDY", "S&P MidCap 400"),
    ("RSP", "S&P 500 equal-weight (breadth)"),
]

SECTORS = [
    ("XLK", "Technology"),
    ("XLC", "Communication Svcs"),
    ("XLY", "Consumer Discretionary"),
    ("XLP", "Consumer Staples"),
    ("XLE", "Energy"),
    ("XLF", "Financials"),
    ("XLV", "Health Care"),
    ("XLI", "Industrials"),
    ("XLB", "Materials"),
    ("XLRE", "Real Estate"),
    ("XLU", "Utilities"),
]

INDUSTRIES = [
    ("SMH", "Semiconductors"),
    ("IGV", "Software"),
    ("CIBR", "Cybersecurity"),
    ("XBI", "Biotech (equal-wt)"),
    ("IHI", "Medical Devices"),
    ("KRE", "Regional Banks"),
    ("KIE", "Insurance"),
    ("ITB", "Homebuilders"),
    ("XRT", "Retail"),
    ("XOP", "Oil & Gas E&P"),
    ("OIH", "Oil Services"),
    ("XME", "Metals & Mining"),
    ("GDX", "Gold Miners"),
    ("XAR", "Aerospace & Defense"),
    ("IYT", "Transports"),
    ("JETS", "Airlines"),
    ("TAN", "Solar"),
    ("URA", "Uranium"),
    ("KWEB", "China Internet"),
    ("ARKK", "Hi-growth/Innovation"),
]

# ---- metrics --------------------------------------------------------------


@dataclass
class Metrics:
    symbol: str
    label: str
    asof: str
    close: float
    sma20: Optional[float]
    sma50: Optional[float]
    sma200: Optional[float]
    sma50_slope_up: Optional[bool]      # 50SMA today vs 21 trading days ago
    ret_5d: Optional[float]
    ret_21d: Optional[float]
    ret_63d: Optional[float]
    rs_21d: Optional[float]             # ret_21d minus benchmark ret_21d
    vol_20d: Optional[float]            # annualized realized vol, % (risk)
    trend_score: Optional[int]          # 0..4 stage-style score
    dist_days: Optional[int]            # IBD distribution days in last 25 sessions

    @property
    def pct_vs(self):
        def p(ma):
            return None if ma in (None, 0) else (self.close / ma - 1.0)
        return p


def _sma(values: List[float], window: int, end_idx: int) -> Optional[float]:
    """SMA of `window` closes ending at end_idx (inclusive)."""
    if end_idx + 1 < window:
        return None
    seg = values[end_idx + 1 - window : end_idx + 1]
    return sum(seg) / window


def _ret(values: List[float], n: int) -> Optional[float]:
    if len(values) <= n:
        return None
    a, b = values[-1], values[-1 - n]
    return None if b == 0 else (a / b - 1.0)


def _realized_vol(values: List[float], n: int = 20) -> Optional[float]:
    if len(values) <= n:
        return None
    rets = []
    for i in range(len(values) - n, len(values)):
        prev = values[i - 1]
        if prev > 0:
            rets.append(math.log(values[i] / prev))
    if len(rets) < 2:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252)


async def fetch_days(client: TradierClient, symbol: str, days_back: int = 420,
                     asof: Optional[date] = None):
    """Chronological list of {date, close, volume} day records (<= asof)."""
    end = asof or date.today()
    start = end - timedelta(days=days_back)
    payload = await client.get_json(
        "/markets/history",
        params={"symbol": symbol, "start": start.isoformat(), "end": end.isoformat()},
    )
    history = (payload or {}).get("history") or {}
    days = history.get("day")
    if not days:
        return []
    if isinstance(days, dict):
        days = [days]
    out = []
    for d in sorted(days, key=lambda x: x.get("date", "")):
        c, dt, v = d.get("close"), d.get("date"), d.get("volume")
        if c is None or dt is None:
            continue
        out.append({
            "date": str(dt),
            "close": float(c),
            "volume": float(v) if v is not None else None,
        })
    return out


def count_distribution_days(days: List[dict], lookback: int = 25,
                            thresh: float = -0.002) -> Tuple[int, List[str]]:
    """
    IBD-style distribution day: index closes down >= 0.2% on volume HIGHER than
    the prior session — a footprint of institutional selling. Count within the
    last `lookback` sessions. 5+ in a rolling month = uptrend under pressure.
    """
    if len(days) < 2:
        return 0, []
    window = days[-(lookback + 1):]  # +1 so the oldest session has a prior to compare
    count, dates = 0, []
    for i in range(1, len(window)):
        prev, cur = window[i - 1], window[i]
        if prev["close"] <= 0 or prev["volume"] is None or cur["volume"] is None:
            continue
        chg = cur["close"] / prev["close"] - 1.0
        if chg <= thresh and cur["volume"] > prev["volume"]:
            count += 1
            dates.append(cur["date"])
    return count, dates


async def compute(client: TradierClient, symbol: str, label: str,
                  bench_ret21: Optional[float],
                  asof: Optional[date] = None) -> Optional[Metrics]:
    days = await fetch_days(client, symbol, asof=asof)
    if len(days) < 25:
        return None
    closes = [d["close"] for d in days]
    asof = days[-1]["date"]
    dist, _ = count_distribution_days(days)
    last = len(closes) - 1
    sma20 = _sma(closes, 20, last)
    sma50 = _sma(closes, 50, last)
    sma200 = _sma(closes, 200, last)

    slope_up = None
    sma50_then = _sma(closes, 50, last - 21) if last - 21 >= 0 else None
    if sma50 is not None and sma50_then is not None:
        slope_up = sma50 > sma50_then

    ret21 = _ret(closes, 21)
    rs21 = None
    if ret21 is not None and bench_ret21 is not None:
        rs21 = ret21 - bench_ret21

    close = closes[-1]
    score = None
    if None not in (sma20, sma50, sma200) and slope_up is not None:
        score = sum([close > sma20, close > sma50, close > sma200, slope_up])

    return Metrics(
        symbol=symbol, label=label, asof=asof, close=close,
        sma20=sma20, sma50=sma50, sma200=sma200, sma50_slope_up=slope_up,
        ret_5d=_ret(closes, 5), ret_21d=ret21, ret_63d=_ret(closes, 63),
        rs_21d=rs21, vol_20d=_realized_vol(closes, 20), trend_score=score,
        dist_days=dist,
    )


# ---- formatting -----------------------------------------------------------

def pct(x: Optional[float], width: int = 7) -> str:
    if x is None:
        return "—".rjust(width)
    return f"{x * 100:+.1f}%".rjust(width)


def trend_word(m: Metrics) -> str:
    s = m.trend_score
    if s is None:
        return "?"
    return {4: "STRONG UP", 3: "Up", 2: "Mixed", 1: "Weak", 0: "DOWNTREND"}[s]


def stack_glyph(m: Metrics) -> str:
    """Price position vs the 20/50/200 stack, left→right."""
    def g(ma):
        if ma is None:
            return "·"
        return "▲" if m.close > ma else "▼"
    return f"{g(m.sma20)}{g(m.sma50)}{g(m.sma200)}"


def risk_word(m: Metrics) -> str:
    v = m.vol_20d
    if v is None:
        return "—"
    if v >= 0.45:
        return "HIGH"
    if v >= 0.28:
        return "med"
    return "low"


async def gather(client, universe, bench_ret21, asof=None):
    sem = asyncio.Semaphore(12)

    async def one(sym, lbl):
        async with sem:
            try:
                return await compute(client, sym, lbl, bench_ret21, asof=asof)
            except Exception as e:
                print(f"  ! {sym}: {e}")
                return None

    results = await asyncio.gather(*(one(s, l) for s, l in universe))
    return [r for r in results if r is not None]


def print_table(title: str, rows: List[Metrics], rank_by_rs: bool = True):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")
    if rank_by_rs:
        rows = sorted(rows, key=lambda m: (m.rs_21d if m.rs_21d is not None else -9), reverse=True)
    hdr = f"{'sym':<5}{'name':<22}{'stack':<7}{'trend':<10}{'5d':>7}{'21d':>8}{'3mo':>8}{'RSvSPY':>8}  {'risk':>5}"
    print(hdr)
    print("-" * 78)
    for m in rows:
        print(
            f"{m.symbol:<5}{m.label[:21]:<22}{stack_glyph(m):<7}{trend_word(m):<10}"
            f"{pct(m.ret_5d)}{pct(m.ret_21d,8)}{pct(m.ret_63d,8)}{pct(m.rs_21d,8)}  {risk_word(m):>5}"
        )


def regime_verdict(spy: Metrics) -> str:
    above200 = spy.sma200 is not None and spy.close > spy.sma200
    golden = (spy.sma50 is not None and spy.sma200 is not None and spy.sma50 > spy.sma200)
    if above200 and golden and spy.trend_score == 4:
        return "BULL  — SPY above a rising 50 & 200, full uptrend stack"
    if above200 and golden:
        return "BULL (cooling) — SPY > 200SMA & 50>200, but stack not fully aligned"
    if above200 and not golden:
        return "NEUTRAL/REPAIR — SPY > 200SMA but 50<200 (recovering or topping)"
    if (not above200) and spy.sma50 is not None and spy.close > spy.sma50:
        return "NEUTRAL/CAUTION — SPY < 200SMA but reclaiming 50SMA (bounce in a downtrend)"
    return "BEAR — SPY below 200SMA and 50SMA"


def dist_phrase(n: Optional[int]) -> str:
    if n is None:
        return "n/a"
    if n <= 2:
        return f"{n} (healthy)"
    if n <= 4:
        return f"{n} (caution building)"
    if n == 5:
        return f"{n} (UNDER PRESSURE)"
    return f"{n} (SERIOUS — defend / raise cash)"


def regime_block(spy: Metrics, indices: List[Metrics]):
    print(f"\n{'#' * 78}\n#  MARKET REGIME  (as of {spy.asof})\n{'#' * 78}")
    pv50 = spy.pct_vs(spy.sma50)
    pv200 = spy.pct_vs(spy.sma200)
    verdict = regime_verdict(spy)

    n_up = sum(1 for m in indices if m.trend_score is not None and m.trend_score >= 3)
    breadth = f"{n_up}/{len(indices)} headline indices in an uptrend (score ≥3)"

    print(f"\n  VERDICT: {verdict}")
    print(f"  SPY: {spy.close:.2f}   vs50: {pct(pv50)}   vs200: {pct(pv200)}   "
          f"50SMA slope: {'UP' if spy.sma50_slope_up else 'DOWN'}")
    print(f"  Breadth: {breadth}")
    # equal-weight vs cap-weight divergence
    rsp = next((m for m in indices if m.symbol == "RSP"), None)
    if rsp and rsp.ret_21d is not None and spy.ret_21d is not None:
        diff = rsp.ret_21d - spy.ret_21d
        note = "broad participation" if diff >= 0 else "narrow / mega-cap-led (RSP lagging SPY)"
        print(f"  Participation: RSP−SPY 21d = {pct(diff)}  → {note}")

    # ---- distribution-day breadth deterioration ----
    qqq = next((m for m in indices if m.symbol == "QQQ"), None)
    spy_dd = spy.dist_days
    qqq_dd = qqq.dist_days if qqq else None
    print(f"  Distribution days (last 25 sessions, institutional selling):")
    print(f"      SPY {dist_phrase(spy_dd)}   |   QQQ {dist_phrase(qqq_dd)}")
    worst = max([d for d in (spy_dd, qqq_dd) if d is not None], default=0)
    if worst >= 5:
        print("      ⚠  An uptrend with 5+ distribution days is deteriorating even if "
              "price looks fine — tighten stops, throttle new risk.")
    elif worst >= 3:
        print("      ◦  Selling is accumulating; not a sell signal, but stop adding "
              "aggressively until it resets.")
    if spy_dd is not None and qqq_dd is not None and qqq_dd - spy_dd >= 2:
        print("      ◦  QQQ carrying more distribution than SPY → tech is where the "
              "institutional selling is concentrated (confirms the rotation).")


def takeaways(indices, sectors, industries):
    print(f"\n{'#' * 78}\n#  TAKEAWAYS\n{'#' * 78}\n")

    def top(rows, n=3):
        r = sorted([m for m in rows if m.rs_21d is not None], key=lambda m: m.rs_21d, reverse=True)
        return r[:n]

    def bottom(rows, n=3):
        r = sorted([m for m in rows if m.rs_21d is not None], key=lambda m: m.rs_21d)
        return r[:n]

    spy = next((m for m in indices if m.symbol == "SPY"), None)
    qqq = next((m for m in indices if m.symbol == "QQQ"), None)
    iwm = next((m for m in indices if m.symbol == "IWM"), None)

    if qqq and iwm and qqq.rs_21d is not None and iwm.rs_21d is not None:
        if iwm.rs_21d > qqq.rs_21d:
            print("  • ROTATION: small-caps (IWM) leading mega-tech (QQQ). "
                  "Lean toward broad/value/small over crowded semis & tech.")
        else:
            print("  • Mega-tech (QQQ) still leading small-caps (IWM).")

    print("\n  Strongest sectors (RS vs SPY):")
    for m in top(sectors):
        print(f"     {m.symbol:<5}{m.label:<24}{pct(m.rs_21d)}  {trend_word(m):<10} risk:{risk_word(m)}")
    print("  Weakest sectors — avoid / fade candidates:")
    for m in bottom(sectors):
        print(f"     {m.symbol:<5}{m.label:<24}{pct(m.rs_21d)}  {trend_word(m):<10} risk:{risk_word(m)}")

    print("\n  Industry leaders that are ALSO lower-risk (uptrend + non-HIGH vol):")
    cand = [m for m in industries
            if m.trend_score is not None and m.trend_score >= 3
            and m.rs_21d is not None and m.rs_21d > 0
            and risk_word(m) != "HIGH"]
    cand = sorted(cand, key=lambda m: m.rs_21d, reverse=True)[:6]
    if cand:
        for m in cand:
            print(f"     {m.symbol:<5}{m.label:<24}{pct(m.rs_21d)}  vol:{(m.vol_20d or 0)*100:4.0f}%  {trend_word(m)}")
    else:
        print("     (none — strength is concentrated in high-vol groups; size down)")

    smh = next((m for m in industries if m.symbol == "SMH"), None)
    if smh:
        rank = sorted([m for m in industries if m.rs_21d is not None],
                      key=lambda m: m.rs_21d, reverse=True)
        pos = next((i + 1 for i, m in enumerate(rank) if m.symbol == "SMH"), None)
        print(f"\n  Semis (SMH) reality check: RS rank {pos}/{len(rank)} industries, "
              f"trend={trend_word(smh)}, risk={risk_word(smh)}, 21d={pct(smh.ret_21d)}")


# ---- position radar -------------------------------------------------------

def load_positions(cli_csv: Optional[str], cli_file: Optional[str]) -> Tuple[List[str], str]:
    """Resolve held/watched tickers. Priority: --positions > --positions-file >
    the active breakout watchlist. Returns (tickers, source-label)."""
    if cli_csv:
        toks = [t.strip().upper() for t in cli_csv.split(",") if t.strip()]
        return toks, "--positions"
    if cli_file:
        try:
            with open(cli_file) as f:
                toks = [ln.strip().upper() for ln in f if ln.strip() and not ln.startswith("#")]
            return toks, cli_file
        except OSError as e:
            print(f"  ! could not read {cli_file}: {e}")
            return [], cli_file
    # default: the active watchlist
    try:
        with open(WATCHLIST_FILE) as f:
            data = json.load(f)
        toks = [t.upper() for t in data.keys()]
        return toks, f"{WATCHLIST_FILE} (active watchlist)"
    except (OSError, ValueError):
        return [], "(none)"


def position_status(m: Metrics) -> Tuple[str, int]:
    """Return (label, severity) — severity 0=red,1=yellow,2=green for sorting."""
    if m.trend_score is None or m.sma50 is None:
        return "?", 1
    lost_50 = m.close < m.sma50
    if m.trend_score <= 1 or (lost_50 and (m.rs_21d or 0) < 0):
        return "🔴 RED", 0
    if lost_50 or m.trend_score == 2 or (m.rs_21d or 0) < 0 or (m.sma20 and m.close < m.sma20):
        return "🟡 WARN", 1
    return "🟢 OK", 2


def position_radar(positions: List[Metrics], source: str,
                   group_metrics: Dict[str, Metrics]):
    print(f"\n{'#' * 78}\n#  POSITION RADAR  (source: {source})\n{'#' * 78}")
    if not positions:
        print("\n  No positions resolved. Pass --positions AMD,GFS or --positions-file path.")
        return

    ranked = sorted(positions, key=lambda m: (position_status(m)[1],
                                              -(m.rs_21d if m.rs_21d is not None else -9)))
    print(f"\n{'sym':<6}{'status':<9}{'stack':<7}{'trend':<10}{'21d':>8}{'RSvSPY':>8}"
          f"{'risk':>6}  {'group':<6}{'group trend':<12}")
    print("-" * 78)
    for m in ranked:
        status, _ = position_status(m)
        g = SECTOR_MAP.get(m.symbol, "")
        gm = group_metrics.get(g)
        g_trend = ""
        if gm:
            g_trend = f"{trend_word(gm)} {pct(gm.rs_21d,0).strip()}"
        print(f"{m.symbol:<6}{status:<9}{stack_glyph(m):<7}{trend_word(m):<10}"
              f"{pct(m.ret_21d,8)}{pct(m.rs_21d,8)}{risk_word(m):>6}  {g:<6}{g_trend:<12}")

    # --- sector-level rollup: groups you're positioned in that are turning red ---
    groups: Dict[str, List[str]] = {}
    for m in positions:
        g = SECTOR_MAP.get(m.symbol)
        if g:
            groups.setdefault(g, []).append(m.symbol)

    weak_groups = []
    for g, members in groups.items():
        gm = group_metrics.get(g)
        if gm is None:
            continue
        is_weak = (gm.trend_score is not None and gm.trend_score <= 2) or (gm.rs_21d or 0) < 0
        if is_weak:
            weak_groups.append((g, members, gm))

    print()
    if weak_groups:
        print("  ⚠  GROUP ALERTS — you hold names in sectors/industries that are weak or red:")
        for g, members, gm in sorted(weak_groups, key=lambda x: (x[2].rs_21d or 0)):
            print(f"     {g:<5}{trend_word(gm):<10}RS {pct(gm.rs_21d).strip():<7} risk:{risk_word(gm):<5}"
                  f"→ holdings: {', '.join(members)}")
        print("     Consider trimming/hedging these before adding elsewhere.")
    else:
        print("  ✓  No group alerts — every mapped holding sits in a sector/industry "
              "that's still in gear.")

    reds = [m for m in positions if position_status(m)[1] == 0]
    if reds:
        print(f"\n  🔴 Individually broken (lost 50SMA + negative RS): "
              f"{', '.join(m.symbol for m in reds)}")


# ---- snapshot + compare ---------------------------------------------------

async def snapshot(client, asof, pos_tickers) -> dict:
    """Compute the full metric set as of `asof` (None = today)."""
    bench = await compute(client, BENCHMARK, "S&P 500", None, asof=asof)
    if bench is None:
        raise SystemExit(f"Could not fetch benchmark SPY (asof={asof})")
    bench_ret21 = bench.ret_21d
    idx, sec, ind, pos = await asyncio.gather(
        gather(client, INDICES, bench_ret21, asof=asof),
        gather(client, SECTORS, bench_ret21, asof=asof),
        gather(client, INDUSTRIES, bench_ret21, asof=asof),
        gather(client, [(t, "") for t in pos_tickers], bench_ret21, asof=asof),
    )
    spy = next((m for m in idx if m.symbol == "SPY"), bench)
    return {"idx": idx, "sec": sec, "ind": ind, "pos": pos, "spy": spy, "asof": spy.asof}


def render_full(snap: dict, pos_source: str, show_positions: bool):
    idx, sec, ind, pos, spy = snap["idx"], snap["sec"], snap["ind"], snap["pos"], snap["spy"]
    group_metrics = {m.symbol: m for m in (sec + ind + idx)}
    print("\nLegend: stack = price vs 20/50/200 SMA (▲above ▼below).  "
          "trend = stage score 0-4.  RSvSPY = 21d return minus SPY.  risk = 20d realized vol.")
    regime_block(spy, idx)
    print_table("INDEX SCOREBOARD  (ranked by 1-month relative strength)", idx)
    print_table("SECTOR ROTATION  (11 SPDR sectors, ranked by RS)", sec)
    print_table("INDUSTRY STRENGTH  (ranked by RS — where to fish, what to avoid)", ind)
    takeaways(idx, sec, ind)
    if show_positions:
        position_radar(pos, pos_source, group_metrics)
    print()


def _rank_map(rows: List[Metrics]) -> Dict[str, Tuple[int, Metrics]]:
    r = sorted([m for m in rows if m.rs_21d is not None], key=lambda m: m.rs_21d, reverse=True)
    return {m.symbol: (i + 1, m) for i, m in enumerate(r)}


def _rs_arrow(d: Optional[float]) -> str:
    if d is None:
        return " "
    return "▲" if d > 0.0001 else ("▼" if d < -0.0001 else "·")


def diff_group(title: str, rows_a: List[Metrics], rows_b: List[Metrics]):
    ra, rb = _rank_map(rows_a), _rank_map(rows_b)
    deltas = []
    for s, (rank_b, mb) in rb.items():
        if s not in ra:
            continue
        rank_a, ma = ra[s]
        d_rs = (mb.rs_21d - ma.rs_21d) if (mb.rs_21d is not None and ma.rs_21d is not None) else None
        deltas.append((s, ma.label, rank_a, rank_b, ma, mb, d_rs))
    deltas.sort(key=lambda x: (x[6] if x[6] is not None else -99), reverse=True)

    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")
    print(f"{'sym':<5}{'name':<22}{'rank Δ':<12}{'RS  then→now':<18}{'ΔRS':>7}  "
          f"{'trend then→now':<22}")
    print("-" * 78)
    for s, label, rank_a, rank_b, ma, mb, d_rs in deltas:
        move = rank_a - rank_b
        rank_str = f"#{rank_a}→#{rank_b} ({'+' if move > 0 else ''}{move})"
        rs_str = f"{pct(ma.rs_21d,0).strip()}→{pct(mb.rs_21d,0).strip()}"
        ta, tb = trend_word(ma), trend_word(mb)
        trend_str = tb if ta == tb else f"{ta}→{tb}"
        print(f"{s:<5}{label[:21]:<22}{rank_str:<12}{rs_str:<18}"
              f"{_rs_arrow(d_rs)}{pct(d_rs,6)}  {trend_str:<22}")


def render_compare(snap_a: dict, snap_b: dict, pos_source: str, show_positions: bool):
    a_date, b_date = snap_a["asof"], snap_b["asof"]
    spy_a, spy_b = snap_a["spy"], snap_b["spy"]
    qqq_a = next((m for m in snap_a["idx"] if m.symbol == "QQQ"), None)
    qqq_b = next((m for m in snap_b["idx"] if m.symbol == "QQQ"), None)

    print(f"\n{'#' * 78}\n#  WHAT CHANGED:  {a_date}  →  {b_date}\n{'#' * 78}")
    print(f"\n  Regime:  {regime_verdict(spy_a)}")
    print(f"        →  {regime_verdict(spy_b)}")
    print(f"\n  SPY:           {spy_a.close:.2f} → {spy_b.close:.2f}  "
          f"({pct(spy_b.close / spy_a.close - 1).strip()})    "
          f"vs50: {pct(spy_a.pct_vs(spy_a.sma50)).strip()} → {pct(spy_b.pct_vs(spy_b.sma50)).strip()}")
    print(f"  Distribution:  SPY {dist_phrase(spy_a.dist_days)} → {dist_phrase(spy_b.dist_days)}")
    if qqq_a and qqq_b:
        print(f"                 QQQ {dist_phrase(qqq_a.dist_days)} → {dist_phrase(qqq_b.dist_days)}")

    def breadth(snap):
        return sum(1 for m in snap["idx"] if m.trend_score is not None and m.trend_score >= 3)
    print(f"  Breadth:       {breadth(snap_a)}/{len(snap_a['idx'])} → "
          f"{breadth(snap_b)}/{len(snap_b['idx'])} indices in uptrend")

    diff_group(f"INDEX ROTATION  (Δ rank by RS, biggest gainers first)", snap_a["idx"], snap_b["idx"])
    diff_group(f"SECTOR ROTATION  (Δ rank by RS)", snap_a["sec"], snap_b["sec"])
    diff_group(f"INDUSTRY ROTATION  (Δ rank by RS)", snap_a["ind"], snap_b["ind"])

    if show_positions:
        a = {m.symbol: m for m in snap_a["pos"]}
        b = {m.symbol: m for m in snap_b["pos"]}
        worse, better = [], []
        for s, mb in b.items():
            if s not in a:
                continue
            la, sev_a = position_status(a[s])
            lb, sev_b = position_status(mb)
            d_rs = None
            if a[s].rs_21d is not None and mb.rs_21d is not None:
                d_rs = mb.rs_21d - a[s].rs_21d
            if sev_b < sev_a:
                worse.append((s, la, lb, d_rs))
            elif sev_b > sev_a:
                better.append((s, la, lb, d_rs))

        print(f"\n{'#' * 78}\n#  POSITION FLIPS  (source: {pos_source})\n{'#' * 78}")
        if worse:
            print("\n  🔻 DETERIORATED:")
            for s, la, lb, d_rs in sorted(worse, key=lambda x: (x[3] if x[3] is not None else 0)):
                print(f"     {s:<6}{la} → {lb}    ΔRS {pct(d_rs).strip()}")
        if better:
            print("\n  🔺 IMPROVED:")
            for s, la, lb, d_rs in sorted(better, key=lambda x: -(x[3] if x[3] is not None else 0)):
                print(f"     {s:<6}{la} → {lb}    ΔRS {pct(d_rs).strip()}")
        if not worse and not better:
            print("\n  No status flips between the two dates.")
        # biggest RS movers regardless of flip
        movers = []
        for s, mb in b.items():
            if s in a and a[s].rs_21d is not None and mb.rs_21d is not None:
                movers.append((s, mb.rs_21d - a[s].rs_21d))
        movers.sort(key=lambda x: x[1])
        if movers:
            losers = ", ".join(f"{s} {pct(d).strip()}" for s, d in movers[:5])
            winners = ", ".join(f"{s} {pct(d).strip()}" for s, d in movers[-5:][::-1])
            print(f"\n  Biggest RS losers:  {losers}")
            print(f"  Biggest RS gainers: {winners}")
    print()


# ---- main -----------------------------------------------------------------

async def main(args):
    api_key = os.environ.get("TRADIER_API_KEY")
    if not api_key:
        raise SystemExit("Set TRADIER_API_KEY")

    pos_tickers, pos_source = ([], "(disabled)")
    if not args.no_positions:
        pos_tickers, pos_source = load_positions(args.positions, args.positions_file)

    async with TradierClient(api_key=api_key) as client:
        if args.compare:
            parts = [p.strip() for p in args.compare.split(",")]
            if len(parts) != 2:
                raise SystemExit("--compare needs two dates: DATE1,DATE2")
            d1, d2 = date.fromisoformat(parts[0]), date.fromisoformat(parts[1])
            snap_a, snap_b = await asyncio.gather(
                snapshot(client, d1, pos_tickers),
                snapshot(client, d2, pos_tickers),
            )
            render_compare(snap_a, snap_b, pos_source, not args.no_positions)
            return

        asof = date.fromisoformat(args.asof) if args.asof else None
        snap = await snapshot(client, asof, pos_tickers)

    render_full(snap, pos_source, not args.no_positions)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Top-down pre-market market-conditions report")
    ap.add_argument("--positions", help="comma-separated tickers to flag, e.g. AMD,GFS,CMI")
    ap.add_argument("--positions-file", help="file with one ticker per line")
    ap.add_argument("--no-positions", action="store_true",
                    help="skip the position radar")
    ap.add_argument("--asof", help="reconstruct the report as of a past date, YYYY-MM-DD")
    ap.add_argument("--compare", metavar="DATE1,DATE2",
                    help="print only the deltas between two dates (rotation view)")
    asyncio.run(main(ap.parse_args()))
