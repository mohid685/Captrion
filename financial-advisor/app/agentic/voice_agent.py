"""
Conversational voice agent: a direct, opinionated financial-advisor
persona with memory of the ongoing conversation. Uses fast internal
tools plus broad-coverage external data (Alpha Vantage), rather than
the narrow locally-ingested RAG/ML tools — so it can answer about any
ticker, not just ones we've pre-loaded.
"""

from __future__ import annotations

import json
from typing import Any

from app.agentic.tool_definitions import get_voice_tool_definitions
from app.agentic.tool_executor import execute_tool, parse_tool_call_arguments
from app.core.llm_client import LLMClientError, chat_completion

MAX_ITERATIONS = 3
MAX_REPLY_CHARS = 480

VOICE_SYSTEM_PROMPT = """You are a knowledgeable, confident financial advisor speaking face to face \
with a client, continuing an ongoing conversation. You have tools for live prices, company \
fundamentals, earnings, news, and risk metrics covering any publicly traded company — use them for \
any ticker the client asks about, not just well-known ones. Never mention tools, data, sources, or \
that you "looked something up." Speak as if this knowledge is simply yours.

If the client mentions a company you don't have a ticker symbol for, use your search tool to find it first, then proceed.

Give real opinions and direct guidance the way an experienced advisor would, including calling \
something a buy, hold, or a reason for caution — but ground every claim only in what your tools \
actually return. Never invent facts. If a tool returns no data for a ticker, say so plainly rather \
than guessing.

Style:
- 2-4 sentences per reply. Natural spoken rhythm. First person ("I'd...", "I wouldn't...", "I think...").
- Address the client as "you". Weave any caution directly into the advice itself.
- No markdown, no symbols like %, $, | — say numbers the way a person would speak them.
- Use the conversation history to understand follow-ups without the client repeating context.
- Keep it tight — under 400 characters per reply."""


def _build_history_messages(conversation_history: list[dict[str, str]]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for turn in conversation_history:
        messages.append({"role": "user", "content": turn["question"]})
        messages.append({"role": "assistant", "content": turn["answer"]})
    return messages


def _fit_to_char_limit(text: str, limit: int = MAX_REPLY_CHARS) -> str:
    if len(text) <= limit:
        return text
    truncated = text[:limit]
    last_sentence_end = max(truncated.rfind(". "), truncated.rfind("! "), truncated.rfind("? "))
    if last_sentence_end > limit * 0.5:
        return truncated[: last_sentence_end + 1]
    return truncated.rsplit(" ", 1)[0] + "."


def _summarize_gathered(tool_name: str, result: dict[str, Any]) -> str:
    """Short human-readable line for the data-gathering display."""
    if "error" in result:
        return f"{tool_name}: no data available"
    if "raw_result" in result:
        raw = str(result["raw_result"])
        return f"{tool_name}: {raw[:120]}..." if len(raw) > 120 else f"{tool_name}: {raw}"
    keys_preview = ", ".join(f"{k}={result[k]}" for k in list(result.keys())[:4])
    return f"{tool_name}: {keys_preview}"


def ask_voice_advisor(
    ticker: str,
    question: str,
    conversation_history: list[dict[str, str]] | None = None,
    user_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context_note = ""
    if user_context:
        parts = []
        if user_context.get("risk_tolerance"):
            parts.append(f"risk tolerance: {user_context['risk_tolerance']}")
        if user_context.get("investment_goals"):
            parts.append(f"goals: {user_context['investment_goals']}")
        if user_context.get("holding"):
            h = user_context["holding"]
            parts.append(f"currently holds {h['shares']} shares at ${h['cost_basis']:.2f} cost basis")
        if parts:
            context_note = f" (Client context: {', '.join(parts)}.)"

    messages: list[dict[str, Any]] = [{"role": "system", "content": VOICE_SYSTEM_PROMPT}]
    messages.extend(_build_history_messages(conversation_history or []))
    messages.append({"role": "user", "content": f"Ticker: {ticker.upper()}.{context_note} {question}"})

    tools = get_voice_tool_definitions()
    data_gathered: list[str] = []
    tool_call_log: list[dict[str, Any]] = []

    for _ in range(MAX_ITERATIONS):
        message = chat_completion(messages, tools=tools)
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            reply = _fit_to_char_limit((message.get("content") or "").strip())
            return {
                "ticker": ticker.upper(),
                "question": question,
                "reply": reply,
                "tool_calls_made": tool_call_log,
                "data_gathered": data_gathered,
            }

        messages.append(message)

        for call in tool_calls:
            tool_name = call["function"]["name"]
            arguments = parse_tool_call_arguments(call["function"]["arguments"])
            result = execute_tool(tool_name, arguments)

            tool_call_log.append({"tool": tool_name, "arguments": arguments})
            data_gathered.append(_summarize_gathered(tool_name, result))

            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result, default=str)}
            )

    raise LLMClientError(f"Voice agent did not produce a reply within {MAX_ITERATIONS} tool-calling iterations")