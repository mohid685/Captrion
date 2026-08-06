"""
Combines real and mock ML signals into a single interface for the
reasoning layer. Trend is real when a model has been trained for the
ticker; falls back to mock (clearly labeled) otherwise, so /advisor/ask
never breaks for an untrained ticker.
"""

from __future__ import annotations

from typing import Any

from app.ml.mock_predictor import get_mock_ml_signals
from app.ml.trend_model import TrendModelError, predict_trend


def get_ml_signals(ticker: str) -> dict[str, Any]:
    signals = get_mock_ml_signals(ticker)

    try:
        real_trend = predict_trend(ticker)
    except TrendModelError:
        signals["trend_source"] = (
            f"MOCK (no trained model yet — POST /ml/{ticker.upper()}/train to enable real predictions)"
        )
        return signals

    signals["trend_prediction"] = real_trend["trend_prediction"]
    signals["trend_confidence"] = real_trend["trend_confidence"]
    signals["trend_probabilities"] = real_trend["probabilities"]
    signals["trend_source"] = "XGBoost (real model)"
    signals["note"] = (
        "Trend prediction is REAL (XGBoost, next-5-trading-day direction). "
        "Risk level and volatility are still MOCK DATA."
    )
    return signals