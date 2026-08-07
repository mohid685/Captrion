import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ml import trend_model


def _fake_history(n: int = 300, trend: str = "up") -> list[dict]:
    """
    Synthetic OHLCV history that oscillates in medium-length waves, so
    the 5-day-ahead label ends up containing a mix of up/down/sideways
    — a flat or monotonic series only produces 1-2 classes, which
    XGBoost's multiclass fit rejects.
    """
    import math

    records = []
    price = 100.0
    for i in range(n):
        # A slow sine wave drift plus small daily noise-like step
        price = 100 + 15 * math.sin(i / 12) + (i % 5) * 0.3
        records.append(
            {
                "date": f"day{i}",
                "open": price - 0.5,
                "high": price + 1,
                "low": price - 1,
                "close": price,
                "volume": 1_000_000 + (i % 50) * 5000,
            }
        )
    return records


@pytest.fixture
def models_dir(monkeypatch):
    """Manually managed temp dir, sidestepping pytest's own tmp_path machinery."""
    temp_dir = Path(tempfile.mkdtemp(prefix="captrion_models_"))
    monkeypatch.setattr(trend_model, "MODELS_DIR", temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestTrainTrendModel:
    def test_raises_on_insufficient_data(self, models_dir) -> None:
        with patch.object(trend_model, "get_historical_prices", return_value=_fake_history(n=20)):
            with pytest.raises(trend_model.TrendModelError):
                trend_model.train_trend_model("FAKE")

    def test_trains_and_persists_model(self, models_dir) -> None:
        with patch.object(trend_model, "get_historical_prices", return_value=_fake_history(n=300)):
            result = trend_model.train_trend_model("FAKE")

        assert result["ticker"] == "FAKE"
        assert result["train_samples"] > 0
        assert (models_dir / "FAKE_trend.json").exists()


class TestPredictTrend:
    def test_raises_if_no_model_trained(self, models_dir) -> None:
        with pytest.raises(trend_model.TrendModelError):
            trend_model.predict_trend("NOTRAINED")

    def test_predicts_after_training(self, models_dir) -> None:
        history = _fake_history(n=300)

        with patch.object(trend_model, "get_historical_prices", return_value=history):
            trend_model.train_trend_model("FAKE")
            result = trend_model.predict_trend("FAKE")

        assert result["trend_prediction"] in {"up", "down", "sideways"}
        assert 0 <= result["trend_confidence"] <= 1
        assert set(result["probabilities"].keys()) == {"up", "down", "sideways"}