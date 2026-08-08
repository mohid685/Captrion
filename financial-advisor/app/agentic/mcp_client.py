"""
MCP client for Alpha Vantage's remote MCP server.

Connects to https://mcp.alphavantage.co/mcp as a standard MCP client
(not through Claude's chat connector — this is a separate, direct
connection from our own backend), discovers its tools, and exposes a
curated subset to our agentic loop alongside our internal tools.

The MCP SDK is async; we wrap each call with asyncio.run() so the rest
of the codebase (which is synchronous) can call these functions plainly.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.config import get_settings

logger = logging.getLogger(__name__)

# Curated subset — Alpha Vantage's MCP server exposes 130+ tools; we
# only want the ones that add genuinely new capability beyond what
# we've already built (fundamentals, earnings, live quote, their own
# sentiment scoring for comparison against our FinBERT).
CURATED_TOOL_NAMES = {"COMPANY_OVERVIEW", "EARNINGS", "GLOBAL_QUOTE", "NEWS_SENTIMENT"}

class MCPClientError(Exception):
    """Raised when the Alpha Vantage MCP server can't be reached or called."""


def _server_url() -> str:
    settings = get_settings()
    if not settings.alpha_vantage_api_key:
        raise MCPClientError("ALPHA_VANTAGE_API_KEY is not set. Add it to your .env file.")
    return f"https://mcp.alphavantage.co/mcp?apikey={settings.alpha_vantage_api_key}"


async def _list_tools_async() -> list[dict[str, Any]]:
    async with streamablehttp_client(_server_url()) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema,
                }
                for tool in result.tools
                if tool.name in CURATED_TOOL_NAMES
            ]


async def _call_tool_async(name: str, arguments: dict[str, Any]) -> Any:
    async with streamablehttp_client(_server_url()) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            # MCP tool results are a list of content blocks; extract text content.
            texts = [block.text for block in result.content if hasattr(block, "text")]
            return "\n".join(texts) if texts else str(result.content)


@lru_cache
def get_curated_tool_definitions() -> list[dict[str, Any]]:
    """
    Fetches and caches the curated Alpha Vantage tool schemas, converted
    to OpenAI-compatible tool format. Cached for the process lifetime —
    the tool schemas themselves don't change at runtime.
    """
    try:
        mcp_tools = asyncio.run(_list_tools_async())
    except Exception as exc:
        logger.warning("Could not fetch Alpha Vantage MCP tools: %s", exc)
        return []

    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": f"[Alpha Vantage MCP] {tool['description']}",
                "parameters": tool["inputSchema"],
            },
        }
        for tool in mcp_tools
    ]


def call_alphavantage_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Calls a curated Alpha Vantage MCP tool and returns a JSON-serializable result."""
    if name not in CURATED_TOOL_NAMES:
        raise MCPClientError(f"'{name}' is not in the curated Alpha Vantage tool set")

    try:
        raw_result = asyncio.run(_call_tool_async(name, arguments))
    except Exception as exc:
        raise MCPClientError(f"Alpha Vantage MCP call to '{name}' failed: {exc}") from exc

    return {"tool": name, "raw_result": raw_result}