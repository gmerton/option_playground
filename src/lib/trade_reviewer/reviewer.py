"""
Core agentic review loop.

review_trade(trade_dict) -> str
    Review a past trade against O'Neill principles.

evaluate_proposal(ticker) -> str
    Evaluate a prospective trade in real time against O'Neill principles.
"""

from __future__ import annotations

import json
import time

import anthropic

from lib.trade_reviewer.principles import SYSTEM_PROMPT, PROPOSAL_SYSTEM_PROMPT
from lib.trade_reviewer.tools import TOOL_DEFS, dispatch_tool

_client = anthropic.Anthropic()
# Primary model; falls back to the next in list on 529 Overloaded
MODELS = ["claude-sonnet-4-6", "claude-opus-4-6"]
MAX_TOKENS = 4096


def _create_with_retry(**kwargs):
    """Call _client.messages.create, falling back through MODELS on 529 Overloaded."""
    for i, model in enumerate(MODELS):
        kwargs["model"] = model
        if i > 0:
            print(f"  [fallback] switching to {model}...")
        try:
            return _client.messages.create(**kwargs)
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and i < len(MODELS) - 1:
                print(f"  [overloaded] {model} is overloaded, trying next model...")
                continue
            raise


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
        response = _create_with_retry(

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


def evaluate_proposal(ticker: str) -> str:
    """
    Evaluate a prospective trade in real time.

    Args:
        ticker: Stock symbol to evaluate, e.g. 'PHIN'

    Returns:
        The final BUY / WAIT / PASS recommendation from Claude.
    """
    from datetime import date
    today = date.today().isoformat()

    user_msg = (
        f"I'm considering buying {ticker} right now ({today}). "
        f"Please evaluate this prospective trade against the Stage 2 Breakout principle "
        f"and give me a clear BUY, WAIT, or PASS recommendation."
    )

    messages = [{"role": "user", "content": user_msg}]

    while True:
        response = _create_with_retry(

            max_tokens=MAX_TOKENS,
            system=PROPOSAL_SYSTEM_PROMPT,
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
                    print(f"  [tool] {block.name}({json.dumps(block.input)})")
                    result_str = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        return f"(unexpected stop_reason: {response.stop_reason})"
