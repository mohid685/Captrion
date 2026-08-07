"""
Combines real and mock ML signals into a single interface for the
reasoning layer. Trend is real when a model has been trained for the
ticker; falls back to mock (clearly labeled) otherwise. The trend
signal always carries an honest reliability rating, so the LLM prompt
can weight it appropriately rather than treating it as authoritative.
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
        signals["trend_reliability_tier"] = "n/a — this is a placeholder, not a real prediction"
        return signals

    signals["trend_prediction"] = real_trend["trend_prediction"]
    signals["trend_confidence"] = real_trend["trend_confidence"]
    signals["trend_probabilities"] = real_trend["probabilities"]
    signals["trend_source"] = "XGBoost (real model)"
    signals["trend_reliability_tier"] = real_trend["reliability"]["reliability_tier"]
    signals["trend_edge_over_baseline"] = real_trend["reliability"]["edge_over_baseline"]
    signals["note"] = (
        "Trend prediction is REAL (XGBoost, next-5-trading-day direction), "
        f"with reliability: {real_trend['reliability']['reliability_tier']}. "
        "Risk level and volatility are still MOCK DATA."
    )
    return signals