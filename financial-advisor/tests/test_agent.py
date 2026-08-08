from unittest.mock import MagicMock, patch

from app.agentic.agent import ask_agentic_advisor


class TestAskAgenticAdvisor:
    @patch("app.agentic.agent.execute_tool")
    @patch("app.agentic.agent.chat_completion")
    def test_no_tool_calls_returns_direct_answer(
        self, mock_chat: MagicMock, mock_execute: MagicMock
    ) -> None:
        mock_chat.return_value = {"content": "AAPL is a large tech company.", "tool_calls": None}

        result = ask_agentic_advisor("AAPL", "What does AAPL do?")

        assert result["answer"] == "AAPL is a large tech company."
        assert result["tool_calls_made"] == []
        mock_execute.assert_not_called()

    @patch("app.agentic.agent.execute_tool")
    @patch("app.agentic.agent.chat_completion")
    def test_single_tool_call_then_final_answer(
        self, mock_chat: MagicMock, mock_execute: MagicMock
    ) -> None:
        mock_chat.side_effect = [
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "get_current_price",
                            "arguments": '{"ticker": "AAPL"}',
                        },
                    }
                ],
            },
            {"content": "AAPL is currently trading at $312.41.", "tool_calls": None},
        ]
        mock_execute.return_value = {"date": "2026-08-06", "close": 312.41}

        result = ask_agentic_advisor("AAPL", "What's the current price?")

        assert result["answer"] == "AAPL is currently trading at $312.41."
        assert len(result["tool_calls_made"]) == 1
        assert result["tool_calls_made"][0]["tool"] == "get_current_price"
        mock_execute.assert_called_once_with("get_current_price", {"ticker": "AAPL"})

    @patch("app.agentic.agent.execute_tool")
    @patch("app.agentic.agent.chat_completion")
    def test_raises_after_max_iterations_without_final_answer(
        self, mock_chat: MagicMock, mock_execute: MagicMock
    ) -> None:
        from app.core.llm_client import LLMClientError

        mock_chat.return_value = {
            "content": None,
            "tool_calls": [
                {"id": "call_x", "function": {"name": "get_current_price", "arguments": '{"ticker": "AAPL"}'}}
            ],
        }
        mock_execute.return_value = {"close": 100}

        import pytest

        with pytest.raises(LLMClientError):
            ask_agentic_advisor("AAPL", "loop forever")