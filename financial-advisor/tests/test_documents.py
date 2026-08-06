from unittest.mock import MagicMock, patch

import pytest

from app.ingestion.documents import (
    DocumentIngestionError,
    fetch_recent_news,
)


class TestFetchRecentNews:
    @patch("app.ingestion.documents.get_settings")
    @patch("app.ingestion.documents.requests.get")
    def test_returns_documents_from_feed(
        self, mock_get: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.return_value.alpha_vantage_api_key = "fake-key"
        mock_get.return_value.json.return_value = {
            "feed": [
                {
                    "title": "Company beats earnings estimates",
                    "summary": "Strong quarter driven by cloud growth.",
                    "time_published": "20260801T120000",
                }
            ]
        }
        mock_get.return_value.raise_for_status = MagicMock()

        result = fetch_recent_news("MSFT")

        assert len(result) == 1
        assert result[0]["source"] == "news"
        assert "beats earnings" in result[0]["raw_text"]

    @patch("app.ingestion.documents.get_settings")
    def test_raises_without_api_key(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value.alpha_vantage_api_key = None
        with pytest.raises(DocumentIngestionError):
            fetch_recent_news("MSFT")