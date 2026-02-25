"""
Core agentic review loop.

review_trade(trade_dict) -> str

Sends the trade to Claude Opus, handles tool calls in a loop until Claude
produces a final text response, then returns it.
"""

from __future__ import annotations

import json

import anthropic

from lib.trade_reviewer.principles import SYSTEM_PROMPT
from lib.trade_reviewer.tools import TOOL_DEFS, dispatch_tool

_client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"
MAX_TOKENS = 4096


def review_trade(trade: dict) -> str:
    """
    Run an agentic review of a single trade.

    Args:
        trade: dict with at least: symbol, underlying, trade_date, buy_sell,
               quantity, price, asset_category

    Returns:
        The final text analysis from Claude.
    """
    user_msg = (
        f"Please review this trade against the Stage 2 Breakout principle:\n\n"
        f"{json.dumps(trade, default=str, indent=2)}"
    )

    messages = [{"role": "user", "content": user_msg}]

    # Agentic loop — keep going until Claude stops calling tools
    while True:
        response = _client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFS,
            messages=messages,
        )

        # Append Claude's response to the conversation
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract the final text block
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "(no text response)"

        if response.stop_reason == "tool_use":
            # Execute all tool calls and feed results back
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [tool] {block.name}({json.dumps(block.input)})")
                    result_str = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason
        return f"(unexpected stop_reason: {response.stop_reason})"
