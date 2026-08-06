"""
Tests for the market data ingestion layer.

Mocks yfinance/requests so these run offline and deterministically.
Run with: pytest -m "not integration"  (skips the real network call)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.ingestion.market_data import (
    MarketDataError,
    get_historical_prices,
    get_latest_price,
)


def _fake_yfinance_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [100.0, 102.0],
            "High": [105.0, 107.0],
            "Low": [99.0, 101.0],
            "Close": [104.0, 106.0],
            "Volume": [1_000_000, 1_200_000],
        },
        index=pd.to_datetime(["2026-07-01", "2026-07-02"]),
    )


class TestGetHistoricalPrices:
    @patch("app.ingestion.market_data.yf.Ticker")
    def test_returns_records_from_yfinance(self, mock_ticker: MagicMock) -> None:
        mock_ticker.return_value.history.return_value = _fake_yfinance_history()

        result = get_historical_prices("AAPL", period="1mo", interval="1d")

        assert len(result) == 2
        assert result[0]["date"] == "2026-07-01"
        assert result[0]["close"] == 104.0
        assert result[1]["volume"] == 1_200_000

    @patch("app.ingestion.market_data.get_settings")
    @patch("app.ingestion.market_data.yf.Ticker")
    def test_falls_back_to_alpha_vantage_when_yfinance_empty(
        self, mock_ticker: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_ticker.return_value.history.return_value = pd.DataFrame()
        mock_settings.return_value.alpha_vantage_api_key = "fake-key"

        fake_response = {
            "Time Series (Daily)": {
                "2026-07-01": {
                    "1. open": "100.0",
                    "2. high": "105.0",
                    "3. low": "99.0",
                    "4. close": "104.0",
                    "5. volume": "1000000",
                }
            }
        }

        with patch("app.ingestion.market_data.requests.get") as mock_get:
            mock_get.return_value.json.return_value = fake_response
            mock_get.return_value.raise_for_status = MagicMock()

            result = get_historical_prices("AAPL")

        assert len(result) == 1
        assert result[0]["close"] == 104.0

    @patch("app.ingestion.market_data.get_settings")
    @patch("app.ingestion.market_data.yf.Ticker")
    def test_raises_when_no_source_has_data(
        self, mock_ticker: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_ticker.return_value.history.return_value = pd.DataFrame()
        mock_settings.return_value.alpha_vantage_api_key = None

        with pytest.raises(MarketDataError):
            get_historical_prices("INVALID_TICKER_XYZ")


class TestGetLatestPrice:
    @patch("app.ingestion.market_data.yf.Ticker")
    def test_returns_most_recent_day(self, mock_ticker: MagicMock) -> None:
        mock_ticker.return_value.history.return_value = _fake_yfinance_history()

        result = get_latest_price("AAPL")

        assert result["date"] == "2026-07-02"
        assert result["close"] == 106.0


@pytest.mark.integration
class TestIntegration:
    """Hits the real yfinance API. Requires network access."""

    def test_real_fetch_for_known_ticker(self) -> None:
        result = get_historical_prices("AAPL", period="5d", interval="1d")
        assert len(result) > 0
        assert "close" in result[0]