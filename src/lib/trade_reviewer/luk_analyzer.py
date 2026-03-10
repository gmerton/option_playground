"""
Reverse-engineer Martin Luk's stock picks by analyzing the technical setup
present on the date he mentioned each ticker.

analyze_ticker(ticker, obs_date, comment, direction) -> str
    Fetches price history, computes vol compression / distribution metrics,
    and asks Claude to identify the pattern(s) that likely drove the call.
    Applies long-side rules (Luk/Qullamaggie/O'Neil) or short-side rules
    (Weinstein/Morales/Kacher) depending on direction.

synthesize_patterns(entries) -> str
    Across all analyzed entries, distills common patterns into screener rules.
"""

from __future__ import annotations

import json
from statistics import mean

import anthropic

from lib.trade_reviewer.tools import TOOL_DEFS, dispatch_tool

_client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# ── Metric helpers ────────────────────────────────────────────────────────────

def _compute_vol_compression(price_data: dict) -> dict:
    """
    Compute volatility compression metrics from recent_10_days bars.
    Used for long setups: look for tightening range + drying volume before a breakout.
    """
    recent = price_data.get("recent_10_days", [])
    vol_50d = price_data.get("vol_50d_avg") or 0

    if len(recent) < 6:
        return {}

    def _range_pct(bar):
        c = bar.get("close") or 1
        return (bar.get("high", c) - bar.get("low", c)) / c * 100

    last5 = recent[-5:]
    prior5 = recent[-10:-5] if len(recent) >= 10 else recent[:-5]

    last5_range = mean([_range_pct(b) for b in last5])
    prior5_range = mean([_range_pct(b) for b in prior5]) if prior5 else last5_range
    last5_vol = mean([b.get("volume", 0) for b in last5])
    contraction = (last5_range - prior5_range) / prior5_range * 100 if prior5_range else 0

    return {
        "last5_avg_range_pct":   round(last5_range, 2),
        "prior5_avg_range_pct":  round(prior5_range, 2),
        "range_contraction_pct": round(contraction, 1),    # negative = compression
        "is_range_contracting":  contraction < -10,         # >10% tighter = yes
        "last5_avg_vol":         round(last5_vol),
        "last5_vol_vs_50d_pct":  round(last5_vol / vol_50d * 100, 1) if vol_50d else None,
        "is_volume_drying_up":   (last5_vol / vol_50d < 0.80) if vol_50d else None,
    }


def _compute_distribution(price_data: dict) -> dict:
    """
    Compute distribution metrics from recent_10_days bars.
    Used for short setups: look for heavy-volume down days + light-volume bounces.
    """
    recent = price_data.get("recent_10_days", [])
    vol_50d = price_data.get("vol_50d_avg") or 0

    if len(recent) < 3:
        return {}

    down_days = [b for b in recent if b.get("close", 0) < b.get("open", 0)]
    up_days   = [b for b in recent if b.get("close", 0) >= b.get("open", 0)]

    heavy_down = [b for b in down_days if vol_50d and b.get("volume", 0) > vol_50d * 1.25]
    light_up   = [b for b in up_days   if vol_50d and b.get("volume", 0) < vol_50d * 0.75]

    avg_down_vol = mean([b.get("volume", 0) for b in down_days]) if down_days else None
    avg_up_vol   = mean([b.get("volume", 0) for b in up_days])   if up_days   else None

    return {
        "down_days_last10":              len(down_days),
        "up_days_last10":                len(up_days),
        "distribution_days_last10":      len(heavy_down),   # high-vol down days
        "light_volume_bounces_last10":   len(light_up),     # low-vol up days
        "avg_down_day_vol":              round(avg_down_vol) if avg_down_vol else None,
        "avg_up_day_vol":                round(avg_up_vol)   if avg_up_vol   else None,
        "vol_50d_avg":                   round(vol_50d)      if vol_50d      else None,
        "distribution_pattern_present":  len(heavy_down) >= 2 and len(light_up) >= 1,
    }


# ── System prompts ────────────────────────────────────────────────────────────

_LONG_ANALYSIS_SYSTEM = """\
You are a technical analyst reverse-engineering why Martin Luk (2025 US Investing Champion,
+969% return) highlighted a stock as a LONG setup on his livestream. Your job is to examine
the price data and identify the specific technical pattern(s) that likely caught his attention.

You have access to get_price_history. Call it first.

Check each of the following explicitly:

1. STAGE 2 / EMA STACK (Weinstein + Luk)
   - Price > MA50 > MA200, MA200 sloping up (compare ma200 vs ma200_10_weeks_ago)
   - EMA stack aligned: EMA9 > EMA21 > EMA50 ("Lead" category in Luk's system)

2. VOLATILITY COMPRESSION (use the vol_compression field injected into the data)
   - is_range_contracting: daily range tightening over last 5 days vs prior 5?
   - is_volume_drying_up: last 5 days avg vol < 80% of 50d avg?
   - Cite range_contraction_pct and last5_vol_vs_50d_pct

3. PIVOT / BREAKOUT PROXIMITY
   - Distance from consolidation_pivot_high_6_to_10wks_ago
   - Sitting just below pivot, breaking out, or already extended?

4. MOMENTUM (Qullamaggie)
   - pct_change_1m and pct_change_3m: strong prior momentum?

5. ADR (Luk)
   - adr_50d_pct > 5%?

Write a concise pattern summary using 3-5 bullet points. Cite actual numbers.
End with exactly one line:
SCREENER HINT: [one concrete, numeric rule that could screen for this type of setup]

Be specific. No hedging."""


_SHORT_ANALYSIS_SYSTEM = """\
You are a technical analyst reverse-engineering why Martin Luk shorted a stock on his
livestream. Apply the short-selling frameworks of Stan Weinstein (Stage Analysis),
Gil Morales & Chris Kacher (O'Neil Disciples short-selling methodology), and Luk's
EMA-cross trigger.

You have access to get_price_history. Call it first.

Check each of the following explicitly:

1. STAGE ANALYSIS (Weinstein)
   - Stage 3 topping: price breaking below or testing the 150-day (30-week) MA,
     MA200 slope flattening or rolling over (compare ma200 vs ma200_10_weeks_ago)
   - Stage 4 downtrend: price below declining MA200; bounces failing at the MA
   - Cite the exact relationship between price, MA50, and MA200

2. CLIMAX / EXHAUSTION TOP (Morales & Kacher)
   - pct_change_3m > 50% or pct_change_1m unusually large? (parabolic move)
   - Price extended well above MA50 or MA200? Compute: (price - MA200) / MA200 * 100
   - Any sign of a blow-off: wide-ranging bars, gap ups in recent_10_days?

3. EMA CROSS / BREAKDOWN TRIGGER (Luk)
   - Is the EMA stack breaking down? EMA9 < EMA21 or EMA21 < EMA50?
   - Did price recently cross below the EMA9 on the daily chart?
   - Cite the actual EMA values

4. DISTRIBUTION PATTERN (use the distribution field injected into the data)
   - distribution_days_last10: count of above-avg-volume down days
   - light_volume_bounces_last10: count of below-avg-volume up days
   - distribution_pattern_present: is the classic distribution fingerprint there?

5. EXTENSION FROM MAs (Morales & Kacher)
   - How far above MA50 and MA200 is the stock?
   - Morales/Kacher: >50% above MA200 = potential climax zone

Write a concise pattern summary using 3-5 bullet points. Cite actual numbers.
End with exactly one line:
SCREENER HINT: [one concrete, numeric rule that could screen for this type of short setup]

Be specific. No hedging."""


# ── Per-ticker analysis ───────────────────────────────────────────────────────

def analyze_ticker(ticker: str, obs_date: str, comment: str, direction: str = "long") -> str:
    """
    Analyze a single ticker on a specific date.

    direction: "long" or "short" — selects the appropriate analysis framework.
    Returns Claude's pattern description as a string.
    """
    direction = direction.lower()
    side_label = "LONG" if direction == "long" else "SHORT"
    system = _LONG_ANALYSIS_SYSTEM if direction == "long" else _SHORT_ANALYSIS_SYSTEM

    user_msg = (
        f"Martin Luk took a {side_label} position in {ticker} on {obs_date} "
        f"with this comment: \"{comment}\"\n\n"
        f"Pull the price history for {ticker} as of {obs_date} and identify the technical "
        f"pattern(s) that likely drove his decision."
    )

    messages = [{"role": "user", "content": user_msg}]

    def _dispatch(name: str, inputs: dict) -> str:
        result_str = dispatch_tool(name, inputs)
        if name == "get_price_history":
            data = json.loads(result_str)
            if direction == "long":
                data["vol_compression"] = _compute_vol_compression(data)
            else:
                data["distribution"] = _compute_distribution(data)
            result_str = json.dumps(data)
        return result_str

    while True:
        response = _client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            tools=TOOL_DEFS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "(no text response)"

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"    [tool] {block.name}({json.dumps(block.input)})")
                    result_str = _dispatch(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        return f"(unexpected stop_reason: {response.stop_reason})"


# ── Pattern synthesis ─────────────────────────────────────────────────────────

_SYNTHESIS_SYSTEM = """\
You are a quantitative strategist. You have been given technical pattern analyses for
stocks that Martin Luk highlighted on his livestream — both long and short positions.
Each analysis describes the setup present on the date he made the call.

Your job: identify common patterns within each direction (long / short) and distill
them into concrete, measurable screening criteria implementable in a stock screener.

Format your output as:

## LONG SETUPS — COMMON PATTERNS
(what appears consistently across long calls)

## LONG SETUPS — PROPOSED SCREENER RULES
(specific, numeric, directly implementable)

## SHORT SETUPS — COMMON PATTERNS
(what appears consistently across short calls)

## SHORT SETUPS — PROPOSED SCREENER RULES
(specific, numeric, directly implementable)

## EDGE CASES / VARIATIONS
(patterns that appear in some but not all setups of either direction)

Be specific. Use numbers where possible."""


def synthesize_patterns(entries: list[dict]) -> str:
    """
    Distill common patterns from a list of analyzed note entries.
    Handles both long and short entries, plus general market context notes.
    """
    context_parts = []
    ticker_parts = []

    for entry in entries:
        if entry.get("type") == "market_context":
            context_parts.append(f"- {entry['date']}: \"{entry['comment']}\"")
            continue
        direction = entry.get("direction", "long").upper()
        for ticker, analysis in (entry.get("analyses") or {}).items():
            ticker_parts.append(
                f"=== {ticker} ({direction}) on {entry['date']} ===\n"
                f"Luk's comment: \"{entry['comment']}\"\n\n"
                f"{analysis}"
            )

    if not ticker_parts:
        return "No analyzed ticker entries found."

    preamble = ""
    if context_parts:
        preamble = (
            "GENERAL MARKET CONTEXT (Luk's broader observations):\n"
            + "\n".join(context_parts)
            + "\n\n"
        )

    user_msg = (
        preamble
        + f"Here are {len(ticker_parts)} technical pattern analyses for stocks Martin Luk highlighted:\n\n"
        + "\n\n".join(ticker_parts)
        + "\n\nPlease identify the common patterns and propose concrete screening rules."
    )

    response = _client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=_SYNTHESIS_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    for block in response.content:
        if hasattr(block, "text"):
            return block.text
    return "(no text response)"
