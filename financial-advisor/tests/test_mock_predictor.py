from app.ml.mock_predictor import get_mock_ml_signals


class TestMockPredictor:
    def test_returns_expected_shape(self) -> None:
        signals = get_mock_ml_signals("aapl")
        assert signals["ticker"] == "AAPL"
        assert signals["trend_prediction"] == "upward"
        assert 0 <= signals["trend_confidence"] <= 1
        assert "risk_level" in signals
        assert "MOCK DATA" in signals["note"]

    def test_ticker_is_uppercased(self) -> None:
        assert get_mock_ml_signals("tsla")["ticker"] == "TSLA"