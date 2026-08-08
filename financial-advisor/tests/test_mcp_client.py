from unittest.mock import AsyncMock, patch

import pytest

from app.agentic.mcp_client import (
    CURATED_TOOL_NAMES,
    MCPClientError,
    call_alphavantage_tool,
    get_curated_tool_definitions,
)


class TestGetCuratedToolDefinitions:
    def test_returns_empty_list_on_connection_failure(self) -> None:
        get_curated_tool_definitions.cache_clear()
        with patch("app.agentic.mcp_client._list_tools_async", side_effect=Exception("connection failed")):
            result = get_curated_tool_definitions()
        assert result == []
        get_curated_tool_definitions.cache_clear()

    def test_converts_mcp_schema_to_openai_format(self) -> None:
        get_curated_tool_definitions.cache_clear()
        fake_tools = [
            {"name": "OVERVIEW", "description": "Company overview", "inputSchema": {"type": "object", "properties": {}}}
        ]
        with patch("app.agentic.mcp_client._list_tools_async", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = fake_tools
            with patch("app.agentic.mcp_client.asyncio.run", return_value=fake_tools):
                result = get_curated_tool_definitions()

        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "OVERVIEW"
        assert "[Alpha Vantage MCP]" in result[0]["function"]["description"]
        get_curated_tool_definitions.cache_clear()


class TestCallAlphavantageTool:
    def test_raises_on_uncurated_tool_name(self) -> None:
        with pytest.raises(MCPClientError):
            call_alphavantage_tool("SOME_UNCURATED_TOOL", {})

    def test_returns_result_on_success(self) -> None:
        with patch("app.agentic.mcp_client.asyncio.run", return_value="AAPL overview text"):
            result = call_alphavantage_tool("COMPANY_OVERVIEW", {"symbol": "AAPL"})

        assert result["tool"] == "COMPANY_OVERVIEW"
        assert result["raw_result"] == "AAPL overview text"

    def test_wraps_failures_in_mcp_client_error(self) -> None:
        with patch("app.agentic.mcp_client.asyncio.run", side_effect=Exception("network error")):
            with pytest.raises(MCPClientError):
                call_alphavantage_tool("GLOBAL_QUOTE", {"symbol": "AAPL"})


def test_curated_tool_names_are_the_expected_set() -> None:
    assert CURATED_TOOL_NAMES == {"COMPANY_OVERVIEW", "EARNINGS", "GLOBAL_QUOTE", "NEWS_SENTIMENT"}