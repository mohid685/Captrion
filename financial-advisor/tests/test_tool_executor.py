from unittest.mock import patch

from app.agentic.tool_executor import execute_tool, parse_tool_call_arguments


class TestExecuteTool:
    def test_unknown_tool_raises(self) -> None:
        import pytest

        from app.agentic.tool_executor import ToolExecutionError

        with pytest.raises(ToolExecutionError):
            execute_tool("nonexistent_tool", {})

    def test_calculate_financial_metric_success(self) -> None:
        result = execute_tool(
            "calculate_financial_metric",
            {"metric": "ROI", "cost": 100, "gain": 150, "beginning_value": None},
        )
        assert result["metric"] == "ROI"
        assert result["result"] == 0.5

    def test_calculate_financial_metric_error_returns_error_dict(self) -> None:
        result = execute_tool("calculate_financial_metric", {"metric": "CAGR"})
        assert "error" in result

    @patch("app.agentic.tool_executor.get_latest_price")
    def test_get_current_price(self, mock_price) -> None:
        mock_price.return_value = {"date": "2026-08-06", "close": 312.41}
        result = execute_tool("get_current_price", {"ticker": "AAPL"})
        assert result["close"] == 312.41


class TestParseToolCallArguments:
    def test_parses_valid_json(self) -> None:
        args = parse_tool_call_arguments('{"ticker": "AAPL", "query": "revenue"}')
        assert args == {"ticker": "AAPL", "query": "revenue"}

    def test_raises_on_invalid_json(self) -> None:
        import pytest

        from app.agentic.tool_executor import ToolExecutionError

        with pytest.raises(ToolExecutionError):
            parse_tool_call_arguments("not valid json")