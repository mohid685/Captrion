from unittest.mock import patch

from app.ml.predictor import get_ml_signals
from app.ml.trend_model import TrendModelError


class TestGetMlSignals:
    def test_falls_back_to_mock_when_no_model(self) -> None:
        with patch("app.ml.predictor.predict_trend", side_effect=TrendModelError("no model")):
            signals = get_ml_signals("UNTRAINED")

        assert signals["trend_prediction"] == "upward"  # from mock_predictor
        assert "MOCK" in signals["trend_source"]

    def test_uses_real_trend_when_model_exists(self) -> None:
        fake_real = {
            "trend_prediction": "down",
            "trend_confidence": 0.81,
            "probabilities": {"up": 0.1, "down": 0.81, "sideways": 0.09},
            "reliability": {
                "naive_baseline_accuracy": 0.5,
                "edge_over_baseline": 0.12,
                "reliability_tier": "moderate — meaningfully outperforms the naive baseline",
            },
        }
        with patch("app.ml.predictor.predict_trend", return_value=fake_real):
            signals = get_ml_signals("TRAINED")

        assert signals["trend_prediction"] == "down"
        assert signals["trend_confidence"] == 0.81
        assert signals["trend_source"] == "XGBoost (real model)"
        assert signals["trend_reliability_tier"] == "moderate — meaningfully outperforms the naive baseline"
        assert "REAL" in signals["note"]