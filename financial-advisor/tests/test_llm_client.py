from unittest.mock import MagicMock, patch

import pytest

from app.core.llm_client import LLMClientError, generate_response


class TestGenerateResponse:
    @patch("app.core.llm_client.get_settings")
    def test_raises_without_api_key(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value.openrouter_api_key = None
        with pytest.raises(LLMClientError):
            generate_response("system", "user")

    @patch("app.core.llm_client.get_settings")
    @patch("app.core.llm_client.requests.post")
    def test_returns_content_on_success(
        self, mock_post: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.return_value.openrouter_api_key = "fake-key"
        mock_settings.return_value.openrouter_model = "openai/gpt-oss-20b:free"
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "This is the answer."}}]
        }
        mock_post.return_value.raise_for_status = MagicMock()

        result = generate_response("system prompt", "user prompt")

        assert result == "This is the answer."

    @patch("app.core.llm_client.get_settings")
    @patch("app.core.llm_client.requests.post")
    def test_raises_on_empty_choices(
        self, mock_post: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.return_value.openrouter_api_key = "fake-key"
        mock_settings.return_value.openrouter_model = "openai/gpt-oss-20b:free"
        mock_post.return_value.json.return_value = {"choices": []}
        mock_post.return_value.raise_for_status = MagicMock()

        with pytest.raises(LLMClientError):
            generate_response("system", "user")