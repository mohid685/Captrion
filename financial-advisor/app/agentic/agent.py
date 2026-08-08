"""
Agentic orchestration: the LLM decides which tools to call, we execute
them, and feed results back until it produces a final answer.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.agentic.tool_definitions import TOOL_DEFINITIONS
from app.agentic.tool_executor import execute_tool, parse_tool_call_arguments
from app.core.llm_client import LLMClientError, chat_completion

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5

SYSTEM_PROMPT = """You are a financial investment advisor assistant with access to tools \
for retrieving real financial data: document search, sentiment analysis, trend prediction, \
risk metrics, current price, and financial calculations.

Call only the tools relevant to the user's specific question — do not call every tool by \
default. Base your final answer only on tool results and information the user has provided. \
Do not invent facts, figures, or events.

When a tool result includes a reliability or confidence rating, weight it accordingly in \
your answer and say so explicitly if a signal is weak. Always mention that quantitative \
signals are model estimates, not guarantees. Never present this as personalized financial \
advice — frame it as informational analysis only."""


def ask_agentic_advisor(ticker: str, question: str) -> dict[str, Any]:
    """
    Runs the tool-calling loop: the LLM decides which tools to call
    (if any), tools execute, results feed back, repeat until a final
    text answer is produced.
    """
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Ticker: {ticker.upper()}\nQuestion: {question}"},
    ]
    tool_call_log: list[dict[str, Any]] = []

    for _ in range(MAX_ITERATIONS):
        message = chat_completion(messages, tools=TOOL_DEFINITIONS)
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            return {
                "ticker": ticker.upper(),
                "question": question,
                "answer": message.get("content", ""),
                "tool_calls_made": tool_call_log,
            }

        messages.append(message)

        for call in tool_calls:
            tool_name = call["function"]["name"]
            arguments = parse_tool_call_arguments(call["function"]["arguments"])

            result = execute_tool(tool_name, arguments)

            tool_call_log.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "result_summary": _summarize_result(result),
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(result, default=str),
                }
            )

    raise LLMClientError(
        f"Agent did not produce a final answer within {MAX_ITERATIONS} tool-calling iterations"
    )


def _summarize_result(result: dict[str, Any]) -> str:
    """Short human-readable summary of a tool result, for the trace log."""
    if "error" in result:
        return f"error: {result['error']}"
    if "results" in result:  # search_documents
        return f"{len(result['results'])} document(s) found"
    keys_preview = {k: result[k] for k in list(result.keys())[:3]}
    return json.dumps(keys_preview, default=str)