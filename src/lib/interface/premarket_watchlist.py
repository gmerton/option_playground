"""
Pre-market watchlist scanner — Martin Luk / Qullamaggie inspired.

EOD mode:
  - Potent: yesterday's leaders in Stage 2 near pivot, EMA 9>21>50, ADR>3.5%
  - Leader: Stage 2 + EMA Lead + strong 1-month/3-month RS (>15%/30%)

Pre-market mode:
  - EOD scan + yfinance pre-market gap enrichment
  - Categorizes: EP (≥8%), Gap-up (2–8%), Near-pivot (<2%)

Filters applied in order for efficiency:
  1. Fetch 420 calendar days of OHLCV (skip if no data / <60 bars)
  2. Stage 2: SMA50 > SMA150 > SMA200, close > SMA50
  3. ADR(20) > 3.5%
  4. 5-day avg dollar volume > $10M
  5. EMA stack (9>21>50), pivot detection, RS
  6. Potent / Leader classification
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from lib.tradier.get_daily_history import get_daily_history
from lib.tradier.tradier_client_wrapper import TradierClient

# ── Default ticker universe ───────────────────────────────────────────────────

_FOOL_LIST: List[str] = [
    "AAPL", "ABNB", "ACN", "ADBE", "ADSK", "AMD", "AMGN", "AMZN", "ANET",
    "BAND", "BKNG", "BLD", "BROS", "CART", "CASY", "CBOE", "CELH",
    "CME", "CMG", "CMI", "COST", "CRWD", "CTAS", "DASH", "DDOG",
    "DIS", "DOCU", "DXCM", "EME", "ENPH", "FDX", "FICO", "FIX",
    "FTNT", "GEHC", "GILD", "GOOG", "GRMN", "HCA", "HEI", "HUBS",
    "HWM", "IBKR", "IDXX", "INTU", "KNSL", "LRCX", "LULU", "MA",
    "MAR", "MCK", "MELI", "META", "MNST", "MSFT", "NDAQ", "NET",
    "NFLX", "NOW", "NVDA", "NVO", "ODFL", "OKTA", "ONON", "PAYC",
    "PGR", "PSTG", "RKLB", "ROKU", "RPM", "SBUX", "SHOP", "SHW",
    "SNOW", "SNPS", "SPOT", "STRL", "TDG", "TEAM", "TJX", "TMUS",
    "TOST", "TSCO", "TSLA", "TTD", "TYL", "ULTA", "UNP", "UPST",
    "V", "VEEV", "VRTX", "WDAY", "WEX", "WING", "WM", "WSM",
    "WSO", "ZM", "ZS",
]

_HOLDINGS_LIST: List[str] = [
    "AMD", "AMZN", "AXP", "GOOG", "GILD", "POOL", "TSM",
    "WDC", "CRUS", "YETI", "ZM", "PLXS",
]

DEFAULT_UNIVERSE: List[str] = sorted(set(_FOOL_LIST + _HOLDINGS_LIST))


# ── Indicator helpers ─────────────────────────────────────────────────────────

def _sma(values: List[float], window: int) -> Optional[float]:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def _ema_series(values: List[float], span: int) -> List[float]:
    s = pd.Series(values)
    return list(s.ewm(span=span, adjust=False).mean())


def _detect_pivot(
    highs: List[float],
    lows: List[float],
    base_lookback_days: int = 90,
    min_base_len_bars: int = 15,
    min_depth: float = 0.05,
    max_depth: float = 0.45,
) -> Optional[float]:
    """
    Find the consolidation pivot (= base high) using the same logic as
    pivot_detector._detect_base_simple.

    Returns the pivot price, or None if no valid base is found.
    """
    n = len(highs)
    if n < min_base_len_bars:
        return None

    start_i = max(0, n - base_lookback_days)
    window_lows = lows[start_i:]
    if not window_lows:
        return None

    rel_low_i = min(range(len(window_lows)), key=lambda i: window_lows[i])
    low_i = start_i + rel_low_i

    base_len = n - low_i
    if base_len < min_base_len_bars:
        return None

    base_high = max(highs[low_i:])
    base_low = min(lows[low_i:])

    if base_high <= 0:
        return None

    depth = (base_high - base_low) / base_high
    if depth < min_depth or depth > max_depth:
        return None

    return float(base_high)


# ── Per-ticker EOD screen ─────────────────────────────────────────────────────

async def screen_ticker(client: TradierClient, ticker: str) -> Optional[Dict[str, Any]]:
    """
    Screen a single ticker for EOD watchlist inclusion.

    Returns a dict if the stock qualifies as Potent or Leader; None otherwise.
    A single Tradier history call is made per ticker (no duplicate fetches).
    """
    end = date.today()
    start = end - timedelta(days=420)

    try:
        df = await get_daily_history(ticker, start, end, client=client)
    except Exception:
        return None

    if df is None or len(df) < 60:
        return None

    df = df.sort_index()
    closes = list(df["close"].astype(float))
    highs  = list(df["high"].astype(float))
    lows   = list(df["low"].astype(float))
    opens  = list(df["open"].astype(float))
    vols   = list(df["volume"].astype(float))
    n = len(closes)

    # ── Stage 2: SMA50 > SMA150 > SMA200, close > SMA50 ──────────────────────
    sma50  = _sma(closes, 50)
    sma150 = _sma(closes, 150)
    sma200 = _sma(closes, 200)

    if sma50 is None or sma150 is None or sma200 is None:
        return None

    close_now = closes[-1]
    if not (sma50 > sma150 > sma200 and close_now > sma50):
        return None

    # ── ADR(20) > 3.5% ────────────────────────────────────────────────────────
    ranges_pct = [(h - l) / c * 100 for h, l, c in zip(highs, lows, closes)]
    adr20 = _sma(ranges_pct, 20)
    if adr20 is None or adr20 < 3.5:
        return None

    # ── 5-day avg dollar volume > $10M ────────────────────────────────────────
    dollar_vols = [c * v for c, v in zip(closes, vols)]
    avg_dolvol_5d = _sma(dollar_vols, 5)
    if avg_dolvol_5d is None or avg_dolvol_5d < 10_000_000:
        return None

    # ── EMA stack (Luk's Lead: 9 > 21 > 50) ──────────────────────────────────
    ema9_s  = _ema_series(closes, 9)
    ema21_s = _ema_series(closes, 21)
    ema50_s = _ema_series(closes, 50)
    ema_lead = bool(ema9_s[-1] > ema21_s[-1] > ema50_s[-1])

    # ── 1-month and 3-month RS ────────────────────────────────────────────────
    close_21d = closes[-(21 + 1)] if n > 21 else None
    close_63d = closes[-(63 + 1)] if n > 63 else None

    def _pct(now: float, then: Optional[float]) -> Optional[float]:
        if then and then > 0:
            return round((now - then) / then * 100, 1)
        return None

    pct_1m = _pct(close_now, close_21d)
    pct_3m = _pct(close_now, close_63d)

    # ── Pivot (exclude today so tomorrow's breakout is the event) ─────────────
    pivot = _detect_pivot(highs[:-1], lows[:-1])
    pivot_dist_pct: Optional[float] = None
    if pivot is not None and pivot > 0:
        pivot_dist_pct = round((close_now - pivot) / pivot * 100, 1)

    # ── Previous day green candle (for Potent) ────────────────────────────────
    prev_green = bool(closes[-2] > opens[-2]) if n >= 2 else False
    prev_high  = round(highs[-2], 2) if n >= 2 else None

    # ── Potent: Stage2 + EMA Lead + ADR + prev green + near pivot (within 8%) ─
    near_pivot = (pivot_dist_pct is not None) and (-8 <= pivot_dist_pct <= 8)
    is_potent = bool(ema_lead and prev_green and near_pivot)

    # ── Leader: Stage2 + EMA Lead + 1m>15% + 3m>30% ─────────────────────────
    is_leader = bool(
        ema_lead
        and pct_1m is not None and pct_1m > 15
        and pct_3m is not None and pct_3m > 30
    )

    if not is_potent and not is_leader:
        return None

    return {
        "ticker":           ticker,
        "close":            round(close_now, 2),
        "pivot":            round(pivot, 2) if pivot else None,
        "pivot_dist_pct":   pivot_dist_pct,
        "adr20":            round(adr20, 1),
        "ema_lead":         ema_lead,
        "pct_1m":           pct_1m,
        "pct_3m":           pct_3m,
        "prev_green":       prev_green,
        "prev_high":        prev_high,
        "avg_dolvol_5d_m":  round(avg_dolvol_5d / 1_000_000, 1),
        "is_potent":        is_potent,
        "is_leader":        is_leader,
    }


# ── Concurrent EOD scan ───────────────────────────────────────────────────────

async def run_eod_scan(
    client: TradierClient,
    tickers: List[str],
) -> List[Dict[str, Any]]:
    """Concurrently screen all tickers and return those that pass."""
    tasks = [screen_ticker(client, t) for t in tickers]
    raw = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in raw if isinstance(r, dict)]


# ── Pre-market gap enrichment ─────────────────────────────────────────────────

def enrich_premarket(eod_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Overlay pre-market price data on EOD results using yfinance.
    Categorizes each stock as EP (≥8%), GAP_UP (2–8%), or NEAR_PIVOT (<2%).
    """
    try:
        import yfinance as yf  # optional dependency
    except ImportError:
        print("yfinance not installed. Run: pip install yfinance")
        return []

    enriched: List[Dict[str, Any]] = []
    for row in eod_results:
        ticker = row["ticker"]
        pm_price: float = row["close"]
        gap_pct: float = 0.0

        try:
            fi = yf.Ticker(ticker).fast_info
            # fast_info supports dict-style access
            raw_pm = fi.get("preMarketPrice") if hasattr(fi, "get") else None
            if raw_pm is None:
                # fallback: attribute-style access in newer yfinance
                raw_pm = getattr(fi, "pre_market_price", None)
            if raw_pm is not None:
                pm_price = float(raw_pm)
                gap_pct = round((pm_price - row["close"]) / row["close"] * 100, 1)
        except Exception:
            pass

        if gap_pct >= 8:
            category = "EP"
        elif gap_pct >= 2:
            category = "GAP_UP"
        else:
            category = "NEAR_PIVOT"

        enriched.append({
            **row,
            "pm_price":    round(pm_price, 2),
            "gap_pct":     gap_pct,
            "pm_category": category,
        })

    # Sort: EP → GAP_UP → NEAR_PIVOT, then by gap % descending within each
    cat_order = {"EP": 0, "GAP_UP": 1, "NEAR_PIVOT": 2}
    enriched.sort(key=lambda x: (cat_order.get(x["pm_category"], 9), -x.get("gap_pct", 0)))
    return enriched


# ── Console output formatters ─────────────────────────────────────────────────

def format_eod_output(results: List[Dict[str, Any]], as_of: date) -> str:
    lines = [f"\n=== EOD WATCHLIST — {as_of} (for tomorrow) ===\n"]

    potent  = sorted([r for r in results if r["is_potent"]],
                     key=lambda x: x.get("pivot_dist_pct") or 0)
    leaders = sorted([r for r in results if r["is_leader"] and not r["is_potent"]],
                     key=lambda x: -(x.get("pct_1m") or 0))

    if potent:
        lines.append("* POTENT — yesterday's leaders near pivot")
        for r in potent:
            ema_tag = "EMA:Lead" if r["ema_lead"] else "EMA:--"
            rs = f"1M:{r['pct_1m']:+.0f}%" if r["pct_1m"] is not None else ""
            pdist = f"({r['pivot_dist_pct']:+.1f}%)" if r["pivot_dist_pct"] is not None else ""
            pivot_str = f"pivot ${r['pivot']:.2f} {pdist}" if r["pivot"] else "no pivot"
            lines.append(
                f"  {r['ticker']:<6} close ${r['close']:<9.2f}"
                f"{pivot_str:<26}  ADR {r['adr20']:.1f}%  {ema_tag}  {rs}"
                f"  vol ${r['avg_dolvol_5d_m']:.0f}M"
            )
    else:
        lines.append("* POTENT — no candidates today")

    lines.append("")

    if leaders:
        lines.append("^ LEADERS — 1-month RS standouts")
        for r in leaders:
            ema_tag = "EMA:Lead" if r["ema_lead"] else "EMA:--"
            pd_val  = r.get("pivot_dist_pct")
            if pd_val is None:
                near_str = "no base"
            elif abs(pd_val) <= 8:
                near_str = f"near pivot ({pd_val:+.1f}%)"
            else:
                near_str = f"pivot dist ({pd_val:+.1f}%)"
            lines.append(
                f"  {r['ticker']:<6} close ${r['close']:<9.2f}"
                f"1M:{r['pct_1m']:+.0f}%  3M:{r['pct_3m']:+.0f}%  "
                f"ADR {r['adr20']:.1f}%  {ema_tag}  {near_str}"
                f"  vol ${r['avg_dolvol_5d_m']:.0f}M"
            )
    else:
        lines.append("^ LEADERS — no candidates today")

    lines.append("")
    total = len(set(r["ticker"] for r in results))
    lines.append(f"Total candidates: {total}  (Potent: {len(potent)}, Leaders: {len(leaders)})")
    lines.append("")
    return "\n".join(lines)


def format_premarket_output(enriched: List[Dict[str, Any]], as_of: date) -> str:
    lines = [f"\n=== PRE-MARKET WATCHLIST — {as_of} ===\n"]

    ep      = [r for r in enriched if r["pm_category"] == "EP"]
    gap_up  = [r for r in enriched if r["pm_category"] == "GAP_UP"]
    near_pv = [r for r in enriched if r["pm_category"] == "NEAR_PIVOT"]

    if ep:
        lines.append("!! EP CANDIDATES (gap >=8% — episodic pivot)")
        for r in ep:
            lines.append(
                f"  {r['ticker']:<6} +{r['gap_pct']:.1f}%  "
                f"pm ${r['pm_price']:.2f}  close ${r['close']:.2f}  "
                f"pivot ${r['pivot']:.2f}  "
                f"-> buy break of 1-min high, stop day low"
            )
    else:
        lines.append("!! EP CANDIDATES — none")

    lines.append("")

    if gap_up:
        lines.append(">> GAP-UP WATCH (gap 2-8% — PDH breakout)")
        for r in gap_up:
            ema_tag = "Stage2/Lead" if r["ema_lead"] else "Stage2"
            pdh = f"PDH ${r['prev_high']:.2f}" if r.get("prev_high") else ""
            lines.append(
                f"  {r['ticker']:<6} +{r['gap_pct']:.1f}%  "
                f"pm ${r['pm_price']:.2f}  {ema_tag}  "
                f"pivot ${r['pivot']:.2f}  {pdh}  "
                f"-> watch open"
            )
    else:
        lines.append(">> GAP-UP WATCH — none")

    lines.append("")

    if near_pv:
        lines.append("-- NEAR-PIVOT WATCH (no gap, in setup)")
        for r in near_pv:
            gap_str = f"+{r['gap_pct']:.1f}%" if r["gap_pct"] > 0 else "flat"
            lines.append(
                f"  {r['ticker']:<6} {gap_str:<8}  "
                f"pivot ${r['pivot']:.2f}  close ${r['close']:.2f}  "
                f"ADR {r['adr20']:.1f}%  "
                f"-> watch for RTH breakout"
            )
    else:
        lines.append("-- NEAR-PIVOT WATCH — none")

    lines.append("")
    return "\n".join(lines)
