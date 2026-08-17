"""
Conversational voice agent: a direct, opinionated financial-advisor
persona with memory of the ongoing conversation. Uses all internal
tools (RAG, sentiment, trend, risk, price, calculator) plus live web
search (Tavily) as the Alpha Vantage replacement.
"""

from __future__ import annotations

import json
from typing import Any

from app.agentic.tool_definitions import get_voice_tool_definitions
from app.agentic.tool_executor import execute_tool, parse_tool_call_arguments
from app.core.llm_client import LLMClientError, chat_completion

MAX_ITERATIONS = 4
MAX_REPLY_CHARS = 480

VOICE_SYSTEM_PROMPT = """You are a knowledgeable, confident financial advisor speaking face to face \
with a client, continuing an ongoing conversation. You have tools for document search, sentiment, \
trend signals, risk metrics, live prices, and general web search — use whichever are relevant to \
answer the client's actual question about whatever company or ticker they're asking about right now. \
Never mention tools, data, sources, or that you "looked something up." Speak as if this knowledge is \
simply yours.

The client may hold positions in one or more other companies (listed below if any). Only bring up a \
specific holding if the client is asking about that exact company right now — do not mention or \
compare to their other holdings unless they ask, or unless it's genuinely relevant (e.g. portfolio \
concentration, diversification).

Give real opinions and direct guidance the way an experienced advisor would, including calling \
something a buy, hold, or a reason for caution — but ground every claim only in what your tools \
actually return. Never invent facts. If nothing useful turns up, say so plainly.

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
    if "error" in result:
        return f"{tool_name}: no data available"
    if "raw_result" in result:
        raw = str(result["raw_result"])
        return f"{tool_name}: {raw[:120]}..." if len(raw) > 120 else f"{tool_name}: {raw}"
    if "answer" in result:
        return f"{tool_name}: {str(result['answer'])[:150]}"
    keys_preview = ", ".join(f"{k}={result[k]}" for k in list(result.keys())[:4])
    return f"{tool_name}: {keys_preview}"


def _build_context_note(ticker: str, user_context: dict[str, Any] | None) -> str:
    if not user_context:
        return ""

    parts = []
    if user_context.get("risk_tolerance"):
        parts.append(f"risk tolerance: {user_context['risk_tolerance']}")
    if user_context.get("investment_goals"):
        parts.append(f"goals: {user_context['investment_goals']}")

    holdings = user_context.get("holdings") or []
    if holdings:
        holdings_str = "; ".join(
            f"{h['ticker']}: {h['shares']} shares @ ${h['cost_basis']:.2f} cost basis" for h in holdings
        )
        parts.append(f"portfolio holdings: {holdings_str}")

    if not parts:
        return ""
    return f" (Client context: {', '.join(parts)}. Ticker being discussed right now: {ticker.upper()}.)"


def _resolve_ticker_from_tool_calls(tool_call_log: list[dict[str, Any]], fallback: str) -> str:
    """Best-effort: report the most recent ticker actually looked up by a tool this turn."""
    for entry in reversed(tool_call_log):
        arguments = entry.get("arguments", {})
        if "ticker" in arguments and arguments["ticker"]:
            return str(arguments["ticker"]).upper()
    return fallback.upper()


def ask_voice_advisor(
    ticker: str,
    question: str,
    conversation_history: list[dict[str, str]] | None = None,
    user_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context_note = _build_context_note(ticker, user_context)

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
            resolved_ticker = _resolve_ticker_from_tool_calls(tool_call_log, ticker)
            return {
                "ticker": resolved_ticker,
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