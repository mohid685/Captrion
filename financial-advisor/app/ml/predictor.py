"""
Combines real trend prediction, real risk metrics, and mock signals
into a single interface for the reasoning layer. Trend and risk are
real when computable; each falls back to mock (clearly labeled)
independently, so /advisor/ask never breaks entirely if one piece
fails.
"""

from __future__ import annotations

from typing import Any

from app.ml.mock_predictor import get_mock_ml_signals
from app.ml.risk_metrics import RiskMetricsError, compute_risk_metrics
from app.ml.trend_model import TrendModelError, predict_trend


def get_ml_signals(ticker: str) -> dict[str, Any]:
    signals = get_mock_ml_signals(ticker)
    notes: list[str] = []

    try:
        real_trend = predict_trend(ticker)
        signals["trend_prediction"] = real_trend["trend_prediction"]
        signals["trend_confidence"] = real_trend["trend_confidence"]
        signals["trend_probabilities"] = real_trend["probabilities"]
        signals["trend_source"] = "XGBoost (real model)"
        signals["trend_reliability_tier"] = real_trend["reliability"]["reliability_tier"]
        signals["trend_edge_over_baseline"] = real_trend["reliability"]["edge_over_baseline"]
        notes.append(
            f"Trend prediction is REAL (XGBoost, next-5-trading-day direction), "
            f"reliability: {real_trend['reliability']['reliability_tier']}."
        )
    except TrendModelError:
        signals["trend_source"] = (
            f"MOCK (no trained model yet — POST /ml/{ticker.upper()}/train to enable real predictions)"
        )
        signals["trend_reliability_tier"] = "n/a — this is a placeholder, not a real prediction"
        notes.append("Trend prediction is MOCK DATA (no model trained yet).")

    try:
        real_risk = compute_risk_metrics(ticker)
        signals["risk_level"] = real_risk["risk_level"]
        signals["sharpe_ratio_estimate"] = real_risk["sharpe_ratio"]
        signals["volatility"] = real_risk["risk_level"]  # keep prior string-shaped field for prompt compatibility
        signals["annualized_volatility"] = real_risk["annualized_volatility"]
        signals["max_drawdown"] = real_risk["max_drawdown"]
        signals["beta"] = real_risk["beta"]
        signals["risk_source"] = "Computed (real statistics: volatility, Sharpe, max drawdown, Beta vs. SPY)"
        notes.append(
            f"Risk metrics are REAL: volatility {real_risk['annualized_volatility']:.1%}, "
            f"Sharpe {real_risk['sharpe_ratio']}, max drawdown {real_risk['max_drawdown']:.1%}, "
            f"Beta {real_risk['beta']}."
        )
    except RiskMetricsError:
        signals["risk_source"] = "MOCK (risk metrics could not be computed)"
        notes.append("Risk metrics are MOCK DATA (calculation failed, likely insufficient price history).")

    signals["note"] = " ".join(notes)
    return signals