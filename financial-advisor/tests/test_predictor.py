from unittest.mock import patch

from app.ml.predictor import get_ml_signals
from app.ml.risk_metrics import RiskMetricsError
from app.ml.trend_model import TrendModelError


FAKE_REAL_TREND = {
    "trend_prediction": "down",
    "trend_confidence": 0.81,
    "probabilities": {"up": 0.1, "down": 0.81, "sideways": 0.09},
    "reliability": {
        "naive_baseline_accuracy": 0.5,
        "edge_over_baseline": 0.12,
        "reliability_tier": "moderate — meaningfully outperforms the naive baseline",
    },
}

FAKE_REAL_RISK = {
    "ticker": "TRAINED",
    "annualized_volatility": 0.28,
    "annualized_return": 0.15,
    "sharpe_ratio": 0.36,
    "max_drawdown": -0.22,
    "beta": 1.15,
    "risk_level": "moderate",
    "risk_free_rate_assumption": 0.045,
    "benchmark": "SPY",
}


class TestGetMlSignals:
    def test_falls_back_to_mock_trend_when_no_model(self) -> None:
        with (
            patch("app.ml.predictor.predict_trend", side_effect=TrendModelError("no model")),
            patch("app.ml.predictor.compute_risk_metrics", return_value=FAKE_REAL_RISK),
        ):
            signals = get_ml_signals("UNTRAINED")

        assert signals["trend_prediction"] == "upward"  # from mock_predictor
        assert "MOCK" in signals["trend_source"]

    def test_uses_real_trend_when_model_exists(self) -> None:
        with (
            patch("app.ml.predictor.predict_trend", return_value=FAKE_REAL_TREND),
            patch("app.ml.predictor.compute_risk_metrics", return_value=FAKE_REAL_RISK),
        ):
            signals = get_ml_signals("TRAINED")

        assert signals["trend_prediction"] == "down"
        assert signals["trend_confidence"] == 0.81
        assert signals["trend_source"] == "XGBoost (real model)"
        assert signals["trend_reliability_tier"] == "moderate — meaningfully outperforms the naive baseline"

    def test_uses_real_risk_metrics_when_available(self) -> None:
        with (
            patch("app.ml.predictor.predict_trend", return_value=FAKE_REAL_TREND),
            patch("app.ml.predictor.compute_risk_metrics", return_value=FAKE_REAL_RISK),
        ):
            signals = get_ml_signals("TRAINED")

        assert signals["risk_level"] == "moderate"
        assert signals["sharpe_ratio_estimate"] == 0.36
        assert signals["annualized_volatility"] == 0.28
        assert signals["max_drawdown"] == -0.22
        assert signals["beta"] == 1.15
        assert "Computed (real statistics" in signals["risk_source"]

    def test_falls_back_to_mock_risk_when_computation_fails(self) -> None:
        with (
            patch("app.ml.predictor.predict_trend", return_value=FAKE_REAL_TREND),
            patch("app.ml.predictor.compute_risk_metrics", side_effect=RiskMetricsError("no data")),
        ):
            signals = get_ml_signals("NODATA")

        assert "MOCK" in signals["risk_source"]

    def test_note_combines_both_trend_and_risk_status(self) -> None:
        with (
            patch("app.ml.predictor.predict_trend", side_effect=TrendModelError("no model")),
            patch("app.ml.predictor.compute_risk_metrics", side_effect=RiskMetricsError("no data")),
        ):
            signals = get_ml_signals("NOTHING")

        assert "Trend prediction is MOCK DATA" in signals["note"]
        assert "Risk metrics are MOCK DATA" in signals["note"]