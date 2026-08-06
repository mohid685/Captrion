"""
Mock ML signals.

Fixed values, shaped exactly like what Phase 3's real models (XGBoost
trend classifier, risk metrics, etc.) will eventually produce. This
lets the prompt structure in the reasoning layer be built once and
stay unchanged when the mock is swapped for real predictions.
"""

from __future__ import annotations

from typing import Any


def get_mock_ml_signals(ticker: str) -> dict[str, Any]:
    """Fixed mock signals — same for any ticker, for predictable prompt testing."""
    return {
        "ticker": ticker.upper(),
        "trend_prediction": "upward",
        "trend_confidence": 0.72,
        "risk_level": "moderate",
        "sharpe_ratio_estimate": 1.1,
        "volatility": "medium",
        "note": "MOCK DATA — Phase 3 will replace this with real model output",
    }