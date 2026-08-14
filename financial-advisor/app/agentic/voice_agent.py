"""
Conversational voice agent: a direct, opinionated financial-advisor
persona (not a report-reader), with memory of the ongoing conversation.
Reuses the same tools as the analytical agent, but with a different
system prompt and a multi-turn message history.
"""

from __future__ import annotations

import json
from typing import Any

from app.agentic.tool_definitions import get_all_tool_definitions
from app.agentic.tool_executor import execute_tool, parse_tool_call_arguments
from app.core.llm_client import LLMClientError, chat_completion

MAX_ITERATIONS = 5
MAX_REPLY_CHARS = 480  # camb.ai free tier caps around 500 chars

VOICE_SYSTEM_PROMPT = """You are a knowledgeable, confident financial advisor speaking face to face \
with a client, continuing an ongoing conversation. You have tools for real market data, filings, \
sentiment, and risk metrics — use them when relevant, but NEVER mention tools, models, data, sources, \
or that you "looked something up." Speak as if this knowledge is simply yours.

Give real opinions and direct guidance the way an experienced advisor would, including calling \
something a buy, hold, or a reason for caution — but ground every claim only in what your tools \
actually return. Never invent facts.

Style:
- 2-4 sentences per reply. Natural spoken rhythm. First person ("I'd...", "I wouldn't...", "I think...").
- Address the client as "you". Weave any caution directly into the advice itself, e.g. "I wouldn't put \
it all in today, I'd start small and average in" — not a separate disclaimer paragraph.
- No markdown, no bullet points, no symbols like %, $, | — say numbers the way a person would speak \
them ("around three hundred five dollars", "up about eleven percent").
- Use the conversation history to understand follow-ups like "should I buy" or "what would you do" \
without the client repeating context.
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
    return text[:limit].rsplit(" ", 1)[0] + "."


def ask_voice_advisor(
    ticker: str,
    question: str,
    conversation_history: list[dict[str, str]] | None = None,
    user_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Runs the conversational voice agent: tool-calling loop with a
    direct advisor persona and multi-turn memory.
    """
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

    tool_call_log: list[dict[str, Any]] = []

    for _ in range(MAX_ITERATIONS):
        message = chat_completion(messages, tools=get_all_tool_definitions())
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            reply = _fit_to_char_limit((message.get("content") or "").strip())
            return {
                "ticker": ticker.upper(),
                "question": question,
                "reply": reply,
                "tool_calls_made": tool_call_log,
            }

        messages.append(message)

        for call in tool_calls:
            tool_name = call["function"]["name"]
            arguments = parse_tool_call_arguments(call["function"]["arguments"])
            result = execute_tool(tool_name, arguments)

            tool_call_log.append({"tool": tool_name, "arguments": arguments})
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result, default=str)}
            )

    raise LLMClientError(f"Voice agent did not produce a reply within {MAX_ITERATIONS} tool-calling iterations")