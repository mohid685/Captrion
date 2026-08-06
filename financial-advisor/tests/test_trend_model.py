from unittest.mock import MagicMock, patch

import pytest

from app.ml import trend_model


def _fake_history(n: int = 300, trend: str = "up") -> list[dict]:
    step = 1.0 if trend == "up" else -1.0
    return [
        {
            "date": f"day{i}",
            "open": 100 + i * step - 0.5,
            "high": 100 + i * step + 1,
            "low": 100 + i * step - 1,
            "close": 100 + i * step,
            "volume": 1_000_000 + (i % 50) * 5000,
        }
        for i in range(n)
    ]


class TestTrainTrendModel:
    def test_raises_on_insufficient_data(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(trend_model, "MODELS_DIR", tmp_path)
        with patch.object(trend_model, "get_historical_prices", return_value=_fake_history(n=20)):
            with pytest.raises(trend_model.TrendModelError):
                trend_model.train_trend_model("FAKE")

    def test_trains_and_persists_model(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(trend_model, "MODELS_DIR", tmp_path)
        with patch.object(trend_model, "get_historical_prices", return_value=_fake_history(n=300)):
            result = trend_model.train_trend_model("FAKE")

        assert result["ticker"] == "FAKE"
        assert result["train_samples"] > 0
        assert (tmp_path / "FAKE_trend.json").exists()


class TestPredictTrend:
    def test_raises_if_no_model_trained(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(trend_model, "MODELS_DIR", tmp_path)
        with pytest.raises(trend_model.TrendModelError):
            trend_model.predict_trend("NOTRAINED")

    def test_predicts_after_training(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(trend_model, "MODELS_DIR", tmp_path)
        history = _fake_history(n=300)

        with patch.object(trend_model, "get_historical_prices", return_value=history):
            trend_model.train_trend_model("FAKE")
            result = trend_model.predict_trend("FAKE")

        assert result["trend_prediction"] in {"up", "down", "sideways"}
        assert 0 <= result["trend_confidence"] <= 1
        assert set(result["probabilities"].keys()) == {"up", "down", "sideways"}