"""
Real-time financial web search via Tavily — replaces Alpha Vantage MCP
in the voice path. One call, current results, works for any company or
topic (not limited to a curated tool list or ticker coverage gaps).
"""

from __future__ import annotations

import logging

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

TAVILY_URL = "https://api.tavily.com/search"


class WebSearchError(Exception):
    """Raised when the web search fails."""


def search_financial_web(query: str, max_results: int = 5) -> dict:
    """
    Runs a fine-grained web search built from the user's actual query at
    call time, and returns a compact index (Tavily's synthesized answer
    plus source snippets) suitable for LLM context.
    """
    settings = get_settings()
    if not settings.tavily_api_key:
        raise WebSearchError("TAVILY_API_KEY is not set. Add it to your .env file.")

    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True,
    }

    try:
        response = requests.post(TAVILY_URL, json=payload, timeout=(5, 12))
    except requests.exceptions.RequestException as exc:
        logger.warning("Tavily search failed: %s", exc)
        raise WebSearchError(f"Tavily search failed: {exc}") from exc

    if response.status_code != 200:
        raise WebSearchError(f"Tavily returned status {response.status_code}: {response.text[:300]}")

    data = response.json()
    results = [
        {"title": r.get("title", ""), "content": r.get("content", "")[:400], "url": r.get("url", "")}
        for r in data.get("results", [])
    ]

    return {
        "query": query,
        "answer": data.get("answer", ""),
        "sources": results,
    }