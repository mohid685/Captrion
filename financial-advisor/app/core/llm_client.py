"""
OpenRouter LLM client wrapper.

OpenRouter exposes an OpenAI-compatible chat completions endpoint, so
this is a thin requests-based wrapper rather than a full SDK dependency.
Kept provider-agnostic in shape (system + user message in, text out) so
swapping providers later doesn't ripple through the reasoning layer.
"""

from __future__ import annotations

import logging

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMClientError(Exception):
    """Raised when the LLM provider isn't configured or the call fails."""


def generate_response(system_prompt: str, user_prompt: str) -> str:
    """
    Send a system + user prompt to the configured OpenRouter model and
    return the model's text response.
    """
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise LLMClientError("OPENROUTER_API_KEY is not set. Add it to your .env file.")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.exception("OpenRouter request failed")
        raise LLMClientError(f"OpenRouter request failed: {exc}") from exc

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise LLMClientError(f"OpenRouter returned no choices: {data}")

    return choices[0]["message"]["content"]