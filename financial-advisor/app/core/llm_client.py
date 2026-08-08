"""
OpenRouter LLM client wrapper.

generate_response() is the simple text-in/text-out call used by the
fixed-pipeline /advisor/ask endpoint (Phase 2/3).
chat_completion() is the lower-level call used by the agentic layer
(Phase 4), which needs the full message/tool_calls structure rather
than just the final text.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMClientError(Exception):
    """Raised when the LLM provider isn't configured or the call fails."""


def _post_to_openrouter(payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise LLMClientError("OPENROUTER_API_KEY is not set. Add it to your .env file.")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.exception("OpenRouter request failed")
        raise LLMClientError(f"OpenRouter request failed: {exc}") from exc

    return response.json()


def generate_response(system_prompt: str, user_prompt: str) -> str:
    """Simple text-in/text-out call — no tool calling."""
    settings = get_settings()
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    data = _post_to_openrouter(payload)
    choices = data.get("choices", [])
    if not choices:
        raise LLMClientError(f"OpenRouter returned no choices: {data}")
    return choices[0]["message"]["content"]


def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Lower-level call for the agentic layer. Returns the full assistant
    message dict (which may contain "content" and/or "tool_calls"),
    rather than just extracted text.
    """
    settings = get_settings()
    payload: dict[str, Any] = {
        "model": settings.openrouter_model,
        "messages": messages,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    data = _post_to_openrouter(payload)
    choices = data.get("choices", [])
    if not choices:
        raise LLMClientError(f"OpenRouter returned no choices: {data}")

    return choices[0]["message"]